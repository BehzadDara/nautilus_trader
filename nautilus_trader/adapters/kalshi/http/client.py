from __future__ import annotations
import base64
from typing import Any
from urllib.parse import urlsplit
import msgspec
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_ACCESS_KEY_HEADER
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_ACCESS_SIGNATURE_HEADER
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_ACCESS_TIMESTAMP_HEADER
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_API_PATH
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_HTTP_RATE_LIMIT
from nautilus_trader.adapters.kalshi.common.env import get_kalshi_base_url_http
from nautilus_trader.adapters.kalshi.http.errors import KalshiHttpError
from nautilus_trader.common.component import Logger
from nautilus_trader.core.nautilus_pyo3 import HttpClient
from nautilus_trader.core.nautilus_pyo3 import HttpMethod
from nautilus_trader.core.nautilus_pyo3 import HttpResponse
from nautilus_trader.core.nautilus_pyo3 import Quota
_HTTP_METHOD_NAMES: dict[HttpMethod, str] = {HttpMethod.GET: 'GET', HttpMethod.POST: 'POST', HttpMethod.PUT: 'PUT', HttpMethod.DELETE: 'DELETE', HttpMethod.PATCH: 'PATCH'}

def load_private_key(private_key_pem: str) -> RSAPrivateKey:
    key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    if not isinstance(key, RSAPrivateKey):
        raise ValueError('Kalshi private key must be an RSA private key')
    return key

def sign_pss_text(private_key: RSAPrivateKey, text: str) -> str:
    signature = private_key.sign(text.encode(), padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH), hashes.SHA256())
    return base64.b64encode(signature).decode()

class KalshiHttpClient:

    def __init__(self, api_key_id: str, private_key_pem: str, clock: Any, base_url: str | None=None, proxy_url: str | None=None) -> None:
        self._api_key_id = api_key_id
        self._private_key = load_private_key(private_key_pem)
        self._clock = clock
        self._base_url = base_url or get_kalshi_base_url_http()
        self._log = Logger(name=type(self).__name__)
        self._client = HttpClient(proxy_url=proxy_url, default_quota=Quota.rate_per_minute(KALSHI_HTTP_RATE_LIMIT))
        self._decoder = msgspec.json.Decoder()

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def api_key_id(self) -> str:
        return self._api_key_id

    def _signed_headers(self, method: HttpMethod, path: str) -> dict[str, str]:
        timestamp_ms = str(self._clock.timestamp_ms())
        message = timestamp_ms + _HTTP_METHOD_NAMES[method] + path
        signature = sign_pss_text(self._private_key, message)
        return {KALSHI_ACCESS_KEY_HEADER: self._api_key_id, KALSHI_ACCESS_TIMESTAMP_HEADER: timestamp_ms, KALSHI_ACCESS_SIGNATURE_HEADER: signature, 'Content-Type': 'application/json', 'Accept': 'application/json'}

    async def request(self, method: HttpMethod, endpoint: str, params: dict[str, Any] | None=None, payload: dict[str, Any] | None=None) -> Any:
        path = KALSHI_API_PATH + endpoint
        url = self._base_url + path
        if params:
            query = '&'.join((f'{k}={v}' for k, v in params.items() if v is not None))
            if query:
                url = f'{url}?{query}'
        headers = self._signed_headers(method, path)
        body = msgspec.json.encode(payload) if payload is not None else None
        self._log.debug(f'[REQ] {_HTTP_METHOD_NAMES[method]} {url}')
        response: HttpResponse = await self._client.request(method, url, headers=headers, body=body)
        if response.status >= 400:
            self._handle_error(response)
        if not response.body:
            return None
        return self._decoder.decode(response.body)

    def _handle_error(self, response: HttpResponse) -> None:
        message = response.body.decode() if response.body else ''
        code = None
        try:
            parsed = self._decoder.decode(response.body)
            if isinstance(parsed, dict):
                code = parsed.get('code')
                message = parsed.get('message', message)
        except Exception:
            pass
        raise KalshiHttpError(status=response.status, message=message, code=code)

    async def get(self, endpoint: str, params: dict[str, Any] | None=None) -> Any:
        return await self.request(HttpMethod.GET, endpoint, params=params)

    async def post(self, endpoint: str, payload: dict[str, Any] | None=None) -> Any:
        return await self.request(HttpMethod.POST, endpoint, payload=payload)

    async def delete(self, endpoint: str, params: dict[str, Any] | None=None) -> Any:
        return await self.request(HttpMethod.DELETE, endpoint, params=params)

    @staticmethod
    def path_without_query(url: str) -> str:
        return urlsplit(url).path

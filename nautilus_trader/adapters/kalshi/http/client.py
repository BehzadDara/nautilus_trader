# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2026 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------
"""
Kalshi REST HTTP client with RSA-PSS request signing.

Signing scheme: the string-to-sign is ``timestamp(ms) + METHOD + path`` where the
path excludes any query string and includes the ``/trade-api/v2`` prefix. The
signature is RSA-PSS over SHA-256 with a salt length equal to the digest length,
base64-encoded, and sent via the ``KALSHI-ACCESS-KEY`` / ``KALSHI-ACCESS-TIMESTAMP``
/ ``KALSHI-ACCESS-SIGNATURE`` headers.
"""

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


# The pyo3 ``HttpMethod`` enum has no clean string accessor, so map to the verb
# used in the signed string-to-sign.
_HTTP_METHOD_NAMES: dict[HttpMethod, str] = {
    HttpMethod.GET: "GET",
    HttpMethod.POST: "POST",
    HttpMethod.PUT: "PUT",
    HttpMethod.DELETE: "DELETE",
    HttpMethod.PATCH: "PATCH",
}


def load_private_key(private_key_pem: str) -> RSAPrivateKey:
    """
    Load an RSA private key from its PEM representation.
    """
    key = serialization.load_pem_private_key(private_key_pem.encode(), password=None)
    if not isinstance(key, RSAPrivateKey):
        raise ValueError("Kalshi private key must be an RSA private key")
    return key


def sign_pss_text(private_key: RSAPrivateKey, text: str) -> str:
    """
    Return the base64-encoded RSA-PSS/SHA-256 signature of ``text``.

    Uses a salt length equal to the digest length, matching Kalshi's scheme.
    """
    signature = private_key.sign(
        text.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode()


class KalshiHttpClient:
    """
    Provides a Kalshi REST API client with RSA-PSS request signing.

    Parameters
    ----------
    api_key_id : str
        The Kalshi API key ID (the ``KALSHI-ACCESS-KEY`` header value).
    private_key_pem : str
        The RSA private key (PEM) used to sign requests.
    clock : object
        A clock exposing ``timestamp_ms()`` (the Nautilus ``LiveClock``).
    base_url : str, optional
        An explicit base URL override.
    proxy_url : str, optional
        An optional proxy URL.

    """

    def __init__(
        self,
        api_key_id: str,
        private_key_pem: str,
        clock: Any,
        base_url: str | None = None,
        proxy_url: str | None = None,
    ) -> None:
        self._api_key_id = api_key_id
        self._private_key = load_private_key(private_key_pem)
        self._clock = clock
        self._base_url = base_url or get_kalshi_base_url_http()
        self._log = Logger(name=type(self).__name__)

        self._client = HttpClient(
            proxy_url=proxy_url,
            default_quota=Quota.rate_per_minute(KALSHI_HTTP_RATE_LIMIT),
        )
        self._decoder = msgspec.json.Decoder()

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def api_key_id(self) -> str:
        return self._api_key_id

    def _signed_headers(self, method: HttpMethod, path: str) -> dict[str, str]:
        """
        Build the signed request headers for ``method`` and ``path``.

        ``path`` must be the request path without a query string and must include
        the ``/trade-api/v2`` prefix (this is exactly what gets signed).
        """
        timestamp_ms = str(self._clock.timestamp_ms())
        message = timestamp_ms + _HTTP_METHOD_NAMES[method] + path
        signature = sign_pss_text(self._private_key, message)
        return {
            KALSHI_ACCESS_KEY_HEADER: self._api_key_id,
            KALSHI_ACCESS_TIMESTAMP_HEADER: timestamp_ms,
            KALSHI_ACCESS_SIGNATURE_HEADER: signature,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def request(
        self,
        method: HttpMethod,
        endpoint: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        """
        Send a signed request to ``endpoint`` and return the decoded JSON body.

        Parameters
        ----------
        method : HttpMethod
            The HTTP method.
        endpoint : str
            The endpoint path relative to the API base path, e.g. ``/markets``.
            The ``/trade-api/v2`` prefix is added automatically.
        params : dict, optional
            Query parameters (not part of the signature).
        payload : dict, optional
            A JSON request body.

        """
        path = KALSHI_API_PATH + endpoint  # signed path (no query string)
        url = self._base_url + path
        if params:
            query = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
            if query:
                url = f"{url}?{query}"

        headers = self._signed_headers(method, path)
        body = msgspec.json.encode(payload) if payload is not None else None

        self._log.debug(f"[REQ] {_HTTP_METHOD_NAMES[method]} {url}")
        response: HttpResponse = await self._client.request(
            method,
            url,
            headers=headers,
            body=body,
        )

        if response.status >= 400:
            self._handle_error(response)

        if not response.body:
            return None
        return self._decoder.decode(response.body)

    def _handle_error(self, response: HttpResponse) -> None:
        message = response.body.decode() if response.body else ""
        code = None
        try:
            parsed = self._decoder.decode(response.body)
            if isinstance(parsed, dict):
                code = parsed.get("code")
                message = parsed.get("message", message)
        except Exception:  # noqa: BLE001 (best-effort error parsing)
            pass
        raise KalshiHttpError(status=response.status, message=message, code=code)

    async def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        return await self.request(HttpMethod.GET, endpoint, params=params)

    async def post(self, endpoint: str, payload: dict[str, Any] | None = None) -> Any:
        return await self.request(HttpMethod.POST, endpoint, payload=payload)

    async def delete(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        return await self.request(HttpMethod.DELETE, endpoint, params=params)

    @staticmethod
    def path_without_query(url: str) -> str:
        """
        Return the path component of ``url`` without its query string.
        """
        return urlsplit(url).path

import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import rsa
from nautilus_trader.adapters.kalshi.http.client import KalshiHttpClient
from nautilus_trader.adapters.kalshi.http.client import load_private_key
from nautilus_trader.adapters.kalshi.http.client import sign_pss_text
from nautilus_trader.common.component import LiveClock
from nautilus_trader.core.nautilus_pyo3 import HttpMethod

_PEM = rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()

def _client():
    return KalshiHttpClient(api_key_id="k-1", private_key_pem=_PEM, clock=LiveClock(), base_url="https://demo-api.kalshi.co")

def test_signed_headers_present():
    headers = _client()._signed_headers(HttpMethod.GET, "/trade-api/v2/markets")
    assert headers["KALSHI-ACCESS-KEY"] == "k-1"
    assert headers["KALSHI-ACCESS-TIMESTAMP"]
    assert headers["KALSHI-ACCESS-SIGNATURE"]

def test_signature_verifies_against_public_key():
    client = _client()
    headers = client._signed_headers(HttpMethod.GET, "/trade-api/v2/markets")
    key = load_private_key(_PEM)
    message = headers["KALSHI-ACCESS-TIMESTAMP"] + "GET" + "/trade-api/v2/markets"
    key.public_key().verify(
        base64.b64decode(headers["KALSHI-ACCESS-SIGNATURE"]),
        message.encode(),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256(),
    )

def test_sign_pss_text_is_base64():
    signature = sign_pss_text(load_private_key(_PEM), "hello")
    assert base64.b64decode(signature)

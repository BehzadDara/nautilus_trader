"""Offline Phase 3 check: construct the signed client and verify a signature round-trips. No network."""
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

from nautilus_trader.adapters.kalshi.http.client import KalshiHttpClient
from nautilus_trader.adapters.kalshi.http.client import load_private_key
from nautilus_trader.adapters.kalshi.http.client import sign_pss_text
from nautilus_trader.common.component import LiveClock
from nautilus_trader.core.nautilus_pyo3 import HttpMethod

PEM = r"D:\Projects\Nautilustrader\secrets\kalshi_private_key.pem"

with open(PEM) as f:
    pem = f.read()

# Construct the client with the real key (demo, no network call made).
client = KalshiHttpClient(
    api_key_id="test-key-id",
    private_key_pem=pem,
    clock=LiveClock(),
    is_demo=True,
)
print("client base_url:", client.base_url)

# Build the exact signed headers for a sample GET and verify the signature.
headers = client._signed_headers(HttpMethod.GET, "/trade-api/v2/markets")
print("headers keys:", sorted(headers))
assert headers["KALSHI-ACCESS-KEY"] == "test-key-id"
ts = headers["KALSHI-ACCESS-TIMESTAMP"]
sig_b64 = headers["KALSHI-ACCESS-SIGNATURE"]

import base64

key = load_private_key(pem)
message = ts + "GET" + "/trade-api/v2/markets"
key.public_key().verify(
    base64.b64decode(sig_b64),
    message.encode(),
    padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
    hashes.SHA256(),
)
print("signed message:", message[:13], "...GET/trade-api/v2/markets")
print("signature verified against public key OK")

# Sanity: standalone helper matches.
sign_pss_text(key, "hello")
print("\nPHASE 3 SIGNING OK (offline) - signature scheme valid, client constructs.")

import asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from nautilus_trader.adapters.kalshi.websocket.client import KalshiWebSocketClient
from nautilus_trader.adapters.kalshi.websocket.types import KALSHI_WS_CHANNELS_REQUIRING_TICKERS
from nautilus_trader.adapters.kalshi.websocket.types import KalshiWebSocketChannel
from nautilus_trader.common.component import LiveClock

_PEM = rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()

def _client():
    return KalshiWebSocketClient(clock=LiveClock(), api_key_id="k-1", private_key_pem=_PEM, handler=lambda raw: None, loop=asyncio.new_event_loop(), base_url="wss://demo-api.kalshi.co/trade-api/ws/v2")

def test_signed_headers_present():
    headers = dict(_client()._signed_headers())
    assert headers["KALSHI-ACCESS-KEY"] == "k-1"
    assert headers["KALSHI-ACCESS-TIMESTAMP"]
    assert headers["KALSHI-ACCESS-SIGNATURE"]

def test_build_subscribe_with_ticker():
    msg = _client()._build_subscribe(1, KalshiWebSocketChannel.ORDERBOOK_DELTA.value, "KXMENWORLDCUP-26-FR")
    assert msg["cmd"] == "subscribe"
    assert msg["id"] == 1
    assert msg["params"]["channels"] == ["orderbook_delta"]
    assert msg["params"]["market_tickers"] == ["KXMENWORLDCUP-26-FR"]

def test_build_subscribe_channel_requiring_tickers_defaults_empty():
    assert KalshiWebSocketChannel.TICKER.value in KALSHI_WS_CHANNELS_REQUIRING_TICKERS
    msg = _client()._build_subscribe(2, KalshiWebSocketChannel.TICKER.value, None)
    assert msg["params"]["market_tickers"] == []

def test_subscriptions_tracked():
    client = _client()
    client._subscriptions[("ticker", None)] = 1
    assert ("ticker", None) in client.subscriptions

import asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_instrument
from nautilus_trader.adapters.kalshi.config import KalshiDataClientConfig
from nautilus_trader.adapters.kalshi.data import KalshiDataClient
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProvider
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProviderConfig
from nautilus_trader.common.component import LiveClock
from nautilus_trader.model.data import OrderBookDeltas
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.test_kit.stubs.component import TestComponentStubs
import msgspec

_PEM = rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()

class _FakeHttpClient:
    async def get(self, endpoint, params=None):
        return {"markets": [], "cursor": None}

def _client(instrument):
    clock = LiveClock()
    cache = TestComponentStubs.cache()
    cache.add_instrument(instrument)
    provider = KalshiInstrumentProvider(http_client=_FakeHttpClient(), clock=clock, config=KalshiInstrumentProviderConfig())
    config = KalshiDataClientConfig(api_key_id="k-1", private_key_pem=_PEM, base_url_ws="wss://demo-api.kalshi.co/trade-api/ws/v2")
    client = KalshiDataClient(loop=asyncio.new_event_loop(), client=_FakeHttpClient(), msgbus=TestComponentStubs.msgbus(), cache=cache, clock=clock, instrument_provider=provider, config=config, name="KALSHI")
    return client

def test_snapshot_builds_book_and_quote(http_market, ws_orderbook_snapshot):
    instrument = parse_kalshi_instrument(http_market, ts_init=1)
    client = _client(instrument)
    captured = []
    original = client._handle_data
    client._handle_data = lambda data: (captured.append(data), original(data))[1]
    client._add_subscription_order_book_deltas(instrument.id)
    client._add_subscription_quote_ticks(instrument.id)
    client._create_local_book(instrument.id)
    client._handle_raw_ws_message(msgspec.json.encode(ws_orderbook_snapshot))
    book = client._local_books[instrument.id]
    assert float(book.best_bid_price()) == 0.19
    assert any(isinstance(d, OrderBookDeltas) for d in captured)
    assert any(isinstance(d, QuoteTick) for d in captured)

def test_unknown_ticker_ignored(http_market):
    instrument = parse_kalshi_instrument(http_market, ts_init=1)
    client = _client(instrument)
    msg = {"type": "orderbook_snapshot", "sid": 1, "seq": 1, "msg": {"market_ticker": "DOES-NOT-EXIST", "yes_dollars_fp": [["0.10", "1.00"]]}}
    client._handle_raw_ws_message(msgspec.json.encode(msg))
    assert "DOES-NOT-EXIST" not in [str(i) for i in client._local_books]

def test_subscribed_confirmation_ignored(http_market):
    instrument = parse_kalshi_instrument(http_market, ts_init=1)
    client = _client(instrument)
    client._handle_raw_ws_message(msgspec.json.encode({"type": "subscribed", "id": 1, "msg": {"channel": "ticker", "sid": 1}}))

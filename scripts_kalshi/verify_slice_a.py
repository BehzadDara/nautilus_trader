import os
import sys
import tempfile
import asyncio

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != _REPO]
os.environ.setdefault("KALSHI_ENV_FILE", os.path.join(_REPO, ".env"))
os.chdir(tempfile.gettempdir())

from nautilus_trader.adapters.kalshi.common.credentials import get_kalshi_api_key_id
from nautilus_trader.adapters.kalshi.common.credentials import get_kalshi_private_key_pem
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_instrument_id
from nautilus_trader.adapters.kalshi.config import KalshiDataClientConfig
from nautilus_trader.adapters.kalshi.data import KalshiDataClient
from nautilus_trader.adapters.kalshi.http.client import KalshiHttpClient
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProvider
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProviderConfig
from nautilus_trader.common.component import LiveClock
from nautilus_trader.model.data import OrderBookDeltas
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.instruments import BinaryOption
from nautilus_trader.test_kit.stubs.component import TestComponentStubs

RUN_SECS = int(os.environ.get("VERIFY_SECS", "20"))

def pick_busiest(markets):
    return sorted(markets, key=lambda m: float(m.get("volume_24h_fp") or 0), reverse=True)

async def main() -> None:
    clock = LiveClock()
    api_key_id = get_kalshi_api_key_id()
    pem = get_kalshi_private_key_pem()

    http = KalshiHttpClient(api_key_id=api_key_id, private_key_pem=pem, clock=clock)

    print("[1] Loading instruments via provider ...")
    provider = KalshiInstrumentProvider(http_client=http, clock=clock, config=KalshiInstrumentProviderConfig(load_status="open"))
    page = await http.get("/markets", params={"limit": 500, "status": "open"})
    busiest = pick_busiest(page["markets"])
    target = os.environ.get("VERIFY_TICKER") or busiest[0]["ticker"]
    await provider.load_async(get_kalshi_instrument_id(target))
    instrument = provider.find(get_kalshi_instrument_id(target))
    assert isinstance(instrument, BinaryOption)
    print(f"    OK - {instrument.id}")
    print(f"    question : {instrument.description}")
    print(f"    tick={instrument.price_increment} | expiry_ns={instrument.expiration_ns}")

    cache = TestComponentStubs.cache()
    msgbus = TestComponentStubs.msgbus()
    cache.add_instrument(instrument)

    config = KalshiDataClientConfig(api_key_id=api_key_id, private_key_pem=pem)
    client = KalshiDataClient(loop=asyncio.get_event_loop(), client=http, msgbus=msgbus, cache=cache, clock=clock, instrument_provider=provider, config=config, name="KALSHI")

    captured = {"book": 0, "quote": 0, "trade": 0}
    original_handle_data = client._handle_data

    def capture(data):
        if isinstance(data, OrderBookDeltas):
            captured["book"] += 1
            if captured["book"] <= 2:
                print(f"    [BOOK] {len(data.deltas)} delta(s) seq={data.sequence}")
        elif isinstance(data, QuoteTick):
            captured["quote"] += 1
            if captured["quote"] <= 5:
                print(f"    [QUOTE] bid={data.bid_price}x{data.bid_size}  ask={data.ask_price}x{data.ask_size}")
        elif isinstance(data, TradeTick):
            captured["trade"] += 1
            print(f"    [TRADE] price={data.price} size={data.size} side={data.aggressor_side} id={data.trade_id}")
        return original_handle_data(data)

    client._handle_data = capture

    raw_count = {"n": 0}
    original_raw = client._handle_raw_ws_message

    def raw_tap(raw: bytes) -> None:
        raw_count["n"] += 1
        if os.environ.get("VERIFY_RAW") and raw_count["n"] <= 4:
            print(f"    [RAW] {raw.decode(errors='replace')[:200]}")
        return original_raw(raw)

    client._handle_raw_ws_message = raw_tap
    client._ws_client._handler = raw_tap

    client._add_subscription_order_book_deltas(instrument.id)
    client._add_subscription_quote_ticks(instrument.id)
    client._add_subscription_trade_ticks(instrument.id)
    client._create_local_book(instrument.id)

    print(f"[2] Subscribing live (order book + quotes + trades) on {target} ...")
    await client._ws_client.subscribe("orderbook_delta", market_ticker=target)
    await client._ws_client.subscribe("trade", market_ticker=target)
    await client._ws_client.connect()
    print(f"    connected={client._ws_client.is_connected()} ; listening {RUN_SECS}s ...")

    await asyncio.sleep(RUN_SECS)
    await client._ws_client.disconnect()

    book = client._local_books.get(instrument.id)
    best_bid = book.best_bid_price() if book is not None else None
    best_ask = book.best_ask_price() if book is not None else None
    print("\n[3] Results")
    print(f"    raw messages  : {raw_count['n']}")
    print(f"    book messages : {captured['book']}")
    print(f"    quote ticks   : {captured['quote']}")
    print(f"    trade ticks   : {captured['trade']}")
    print(f"    final best_bid: {best_bid}   best_ask: {best_ask}")
    if raw_count["n"] == 0:
        print("    note: no websocket traffic this run (demo can be slow/flaky); raise VERIFY_SECS and retry")
    elif best_bid is None and best_ask is None:
        print("    note: this market's book is empty/one-sided; try VERIFY_TICKER on a busier market")

    ok = captured["book"] >= 1 and (best_bid is not None or best_ask is not None)
    print("\nSLICE A OK - instrument loaded, WS connected, book parsed and applied" if ok else "\nSLICE A CHECK FAILED - no book levels parsed (no data received from venue)")

if __name__ == "__main__":
    asyncio.run(main())

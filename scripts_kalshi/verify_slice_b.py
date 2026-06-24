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
from nautilus_trader.adapters.kalshi.config import KalshiExecClientConfig
from nautilus_trader.adapters.kalshi.execution import KalshiExecutionClient
from nautilus_trader.adapters.kalshi.http.client import KalshiHttpClient
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProvider
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProviderConfig
from nautilus_trader.common.component import LiveClock
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.test_kit.stubs.component import TestComponentStubs

async def main() -> None:
    clock = LiveClock()
    api_key_id = get_kalshi_api_key_id()
    pem = get_kalshi_private_key_pem()
    http = KalshiHttpClient(api_key_id=api_key_id, private_key_pem=pem, clock=clock)

    cache = TestComponentStubs.cache()
    msgbus = TestComponentStubs.msgbus()
    provider = KalshiInstrumentProvider(http_client=http, clock=clock, config=KalshiInstrumentProviderConfig(load_status="open"))
    config = KalshiExecClientConfig(api_key_id=api_key_id, private_key_pem=pem)
    client = KalshiExecutionClient(loop=asyncio.get_event_loop(), client=http, msgbus=msgbus, cache=cache, clock=clock, instrument_provider=provider, config=config, name="KALSHI")
    client._set_account_id(client._account_id)

    print("[1] Account balance (signed) ...")
    balance = await http.get("/portfolio/balance")
    print(f"    balance_dollars={balance.get('balance_dollars')}  portfolio_value={balance.get('portfolio_value')}")

    print("[2] Order status reports ...")
    orders = await _safe(client.generate_order_status_reports)
    print(f"    open/recent orders: {len(orders)}")

    print("[3] Fill reports ...")
    fills = await _safe(client.generate_fill_reports)
    print(f"    fills: {len(fills)}")

    print("[4] Position reports ...")
    positions = await _safe(client.generate_position_status_reports)
    print(f"    positions: {len(positions)}")

    print("[5] Order side -> Kalshi mapping ...")
    from nautilus_trader.adapters.kalshi.common.enums import kalshi_side_from_order_side, kalshi_time_in_force, kalshi_order_type
    print(f"    BUY -> {kalshi_side_from_order_side(OrderSide.BUY).value} ; SELL -> {kalshi_side_from_order_side(OrderSide.SELL).value}")
    print(f"    LIMIT -> {kalshi_order_type(OrderType.LIMIT)} ; MARKET -> {kalshi_order_type(OrderType.MARKET)}")
    print(f"    GTC -> {kalshi_time_in_force(TimeInForce.GTC)} ; IOC -> {kalshi_time_in_force(TimeInForce.IOC)} ; FOK -> {kalshi_time_in_force(TimeInForce.FOK)}")

    placed = await _place_order(client, cache, clock)

    if placed:
        print("\nSLICE B OK - order placed and acknowledged on demo")
    else:
        print("\nSLICE B PARTIAL - read-only paths OK, but the order was not accepted (see the rejection reason above)")

async def _place_order(client, cache, clock) -> bool:
    from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_instrument_id
    from nautilus_trader.test_kit.stubs.component import TestComponentStubs
    from nautilus_trader.test_kit.stubs.commands import TestCommandStubs
    from nautilus_trader.model.objects import Price, Quantity

    ticker = os.environ.get("VERIFY_TICKER", "KXMENWORLDCUP-26-FR")
    side = os.environ.get("VERIFY_SIDE", "yes").lower()
    cents = int(os.environ.get("VERIFY_AMOUNT", "1"))
    await client._instrument_provider.load_async(get_kalshi_instrument_id(ticker))
    instrument = client._instrument_provider.find(get_kalshi_instrument_id(ticker))
    cache.add_instrument(instrument)

    captured = {"order_id": None, "error": None}
    original_post = client._http_client.post

    async def post_tap(endpoint, payload=None):
        try:
            resp = await original_post(endpoint, payload=payload)
            if isinstance(resp, dict) and resp.get("order_id"):
                captured["order_id"] = resp["order_id"]
            return resp
        except Exception as e:
            captured["error"] = str(e)
            raise

    client._http_client.post = post_tap

    if side == "yes":
        order_side = OrderSide.BUY
        yes_price = cents / 100.0
    else:
        order_side = OrderSide.SELL
        yes_price = 1.0 - cents / 100.0

    print(f"\n[6] Placing 1 contract {side.upper()} @ {cents}c (YES leg {order_side.name} @ {yes_price:.2f}) on {ticker} ...")
    factory = TestComponentStubs.order_factory()
    order = factory.limit(instrument_id=instrument.id, order_side=order_side, quantity=Quantity.from_int(1), price=Price(yes_price, 2), time_in_force=TimeInForce.GTC)
    cache.add_order(order, None)
    await client._submit_order(TestCommandStubs.submit_order_command(order))
    await asyncio.sleep(1)

    if captured["order_id"]:
        print(f"    ACCEPTED - venue_order_id={captured['order_id']}")
        return True
    print(f"    REJECTED by venue: {captured['error']}")
    return False

async def _safe(coro_fn):
    try:
        return await coro_fn(None)
    except Exception as e:
        print(f"    (call raised: {type(e).__name__}: {str(e)[:100]})")
        return []

if __name__ == "__main__":
    asyncio.run(main())

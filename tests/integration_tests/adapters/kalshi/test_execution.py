from nautilus_trader.adapters.kalshi.common.enums import kalshi_order_type
from nautilus_trader.adapters.kalshi.common.enums import kalshi_side_from_order_side
from nautilus_trader.adapters.kalshi.common.enums import kalshi_time_in_force
from nautilus_trader.adapters.kalshi.common.enums import order_side_from_kalshi_side
from nautilus_trader.adapters.kalshi.common.enums import order_status_from_kalshi
from nautilus_trader.adapters.kalshi.common.symbol import yes_price_from_outcome_price
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderStatus
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import TimeInForce
from decimal import Decimal
import pytest

def test_yes_price_buy_is_unchanged():
    assert yes_price_from_outcome_price(Decimal("0.40"), OrderSide.BUY) == Decimal("0.40")

def test_yes_price_sell_is_inverted():
    assert yes_price_from_outcome_price(Decimal("0.40"), OrderSide.SELL) == Decimal("0.60")
    assert yes_price_from_outcome_price(Decimal("0.01"), OrderSide.SELL) == Decimal("0.99")

@pytest.mark.parametrize("price", ["0", "1", "-0.1", "1.5"])
def test_yes_price_out_of_range_raises(price):
    with pytest.raises(ValueError):
        yes_price_from_outcome_price(Decimal(price), OrderSide.BUY)

def test_side_mapping():
    assert kalshi_side_from_order_side(OrderSide.BUY).value == "bid"
    assert kalshi_side_from_order_side(OrderSide.SELL).value == "ask"
    assert order_side_from_kalshi_side("bid") == OrderSide.BUY
    assert order_side_from_kalshi_side("ask") == OrderSide.SELL

def test_order_type_mapping():
    assert kalshi_order_type(OrderType.LIMIT) == "limit"
    assert kalshi_order_type(OrderType.MARKET) == "market"

def test_time_in_force_mapping():
    assert kalshi_time_in_force(TimeInForce.GTC) == "good_till_canceled"
    assert kalshi_time_in_force(TimeInForce.IOC) == "immediate_or_cancel"
    assert kalshi_time_in_force(TimeInForce.FOK) == "fill_or_kill"

def test_unsupported_time_in_force_raises():
    with pytest.raises(ValueError):
        kalshi_time_in_force(TimeInForce.DAY)

def test_order_status_mapping():
    assert order_status_from_kalshi("resting") == OrderStatus.ACCEPTED
    assert order_status_from_kalshi("canceled") == OrderStatus.CANCELED
    assert order_status_from_kalshi("executed") == OrderStatus.FILLED

import asyncio
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_instrument
from nautilus_trader.adapters.kalshi.config import KalshiExecClientConfig
from nautilus_trader.adapters.kalshi.execution import KalshiExecutionClient
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProvider
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProviderConfig
from nautilus_trader.common.component import LiveClock
from nautilus_trader.test_kit.stubs.component import TestComponentStubs

_PEM = rsa.generate_private_key(public_exponent=65537, key_size=2048).private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()

class _FakeHttpClient:
    async def get(self, endpoint, params=None):
        return {"markets": [], "cursor": None}

def _exec_client(instrument):
    clock = LiveClock()
    cache = TestComponentStubs.cache()
    cache.add_instrument(instrument)
    provider = KalshiInstrumentProvider(http_client=_FakeHttpClient(), clock=clock, config=KalshiInstrumentProviderConfig())
    config = KalshiExecClientConfig(api_key_id="k-1", private_key_pem=_PEM)
    return KalshiExecutionClient(loop=asyncio.new_event_loop(), client=_FakeHttpClient(), msgbus=TestComponentStubs.msgbus(), cache=cache, clock=clock, instrument_provider=provider, config=config, name="KALSHI")

def _build(http_market, market, price, count=1):
    instrument = parse_kalshi_instrument(http_market, ts_init=1)
    client = _exec_client(instrument)
    return asyncio.run(client.build_limit_order(market, price=price, quantity=count, order_factory=TestComponentStubs.order_factory()))

def test_build_limit_order_yes_string(http_market):
    ticker = http_market["ticker"]
    order = _build(http_market, f"{ticker}_yes.KALSHI", "0.40")
    assert order.side == OrderSide.BUY
    assert float(order.price) == 0.40

def test_build_limit_order_no_string_inverts_price(http_market):
    ticker = http_market["ticker"]
    order = _build(http_market, f"{ticker}_no.KALSHI", "0.40")
    assert order.side == OrderSide.SELL
    assert float(order.price) == 0.60

def test_build_limit_order_bare_ticker_defaults_to_yes(http_market):
    order = _build(http_market, http_market["ticker"], "0.40")
    assert order.side == OrderSide.BUY

def test_build_limit_order_same_instrument_both_sides(http_market):
    ticker = http_market["ticker"]
    yes = _build(http_market, f"{ticker}_yes.KALSHI", "0.40")
    no = _build(http_market, f"{ticker}_no.KALSHI", "0.40")
    assert yes.instrument_id == no.instrument_id
    assert float(yes.price) + float(no.price) == 1.0

def test_build_limit_order_unknown_market_raises(http_market):
    with pytest.raises(ValueError):
        _build(http_market, "KXDOESNOTEXIST-99_yes.KALSHI", "0.40")

def test_order_report_fields(http_order):
    assert http_order["order_id"]
    assert http_order["book_side"] in ("bid", "ask")
    assert float(http_order["initial_count_fp"]) > 0
    assert float(http_order["yes_price_dollars"]) >= 0

def test_fill_report_fields(http_fill):
    assert http_fill["order_id"]
    assert float(http_fill["count_fp"]) > 0
    assert http_fill["book_side"] in ("bid", "ask")

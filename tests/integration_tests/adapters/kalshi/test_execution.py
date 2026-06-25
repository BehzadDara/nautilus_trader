from nautilus_trader.adapters.kalshi.common.enums import kalshi_order_type
from nautilus_trader.adapters.kalshi.common.enums import kalshi_side_from_order_side
from nautilus_trader.adapters.kalshi.common.enums import kalshi_time_in_force
from nautilus_trader.adapters.kalshi.common.enums import order_side_from_kalshi_side
from nautilus_trader.adapters.kalshi.common.enums import order_status_from_kalshi
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.enums import OrderStatus
from nautilus_trader.model.enums import OrderType
from nautilus_trader.model.enums import TimeInForce
import pytest

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

def test_order_report_fields(http_order):
    assert http_order["order_id"]
    assert http_order["book_side"] in ("bid", "ask")
    assert float(http_order["initial_count_fp"]) > 0
    assert float(http_order["yes_price_dollars"]) >= 0

def test_fill_report_fields(http_fill):
    assert http_fill["order_id"]
    assert float(http_fill["count_fp"]) > 0
    assert http_fill["book_side"] in ("bid", "ask")

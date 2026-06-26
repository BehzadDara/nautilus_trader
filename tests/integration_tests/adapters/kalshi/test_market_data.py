from nautilus_trader.adapters.kalshi.common.parsing import kalshi_candle_period_minutes
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_candle
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_instrument
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_lifecycle
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_rest_orderbook
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_rest_trade
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_instrument_id
from nautilus_trader.model.book import OrderBook
from nautilus_trader.model.data import Bar
from nautilus_trader.model.data import BarType
from nautilus_trader.model.data import InstrumentStatus
from nautilus_trader.model.data import TradeTick
from nautilus_trader.model.enums import BarAggregation
from nautilus_trader.model.enums import BookType
from nautilus_trader.model.enums import MarketStatusAction
import pytest

def _instrument(http_market):
    return parse_kalshi_instrument(http_market, ts_init=1)

def test_rest_orderbook_builds_book(http_market, http_orderbook):
    instrument = _instrument(http_market)
    ob = http_orderbook.get("orderbook_fp") or http_orderbook.get("orderbook") or {}
    deltas = parse_kalshi_rest_orderbook(instrument, ob, 2, 3)
    book = OrderBook(instrument.id, book_type=BookType.L2_MBP)
    book.apply_deltas(deltas)
    assert book.best_bid_price() is not None or book.best_ask_price() is not None

def test_rest_trade(http_market, http_trade):
    instrument = _instrument(http_market)
    trade = parse_kalshi_rest_trade(instrument, http_trade, ts_init=3)
    assert isinstance(trade, TradeTick)
    assert float(trade.price) == float(http_trade["yes_price_dollars"])
    assert float(trade.size) == float(http_trade["count_fp"])

def test_candle(http_market, http_candlestick):
    instrument = _instrument(http_market)
    bar_type = BarType.from_str(f"{instrument.id}-1-DAY-LAST-EXTERNAL")
    bar = parse_kalshi_candle(instrument, bar_type, http_candlestick, ts_init=3)
    assert isinstance(bar, Bar)
    assert float(bar.close) == float(http_candlestick["price"]["close_dollars"])

def test_candle_period_mapping(http_market):
    instrument = _instrument(http_market)
    assert kalshi_candle_period_minutes(BarType.from_str(f"{instrument.id}-1-MINUTE-LAST-EXTERNAL")) == 1
    assert kalshi_candle_period_minutes(BarType.from_str(f"{instrument.id}-1-HOUR-LAST-EXTERNAL")) == 60
    assert kalshi_candle_period_minutes(BarType.from_str(f"{instrument.id}-1-DAY-LAST-EXTERNAL")) == 1440

def test_candle_period_unsupported_raises(http_market):
    instrument = _instrument(http_market)
    with pytest.raises(ValueError):
        kalshi_candle_period_minutes(BarType.from_str(f"{instrument.id}-1-SECOND-LAST-EXTERNAL"))

def test_lifecycle_status_mapping():
    iid = get_kalshi_instrument_id("KXMENWORLDCUP-26-FR")
    assert parse_kalshi_lifecycle(iid, {"status": "open"}, 1, 2).action == MarketStatusAction.TRADING
    assert parse_kalshi_lifecycle(iid, {"status": "paused"}, 1, 2).action == MarketStatusAction.PAUSE
    assert parse_kalshi_lifecycle(iid, {"status": "closed"}, 1, 2).action == MarketStatusAction.CLOSE
    assert isinstance(parse_kalshi_lifecycle(iid, {"status": "open"}, 1, 2), InstrumentStatus)

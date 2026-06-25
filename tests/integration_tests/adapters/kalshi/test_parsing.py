from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_book_delta
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_book_snapshot
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_instrument
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_trade
from nautilus_trader.model.book import OrderBook
from nautilus_trader.model.enums import AggressorSide
from nautilus_trader.model.enums import BookAction
from nautilus_trader.model.enums import BookType
from nautilus_trader.model.instruments import BinaryOption

def test_parse_instrument(http_market):
    instrument = parse_kalshi_instrument(http_market, ts_init=1)
    assert isinstance(instrument, BinaryOption)
    assert instrument.id.symbol.value == http_market["ticker"]
    assert instrument.outcome == http_market["yes_sub_title"]
    assert str(instrument.price_increment) == "0.0100"
    assert instrument.expiration_ns > 0

def test_parse_instrument_missing_expiration_uses_fallback():
    market = {"ticker": "X-1", "title": "t", "yes_sub_title": "Yes", "price_ranges": [{"step": "0.01"}]}
    instrument = parse_kalshi_instrument(market, ts_init=1)
    assert instrument.expiration_ns > 0

def _instrument(http_market):
    return parse_kalshi_instrument(http_market, ts_init=1)

def test_parse_book_snapshot_yes_no_transform(http_market, ws_orderbook_snapshot):
    instrument = _instrument(http_market)
    deltas = parse_kalshi_book_snapshot(instrument, ws_orderbook_snapshot["msg"], 1, 2, 3)
    assert deltas.deltas[0].action == BookAction.CLEAR
    book = OrderBook(instrument.id, book_type=BookType.L2_MBP)
    book.apply_deltas(deltas)
    assert float(book.best_bid_price()) == 0.19
    assert float(book.best_ask_price()) == round(1.0 - 0.84, 2)

def test_parse_book_delta_no_side_becomes_ask(http_market):
    instrument = _instrument(http_market)
    msg = {"market_ticker": instrument.id.symbol.value, "side": "no", "price_dollars": "0.8400", "delta_fp": "10.00"}
    deltas = parse_kalshi_book_delta(instrument, msg, 5, 2, 3)
    delta = deltas.deltas[0]
    assert float(delta.order.price) == round(1.0 - 0.84, 2)

def test_parse_trade(http_market):
    instrument = _instrument(http_market)
    msg = {"market_ticker": instrument.id.symbol.value, "yes_price_dollars": "0.1600", "count_fp": "3.00", "taker_side": "yes"}
    trade = parse_kalshi_trade(instrument, msg, 7, 2, 3)
    assert float(trade.price) == 0.16
    assert float(trade.size) == 3
    assert trade.aggressor_side == AggressorSide.BUYER

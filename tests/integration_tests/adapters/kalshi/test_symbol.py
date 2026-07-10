from nautilus_trader.adapters.kalshi.common.constants import KALSHI_VENUE
from nautilus_trader.adapters.kalshi.common.symbol import KalshiMarket
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_instrument_id
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_ticker
from nautilus_trader.adapters.kalshi.common.symbol import kalshi_outcome_to_order_side
from nautilus_trader.adapters.kalshi.common.symbol import order_side_to_kalshi_outcome
from nautilus_trader.adapters.kalshi.common.symbol import parse_kalshi_market
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
import pytest

TICKER = "KXMENWORLDCUP-26-FR"

def test_instrument_id_from_ticker():
    instrument_id = get_kalshi_instrument_id(TICKER)
    assert instrument_id.symbol.value == TICKER
    assert instrument_id.venue == KALSHI_VENUE

def test_ticker_round_trip():
    assert get_kalshi_ticker(get_kalshi_instrument_id(TICKER)) == TICKER

def test_round_trip_long_ticker():
    ticker = "KXATPCHALLENGERMATCH-26JUN15FILWAZ-WAZ"
    assert get_kalshi_ticker(get_kalshi_instrument_id(ticker)) == ticker

def test_outcome_side_mapping():
    assert kalshi_outcome_to_order_side("yes") == OrderSide.BUY
    assert kalshi_outcome_to_order_side("NO") == OrderSide.SELL
    assert order_side_to_kalshi_outcome(OrderSide.BUY) == "yes"
    assert order_side_to_kalshi_outcome(OrderSide.SELL) == "no"

def test_outcome_invalid_raises():
    with pytest.raises(ValueError):
        kalshi_outcome_to_order_side("maybe")

DOTTED = "KXTRUMPVH-26JUL17-T40.8"

@pytest.mark.parametrize(
    ("value", "side"),
    [
        (f"{TICKER}_yes.KALSHI", OrderSide.BUY),
        (f"{TICKER}_no.KALSHI", OrderSide.SELL),
        (f"{TICKER}_yes", OrderSide.BUY),
        (f"{TICKER}_no", OrderSide.SELL),
        (f"{TICKER}_YES.kalshi", OrderSide.BUY),
        (f"  {TICKER}_no.KALSHI  ", OrderSide.SELL),
    ],
)
def test_parse_shorthand_with_side(value, side):
    market = parse_kalshi_market(value)
    assert market.instrument_id == get_kalshi_instrument_id(TICKER)
    assert market.side == side

@pytest.mark.parametrize("value", [TICKER, f"{TICKER}.KALSHI", f"{TICKER}.kalshi"])
def test_parse_shorthand_without_side(value):
    market = parse_kalshi_market(value)
    assert market.instrument_id == get_kalshi_instrument_id(TICKER)
    assert market.side is None

@pytest.mark.parametrize(
    ("value", "side"),
    [
        (DOTTED, None),
        (f"{DOTTED}_yes", OrderSide.BUY),
        (f"{DOTTED}_no.KALSHI", OrderSide.SELL),
        (f"{DOTTED}.KALSHI", None),
    ],
)
def test_parse_ticker_containing_dot(value, side):
    market = parse_kalshi_market(value)
    assert market.ticker == DOTTED
    assert market.side == side

def test_parse_default_side_applied_only_when_absent():
    assert parse_kalshi_market(TICKER, default_side=OrderSide.BUY).side == OrderSide.BUY
    assert parse_kalshi_market(f"{TICKER}_no", default_side=OrderSide.BUY).side == OrderSide.SELL

def test_yes_and_no_are_the_same_instrument():
    yes = parse_kalshi_market(f"{TICKER}_yes.KALSHI")
    no = parse_kalshi_market(f"{TICKER}_no.KALSHI")
    assert yes.instrument_id == no.instrument_id
    assert yes.side != no.side

@pytest.mark.parametrize(
    "url",
    [
        f"https://kalshi.com/markets/kxmenworldcup/world-cup?ticker={TICKER}",
        f"https://kalshi.com/markets/{TICKER}",
        f"https://demo.kalshi.co/markets/kxmenworldcup?market_ticker={TICKER}",
    ],
)
def test_parse_url(url):
    market = parse_kalshi_market(url)
    assert market.instrument_id == get_kalshi_instrument_id(TICKER)
    assert market.side is None

_REAL_URL = (
    "https://demo.kalshi.co/markets/kxmenworldcup/mens-world-cup-winner/"
    f"kxmenworldcup-26?op_market_ticker={TICKER}&op_order_side="
)

def test_parse_real_url_prefers_query_ticker_over_path():
    market = parse_kalshi_market(f"{_REAL_URL}yes")
    assert market.ticker == TICKER
    assert market.ticker != "KXMENWORLDCUP-26"
    assert market.side == OrderSide.BUY

def test_parse_real_url_no_side():
    assert parse_kalshi_market(f"{_REAL_URL}no").side == OrderSide.SELL

def test_parse_real_url_side_overrides_default():
    market = parse_kalshi_market(f"{_REAL_URL}no", default_side=OrderSide.BUY)
    assert market.side == OrderSide.SELL

def test_parse_url_without_side_uses_default():
    url = f"https://demo.kalshi.co/markets/kxmenworldcup?op_market_ticker={TICKER}"
    assert parse_kalshi_market(url).side is None
    assert parse_kalshi_market(url, default_side=OrderSide.SELL).side == OrderSide.SELL

def test_parse_url_invalid_side_raises():
    with pytest.raises(ValueError):
        parse_kalshi_market(f"{_REAL_URL}maybe")

def test_parse_url_lowercase_ticker_normalized():
    market = parse_kalshi_market(f"https://kalshi.com/markets/{TICKER.lower()}")
    assert market.ticker == TICKER

def test_parse_url_default_side():
    market = parse_kalshi_market(f"https://kalshi.com/markets/{TICKER}", default_side=OrderSide.SELL)
    assert market.side == OrderSide.SELL

@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "_",
        ".KALSHI",
        f"{TICKER}_maybe",
        f"{TICKER}_yes_no.KALSHI",
        f"{TICKER}_KALSHI",
        "bad ticker",
        "KX@BAD",
    ],
)
def test_parse_invalid_raises(value):
    with pytest.raises(ValueError):
        parse_kalshi_market(value)

def test_dot_no_longer_separates_side():
    market = parse_kalshi_market(f"{TICKER}.yes")
    assert market.side is None
    assert market.ticker == f"{TICKER}.YES"

def test_shorthand_is_a_valid_instrument_id_string():
    market = parse_kalshi_market(f"{TICKER}_no.KALSHI")
    instrument_id = InstrumentId.from_str(str(market))
    assert instrument_id.venue == KALSHI_VENUE
    assert instrument_id.symbol.value == f"{TICKER}_no"

def test_str_round_trip():
    for value in (f"{TICKER}_yes.KALSHI", f"{TICKER}_no.KALSHI", f"{TICKER}.KALSHI", f"{DOTTED}_no.KALSHI"):
        assert str(parse_kalshi_market(value)) == value

def test_market_helpers():
    market = parse_kalshi_market(f"{TICKER}_yes.KALSHI")
    assert market.ticker == TICKER
    assert market.outcome == "yes"
    assert market.with_side(OrderSide.SELL).outcome == "no"
    assert KalshiMarket(get_kalshi_instrument_id(TICKER)).outcome is None

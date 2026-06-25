from nautilus_trader.adapters.kalshi.common.constants import KALSHI_VENUE
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_instrument_id
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_ticker

def test_instrument_id_from_ticker():
    instrument_id = get_kalshi_instrument_id("KXMENWORLDCUP-26-FR")
    assert instrument_id.symbol.value == "KXMENWORLDCUP-26-FR"
    assert instrument_id.venue == KALSHI_VENUE

def test_ticker_round_trip():
    ticker = "KXMENWORLDCUP-26-FR"
    instrument_id = get_kalshi_instrument_id(ticker)
    assert get_kalshi_ticker(instrument_id) == ticker

def test_round_trip_long_ticker():
    ticker = "KXATPCHALLENGERMATCH-26JUN15FILWAZ-WAZ"
    assert get_kalshi_ticker(get_kalshi_instrument_id(ticker)) == ticker

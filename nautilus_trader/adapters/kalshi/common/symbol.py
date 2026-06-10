from nautilus_trader.adapters.kalshi.common.constants import KALSHI_VENUE
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Symbol

def get_kalshi_instrument_id(ticker: str) -> InstrumentId:
    return InstrumentId(Symbol(ticker), KALSHI_VENUE)

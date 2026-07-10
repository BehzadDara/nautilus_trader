import re
from dataclasses import dataclass
from decimal import Decimal
from urllib.parse import parse_qs
from urllib.parse import urlparse

from nautilus_trader.adapters.kalshi.common.constants import KALSHI_VENUE
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Symbol

KALSHI_OUTCOME_YES = 'yes'
KALSHI_OUTCOME_NO = 'no'

_OUTCOME_TO_SIDE = {
    KALSHI_OUTCOME_YES: OrderSide.BUY,
    KALSHI_OUTCOME_NO: OrderSide.SELL,
}
_SIDE_TO_OUTCOME = {
    OrderSide.BUY: KALSHI_OUTCOME_YES,
    OrderSide.SELL: KALSHI_OUTCOME_NO,
}

KALSHI_MARKET_SEP = '_'

_TICKER_RE = re.compile(r'^[A-Z0-9]+(?:[-.][A-Z0-9]+)*$')


def get_kalshi_instrument_id(ticker: str) -> InstrumentId:
    return InstrumentId(Symbol(ticker), KALSHI_VENUE)


def get_kalshi_ticker(instrument_id: InstrumentId) -> str:
    return instrument_id.symbol.value


def kalshi_outcome_to_order_side(outcome: str) -> OrderSide:
    try:
        return _OUTCOME_TO_SIDE[outcome.strip().lower()]
    except KeyError:
        raise ValueError(f'invalid kalshi outcome: {outcome!r}') from None


def order_side_to_kalshi_outcome(order_side: OrderSide) -> str:
    try:
        return _SIDE_TO_OUTCOME[order_side]
    except KeyError:
        raise ValueError(f'invalid order side: {order_side}') from None


def yes_price_from_outcome_price(price: Decimal, side: OrderSide) -> Decimal:
    if price <= 0 or price >= 1:
        raise ValueError(f'price must be between 0 and 1 exclusive: {price}')
    return price if side == OrderSide.BUY else Decimal(1) - price


@dataclass(frozen=True)
class KalshiMarket:
    instrument_id: InstrumentId
    side: OrderSide | None = None

    @property
    def ticker(self) -> str:
        return self.instrument_id.symbol.value

    @property
    def outcome(self) -> str | None:
        return None if self.side is None else _SIDE_TO_OUTCOME[self.side]

    def with_side(self, side: OrderSide) -> 'KalshiMarket':
        return KalshiMarket(self.instrument_id, side)

    def __str__(self) -> str:
        if self.side is None:
            return f'{self.ticker}.{KALSHI_VENUE.value}'
        return f'{self.ticker}{KALSHI_MARKET_SEP}{self.outcome}.{KALSHI_VENUE.value}'


_URL_TICKER_KEYS = ('op_market_ticker', 'market_ticker', 'ticker')
_URL_SIDE_KEYS = ('op_order_side', 'order_side', 'side')


def _parse_url(value: str) -> tuple[str, str | None]:
    parsed = urlparse(value)
    query = parse_qs(parsed.query)

    outcome = None
    for key in _URL_SIDE_KEYS:
        if query.get(key):
            outcome = query[key][0].strip().lower()
            break

    for key in _URL_TICKER_KEYS:
        if query.get(key):
            return query[key][0].strip().upper(), outcome

    segments = [s for s in parsed.path.split('/') if s]
    if not segments:
        raise ValueError(f'no kalshi ticker in url: {value!r}')
    return segments[-1].strip().upper(), outcome


def _split_shorthand(value: str) -> tuple[str, str | None]:
    suffix = f'.{KALSHI_VENUE.value}'
    if value.upper().endswith(suffix):
        value = value[: -len(suffix)]

    parts = value.split(KALSHI_MARKET_SEP)
    if not parts[0]:
        raise ValueError(f'no kalshi ticker in: {value!r}')
    if len(parts) == 1:
        return parts[0].upper(), None
    if len(parts) == 2:
        return parts[0].upper(), parts[1].lower()
    raise ValueError(f'invalid kalshi market: {value!r}')


def parse_kalshi_market(value: str, default_side: OrderSide | None = None) -> KalshiMarket:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'invalid kalshi market: {value!r}')
    value = value.strip()

    if '://' in value or 'kalshi.co' in value.lower():
        ticker, outcome = _parse_url(value)
    else:
        ticker, outcome = _split_shorthand(value)

    if not _TICKER_RE.match(ticker):
        raise ValueError(f'invalid kalshi ticker: {ticker!r}')

    side = kalshi_outcome_to_order_side(outcome) if outcome else default_side
    return KalshiMarket(get_kalshi_instrument_id(ticker), side)

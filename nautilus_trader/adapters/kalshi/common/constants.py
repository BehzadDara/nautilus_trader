from typing import Final
from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import Venue
KALSHI: Final[str] = 'KALSHI'
KALSHI_VENUE: Final[Venue] = Venue(KALSHI)
KALSHI_CLIENT_ID: Final[ClientId] = ClientId(KALSHI)
KALSHI_DEFAULT_BASE_URL_HTTP: Final[str] = 'https://demo-api.kalshi.co'
KALSHI_DEFAULT_BASE_URL_WS: Final[str] = 'wss://demo-api.kalshi.co/trade-api/ws/v2'
KALSHI_API_PATH: Final[str] = '/trade-api/v2'
KALSHI_ACCESS_KEY_HEADER: Final[str] = 'KALSHI-ACCESS-KEY'
KALSHI_ACCESS_TIMESTAMP_HEADER: Final[str] = 'KALSHI-ACCESS-TIMESTAMP'
KALSHI_ACCESS_SIGNATURE_HEADER: Final[str] = 'KALSHI-ACCESS-SIGNATURE'
KALSHI_MAX_PRICE: Final[float] = 0.99
KALSHI_MIN_PRICE: Final[float] = 0.01
KALSHI_PRICE_PRECISION: Final[int] = 2
VALID_KALSHI_TIME_IN_FORCE: Final[set[TimeInForce]] = {TimeInForce.GTC, TimeInForce.IOC, TimeInForce.FOK}
KALSHI_HTTP_RATE_LIMIT: Final[int] = 100

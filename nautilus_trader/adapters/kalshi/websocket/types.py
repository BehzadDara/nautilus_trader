from enum import Enum
from typing import Final

class KalshiWebSocketChannel(Enum):
    ORDERBOOK_DELTA = 'orderbook_delta'
    TICKER = 'ticker'
    TRADE = 'trade'
    FILL = 'fill'
    MARKET_POSITIONS = 'market_positions'
    MARKET_LIFECYCLE = 'market_lifecycle_v2'

KALSHI_WS_DATA_CHANNELS: Final[tuple[str, ...]] = (KalshiWebSocketChannel.ORDERBOOK_DELTA.value, KalshiWebSocketChannel.TICKER.value, KalshiWebSocketChannel.TRADE.value, KalshiWebSocketChannel.MARKET_LIFECYCLE.value)
KALSHI_WS_USER_CHANNELS: Final[tuple[str, ...]] = (KalshiWebSocketChannel.FILL.value, KalshiWebSocketChannel.MARKET_POSITIONS.value)
KALSHI_WS_CHANNELS_REQUIRING_TICKERS: Final[frozenset[str]] = frozenset({KalshiWebSocketChannel.ORDERBOOK_DELTA.value, KalshiWebSocketChannel.TICKER.value, KalshiWebSocketChannel.TRADE.value})

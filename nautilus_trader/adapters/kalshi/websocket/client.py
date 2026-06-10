from nautilus_trader.adapters.kalshi.common.env import get_kalshi_base_url_ws

class KalshiWebSocketClient:

    def __init__(self, base_url: str | None=None) -> None:
        self._base_url = base_url or get_kalshi_base_url_ws()

    @property
    def base_url(self) -> str:
        return self._base_url

    async def connect(self) -> None:
        raise NotImplementedError('KalshiWebSocketClient.connect')

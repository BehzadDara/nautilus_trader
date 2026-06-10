from nautilus_trader.adapters.kalshi.config import KalshiDataClientConfig
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProvider
from nautilus_trader.live.data_client import LiveMarketDataClient

class KalshiDataClient(LiveMarketDataClient):

    def __init__(self, loop, client, msgbus, cache, clock, instrument_provider: KalshiInstrumentProvider, config: KalshiDataClientConfig, name: str | None=None) -> None:
        super().__init__(loop=loop, client_id=None, venue=config.venue, msgbus=msgbus, cache=cache, clock=clock, instrument_provider=instrument_provider, config=config, name=name)
        self._http_client = client
        self._config = config

    async def _connect(self) -> None:
        raise NotImplementedError('KalshiDataClient._connect')

    async def _disconnect(self) -> None:
        raise NotImplementedError('KalshiDataClient._disconnect')

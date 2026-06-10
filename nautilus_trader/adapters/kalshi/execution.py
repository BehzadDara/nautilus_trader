from nautilus_trader.adapters.kalshi.config import KalshiExecClientConfig
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProvider
from nautilus_trader.live.execution_client import LiveExecutionClient

class KalshiExecutionClient(LiveExecutionClient):

    def __init__(self, loop, client, msgbus, cache, clock, instrument_provider: KalshiInstrumentProvider, config: KalshiExecClientConfig, name: str | None=None) -> None:
        super().__init__(loop=loop, client_id=None, venue=config.venue, oms_type=None, account_type=None, base_currency=None, instrument_provider=instrument_provider, msgbus=msgbus, cache=cache, clock=clock, config=config, name=name)
        self._http_client = client
        self._config = config

    async def _connect(self) -> None:
        raise NotImplementedError('KalshiExecutionClient._connect — Phase 7')

    async def _disconnect(self) -> None:
        raise NotImplementedError('KalshiExecutionClient._disconnect — Phase 7')

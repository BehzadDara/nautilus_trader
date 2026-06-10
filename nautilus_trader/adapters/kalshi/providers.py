from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.config import InstrumentProviderConfig

class KalshiInstrumentProviderConfig(InstrumentProviderConfig, frozen=True):
    load_series: list[str] | None = None

class KalshiInstrumentProvider(InstrumentProvider):

    def __init__(self, http_client=None, config: KalshiInstrumentProviderConfig | None=None) -> None:
        super().__init__(config=config or KalshiInstrumentProviderConfig())
        self._http_client = http_client

    async def load_all_async(self, filters: dict | None=None) -> None:
        raise NotImplementedError('KalshiInstrumentProvider.load_all_async')

    async def load_ids_async(self, instrument_ids, filters: dict | None=None) -> None:
        raise NotImplementedError('KalshiInstrumentProvider.load_ids_async')

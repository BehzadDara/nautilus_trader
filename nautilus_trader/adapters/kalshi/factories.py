import asyncio
from functools import lru_cache
from nautilus_trader.adapters.kalshi.common.credentials import get_kalshi_api_key_id
from nautilus_trader.adapters.kalshi.common.credentials import get_kalshi_private_key_pem
from nautilus_trader.adapters.kalshi.config import KalshiDataClientConfig
from nautilus_trader.adapters.kalshi.config import KalshiExecClientConfig
from nautilus_trader.adapters.kalshi.data import KalshiDataClient
from nautilus_trader.adapters.kalshi.execution import KalshiExecutionClient
from nautilus_trader.adapters.kalshi.http.client import KalshiHttpClient
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProvider
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProviderConfig
from nautilus_trader.cache.cache import Cache
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import MessageBus
from nautilus_trader.live.factories import LiveDataClientFactory
from nautilus_trader.live.factories import LiveExecClientFactory

def get_kalshi_http_client(clock: LiveClock, api_key_id: str | None=None, private_key_pem: str | None=None, base_url: str | None=None) -> KalshiHttpClient:
    return KalshiHttpClient(api_key_id=api_key_id or get_kalshi_api_key_id(), private_key_pem=private_key_pem or get_kalshi_private_key_pem(), clock=clock, base_url=base_url)

@lru_cache(maxsize=1)
def get_kalshi_instrument_provider(client: KalshiHttpClient, clock: LiveClock, config: KalshiInstrumentProviderConfig | None=None) -> KalshiInstrumentProvider:
    return KalshiInstrumentProvider(http_client=client, clock=clock, config=config or KalshiInstrumentProviderConfig())

class KalshiLiveDataClientFactory(LiveDataClientFactory):

    @staticmethod
    def create(loop: asyncio.AbstractEventLoop, name: str, config: KalshiDataClientConfig, msgbus: MessageBus, cache: Cache, clock: LiveClock) -> KalshiDataClient:
        http_client = get_kalshi_http_client(clock=clock, api_key_id=config.api_key_id, private_key_pem=config.private_key_pem, base_url=config.base_url_http)
        provider = get_kalshi_instrument_provider(client=http_client, clock=clock, config=config.instrument_provider)
        return KalshiDataClient(loop=loop, client=http_client, msgbus=msgbus, cache=cache, clock=clock, instrument_provider=provider, config=config, name=name)

class KalshiLiveExecClientFactory(LiveExecClientFactory):

    @staticmethod
    def create(loop: asyncio.AbstractEventLoop, name: str, config: KalshiExecClientConfig, msgbus: MessageBus, cache: Cache, clock: LiveClock) -> KalshiExecutionClient:
        http_client = get_kalshi_http_client(clock=clock, api_key_id=config.api_key_id, private_key_pem=config.private_key_pem, base_url=config.base_url_http)
        provider = get_kalshi_instrument_provider(client=http_client, clock=clock, config=config.instrument_provider)
        return KalshiExecutionClient(loop=loop, client=http_client, msgbus=msgbus, cache=cache, clock=clock, instrument_provider=provider, config=config, name=name)

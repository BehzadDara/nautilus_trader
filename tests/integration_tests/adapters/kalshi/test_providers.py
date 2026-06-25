import asyncio
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_instrument_id
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProvider
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProviderConfig
from nautilus_trader.common.component import LiveClock
from nautilus_trader.model.instruments import BinaryOption

class _FakeHttpClient:
    def __init__(self, market):
        self._market = market
        self._page_served = False

    async def get(self, endpoint, params=None):
        if endpoint.startswith("/markets/"):
            return {"market": self._market}
        if self._page_served:
            return {"markets": [], "cursor": None}
        self._page_served = True
        return {"markets": [self._market], "cursor": None}

def test_load_async_parses_one(http_market):
    provider = KalshiInstrumentProvider(http_client=_FakeHttpClient(http_market), clock=LiveClock(), config=KalshiInstrumentProviderConfig())
    instrument_id = get_kalshi_instrument_id(http_market["ticker"])
    asyncio.run(provider.load_async(instrument_id))
    instrument = provider.find(instrument_id)
    assert isinstance(instrument, BinaryOption)
    assert instrument.id == instrument_id

def test_load_all_async_paginates(http_market):
    provider = KalshiInstrumentProvider(http_client=_FakeHttpClient(http_market), clock=LiveClock(), config=KalshiInstrumentProviderConfig())
    asyncio.run(provider.load_all_async())
    assert len(provider.get_all()) == 1

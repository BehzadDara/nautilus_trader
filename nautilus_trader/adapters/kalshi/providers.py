from __future__ import annotations
from typing import Any
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_VENUE
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_instrument
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_ticker
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.config import InstrumentProviderConfig
from nautilus_trader.core.correctness import PyCondition
from nautilus_trader.model.identifiers import InstrumentId

KALSHI_MARKETS_PAGE_LIMIT = 1000

class KalshiInstrumentProviderConfig(InstrumentProviderConfig, frozen=True):
    load_series: list[str] | None = None
    load_status: str | None = 'open'

class KalshiInstrumentProvider(InstrumentProvider):

    def __init__(self, http_client, clock: LiveClock | None=None, config: KalshiInstrumentProviderConfig | None=None) -> None:
        super().__init__(config=config or KalshiInstrumentProviderConfig())
        self._http_client = http_client
        self._clock = clock or LiveClock()

    async def load_all_async(self, filters: dict | None=None) -> None:
        series = self._config.load_series if isinstance(self._config, KalshiInstrumentProviderConfig) else None
        status = self._config.load_status if isinstance(self._config, KalshiInstrumentProviderConfig) else None
        if series:
            for ticker in series:
                await self._load_markets_page(filters, status=status, series_ticker=ticker)
        else:
            await self._load_markets_page(filters, status=status, series_ticker=None)

    async def load_ids_async(self, instrument_ids: list[InstrumentId], filters: dict | None=None) -> None:
        if not instrument_ids:
            self._log.info('No instrument IDs given for loading')
            return
        for instrument_id in instrument_ids:
            PyCondition.equal(instrument_id.venue, KALSHI_VENUE, 'instrument_id.venue', 'KALSHI')
        for instrument_id in instrument_ids:
            await self.load_async(instrument_id, filters)

    async def load_async(self, instrument_id: InstrumentId, filters: dict | None=None) -> None:
        PyCondition.not_none(instrument_id, 'instrument_id')
        PyCondition.equal(instrument_id.venue, KALSHI_VENUE, 'instrument_id.venue', 'KALSHI')
        ticker = get_kalshi_ticker(instrument_id)
        response = await self._http_client.get(f'/markets/{ticker}')
        market = response.get('market') if response else None
        if market:
            self._add_market(market)

    async def _load_markets_page(self, filters: dict | None, status: str | None, series_ticker: str | None) -> None:
        cursor: str | None = None
        loaded = 0
        while True:
            params: dict[str, Any] = {'limit': KALSHI_MARKETS_PAGE_LIMIT}
            if status:
                params['status'] = status
            if series_ticker:
                params['series_ticker'] = series_ticker
            if cursor:
                params['cursor'] = cursor
            response = await self._http_client.get('/markets', params=params)
            markets = response.get('markets', []) if response else []
            for market in markets:
                self._add_market(market)
                loaded += 1
            cursor = response.get('cursor') if response else None
            if not cursor or not markets:
                break
        self._log.info(f'Loaded {loaded} instruments')

    def _add_market(self, market: dict[str, Any]) -> None:
        try:
            instrument = parse_kalshi_instrument(market, ts_init=self._clock.timestamp_ns())
        except (KeyError, ValueError) as e:
            self._log.error(f'Unable to parse market: {e}, {market}')
            return
        self.add(instrument)

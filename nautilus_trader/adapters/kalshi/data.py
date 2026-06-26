from __future__ import annotations
import asyncio
from typing import Any
import msgspec
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_VENUE
from nautilus_trader.adapters.kalshi.common.parsing import kalshi_candle_period_minutes
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_book_delta
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_book_snapshot
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_candle
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_lifecycle
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_rest_orderbook
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_rest_trade
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_trade
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_instrument_id
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_ticker
from nautilus_trader.adapters.kalshi.config import KalshiDataClientConfig
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProvider
from nautilus_trader.adapters.kalshi.websocket.client import KalshiWebSocketClient
from nautilus_trader.adapters.kalshi.websocket.types import KalshiWebSocketChannel
from nautilus_trader.common.enums import LogColor
from nautilus_trader.core.datetime import secs_to_nanos
from nautilus_trader.data.messages import RequestBars
from nautilus_trader.data.messages import RequestInstrument
from nautilus_trader.data.messages import RequestInstruments
from nautilus_trader.data.messages import RequestOrderBookSnapshot
from nautilus_trader.data.messages import RequestQuoteTicks
from nautilus_trader.data.messages import RequestTradeTicks
from nautilus_trader.data.messages import SubscribeBars
from nautilus_trader.data.messages import SubscribeInstruments
from nautilus_trader.data.messages import SubscribeInstrumentStatus
from nautilus_trader.data.messages import SubscribeOrderBook
from nautilus_trader.data.messages import SubscribeQuoteTicks
from nautilus_trader.data.messages import SubscribeTradeTicks
from nautilus_trader.data.messages import UnsubscribeBars
from nautilus_trader.data.messages import UnsubscribeInstruments
from nautilus_trader.data.messages import UnsubscribeInstrumentStatus
from nautilus_trader.data.messages import UnsubscribeOrderBook
from nautilus_trader.data.messages import UnsubscribeQuoteTicks
from nautilus_trader.data.messages import UnsubscribeTradeTicks
from nautilus_trader.live.data_client import LiveMarketDataClient
from nautilus_trader.model.book import OrderBook
from nautilus_trader.model.data import OrderBookDeltas
from nautilus_trader.model.data import QuoteTick
from nautilus_trader.model.enums import BookType
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import BinaryOption

class KalshiDataClient(LiveMarketDataClient):

    def __init__(self, loop: asyncio.AbstractEventLoop, client: Any, msgbus: Any, cache: Any, clock: Any, instrument_provider: KalshiInstrumentProvider, config: KalshiDataClientConfig, name: str | None=None) -> None:
        super().__init__(loop=loop, client_id=ClientId(name or KALSHI_VENUE.value), venue=config.venue, msgbus=msgbus, cache=cache, clock=clock, instrument_provider=instrument_provider, config=config)
        self._config = config
        self._http_client = client
        self._ws_client = KalshiWebSocketClient(clock=clock, api_key_id=config.api_key_id, private_key_pem=config.private_key_pem, handler=self._handle_raw_ws_message, loop=loop, base_url=config.base_url_ws, handler_reconnect=None)
        self._decoder = msgspec.json.Decoder()
        self._local_books: dict[InstrumentId, OrderBook] = {}
        self._last_quotes: dict[InstrumentId, QuoteTick] = {}
        self._update_instruments_task: asyncio.Task | None = None
        self._ws_connect_task: asyncio.Task | None = None

    async def _connect(self) -> None:
        await self._instrument_provider.initialize()
        self._send_all_instruments_to_data_engine()
        if self._config.update_instruments_interval_mins:
            self._update_instruments_task = self.create_task(self._update_instruments(self._config.update_instruments_interval_mins))

    async def _disconnect(self) -> None:
        if self._update_instruments_task:
            self._update_instruments_task.cancel()
            self._update_instruments_task = None
        if self._ws_connect_task:
            self._ws_connect_task.cancel()
            self._ws_connect_task = None
        await self._ws_client.disconnect()

    def _send_all_instruments_to_data_engine(self) -> None:
        for instrument in self._instrument_provider.get_all().values():
            self._handle_data(instrument)
        for currency in self._instrument_provider.currencies().values():
            self._cache.add_currency(currency)

    async def _update_instruments(self, interval_mins: int) -> None:
        try:
            while True:
                await asyncio.sleep(interval_mins * 60)
                await self._instrument_provider.initialize(reload=True)
                self._send_all_instruments_to_data_engine()
        except asyncio.CancelledError:
            pass

    def _create_local_book(self, instrument_id: InstrumentId) -> OrderBook:
        book = OrderBook(instrument_id, book_type=BookType.L2_MBP)
        self._local_books[instrument_id] = book
        return book

    async def _ensure_connected(self) -> None:
        if not self._ws_client.is_connected() and self._ws_connect_task is None:
            self._ws_connect_task = self.create_task(self._delayed_connect())

    async def _delayed_connect(self) -> None:
        await asyncio.sleep(self._config.ws_connection_delay_secs)
        self._ws_connect_task = None
        await self._ws_client.connect()

    async def _subscribe_order_book_deltas(self, command: SubscribeOrderBook) -> None:
        if command.book_type == BookType.L3_MBO:
            self._log.error('Cannot subscribe to order book deltas: L3_MBO is not published by Kalshi')
            return
        if self._cache.instrument(command.instrument_id) is None:
            self._log.error(f'Cannot find instrument for {command.instrument_id}')
            return
        if command.instrument_id not in self._local_books:
            self._create_local_book(command.instrument_id)
        await self._ws_client.subscribe(KalshiWebSocketChannel.ORDERBOOK_DELTA.value, market_ticker=get_kalshi_ticker(command.instrument_id))
        await self._ensure_connected()

    async def _subscribe_quote_ticks(self, command: SubscribeQuoteTicks) -> None:
        if self._cache.instrument(command.instrument_id) is None:
            self._log.error(f'Cannot find instrument for {command.instrument_id}')
            return
        if command.instrument_id not in self._local_books:
            self._create_local_book(command.instrument_id)
        await self._ws_client.subscribe(KalshiWebSocketChannel.ORDERBOOK_DELTA.value, market_ticker=get_kalshi_ticker(command.instrument_id))
        await self._ensure_connected()

    async def _subscribe_trade_ticks(self, command: SubscribeTradeTicks) -> None:
        if self._cache.instrument(command.instrument_id) is None:
            self._log.error(f'Cannot find instrument for {command.instrument_id}')
            return
        await self._ws_client.subscribe(KalshiWebSocketChannel.TRADE.value, market_ticker=get_kalshi_ticker(command.instrument_id))
        await self._ensure_connected()

    async def _unsubscribe_order_book_deltas(self, command: UnsubscribeOrderBook) -> None:
        await self._ws_client.unsubscribe(KalshiWebSocketChannel.ORDERBOOK_DELTA.value, market_ticker=get_kalshi_ticker(command.instrument_id))
        self._discard_local_state_if_unwanted(command.instrument_id)

    async def _unsubscribe_quote_ticks(self, command: UnsubscribeQuoteTicks) -> None:
        await self._ws_client.unsubscribe(KalshiWebSocketChannel.ORDERBOOK_DELTA.value, market_ticker=get_kalshi_ticker(command.instrument_id))
        self._discard_local_state_if_unwanted(command.instrument_id)

    async def _unsubscribe_trade_ticks(self, command: UnsubscribeTradeTicks) -> None:
        await self._ws_client.unsubscribe(KalshiWebSocketChannel.TRADE.value, market_ticker=get_kalshi_ticker(command.instrument_id))

    async def _subscribe_instrument_status(self, command: SubscribeInstrumentStatus) -> None:
        await self._ws_client.subscribe(KalshiWebSocketChannel.MARKET_LIFECYCLE.value)
        await self._ensure_connected()

    async def _unsubscribe_instrument_status(self, command: UnsubscribeInstrumentStatus) -> None:
        await self._ws_client.unsubscribe(KalshiWebSocketChannel.MARKET_LIFECYCLE.value)

    async def _subscribe_instruments(self, command: SubscribeInstruments) -> None:
        await self._ws_client.subscribe(KalshiWebSocketChannel.MARKET_LIFECYCLE.value)
        await self._ensure_connected()

    async def _unsubscribe_instruments(self, command: UnsubscribeInstruments) -> None:
        await self._ws_client.unsubscribe(KalshiWebSocketChannel.MARKET_LIFECYCLE.value)

    async def _subscribe_bars(self, command: SubscribeBars) -> None:
        self._log.error(f'Cannot subscribe to {command.bar_type} bars: Kalshi does not stream bars; use request_bars for candlestick history')

    async def _unsubscribe_bars(self, command: UnsubscribeBars) -> None:
        self._log.error(f'Cannot unsubscribe from {command.bar_type} bars: not streamed by Kalshi')

    def _discard_local_state_if_unwanted(self, instrument_id: InstrumentId) -> None:
        if instrument_id not in self.subscribed_order_book_deltas() and instrument_id not in self.subscribed_quote_ticks():
            self._local_books.pop(instrument_id, None)
            self._last_quotes.pop(instrument_id, None)

    async def _request_instrument(self, request: RequestInstrument) -> None:
        instrument = self._instrument_provider.find(request.instrument_id)
        if instrument is None:
            self._log.error(f'Cannot find instrument for {request.instrument_id}')
            return
        self._handle_instrument(instrument, request.id, request.start, request.end, request.params)

    async def _request_instruments(self, request: RequestInstruments) -> None:
        target = [i for i in self._instrument_provider.get_all().values() if i.venue == request.venue]
        self._handle_instruments(request.venue, target, request.id, request.start, request.end, request.params)

    async def _request_order_book_snapshot(self, request: RequestOrderBookSnapshot) -> None:
        instrument = self._cache.instrument(request.instrument_id)
        if instrument is None:
            self._log.error(f'Cannot find instrument for {request.instrument_id}')
            return
        ticker = get_kalshi_ticker(request.instrument_id)
        response = await self._http_client.get(f'/markets/{ticker}/orderbook')
        orderbook = response.get('orderbook_fp') or response.get('orderbook') or {} if response else {}
        now = self._clock.timestamp_ns()
        deltas = parse_kalshi_rest_orderbook(instrument, orderbook, now, now)
        self._handle_data(deltas)

    async def _request_quote_ticks(self, request: RequestQuoteTicks) -> None:
        self._log.error('Cannot request historical quotes: not published by Kalshi')

    async def _request_trade_ticks(self, request: RequestTradeTicks) -> None:
        instrument = self._cache.instrument(request.instrument_id)
        if instrument is None:
            self._log.error(f'Cannot find instrument for {request.instrument_id}')
            return
        ticker = get_kalshi_ticker(request.instrument_id)
        params: dict[str, Any] = {'ticker': ticker, 'limit': request.limit or 1000}
        if request.start is not None:
            params['min_ts'] = int(request.start.timestamp())
        if request.end is not None:
            params['max_ts'] = int(request.end.timestamp())
        now = self._clock.timestamp_ns()
        trades = []
        cursor = None
        while True:
            if cursor:
                params['cursor'] = cursor
            response = await self._http_client.get('/markets/trades', params=params)
            page = response.get('trades') or [] if response else []
            for trade in page:
                try:
                    trades.append(parse_kalshi_rest_trade(instrument, trade, now))
                except (KeyError, ValueError) as e:
                    self._log.warning(f'Skipping unparsable trade: {e}')
            cursor = response.get('cursor') if response else None
            if not cursor or not page or (request.limit and len(trades) >= request.limit):
                break
        self._handle_trade_ticks(request.instrument_id, trades, request.id, request.start, request.end, request.params)

    async def _request_bars(self, request: RequestBars) -> None:
        instrument = self._cache.instrument(request.bar_type.instrument_id)
        if instrument is None:
            self._log.error(f'Cannot find instrument for {request.bar_type.instrument_id}')
            return
        try:
            period = kalshi_candle_period_minutes(request.bar_type)
        except ValueError as e:
            self._log.error(f'Cannot request bars: {e}')
            return
        ticker = get_kalshi_ticker(request.bar_type.instrument_id)
        series = ticker.split('-')[0]
        end_ts = int(request.end.timestamp()) if request.end is not None else int(self._clock.timestamp_ns() / 1_000_000_000)
        start_ts = int(request.start.timestamp()) if request.start is not None else end_ts - period * 60 * 1000
        params = {'start_ts': start_ts, 'end_ts': end_ts, 'period_interval': period}
        response = await self._http_client.get(f'/series/{series}/markets/{ticker}/candlesticks', params=params)
        now = self._clock.timestamp_ns()
        bars = []
        for candle in (response.get('candlesticks') or [] if response else []):
            bar = parse_kalshi_candle(instrument, request.bar_type, candle, now)
            if bar is not None:
                bars.append(bar)
        self._handle_bars(request.bar_type, bars, request.id, request.start, request.end, request.params)

    def _handle_raw_ws_message(self, raw: bytes) -> None:
        try:
            msg = self._decoder.decode(raw)
            self._handle_ws_message(msg)
        except Exception as e:
            self._log.exception(f'Failed to parse websocket message: {raw.decode(errors="replace")}', e)

    def _handle_ws_message(self, msg: dict[str, Any]) -> None:
        msg_type = msg.get('type')
        if msg_type in ('subscribed', 'ok'):
            return
        if msg_type == 'error':
            self._log.error(f'Websocket error: {msg.get("msg")}')
            return
        body = msg.get('msg') or {}
        ticker = body.get('market_ticker')
        if not ticker:
            return
        ts_event = secs_to_nanos(body['ts']) if body.get('ts') else self._clock.timestamp_ns()
        ts_init = self._clock.timestamp_ns()
        if msg_type == 'market_lifecycle_v2':
            self._handle_data(parse_kalshi_lifecycle(get_kalshi_instrument_id(ticker), body, ts_event, ts_init))
            return
        instrument = self._cache.instrument(get_kalshi_instrument_id(ticker))
        if instrument is None:
            self._log.error(f'Cannot find instrument for {ticker}')
            return
        sequence = msg.get('seq') or 0
        if msg_type == 'orderbook_snapshot':
            self._handle_book(instrument, parse_kalshi_book_snapshot(instrument, body, sequence, ts_event, ts_init))
        elif msg_type == 'orderbook_delta':
            self._handle_book(instrument, parse_kalshi_book_delta(instrument, body, sequence, ts_event, ts_init))
        elif msg_type == 'trade':
            self._handle_data(parse_kalshi_trade(instrument, body, sequence, ts_event, ts_init))
        else:
            self._log.debug(f'Unhandled websocket message type: {msg_type}')

    def _handle_book(self, instrument: BinaryOption, deltas: OrderBookDeltas) -> None:
        book = self._local_books.get(instrument.id) or self._create_local_book(instrument.id)
        book.apply_deltas(deltas)
        if instrument.id in self.subscribed_order_book_deltas():
            self._handle_data(deltas)
        if instrument.id in self.subscribed_quote_ticks():
            self._emit_quote_from_book(instrument, book, deltas.ts_event, deltas.ts_init)

    def _emit_quote_from_book(self, instrument: BinaryOption, book: OrderBook, ts_event: int, ts_init: int) -> None:
        bid_price = book.best_bid_price()
        ask_price = book.best_ask_price()
        if bid_price is None or ask_price is None:
            return
        bid_size = book.best_bid_size()
        ask_size = book.best_ask_size()
        quote = QuoteTick(instrument_id=instrument.id, bid_price=bid_price, ask_price=ask_price, bid_size=bid_size, ask_size=ask_size, ts_event=ts_event, ts_init=ts_init)
        last = self._last_quotes.get(instrument.id)
        if last is not None and quote.bid_price == last.bid_price and (quote.ask_price == last.ask_price) and (quote.bid_size == last.bid_size) and (quote.ask_size == last.ask_size):
            return
        self._last_quotes[instrument.id] = quote
        self._handle_data(quote)

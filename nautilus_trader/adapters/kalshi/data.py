from __future__ import annotations
import asyncio
from typing import Any
import msgspec
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_VENUE
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_book_delta
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_book_snapshot
from nautilus_trader.adapters.kalshi.common.parsing import parse_kalshi_trade
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_instrument_id
from nautilus_trader.adapters.kalshi.common.symbol import get_kalshi_ticker
from nautilus_trader.adapters.kalshi.config import KalshiDataClientConfig
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProvider
from nautilus_trader.adapters.kalshi.websocket.client import KalshiWebSocketClient
from nautilus_trader.adapters.kalshi.websocket.types import KalshiWebSocketChannel
from nautilus_trader.common.enums import LogColor
from nautilus_trader.core.datetime import secs_to_nanos
from nautilus_trader.data.messages import RequestInstrument
from nautilus_trader.data.messages import RequestInstruments
from nautilus_trader.data.messages import SubscribeOrderBook
from nautilus_trader.data.messages import SubscribeQuoteTicks
from nautilus_trader.data.messages import SubscribeTradeTicks
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
        instrument = self._cache.instrument(get_kalshi_instrument_id(ticker))
        if instrument is None:
            self._log.error(f'Cannot find instrument for {ticker}')
            return
        sequence = msg.get('seq') or 0
        ts_event = secs_to_nanos(body['ts']) if body.get('ts') else self._clock.timestamp_ns()
        ts_init = self._clock.timestamp_ns()
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

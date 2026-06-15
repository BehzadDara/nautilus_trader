from __future__ import annotations
import asyncio
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit
from weakref import WeakSet
import msgspec
from nautilus_trader.adapters.kalshi.common.env import get_kalshi_base_url_ws
from nautilus_trader.adapters.kalshi.http.client import load_private_key
from nautilus_trader.adapters.kalshi.http.client import sign_pss_text
from nautilus_trader.adapters.kalshi.websocket.types import KALSHI_WS_CHANNELS_REQUIRING_TICKERS
from nautilus_trader.common.component import LiveClock
from nautilus_trader.common.component import Logger
from nautilus_trader.common.enums import LogColor
from nautilus_trader.core.nautilus_pyo3 import WebSocketClient
from nautilus_trader.core.nautilus_pyo3 import WebSocketClientError
from nautilus_trader.core.nautilus_pyo3 import WebSocketConfig

class KalshiWebSocketClient:

    def __init__(self, clock: LiveClock, api_key_id: str, private_key_pem: str, handler: Callable[[bytes], None], loop: asyncio.AbstractEventLoop, base_url: str | None=None, handler_reconnect: Callable[..., Awaitable[None]] | None=None, heartbeat: int=10, idle_timeout_ms: int=60000, proxy_url: str | None=None) -> None:
        self._clock = clock
        self._api_key_id = api_key_id
        self._private_key = load_private_key(private_key_pem)
        self._handler = handler
        self._handler_reconnect = handler_reconnect
        self._loop = loop
        self._base_url = base_url or get_kalshi_base_url_ws()
        self._heartbeat = heartbeat
        self._idle_timeout_ms = idle_timeout_ms
        self._proxy_url = proxy_url
        self._log = Logger(type(self).__name__)
        self._client: WebSocketClient | None = None
        self._next_id = 1
        self._subscriptions: dict[tuple[str, str | None], int] = {}
        self._tasks: WeakSet[asyncio.Task] = WeakSet()

    @property
    def url(self) -> str:
        return self._base_url

    @property
    def subscriptions(self) -> list[tuple[str, str | None]]:
        return list(self._subscriptions)

    def is_connected(self) -> bool:
        return self._client is not None and self._client.is_active()

    def is_disconnected(self) -> bool:
        return not self.is_connected()

    def _signed_headers(self) -> list[tuple[str, str]]:
        timestamp_ms = str(self._clock.timestamp_ms())
        path = urlsplit(self._base_url).path
        message = timestamp_ms + 'GET' + path
        signature = sign_pss_text(self._private_key, message)
        return [('KALSHI-ACCESS-KEY', self._api_key_id), ('KALSHI-ACCESS-TIMESTAMP', timestamp_ms), ('KALSHI-ACCESS-SIGNATURE', signature)]

    async def connect(self) -> None:
        if self.is_connected():
            return
        self._log.debug(f'Connecting to {self._base_url}...')
        config = WebSocketConfig(url=self._base_url, headers=self._signed_headers(), heartbeat=self._heartbeat, idle_timeout_ms=self._idle_timeout_ms, proxy_url=self._proxy_url)
        self._client = await WebSocketClient.connect(loop_=self._loop, config=config, handler=self._handler, post_reconnection=self._handle_reconnect)
        self._log.info(f'Connected to {self._base_url}', LogColor.BLUE)
        await self._resubscribe_all()

    async def disconnect(self) -> None:
        client = self._client
        if client is None:
            return
        if client.is_disconnecting() or client.is_closed():
            return
        self._log.debug('Disconnecting...')
        try:
            await client.disconnect()
        except WebSocketClientError as e:
            self._log.error(str(e))
        self._client = None
        self._log.info(f'Disconnected from {self._base_url}', LogColor.BLUE)

    async def subscribe(self, channel: str, market_ticker: str | None=None) -> None:
        key = (channel, market_ticker)
        if key in self._subscriptions:
            return
        command_id = self._next_id
        self._next_id += 1
        self._subscriptions[key] = command_id
        if self.is_connected():
            await self._send(self._build_subscribe(command_id, channel, market_ticker))

    async def unsubscribe(self, channel: str, market_ticker: str | None=None) -> None:
        key = (channel, market_ticker)
        command_id = self._subscriptions.pop(key, None)
        if command_id is None:
            return
        if self.is_connected():
            await self._send({'id': self._next_id, 'cmd': 'unsubscribe', 'params': {'sids': [command_id]}})
            self._next_id += 1

    async def _resubscribe_all(self) -> None:
        for (channel, market_ticker), command_id in self._subscriptions.items():
            await self._send(self._build_subscribe(command_id, channel, market_ticker))

    def _build_subscribe(self, command_id: int, channel: str, market_ticker: str | None) -> dict[str, Any]:
        params: dict[str, Any] = {'channels': [channel]}
        if market_ticker is not None:
            params['market_tickers'] = [market_ticker]
        elif channel in KALSHI_WS_CHANNELS_REQUIRING_TICKERS:
            params['market_tickers'] = []
        return {'id': command_id, 'cmd': 'subscribe', 'params': params}

    def _handle_reconnect(self) -> None:
        self._log.warning(f'Reconnected to {self._base_url}')
        task = self._loop.create_task(self._resubscribe_all())
        self._tasks.add(task)
        if self._handler_reconnect is not None:
            task = self._loop.create_task(self._handler_reconnect())
            self._tasks.add(task)

    async def _send(self, msg: dict[str, Any]) -> None:
        client = self._client
        if client is None:
            self._log.error(f'Cannot send message {msg}: not connected')
            return
        self._log.debug(f'SENDING: {msg}')
        try:
            await client.send_text(msgspec.json.encode(msg))
        except WebSocketClientError as e:
            self._log.error(str(e))

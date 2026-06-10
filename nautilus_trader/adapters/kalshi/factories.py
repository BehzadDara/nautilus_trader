# -------------------------------------------------------------------------------------------------
#  Copyright (C) 2015-2026 Nautech Systems Pty Ltd. All rights reserved.
#  https://nautechsystems.io
#
#  Licensed under the GNU Lesser General Public License Version 3.0 (the "License");
#  You may not use this file except in compliance with the License.
#  You may obtain a copy of the License at https://www.gnu.org/licenses/lgpl-3.0.en.html
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
# -------------------------------------------------------------------------------------------------
"""
Kalshi client factories — wire the adapter into a Nautilus trading node.
"""

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


def get_kalshi_http_client(
    clock: LiveClock,
    api_key_id: str | None = None,
    private_key_pem: str | None = None,
    base_url: str | None = None,
) -> KalshiHttpClient:
    """
    Return a Kalshi HTTP client with the given credentials.
    """
    return KalshiHttpClient(
        api_key_id=api_key_id or get_kalshi_api_key_id(),
        private_key_pem=private_key_pem or get_kalshi_private_key_pem(),
        clock=clock,
        base_url=base_url,
    )


@lru_cache(maxsize=1)
def get_kalshi_instrument_provider(
    client: KalshiHttpClient,
    config: KalshiInstrumentProviderConfig | None = None,
) -> KalshiInstrumentProvider:
    """
    Cache and return a Kalshi instrument provider.
    """
    return KalshiInstrumentProvider(
        http_client=client,
        config=config or KalshiInstrumentProviderConfig(),
    )


class KalshiLiveDataClientFactory(LiveDataClientFactory):
    """
    Provides a Kalshi live data client factory.
    """

    @staticmethod
    def create(  # type: ignore[override]
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: KalshiDataClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> KalshiDataClient:
        http_client = get_kalshi_http_client(
            clock=clock,
            api_key_id=config.api_key_id,
            private_key_pem=config.private_key_pem,
            base_url=config.base_url_http,
        )
        provider = get_kalshi_instrument_provider(
            client=http_client,
            config=config.instrument_provider,
        )
        return KalshiDataClient(
            loop=loop,
            client=http_client,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=provider,
            config=config,
            name=name,
        )


class KalshiLiveExecClientFactory(LiveExecClientFactory):
    """
    Provides a Kalshi live execution client factory.
    """

    @staticmethod
    def create(  # type: ignore[override]
        loop: asyncio.AbstractEventLoop,
        name: str,
        config: KalshiExecClientConfig,
        msgbus: MessageBus,
        cache: Cache,
        clock: LiveClock,
    ) -> KalshiExecutionClient:
        http_client = get_kalshi_http_client(
            clock=clock,
            api_key_id=config.api_key_id,
            private_key_pem=config.private_key_pem,
            base_url=config.base_url_http,
        )
        provider = get_kalshi_instrument_provider(
            client=http_client,
            config=config.instrument_provider,
        )
        return KalshiExecutionClient(
            loop=loop,
            client=http_client,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=provider,
            config=config,
            name=name,
        )

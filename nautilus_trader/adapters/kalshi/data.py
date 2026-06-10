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
Kalshi live market data client.

Scaffold stub. Implemented in Phase 6 (market data flows): subscribe to order
book + trades over the WebSocket and feed Nautilus data types into the engine.
"""

from nautilus_trader.adapters.kalshi.config import KalshiDataClientConfig
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProvider
from nautilus_trader.live.data_client import LiveMarketDataClient


class KalshiDataClient(LiveMarketDataClient):
    """
    Provides a data client for the Kalshi prediction market exchange.

    TODO(Phase 5/6): connect the WebSocket, subscribe to ``orderbook_delta`` /
    ``trade`` / ``ticker`` channels, and publish Nautilus deltas / trades / quotes.
    """

    def __init__(
        self,
        loop,
        client,
        msgbus,
        cache,
        clock,
        instrument_provider: KalshiInstrumentProvider,
        config: KalshiDataClientConfig,
        name: str | None = None,
    ) -> None:
        super().__init__(
            loop=loop,
            client_id=None,
            venue=config.venue,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            instrument_provider=instrument_provider,
            config=config,
            name=name,
        )
        self._http_client = client
        self._config = config

    async def _connect(self) -> None:
        raise NotImplementedError("KalshiDataClient._connect — Phase 5/6")

    async def _disconnect(self) -> None:
        raise NotImplementedError("KalshiDataClient._disconnect — Phase 5/6")

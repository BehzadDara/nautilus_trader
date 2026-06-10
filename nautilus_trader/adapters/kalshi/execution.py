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
Kalshi live execution client.

Scaffold stub. Implemented in Phase 7 (order execution): submit/cancel/modify
orders, report fills, and reconcile account/positions. HIGHEST RISK — always
test against a non-production environment first.
"""

from nautilus_trader.adapters.kalshi.config import KalshiExecClientConfig
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProvider
from nautilus_trader.live.execution_client import LiveExecutionClient


class KalshiExecutionClient(LiveExecutionClient):
    """
    Provides an execution client for the Kalshi prediction market exchange.

    TODO(Phase 7): implement order submit/cancel/modify, fill handling, and
    account/position reconciliation against the Kalshi REST + WebSocket APIs.
    """

    def __init__(
        self,
        loop,
        client,
        msgbus,
        cache,
        clock,
        instrument_provider: KalshiInstrumentProvider,
        config: KalshiExecClientConfig,
        name: str | None = None,
    ) -> None:
        super().__init__(
            loop=loop,
            client_id=None,
            venue=config.venue,
            oms_type=None,
            account_type=None,
            base_currency=None,
            instrument_provider=instrument_provider,
            msgbus=msgbus,
            cache=cache,
            clock=clock,
            config=config,
            name=name,
        )
        self._http_client = client
        self._config = config

    async def _connect(self) -> None:
        raise NotImplementedError("KalshiExecutionClient._connect — Phase 7")

    async def _disconnect(self) -> None:
        raise NotImplementedError("KalshiExecutionClient._disconnect — Phase 7")

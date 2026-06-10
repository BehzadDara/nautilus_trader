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
Kalshi instrument provider.

Scaffold stub. Implemented in Phase 4 (instrument loading): load Kalshi markets
via the REST client and parse them into Nautilus ``BinaryOption`` instruments.
"""

from nautilus_trader.common.providers import InstrumentProvider
from nautilus_trader.config import InstrumentProviderConfig


class KalshiInstrumentProviderConfig(InstrumentProviderConfig, frozen=True):
    """
    Configuration for the ``KalshiInstrumentProvider``.

    Parameters
    ----------
    load_series : list[str], optional
        Optional list of Kalshi series tickers to restrict loading to.

    """

    load_series: list[str] | None = None


class KalshiInstrumentProvider(InstrumentProvider):
    """
    Provides Kalshi market instruments (binary Yes/No event contracts).

    TODO(Phase 4): implement ``load_all_async`` / ``load_ids_async`` against the
    Kalshi REST client and parse markets into ``BinaryOption`` instruments.
    """

    def __init__(
        self,
        http_client=None,
        config: KalshiInstrumentProviderConfig | None = None,
    ) -> None:
        super().__init__(config=config or KalshiInstrumentProviderConfig())
        self._http_client = http_client

    async def load_all_async(self, filters: dict | None = None) -> None:
        raise NotImplementedError("KalshiInstrumentProvider.load_all_async — Phase 4")

    async def load_ids_async(self, instrument_ids, filters: dict | None = None) -> None:
        raise NotImplementedError("KalshiInstrumentProvider.load_ids_async — Phase 4")

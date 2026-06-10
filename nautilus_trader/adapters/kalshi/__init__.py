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
Kalshi prediction market integration adapter.

This subpackage provides instrument providers, data and execution client configurations,
factories, constants, and credential helpers for connecting to and interacting with
the Kalshi REST + WebSocket API.

Kalshi instruments are binary (Yes/No) event contracts, loaded as Nautilus
``BinaryOption`` instruments (mirroring the Polymarket adapter).

For convenience, the most commonly used symbols are re-exported at the subpackage's
top level, so downstream code can simply import from ``nautilus_trader.adapters.kalshi``.

"""

from nautilus_trader.adapters.kalshi.common.constants import KALSHI
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_CLIENT_ID
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_MAX_PRICE
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_MIN_PRICE
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_VENUE
from nautilus_trader.adapters.kalshi.config import KalshiDataClientConfig
from nautilus_trader.adapters.kalshi.config import KalshiExecClientConfig
from nautilus_trader.adapters.kalshi.factories import KalshiLiveDataClientFactory
from nautilus_trader.adapters.kalshi.factories import KalshiLiveExecClientFactory
from nautilus_trader.adapters.kalshi.factories import get_kalshi_http_client
from nautilus_trader.adapters.kalshi.factories import get_kalshi_instrument_provider
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProvider


__all__ = [
    "KALSHI",
    "KALSHI_CLIENT_ID",
    "KALSHI_MAX_PRICE",
    "KALSHI_MIN_PRICE",
    "KALSHI_VENUE",
    "KalshiDataClientConfig",
    "KalshiExecClientConfig",
    "KalshiInstrumentProvider",
    "KalshiLiveDataClientFactory",
    "KalshiLiveExecClientFactory",
    "get_kalshi_http_client",
    "get_kalshi_instrument_provider",
]

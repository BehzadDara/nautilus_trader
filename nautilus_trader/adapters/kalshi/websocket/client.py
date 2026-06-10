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
Kalshi WebSocket client.

Scaffold stub. Implemented in Phase 5: connect, authenticate (if required),
subscribe to channels (``orderbook_delta`` / ``trade`` / ``ticker`` / ``fill`` /
``order`` / ``position``), heartbeat, and reconnect.
"""

from nautilus_trader.adapters.kalshi.common.env import get_kalshi_base_url_ws


class KalshiWebSocketClient:
    """
    Provides a Kalshi WebSocket client.

    TODO(Phase 5): implement connect / subscribe / heartbeat / reconnect.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self._base_url = base_url or get_kalshi_base_url_ws()

    @property
    def base_url(self) -> str:
        return self._base_url

    async def connect(self) -> None:
        raise NotImplementedError("KalshiWebSocketClient.connect — Phase 5")

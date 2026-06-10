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
Kalshi JSON -> Nautilus type parsing.

Scaffold stub. The most bug-prone area — implemented across Phase 4 (instruments),
Phase 6 (book/trades), and Phase 7 (orders/fills). Wrong parse = wrong orders.
"""

from typing import Any

from nautilus_trader.model.instruments import BinaryOption


def parse_kalshi_instrument(market: dict[str, Any]) -> BinaryOption:
    """
    Parse a Kalshi market JSON object into a Nautilus ``BinaryOption`` instrument.

    TODO(Phase 4): implement the full field mapping (ticker, expiry, price
    precision, tick size, currency) from the Kalshi ``GET /markets`` response.
    """
    raise NotImplementedError("parse_kalshi_instrument — Phase 4")

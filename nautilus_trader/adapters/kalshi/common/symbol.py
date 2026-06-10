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
Kalshi market ticker <-> Nautilus ``InstrumentId`` mapping.

Scaffold stub. Implemented in Phase 4: map a Kalshi market ticker
(e.g. ``SERIES-EVENT-OUTCOME``) to a Nautilus ``InstrumentId`` and back.
"""

from nautilus_trader.adapters.kalshi.common.constants import KALSHI_VENUE
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.identifiers import Symbol


def get_kalshi_instrument_id(ticker: str) -> InstrumentId:
    """
    Return the Nautilus ``InstrumentId`` for a Kalshi market ticker.

    TODO(Phase 4): confirm the canonical ticker format and any normalization.
    """
    return InstrumentId(Symbol(ticker), KALSHI_VENUE)

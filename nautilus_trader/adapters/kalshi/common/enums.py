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
Kalshi enums and their mappings to Nautilus enums.

Scaffold stub. Implemented across Phase 4 (status) and Phase 7 (order side/type/TIF):
map Kalshi order status / side / time-in-force strings to Nautilus enums.
"""

from enum import Enum


class KalshiOrderSide(Enum):
    """
    Kalshi order side. Kalshi contracts trade as ``yes`` / ``no``.

    TODO(Phase 7): confirm values + map to Nautilus ``OrderSide``.
    """

    YES = "yes"
    NO = "no"


class KalshiOrderStatus(Enum):
    """
    Kalshi order status.

    TODO(Phase 7): confirm full set from live API + map to Nautilus ``OrderStatus``.
    """

    RESTING = "resting"
    CANCELED = "canceled"
    EXECUTED = "executed"

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

from typing import Final

from nautilus_trader.model.enums import TimeInForce
from nautilus_trader.model.identifiers import ClientId
from nautilus_trader.model.identifiers import Venue


KALSHI: Final[str] = "KALSHI"
KALSHI_VENUE: Final[Venue] = Venue(KALSHI)
KALSHI_CLIENT_ID: Final[ClientId] = ClientId(KALSHI)

# Default base URLs (API base path prefix is ``/trade-api/v2``). These are
# fallbacks only — the effective URLs are resolved from the environment via
# ``common/env.py`` (``KALSHI_BASE_URL_HTTP`` / ``KALSHI_BASE_URL_WS``), so they
# can be changed per environment without editing code.
KALSHI_DEFAULT_BASE_URL_HTTP: Final[str] = "https://demo-api.kalshi.co"
KALSHI_DEFAULT_BASE_URL_WS: Final[str] = "wss://demo-api.kalshi.co/trade-api/ws/v2"

# REST API base path appended to the base URL and included in the signed path.
KALSHI_API_PATH: Final[str] = "/trade-api/v2"

# RSA-PSS request signing headers (see common/credentials.py + http/client.py).
KALSHI_ACCESS_KEY_HEADER: Final[str] = "KALSHI-ACCESS-KEY"
KALSHI_ACCESS_TIMESTAMP_HEADER: Final[str] = "KALSHI-ACCESS-TIMESTAMP"
KALSHI_ACCESS_SIGNATURE_HEADER: Final[str] = "KALSHI-ACCESS-SIGNATURE"

# Kalshi prices are integer cents in [1, 99] (probability 1c-99c). Expressed here
# as the Nautilus probability range used for the BinaryOption instrument.
KALSHI_MAX_PRICE: Final[float] = 0.99
KALSHI_MIN_PRICE: Final[float] = 0.01
KALSHI_PRICE_PRECISION: Final[int] = 2

VALID_KALSHI_TIME_IN_FORCE: Final[set[TimeInForce]] = {
    TimeInForce.GTC,
    TimeInForce.IOC,
    TimeInForce.FOK,
}

# TODO(Phase 1/3): confirm exact rate limits per Kalshi tier from live responses.
KALSHI_HTTP_RATE_LIMIT: Final[int] = 100  # requests per minute (placeholder)

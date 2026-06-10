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

from nautilus_trader.adapters.kalshi.common.constants import KALSHI_VENUE
from nautilus_trader.adapters.kalshi.providers import KalshiInstrumentProviderConfig
from nautilus_trader.config import LiveDataClientConfig
from nautilus_trader.config import LiveExecClientConfig
from nautilus_trader.config import PositiveFloat
from nautilus_trader.config import PositiveInt
from nautilus_trader.model.identifiers import Venue


class KalshiDataClientConfig(LiveDataClientConfig, frozen=True):
    """
    Configuration for ``KalshiDataClient`` instances.

    Parameters
    ----------
    instrument_provider : KalshiInstrumentProviderConfig, optional
        The Kalshi instrument provider config.
    venue : Venue, default KALSHI_VENUE
        The venue for the client.
    api_key_id : str, optional
        The Kalshi API key ID (``KALSHI-ACCESS-KEY``).
        If ``None`` then will source the ``KALSHI_API_KEY_ID`` environment variable.
    private_key_pem : str, optional
        The RSA private key contents (PEM) used to sign requests.
        If ``None`` then sourced from ``KALSHI_PRIVATE_KEY_PEM`` or read from
        the file at ``KALSHI_PRIVATE_KEY_PATH``.
    base_url_http : str, optional
        The HTTP client custom endpoint override.
    base_url_ws : str, optional
        The WebSocket client custom endpoint override.
    ws_connection_delay_secs : PositiveFloat, default 0.1
        The delay (seconds) prior to making a new websocket connection.
    update_instruments_interval_mins : PositiveInt or None, default 60
        The interval (minutes) between updating Kalshi instruments.

    """

    instrument_provider: KalshiInstrumentProviderConfig | None = None
    venue: Venue = KALSHI_VENUE
    api_key_id: str | None = None
    private_key_pem: str | None = None
    base_url_http: str | None = None
    base_url_ws: str | None = None
    ws_connection_delay_secs: PositiveFloat = 0.1
    update_instruments_interval_mins: PositiveInt | None = 60


class KalshiExecClientConfig(LiveExecClientConfig, frozen=True):
    """
    Configuration for ``KalshiExecutionClient`` instances.

    Parameters
    ----------
    instrument_provider : KalshiInstrumentProviderConfig, optional
        The Kalshi instrument provider config.
    venue : Venue, default KALSHI_VENUE
        The venue for the client.
    api_key_id : str, optional
        The Kalshi API key ID (``KALSHI-ACCESS-KEY``).
        If ``None`` then will source the ``KALSHI_API_KEY_ID`` environment variable.
    private_key_pem : str, optional
        The RSA private key contents (PEM) used to sign requests.
        If ``None`` then sourced from ``KALSHI_PRIVATE_KEY_PEM`` or read from
        the file at ``KALSHI_PRIVATE_KEY_PATH``.
    base_url_http : str, optional
        The HTTP client custom endpoint override.
    base_url_ws : str, optional
        The WebSocket client custom endpoint override.
    max_retries : PositiveInt, optional
        The maximum number of times a submit or cancel order request will be retried.
    retry_delay_initial_ms : PositiveInt, optional
        The initial delay (milliseconds) between retries.
    retry_delay_max_ms : PositiveInt, optional
        The maximum delay (milliseconds) between retries.

    """

    instrument_provider: KalshiInstrumentProviderConfig | None = None
    venue: Venue = KALSHI_VENUE
    api_key_id: str | None = None
    private_key_pem: str | None = None
    base_url_http: str | None = None
    base_url_ws: str | None = None
    max_retries: PositiveInt | None = None
    retry_delay_initial_ms: PositiveInt | None = None
    retry_delay_max_ms: PositiveInt | None = None

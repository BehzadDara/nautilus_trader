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
Kalshi REST HTTP client with RSA-PSS request signing.

Scaffold stub. The signing logic + request methods are implemented in Phase 3.
Signing scheme (confirmed): string-to-sign = ``timestamp(ms) + METHOD + path``
(path without query, includes the ``/trade-api/v2`` prefix); RSA-PSS, SHA-256,
salt length = digest length; signature base64-encoded; sent via the
``KALSHI-ACCESS-KEY`` / ``KALSHI-ACCESS-TIMESTAMP`` / ``KALSHI-ACCESS-SIGNATURE`` headers.
"""

from nautilus_trader.adapters.kalshi.common.constants import KALSHI_BASE_URL_DEMO_HTTP
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_BASE_URL_HTTP


class KalshiHttpClient:
    """
    Provides a Kalshi REST API client with RSA-PSS request signing.

    TODO(Phase 3): implement request signing, the signed-GET path, retries,
    and rate-limit handling against the Kalshi REST API.

    Parameters
    ----------
    api_key_id : str
        The Kalshi API key ID.
    private_key_pem : str
        The RSA private key (PEM) used to sign requests.
    is_demo : bool, default True
        If the demo (sandbox) environment should be used.
    base_url : str, optional
        An explicit base URL override.

    """

    def __init__(
        self,
        api_key_id: str,
        private_key_pem: str,
        is_demo: bool = True,
        base_url: str | None = None,
    ) -> None:
        self._api_key_id = api_key_id
        self._private_key_pem = private_key_pem
        self._base_url = base_url or (
            KALSHI_BASE_URL_DEMO_HTTP if is_demo else KALSHI_BASE_URL_HTTP
        )

    @property
    def base_url(self) -> str:
        return self._base_url

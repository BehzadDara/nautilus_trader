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

from pathlib import Path

from nautilus_trader.adapters.env import get_env_key
from nautilus_trader.adapters.env import get_env_key_or


def get_kalshi_api_key_id() -> str:
    """
    Return the Kalshi API key ID (the ``KALSHI-ACCESS-KEY`` header value).
    """
    return get_env_key("KALSHI_API_KEY_ID")


def get_kalshi_private_key_pem() -> str:
    """
    Return the Kalshi RSA private key in PEM form.

    Resolves ``KALSHI_PRIVATE_KEY_PEM`` (the PEM contents) if set; otherwise reads
    the file at ``KALSHI_PRIVATE_KEY_PATH``. The private key is never logged.
    """
    pem = get_env_key_or("KALSHI_PRIVATE_KEY_PEM", "")
    if pem:
        return pem
    path = get_env_key("KALSHI_PRIVATE_KEY_PATH")
    return Path(path).read_text()

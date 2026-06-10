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
Environment configuration for the Kalshi adapter.

Loads a ``.env`` file (if present) so that environment-specific values — the API
key ID, the base URLs, and the private key location — can be changed without
editing code. Values already set in the process environment always take
precedence over ``.env`` (``load_dotenv`` is called with ``override=False``).
"""

import os

from dotenv import find_dotenv
from dotenv import load_dotenv

from nautilus_trader.adapters.kalshi.common.constants import KALSHI_DEFAULT_BASE_URL_HTTP
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_DEFAULT_BASE_URL_WS


_DOTENV_LOADED = False


def load_kalshi_env() -> None:
    """
    Load a ``.env`` file into the process environment (once).

    The file path is taken from ``KALSHI_ENV_FILE`` if set; otherwise the nearest
    ``.env`` searched upward from the current working directory is used. Existing
    environment variables are not overridden. Safe to call repeatedly.
    """
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    dotenv_path = os.environ.get("KALSHI_ENV_FILE") or find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path, override=False)
    _DOTENV_LOADED = True


def get_kalshi_base_url_http() -> str:
    """
    Return the REST base URL from ``KALSHI_BASE_URL_HTTP`` (or the default).
    """
    load_kalshi_env()
    return os.environ.get("KALSHI_BASE_URL_HTTP", KALSHI_DEFAULT_BASE_URL_HTTP)


def get_kalshi_base_url_ws() -> str:
    """
    Return the WebSocket base URL from ``KALSHI_BASE_URL_WS`` (or the default).
    """
    load_kalshi_env()
    return os.environ.get("KALSHI_BASE_URL_WS", KALSHI_DEFAULT_BASE_URL_WS)

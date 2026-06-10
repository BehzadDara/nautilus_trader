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
Kalshi HTTP error types.

Scaffold stub. Error-response mapping is implemented in Phase 3 (HTTP client).
"""


class KalshiError(Exception):
    """
    The base class for all Kalshi specific errors.
    """


class KalshiHttpError(KalshiError):
    """
    Represents a Kalshi REST API error response.

    Parameters
    ----------
    status : int
        The HTTP status code.
    message : str
        The error message.
    code : str, optional
        The Kalshi error code, if provided.

    """

    def __init__(self, status: int, message: str, code: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.code = code

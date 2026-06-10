import os
import sys
import tempfile

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != _REPO]
os.environ.setdefault("KALSHI_ENV_FILE", os.path.join(_REPO, ".env"))
os.chdir(tempfile.gettempdir())

import asyncio
from nautilus_trader.adapters.kalshi.common.credentials import get_kalshi_api_key_id
from nautilus_trader.adapters.kalshi.common.credentials import get_kalshi_private_key_pem
from nautilus_trader.adapters.kalshi.http.client import KalshiHttpClient
from nautilus_trader.common.component import LiveClock

async def main() -> None:
    client = KalshiHttpClient(api_key_id=get_kalshi_api_key_id(), private_key_pem=get_kalshi_private_key_pem(), clock=LiveClock())
    print('base_url:', client.base_url)
    print('\n[1] GET /markets?limit=2 ...')
    markets = await client.get('/markets', params={'limit': 2})
    tickers = [m.get('ticker') for m in markets.get('markets', [])]
    print('    OK - sample tickers:', tickers)
    print('\n[2] GET /portfolio/balance (signed/auth-required) ...')
    balance = await client.get('/portfolio/balance')
    print('    OK - balance response:', balance)
    print('\nLIVE OK - signed requests to the Kalshi API succeeded (HTTP 200).')
if __name__ == '__main__':
    asyncio.run(main())

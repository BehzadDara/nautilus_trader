from pathlib import Path
from nautilus_trader.adapters.env import get_env_key
from nautilus_trader.adapters.env import get_env_key_or
from nautilus_trader.adapters.kalshi.common.env import load_kalshi_env

def get_kalshi_api_key_id() -> str:
    load_kalshi_env()
    return get_env_key('KALSHI_API_KEY_ID')

def get_kalshi_private_key_pem() -> str:
    load_kalshi_env()
    pem = get_env_key_or('KALSHI_PRIVATE_KEY_PEM', '')
    if pem:
        return pem
    path = get_env_key('KALSHI_PRIVATE_KEY_PATH')
    return Path(path).read_text()

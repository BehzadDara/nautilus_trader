import os
from dotenv import find_dotenv
from dotenv import load_dotenv
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_DEFAULT_BASE_URL_HTTP
from nautilus_trader.adapters.kalshi.common.constants import KALSHI_DEFAULT_BASE_URL_WS
_DOTENV_LOADED = False

def load_kalshi_env() -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    dotenv_path = os.environ.get('KALSHI_ENV_FILE') or find_dotenv(usecwd=True)
    if dotenv_path:
        load_dotenv(dotenv_path, override=False)
    _DOTENV_LOADED = True

def get_kalshi_base_url_http() -> str:
    load_kalshi_env()
    return os.environ.get('KALSHI_BASE_URL_HTTP', KALSHI_DEFAULT_BASE_URL_HTTP)

def get_kalshi_base_url_ws() -> str:
    load_kalshi_env()
    return os.environ.get('KALSHI_BASE_URL_WS', KALSHI_DEFAULT_BASE_URL_WS)

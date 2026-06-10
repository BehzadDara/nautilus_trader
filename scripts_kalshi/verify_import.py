"""Phase 2 scaffold verification: every kalshi module imports cleanly against the wheel."""
import importlib

MODULES = [
    "nautilus_trader.adapters.kalshi",
    "nautilus_trader.adapters.kalshi.common.constants",
    "nautilus_trader.adapters.kalshi.common.credentials",
    "nautilus_trader.adapters.kalshi.common.enums",
    "nautilus_trader.adapters.kalshi.common.symbol",
    "nautilus_trader.adapters.kalshi.common.parsing",
    "nautilus_trader.adapters.kalshi.common.retry",
    "nautilus_trader.adapters.kalshi.config",
    "nautilus_trader.adapters.kalshi.providers",
    "nautilus_trader.adapters.kalshi.data",
    "nautilus_trader.adapters.kalshi.execution",
    "nautilus_trader.adapters.kalshi.factories",
    "nautilus_trader.adapters.kalshi.http.client",
    "nautilus_trader.adapters.kalshi.http.errors",
    "nautilus_trader.adapters.kalshi.websocket.client",
    "nautilus_trader.adapters.kalshi.websocket.types",
]

for m in MODULES:
    importlib.import_module(m)
    print("ok:", m)

# Public surface sanity
from nautilus_trader.adapters.kalshi import (
    KALSHI_VENUE,
    KalshiDataClientConfig,
    KalshiExecClientConfig,
    KalshiInstrumentProvider,
    KalshiLiveDataClientFactory,
    KalshiLiveExecClientFactory,
)
from nautilus_trader.adapters.kalshi.common.constants import (
    KALSHI_BASE_URL_HTTP,
    KALSHI_BASE_URL_WS,
    KALSHI_API_PATH,
)

print()
print("venue:", KALSHI_VENUE)
print("http:", KALSHI_BASE_URL_HTTP)
print("ws:", KALSHI_BASE_URL_WS)
print("api path:", KALSHI_API_PATH)

print("\nPHASE 2 SCAFFOLD OK — all modules import, public surface present.")

# Kalshi adapter (internal)

Pure-Python integration adapter for the Kalshi prediction/event exchange, mirroring the
Polymarket adapter. Internal use only.

Markets are binary Yes/No event contracts mapped to Nautilus `BinaryOption`. The instrument
symbol is the Kalshi market ticker (e.g. `KXMENWORLDCUP-26-FR`); the venue is `KALSHI`.

## Auth

Every request is signed with an RSA private key. String to sign is
`timestamp_ms + METHOD + path` (path includes the `/trade-api/v2` prefix, no query),
RSA-PSS / SHA-256, salt = digest length, base64. Headers: `KALSHI-ACCESS-KEY`,
`KALSHI-ACCESS-TIMESTAMP`, `KALSHI-ACCESS-SIGNATURE`. The WebSocket handshake is signed the
same way with the WS path.

## Configuration

Credentials and endpoints come from environment variables (loaded from a `.env` file via
`KALSHI_ENV_FILE`, or an upward search):

| Variable | Meaning |
|---|---|
| `KALSHI_API_KEY_ID` | API key id |
| `KALSHI_PRIVATE_KEY_PEM` | RSA private key PEM (inline) |
| `KALSHI_PRIVATE_KEY_PATH` | path to the RSA private key PEM (used if `_PEM` is unset) |
| `KALSHI_BASE_URL_HTTP` | REST base URL (e.g. `https://demo-api.kalshi.co`) |
| `KALSHI_BASE_URL_WS` | WebSocket URL (e.g. `wss://demo-api.kalshi.co/trade-api/ws/v2`) |

`KalshiDataClientConfig` / `KalshiExecClientConfig` accept the same values directly
(`api_key_id`, `private_key_pem`, `base_url_http`, `base_url_ws`) which override the env.

## Wiring into a node

```python
from nautilus_trader.adapters.kalshi.factories import KalshiLiveDataClientFactory
from nautilus_trader.adapters.kalshi.factories import KalshiLiveExecClientFactory
from nautilus_trader.adapters.kalshi.config import KalshiDataClientConfig
from nautilus_trader.adapters.kalshi.config import KalshiExecClientConfig

config.data_clients["KALSHI"] = KalshiDataClientConfig()
config.exec_clients["KALSHI"] = KalshiExecClientConfig()

node.add_data_client_factory("KALSHI", KalshiLiveDataClientFactory)
node.add_exec_client_factory("KALSHI", KalshiLiveExecClientFactory)
```

## What it supports

- Instruments: load all (cursor-paginated) or by ticker, parsed to `BinaryOption`.
- Market data: order book deltas (Yes orders = bids, No orders @ q = Yes asks @ 1-q),
  top-of-book quotes, trades.
- Execution: submit limit/market orders (V2 endpoint, `side` = bid/ask, price in dollars),
  cancel by venue order id, and order/fill/position status reports.

## Order side model

A Kalshi market is the Yes contract. Nautilus `BUY` = `bid` (buy Yes); `SELL` = `ask`
(sell Yes, equivalent to buying No). Prices are Yes-leg dollars.

## Development

The installed wheel and the source tree are two separate copies. Develop in the source
tree, then copy into the wheel before running anything:

```powershell
scripts_kalshi\sync_to_venv.ps1
```

Run Python from outside the repo (the source tree shadows the working wheel). Helper scripts
under `scripts_kalshi/` cover live checks (`verify_slice_a.py`, `verify_slice_b.py`) and the
unit tests (`run_tests.ps1`); see `scripts_kalshi/VERIFY.txt`.

Tests live in `tests/integration_tests/adapters/kalshi/`.

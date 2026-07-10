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
- Market data (live): order book deltas (Yes orders = bids, No orders @ q = Yes asks @ 1-q),
  top-of-book quotes, trades, and instrument status via the `market_lifecycle_v2` channel.
- Market data (historical/request): instrument(s), order book snapshot
  (`GET /markets/{ticker}/orderbook`), trade ticks (`GET /markets/trades`), and bars/candlesticks
  (`GET /series/{series}/markets/{ticker}/candlesticks`, intervals 1/60/1440 min).
- Not applicable on Kalshi (handled as explicit "unsupported"): historical quotes, streamed bars,
  funding/index/mark prices, option greeks, L3/depth.
- Execution: submit limit/market orders (V2 endpoint, `side` = bid/ask, price in dollars),
  batch submit (`_submit_order_list`), cancel, batch cancel, cancel-all, amend/modify, and
  order/fill/position status reports.
- Fees: `KalshiFeeModel` (backtests) computes `ceil(0.07 * count * price * (1 - price))` to the
  centicent; live fills use the venue's reported `fee_cost`. Verified equal to a real demo fill.

## Order side model

A Kalshi market is the Yes contract. Nautilus `BUY` = `bid` (buy Yes); `SELL` = `ask`
(sell Yes, equivalent to buying No). Prices are Yes-leg dollars.

Yes and No are the same instrument, not two: buying 1 Yes and 1 No leaves you flat. The
outcome is therefore carried as an `OrderSide`, never in the `InstrumentId`.

## Market strings

`parse_kalshi_market` takes a single string and returns a `KalshiMarket` (`instrument_id`
plus optional `side`). The format is `TICKER_side.KALSHI`: the side joins with `_` because
roughly half of all Kalshi tickers contain a `.` (e.g. `KXTRUMPVH-26JUL17-T40.8`), and the
venue joins with `.` so the result is a valid `InstrumentId` string.

| Input | Ticker | Side |
|---|---|---|
| `KXMENWORLDCUP-26-FR_yes.KALSHI` | `KXMENWORLDCUP-26-FR` | `BUY` |
| `KXMENWORLDCUP-26-FR_no` | `KXMENWORLDCUP-26-FR` | `SELL` |
| `KXMENWORLDCUP-26-FR` | `KXMENWORLDCUP-26-FR` | `default_side` |
| `https://demo.kalshi.co/markets/...?op_market_ticker=...&op_order_side=no` | from query | `SELL` |

The execution client consumes these directly, so callers never invert prices themselves:

```python
order = await exec_client.build_limit_order(
    "KXMENWORLDCUP-26-FR_no.KALSHI",  # or a KalshiMarket, or a pasted URL
    price=0.40,                       # price of the named outcome
    quantity=10,
    order_factory=factory,
)
# -> OrderSide.SELL, Yes-leg price 0.60
```

`build_limit_order` maps the outcome to a side, converts the price to the Yes leg for `no`,
and loads the instrument if it is not cached. `resolve_instrument` performs the lookup alone.
Kalshi itself never sees the market string: the payload carries `ticker` and `side: bid|ask`.

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

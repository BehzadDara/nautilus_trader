# Verifying the Kalshi adapter

How to run the two end-to-end check scripts: `verify_slice_a.py` (market data) and
`verify_slice_b.py` (execution). Both read credentials from the repo `.env` automatically,
both run from their own location, and both print a final `OK` / `CHECK FAILED` line.

> Commands below assume **PowerShell** on Windows.

---

## Before every run: sync the adapter into the venv

The scripts import the adapter from the installed wheel, not the source tree. After any code
change, copy the latest source in first:

```powershell
& "D:\Projects\Nautilustrader\scripts_kalshi\sync_to_venv.ps1"
```

Then change into the scripts folder:

```powershell
cd D:\Projects\Nautilustrader\scripts_kalshi
```

---

## verify_slice_a.py — market data

Loads an instrument, connects the signed WebSocket, subscribes to the order book and trades,
and prints the live book / quotes / trades flowing through the data client.

### Run (simplest)

```powershell
python .\verify_slice_a.py
```

With no env vars set it picks the **busiest open market by 24h volume** (non-deterministic; can
land on a thin or one-sided book).

### Environment variables (all optional)

| Variable | What it does | Default |
|---|---|---|
| `VERIFY_TICKER` | Watch a specific market instead of the busiest one | busiest by volume |
| `VERIFY_SECS` | How many seconds to listen for live messages | `20` |
| `VERIFY_RAW` | If set to anything, prints the first 4 raw WebSocket frames (debugging) | unset |

### Set / run / unset

```powershell
$env:VERIFY_TICKER = "KXMENWORLDCUP-26-FR"   # France to win the 2026 World Cup (two-sided, stable)
$env:VERIFY_SECS   = "30"
python .\verify_slice_a.py

# clear them again when done
Remove-Item Env:VERIFY_TICKER
Remove-Item Env:VERIFY_SECS
```

### Reading the result

```
[3] Results
    raw messages  : 12     <- frames received from the venue (0 = nothing arrived; raise VERIFY_SECS or retry)
    book messages : 1      <- order-book snapshots/updates parsed
    quote ticks   : 1      <- bid/ask quotes produced
    trade ticks   : 0      <- executed trades seen (often 0 on the quiet demo)
    final best_bid: 0.1600   best_ask: 0.1600
SLICE A OK - ...
```

`SLICE A OK` needs at least one parsed book level. If you get `CHECK FAILED`:
- `raw messages: 0` -> no traffic; raise `VERIFY_SECS` and run again (demo can be slow).
- `raw messages > 0` but no book -> the market is empty/one-sided; set `VERIFY_TICKER` to a busier one.

---

## verify_slice_b.py — execution

Builds the execution client and checks the signed account / orders / fills / positions endpoints
and the order-side / type / time-in-force mappings. By default it does **not** place any order.

### Run (read-only, safe)

```powershell
python .\verify_slice_b.py
```

This only reads. It ends with `SLICE B (read-only) OK`. On an unfunded demo account the balance,
orders, fills and positions all come back empty (expected).

### Environment variables (all optional)

| Variable | What it does | Default |
|---|---|---|
| `VERIFY_PLACE_ORDER` | Set to `1` to actually place a tiny real demo order, then cancel it | unset (placement skipped) |
| `VERIFY_TICKER` | Which market to place the test order on (only used when placing) | `KXMENWORLDCUP-26-FR` |

### Placing a real demo order (funded account only)

This sends a **real 1-contract BUY YES limit @ $0.01** to the demo exchange and then cancels it.
Fund the demo account first, otherwise the venue rejects it.

```powershell
$env:VERIFY_PLACE_ORDER = "1"
$env:VERIFY_TICKER      = "KXMENWORLDCUP-26-FR"
python .\verify_slice_b.py

# clear them again so a later run stays read-only
Remove-Item Env:VERIFY_PLACE_ORDER
Remove-Item Env:VERIFY_TICKER
```

It prints the venue order id and status after placing, then the status after cancelling.

---

## Notes

- **Env vars last only for the current PowerShell window.** Closing the window clears them; you do
  not have to unset manually unless you want to in the same session.
- Check a value with `echo $env:VERIFY_TICKER` (blank means unset).
- Credentials (`KALSHI_*`) live in the repo `.env` and are loaded automatically — you do **not**
  set those here.

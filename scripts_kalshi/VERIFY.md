# Verify scripts

First (after any code change), sync + cd:

```powershell
& "D:\Projects\Nautilustrader\scripts_kalshi\sync_to_venv.ps1"
cd D:\Projects\Nautilustrader\scripts_kalshi
```

Credentials load from `.env` automatically. Env vars below last only for the current window; clear with `Remove-Item Env:NAME`.

## verify_slice_a.py — market data

```powershell
python .\verify_slice_a.py
```

| Env | Default | Effect |
|---|---|---|
| `VERIFY_TICKER` | busiest market | watch a specific market |
| `VERIFY_SECS` | `20` | seconds to listen |
| `VERIFY_RAW` | unset | print first raw frames |

```powershell
$env:VERIFY_TICKER="KXMENWORLDCUP-26-FR"; python .\verify_slice_a.py
```

Pass = `SLICE A OK`. `CHECK FAILED` with `raw messages: 0` → raise `VERIFY_SECS`; with raw > 0 → market is empty, pick another `VERIFY_TICKER`.

## verify_slice_b.py — execution

Read-only by default (safe):

```powershell
python .\verify_slice_b.py
```

| Env | Default | Effect |
|---|---|---|
| `VERIFY_PLACE_ORDER` | unset | `1` = place a real 1-contract demo order, then cancel |
| `VERIFY_TICKER` | `KXMENWORLDCUP-26-FR` | market for the test order |

Placing an order needs a funded demo account:

```powershell
$env:VERIFY_PLACE_ORDER="1"; python .\verify_slice_b.py
Remove-Item Env:VERIFY_PLACE_ORDER
```

# Verify scripts

Sync + cd first:

```powershell
& ".\sync_to_venv.ps1"; cd D:\Projects\Nautilustrader\scripts_kalshi
```

Creds load from `.env`. Env vars last for the window only (`Remove-Item Env:NAME` to clear).

**Slice A (data):** `python .\verify_slice_a.py` → `SLICE A OK`
- `VERIFY_TICKER` (default: busiest), `VERIFY_SECS` (20)

**Slice B (execution):** `python .\verify_slice_b.py` → read-only, safe
- `VERIFY_PLACE_ORDER=1` places a real 1-contract demo order then cancels (needs funded account)

```powershell
$env:VERIFY_TICKER="KXMENWORLDCUP-26-FR"; python .\verify_slice_a.py
```

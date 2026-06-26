import os
import sys
import tempfile
import asyncio

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or ".") != _REPO]
os.environ.setdefault("KALSHI_ENV_FILE", os.path.join(_REPO, ".env"))
os.chdir(tempfile.gettempdir())

from nautilus_trader.adapters.kalshi.common.credentials import get_kalshi_api_key_id
from nautilus_trader.adapters.kalshi.common.credentials import get_kalshi_private_key_pem
from nautilus_trader.adapters.kalshi.http.client import KalshiHttpClient
from nautilus_trader.common.component import LiveClock

async def main() -> None:
    clock = LiveClock()
    http = KalshiHttpClient(api_key_id=get_kalshi_api_key_id(), private_key_pem=get_kalshi_private_key_pem(), clock=clock)

    order_ids = []
    cursor = None
    while True:
        params = {"limit": 1000, "status": "resting"}
        if cursor:
            params["cursor"] = cursor
        page = await http.get("/portfolio/orders", params=params)
        order_ids.extend(o["order_id"] for o in (page.get("orders") or []))
        cursor = page.get("cursor")
        if not cursor or not page.get("orders"):
            break

    print(f"resting orders found: {len(order_ids)}")
    if not order_ids:
        print("nothing to cancel")
        return

    canceled = 0
    for start in range(0, len(order_ids), 20):
        batch = order_ids[start:start + 20]
        resp = await http.delete("/portfolio/events/orders/batched", payload={"orders": [{"order_id": oid} for oid in batch]})
        canceled += len(resp.get("orders") or []) if resp else 0

    print(f"canceled: {canceled}")

    remaining = await http.get("/portfolio/orders", params={"limit": 1000, "status": "resting"})
    print(f"resting orders now: {len(remaining.get('orders') or [])}")

if __name__ == "__main__":
    asyncio.run(main())

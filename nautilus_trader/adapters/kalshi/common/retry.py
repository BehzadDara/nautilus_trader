import random
from collections.abc import Callable

def auto_load_retry_delay(attempt: int, *, base_secs: float, max_secs: float, random_fn: Callable[[], float]=random.random) -> float:
    delay = min(max_secs, base_secs * 2 ** attempt)
    return delay + delay * 0.25 * random_fn()

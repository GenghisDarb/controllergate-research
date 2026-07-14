from __future__ import annotations

import time


def due(next_retry_time: float | None, now: float | None = None) -> bool:
    return next_retry_time is None or float(next_retry_time) <= float(now if now is not None else time.time())

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetryPolicy:
    maximum_attempts: int = 2
    retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504)

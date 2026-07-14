from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HealthContract:
    expected_returncode: int
    minimum_events: int = 1
    maximum_skips: int = 0

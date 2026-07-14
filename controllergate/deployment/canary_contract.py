from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CanaryContract:
    proof_hash: str
    source_hash: str
    command: list[str]
    expected_returncode: int = 0

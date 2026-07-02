from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ComputeBudget:
    max_probes: int
    max_patch_fragments: int
    max_null_attempts: int
    max_retries: int
    max_runtime_seconds: int
    spent: dict[str, int] = field(default_factory=lambda: {"probes": 0, "patch_fragments": 0, "null_attempts": 0, "retries": 0, "runtime_seconds": 0})

    def spend(self, key: str, amount: int = 1) -> dict[str, Any]:
        if key not in self.spent:
            raise KeyError(key)
        self.spent[key] += amount
        return self.status()

    def status(self) -> dict[str, Any]:
        limits = {
            "probes": self.max_probes,
            "patch_fragments": self.max_patch_fragments,
            "null_attempts": self.max_null_attempts,
            "retries": self.max_retries,
            "runtime_seconds": self.max_runtime_seconds,
        }
        exceeded = sorted(key for key, limit in limits.items() if self.spent[key] > limit)
        return {
            "status": "SAFE_STOP" if exceeded else "PASS",
            "spent": dict(self.spent),
            "limits": limits,
            "budget_exceeded": exceeded,
            "blocker": "safe_stop_budget_exceeded" if exceeded else None,
            "workspace_quarantine_required": bool(exceeded),
            "rollback_record_required": bool(exceeded),
        }

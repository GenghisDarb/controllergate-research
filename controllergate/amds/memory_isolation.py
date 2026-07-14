from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from controllergate.state.integrity import canonical_hash


FORBIDDEN_ROUTING_FIELDS = {"terminal_truth", "ownership_label", "repair_result", "count_result", "patch", "patch_bytes", "gold"}


class IsolatedMemoryStore:
    def __init__(self, routing_path: str | Path, truth_path: str | Path, patch_path: str | Path):
        self.routing_path, self.truth_path, self.patch_path = map(Path, (routing_path, truth_path, patch_path))
        if len({p.resolve() for p in (self.routing_path, self.truth_path, self.patch_path)}) != 3:
            raise ValueError("routing, truth, and patch stores must be physically separate")

    def append_routing(self, record: dict[str, Any]) -> str:
        forbidden = FORBIDDEN_ROUTING_FIELDS & set(record)
        if forbidden:
            raise ValueError(f"forbidden routing-memory fields: {sorted(forbidden)}")
        self.routing_path.parent.mkdir(parents=True, exist_ok=True)
        value = {**record, "memory_hash": canonical_hash(record)}
        with self.routing_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, sort_keys=True) + "\n")
        return str(value["memory_hash"])

    def decision_records(self) -> list[dict[str, Any]]:
        if not self.routing_path.is_file():
            return []
        return [json.loads(line) for line in self.routing_path.read_text(encoding="utf-8").splitlines() if line]

    def join_truth_after_seal(self, sealed_decision_hash: str, truth: dict[str, Any]) -> dict[str, Any]:
        if sealed_decision_hash not in {row.get("memory_hash") for row in self.decision_records()}:
            raise ValueError("decision must be sealed before truth join")
        self.truth_path.parent.mkdir(parents=True, exist_ok=True)
        value = {"sealed_decision_hash": sealed_decision_hash, "truth": truth, "truth_hash": canonical_hash(truth)}
        with self.truth_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(value, sort_keys=True) + "\n")
        return value

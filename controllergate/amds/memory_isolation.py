from __future__ import annotations

import json
import sqlite3
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


class SqliteIsolationStores:
    """Four physically separate databases with role-specific connections."""

    def __init__(self, root: str | Path):
        root = Path(root)
        root.mkdir(parents=True, exist_ok=True)
        self.paths = {
            "routing": root / "routing-memory.sqlite",
            "truth": root / "sealed-truth.sqlite",
            "patch": root / "repair-proof.sqlite",
            "claims": root / "public-claims.sqlite",
        }
        if len({path.resolve() for path in self.paths.values()}) != 4:
            raise ValueError("memory stores must be physically separate")
        for role, path in self.paths.items():
            connection = sqlite3.connect(path)
            connection.execute("CREATE TABLE IF NOT EXISTS records(record_hash TEXT PRIMARY KEY, record_json TEXT NOT NULL)")
            connection.commit(); connection.close()

    def append_routing(self, record: dict[str, Any]) -> str:
        if FORBIDDEN_ROUTING_FIELDS & set(record) or {"candidate_id", "repository_id"} & set(record):
            raise ValueError("routing record contains forbidden retrieval feature")
        digest = canonical_hash(record)
        connection = sqlite3.connect(self.paths["routing"])
        connection.execute("INSERT INTO records VALUES (?,?)", (digest, json.dumps(record, sort_keys=True)))
        connection.commit(); connection.close()
        return digest

    def diagnostic_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(f"file:{self.paths['routing'].as_posix()}?mode=ro", uri=True)

    def forbidden_diagnostic_path(self, role: str) -> Path:
        if role != "routing":
            raise PermissionError("diagnostic process may read routing memory only")
        return self.paths[role]

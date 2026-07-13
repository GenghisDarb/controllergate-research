from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record
from .execution_record import ExecutionRecord


class ExecutionLedger:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def records(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def append(self, record: ExecutionRecord) -> dict[str, Any]:
        rows = self.records()
        record.ledger_parent_hash = rows[-1]["record_hash"] if rows else None
        value = record.to_dict()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(value, sort_keys=True) + "\n")
        return value

    def verify_chain(self) -> dict[str, Any]:
        rows = self.records()
        failures: list[int] = []
        parent = None
        for index, row in enumerate(rows):
            claimed = row.get("record_hash")
            check = dict(row)
            check["record_hash"] = None
            if row.get("ledger_parent_hash") != parent or hash_record(check) != claimed:
                failures.append(index)
            parent = claimed
        return {"status": "PASS" if not failures else "BLOCK", "record_count": len(rows), "failures": failures}

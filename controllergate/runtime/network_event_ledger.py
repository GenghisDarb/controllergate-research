from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record


def append_network_event(path: Path, event: dict[str, Any]) -> dict[str, Any]:
    previous = "0" * 64
    sequence = 1
    if path.is_file():
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if rows:
            previous = rows[-1]["event_hash"]; sequence = len(rows) + 1
    row = {**event, "sequence": sequence, "previous_event_hash": previous}
    row["event_hash"] = hash_record(row)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle: handle.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def verify_network_event_ledger(path: Path) -> dict[str, Any]:
    previous = "0" * 64; checked = 0
    for line in path.read_text(encoding="utf-8").splitlines() if path.is_file() else []:
        row = json.loads(line); supplied = row.pop("event_hash", None)
        if row.get("previous_event_hash") != previous or supplied != hash_record(row): return {"status": "BLOCK", "blocker": "network_event_hash_chain_invalid", "checked": checked}
        previous = str(supplied); checked += 1
    return {"status": "PASS", "checked": checked, "chain_head": previous}

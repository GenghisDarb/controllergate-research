from __future__ import annotations

from dataclasses import dataclass, asdict, field
import json
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record, write_json_deterministic


@dataclass(frozen=True)
class RuntimeCheckpoint:
    candidate_id: str
    plan_hash: str
    completed_phases: tuple[str, ...]
    terminal_status: str
    terminal_blocker: str | None
    spent_nonces: tuple[str, ...]
    event_chain_head: str
    checkpoint_hash: str = ""
    context_state: dict[str, Any] = field(default_factory=dict)


def seal_checkpoint(checkpoint: RuntimeCheckpoint) -> dict[str, Any]:
    value = asdict(checkpoint); value.pop("checkpoint_hash", None); value["checkpoint_hash"] = hash_record(value); return value


def write_checkpoint(path: Path, checkpoint: RuntimeCheckpoint) -> None:
    write_json_deterministic(path, seal_checkpoint(checkpoint))


def load_checkpoint(path: Path) -> dict[str, Any]:
    if not path.is_file(): return {"status": "NEW", "completed_phases": [], "spent_nonces": [], "event_chain_head": "0" * 64}
    value = json.loads(path.read_text(encoding="utf-8")); expected = value.get("checkpoint_hash"); unsigned = dict(value); unsigned.pop("checkpoint_hash", None)
    if expected != hash_record(unsigned): return {"status": "BLOCK", "blocker": "runtime_checkpoint_hash_invalid"}
    return {"status": "PASS", **value}

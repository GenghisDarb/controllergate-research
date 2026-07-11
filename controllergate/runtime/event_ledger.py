from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record, write_text_lf


@dataclass(frozen=True)
class RuntimeEvent:
    event_id: str
    phase_id: str
    status: str
    input_hash: str
    output_hash: str
    blocker: str | None
    parent_event_hash: str
    event_hash: str = ""


def append_event(path: Path, event: RuntimeEvent) -> dict[str, Any]:
    value = asdict(event); value.pop("event_hash", None); value["event_hash"] = hash_record(value)
    existing = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    write_text_lf(path, "\n".join([*existing, json.dumps(value, sort_keys=True)]))
    return value

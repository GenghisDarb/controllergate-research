from __future__ import annotations

import json
import os
from pathlib import Path

from .run_state import RunState


class StateStore:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()
        if str(self.root).upper().startswith("E:\\"):
            raise ValueError("authoritative_runtime_root_prohibited")
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, run_id: str) -> Path:
        return self.root / run_id / "state.json"

    def save(self, state: RunState) -> Path:
        path = self.path(state.run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state.record(), indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        os.replace(tmp, path)
        return path

    def load(self, run_id: str) -> RunState:
        return RunState.from_record(json.loads(self.path(run_id).read_text(encoding="utf-8")))

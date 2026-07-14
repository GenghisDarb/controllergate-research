from __future__ import annotations

import json
from pathlib import Path


def current_state(repo_root: str | Path) -> dict[str, object]:
    path = Path(repo_root) / "outputs" / "current" / "CURRENT_PROTOCOL_STATE.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    return {"protocol": value.get("protocol_version", value.get("version", "v2.19")),
            "status": value.get("status", "PASS"), "source": str(path)}

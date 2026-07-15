from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from controllergate.reactions.stable_identity import stable_hash


REQUIRED = {"run_id", "candidate_id", "fixture_root", "runtime_root", "incident_command", "patch_plan"}
ALLOWED_MODES = {"mechanism_rehearsal", "historical_repair", "historical_non_source", "canary", "rollback"}


def load_manifest(path: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    source = Path(path)
    value = json.loads(source.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED - set(value))
    runtime = Path(value.get("runtime_root", ".")).resolve()
    mode = value.get("execution_mode", "historical_repair")
    if mode == "historical_non_counting":
        mode = "historical_non_source"
    value["execution_mode"] = mode
    prohibited = str(runtime).upper().startswith("E:\\") or "ONEDRIVE" in str(runtime).upper() or "INCOMING_ARTIFACTS" in str(runtime).upper()
    mode_invalid = mode not in ALLOWED_MODES
    return value, {"status": "PASS" if not missing and not prohibited and not mode_invalid else "BLOCK", "missing": missing,
                   "runtime_root": str(runtime), "runtime_root_prohibited": prohibited,
                   "execution_mode": mode, "execution_mode_invalid": mode_invalid,
                   "manifest_hash": stable_hash(value)}

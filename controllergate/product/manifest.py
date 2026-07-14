from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from controllergate.reactions.stable_identity import stable_hash


REQUIRED = {"run_id", "candidate_id", "fixture_root", "runtime_root", "incident_command", "patch_plan"}


def load_manifest(path: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    source = Path(path)
    value = json.loads(source.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED - set(value))
    runtime = Path(value.get("runtime_root", ".")).resolve()
    prohibited = str(runtime).upper().startswith("E:\\") or "ONEDRIVE" in str(runtime).upper()
    return value, {"status": "PASS" if not missing and not prohibited else "BLOCK", "missing": missing,
                   "runtime_root": str(runtime), "runtime_root_prohibited": prohibited,
                   "manifest_hash": stable_hash(value)}

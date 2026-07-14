from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .engine import load_contracts


def audit_registry(repo_root: Path) -> dict:
    registry = json.loads((repo_root / "configs/controllergate_interlock_registry_v2.json").read_text(encoding="utf-8"))
    historical = repo_root / registry["historical_manifest_path"]
    digest = hashlib.sha256(historical.read_bytes()).hexdigest() if historical.is_file() else None
    contracts = load_contracts(repo_root)
    errors = []
    if digest != registry["historical_manifest_sha256"]: errors.append("historical_interlock_identity_mismatch")
    if len(contracts) != 23 or len({item.interlock_id for item in contracts}) != 23: errors.append("historical_interlock_set_incomplete")
    if any(item.can_authorize_patch for item in contracts): errors.append("interlock_illegally_authorizes_patch")
    return {"status": "PASS" if not errors else "FAIL", "interlock_count": len(contracts), "historical_manifest_sha256": digest, "errors": errors}

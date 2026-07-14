from __future__ import annotations

import json
from pathlib import Path

from .contract import InterlockContract
from .negative_regulation import apply_negative_regulation


def load_contracts(repo_root: Path) -> list[InterlockContract]:
    registry = json.loads((repo_root / "configs/controllergate_interlock_registry_v2.json").read_text(encoding="utf-8"))
    mapping = registry["canonical_scope_mapping"]
    return [InterlockContract(item, tuple(mapping.get(item, ("decision-time safety",))), reopen_condition=f"provide_verified_{item}_evidence") for item in registry["historical_interlock_ids"]]


def evaluate_interlocks(repo_root: Path, evidence_by_interlock: dict[str, dict]) -> dict:
    results = [apply_negative_regulation(contract, evidence_by_interlock.get(contract.interlock_id, {})) for contract in load_contracts(repo_root)]
    return {"status": "PASS" if all(item["status"] == "PASS" for item in results) else "BLOCK",
            "results": results, "interlock_count": len(results), "interlocks_can_authorize_patch": False}

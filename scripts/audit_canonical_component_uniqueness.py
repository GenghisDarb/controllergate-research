from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "product_engine", "dispatcher", "reaction_engine", "execution_broker", "state_store",
    "source_acquisition", "provider_planning", "provider_materialization", "provider_verification",
    "target_reproducer_resolution", "collection", "failure_classification", "AMDS_diagnosis",
    "routing_memory", "source_ownership", "patch_planning", "patch_application", "validation",
    "duplicate_replay", "canary", "health_monitoring", "rollback", "proof_ledger",
    "count_service", "connector_policy", "public_state_generation",
}


def audit() -> dict[str, object]:
    registry = json.loads((ROOT / "configs/controllergate_canonical_component_registry.json").read_text(encoding="utf-8"))
    components = registry.get("components", {})
    errors = []
    if set(components) != REQUIRED:
        errors.append("canonical_component_set_mismatch")
    if any(".batch" in value or value.startswith("scripts.generate_batch") for value in components.values()):
        errors.append("batch_component_selected_for_production")
    legacy = [json.loads(line) for line in (ROOT / "configs/controllergate_legacy_component_registry.jsonl").read_text(encoding="utf-8").splitlines() if line]
    if any(row.get("production_import_allowed") is not False for row in legacy):
        errors.append("legacy_production_import_allowed")
    return {"status": "PASS" if not errors else "FAIL", "component_count": len(components), "legacy_record_count": len(legacy), "errors": errors}


if __name__ == "__main__":
    result = audit()
    print(json.dumps(result, sort_keys=True))
    raise SystemExit(0 if result["status"] == "PASS" else 1)

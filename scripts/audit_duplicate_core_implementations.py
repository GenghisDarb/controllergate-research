from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def audit() -> dict[str, object]:
    registry=json.loads((ROOT/"configs/controllergate_canonical_component_registry.json").read_text(encoding="utf-8"))["components"]
    required={"product_engine","dispatcher","state_store","execution_broker","proof_ledger","count_service","AMDS_diagnosis","provider_verification"}
    errors=[]
    if not required <= set(registry): errors.append("critical_component_missing")
    legacy=[json.loads(line) for line in (ROOT/"configs/controllergate_legacy_component_registry.jsonl").read_text(encoding="utf-8").splitlines() if line]
    if any(row["production_import_allowed"] for row in legacy): errors.append("legacy_core_still_production_allowed")
    return {"status":"PASS" if not errors else "FAIL","errors":errors,"canonical_component_count":len(registry),"legacy_blocked_count":len(legacy)}


if __name__=="__main__":
    result=audit(); print(json.dumps(result,sort_keys=True)); raise SystemExit(result["status"]!="PASS")

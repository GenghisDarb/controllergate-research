from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {"IMPLEMENTED_AND_EXECUTED","IMPLEMENTED_FIXTURE_ONLY","IMPLEMENTED_HISTORICAL_REPLAY","PROSPECTIVE_PILOT_COMPLETE","BLOCKED_EXACT","DEFERRED_NAMED_BATCH","DEPRECATED_WITH_REASON"}
REQUIRED = {"requirement_id","category","name","historical_origin","current_evidence","actual_evidence_depth","status","owner_module","enforcer","acceptance_tests","required_artifacts","current_blocker","risk_if_ignored","next_legal_action","reopen_condition","claim_boundary","product_dependency","last_verified_head","record_hash"}


def main() -> int:
    source = ROOT / "configs/controllergate_loose_end_registry_v2.jsonl"
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    historical = [json.loads(line)["requirement_id"] for line in (ROOT / "configs/historical_requirement_registry_v1.jsonl").read_text(encoding="utf-8").splitlines() if line]
    errors = []
    for row in rows:
        if REQUIRED - set(row): errors.append(f"missing_fields:{row.get('requirement_id')}")
        if row.get("status") not in ALLOWED: errors.append(f"bad_status:{row.get('requirement_id')}")
        if not row.get("owner_module") or not row.get("enforcer"): errors.append(f"owner_missing:{row.get('requirement_id')}")
        for test in row.get("acceptance_tests", []):
            if not (ROOT / test.split("::", 1)[0]).is_file(): errors.append(f"acceptance_test_missing:{row.get('requirement_id')}:{test}")
        if row.get("status") == "BLOCKED_EXACT" and not row.get("reopen_condition"): errors.append(f"reopen_missing:{row.get('requirement_id')}")
        source_row = {key:value for key,value in row.items() if key != "record_hash"}
        expected = hashlib.sha256(json.dumps(source_row, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode()).hexdigest()
        if expected != row.get("record_hash"): errors.append(f"hash:{row.get('requirement_id')}")
    ids = {row["requirement_id"] for row in rows}
    errors.extend(f"historical_vanished:{rid}" for rid in historical if rid not in ids)
    for rid in ["CG-GAP-002","CG-GAP-003","CG-GAP-004","CG-GAP-005","CG-GAP-006","CG-GAP-013"]:
        if rid not in ids: errors.append(f"critical_dimension_missing:{rid}")
    print(json.dumps({"status":"PASS" if not errors else "FAIL","record_count":len(rows),"errors":errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__": raise SystemExit(main())

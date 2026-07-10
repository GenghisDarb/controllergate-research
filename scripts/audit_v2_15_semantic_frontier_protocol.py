from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.frontier_state import verify_state_hash
from controllergate.engine import FrontierEngine


def main() -> int:
    errors: list[str] = []
    current = ROOT / "outputs/current/CURRENT_PROTOCOL_STATE.json"
    if not current.is_file(): errors.append("current_protocol_state_missing")
    else:
        state = json.loads(current.read_text(encoding="utf-8"))
        if not verify_state_hash(state): errors.append("current_protocol_state_hash_invalid")
        if state.get("protocol_version") not in {"v2.15", "v2.16"}: errors.append("protocol_version_not_v2_15_or_approved_successor")
        if state.get("protocol_version") == "v2.15" and state.get("static_semantic_planning_promoted") is not True: errors.append("static_semantic_planning_not_promoted")
        if state.get("protocol_version") == "v2.16":
            promotion = ROOT / "outputs/post_v2_37_hardening_batch068h1_universal_interlock_elbow_harness_decomposition/v2_16_promotion_decision_batch068h1.json"
            if not promotion.is_file(): errors.append("v2_16_promotion_evidence_missing")
            else:
                record = json.loads(promotion.read_text(encoding="utf-8"))
                if record.get("status") != "PASS" or record.get("protocol_before") != "v2.15" or record.get("protocol_after") != "v2.16": errors.append("v2_16_promotion_evidence_invalid")
        if state.get("patch_authority") is not False: errors.append("patch_authority_changed")
        if state.get("repair_execution_authority") is not False: errors.append("repair_execution_authority_changed")
        if state.get("live_runtime_connectors") != "inactive": errors.append("live_runtime_connectors_changed")
        if state.get("full_scoring") != "NOT_RUN/disallowed": errors.append("full_scoring_changed")
        if state.get("memory_lift") != "not_demonstrated": errors.append("memory_claim_changed")
        if state.get("self_maintaining_software") != "false/not_demonstrated": errors.append("self_maintaining_claim_changed")
    out = ROOT / "outputs/post_v2_37_hardening_batch068h_semantic_pathway_secure_provider_probe"
    for name in ["semantic_step_resolution_audit_batch068h.json", "static_planning_protocol_promotion_decision_batch068h.json", "v2_14_preservation_audit_batch068h.json"]:
        path = out / name
        if not path.is_file() or json.loads(path.read_text(encoding="utf-8")).get("status") != "PASS": errors.append(f"required_protocol_evidence_failed:{name}")
    try:
        if FrontierEngine(ROOT).validate().get("status") != "PASS": errors.append("frontier_engine_validation_failed")
    except Exception as exc:
        errors.append(f"frontier_engine_error:{type(exc).__name__}")
    v214 = subprocess.run([sys.executable, str(ROOT / "scripts/audit_v2_14_capability_recovery_lane.py")], cwd=ROOT, capture_output=True)
    if v214.returncode != 0: errors.append("historical_v2_14_audit_failed")
    if errors:
        print("v2.15 semantic frontier protocol audit FAIL")
        print("\n".join(errors)); return 1
    print("v2.15 semantic frontier protocol audit PASS")
    return 0


if __name__ == "__main__": raise SystemExit(main())

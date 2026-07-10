from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from controllergate.core.frontier_state import verify_state_hash


def main() -> int:
    errors: list[str] = []
    state_path = ROOT / "outputs/current/CURRENT_PROTOCOL_STATE.json"
    if not state_path.is_file(): errors.append("current_state_missing")
    else:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if not verify_state_hash(state): errors.append("current_state_hash_invalid")
        version = state.get("protocol_version")
        if version == "v2.17":
            promotion_path = ROOT / "outputs/post_v2_37_hardening_batch068h2_tld_brot_bulb_topology_runtime_historical_capsule_recovery/v2_17_topology_promotion_decision.json"
            promotion = json.loads(promotion_path.read_text(encoding="utf-8")) if promotion_path.is_file() else {}
            if promotion.get("status") != "PASS" or promotion.get("protocol_before") != "v2.16": errors.append("v2_17_successor_not_approved")
        elif version != "v2.16": errors.append("protocol_not_v2_16_or_approved_successor")
        if version == "v2.16" and state.get("universal_interlock_runtime_status") != "PASS": errors.append("interlock_runtime_not_pass")
        if version == "v2.16" and state.get("elbow_runtime_status") != "PASS": errors.append("elbow_runtime_not_pass")
        if state.get("patch_authority") is not False or state.get("repair_execution_authority") is not False: errors.append("repair_authority_changed")
        if state.get("full_scoring") != "NOT_RUN/disallowed": errors.append("full_scoring_changed")
        if state.get("memory_lift") != "not_demonstrated": errors.append("memory_claim_changed")
        if state.get("self_maintaining_software") != "false/not_demonstrated": errors.append("self_maintaining_claim_changed")
    out = ROOT / "outputs/post_v2_37_hardening_batch068h1_universal_interlock_elbow_harness_decomposition"
    for name in ["interlock_resolution_audit_batch068h1.json", "semantic_runtime_pathway_audit_batch068h1.json", "v2_15_preservation_audit_batch068h1.json", "v2_16_promotion_decision_batch068h1.json"]:
        path = out / name
        if not path.is_file() or json.loads(path.read_text(encoding="utf-8")).get("status") != "PASS": errors.append(f"protocol_evidence_failed:{name}")
    v215 = subprocess.run([sys.executable, str(ROOT / "scripts/audit_v2_15_semantic_frontier_protocol.py")], cwd=ROOT, capture_output=True)
    if v215.returncode != 0: errors.append("v2_15_preservation_audit_failed")
    if errors:
        print("v2.16 universal interlock elbow runtime audit FAIL"); print("\n".join(errors)); return 1
    print("v2.16 universal interlock elbow runtime audit PASS"); return 0


if __name__ == "__main__": raise SystemExit(main())

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from controllergate.core.frontier_state import verify_state_hash
from controllergate.protocols.v2_18_evidence_derived_topology_historical_provider import runtime_capabilities


def main() -> int:
    errors: list[str] = []
    state = json.loads((ROOT / "outputs/current/CURRENT_PROTOCOL_STATE.json").read_text(encoding="utf-8"))
    if not verify_state_hash(state): errors.append("current_state_hash_invalid")
    if state.get("protocol_version") == "v2.19":
        promotion_path = ROOT / "outputs/post_v2_37_hardening_batch070_v2_19_amds_fifth_repair_sprint/v2_19_promotion_decision_batch070.json"
        if not promotion_path.is_file(): errors.append("v2_19_successor_promotion_missing")
        else:
            promotion = json.loads(promotion_path.read_text(encoding="utf-8"))
            if promotion.get("status") != "PASS" or promotion.get("protocol_before") != "v2.18" or promotion.get("protocol_after") != "v2.19": errors.append("v2_19_successor_promotion_invalid")
    elif state.get("protocol_version") != "v2.18": errors.append("protocol_not_v2_18_or_approved_successor")
    elif state.get("patch_authority") is not False or state.get("repair_execution_authority") is not False or state.get("target_test_execution_authority") is not False: errors.append("execution_authority_changed")
    if runtime_capabilities().get("status") != "PASS" or runtime_capabilities().get("unbound_reusable_mechanisms") != []: errors.append("runtime_bindings_invalid")
    batch = subprocess.run([sys.executable, str(ROOT / "scripts/audit_batch068h3_historical_transitive_provider_closure_topology_hardening.py")], cwd=ROOT)
    if batch.returncode != 0: errors.append("batch068h3_audit_failed")
    prior = subprocess.run([sys.executable, str(ROOT / "scripts/audit_v2_17_topology_runtime.py")], cwd=ROOT, capture_output=True)
    if prior.returncode != 0: errors.append("v2_17_preservation_failed")
    if errors:
        print("v2.18 evidence-derived topology historical-provider audit FAIL")
        print("\n".join(errors)); return 1
    print("v2.18 evidence-derived topology historical-provider audit PASS")
    return 0


if __name__ == "__main__": raise SystemExit(main())

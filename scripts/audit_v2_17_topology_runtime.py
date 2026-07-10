from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.frontier_state import verify_state_hash

OUT = ROOT / "outputs/post_v2_37_hardening_batch068h2_tld_brot_bulb_topology_runtime_historical_capsule_recovery"


def load(name: str) -> dict[str, object]:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    state = json.loads((ROOT / "outputs/current/CURRENT_PROTOCOL_STATE.json").read_text(encoding="utf-8"))
    if not verify_state_hash(state): errors.append("current_state_hash_invalid")
    if state.get("protocol_version") != "v2.17": errors.append("protocol_not_v2_17")
    if state.get("topology_runtime_status") != "PASS": errors.append("topology_runtime_not_pass")
    if state.get("patch_authority") is not False or state.get("repair_execution_authority") is not False: errors.append("repair_authority_changed")
    if state.get("target_test_execution_authority") is not False: errors.append("target_test_authority_changed")
    if state.get("full_scoring") != "NOT_RUN/disallowed" or state.get("memory_lift") != "not_demonstrated" or state.get("self_maintaining_software") != "false/not_demonstrated": errors.append("claim_boundary_changed")
    for name in ["reference_core_5.json", "contact_ledger_14.json", "activation_license_6.json", "proof_matrix_196.json", "tot_brot_coupled_graph.json", "tot_bulb_environment_volume.json", "tld_shadow_assay.json", "v2_16_preservation_audit_batch068h2.json", "v2_17_topology_promotion_decision.json"]:
        if not (OUT / name).is_file() or load(name).get("status") not in {"PASS", "NOT_ESTABLISHED"}: errors.append(f"protocol_evidence_failed:{name}")
    if load("activation_license_6.json").get("license_result") != "BLOCK": errors.append("activation_license_not_blocked")
    if load("proof_matrix_196.json").get("matrix_status") != "PLANNED": errors.append("proof_matrix_not_planned")
    if errors:
        print("v2.17 canonical topology environment volume runtime audit FAIL"); print("\n".join(errors)); return 1
    print("v2.17 canonical topology environment volume runtime audit PASS"); return 0


if __name__ == "__main__":
    raise SystemExit(main())

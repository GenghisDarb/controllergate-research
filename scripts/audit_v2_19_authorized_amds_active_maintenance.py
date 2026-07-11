from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.frontier_state import verify_state_hash
from controllergate.protocols.v2_19_authorized_amds_active_maintenance import RUNTIME_BINDINGS, runtime_capabilities


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    errors: list[str] = []
    state = load(ROOT / "outputs/current/CURRENT_PROTOCOL_STATE.json")
    frontier = load(ROOT / "outputs/frontier/CURRENT_FRONTIER_STATE.json")
    promotion = load(ROOT / "outputs/post_v2_37_hardening_batch070_v2_19_amds_fifth_repair_sprint/v2_19_promotion_decision_batch070.json")
    if not verify_state_hash(state): errors.append("current_state_hash_invalid")
    if state.get("protocol_version") != "v2.19": errors.append("protocol_not_v2_19")
    if state.get("patch_authority") != "conditional_source_only": errors.append("patch_authority_not_conditional_source_only")
    if state.get("repair_execution_authority") != "conditional_authorized": errors.append("repair_execution_authority_invalid")
    if state.get("full_scoring") != "NOT_RUN/disallowed": errors.append("full_scoring_boundary_changed")
    if state.get("memory_lift") != "not_demonstrated": errors.append("memory_lift_overclaim")
    if state.get("self_maintaining_software") != "false/not_demonstrated": errors.append("self_maintaining_overclaim")
    if frontier.get("validated_current_protocol") != "v2.19 authorized_amds_active_maintenance_lane": errors.append("frontier_not_v2_19")
    capabilities = runtime_capabilities()
    if capabilities.get("status") != "PASS" or capabilities.get("runtime_binding_count") != 22: errors.append("runtime_bindings_invalid")
    if capabilities.get("batch_specific_current_bindings") != []: errors.append("batch_specific_current_bindings_present")
    if any("batch068h" in value for value in RUNTIME_BINDINGS.values()): errors.append("batch_specific_binding_target_present")
    if promotion.get("status") != "PASS" or promotion.get("protocol_before") != "v2.18" or promotion.get("protocol_after") != "v2.19": errors.append("promotion_record_invalid")
    batch = subprocess.run([sys.executable, str(ROOT / "scripts/audit_batch070_v2_19_amds_fifth_repair_sprint.py")], cwd=ROOT, capture_output=True, text=True)
    if batch.returncode != 0: errors.append("batch070_audit_failed:" + batch.stdout.strip().replace("\n", ";"))
    batch071_path = ROOT / "outputs/post_v2_37_hardening_batch071_live_v2_19_command_repair_continuation/batch071_final_decision.json"
    if batch071_path.is_file():
        batch071 = subprocess.run([sys.executable, str(ROOT / "scripts/audit_batch071_live_v2_19_command_repair_continuation.py")], cwd=ROOT, capture_output=True, text=True)
        if batch071.returncode != 0: errors.append("batch071_audit_failed:" + batch071.stdout.strip().replace("\n", ";"))
    prior = subprocess.run([sys.executable, str(ROOT / "scripts/audit_v2_18_evidence_derived_topology_historical_provider.py")], cwd=ROOT, capture_output=True, text=True)
    if prior.returncode != 0: errors.append("v2_18_preservation_failed:" + prior.stdout.strip().replace("\n", ";"))
    if errors:
        print("v2.19 authorized AMDS active maintenance audit FAIL")
        print("\n".join(errors))
        return 1
    print("v2.19 authorized AMDS active maintenance audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

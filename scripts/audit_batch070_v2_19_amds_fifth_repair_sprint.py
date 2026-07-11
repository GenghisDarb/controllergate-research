from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.constraints import ALLOWED_CONSTRAINT_TYPES, constraint_semantics_registry
from controllergate.protocols.v2_19_authorized_amds_active_maintenance import RUNTIME_BINDINGS, runtime_capabilities

OUT = ROOT / "outputs/post_v2_37_hardening_batch070_v2_19_amds_fifth_repair_sprint"


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def verify_manifest() -> list[str]:
    errors: list[str] = []
    manifest = OUT / "SHA256SUMS.txt"
    if not manifest.is_file(): return ["batch070_manifest_missing"]
    for line in manifest.read_text(encoding="utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]): errors.append("batch070_manifest_malformed"); continue
        path = OUT / parts[1].lstrip("*")
        if not path.is_file(): errors.append(f"batch070_manifest_missing:{parts[1]}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != parts[0]: errors.append(f"batch070_manifest_mismatch:{parts[1]}")
    return errors


def main() -> int:
    errors = verify_manifest()
    required = {
        "batch068h9_artifact_ingest.json", "batch068h9_state_preservation.json", "batch068h9_claim_boundary_preservation.json",
        "v2_19_production_binding_audit.json", "v2_19_batch_specific_binding_removal.json", "amds_generic_board_construction_batch070.json",
        "amds_constraint_semantics_batch070.json", "amds_persistent_posterior_batch070.json", "amds_backtracking_integration_batch070.json",
        "amds_canonical_probe_authorization_batch070.json", "amds_semantic_verification_batch070.json", "amds_information_gain_planner_batch070.json",
        "amds_completion_decisions_batch070.json", "batch070_candidate_portfolio_policy.json", "batch070_candidate_portfolio_frozen.json",
        "batch070_candidate_ranking_trace.jsonl", "batch070_candidate_execution_results.json", "batch070_candidate_terminal_states.json",
        "batch070_repair_and_count_decision.json", "amds_prospective_shadow_pilot_batch070.json", "batch070_operational_law_audit.json",
        "v2_19_promotion_decision_batch070.json", "batch071_cold_start_handoff.json", "batch071_exact_next_actions.json",
        "batch071_blocker_or_validation_matrix.json", "batch070_final_decision.json", "batch070_claim_boundary.json", "batch070_summary.md", "SHA256SUMS.txt",
    }
    missing = sorted(name for name in required if not (OUT / name).is_file())
    if missing: errors.append("required_outputs_missing:" + ",".join(missing))
    if len(list(OUT.glob("*"))) > 40: errors.append("batch070_evidence_not_compact")
    ingest = load("batch068h9_artifact_ingest.json")
    if ingest.get("status") != "PASS" or ingest.get("observed_size_bytes") != 204279 or ingest.get("observed_sha256") != "7061224d5ff8e790b9bf492d9826ebac4e1f6710c96b2c872683522abf61be6b" or ingest.get("file_count") != 106: errors.append("h9_identity_invalid")
    for key, count in (("outer_manifest", 105), ("h8_internal_manifest", 70), ("h9_internal_manifest", 24)):
        if ingest.get(key, {}).get("status") != "PASS" or ingest.get(key, {}).get("checked") != count: errors.append(f"h9_manifest_invalid:{key}")
    preserved = load("batch068h9_claim_boundary_preservation.json")
    if preserved.get("issue_derived_repair_count") != 4: errors.append("h9_repair_count_changed_on_ingest")
    h9state = load("batch068h9_state_preservation.json")
    if not h9state.get("candidate_retired"): errors.append("nbclient_not_retired")
    capabilities = runtime_capabilities()
    if capabilities.get("status") != "PASS" or capabilities.get("runtime_binding_count") != 22: errors.append("generic_bindings_invalid")
    if capabilities.get("batch_specific_current_bindings") or any("batch068h" in value for value in RUNTIME_BINDINGS.values()): errors.append("batch_specific_current_binding_present")
    posterior = load("amds_persistent_posterior_batch070.json")
    if posterior.get("status") != "PASS" or any(item.get("posterior_event_count", 0) < 1 for item in posterior.get("demonstrations", [])): errors.append("posterior_state_not_persistent")
    backtracking = load("amds_backtracking_integration_batch070.json")
    if backtracking.get("status") != "PASS" or backtracking.get("backtracking_components", 0) < 1: errors.append("bounded_backtracking_not_invoked")
    if set(constraint_semantics_registry()) != ALLOWED_CONSTRAINT_TYPES: errors.append("constraint_semantics_incomplete")
    auth = load("amds_canonical_probe_authorization_batch070.json")
    if auth.get("status") != "PASS" or auth.get("first_use", {}).get("status") != "PASS" or auth.get("second_use", {}).get("blocker") != "amds_probe_nonce_already_spent": errors.append("authorization_not_single_use")
    semantic = load("amds_semantic_verification_batch070.json")
    if semantic.get("status") != "PASS" or not semantic.get("custody_and_semantic_layers_separate"): errors.append("semantic_verification_not_independent")
    planner = load("amds_information_gain_planner_batch070.json")
    if planner.get("status") != "PASS" or not planner.get("dynamic_regeneration") or not planner.get("outranking_recorded"): errors.append("dynamic_probe_planning_missing")
    portfolio = load("batch070_candidate_portfolio_frozen.json"); policy = load("batch070_candidate_portfolio_policy.json")
    candidates = portfolio.get("candidates", [])
    if portfolio.get("status") != "PASS" or not portfolio.get("frozen_before_execution") or len(candidates) > 3: errors.append("portfolio_freeze_invalid")
    if not policy.get("ranking_formula_frozen_before_execution") or not policy.get("prior_patch_candidates_excluded"): errors.append("portfolio_policy_invalid")
    if any(item.get("prior_patch_exists") or item.get("retired") or item.get("previously_counted") for item in candidates): errors.append("ineligible_candidate_in_fresh_arm")
    execution = load("batch070_candidate_execution_results.json").get("results", [])
    if len(execution) > 3: errors.append("candidate_execution_limit_exceeded")
    if len(execution) != len(candidates): errors.append("terminal_candidate_did_not_advance")
    if any(not item.get("terminal_prepatch") or item.get("patch_generated") or item.get("count_gate") != "NOT_RUN" for item in execution): errors.append("prepatch_terminal_or_count_boundary_invalid")
    if any(item.get("rollback_status") != "PASS" or item.get("proof_ledger_status") != "PASS" or item.get("routing_memory_status") != "PASS" for item in execution): errors.append("terminal_rollback_or_ledger_cleanup_missing")
    decision = load("batch070_repair_and_count_decision.json")
    if decision.get("patch_authorizations") != 0 or decision.get("patches_generated") != 0 or decision.get("duplicate_clean_replays") != 0 or decision.get("count_gate") != "NOT_RUN": errors.append("patch_or_count_gate_ran_early")
    if decision.get("issue_derived_repair_count_after") not in {4, 5}: errors.append("repair_count_out_of_range")
    pilot = load("amds_prospective_shadow_pilot_batch070.json")
    if pilot.get("AMDS_PROSPECTIVE_EFFECTIVENESS") != "NOT_ESTABLISHED" or len(pilot.get("arms", [])) != 4 or not pilot.get("matched_probe_budget"): errors.append("prospective_pilot_claim_boundary_invalid")
    law = load("batch070_operational_law_audit.json")
    if law.get("status") != "PASS" or law.get("TLD_role") != "shadow_metrology_nonblocking": errors.append("operational_law_or_tld_boundary_invalid")
    promotion = load("v2_19_promotion_decision_batch070.json")
    if promotion.get("status") != "PASS" or promotion.get("protocol_before") != "v2.18" or promotion.get("protocol_after") != "v2.19": errors.append("v2_19_promotion_invalid")
    handoff = load("batch071_cold_start_handoff.json")
    if handoff.get("status") != "PASS" or not handoff.get("primary_objective") or len(load("batch071_exact_next_actions.json").get("actions", [])) < 1: errors.append("batch071_handoff_incomplete")
    claims = load("batch070_claim_boundary.json")
    if claims.get("full_scoring") != "NOT_RUN/disallowed" or claims.get("memory_lift") != "not_demonstrated" or claims.get("self_maintaining_software") != "false/not_demonstrated": errors.append("claim_boundary_overreach")
    if errors:
        print("Batch070 v2.19 AMDS fifth-repair sprint audit FAIL")
        print("\n".join(errors))
        return 1
    print("Batch070 v2.19 AMDS fifth-repair sprint audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

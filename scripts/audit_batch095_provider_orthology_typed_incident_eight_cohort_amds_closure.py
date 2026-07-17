from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "post_v2_37_hardening_batch095_provider_orthology_typed_incident_eight_cohort_amds_closure"


def load(name: str) -> dict:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def rows(name: str) -> list[dict]:
    path = OUTPUT / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    errors: list[str] = []
    required = [
        "batch094_artifact_ingest.json", "batch094_artifact_manifest_verification.json",
        "batch095_worktree_official_head_reconciliation.json", "batch095_pre_fix_provider_orthology_and_typed_incident_expected_failure.json",
        "batch095_blocker_dependency_graph.json", "provider_recipe_schema_v2.json", "provider_recipe_registry_v2.jsonl",
        "provider_recipe_selection_receipts.jsonl", "provider_recipe_verification_receipts.jsonl", "provider_identity_uniqueness_audit.json",
        "incident_outcome_contract_schema.json", "incident_outcome_contracts.jsonl", "incident_outcome_future_evidence_scan.json",
        "external_human_authorization_gate_v2.json", "protected_continuation_contract.json",
        "reactome_stoichiometry_shadow_decision.json", "reactome_product_dependency_audit.json",
        "batch095_internal_release_decision.json", "batch095_claim_boundary.json", "batch095_consolidated_state.json", "campaign_summary.md",
        "ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt",
    ]
    for name in required:
        if not (OUTPUT / name).is_file() or (OUTPUT / name).stat().st_size == 0:
            errors.append(f"missing_or_empty:{name}")
    if errors:
        print(json.dumps({"status": "BLOCK", "errors": errors}, sort_keys=True)); return 1
    ingest = load("batch094_artifact_ingest.json")
    manifest = load("batch094_artifact_manifest_verification.json")
    if ingest.get("status") != "PASS" or manifest.get("status") != "PASS": errors.append("batch094_artifact_custody")
    if load("batch095_worktree_official_head_reconciliation.json").get("status") != "PASS": errors.append("worktree_reconciliation")
    if load("batch095_pre_fix_provider_orthology_and_typed_incident_expected_failure.json").get("status") != "BATCH095_PRE_FIX_AUDIT_FAIL_EXPECTED": errors.append("expected_red")
    recipes = rows("provider_recipe_registry_v2.jsonl")
    contracts = rows("incident_outcome_contracts.jsonl")
    if len(recipes) != 8 or len(contracts) != 8: errors.append("frozen_eight_contract_count")
    if any(not row.get("selection_frozen_before_target_execution") for row in recipes): errors.append("provider_selected_after_outcome")
    identities = [row.get("provider_identity") for row in recipes]
    if len(set(identities)) != 8: errors.append("provider_identity_collision")
    if load("provider_identity_uniqueness_audit.json").get("status") != "PASS": errors.append("provider_identity_audit")
    allowed_families = {"NONZERO_FAILURE", "SUCCESS_WITH_INVALID_PRODUCT", "SUCCESS_WITH_STATE_DEFECT", "WARNING_ONLY_FAILURE", "IMPORT_OR_COLLECTION_FAILURE", "TRANSPORT_OR_SERVICE_FAILURE", "SAFE_ABSTENTION_INSUFFICIENT_EVIDENCE"}
    if any(row.get("expected_process_level_outcome") not in allowed_families for row in contracts): errors.append("incident_family")
    cohort_path = OUTPUT / "historical_eight_episode_materialization_gate.json"
    if cohort_path.exists():
        cohort = load("historical_eight_episode_materialization_gate.json")
        if cohort.get("candidate_substitutions") != 0 or cohort.get("patch_operation_count") != 0 or cohort.get("historical_count_increment") != 0: errors.append("cohort_guardrail")
        role = load("role_measurement_quality_gate_v3.json")
        if cohort.get("status") == "EIGHT_EPISODE_SEMANTIC_MATERIALIZATION_PASS":
            if role.get("execution_receipt_count") != 80 or role.get("verification_receipt_count") != 80 or role.get("pass_count") != 80: errors.append("role_boundary")
        else:
            if (OUTPUT / "role_measurement_execution_receipts_v3.jsonl").exists() or (OUTPUT / "amds_controller_audit_terminals_v4.jsonl").exists(): errors.append("downstream_evidence_after_cohort_block")
    authorization = load("external_human_authorization_gate_v2.json")
    if authorization.get("status") != "HUMAN_AUTHORIZATION_BLOCKED_EXACT" or authorization.get("repository_generated_approval") is not False: errors.append("ordinary_authorization_boundary")
    dependency = load("reactome_product_dependency_audit.json")
    if dependency.get("active_product_blocker") is not False: errors.append("stoichiometry_shadow_promoted")
    claim = load("batch095_claim_boundary.json")
    expected = {"protocol": "v2.19", "package_version": "0.2.0b2.dev0", "issue_derived_repair_count": 6, "native_external_repair_count": 4, "historical_increment": 0, "full_scoring": "NOT_RUN/disallowed", "production_readiness": False, "self_maintaining_software": "false/not demonstrated"}
    if any(claim.get(key) != value for key, value in expected.items()): errors.append("claim_boundary")
    decision = load("batch095_internal_release_decision.json")
    if decision.get("status") != "PRODUCT_BETA_RC_BLOCKED_EXACT" or not decision.get("Product_Beta_PASS_forbidden"): errors.append("release_overclaim")
    state = load("batch095_consolidated_state.json")
    if not state.get("active_blockers") or not state.get("dormant_external_conditions") or not state.get("claim_boundaries") or not state.get("shadow_capability_limitations"): errors.append("typed_public_state_sections")
    for name in ("ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt"):
        text = (OUTPUT / name).read_text(encoding="utf-8")
        if any(line.endswith(f"  {name}") for line in text.splitlines()): errors.append(f"self_manifest:{name}")
    result = {"status": "PASS" if not errors else "BLOCK", "error_count": len(errors), "errors": errors, "release_decision": decision.get("status"), "protocol": claim.get("protocol")}
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from controllergate.core.command_authority_resolver import resolve_command_authority
from controllergate.core.command_role_classifier import classify_command
from controllergate.core.command_sources.tox_parser import parse_tox
from controllergate.core.evidence import hash_record
from controllergate.protocols.v2_19_authorized_amds_active_maintenance import RUNTIME_BINDINGS, runtime_capabilities

OUT = ROOT / "outputs/post_v2_37_hardening_batch071_live_v2_19_command_repair_continuation"


def load(name: str) -> dict: return json.loads((OUT / name).read_text(encoding="utf-8"))


def verify_manifest() -> list[str]:
    errors = []; seen = set(); manifest = OUT / "SHA256SUMS.txt"
    if not manifest.is_file(): return ["batch071_manifest_missing"]
    for line in manifest.read_text(encoding="utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]): errors.append("batch071_manifest_malformed"); continue
        digest, rel = parts; rel = rel.lstrip("*"); path = OUT / rel; seen.add(rel)
        if not path.is_file(): errors.append(f"batch071_manifest_missing:{rel}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest: errors.append(f"batch071_manifest_mismatch:{rel}")
    expected = {path.name for path in OUT.iterdir() if path.is_file() and path.name != "SHA256SUMS.txt"}
    if seen != expected: errors.append("batch071_manifest_coverage_invalid")
    return errors


def main() -> int:
    errors = verify_manifest()
    required = {"batch070_artifact_ingest.json", "batch070_state_preservation.json", "batch070_claim_boundary_preservation.json", "v2_19_binding_depth_registry_batch071.json", "v2_19_manifest_trust_audit_batch071.json", "v2_19_live_execution_readiness_batch071.json", "batch071_candidate_reconciliation.json", "batch071_corrected_portfolio_policy.json", "batch071_corrected_portfolio_frozen.json", "batch071_portfolio_freeze_hash.json", "batch070_checkpoint_validity_audit_batch071.json", "batch071_checkpoint_rebase_plan.json", "command_authority_resolution_batch071.json", "batch071_live_candidate_execution.json", "live_amds_evidence_batch071.json", "batch071_patch_validation_and_count.json", "batch071_prospective_amds_pilot.json", "batch072_prospective_validation_design.json", "batch072_cold_start_handoff.json", "batch072_exact_next_actions.json", "batch072_candidate_and_validation_matrix.json", "batch071_final_decision.json", "batch071_claim_boundary.json", "batch071_summary.md", "SHA256SUMS.txt"}
    missing = sorted(name for name in required if not (OUT / name).is_file())
    if missing: errors.append("required_outputs_missing:" + ",".join(missing))
    if len(list(OUT.iterdir())) > 40: errors.append("batch071_evidence_not_compact")
    ingest = load("batch070_artifact_ingest.json")
    if ingest.get("status") != "PASS" or ingest.get("observed_size_bytes") != 227309 or ingest.get("observed_sha256") != "4a1fb82890b6d4b12456437a6db93c730d6c9c535bbb42605c135976281e7f87" or ingest.get("file_count") != 136: errors.append("batch070_artifact_identity_invalid")
    for key, count in (("outer", 135), ("h8", 70), ("h9", 24), ("batch070", 28)):
        if ingest.get("manifests", {}).get(key, {}).get("status") != "PASS" or ingest.get("manifests", {}).get(key, {}).get("checked") != count: errors.append(f"artifact_manifest_invalid:{key}")
    if ingest.get("unsafe_paths") or ingest.get("duplicate_path_count") or ingest.get("forbidden_payloads"): errors.append("artifact_custody_invalid")
    reconciliation = load("batch071_candidate_reconciliation.json")
    if reconciliation.get("biface") != "solution_guidance_contaminated_for_fresh_authoritative_repair": errors.append("biface_not_excluded")
    if reconciliation.get("hipo_corrected_target") != "tests/test_relations.py::TestPresentablePrimaryKeyRelatedField::test_read_source_with_context": errors.append("hipo_target_not_corrected")
    if reconciliation.get("connexion_target") != "tests/test_utils.py::test_sort_routes" or not reconciliation.get("connexion_setup_commands_separated"): errors.append("connexion_target_or_command_separation_invalid")
    portfolio = load("batch071_corrected_portfolio_frozen.json")
    if not portfolio.get("frozen_before_outcomes") or len(portfolio.get("candidates", [])) != 3 or portfolio.get("freeze_hash") != hash_record_without_freeze(portfolio): errors.append("portfolio_freeze_invalid")
    ids = [item["candidate_id"] for item in portfolio.get("candidates", [])]
    if "codex_wave3_biface_i18n_issues_86" in ids or ids[-1] != "codex_wave3_aio_libs_aiosmtpd_issues_403": errors.append("portfolio_replacement_invalid")
    checkpoint = load("batch070_checkpoint_validity_audit_batch071.json")
    if checkpoint.get("h70_manifest_trust_checkpoints_are_live_evidence") is not False: errors.append("h70_checkpoint_trust_not_invalidated")
    depth = load("v2_19_binding_depth_registry_batch071.json").get("records", [])
    audited = {"acquire_source", "reconstruct_environment", "resolve_provider_closure", "recover_authoritative_command", "reproduce_prerepair_failure", "classify_failure_ownership", "derive_patch_locality", "generate_bounded_source_patch", "validate_target_and_invariants", "run_duplicate_clean_replay", "execute_count_gate"}
    by_name = {row["binding"]: row for row in depth}
    if not audited.issubset(by_name): errors.append("binding_depth_records_missing")
    if any(not by_name[name].get("live_operation_implemented") for name in audited): errors.append("manifest_trust_function_not_replaced")
    if any(row.get("generalization_demonstrated") for row in depth): errors.append("binding_generalization_overclaim")
    if runtime_capabilities().get("status") != "PASS" or any("batch068h" in target for target in RUNTIME_BINDINGS.values()): errors.append("v2_19_bindings_invalid")
    parser_source = ROOT / "controllergate/core/command_sources/tox_parser.py"
    if "lstrip().startswith(\"#\")" not in parser_source.read_text(encoding="utf-8") or "condition" not in parser_source.read_text(encoding="utf-8"): errors.append("tox_comment_or_condition_semantics_missing")
    if classify_command(["black", "."]) != "formatter_mutating" or classify_command(["python", "-m", "pytest", "tests"]) != "test_runner": errors.append("command_role_semantics_invalid")
    execution = load("batch071_live_candidate_execution.json")
    results = execution.get("results", [])
    if not execution.get("canonical_dispatcher") or len(results) != 2: errors.append("canonical_live_execution_invalid")
    if any(row["summary"].get("source_acquisition") != "PASS" or row["summary"].get("environment") != "PASS" or row["summary"].get("provider_closure") != "PASS" for row in results): errors.append("live_source_or_provider_not_demonstrated")
    if any(row["summary"].get("duplicate_collection_count") != 2 or row["summary"].get("prerepair_reproduction_count") != 2 for row in results): errors.append("live_collection_or_replay_missing")
    hipo, connexion = results
    if hipo["summary"].get("ownership") != "test_expectation_fragility" or hipo["summary"].get("patch_generated"): errors.append("hipo_ownership_or_patch_boundary_invalid")
    c = connexion["summary"]
    if c.get("ownership") != "source_owned_behavior_defect" or not c.get("patch_plan") or not c.get("patch_generated"): errors.append("connexion_live_ownership_or_patch_plan_missing")
    if c.get("modified_files") != ["connexion/utils.py"]: errors.append("source_only_patch_boundary_invalid")
    patch_path = OUT / "codex_wave3_spec_first_connexion_issues_2012_source_only_patch.diff"
    if not patch_path.is_file() or "tests/" in patch_path.read_text(encoding="utf-8") or "pyproject.toml" in patch_path.read_text(encoding="utf-8"): errors.append("patch_diff_invalid")
    if c.get("target_validation") != 0 or c.get("invariant_validation") != 0 or c.get("duplicate_replay") != "PASS" or c.get("count_gate") != "PASS": errors.append("validation_duplicate_replay_or_count_failed")
    phases = c.get("completed_phases", [])
    required_order = ["reproduce_prerepair_failure", "classify_failure_ownership", "derive_patch_locality", "authorize_source_patch", "generate_bounded_source_patch", "validate_target_and_invariants", "run_duplicate_clean_replay", "execute_count_gate"]
    if any(phases.index(a) >= phases.index(b) for a, b in zip(required_order, required_order[1:])): errors.append("patch_or_count_gate_order_invalid")
    amds = load("live_amds_evidence_batch071.json")
    if amds.get("placeholder_hashes_used") or not amds.get("boundary_constraints_enforced_in_patch_authorization") or any(row.get("posterior_updates", 0) < 1 or row.get("backtracking_components", 0) < 1 or row.get("semantic_verifications", 0) < 1 for row in amds.get("records", [])): errors.append("live_amds_evidence_invalid")
    pilot = load("batch071_prospective_amds_pilot.json")
    if not pilot.get("arms_operationally_separate") or not pilot.get("matched_budgets") or pilot.get("AMDS_PROSPECTIVE_EFFECTIVENESS") != "NOT_ESTABLISHED" or pilot.get("superiority_claim"): errors.append("prospective_pilot_boundary_invalid")
    decision = load("batch071_patch_validation_and_count.json")
    if decision.get("issue_derived_repair_count_after") not in {4, 5} or not decision.get("count_gate_could_not_run_early"): errors.append("repair_count_proof_invalid")
    if decision.get("issue_derived_repair_count_after") != 5: errors.append("connexion_count_gate_did_not_establish_fifth_repair")
    final = load("batch071_final_decision.json")
    if final.get("validated_protocol") != "v2.19" or final.get("v2_19_interface_status") != "PASS" or final.get("v2_19_live_execution_status") != "PASS": errors.append("v2_19_status_invalid")
    if final.get("full_scoring") != "NOT_RUN/disallowed" or final.get("memory_lift") != "not_demonstrated" or final.get("self_maintaining_software") != "false/not_demonstrated" or final.get("live_connectors") != "inactive": errors.append("claim_boundary_overreach")
    handoff = load("batch072_cold_start_handoff.json")
    if handoff.get("status") != "PASS" or not handoff.get("primary_objective") or not load("batch072_exact_next_actions.json").get("actions"): errors.append("batch072_handoff_incomplete")
    forbidden_public_terms = ("TORUS", "BROT", "BULB", "chromosomal", "Reactome")
    public_paths = [OUT / "batch071_summary.md"]
    if any(term.lower() in path.read_text(encoding="utf-8").lower() for path in public_paths for term in forbidden_public_terms): errors.append("public_language_audit_failed")
    if errors:
        print("Batch071 live v2.19 command repair continuation audit FAIL"); print("\n".join(errors)); return 1
    print("Batch071 live v2.19 command repair continuation audit PASS"); return 0


def hash_record_without_freeze(value: dict) -> str:
    unsigned = {key: item for key, item in value.items() if key != "freeze_hash"}
    return hash_record(unsigned)


if __name__ == "__main__": raise SystemExit(main())

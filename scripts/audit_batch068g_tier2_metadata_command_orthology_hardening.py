from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import sha256_file
from controllergate.core.frontier_state import verify_state_hash
from controllergate.engine import FrontierEngine

OUT = ROOT / "outputs" / "post_v2_37_hardening_batch068g_tier2_metadata_command_orthology_hardening"

REQUIRED = [
    "batch068f_artifact_ingestion_summary.json", "batch068f_artifact_outer_identity_verification.json",
    "batch068f_artifact_entry_audit.json", "batch068f_artifact_internal_manifest_verification.json",
    "batch068f_result_preservation.json", "batch068f_candidate_state_preservation.json",
    "batch068f_claim_boundary_preservation.json", "command_orthology_policy_v1_batch068g.json",
    "command_source_precedence_policy_batch068g.json", "command_token_safety_policy_batch068g.json",
    "runner_target_split_policy_batch068g.json", "harness_origin_static_policy_batch068g.json",
    "provider_feasibility_static_policy_batch068g.json", "tier3_promotion_policy_batch068g.json",
    "candidate_terminal_state_vocabulary_batch068g.json", "frontier_static_step_contract_batch068g.json",
    "frontier_step_handler_registry_batch068g.json", "frontier_step_verifier_registry_batch068g.json",
    "frontier_step_resolution_audit_batch068g.json", "frontier_transition_graph_batch068g.json",
    "candidate_state_index_batch068g.json", "command_evidence_graph_registry_batch068g.json",
    "native_target_path_verification_registry_batch068g.json", "command_orthology_results_batch068g.json",
    "runner_target_split_results_batch068g.json", "harness_origin_results_batch068g.json",
    "provider_feasibility_results_batch068g.json", "tier3_candidate_promotion_registry_batch068g.json",
    "tier3_provider_probe_plan_registry_batch068g.json", "tier3_candidate_ranking_batch068g.json",
    "tier2_to_tier3_blocker_distribution_batch068g.json", "candidate_terminal_state_registry_batch068g.json",
    "batch_local_to_core_promotion_result_batch068g.json", "core_module_reuse_map_batch068g.json",
    "candidate_specific_hardcoding_audit_batch068g.json", "frontier_engine_component_registry_batch068g.json",
    "runtime_activation_evidence_policy_batch068g.json", "runtime_activation_watchdog_result_batch068g.json",
    "runtime_activation_missing_evidence_vector_batch068g.json", "workflow_reuse_result_batch068g.json",
    "regression_audit_registry_result_batch068g.json", "redundancy_consolidation_plan_batch068g.json",
    "historical_evidence_preservation_result_batch068g.json", "safe_deletion_decision_batch068g.json",
    "frontier_state_render_verification_batch068g.json", "negative_control_results_batch068g.json",
    "public_claim_boundary_audit_batch068g.json", "batch068g_final_decision.json",
    "batch068g_handoff_plan.json", "batch068g_summary.md", "SHA256SUMS.txt",
]


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def verify_manifest(errors: list[str]) -> None:
    manifest = OUT / "SHA256SUMS.txt"
    covered = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split(maxsplit=1)
        rel = rel.strip().lstrip("*")
        covered.add(rel)
        path = OUT / rel
        require(path.is_file(), f"manifest_missing:{rel}", errors)
        if path.is_file():
            require(sha256_file(path) == digest, f"manifest_mismatch:{rel}", errors)
    actual = {path.relative_to(OUT).as_posix() for path in OUT.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"}
    require(covered == actual, "manifest_coverage_mismatch", errors)


def main() -> int:
    errors: list[str] = []
    for name in REQUIRED:
        require((OUT / name).is_file(), f"missing:{name}", errors)
    if errors:
        print("Batch068g audit FAIL")
        print("\n".join(errors))
        return 1
    verify_manifest(errors)
    outer = load(OUT / "batch068f_artifact_outer_identity_verification.json")
    entry = load(OUT / "batch068f_artifact_entry_audit.json")
    internal = load(OUT / "batch068f_artifact_internal_manifest_verification.json")
    preserve = load(OUT / "batch068f_result_preservation.json")
    claims = load(OUT / "batch068f_claim_boundary_preservation.json")
    require(outer["status"] == "PASS" and outer["observed_size"] == 256844 and outer["observed_sha256"] == "3b7788b1b6bf2a60406a2eba2c82f3850a907c742ff4534ed88c468fce9727ec", "batch068f_outer_identity", errors)
    require(entry["status"] == "PASS" and entry["entry_count"] == 86 and not entry["unsafe_paths"] and not entry["duplicate_paths"], "batch068f_entry_audit", errors)
    require(internal["status"] == "PASS" and internal["artifact_manifest"]["checked"] == 85 and internal["output_manifest"]["checked"] == 84, "batch068f_internal_manifest", errors)
    require(preserve["tier2_candidate_count"] == 25 and preserve["external_seed_sha_verified_count"] == 5 and preserve["existing_backlog_sha_verified_count"] == 20, "batch068f_counts", errors)
    require(claims["issue_derived_repair_count"] == 4 and claims["native_external_repair_count"] == 4, "batch068f_repair_counts", errors)

    index = load(OUT / "candidate_state_index_batch068g.json")
    require(index["candidate_count"] == 25 and len(index["records"]) == 25, "candidate_count_not_25", errors)
    require(len({item["candidate_id"] for item in index["records"]}) == 25, "candidate_duplicate_or_dropped", errors)
    promotion = load(OUT / "tier3_candidate_promotion_registry_batch068g.json")
    for item in index["records"]:
        path = ROOT / item["state_path"]
        require(path.is_file(), f"candidate_state_missing:{item['candidate_id']}", errors)
        if not path.is_file():
            continue
        state = load(path)
        require(verify_state_hash(state), f"state_hash_invalid:{item['candidate_id']}", errors)
        require(state["state_hash"] == item["state_hash"], f"index_hash_mismatch:{item['candidate_id']}", errors)
        require(re.fullmatch(r"[0-9a-f]{40}", state["candidate_sha"]) is not None, f"candidate_sha_invalid:{item['candidate_id']}", errors)
        require(all(source.get("candidate_sha") == state["candidate_sha"] and re.fullmatch(r"[0-9a-f]{64}", source.get("sha256", "")) for source in state["metadata_source_files"]), f"metadata_source_hash_or_sha_invalid:{item['candidate_id']}", errors)
        require(isinstance(state["command_argv"], list), f"command_not_argv:{item['candidate_id']}", errors)
        require(not state["decision_time_evidence_manifest"]["forbidden_evidence_used"], f"forbidden_evidence:{item['candidate_id']}", errors)
        require(state["target_tests_executed"] == 0 and state["provider_probe_executed"] is False, f"execution_occurred:{item['candidate_id']}", errors)
        require(state["patch_generated"] is False and state["patch_applied"] is False, f"patch_occurred:{item['candidate_id']}", errors)
        require(len(state["gate_statuses"]) == 11, f"step_count_invalid:{item['candidate_id']}", errors)
        require(all(step["handler_name"] and step["verifier_name"] and step["post_state_hash"] for step in state["gate_statuses"]), f"step_record_incomplete:{item['candidate_id']}", errors)
        if state["tier_label"].startswith("Tier 3"):
            require(state["target_path_verification"]["status"] == "PASS", f"tier3_target_path_unverified:{item['candidate_id']}", errors)
            require(state["selected_command_candidate"] is not None, f"tier3_command_missing:{item['candidate_id']}", errors)
            require(state["harness_origin_status"]["status"] == "PASS", f"tier3_harness_origin:{item['candidate_id']}", errors)
            require(state["provider_feasibility_class"] != "provider_metadata_missing", f"tier3_provider_unclassified:{item['candidate_id']}", errors)
        else:
            require(bool(state["exact_blocker"]) and bool(state["reopen_conditions"]), f"blocked_state_missing_reopen:{item['candidate_id']}", errors)
    require(promotion["meaning"] == "future bounded static provider-command probe authorization only", "tier3_meaning_invalid", errors)

    resolution = load(OUT / "frontier_step_resolution_audit_batch068g.json")
    hardcoding = load(OUT / "candidate_specific_hardcoding_audit_batch068g.json")
    negative = load(OUT / "negative_control_results_batch068g.json")
    require(resolution["status"] == "PASS" and not resolution["unresolved_handlers"] and not resolution["unresolved_verifiers"], "step_registry_resolution", errors)
    require(hardcoding["candidate_specific_hardcoding_count"] == 0, "candidate_specific_hardcoding", errors)
    require(negative["status"] == "PASS" and all(value.get("status") == "PASS" for key, value in negative.items() if key != "status"), "negative_controls", errors)
    require(load(OUT / "public_claim_boundary_audit_batch068g.json")["status"] == "PASS", "public_claim_boundary", errors)
    require(load(OUT / "historical_evidence_preservation_result_batch068g.json")["status"] == "PASS", "historical_preservation", errors)
    require(load(OUT / "safe_deletion_decision_batch068g.json")["safe_to_delete_now_count"] == 0, "safe_deletion_count", errors)
    watchdog = load(OUT / "runtime_activation_watchdog_result_batch068g.json")
    require(watchdog["runtime_wrapper_activation_allowed"] is False and watchdog["repair_count_is_necessary_but_not_sufficient"] is True, "runtime_watchdog", errors)
    final = load(OUT / "batch068g_final_decision.json")
    require(final["target_tests_executed"] == 0 and final["provider_probes_executed"] == 0, "batch_execution_boundary", errors)
    require(final["patch_generated"] is False and final["patch_applied"] is False and final["repair_count_increment"] is False, "batch_patch_or_count_boundary", errors)
    require(final["full_scoring"] == "NOT_RUN/disallowed" and final["memory_lift"] == "not_demonstrated" and final["self_maintaining_software"] == "false/not_demonstrated", "claim_boundary", errors)
    require(final["validated_current_protocol"] == "v2.14" and final["frontier_protocol_promoted"] is False, "protocol_boundary", errors)
    engine = FrontierEngine(ROOT)
    require(engine.validate()["status"] == "PASS", "frontier_engine_validate", errors)
    sample = index["records"][0]["candidate_id"]
    require(engine.plan(sample)["status"] == "PASS", "frontier_engine_plan", errors)

    current = subprocess.run([sys.executable, str(ROOT / "scripts/controllergate_audit.py"), "--protocol", "current"], cwd=ROOT, text=True, capture_output=True, check=False)
    dry = subprocess.run([sys.executable, str(ROOT / "scripts/controllergate_run.py"), "--protocol", "current", "--dry-run"], cwd=ROOT, text=True, capture_output=True, check=False)
    require(current.returncode == 0 and "v2.14" in current.stdout, "current_protocol_audit", errors)
    require(dry.returncode == 0, "current_protocol_dry_run", errors)
    registry = load(ROOT / "configs/controllergate_regression_audit_registry.json")
    require(registry["status"] == "PASS" and all((ROOT / item["script_path"]).is_file() for item in registry["audits"] if item["required"]), "regression_audit_registry", errors)

    if errors:
        print("Batch068g tier2 metadata command orthology hardening audit FAIL")
        for error in errors:
            print(error)
        return 1
    print("Batch068g tier2 metadata command orthology hardening audit PASS")
    print(f"tier2_candidates=25 tier3_candidates={promotion['promotion_count']} current_protocol=v2.14")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

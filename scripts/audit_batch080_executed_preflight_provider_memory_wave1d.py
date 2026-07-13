from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch080_executed_preflight_provider_memory_wave1d"
EXPECTED_BATCH079_SIZE = 998670
EXPECTED_BATCH079_SHA = "f6a883915e31e91dceb601e5728d338f9b072cfc10acf75cb1e6223ae2c7a4ff"


def load(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def jsonl(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    failures: list[str] = []
    required = [
        "batch079_artifact_ingest.json", "batch079_state_preservation.json",
        "batch079_claim_boundary_preservation.json", "batch079_count6_hardening_preservation.json",
        "batch079_incident_preflight_depth_reconciliation.json", "batch079_recovery_depth_reconciliation.json",
        "batch079_hordeforge_depth_reconciliation.json", "batch079_memory_calibration_depth_reconciliation_v2.json",
        "batch080_incident_lead_pool_freeze.json", "batch080_static_preflight_records.jsonl",
        "batch080_preflight_funnel.json", "batch080_execution_frame_freeze.json",
        "batch080_native_target_registry.jsonl", "batch080_issue_reproducer_registry.jsonl",
        "batch080_provider_capsule_registry.jsonl", "batch080_provider_capsule_sbom.json",
        "batch080_batch078_recovery_stage_ledger.jsonl", "batch080_batch078_collection_diagnostics.json",
        "batch080_batch078_provider_diagnostics.json", "batch080_batch078_recovery_decision.json",
        "batch080_hordeforge_execution_proof.json", "batch080_hordeforge_execution_decision.json",
        "pathway_memory_calibration_v3_preregistration.json", "pathway_memory_v3_identity_registry.jsonl",
        "pathway_memory_v3_holdout_results.jsonl", "pathway_memory_v3_baseline_rankings.jsonl",
        "pathway_memory_v3_shuffled_corpus.jsonl", "pathway_memory_v3_metrics.json",
        "pathway_memory_v3_decision.json", "batch080_duplicate_failure_admission.json",
        "batch080_admitted_cohort_freeze.json", "batch080_comparative_arm_execution_summary.json",
        "batch080_matched_null_preregistration.json", "batch080_matched_null_results.json",
        "batch080_blinded_ground_truth.json", "batch080_authoritative_repair_decision.json",
        "batch080_public_claim_boundary.json", "batch080_final_decision.json", "campaign_summary.md", "SHA256SUMS.txt",
    ]
    for name in required:
        if not (OUT / name).is_file():
            failures.append("missing:" + name)
    if failures:
        return report(failures)

    ingest = load("batch079_artifact_ingest.json")
    if ingest.get("status") != "PASS" or ingest.get("observed_size_bytes") != EXPECTED_BATCH079_SIZE or ingest.get("observed_sha256") != EXPECTED_BATCH079_SHA:
        failures.append("batch079_artifact_identity")
    if ingest.get("file_count") != 383 or ingest.get("outer_manifest", {}).get("checked") != 382 or ingest.get("outer_manifest", {}).get("failures") != []:
        failures.append("batch079_outer_manifest")
    internal_expected = {
        "post_v2_37_hardening_batch073_count5_revalidation_frozen_wave1": 41,
        "post_v2_37_hardening_batch074_sterile_high_yield_amds_memory_wave1": 16,
        "post_v2_37_hardening_batch075_provider_harness_amds_memory_wave1a": 106,
        "post_v2_37_hardening_batch076_amds_causal_memory_calibration": 32,
        "post_v2_37_hardening_batch077_typed_event_pathway_memory_v2": 47,
        "post_v2_37_hardening_batch078_count6_minimal_closure_memory_wave1b": 61,
        "post_v2_37_hardening_batch079_count6_runtime_incident_memory_wave1c": 58,
    }
    internals = ingest.get("internal_manifests", {})
    for label, checked in internal_expected.items():
        record = internals.get(label, {})
        if record.get("checked") != checked or record.get("failures") != []:
            failures.append("batch079_internal_manifest:" + label)

    preservation = load("batch079_count6_hardening_preservation.json")
    if preservation.get("COUNT_6_HARDENING") != "COUNT_6_HARDENING_PASS" or preservation.get("rerun") or preservation.get("recount"):
        failures.append("count_six_preservation")
    incident_reconciliation = load("batch079_incident_preflight_depth_reconciliation.json")
    if incident_reconciliation.get("classification") != "REGISTERED_NOT_EXECUTED_STATIC_PREFLIGHT" or incident_reconciliation.get("promoted_as_executed_evidence") is not False or any(incident_reconciliation.get(key) != 0 for key in ("target_resolution_attempts", "command_resolution_attempts", "provider_dry_lock_attempts", "file_collection_attempts")):
        failures.append("batch079_hardcoded_preflight_promoted")
    if load("batch079_recovery_depth_reconciliation.json").get("classification") != "PARTIAL_RECOVERY_DIAGNOSTICS_ONLY":
        failures.append("batch079_recovery_depth")
    h79 = load("batch079_hordeforge_depth_reconciliation.json")
    if h79.get("native_target_execution") != "NOT_ESTABLISHED" or h79.get("adapter_defect_fixed") != "NOT_ESTABLISHED":
        failures.append("batch079_hordeforge_correction")
    memory_depth = load("batch079_memory_calibration_depth_reconciliation_v2.json")
    if memory_depth.get("forbidden_conclusion") != "STATISTICAL_MEMORY_LIFT_PROVED" or memory_depth.get("prospective_memory_outcome_present") is not False:
        failures.append("batch079_memory_overclaim")

    preflight = jsonl("batch080_static_preflight_records.jsonl")
    funnel = load("batch080_preflight_funnel.json")
    if len(preflight) != 20 or funnel.get("registered_leads") != 20 or funnel.get("source_verification_attempts") != 20 or not funnel.get("every_lead_has_terminal_record"):
        failures.append("executed_preflight_coverage")
    source_commands: set[tuple[str, ...]] = set()
    for row in preflight:
        stages = row.get("stages", {})
        if not row.get("terminal") or set(("issue_snapshot", "source", "runtime", "target", "command", "provider_dry_lock", "collection", "contamination")) - set(stages):
            failures.append("preflight_stage_missing:" + str(row.get("candidate_id")))
            continue
        source = stages["source"]
        for attempt in source.get("attempts", []):
            argv = tuple(attempt.get("argv", []))
            if argv:
                source_commands.add(argv)
        if source.get("status") == "PASS":
            if source.get("object_type") != "commit" or source.get("head") != row.get("candidate_sha") or not re.fullmatch(r"[0-9a-f]{40}", source.get("tree_hash", "")) or not source.get("tree_identity_verified"):
                failures.append("source_identity:" + row["candidate_id"])
        target = stages["target"]
        if target.get("status") == "PASS" and not target.get("target_exists"):
            failures.append("target_pass_without_target:" + row["candidate_id"])
        command = stages["command"]
        if command.get("status") == "PASS" and (command.get("command_authority") != "project_local_metadata" or not command.get("selected", {}).get("transformed_command")):
            failures.append("command_pass_without_authority:" + row["candidate_id"])
        dry = stages["provider_dry_lock"]
        if dry.get("status") == "PASS" and (dry.get("provider_lock_version") != 3 or not dry.get("dependency_roots") or dry.get("provider_bytes_acquired")):
            failures.append("provider_dry_lock_invalid:" + row["candidate_id"])
        collection = stages["collection"]
        if collection.get("target_executed") is not False:
            failures.append("target_executed_during_preflight:" + row["candidate_id"])
    if len(source_commands) < 2:
        failures.append("source_verification_constant_or_unexecuted")

    native = jsonl("batch080_native_target_registry.jsonl")
    reproducers = jsonl("batch080_issue_reproducer_registry.jsonl")
    if not native or not reproducers or any(row.get("lane") == "ISSUE_DERIVED_REPRODUCER_LANE" for row in native) or any(row.get("lane") != "ISSUE_DERIVED_REPRODUCER_LANE" for row in reproducers):
        failures.append("native_issue_lane_separation")
    contaminated = next((row for row in preflight if row.get("candidate_id") == "incident_pytest_asyncio_1501"), None)
    if contaminated is None or contaminated.get("stages", {}).get("contamination", {}).get("status") != "BLOCK" or contaminated.get("terminal", {}).get("admitted_to_execution_frame"):
        failures.append("pytest_asyncio_1501_unsanitized_admission")

    capsules = jsonl("batch080_provider_capsule_registry.jsonl")
    for capsule in capsules:
        if capsule.get("provider_lock_version") != 3 or not capsule.get("platform") or not capsule.get("runtime") or not capsule.get("python_abi") or capsule.get("provider_bytes_committed"):
            failures.append("provider_capsule_binding:" + str(capsule.get("candidate_id")))
    if load("batch080_provider_capsule_sbom.json").get("provider_bytes_stored_in_main_artifact") is not False:
        failures.append("provider_bytes_in_main_artifact")
    forbidden_suffixes = {".whl", ".zip", ".tar", ".tgz", ".pyc", ".pyo"}
    if any(path.suffix.lower() in forbidden_suffixes for path in OUT.rglob("*") if path.is_file()):
        failures.append("forbidden_provider_payload")

    recovery = load("batch080_batch078_recovery_decision.json")
    if len(recovery.get("records", [])) != 4 or recovery.get("classification") != "HISTORICAL_RECOVERY_DIAGNOSTICS_ONLY":
        failures.append("batch078_stage_forensics")
    ledger = jsonl("batch080_batch078_recovery_stage_ledger.jsonl")
    if len({row.get("candidate_id") for row in ledger}) != 4 or not all(row.get("stage") and row.get("status") for row in ledger):
        failures.append("batch078_stage_ledger")
    horde = load("batch080_hordeforge_execution_proof.json")
    sentinels = horde.get("sentinels", {})
    target_proven = sentinels.get("TARGET_STARTED") is True and sentinels.get("TARGET_COMPLETED") is True
    if load("batch080_hordeforge_execution_decision.json").get("target_execution_proven") != target_proven:
        failures.append("hordeforge_sentinel_classification")
    if not target_proven and horde.get("result") == "CONTROLLERGATE_ADAPTER_DEFECT_FIXED":
        failures.append("hordeforge_false_closure")
    if load("batch080_hordeforge_execution_decision.json").get("docker_pull_output_alone_accepted") is not False:
        failures.append("hordeforge_docker_pull_only")

    identities = jsonl("pathway_memory_v3_identity_registry.jsonl")
    if not identities or any(row.get("repository_identity") == row.get("episode_id") or not str(row.get("repository_identity", "")).startswith("https://github.com/") for row in identities):
        failures.append("memory_repository_identities")
    prereg = load("pathway_memory_calibration_v3_preregistration.json")
    if prereg.get("evaluation") != "leave_one_independence_group_out" or prereg.get("frozen_before_Wave1D") is not True:
        failures.append("memory_preregistration")
    baseline_rows = jsonl("pathway_memory_v3_baseline_rankings.jsonl")
    methods = {row.get("method") for row in baseline_rows}
    required_methods = {"real_memory", "no_memory", "uniform_random", "seeded_random", "frequency_only", "shuffled_memory"}
    if not required_methods <= methods or any(not row.get("ranking") for row in baseline_rows):
        failures.append("memory_baseline_execution")
    shuffled = jsonl("pathway_memory_v3_shuffled_corpus.jsonl")
    if not shuffled or all(row.get("original_terminal_class_hash") == hashlib.sha256(str(row.get("shuffled_terminal_class", "")).encode()).hexdigest() for row in shuffled):
        failures.append("shuffled_memory_not_persisted_permutation")
    metrics = load("pathway_memory_v3_metrics.json")
    for method in required_methods:
        summary = metrics.get("methods", {}).get(method, {})
        if not {"micro_mrr", "macro_mrr", "micro_top1", "macro_top1", "per_class"} <= set(summary):
            failures.append("memory_metrics:" + method)
    if load("pathway_memory_v3_decision.json").get("MEMORY_LIFT_PROVED") is not False:
        failures.append("memory_lift_overclaim")

    frame = load("batch080_execution_frame_freeze.json")
    if not frame.get("frozen_before_target_execution") or frame.get("target_execution_count_at_freeze") != 0 or frame.get("adaptive_replenishment") is not False or frame.get("initial_pool_count") != 20:
        failures.append("execution_frame_order_or_replenishment")
    admitted = load("batch080_admitted_cohort_freeze.json").get("candidate_count", 0)
    arms = load("batch080_comparative_arm_execution_summary.json")
    nulls = load("batch080_matched_null_results.json")
    repairs = load("batch080_authoritative_repair_decision.json")
    if admitted == 0 and (arms.get("executed_arm_count") != 0 or nulls.get("executed_replicates") != 0 or repairs.get("attempts") != 0):
        failures.append("downstream_execution_without_admission")
    if not arms.get("all_arms_isolated") or arms.get("observation_sharing") or arms.get("posterior_sharing") or arms.get("patch_authority"):
        failures.append("comparative_arm_isolation")
    if nulls.get("synthetic_utilities") != 0 or nulls.get("duplicate_sequences_counted_independently"):
        failures.append("matched_null_execution_integrity")
    blinded = load("batch080_blinded_ground_truth.json")
    if not all(blinded.get(key) is True for key in ("sealed_before_adjudication", "adjudicator_strategy_blind", "adjudicator_memory_condition_blind", "adjudicator_probe_order_blind", "adjudicator_arm_result_blind")):
        failures.append("blinded_ground_truth")
    if repairs.get("memory_condition") != "NO_MEMORY" or repairs.get("memory_supplied_patch_content") is not False or repairs.get("maximum_attempts", 99) > 2:
        failures.append("authoritative_repair_boundary")

    claims = load("batch080_public_claim_boundary.json")
    if claims.get("current_protocol") != "v2.19" or claims.get("issue_derived_repairs") != 6 or claims.get("native_external_repairs") != 4 or claims.get("memory_lift") != "not demonstrated" or claims.get("self_maintaining_software") != "false/not demonstrated":
        failures.append("public_claim_boundary")
    if not (ROOT / "docs" / "QUICKSTART.md").is_file() or not (ROOT / "docs" / "CAPABILITY_AND_CLAIM_MATRIX.md").is_file() or not (ROOT / "scripts" / "run_local_controllergate_demo.py").is_file():
        failures.append("public_quickstart_surface")

    expected: dict[str, str] = {}
    for line in (OUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, name = line.split("  ", 1)
        expected[name] = digest
    actual = [path for path in OUT.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"]
    if len(expected) != len(actual):
        failures.append("manifest_coverage")
    for path in actual:
        name = path.relative_to(OUT).as_posix()
        if expected.get(name) != hashlib.sha256(path.read_bytes()).hexdigest():
            failures.append("manifest_hash:" + name)

    final = load("batch080_final_decision.json")
    if final.get("validated_protocol", "").split()[0] != "v2.19" or final.get("issue_derived_repair_count") != 6 or final.get("native_external_repair_count") != 4 or final.get("full_scoring") != "NOT_RUN/disallowed" or final.get("live_connectors") != "inactive":
        failures.append("final_claim_boundary")
    return report(failures)


def report(failures: list[str]) -> int:
    print("Batch080 audit:", "PASS" if not failures else "FAIL")
    if failures:
        print("\n".join(failures))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

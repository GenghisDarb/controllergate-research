#!/usr/bin/env python3
"""Audit v2.10 materialization recovery and topology-aware repair artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_10_materialization_recovery_topological_repair"
V29_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_9_topological_source_discovery"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_10_materialization_recovery_topological_repair.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_10_materialization_recovery_topological_repair_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_10_prepare_materialization_recovery_topological_repair.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

BASELINE = {"youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"}
POSITIVE_BASELINE = {"ansible:2", "ansible:5"}

REQUIRED_TOP_LEVEL = [
    "campaign_summary.md",
    "campaign_results.json",
    "decision_report.json",
    "aggregate_report.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "preserved_v2_9_baseline_gate_result.json",
    "bounded_dependency_materialization_recovery_v2_10.json",
    "dependency_cofactor_map_v2_10.json",
    "fixture_materialization_map_v2_10.json",
    "materialization_recovery_decision_log_v2_10.json",
    "v2_9_context_reuse_manifest_v2_10.json",
    "context_bundle_to_repair_plan_v2_10.json",
    "post_materialization_topological_source_discovery_v2_10.json",
    "materialization_recovery_candidate_pool_v2_10.json",
    "repair_path_taxonomy_v2_10.json",
    "duplicate_clean_replay_verification_v2_10.json",
    "phase_inversion_seed_constraint_check_v2_10.json",
    "heterochromatin_monitor_v2_10.json",
    "silent_scaffolding_risk_audit_v2_10.json",
    "memory_arm_separation_check_v2_10.json",
    "memory_evidence_eligibility_check_v2_10.json",
    "observer_state_separation_check_v2_10.json",
    "materialization_recovery_integrity_check_v2_10.json",
    "dependency_recovery_anti_leakage_check_v2_10.json",
    "isomorphism_requirements_matrix_v2_10.json",
    "positive_memory_family_generalization_v2_10.json",
    "harness_sanity_check.json",
    "command_normalization_policy.json",
    "candidate_chromatin_state_v2_10.json",
    "local_tension_relief_v2_10.json",
    "minimal_probe_selection_v2_10.json",
    "candidate_triage_stability_audit_v2_10.json",
    "closure_scaling_audit.json",
    "memory_lift_decomposition.json",
    "broad_candidate_preflight_registry.json",
    "replacement_candidate_policy.json",
    "replacement_candidate_preflight_summary.json",
    "fixture_dependency_preflight_summary.json",
    "candidate_ranking_policy.json",
    "bounded_repair_proposer_summary.json",
    "candidate_pool.json",
    "candidate_source_integrity_check.json",
    "decision_time_policy.json",
    "anti_leakage_policy.json",
    "source_discovery_summary.json",
    "pre_repair_replay_gate_summary.json",
    "workspace_equivalence_summary.json",
    "source_repair_vs_harness_separation.json",
    "classification_vocabulary_check.json",
    "audit.json",
    "package_verification.json",
    "artifact_sha256_verification.json",
    "SHA256SUMS.txt",
]

REQUIRED_EPISODE = [
    "episode_metadata.json",
    "candidate_preflight_result.json",
    "fixture_dependency_preflight_result.json",
    "command_normalization_result.json",
    "dependency_materialization_recovery_result.json",
    "dependency_cofactor_result.json",
    "fixture_materialization_result.json",
    "context_bundle_reuse_result.json",
    "post_materialization_topological_source_discovery_result.json",
    "environmental_stress_state_result.json",
    "chromatin_state_result.json",
    "heterochromatin_monitor_result.json",
    "silent_scaffolding_risk_result.json",
    "repair_path_taxonomy_result.json",
    "checkpoint_cycle_result.json",
    "candidate_senescence_result.json",
    "local_tension_relief_result.json",
    "minimal_probe_selection_result.json",
    "memory_arm_role.json",
    "duplicate_clean_replay_result.json",
    "phase_inversion_seed_constraint_result.json",
    "failing_command.txt",
    "normalized_failing_command.txt",
    "failing_log_raw.txt",
    "failure_signature.txt",
    "source_discovery_report.json",
    "ranked_candidate_source_files.json",
    "candidate_function_extracts.json",
    "repair_heuristic_selection.json",
    "no_memory_repair_candidate_generation.json",
    "memory_enabled_repair_candidate_generation.json",
    "no_memory_source_only_repair_patch.diff",
    "memory_enabled_source_only_repair_patch.diff",
    "patch_candidate_safety_check.json",
    "no_memory_patch_application_result.json",
    "memory_enabled_patch_application_result.json",
    "no_memory_post_repair_command.txt",
    "memory_enabled_post_repair_command.txt",
    "no_memory_post_repair_log_raw.txt",
    "memory_enabled_post_repair_log_raw.txt",
    "post_repair_comparison.json",
    "limited_scoring_result.json",
    "decision_time_input_manifest.json",
    "decision_time_outcome_overlap_check.json",
    "label_blindness_check.json",
    "gold_patch_exclusion_check.json",
    "corruption_check_result.json",
    "wrapper_contamination_check.json",
    "repair_materialization_separation.json",
    "proof_obligations_ledger.json",
    "SHA256SUMS.txt",
]


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"missing JSON file: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{path}: invalid JSON: {exc.msg}"]
    return (data if isinstance(data, dict) else {}), ([] if isinstance(data, dict) else [f"{path}: expected JSON object"])


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_manifest(directory: Path) -> list[str]:
    manifest = directory / "SHA256SUMS.txt"
    if not manifest.exists():
        return [f"missing SHA256SUMS.txt in {directory}"]
    errors: list[str] = []
    seen: set[str] = set()
    for line_no, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            errors.append(f"{manifest}:{line_no}: expected '<sha256>  <path>'")
            continue
        expected, rel = parts
        seen.add(rel)
        path = directory / rel
        if not path.exists():
            errors.append(f"{manifest}:{line_no}: missing artifact {rel}")
            continue
        if sha_file(path) != expected:
            errors.append(f"{manifest}:{line_no}: hash mismatch for {rel}")
    for path in directory.rglob("*"):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rel = str(path.relative_to(directory)).replace("\\", "/")
            if rel not in seen:
                errors.append(f"SHA256SUMS missing artifact entry {rel}")
    return errors


def status_is_pass(data: dict[str, Any]) -> bool:
    return data.get("status") == "PASS"


def candidate_project(candidate: str) -> str:
    return candidate.split(":", 1)[0]


def bad_candidate_strings(data: Any, path: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in {"candidate", "candidate_id"} and isinstance(value, str) and value.strip().startswith("{"):
                errors.append(f"{path}.{key}: stringified candidate metadata")
            errors.extend(bad_candidate_strings(value, f"{path}.{key}"))
    elif isinstance(data, list):
        for index, value in enumerate(data):
            errors.extend(bad_candidate_strings(value, f"{path}[{index}]"))
    return errors


def main() -> int:
    errors: list[str] = []
    for path in [WORKFLOW, RUNNER, PREP]:
        if not path.exists():
            errors.append(f"missing v2.10 implementation file: {path}")

    v29_campaign, e = load_json(V29_OUTPUT_DIR / "campaign_results.json")
    errors.extend(e)
    if v29_campaign:
        if v29_campaign.get("preserved_v2_8w_baseline_gate_status") != "PASS":
            errors.append("v2.10 requires verified v2.9/v2.8w preserved baseline")
        if int(v29_campaign.get("scoreable_episode_count", 0) or 0) < 5:
            errors.append("v2.10 requires v2.9 five-scoreable baseline")
        if int(v29_campaign.get("positive_memory_episode_count", 0) or 0) < 2:
            errors.append("v2.10 requires v2.9 two-positive-memory baseline")
        if v29_campaign.get("controllergate_full_scoring") != "NOT_RUN":
            errors.append("v2.9 prerequisite must keep full scoring NOT_RUN")

    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.10 output directory: {OUTPUT_DIR}")
    else:
        for name in REQUIRED_TOP_LEVEL:
            path = OUTPUT_DIR / name
            if not path.exists():
                errors.append(f"missing v2.10 artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.10 artifact: {path}")
        errors.extend(verify_manifest(OUTPUT_DIR))
        tar_files = [
            path
            for path in OUTPUT_DIR.rglob("*")
            if path.is_file() and (path.suffix in {".tar", ".tgz"} or path.name.endswith(".tar.gz") or path.name.endswith(".tar.zst"))
        ]
        if tar_files:
            errors.append(f"v2.10 output directory must not commit tar snapshots: {tar_files[:3]}")

    campaign, e = load_json(OUTPUT_DIR / "campaign_results.json")
    errors.extend(e)
    pending = campaign.get("workflow_executed") is False or str(campaign.get("aggregate_result", "")).startswith("blocked_pending_")
    if pending:
        if campaign.get("controllergate_full_scoring") != "NOT_RUN":
            errors.append("pending v2.10 checkpoint must keep full scoring NOT_RUN")
        if campaign.get("full_scoring_allowed") is not False:
            errors.append("pending v2.10 checkpoint must disallow full scoring")
        if campaign.get("self_maintaining_software_demonstrated") is not False:
            errors.append("pending v2.10 checkpoint must not claim self-maintaining software")
        if errors:
            print("v2.10 materialization recovery topological repair audit FAIL")
            for error in errors:
                print(f"- {error}")
            return 1
        print("v2.10 materialization recovery topological repair audit PASS")
        return 0

    baseline, e = load_json(OUTPUT_DIR / "preserved_v2_9_baseline_gate_result.json")
    errors.extend(e)
    recovery, e = load_json(OUTPUT_DIR / "bounded_dependency_materialization_recovery_v2_10.json")
    errors.extend(e)
    cofactor, e = load_json(OUTPUT_DIR / "dependency_cofactor_map_v2_10.json")
    errors.extend(e)
    fixture, e = load_json(OUTPUT_DIR / "fixture_materialization_map_v2_10.json")
    errors.extend(e)
    recovery_log, e = load_json(OUTPUT_DIR / "materialization_recovery_decision_log_v2_10.json")
    errors.extend(e)
    context_reuse, e = load_json(OUTPUT_DIR / "v2_9_context_reuse_manifest_v2_10.json")
    errors.extend(e)
    context_plan, e = load_json(OUTPUT_DIR / "context_bundle_to_repair_plan_v2_10.json")
    errors.extend(e)
    post_discovery, e = load_json(OUTPUT_DIR / "post_materialization_topological_source_discovery_v2_10.json")
    errors.extend(e)
    pool, e = load_json(OUTPUT_DIR / "materialization_recovery_candidate_pool_v2_10.json")
    errors.extend(e)
    taxonomy, e = load_json(OUTPUT_DIR / "repair_path_taxonomy_v2_10.json")
    errors.extend(e)
    duplicate, e = load_json(OUTPUT_DIR / "duplicate_clean_replay_verification_v2_10.json")
    errors.extend(e)
    phase, e = load_json(OUTPUT_DIR / "phase_inversion_seed_constraint_check_v2_10.json")
    errors.extend(e)
    hetero, e = load_json(OUTPUT_DIR / "heterochromatin_monitor_v2_10.json")
    errors.extend(e)
    separation, e = load_json(OUTPUT_DIR / "memory_arm_separation_check_v2_10.json")
    errors.extend(e)
    eligibility, e = load_json(OUTPUT_DIR / "memory_evidence_eligibility_check_v2_10.json")
    errors.extend(e)
    observer, e = load_json(OUTPUT_DIR / "observer_state_separation_check_v2_10.json")
    errors.extend(e)
    materialization_integrity, e = load_json(OUTPUT_DIR / "materialization_recovery_integrity_check_v2_10.json")
    errors.extend(e)
    dependency_anti_leakage, e = load_json(OUTPUT_DIR / "dependency_recovery_anti_leakage_check_v2_10.json")
    errors.extend(e)
    isomorphism, e = load_json(OUTPUT_DIR / "isomorphism_requirements_matrix_v2_10.json")
    errors.extend(e)
    family, e = load_json(OUTPUT_DIR / "positive_memory_family_generalization_v2_10.json")
    errors.extend(e)
    vocab, e = load_json(OUTPUT_DIR / "classification_vocabulary_check.json")
    errors.extend(e)
    audit, e = load_json(OUTPUT_DIR / "audit.json")
    errors.extend(e)

    if baseline.get("status") != "PASS":
        errors.append("preserved_v2_9_baseline_gate_result.status must be PASS")
    scoreables = baseline.get("scoreable_status_by_episode") or {}
    if len([value for value in scoreables.values() if value is True]) < 5:
        errors.append("v2.10 baseline gate must preserve at least five scoreable baseline episodes")
    positives = baseline.get("positive_memory_only_preservation_status") or {}
    for candidate in POSITIVE_BASELINE:
        if positives.get(candidate) is not True:
            errors.append(f"{candidate} positive_memory_only preservation must be true")

    if int(campaign.get("scoreable_episode_count", 0) or 0) < 5:
        errors.append("scoreable_episode_count must be >= 5")
    if int(campaign.get("positive_memory_episode_count", 0) or 0) < 2:
        errors.append("positive_memory_episode_count must be >= 2")
    if campaign.get("controllergate_full_scoring") != "NOT_RUN" or campaign.get("full_scoring_allowed") is not False:
        errors.append("full scoring must remain NOT_RUN/disallowed")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain false")
    for field in ["label_leakage_count", "decision_time_outcome_overlap_count", "corruption_count"]:
        if int(campaign.get(field, 0) or 0) != 0:
            errors.append(f"{field} must be 0")

    for label, data in [
        ("recovery", recovery),
        ("cofactor", cofactor),
        ("fixture", fixture),
        ("recovery_log", recovery_log),
        ("context_reuse", context_reuse),
        ("context_plan", context_plan),
        ("post_discovery", post_discovery),
        ("pool", pool),
        ("taxonomy", taxonomy),
        ("duplicate", duplicate),
        ("phase", phase),
        ("heterochromatin", hetero),
        ("separation", separation),
        ("eligibility", eligibility),
        ("observer", observer),
        ("materialization_integrity", materialization_integrity),
        ("dependency_anti_leakage", dependency_anti_leakage),
        ("isomorphism", isomorphism),
        ("family", family),
        ("vocab", vocab),
        ("audit", audit),
    ]:
        if not status_is_pass(data):
            errors.append(f"{label} status must be PASS")
        errors.extend(bad_candidate_strings(data, label))

    recovery_records = recovery.get("records") or []
    if len(recovery_records) < 2:
        errors.append("bounded dependency/materialization recovery must diagnose at least two non-Ansible candidates")
    if not any(record.get("materialization_recovered") is True for record in recovery_records):
        errors.append("v2.10 must either recover at least one materialization blocker or the runner should classify a blocker instead of PASS")
    if materialization_integrity.get("source_files_modified_during_materialization") not in ([], None):
        errors.append("materialization recovery must not modify project source")
    if dependency_anti_leakage.get("arbitrary_undeclared_dependency_install_count", 0) not in {0, "0"}:
        errors.append("arbitrary undeclared dependency installs must be zero")
    if context_reuse.get("fixed_gold_future_context_used") is not False:
        errors.append("v2.9 context reuse must not include fixed/gold/future context")
    if not any(record.get("whether_materialization_recovery_changed_repair_path_selection") for record in taxonomy.get("records", [])):
        errors.append("repair taxonomy must record at least one materialization-aware repair-path change")
    if family.get("cross_family_positive_memory_signal_suggestive") is True and int(family.get("non_ansible_positive_memory_count", 0) or 0) == 0:
        errors.append("cannot claim cross-family positive memory without a non-Ansible positive")
    if family.get("non_ansible_positive_memory_count", 0) in {0, "0"} and family.get("family_generalization") != "not_expanded":
        errors.append("family generalization must remain not_expanded when non-Ansible positive count is zero")

    layers = isomorphism.get("layers") or []
    expected_layers = {"chromosome_chromatin_isomorphism", "tld_isomorphism", "tot_brot_isomorphism", "torus_brot_isomorphism"}
    if {item.get("layer") for item in layers if isinstance(item, dict)} != expected_layers:
        errors.append("isomorphism matrix must include all four required layers")

    episode_dirs = sorted(path for path in OUTPUT_DIR.glob("episode_*") if path.is_dir())
    if len(episode_dirs) < int(campaign.get("executed_episode_count", 0) or 0):
        errors.append("episode artifact directories must cover executed episodes")
    for episode_dir in episode_dirs:
        for name in REQUIRED_EPISODE:
            path = episode_dir / name
            if not path.exists():
                errors.append(f"missing v2.10 episode artifact: {path}")
            elif path.stat().st_size == 0 and name not in {"failing_test_method_extract.txt", "no_memory_source_only_repair_patch.diff", "memory_enabled_source_only_repair_patch.diff"}:
                errors.append(f"empty v2.10 episode artifact: {path}")
        errors.extend(verify_manifest(episode_dir))

    classifications = {record.get("classification") for record in (load_json(OUTPUT_DIR / "decision_report.json")[0].get("records") or [])}
    allowed = set(vocab.get("allowed_vocabulary") or [])
    if classifications and allowed and not classifications <= allowed:
        errors.append(f"decision classifications outside vocabulary: {sorted(classifications - allowed)}")

    summary_text = SUMMARY.read_text(encoding="utf-8", errors="replace") if SUMMARY.exists() else ""
    if "## v2.10 Materialization Recovery and Topological Repair" not in summary_text:
        errors.append("shareable summary missing v2.10 block")

    if errors:
        print("v2.10 materialization recovery topological repair audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.10 materialization recovery topological repair audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

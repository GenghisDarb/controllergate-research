#!/usr/bin/env python3
"""Audit v2.11 topology-aware source repair artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_11_topology_aware_source_repair"
V210_OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_10_materialization_recovery_topological_repair"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_11_topology_aware_source_repair.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_11_topology_aware_source_repair_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_11_prepare_topology_aware_source_repair.py"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

BASELINE = {"youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"}
POSITIVE_BASELINE = {"ansible:2", "ansible:5"}
RECOVERED = {"fastapi:2", "fastapi:3", "fastapi:4", "PySnooper:1"}

REQUIRED_TOP_LEVEL = [
    "campaign_summary.md",
    "campaign_results.json",
    "decision_report.json",
    "aggregate_report.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "preserved_v2_10_baseline_gate_result.json",
    "recovered_surface_repair_plan_v2_11.json",
    "bounded_topology_aware_repair_proposer_v2_11.json",
    "topology_to_patch_proof_ledger_v2_11.json",
    "topology_aware_repair_candidate_pool_v2_11.json",
    "duplicate_clean_replay_verification_v2_11.json",
    "phase_inversion_seed_constraint_check_v2_11.json",
    "heterochromatin_monitor_v2_11.json",
    "silent_scaffolding_risk_audit_v2_11.json",
    "memory_arm_separation_check_v2_11.json",
    "memory_evidence_eligibility_check_v2_11.json",
    "observer_state_separation_check_v2_11.json",
    "topology_aware_repair_integrity_check_v2_11.json",
    "source_patch_anti_leakage_check_v2_11.json",
    "isomorphism_requirements_matrix_v2_11.json",
    "positive_memory_family_generalization_v2_11.json",
    "harness_sanity_check.json",
    "command_normalization_policy.json",
    "candidate_chromatin_state_v2_11.json",
    "local_tension_relief_v2_11.json",
    "minimal_probe_selection_v2_11.json",
    "candidate_triage_stability_audit_v2_11.json",
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
    "context_bundle_reuse_result.json",
    "recovered_surface_repair_plan_result.json",
    "environmental_stress_state_result.json",
    "chromatin_state_result.json",
    "heterochromatin_monitor_result.json",
    "silent_scaffolding_risk_result.json",
    "repair_path_taxonomy_result.json",
    "topology_aware_repair_proposer_result.json",
    "topology_to_patch_proof_ledger_result.json",
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


def main() -> int:
    errors: list[str] = []
    for path in [WORKFLOW, RUNNER, PREP]:
        if not path.exists():
            errors.append(f"missing v2.11 implementation file: {path}")

    v210_campaign, e = load_json(V210_OUTPUT_DIR / "campaign_results.json")
    errors.extend(e)
    if v210_campaign:
        if v210_campaign.get("preserved_v2_9_baseline_gate_status") != "PASS":
            errors.append("v2.11 requires verified v2.10/v2.9 preserved baseline")
        if int(v210_campaign.get("scoreable_episode_count", 0) or 0) < 5:
            errors.append("v2.11 requires v2.10 five-scoreable baseline")
        if int(v210_campaign.get("positive_memory_episode_count", 0) or 0) < 2:
            errors.append("v2.11 requires v2.10 two-positive-memory baseline")
        if v210_campaign.get("controllergate_full_scoring") != "NOT_RUN":
            errors.append("v2.10 prerequisite must keep full scoring NOT_RUN")

    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.11 output directory: {OUTPUT_DIR}")
    else:
        for name in REQUIRED_TOP_LEVEL:
            path = OUTPUT_DIR / name
            if not path.exists():
                errors.append(f"missing v2.11 artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.11 artifact: {path}")
        errors.extend(verify_manifest(OUTPUT_DIR))
        tar_files = [
            path
            for path in OUTPUT_DIR.rglob("*")
            if path.is_file() and (path.suffix in {".tar", ".tgz"} or path.name.endswith(".tar.gz") or path.name.endswith(".tar.zst"))
        ]
        if tar_files:
            errors.append(f"v2.11 output directory must not commit tar snapshots: {tar_files[:3]}")

    campaign, e = load_json(OUTPUT_DIR / "campaign_results.json")
    errors.extend(e)
    pending = campaign.get("workflow_executed") is False or str(campaign.get("aggregate_result", "")).startswith("blocked_pending_")
    if pending:
        if campaign.get("controllergate_full_scoring") != "NOT_RUN":
            errors.append("pending v2.11 checkpoint must keep full scoring NOT_RUN")
        if campaign.get("full_scoring_allowed") is not False:
            errors.append("pending v2.11 checkpoint must disallow full scoring")
        if campaign.get("self_maintaining_software_demonstrated") is not False:
            errors.append("pending v2.11 checkpoint must not claim self-maintaining software")
        if errors:
            print("v2.11 topology-aware source repair audit FAIL")
            for error in errors:
                print(f"- {error}")
            return 1
        print("v2.11 topology-aware source repair audit PASS")
        return 0

    baseline, e = load_json(OUTPUT_DIR / "preserved_v2_10_baseline_gate_result.json")
    errors.extend(e)
    plan, e = load_json(OUTPUT_DIR / "recovered_surface_repair_plan_v2_11.json")
    errors.extend(e)
    proposer, e = load_json(OUTPUT_DIR / "bounded_topology_aware_repair_proposer_v2_11.json")
    errors.extend(e)
    proof, e = load_json(OUTPUT_DIR / "topology_to_patch_proof_ledger_v2_11.json")
    errors.extend(e)
    pool, e = load_json(OUTPUT_DIR / "topology_aware_repair_candidate_pool_v2_11.json")
    errors.extend(e)
    duplicate, e = load_json(OUTPUT_DIR / "duplicate_clean_replay_verification_v2_11.json")
    errors.extend(e)
    phase, e = load_json(OUTPUT_DIR / "phase_inversion_seed_constraint_check_v2_11.json")
    errors.extend(e)
    hetero, e = load_json(OUTPUT_DIR / "heterochromatin_monitor_v2_11.json")
    errors.extend(e)
    separation, e = load_json(OUTPUT_DIR / "memory_arm_separation_check_v2_11.json")
    errors.extend(e)
    eligibility, e = load_json(OUTPUT_DIR / "memory_evidence_eligibility_check_v2_11.json")
    errors.extend(e)
    observer, e = load_json(OUTPUT_DIR / "observer_state_separation_check_v2_11.json")
    errors.extend(e)
    repair_integrity, e = load_json(OUTPUT_DIR / "topology_aware_repair_integrity_check_v2_11.json")
    errors.extend(e)
    source_anti_leakage, e = load_json(OUTPUT_DIR / "source_patch_anti_leakage_check_v2_11.json")
    errors.extend(e)
    isomorphism, e = load_json(OUTPUT_DIR / "isomorphism_requirements_matrix_v2_11.json")
    errors.extend(e)
    family, e = load_json(OUTPUT_DIR / "positive_memory_family_generalization_v2_11.json")
    errors.extend(e)
    vocab, e = load_json(OUTPUT_DIR / "classification_vocabulary_check.json")
    errors.extend(e)
    audit, e = load_json(OUTPUT_DIR / "audit.json")
    errors.extend(e)
    decision, e = load_json(OUTPUT_DIR / "decision_report.json")
    errors.extend(e)

    if baseline.get("status") != "PASS":
        errors.append("preserved_v2_10_baseline_gate_result.status must be PASS")
    scoreables = baseline.get("scoreable_status_by_episode") or {}
    if len([value for value in scoreables.values() if value is True]) < 5:
        errors.append("v2.11 baseline gate must preserve at least five scoreable baseline episodes")
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
        ("plan", plan),
        ("proposer", proposer),
        ("proof", proof),
        ("pool", pool),
        ("duplicate", duplicate),
        ("phase", phase),
        ("heterochromatin", hetero),
        ("separation", separation),
        ("eligibility", eligibility),
        ("observer", observer),
        ("repair_integrity", repair_integrity),
        ("source_anti_leakage", source_anti_leakage),
        ("isomorphism", isomorphism),
        ("family", family),
        ("vocab", vocab),
        ("audit", audit),
    ]:
        if not status_is_pass(data):
            errors.append(f"{label} status must be PASS")

    plan_records = plan.get("records") or []
    allowed = {record.get("candidate") for record in plan_records if record.get("repair_attempt_allowed") is True}
    if not RECOVERED <= allowed:
        errors.append("all v2.10 recovered surfaces must be repair-attempt allowed in v2.11")
    proposer_records = proposer.get("records") or []
    if len(proposer_records) < 8:
        errors.append("v2.11 must record no-memory and memory-enabled proposals for recovered candidates")
    fastapi_records = [record for record in proposer_records if str(record.get("candidate", "")).startswith("fastapi:")]
    pysnooper_records = [record for record in proposer_records if record.get("candidate") == "PySnooper:1"]
    if not fastapi_records:
        errors.append("at least one FastAPI validation_guard path must receive a proposal or no-safe-patch proof")
    if not pysnooper_records:
        errors.append("PySnooper:1 import compatibility path must receive a proposal or no-safe-patch proof")
    if int(proposer.get("generated_patch_count", 0) or 0) > 0 and not proof.get("records"):
        errors.append("generated patches require topology-to-patch proof records")
    if repair_integrity.get("tests_modified") is not False:
        errors.append("v2.11 source repair must not modify tests")
    if source_anti_leakage.get("fixed_gold_future_patch_source_used") is not False:
        errors.append("v2.11 source patches must not use fixed/gold/future patch source")
    if source_anti_leakage.get("test_files_modified_count", 0) not in {0, "0"}:
        errors.append("test file modification count must be zero")
    if family.get("cross_family_positive_memory_signal_suggestive") is True and int(family.get("non_ansible_positive_memory_count", 0) or 0) == 0:
        errors.append("cannot claim cross-family positive memory without a non-Ansible positive")
    if int(family.get("non_ansible_positive_memory_count", 0) or 0) == 0 and family.get("family_generalization") != "not_expanded":
        errors.append("family generalization must remain not_expanded without non-Ansible positive memory")

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
                errors.append(f"missing v2.11 episode artifact: {path}")
            elif path.stat().st_size == 0 and name in {"failing_command.txt", "normalized_failing_command.txt", "failing_log_raw.txt", "failure_signature.txt"}:
                errors.append(f"empty v2.11 episode artifact: {path}")
        errors.extend(verify_manifest(episode_dir))

    classifications = {record.get("classification") for record in (decision.get("records") or [])}
    allowed_vocab = set(vocab.get("allowed_vocabulary") or [])
    if classifications and allowed_vocab and not classifications <= allowed_vocab:
        errors.append(f"decision classifications outside vocabulary: {sorted(classifications - allowed_vocab)}")

    summary_text = SUMMARY.read_text(encoding="utf-8", errors="replace") if SUMMARY.exists() else ""
    if "## v2.11 Topology-Aware Source Repair" not in summary_text:
        errors.append("shareable summary missing v2.11 block")

    if errors:
        print("v2.11 topology-aware source repair audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.11 topology-aware source repair audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

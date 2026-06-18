#!/usr/bin/env python3
"""Audit v2.8r closure-guided third-scoreable checkpoint/artifact."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_8r_closure_guided_third_scoreable"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "v2_8r_closure_guided_third_scoreable.yml"
RUNNER = REPO_ROOT / "scripts" / "v2_8r_closure_guided_third_scoreable_runner.py"
BASE_RUNNER = REPO_ROOT / "scripts" / "v2_8q_bugsinpy_preflight_guided_third_scoreable_runner.py"
PREP = REPO_ROOT / "scripts" / "v2_8r_prepare_closure_guided_third_scoreable.py"
PATCH = REPO_ROOT / "v2_8q_runner_repair_uncommitted.patch"
SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

CLASSIFICATION_VOCABULARY = {
    "blocked_no_safe_patch_candidate_generated",
    "blocked_patch_did_not_apply",
    "blocked_replay_or_materialization_failure",
    "blocked_target_test_failed",
    "failed_both",
    "inconclusive_equal_performance",
    "no_memory_only",
    "positive_memory_only",
    "runner_regression_preserved_reference_failure",
}

REQUIRED_TOP_LEVEL = [
    "campaign_summary.md",
    "campaign_results.json",
    "decision_report.json",
    "aggregate_report.json",
    "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
    "preserved_reference_gate_result.json",
    "harness_sanity_check.json",
    "command_normalization_policy.json",
    "candidate_triage_report.json",
    "candidate_chromatin_state_v2_8r.json",
    "local_tension_relief_v2_8r.json",
    "minimal_probe_selection_v2_8r.json",
    "candidate_triage_stability_audit_v2_8r.json",
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

REPAIR_ATTEMPT_ARTIFACTS = [
    "episode_metadata.json",
    "candidate_preflight_result.json",
    "fixture_dependency_preflight_result.json",
    "command_normalization_result.json",
    "chromatin_state_result.json",
    "local_tension_relief_result.json",
    "minimal_probe_selection_result.json",
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

ALLOWED_CHROMATIN_STATES = {"open", "strained", "blocked", "inaccessible"}
ALLOWED_MEMORY_LABELS = {"demonstrated", "suggestive", "not_demonstrated", "insufficient_evidence"}


def load_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists():
        return {}, [f"missing JSON file: {path}"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, [f"{path}: invalid JSON: {exc.msg}"]
    if not isinstance(data, dict):
        return {}, [f"{path}: expected JSON object"]
    return data, []


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


def text_contains(path: Path, snippets: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    return [f"{path}: missing {snippet!r}" for snippet in snippets if snippet not in text]


def check_memory_lift_decomposition(data: dict[str, Any], positives: int, errors: list[str]) -> None:
    for section in [
        "repair_outcome_memory_lift",
        "selection_memory_lift",
        "stability_memory_lift",
        "global_closure_memory_lift",
    ]:
        label = data.get(section, {}).get("label")
        if label not in ALLOWED_MEMORY_LABELS:
            errors.append(f"memory_lift_decomposition has invalid {section} label: {label}")
    if positives < 2:
        if data.get("repair_outcome_memory_lift", {}).get("label") == "demonstrated":
            errors.append("repair outcome memory lift cannot be demonstrated with fewer than two positive memory episodes")
        if data.get("main_benchmark_memory_lift_status") != "not_demonstrated":
            errors.append("main benchmark memory lift must remain not_demonstrated when positive memory evidence is insufficient")
    if data.get("main_aggregate_must_not_be_inflated_by_auxiliary_closure_metrics") is False:
        errors.append("auxiliary closure metrics must not inflate the main benchmark aggregate")


def main() -> int:
    errors: list[str] = []
    for path in [WORKFLOW, RUNNER, BASE_RUNNER, PREP, PATCH]:
        if not path.exists():
            errors.append(f"missing v2.8r implementation/support file: {path}")
        elif path.is_file() and path.stat().st_size == 0:
            errors.append(f"empty v2.8r implementation/support file: {path}")

    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.8r output directory: {OUTPUT_DIR}")
    else:
        for name in REQUIRED_TOP_LEVEL:
            path = OUTPUT_DIR / name
            if not path.exists():
                errors.append(f"missing v2.8r artifact: {path}")
            elif path.stat().st_size == 0:
                errors.append(f"empty v2.8r artifact: {path}")
        errors.extend(verify_manifest(OUTPUT_DIR))
        tar_files = [path for path in OUTPUT_DIR.rglob("*") if path.is_file() and path.suffix in {".tar", ".tgz"}]
        if tar_files:
            errors.append(f"v2.8r output directory must not commit large tar snapshots: {tar_files[:3]}")

    campaign, e = load_json(OUTPUT_DIR / "campaign_results.json")
    errors.extend(e)
    aggregate, e = load_json(OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json")
    errors.extend(e)
    decision, e = load_json(OUTPUT_DIR / "decision_report.json")
    errors.extend(e)
    gate, e = load_json(OUTPUT_DIR / "preserved_reference_gate_result.json")
    errors.extend(e)
    harness, e = load_json(OUTPUT_DIR / "harness_sanity_check.json")
    errors.extend(e)
    normalization, e = load_json(OUTPUT_DIR / "command_normalization_policy.json")
    errors.extend(e)
    triage, e = load_json(OUTPUT_DIR / "candidate_triage_report.json")
    errors.extend(e)
    chromatin, e = load_json(OUTPUT_DIR / "candidate_chromatin_state_v2_8r.json")
    errors.extend(e)
    tension, e = load_json(OUTPUT_DIR / "local_tension_relief_v2_8r.json")
    errors.extend(e)
    selection, e = load_json(OUTPUT_DIR / "minimal_probe_selection_v2_8r.json")
    errors.extend(e)
    stability, e = load_json(OUTPUT_DIR / "candidate_triage_stability_audit_v2_8r.json")
    errors.extend(e)
    closure, e = load_json(OUTPUT_DIR / "closure_scaling_audit.json")
    errors.extend(e)
    memory, e = load_json(OUTPUT_DIR / "memory_lift_decomposition.json")
    errors.extend(e)
    vocab, e = load_json(OUTPUT_DIR / "classification_vocabulary_check.json")
    errors.extend(e)
    source_separation, e = load_json(OUTPUT_DIR / "source_repair_vs_harness_separation.json")
    errors.extend(e)

    if campaign.get("full_scoring_allowed") is not False or campaign.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.8r must keep full scoring NOT_RUN / disallowed")
    if campaign.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.8r must not claim self-maintaining software")
    if aggregate.get("limited_bugsinpy_real_bug_memory_lift_criteria_met") is True and int(aggregate.get("positive_memory_episode_count", 0) or 0) < 2:
        errors.append("v2.8r cannot claim memory lift without at least two positive memory episodes")
    if source_separation.get("tests_may_be_modified_as_repair") is not False:
        errors.append("v2.8r must forbid test edits as repair candidates")
    if "python -m pytest" not in json.dumps(normalization):
        errors.append("v2.8r must document pytest command normalization to python -m pytest")
    if "returncode 127" not in json.dumps(normalization):
        errors.append("v2.8r must document returncode 127 as harness/normalization failure")

    triage_records = triage.get("records", [])
    chromatin_records = chromatin.get("records", [])
    if not isinstance(triage_records, list) or not triage_records:
        errors.append("v2.8r candidate triage report must contain records")
    if not isinstance(chromatin_records, list):
        errors.append("v2.8r chromatin state must contain a records list")
    elif len(chromatin_records) != len(triage_records):
        errors.append("v2.8r chromatin state must cover every triaged candidate")
    for record in chromatin_records:
        if record.get("state") not in ALLOWED_CHROMATIN_STATES:
            errors.append(f"invalid chromatin state for {record.get('candidate')}: {record.get('state')}")
        if record.get("decision_time_safe") is not True:
            errors.append(f"chromatin state for {record.get('candidate')} must be decision-time safe")
    if chromatin.get("decision_time_safe_fields_only") is not True:
        errors.append("chromatin state must use only decision-time-safe fields")

    selected = selection.get("selected_repair_candidates", [])
    if not isinstance(selected, list):
        errors.append("minimal probe selection must record selected_repair_candidates")
    elif len(selected) > 5:
        errors.append("minimal probe selection must attempt at most five replacement candidates")
    if selection.get("selection_used_only_decision_time_safe_evidence") is not True:
        errors.append("minimal probe selection must use only decision-time-safe evidence")

    if tension.get("scoreable_rules_changed") is True:
        errors.append("local tension relief must not change scoreable rules")
    forbidden = tension.get("forbidden_relief_obeyed", {})
    if forbidden:
        for key in ["fixed_revision_used", "gold_patch_used", "future_outcome_evidence_used_at_decision_time", "tests_modified_as_repair", "scoreable_rules_changed"]:
            if forbidden.get(key) is not False:
                errors.append(f"forbidden tension relief was not ruled out: {key}")

    if stability.get("queue_bias_detected") is not False:
        errors.append("candidate stability audit must not detect queue bias")
    if stability.get("gate_topology_dependence_confirmed") is not True:
        errors.append("candidate stability audit must confirm gate topology dependence")
    if not isinstance(stability.get("phase_null_results"), list) or not stability.get("phase_null_results"):
        errors.append("candidate stability audit must include phase null results")
    else:
        for item in stability["phase_null_results"]:
            observed = item.get("observed")
            if campaign.get("workflow_executed") is True and observed != "FAIL":
                errors.append(f"executed phase null must fail: {item}")
    if not (0 <= float(stability.get("ranking_stability_score", 0)) <= 1):
        errors.append("ranking stability score must be within [0, 1]")

    for key in [
        "local_closure_count",
        "preserved_anchor_count",
        "candidate_space_size",
        "preflight_passing_count",
        "repair_attempted_count",
        "repair_attempt_efficiency",
        "cross_project_span",
        "repeated_blocked_lane_count",
        "candidate_triage_stability_score",
        "queue_bias_detected",
        "gate_topology_dependence_confirmed",
        "provenance_closure_status",
    ]:
        if key not in closure:
            errors.append(f"closure scaling audit missing {key}")

    positives = int(campaign.get("positive_memory_episode_count", 0) or 0)
    check_memory_lift_decomposition(memory, positives, errors)

    workflow_executed = campaign.get("workflow_executed") is True
    if not workflow_executed:
        if campaign.get("aggregate_result") != "blocked_pending_v2_8r_closure_guided_third_scoreable_artifact":
            errors.append("local v2.8r checkpoint must remain pending until the Linux artifact is ingested")
        if gate.get("status") != "PENDING_GITHUB_ACTIONS":
            errors.append("local v2.8r preserved-reference gate must be pending")
        if harness.get("status") != "PENDING_GITHUB_ACTIONS":
            errors.append("local v2.8r harness sanity must be pending")
        if len(triage_records) < 19:
            errors.append("local v2.8r triage should inherit at least the 19 v2.8q preflight-passing candidates")
    else:
        records = decision.get("records", [])
        by_candidate = {record.get("candidate"): record for record in records}
        if gate.get("status") != "PASS":
            errors.append("executed v2.8r preserved-reference gate must pass")
        if harness.get("status") != "PASS":
            errors.append("executed v2.8r harness sanity must pass")
        for candidate in ["youtube-dl:1", "black:4"]:
            if by_candidate.get(candidate, {}).get("scoreable") is not True:
                errors.append(f"executed v2.8r must preserve {candidate} as scoreable")
        if int(campaign.get("scoreable_episode_count", 0) or 0) < 3:
            errors.append("executed v2.8r must reach at least three scoreable episodes")
        if int(campaign.get("replacement_scoreable_episode_count", 0) or 0) < 1:
            errors.append("executed v2.8r must make at least one replacement candidate scoreable")
        for key in ["label_leakage_count", "decision_time_outcome_overlap_count", "corruption_count"]:
            if campaign.get(key) != 0:
                errors.append(f"executed v2.8r must have zero {key}")
        if len(triage_records) != int(campaign.get("preflight_passing_candidate_count", len(triage_records)) or 0):
            errors.append("executed v2.8r triage report must cover all preflight-passing candidates")
        if vocab.get("status") != "PASS":
            errors.append("executed v2.8r classification vocabulary check must pass")
        for record in records:
            classification = record.get("classification")
            if classification not in CLASSIFICATION_VOCABULARY:
                errors.append(f"unexpected v2.8r classification: {classification}")
            directory = OUTPUT_DIR / str(record.get("episode_id"))
            if not directory.exists():
                errors.append(f"executed v2.8r missing episode directory: {directory}")
                continue
            for name in REPAIR_ATTEMPT_ARTIFACTS:
                if not (directory / name).exists():
                    errors.append(f"executed v2.8r {record.get('episode_id')} missing {name}")
            command_norm, ep_errors = load_json(directory / "command_normalization_result.json")
            errors.extend(ep_errors)
            if command_norm.get("pythonpath_includes_project_root") is not True:
                errors.append(f"executed v2.8r {record.get('episode_id')} missing project root PYTHONPATH")
            errors.extend(verify_manifest(directory))

    errors.extend(
        text_contains(
            RUNNER,
            [
                "v2_8q_bugsinpy_preflight_guided_third_scoreable_runner",
                "v2_8r_closure_guided_third_scoreable_artifacts",
                "candidate_chromatin_state_v2_8r",
                "local_tension_relief_v2_8r",
                "minimal_probe_selection_v2_8r",
                "candidate_triage_stability_audit_v2_8r",
                "closure_scaling_audit",
                "memory_lift_decomposition",
                "main_aggregate_must_not_be_inflated_by_auxiliary_closure_metrics",
            ],
        )
    )
    errors.extend(
        text_contains(
            BASE_RUNNER,
            [
                "project_root / \"lib\"",
                "v28j.source_diff",
                "localized_deterministic_missing_argument_order",
                "runner_regression_preserved_reference_failure",
                "returncode_127_treated_as_harness_failure",
            ],
        )
    )
    errors.extend(
        text_contains(
            WORKFLOW,
            [
                "workflow_dispatch",
                "v2_8r_closure_guided_third_scoreable_artifacts",
                "candidate_chromatin_state_v2_8r",
                "local_tension_relief_v2_8r",
                "minimal_probe_selection_v2_8r",
                "actions/upload-artifact@v4",
            ],
        )
    )
    errors.extend(
        text_contains(
            PATCH,
            [
                "v28j.source_diff",
                "project_root / \"lib\"",
                "localized_deterministic_missing_argument_order",
            ],
        )
    )
    errors.extend(
        text_contains(
            SUMMARY,
            [
                "v2.8r Closure-Guided Third Scoreable Recovery",
                "Full scoring remains `NOT_RUN`",
                "Self-maintaining software is not demonstrated",
            ],
        )
    )

    if errors:
        print("v2.8r closure-guided third scoreable audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("v2.8r closure-guided third scoreable audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

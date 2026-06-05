#!/usr/bin/env python3
"""Audit v2.4 SWE-bench/BugsInPy real external bug replay campaign outputs."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = REPO_ROOT / "inputs" / "v2_4_real_external_bug_sources.json"
CAMPAIGN_DIR = REPO_ROOT / "outputs" / "v2_4_real_external_bug_replay_campaign"
V23_AGG = (
    REPO_ROOT
    / "outputs"
    / "v2_3_known_external_bug_replay_campaign"
    / "aggregate_known_external_bug_memory_lift_assessment.json"
)
V22_AGG = (
    REPO_ROOT
    / "outputs"
    / "v2_2_external_fork_controlled_fixture_replay_pilot"
    / "aggregate_external_fork_controlled_fixture_memory_lift_assessment.json"
)
V19_AGG = (
    REPO_ROOT
    / "outputs"
    / "v1_9_organic_style_replay_pilot_completion_pass"
    / "aggregate_v1_9_updated_memory_lift_assessment.json"
)
V18_AGG = REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign" / "aggregate_memory_lift_assessment.json"
E003_RESULT = REPO_ROOT / "outputs" / "v1_8_episode_003_torus_limited_replay_scoring" / "limited_scoring_result.json"
BETA_REPLAY = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
BETA_SCORING = REPO_ROOT / "controllergate_v1_7_beta" / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
ALPHA_CLASSIFICATION = REPO_ROOT / "controllergate_v1_7_alpha" / "traces" / "audits" / "episode_review_classification.json"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

REQUIRED_ACQUISITION_FILES = [
    "source_acquisition_log.json",
    "candidate_preflight_results.json",
    "candidate_promotion_table.json",
    "v2_4_ready_swe_bench_candidate_pool.json",
    "v2_4_ready_bugsinpy_candidate_pool.json",
    "v2_4_candidate_gap_report.md",
    "v2_4_handoff_recommendations.json",
    "campaign_results.json",
    "aggregate_real_external_bug_memory_lift_assessment.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

REQUIRED_EPISODE_FILES = [
    "episode_metadata.json",
    "source_repo_metadata.json",
    "license_summary.txt",
    "candidate_selection_record.json",
    "known_issue_or_bug_reference.json",
    "target_repo_snapshot.json",
    "environment_snapshot.txt",
    "decision_time_input_manifest.json",
    "gold_patch_exclusion_check.json",
    "failing_command.txt",
    "failing_log_raw.txt",
    "failure_signature.txt",
    "pre_repair_replay_transcript.txt",
    "no_memory_decision_time_inputs.json",
    "no_memory_action_trace.json",
    "no_memory_repair_patch.diff",
    "no_memory_post_repair_log_raw.txt",
    "no_memory_outcome.json",
    "memory_enabled_decision_time_inputs.json",
    "memory_enabled_action_trace.json",
    "memory_evidence_used.json",
    "memory_enabled_repair_patch.diff",
    "memory_enabled_post_repair_log_raw.txt",
    "memory_enabled_outcome.json",
    "post_repair_comparison.json",
    "corruption_check_result.json",
    "decision_time_outcome_overlap_check.json",
    "limited_scoring_result.json",
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
    if not isinstance(data, dict):
        return {}, [f"{path}: expected object"]
    return data, []


def require_text(path: Path, required: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing text file: {path}"]
    text = path.read_text(encoding="utf-8")
    return [f"{path}: missing required text {item!r}" for item in required if item not in text]


def verify_manifest(directory: Path, recursive: bool = True) -> list[str]:
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
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"{manifest}:{line_no}: hash mismatch for {rel}")
    if recursive:
        for path in directory.rglob("*"):
            if path.is_file() and path.name != "SHA256SUMS.txt":
                rel = str(path.relative_to(directory)).replace("\\", "/")
                if rel not in seen:
                    errors.append(f"SHA256SUMS missing artifact entry {rel}")
    return errors


def audit_episode(directory: Path) -> list[str]:
    errors: list[str] = []
    for name in REQUIRED_EPISODE_FILES:
        path = directory / name
        if not path.exists():
            errors.append(f"{directory.name}: missing required artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"{directory.name}: empty required artifact {name}")
    metadata, metadata_errors = load_json(directory / "episode_metadata.json")
    gold_check, gold_errors = load_json(directory / "gold_patch_exclusion_check.json")
    overlap, overlap_errors = load_json(directory / "decision_time_outcome_overlap_check.json")
    scoring, scoring_errors = load_json(directory / "limited_scoring_result.json")
    errors.extend(metadata_errors + gold_errors + overlap_errors + scoring_errors)
    if metadata.get("full_scoring_allowed") is not False or scoring.get("full_scoring_allowed") is not False:
        errors.append(f"{directory.name}: full scoring must remain false")
    if metadata.get("controllergate_full_scoring") != "NOT_RUN" or scoring.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append(f"{directory.name}: ControllerGate full scoring must remain NOT_RUN")
    if gold_check.get("gold_patch_excluded_from_decision_time_inputs") is not True:
        errors.append(f"{directory.name}: gold/corrected patch exclusion check must pass")
    if overlap.get("overlap_detected") is not False:
        errors.append(f"{directory.name}: decision-time/outcome overlap must be false")
    errors.extend(verify_manifest(directory))
    return errors


def main() -> int:
    errors: list[str] = []
    if not INPUT_PATH.exists():
        errors.append(f"missing v2.4 input descriptor: {INPUT_PATH}")
    if not CAMPAIGN_DIR.exists():
        errors.append(f"missing v2.4 campaign directory: {CAMPAIGN_DIR}")
    for name in REQUIRED_ACQUISITION_FILES:
        path = CAMPAIGN_DIR / name
        if not path.exists():
            errors.append(f"missing v2.4 acquisition/campaign artifact {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.4 artifact {name}")

    inputs, input_errors = load_json(INPUT_PATH)
    acquisition, acquisition_errors = load_json(CAMPAIGN_DIR / "source_acquisition_log.json")
    preflight, preflight_errors = load_json(CAMPAIGN_DIR / "candidate_preflight_results.json")
    table, table_errors = load_json(CAMPAIGN_DIR / "candidate_promotion_table.json")
    swe_pool, swe_errors = load_json(CAMPAIGN_DIR / "v2_4_ready_swe_bench_candidate_pool.json")
    bugs_pool, bugs_errors = load_json(CAMPAIGN_DIR / "v2_4_ready_bugsinpy_candidate_pool.json")
    handoff, handoff_errors = load_json(CAMPAIGN_DIR / "v2_4_handoff_recommendations.json")
    results, results_errors = load_json(CAMPAIGN_DIR / "campaign_results.json")
    aggregate, aggregate_errors = load_json(CAMPAIGN_DIR / "aggregate_real_external_bug_memory_lift_assessment.json")
    v23, v23_errors = load_json(V23_AGG)
    v22, v22_errors = load_json(V22_AGG)
    v19, v19_errors = load_json(V19_AGG)
    v18, v18_errors = load_json(V18_AGG)
    e003, e003_errors = load_json(E003_RESULT)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING)
    alpha_classification, alpha_errors = load_json(ALPHA_CLASSIFICATION)
    errors.extend(
        input_errors
        + acquisition_errors
        + preflight_errors
        + table_errors
        + swe_errors
        + bugs_errors
        + handoff_errors
        + results_errors
        + aggregate_errors
        + v23_errors
        + v22_errors
        + v19_errors
        + v18_errors
        + e003_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_errors
    )

    candidates = inputs.get("candidates") if isinstance(inputs.get("candidates"), list) else []
    if len(candidates) < 5:
        errors.append("v2.4 input must contain SWE-bench, BugsInPy, and QuixBugs-preservation descriptors")
    source_families = {candidate.get("source_family") for candidate in candidates}
    for required in {"swe_bench_verified", "swe_bench_lite", "bugsinpy", "quixbugs_preserved_not_organic"}:
        if required not in source_families:
            errors.append(f"v2.4 input missing source family {required}")

    if acquisition.get("full_scoring_allowed") is not False or acquisition.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.4 source acquisition must keep full scoring NOT_RUN/disallowed")
    if acquisition.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain false")
    if acquisition.get("broad_organic_external_memory_lift_demonstrated") is not False:
        errors.append("broad organic external memory lift must remain false")

    records = preflight.get("records") if isinstance(preflight.get("records"), list) else []
    if len(records) != len(candidates):
        errors.append("v2.4 preflight record count must match source descriptors")
    valid_statuses = {
        "promoted_ready_for_v2_4_swe_bench_issue",
        "promoted_ready_for_v2_4_bugsinpy_real_bug",
        "blocked_source_unavailable",
        "blocked_metadata_required",
        "blocked_environment_too_heavy",
        "blocked_no_deterministic_replay",
        "blocked_gold_patch_leakage_risk",
        "still_needs_manual_review",
        "rejected_after_triage",
    }
    for record in records:
        status = record.get("promotion_status")
        if status not in valid_statuses:
            errors.append(f"{record.get('candidate_id')}: invalid promotion status {status!r}")
        readiness = record.get("readiness_score")
        if not isinstance(readiness, int | float) or readiness < 0 or readiness > 100:
            errors.append(f"{record.get('candidate_id')}: readiness_score must be numeric 0-100")
        if status in {"promoted_ready_for_v2_4_swe_bench_issue", "promoted_ready_for_v2_4_bugsinpy_real_bug"}:
            if readiness < 75:
                errors.append(f"{record.get('candidate_id')}: promoted candidate readiness_score must be >= 75")
            if not record.get("issue_or_bug_reference"):
                errors.append(f"{record.get('candidate_id')}: promoted candidate lacks real issue/bug reference")
            if record.get("gold_patch_exclusion_plan") in {None, ""}:
                errors.append(f"{record.get('candidate_id')}: promoted candidate lacks gold patch exclusion plan")
        policy = json.dumps(record.get("decision_time_input_policy", ""))
        if "outcome-only" not in policy and record.get("candidate_class") != "algorithmic_benchmark_only":
            errors.append(f"{record.get('candidate_id')}: decision-time policy must mark fixed/gold patches outcome-only")
        if record.get("source_family") == "quixbugs_preserved_not_organic" and record.get("candidate_class") != "algorithmic_benchmark_only":
            errors.append("QuixBugs must remain algorithmic_benchmark_only in v2.4")

    if swe_pool.get("count") != 0 or bugs_pool.get("count") != 0:
        errors.append("this v2.4 run should have zero promoted SWE-bench/BugsInPy candidates")
    if table.get("promoted_known_or_real_bug_count") != 0:
        errors.append("v2.4 promotion table must show zero promoted real bug candidates")
    if table.get("execution_gate") != "do_not_execute_v2_4_no_promoted_candidates":
        errors.append("v2.4 execution gate must block execution when no candidates promote")
    if handoff.get("execute_v2_4_limited_replay") is not False:
        errors.append("v2.4 handoff must not execute when zero candidates promote")
    if handoff.get("blocker") != "blocked_real_external_bug_candidate_acquisition_failure":
        errors.append("v2.4 handoff blocker mismatch")

    expected = "blocked_real_external_bug_candidate_acquisition_failure"
    if results.get("aggregate_result") != expected or aggregate.get("aggregate_result") != expected:
        errors.append("v2.4 aggregate result mismatch")
    if results.get("executed_episode_count") != 0:
        errors.append("v2.4 must not execute episodes without promoted candidates")
    if results.get("scoreable_episode_count") != 0 or aggregate.get("scoreable_episode_count") != 0:
        errors.append("v2.4 scoreable episode count must be 0")
    if results.get("positive_memory_episode_count") != 0 or aggregate.get("positive_memory_episode_count") != 0:
        errors.append("v2.4 positive memory episode count must be 0")
    if aggregate.get("gold_corrected_patches_excluded_from_decision_time_inputs") is not True:
        errors.append("gold/corrected patches must be excluded from decision-time inputs")
    if aggregate.get("quixbugs_counted_as_real_external_bug_evidence") is not False:
        errors.append("QuixBugs-only evidence must not count as real external bug evidence")
    if aggregate.get("fallback_controlled_fixtures_counted") is not False:
        errors.append("fallback controlled fixtures must not count as real external bug evidence")
    if aggregate.get("broad_organic_external_memory_lift_demonstrated") is not False:
        errors.append("broad organic external memory lift must remain false")
    if aggregate.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must remain false")
    if aggregate.get("full_scoring_allowed") is not False or aggregate.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("full scoring must remain NOT_RUN/disallowed")

    episode_dir = CAMPAIGN_DIR / "episodes"
    episode_dirs = sorted(episode_dir.glob("episode_*")) if episode_dir.exists() else []
    for directory in episode_dirs:
        errors.extend(audit_episode(directory))

    if v23.get("aggregate_result") != "limited_known_external_or_benchmark_memory_lift_criteria_met":
        errors.append("v2.3 QuixBugs benchmark result must remain preserved")
    if v23.get("benchmark_bug_episode_count") != 3 or v23.get("known_external_bug_episode_count") != 0:
        errors.append("v2.3 must remain benchmark-only, not organic known bug evidence")
    if v22.get("aggregate_result") != "limited_external_fork_controlled_fixture_memory_lift_criteria_met":
        errors.append("v2.2 controlled fixture result must remain preserved")
    if v19.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("v1.9 user-owned result must remain preserved")
    if v18.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 seeded result must remain preserved")
    if e003.get("result_classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("Episode 003 negative simple-task result must remain preserved")
    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper quarantine must remain unchanged")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    alpha_summary = alpha_classification.get("summary") if isinstance(alpha_classification.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")

    errors.extend(verify_manifest(CAMPAIGN_DIR, recursive=True))
    errors.extend(
        require_text(
            CAMPAIGN_DIR / "campaign_summary.md",
            [
                "SWE-bench-style tasks are real GitHub issue tasks when reproduced safely.",
                "BugsInPy-style entries are real Python bug benchmark entries.",
                "Gold/corrected patches are outcome-only and excluded from decision-time inputs.",
                "Benchmark evidence must be labeled as benchmark evidence.",
                "QuixBugs-only evidence is not counted as real external bug evidence.",
                "Self-maintaining software remains undemonstrated.",
                "Full scoring remains disallowed.",
            ],
        )
    )
    errors.extend(
        require_text(
            SHAREABLE_SUMMARY,
            [
                "v2.4 SWE-bench/BugsInPy Real External Bug Replay Campaign",
                "SWE-bench-style tasks are real GitHub issue tasks when reproduced safely.",
                "BugsInPy-style entries are real Python bug benchmark entries.",
                "QuixBugs remains algorithmic benchmark evidence only",
                "Self-maintaining software remains undemonstrated.",
                "Full scoring remains disallowed.",
            ],
        )
    )

    if errors:
        print("v2.4 real external bug replay campaign audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v2.4 real external bug replay campaign audit: PASS")
    print("promoted candidates: 0")
    print("executed episodes: 0")
    print("scoreable episodes: 0")
    print(f"aggregate: {expected}")
    print("broad organic external memory lift demonstrated: false")
    print("self-maintaining software demonstrated: false")
    print("full scoring allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())

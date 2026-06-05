#!/usr/bin/env python3
"""Audit the v2.1b curated external candidate sourcing outputs."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = REPO_ROOT / "inputs" / "v2_1b_curated_candidate_sources.json"
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_1b_curated_external_candidate_sourcing"
HARNESS_SCRIPT = REPO_ROOT / "scripts" / "v2_1b_curated_external_candidate_sourcing.py"
SUMMARY_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
)
V21_HANDOFF_PATH = (
    REPO_ROOT / "outputs" / "v2_1_external_candidate_acquisition_harness" / "v2_2_handoff_recommendations.json"
)
V20_RESULTS_PATH = REPO_ROOT / "outputs" / "v2_0_external_fork_replay_pilot" / "pilot_results.json"
V19_COMPLETION_PATH = (
    REPO_ROOT
    / "outputs"
    / "v1_9_organic_style_replay_pilot_completion_pass"
    / "aggregate_v1_9_updated_memory_lift_assessment.json"
)
V18_CAMPAIGN_PATH = (
    REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign" / "aggregate_memory_lift_assessment.json"
)
EPISODE_003_PATH = REPO_ROOT / "outputs" / "v1_8_episode_003_torus_limited_replay_scoring" / "limited_scoring_result.json"
BETA_REPLAY_PLAN_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
BETA_SCORING_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
)
ALPHA_CLASSIFICATION_PATH = (
    REPO_ROOT / "controllergate_v1_7_alpha" / "traces" / "audits" / "episode_review_classification.json"
)

REQUIRED_OUTPUT_FILES = [
    "curated_candidate_search_log.json",
    "curated_candidate_preflight_results.json",
    "curated_candidate_ranked_pool.json",
    "curated_candidate_rejection_table.json",
    "curated_candidate_replay_readiness_summary.md",
    "v2_2_handoff_recommendations.json",
    "candidate_source_gap_analysis.md",
    "SHA256SUMS.txt",
]

CONTROLLED_CLASSIFICATIONS = {
    "ready_for_v2_2_candidate",
    "needs_manual_review",
    "not_ready",
    "blocked_candidate_source_unavailable",
    "blocked_local_replay_failed",
    "rejected_no_local_test_command",
    "rejected_no_deterministic_failure",
    "rejected_private_service_required",
    "rejected_license_or_ethics_unclear",
    "rejected_runtime_too_large",
    "rejected_environment_not_reproducible",
    "rejected_subjective_validator",
    "rejected_security_exploit_target",
    "rejected_remote_ci_only",
    "rejected_no_baseline_path",
    "rejected_no_corruption_check",
}


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


def verify_sha256_manifest(base_dir: Path) -> list[str]:
    manifest_path = base_dir / "SHA256SUMS.txt"
    if not manifest_path.exists():
        return [f"missing SHA256SUMS.txt in {base_dir}"]
    errors: list[str] = []
    seen: set[str] = set()
    for line_no, line in enumerate(manifest_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 2:
            errors.append(f"{manifest_path}:{line_no}: expected '<sha256>  <path>'")
            continue
        expected, rel = parts
        seen.add(rel)
        path = base_dir / rel
        if not path.exists():
            errors.append(f"{manifest_path}:{line_no}: missing artifact {rel}")
            continue
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"{manifest_path}:{line_no}: hash mismatch for {rel}")
    for path in base_dir.rglob("*"):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rel = str(path.relative_to(base_dir)).replace("\\", "/")
            if rel not in seen:
                errors.append(f"SHA256SUMS missing artifact entry {rel}")
    return errors


def main() -> int:
    errors: list[str] = []
    if not HARNESS_SCRIPT.exists():
        errors.append(f"missing v2.1b harness script: {HARNESS_SCRIPT}")
    if not INPUT_PATH.exists():
        errors.append(f"missing v2.1b input file: {INPUT_PATH}")
    if not OUTPUT_DIR.exists():
        errors.append(f"missing v2.1b output directory: {OUTPUT_DIR}")
    for name in REQUIRED_OUTPUT_FILES:
        path = OUTPUT_DIR / name
        if not path.exists():
            errors.append(f"missing v2.1b output: {name}")
        elif path.stat().st_size == 0:
            errors.append(f"v2.1b output is empty: {name}")

    input_data, input_errors = load_json(INPUT_PATH)
    search_log, search_errors = load_json(OUTPUT_DIR / "curated_candidate_search_log.json")
    preflight, preflight_errors = load_json(OUTPUT_DIR / "curated_candidate_preflight_results.json")
    ranked_pool, ranked_errors = load_json(OUTPUT_DIR / "curated_candidate_ranked_pool.json")
    rejection_table, rejection_errors = load_json(OUTPUT_DIR / "curated_candidate_rejection_table.json")
    handoff, handoff_errors = load_json(OUTPUT_DIR / "v2_2_handoff_recommendations.json")
    gap, gap_errors = load_json(OUTPUT_DIR / "candidate_source_gap_analysis.json")
    v21, v21_errors = load_json(V21_HANDOFF_PATH)
    v20, v20_errors = load_json(V20_RESULTS_PATH)
    v19, v19_errors = load_json(V19_COMPLETION_PATH)
    v18, v18_errors = load_json(V18_CAMPAIGN_PATH)
    episode_003, episode_003_errors = load_json(EPISODE_003_PATH)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY_PLAN_PATH)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING_PATH)
    alpha_classification, alpha_errors = load_json(ALPHA_CLASSIFICATION_PATH)
    errors.extend(
        input_errors
        + search_errors
        + preflight_errors
        + ranked_errors
        + rejection_errors
        + handoff_errors
        + gap_errors
        + v21_errors
        + v20_errors
        + v19_errors
        + v18_errors
        + episode_003_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_errors
    )

    candidates = input_data.get("candidates") if isinstance(input_data.get("candidates"), list) else []
    if len(candidates) != 10:
        errors.append("v2.1b input must contain 10 curated candidate descriptors")
    if search_log.get("harness_id") != "v2_1b_curated_external_candidate_sourcing":
        errors.append("search log harness_id mismatch")
    if search_log.get("harness_status") != "curated_candidate_preflight_completed":
        errors.append("search log status must be curated_candidate_preflight_completed")
    if search_log.get("candidate_count") != len(candidates):
        errors.append("search log candidate_count must match input descriptors")
    if search_log.get("upstream_interactions") != "none":
        errors.append("v2.1b must not disrupt upstream maintainers")
    if search_log.get("remote_ci_logs_used") is not False:
        errors.append("v2.1b must not use expired/remote-only CI logs")
    if search_log.get("repairs_executed") is not False:
        errors.append("v2.1b must not execute repairs")
    if search_log.get("memory_vs_no_memory_scoring_run") is not False:
        errors.append("v2.1b must not run memory-vs-no-memory scoring")
    if search_log.get("external_memory_lift_demonstrated") is not False:
        errors.append("v2.1b must not demonstrate external memory lift")
    if search_log.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.1b must not demonstrate self-maintaining software")
    if search_log.get("full_scoring_allowed") is not False:
        errors.append("v2.1b must keep full scoring false")
    if search_log.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.1b must keep ControllerGate full scoring NOT_RUN")

    results = preflight.get("results") if isinstance(preflight.get("results"), list) else []
    ranked = ranked_pool.get("ranked_candidates") if isinstance(ranked_pool.get("ranked_candidates"), list) else []
    if len(results) != len(candidates):
        errors.append("preflight results must include each v2.1b candidate")
    if len(ranked) != len(results):
        errors.append("ranked pool must include each v2.1b result")
    observed_sort = [(item.get("readiness_score"), item.get("source_quality_score")) for item in ranked]
    expected_sort = sorted(observed_sort, key=lambda item: (-item[0], -item[1]))
    if observed_sort != expected_sort:
        errors.append("ranked pool must be sorted by readiness score descending, then source quality score descending")

    ready_count = 0
    manual_count = 0
    rejected_or_blocked_count = 0
    for item in ranked:
        candidate_id = item.get("candidate_id")
        classification = item.get("classification")
        if classification not in CONTROLLED_CLASSIFICATIONS:
            errors.append(f"{candidate_id}: uncontrolled classification {classification!r}")
        readiness = item.get("readiness_score")
        source_quality = item.get("source_quality_score")
        if not isinstance(readiness, int | float) or readiness < 0 or readiness > 100:
            errors.append(f"{candidate_id}: readiness_score must be numeric 0-100")
        if not isinstance(source_quality, int | float) or source_quality < 0 or source_quality > 100:
            errors.append(f"{candidate_id}: source_quality_score must be numeric 0-100")
        if classification == "ready_for_v2_2_candidate":
            ready_count += 1
        elif classification == "needs_manual_review":
            manual_count += 1
        elif str(classification).startswith(("rejected", "blocked")) or classification == "not_ready":
            rejected_or_blocked_count += 1
        boundaries = item.get("claim_boundaries") if isinstance(item.get("claim_boundaries"), dict) else {}
        if boundaries.get("candidate_readiness_is_not_repair_success") is not True:
            errors.append(f"{candidate_id}: readiness boundary missing")
        if boundaries.get("repair_scoring_run") is not False:
            errors.append(f"{candidate_id}: repair scoring must remain false")
        if boundaries.get("memory_vs_no_memory_repairs_run") is not False:
            errors.append(f"{candidate_id}: memory-vs-no-memory repairs must remain false")
        if boundaries.get("external_memory_lift_demonstrated") is not False:
            errors.append(f"{candidate_id}: external memory lift must remain false")
        if boundaries.get("self_maintaining_software_demonstrated") is not False:
            errors.append(f"{candidate_id}: self-maintaining software must remain false")
        if boundaries.get("full_scoring_allowed") is not False:
            errors.append(f"{candidate_id}: full scoring must remain false")

    if ready_count != preflight.get("ready_candidate_count"):
        errors.append("preflight ready_candidate_count mismatch")
    if manual_count != preflight.get("manual_review_candidate_count"):
        errors.append("preflight manual_review_candidate_count mismatch")
    if rejected_or_blocked_count != preflight.get("rejected_or_blocked_candidate_count"):
        errors.append("preflight rejected_or_blocked_candidate_count mismatch")
    if ready_count != handoff.get("ready_candidate_count"):
        errors.append("handoff ready count mismatch")
    if manual_count != handoff.get("manual_review_candidate_count"):
        errors.append("handoff manual-review count mismatch")
    if rejected_or_blocked_count != handoff.get("rejected_or_blocked_candidate_count"):
        errors.append("handoff rejected/blocked count mismatch")
    if ready_count >= 3 and handoff.get("recommendation") != "v2_2_external_fork_limited_replay_execution":
        errors.append("3+ ready candidates must recommend v2.2 limited replay execution")
    if 1 <= ready_count <= 2 and handoff.get("recommendation") != "v2_2_small_external_fork_probe":
        errors.append("1-2 ready candidates must recommend v2.2 small external/fork probe")
    if ready_count == 0 and manual_count > 0 and handoff.get("recommendation") != "manual_candidate_triage_before_v2_2":
        errors.append("0 ready with manual-review candidates must recommend manual triage")
    if ready_count == 0 and manual_count == 0 and handoff.get("recommendation") != "continue_curated_candidate_acquisition":
        errors.append("0 ready and 0 manual-review candidates must recommend continued acquisition")
    if handoff.get("repair_execution_allowed_now") is not False:
        errors.append("handoff must not allow repair execution now")
    if handoff.get("scoring_allowed_now") is not False:
        errors.append("handoff must not allow scoring now")
    if handoff.get("external_memory_lift_demonstrated") is not False:
        errors.append("handoff must not demonstrate external memory lift")
    if handoff.get("self_maintaining_software_demonstrated") is not False:
        errors.append("handoff must not demonstrate self-maintaining software")
    if handoff.get("full_scoring_allowed") is not False:
        errors.append("handoff must keep full scoring false")
    if handoff.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("handoff must keep ControllerGate full scoring NOT_RUN")

    controlled = set(rejection_table.get("controlled_classifications") or [])
    if controlled != CONTROLLED_CLASSIFICATIONS:
        errors.append("rejection table controlled classifications mismatch")
    for record in rejection_table.get("records", []):
        if record.get("classification") not in CONTROLLED_CLASSIFICATIONS:
            errors.append(f"rejection table has uncontrolled classification {record.get('classification')!r}")

    if gap.get("ready_candidate_count") != ready_count:
        errors.append("gap analysis ready count mismatch")
    if gap.get("manual_review_candidate_count") != manual_count:
        errors.append("gap analysis manual-review count mismatch")
    if gap.get("blocked_acquisition_is_negative_capability_evidence") is not False:
        errors.append("gap analysis must say blocked acquisition is not negative capability evidence")
    if not gap.get("desired_next_sources"):
        errors.append("gap analysis must include desired next sources")

    errors.extend(verify_sha256_manifest(OUTPUT_DIR))
    if v21.get("recommendation") != "continue_candidate_acquisition":
        errors.append("v2.1 harness result must remain preserved")
    if v21.get("ready_candidate_count") != 0:
        errors.append("v2.1 ready candidate count must remain 0")
    if v20.get("aggregate_classification") != "blocked_external_candidate_acquisition_failure":
        errors.append("v2.0 blocked acquisition result must remain preserved")
    if v20.get("scoreable_episode_count") != 0:
        errors.append("v2.0 scoreable external/fork count must remain 0")
    if v20.get("external_fork_memory_lift_demonstrated") is not False:
        errors.append("v2.0 must not demonstrate external/fork memory lift")
    if v19.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("v1.9 limited user-owned result must remain preserved")
    if v19.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("v1.9 must not demonstrate organic external memory lift")
    if v18.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 limited seeded result must remain preserved")
    if episode_003.get("result_classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("Episode 003 simple-task negative result must remain preserved")
    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper quarantine must remain unchanged")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    alpha_summary = alpha_classification.get("summary") if isinstance(alpha_classification.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")

    errors.extend(
        require_text(
            OUTPUT_DIR / "curated_candidate_replay_readiness_summary.md",
            [
                "v2.1b improves candidate sourcing quality.",
                "Candidate readiness is not repair success.",
                "Ready candidates only authorize future v2.2 replay attempts.",
                "Blocked acquisition is not negative capability evidence.",
                "External memory lift remains undemonstrated.",
                "Self-maintaining software remains undemonstrated.",
                "Full scoring remains disallowed.",
            ],
        )
    )
    errors.extend(
        require_text(
            SUMMARY_PATH,
            [
                "## v2.1b Curated External Candidate Sourcing Result",
                "v2.1b improves candidate sourcing quality.",
                "Candidate readiness is not repair success.",
                "Ready candidates only authorize future v2.2 replay attempts.",
                "Blocked acquisition is not negative capability evidence.",
                "External memory lift remains undemonstrated.",
                "Self-maintaining software remains undemonstrated.",
            ],
        )
    )

    if errors:
        print("v2.1b curated external candidate sourcing audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v2.1b curated external candidate sourcing audit: PASS")
    print(f"candidate pool size: {len(ranked)}")
    print(f"ready candidates: {ready_count}")
    print(f"manual-review candidates: {manual_count}")
    print(f"rejected/blocked candidates: {rejected_or_blocked_count}")
    print(f"v2.2 handoff recommendation: {handoff.get('recommendation')}")
    print("external memory lift demonstrated: false")
    print("self-maintaining software demonstrated: false")
    print("full scoring allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())

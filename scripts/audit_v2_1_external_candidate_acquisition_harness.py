#!/usr/bin/env python3
"""Audit the v2.1 external candidate acquisition harness outputs."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_SCRIPT = REPO_ROOT / "scripts" / "v2_1_external_candidate_acquisition_harness.py"
INPUT_PATH = REPO_ROOT / "inputs" / "v2_1_external_candidate_sources.json"
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_1_external_candidate_acquisition_harness"
PLAN_PATH = REPO_ROOT / "outputs" / "v2_1_external_candidate_acquisition_harness_plan.json"
SUMMARY_PATH = (
    REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
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
    "external_candidate_search_log.json",
    "external_candidate_preflight_results.json",
    "external_candidate_ranked_pool.json",
    "external_candidate_rejection_table.json",
    "external_candidate_replay_readiness_summary.md",
    "v2_2_handoff_recommendations.json",
    "SHA256SUMS.txt",
]

CONTROLLED_CLASSIFICATIONS = {
    "accepted_preflight_candidate",
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
    "blocked_candidate_metadata_incomplete",
    "blocked_candidate_acquisition_unavailable",
}

READINESS_STATUSES = {
    "ready_for_v2_2_candidate",
    "needs_manual_review",
    "not_ready",
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
        errors.append(f"harness script missing: {HARNESS_SCRIPT}")
    if not INPUT_PATH.exists():
        errors.append(f"candidate input file missing: {INPUT_PATH}")
    if not OUTPUT_DIR.exists():
        errors.append(f"output directory missing: {OUTPUT_DIR}")
    for name in REQUIRED_OUTPUT_FILES:
        path = OUTPUT_DIR / name
        if not path.exists():
            errors.append(f"missing harness output: {name}")
        elif path.stat().st_size == 0:
            errors.append(f"harness output is empty: {name}")

    input_data, input_errors = load_json(INPUT_PATH)
    search_log, search_errors = load_json(OUTPUT_DIR / "external_candidate_search_log.json")
    preflight, preflight_errors = load_json(OUTPUT_DIR / "external_candidate_preflight_results.json")
    ranked_pool, ranked_errors = load_json(OUTPUT_DIR / "external_candidate_ranked_pool.json")
    rejection_table, rejection_errors = load_json(OUTPUT_DIR / "external_candidate_rejection_table.json")
    handoff, handoff_errors = load_json(OUTPUT_DIR / "v2_2_handoff_recommendations.json")
    plan, plan_errors = load_json(PLAN_PATH)
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
        + plan_errors
        + v20_errors
        + v19_errors
        + v18_errors
        + episode_003_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_errors
    )

    candidates = input_data.get("candidates") if isinstance(input_data.get("candidates"), list) else []
    if len(candidates) != 5:
        errors.append("candidate input must contain 5 descriptors for this run")
    if search_log.get("harness_id") != "v2_1_external_candidate_acquisition_harness":
        errors.append("search log harness_id mismatch")
    if search_log.get("harness_status") != "real_external_candidate_preflight_completed":
        errors.append("search log must record real_external_candidate_preflight_completed")
    if search_log.get("candidate_count") != len(candidates):
        errors.append("search log candidate_count must match input descriptor count")
    if search_log.get("upstream_interactions") != "none":
        errors.append("harness must not disrupt or interact with upstream")
    if search_log.get("remote_ci_logs_used") is not False:
        errors.append("harness must not use remote-only CI logs")
    if search_log.get("repairs_executed") is not False:
        errors.append("harness must not execute repairs")
    if search_log.get("memory_vs_no_memory_scoring_run") is not False:
        errors.append("harness must not run memory-vs-no-memory scoring")
    if search_log.get("external_memory_lift_demonstrated") is not False:
        errors.append("harness must not demonstrate external memory lift")
    if search_log.get("self_maintaining_software_demonstrated") is not False:
        errors.append("harness must not demonstrate self-maintaining software")

    records = preflight.get("results") if isinstance(preflight.get("results"), list) else []
    ranked = ranked_pool.get("ranked_candidates") if isinstance(ranked_pool.get("ranked_candidates"), list) else []
    if len(records) != len(candidates):
        errors.append("preflight results must include each input candidate")
    if len(ranked) != len(records):
        errors.append("ranked pool must include each preflight record")
    scores = [item.get("readiness_score") for item in ranked]
    if scores != sorted(scores, reverse=True):
        errors.append("ranked pool must be sorted by readiness_score descending")
    for item in ranked:
        candidate_id = item.get("candidate_id")
        score = item.get("readiness_score")
        if not isinstance(score, int | float) or score < 0 or score > 100:
            errors.append(f"{candidate_id}: readiness_score must be numeric 0-100")
        classification = item.get("classification")
        if classification not in CONTROLLED_CLASSIFICATIONS:
            errors.append(f"{candidate_id}: uncontrolled classification {classification!r}")
        status = item.get("readiness_status")
        if status not in READINESS_STATUSES:
            errors.append(f"{candidate_id}: invalid readiness_status {status!r}")
        if status == "ready_for_v2_2_candidate" and classification != "accepted_preflight_candidate":
            errors.append(f"{candidate_id}: ready candidates must have accepted_preflight_candidate classification")
        boundaries = item.get("claim_boundaries") if isinstance(item.get("claim_boundaries"), dict) else {}
        if boundaries.get("candidate_readiness_is_not_repair_success") is not True:
            errors.append(f"{candidate_id}: candidate readiness boundary missing")
        if boundaries.get("external_memory_lift_demonstrated") is not False:
            errors.append(f"{candidate_id}: external memory lift must remain false")
        if boundaries.get("self_maintaining_software_demonstrated") is not False:
            errors.append(f"{candidate_id}: self-maintaining software must remain false")
        if boundaries.get("full_scoring_allowed") is not False:
            errors.append(f"{candidate_id}: full scoring must remain false")
        source = item.get("source_custody_preflight") if isinstance(item.get("source_custody_preflight"), dict) else {}
        if source.get("no_upstream_disruption_required") is not True:
            errors.append(f"{candidate_id}: no upstream disruption boundary missing")

    controlled_vocab = set(rejection_table.get("controlled_vocabulary") or [])
    if controlled_vocab != CONTROLLED_CLASSIFICATIONS:
        errors.append("rejection table controlled vocabulary mismatch")
    rejection_records = rejection_table.get("records") if isinstance(rejection_table.get("records"), list) else []
    for record in rejection_records:
        classification = record.get("classification")
        if classification not in CONTROLLED_CLASSIFICATIONS:
            errors.append(f"rejection table uses uncontrolled classification {classification!r}")

    ready_count = ranked_pool.get("ready_for_v2_2_candidate_count")
    manual_count = ranked_pool.get("needs_manual_review_count")
    not_ready_count = ranked_pool.get("not_ready_count")
    if ready_count != handoff.get("ready_candidate_count"):
        errors.append("handoff ready count must match ranked pool")
    if manual_count != handoff.get("manual_review_candidate_count"):
        errors.append("handoff manual-review count must match ranked pool")
    if ready_count == 0 and handoff.get("recommendation") != "continue_candidate_acquisition":
        errors.append("zero ready candidates must recommend continue_candidate_acquisition")
    if ready_count == 0 and handoff.get("v2_2_authorized_next_step") is not False:
        errors.append("zero ready candidates must not authorize v2.2")
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
    if ready_count != 0 or manual_count != 0 or not_ready_count != 5:
        errors.append("expected this run to produce 0 ready, 0 manual-review, and 5 not-ready candidates")

    errors.extend(verify_sha256_manifest(OUTPUT_DIR))
    if plan.get("plan_id") != "v2_1_external_candidate_acquisition_harness_plan":
        errors.append("v2.1 plan must exist and have matching plan_id")
    if plan.get("full_scoring_allowed") is not False:
        errors.append("v2.1 plan must keep full scoring false")
    if v20.get("aggregate_classification") != "blocked_external_candidate_acquisition_failure":
        errors.append("v2.0 blocked result must remain preserved")
    if v20.get("scoreable_episode_count") != 0:
        errors.append("v2.0 scoreable external/fork count must remain 0")
    if v20.get("external_fork_memory_lift_demonstrated") is not False:
        errors.append("v2.0 external/fork memory lift must remain false")
    if v19.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("v1.9 limited user-owned result must remain preserved")
    if v19.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("v1.9 must not demonstrate organic external memory lift")
    if v18.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 limited seeded result must remain preserved")
    if episode_003.get("result_classification") != "negative_evidence_no_memory_lift_on_seeded_controlled_episode":
        errors.append("Episode 003 simple-task negative result must remain preserved")
    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper quarantine must remain unchanged at 0 deterministic-replay-ready")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    alpha_summary = alpha_classification.get("summary") if isinstance(alpha_classification.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")

    errors.extend(
        require_text(
            OUTPUT_DIR / "external_candidate_replay_readiness_summary.md",
            [
                "v2.1 implements candidate acquisition/preflight.",
                "Candidate acquisition is not repair success.",
                "Ready candidates only authorize future v2.2 replay attempts.",
                "Blocked candidate acquisition is not negative capability evidence.",
                "External memory lift remains undemonstrated.",
                "Self-maintaining software remains undemonstrated.",
                "Full scoring remains disallowed.",
                "controllergate.toml",
                "pytest adapter first",
            ],
        )
    )
    errors.extend(
        require_text(
            SUMMARY_PATH,
            [
                "## v2.1 External Candidate Acquisition Harness Result",
                "v2.1 implements candidate acquisition/preflight.",
                "Candidate acquisition is not repair success.",
                "Ready candidates only authorize future v2.2 replay attempts.",
                "Blocked candidate acquisition is not negative capability evidence.",
                "External memory lift remains undemonstrated.",
                "Self-maintaining software remains undemonstrated.",
            ],
        )
    )

    if errors:
        print("v2.1 external candidate acquisition harness audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v2.1 external candidate acquisition harness audit: PASS")
    print(f"candidate pool size: {len(ranked)}")
    print(f"ready candidates: {ready_count}")
    print(f"manual-review candidates: {manual_count}")
    print(f"not-ready candidates: {not_ready_count}")
    print(f"v2.2 handoff recommendation: {handoff.get('recommendation')}")
    print("external memory lift demonstrated: false")
    print("self-maintaining software demonstrated: false")
    print("full scoring allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())

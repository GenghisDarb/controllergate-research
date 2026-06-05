#!/usr/bin/env python3
"""Audit v2.1c external-fork controlled fixture triage outputs."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
TRIAGE_DIR = REPO_ROOT / "outputs" / "v2_1c_external_fork_controlled_fixture_triage"
V21B_PREFLIGHT = REPO_ROOT / "outputs" / "v2_1b_curated_external_candidate_sourcing" / "curated_candidate_preflight_results.json"
V21B_HANDOFF = REPO_ROOT / "outputs" / "v2_1b_curated_external_candidate_sourcing" / "v2_2_handoff_recommendations.json"
V21_HANDOFF = REPO_ROOT / "outputs" / "v2_1_external_candidate_acquisition_harness" / "v2_2_handoff_recommendations.json"
V20_RESULTS = REPO_ROOT / "outputs" / "v2_0_external_fork_replay_pilot" / "pilot_results.json"
V19_AGG = (
    REPO_ROOT
    / "outputs"
    / "v1_9_organic_style_replay_pilot_completion_pass"
    / "aggregate_v1_9_updated_memory_lift_assessment.json"
)
V18_AGG = REPO_ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign" / "aggregate_memory_lift_assessment.json"
BETA_REPLAY = REPO_ROOT / "controllergate_v1_7_beta" / "outputs" / "v1_7_beta_replay_eligibility_plan.json"
BETA_SCORING = REPO_ROOT / "controllergate_v1_7_beta" / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
ALPHA_CLASSIFICATION = REPO_ROOT / "controllergate_v1_7_alpha" / "traces" / "audits" / "episode_review_classification.json"

REQUIRED_FILES = [
    "fixture_triage_plan.json",
    "fixture_triage_results.json",
    "candidate_promotion_table.json",
    "v2_2_ready_controlled_fixture_candidate_pool.json",
    "v2_2_known_external_bug_candidate_pool.json",
    "candidate_gap_report.md",
    "v2_2_handoff_recommendations.json",
    "SHA256SUMS.txt",
]

PROMOTION_STATUSES = {
    "promoted_ready_for_v2_2_known_external_bug",
    "promoted_ready_for_v2_2_external_fork_controlled_fixture",
    "still_needs_manual_review",
    "rejected_after_triage",
    "blocked_source_unavailable",
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
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            errors.append(f"{manifest}:{line_no}: hash mismatch for {rel}")
    for path in directory.rglob("*"):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rel = str(path.relative_to(directory)).replace("\\", "/")
            if rel not in seen:
                errors.append(f"SHA256SUMS missing artifact entry {rel}")
    return errors


def main() -> int:
    errors: list[str] = []
    if not TRIAGE_DIR.exists():
        errors.append(f"missing v2.1c triage directory: {TRIAGE_DIR}")
    for name in REQUIRED_FILES:
        path = TRIAGE_DIR / name
        if not path.exists():
            errors.append(f"missing v2.1c output: {name}")
        elif path.stat().st_size == 0:
            errors.append(f"empty v2.1c output: {name}")

    preflight, preflight_errors = load_json(V21B_PREFLIGHT)
    plan, plan_errors = load_json(TRIAGE_DIR / "fixture_triage_plan.json")
    results, results_errors = load_json(TRIAGE_DIR / "fixture_triage_results.json")
    table, table_errors = load_json(TRIAGE_DIR / "candidate_promotion_table.json")
    controlled_pool, controlled_errors = load_json(TRIAGE_DIR / "v2_2_ready_controlled_fixture_candidate_pool.json")
    known_pool, known_errors = load_json(TRIAGE_DIR / "v2_2_known_external_bug_candidate_pool.json")
    handoff, handoff_errors = load_json(TRIAGE_DIR / "v2_2_handoff_recommendations.json")
    v21b, v21b_errors = load_json(V21B_HANDOFF)
    v21, v21_errors = load_json(V21_HANDOFF)
    v20, v20_errors = load_json(V20_RESULTS)
    v19, v19_errors = load_json(V19_AGG)
    v18, v18_errors = load_json(V18_AGG)
    beta_replay, beta_replay_errors = load_json(BETA_REPLAY)
    beta_scoring, beta_scoring_errors = load_json(BETA_SCORING)
    alpha_classification, alpha_errors = load_json(ALPHA_CLASSIFICATION)
    errors.extend(
        preflight_errors
        + plan_errors
        + results_errors
        + table_errors
        + controlled_errors
        + known_errors
        + handoff_errors
        + v21b_errors
        + v21_errors
        + v20_errors
        + v19_errors
        + v18_errors
        + beta_replay_errors
        + beta_scoring_errors
        + alpha_errors
    )

    manual_candidates = [item for item in preflight.get("results", []) if item.get("classification") == "needs_manual_review"]
    records = results.get("records") if isinstance(results.get("records"), list) else []
    if len(manual_candidates) != 5:
        errors.append("v2.1b must still have exactly 5 manual-review candidates")
    if len(records) != 5:
        errors.append("v2.1c must triage exactly 5 candidates")
    if {item.get("candidate_id") for item in manual_candidates} != {item.get("candidate_id") for item in records}:
        errors.append("v2.1c triaged candidate IDs must match v2.1b manual-review candidates")

    if plan.get("controlled_fixture_policy", {}).get("label") != "external_fork_controlled_fixture":
        errors.append("controlled fixture policy label mismatch")
    if plan.get("controlled_fixture_policy", {}).get("not_organic_external_bug") is not True:
        errors.append("controlled fixtures must be marked not organic external bugs")
    if plan.get("controlled_fixture_policy", {}).get("upstream_push_allowed") is not False:
        errors.append("upstream push must be disallowed")
    if plan.get("controlled_fixture_policy", {}).get("security_exploit_allowed") is not False:
        errors.append("security exploit tasks must be disallowed")

    promoted = 0
    for record in records:
        candidate_id = record.get("candidate_id")
        status = record.get("promotion_status")
        if status not in PROMOTION_STATUSES:
            errors.append(f"{candidate_id}: uncontrolled promotion_status {status!r}")
        for score_field in ["readiness_score_before", "readiness_score_after", "source_quality_score"]:
            score = record.get(score_field)
            if not isinstance(score, int | float) or score < 0 or score > 100:
                errors.append(f"{candidate_id}: {score_field} must be numeric 0-100")
        if status and status.startswith("promoted"):
            promoted += 1
            if record.get("readiness_score_after", 0) < 75:
                errors.append(f"{candidate_id}: promoted candidate readiness_score_after must be >= 75")
        if status == "promoted_ready_for_v2_2_external_fork_controlled_fixture":
            if record.get("candidate_type_after_triage") != "external_fork_controlled_fixture_candidate":
                errors.append(f"{candidate_id}: controlled fixture candidate type mismatch")
            if not record.get("injection_plan_summary"):
                errors.append(f"{candidate_id}: controlled fixture promotion missing injection_plan_summary")
            if not record.get("reversibility_plan"):
                errors.append(f"{candidate_id}: controlled fixture promotion missing reversibility_plan")
            if record.get("failure_reference_type") != "local_controlled_fixture_injection":
                errors.append(f"{candidate_id}: controlled fixture failure reference type mismatch")
            if "organic" in str(record.get("notes", "")).lower() and "not organic" not in str(record.get("notes", "")).lower():
                errors.append(f"{candidate_id}: controlled fixture note risks organic labeling")
        if status == "promoted_ready_for_v2_2_known_external_bug":
            if record.get("failure_reference_type") not in {"known_external_bug_reference", "known_issue_branch", "known_failing_test"}:
                errors.append(f"{candidate_id}: known external bug promotion lacks real failure reference")
            if not record.get("failure_reference"):
                errors.append(f"{candidate_id}: known external bug promotion missing failure_reference")

    controlled_records = controlled_pool.get("records") if isinstance(controlled_pool.get("records"), list) else []
    known_records = known_pool.get("records") if isinstance(known_pool.get("records"), list) else []
    if len(controlled_records) != 3:
        errors.append("expected 3 controlled fixture candidates in ready pool")
    if known_records != []:
        errors.append("known external bug pool must be empty for this campaign")
    if results.get("promoted_count") != promoted or promoted != 3:
        errors.append("v2.1c promoted_count must be 3")
    if handoff.get("promoted_candidate_count") != 3:
        errors.append("handoff promoted count must be 3")
    if handoff.get("recommendation") != "execute_v2_2_external_fork_controlled_fixture_replay_pilot":
        errors.append("handoff must execute v2.2 when 3 candidates promote")
    if handoff.get("repair_scoring_run_during_triage") is not False:
        errors.append("v2.1c triage must not run repair scoring itself")
    if handoff.get("organic_external_memory_lift_demonstrated") is not False:
        errors.append("v2.1c must not demonstrate organic external memory lift")
    if handoff.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.1c must not demonstrate self-maintaining software")
    if handoff.get("full_scoring_allowed") is not False:
        errors.append("v2.1c full scoring must remain false")
    if handoff.get("controllergate_full_scoring") != "NOT_RUN":
        errors.append("v2.1c ControllerGate full scoring must remain NOT_RUN")

    if v21b.get("recommendation") != "manual_candidate_triage_before_v2_2":
        errors.append("v2.1b result must remain preserved")
    if v21.get("recommendation") != "continue_candidate_acquisition":
        errors.append("v2.1 result must remain preserved")
    if v20.get("aggregate_classification") != "blocked_external_candidate_acquisition_failure":
        errors.append("v2.0 blocked acquisition must remain preserved")
    if v19.get("aggregate_classification") != "limited_user_owned_organic_style_memory_lift_criteria_met":
        errors.append("v1.9 positive limited result must remain preserved")
    if v18.get("aggregate_classification") != "limited_seeded_controlled_memory_lift_criteria_met":
        errors.append("v1.8 positive limited result must remain preserved")
    if beta_replay.get("deterministic_replay_ready_count") != 0:
        errors.append("TatMapper quarantine must remain unchanged")
    if beta_scoring.get("full_scoring_allowed") is not False:
        errors.append("beta full scoring must remain false")
    alpha_summary = alpha_classification.get("summary") if isinstance(alpha_classification.get("summary"), dict) else {}
    if alpha_summary.get("full_scoring_allowed") is not False:
        errors.append("alpha full scoring must remain false")

    errors.extend(verify_manifest(TRIAGE_DIR))
    errors.extend(
        require_text(
            TRIAGE_DIR / "candidate_gap_report.md",
            [
                "No controlled fixture is labeled organic external.",
                "Known external bug replay remains stronger evidence",
            ],
        )
    )

    if errors:
        print("v2.1c external-fork controlled fixture triage audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v2.1c external-fork controlled fixture triage audit: PASS")
    print("triaged candidates: 5")
    print("promoted controlled fixture candidates: 3")
    print("known external bug candidates: 0")
    print("v2.2 handoff: execute_v2_2_external_fork_controlled_fixture_replay_pilot")
    print("organic external memory lift demonstrated: false")
    print("self-maintaining software demonstrated: false")
    print("full scoring allowed: false")
    return 0


if __name__ == "__main__":
    sys.exit(main())

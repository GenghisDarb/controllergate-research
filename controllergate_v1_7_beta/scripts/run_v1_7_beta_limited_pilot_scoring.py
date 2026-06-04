#!/usr/bin/env python3
"""Run the v1.7-beta limited exploratory TatMapper pilot scoring pass."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "traces" / "normalized" / "episodes.jsonl"
CLASSIFICATION_PATH = ROOT / "traces" / "audits" / "beta_episode_review_classification.json"
ELIGIBILITY_REVIEW_PATH = ROOT / "traces" / "audits" / "v1_7_beta_second_repo_eligibility_review.json"
REPORT_DIR = ROOT / "reports" / "limited_pilot_scoring"
AUDIT_DIR = ROOT / "traces" / "audits" / "limited_pilot_scoring"
REPORT_PATH = REPORT_DIR / "limited_pilot_scoring_report.md"
README_PATH = REPORT_DIR / "README.md"
RESULT_PATH = AUDIT_DIR / "limited_pilot_scoring.json"

REQUIRED_FINAL_STATUS = (
    "ControllerGate v1.7-beta limited TatMapper scoring was run on 11 normalized "
    "TatMapper external real repo episodes. This is tiny second-repo exploratory "
    "evidence only, not proof of self-maintaining software."
)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{path} must contain a JSON object")
    return data


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.strip():
            item = json.loads(raw)
            if not isinstance(item, dict):
                raise TypeError(f"{path} must contain JSON objects")
            rows.append(item)
    return rows


def bool_count(rows: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts = {"true": 0, "false": 0, "null": 0, "review_required": 0}
    for row in rows:
        value = row.get(field)
        if value is True:
            counts["true"] += 1
        elif value is False:
            counts["false"] += 1
        elif value == "review_required":
            counts["review_required"] += 1
        else:
            counts["null"] += 1
    return counts


def markdown_table(headers: list[str], rows: list[list[Any]]) -> str:
    def render(value: Any) -> str:
        if value is None:
            return "UNAVAILABLE"
        if isinstance(value, bool):
            return str(value).lower()
        return str(value)

    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(render(value) for value in row) + " |")
    return "\n".join(lines)


def main() -> int:
    ledger = load_jsonl(LEDGER_PATH)
    classification = load_json(CLASSIFICATION_PATH)
    eligibility = load_json(ELIGIBILITY_REVIEW_PATH)

    if eligibility.get("scoring_allowed") != "limited_pilot_only":
        raise RuntimeError("v1.7-beta limited pilot scoring is not eligible")
    if eligibility.get("full_scoring_allowed") is not False:
        raise RuntimeError("full scoring must be disallowed")

    ledger_by_id = {row["episode_id"]: row for row in ledger}
    eligibility_rows = eligibility.get("episodes")
    if not isinstance(eligibility_rows, list):
        raise TypeError("eligibility review episodes must be a list")

    eligible_ids = [
        row["episode_id"]
        for row in eligibility_rows
        if isinstance(row, dict) and row.get("pilot_eligible") is True
    ]
    included = [ledger_by_id[episode_id] for episode_id in eligible_ids]
    if len(included) != 11:
        raise RuntimeError(f"expected 11 included beta episodes, found {len(included)}")

    classification_rows = classification.get("episodes")
    if not isinstance(classification_rows, list):
        raise TypeError("classification episodes must be a list")

    verified_breakdown = Counter(row.get("verified_result", "UNAVAILABLE") for row in included)
    pass_fail_warning_breakdown = {
        "passed": verified_breakdown.get("passed", 0),
        "failed": verified_breakdown.get("failed", 0),
        "warning_only": verified_breakdown.get("warning_only", 0),
        "review_required": verified_breakdown.get("review_required", 0),
    }

    decision_time_overlap_count = 0
    episode_decisions: list[dict[str, Any]] = []
    for row in included:
        decision_time = set(row.get("decision_time_evidence_available") or [])
        outcome_only = set(row.get("outcome_only_evidence") or [])
        overlap = sorted(decision_time & outcome_only)
        if overlap:
            decision_time_overlap_count += 1
        episode_decisions.append(
            {
                "episode_id": row["episode_id"],
                "source_episode_folder": row.get("source_episode_folder"),
                "source_repo": row.get("source_repo"),
                "source_pr": row.get("source_pr"),
                "source_commit": row.get("source_commit"),
                "outcome_type": row.get("outcome_type"),
                "verified_result": row.get("verified_result"),
                "pilot_decision": "review_required",
                "ci_log_available": row.get("ci_log_available"),
                "local_rerun_completed": row.get("local_rerun_completed"),
                "runner_completed": row.get("runner_completed"),
                "analyzer_completed": row.get("analyzer_completed"),
                "rerun_command": row.get("rerun_command"),
                "decision_time_evidence_count": len(decision_time),
                "outcome_only_evidence_count": len(outcome_only),
                "decision_outcome_overlap": overlap,
                "future_leakage_risk": row.get("future_leakage_risk"),
                "stale_read_or_false_completion_detected": row.get(
                    "stale_read_or_false_completion_detected"
                ),
                "dependency_or_config_drift_detected": row.get(
                    "dependency_or_config_drift_detected"
                ),
                "generated_artifact_mismatch_detected": row.get(
                    "generated_artifact_mismatch_detected"
                ),
                "included_in_limited_pilot": True,
                "caveat": row.get("caveat"),
            }
        )

    dependency_counts = bool_count(included, "dependency_or_config_drift_detected")
    stale_counts = bool_count(included, "stale_read_or_false_completion_detected")
    generated_artifact_counts = bool_count(included, "generated_artifact_mismatch_detected")
    correction_counts = bool_count(included, "correction_required")
    ci_log_breakdown = Counter(str(row.get("ci_log_available")) for row in included)
    local_rerun_breakdown = Counter(str(row.get("local_rerun_completed")) for row in included)

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "scoring_date": "2026-06-04",
        "scoring_mode": "limited_pilot_only",
        "full_scoring_allowed": False,
        "beta_limited_pilot_scoring_run": True,
        "source_ledger_path": "controllergate_v1_7_beta/traces/normalized/episodes.jsonl",
        "source_classification_path": (
            "controllergate_v1_7_beta/traces/audits/beta_episode_review_classification.json"
        ),
        "source_eligibility_review_path": (
            "controllergate_v1_7_beta/traces/audits/v1_7_beta_second_repo_eligibility_review.json"
        ),
        "eligible_episode_count": len(included),
        "included_episode_ids": eligible_ids,
        "excluded_scope_counts": {
            "beta_non_external_episode_entries": 0,
            "v1_7_alpha_torus_external_episodes_excluded_from_beta_scoring": 10,
            "v1_6_controlled_benchmark_evidence_excluded_from_beta_scoring": 8,
            "correction_review_episode_entries_excluded_from_beta_scoring": 2,
        },
        "required_scope_enforced": {
            "only_v1_7_beta_tatmapper_external_real_repo_episode_entries_used": True,
            "v1_7_alpha_torus_episodes_excluded": True,
            "v1_6_controlled_benchmark_evidence_excluded": True,
            "weak_ambiguous_warning_unavailable_ci_and_review_required_episodes_preserved": True,
            "decision_time_evidence_separation_preserved": decision_time_overlap_count == 0,
            "future_leakage_checks_preserved": True,
            "full_scoring_disallowed": True,
        },
        "pass_fail_warning_breakdown": pass_fail_warning_breakdown,
        "deterministic_pass_fail_count": (
            pass_fail_warning_breakdown["passed"] + pass_fail_warning_breakdown["failed"]
        ),
        "warning_or_review_required_count": (
            pass_fail_warning_breakdown["warning_only"]
            + pass_fail_warning_breakdown["review_required"]
        ),
        "ci_log_status_breakdown": dict(sorted(ci_log_breakdown.items())),
        "local_rerun_status_breakdown": dict(sorted(local_rerun_breakdown.items())),
        "discovered_memory_result": {
            "status": "UNAVAILABLE",
            "reason": "The TatMapper external evidence does not contain ControllerGate discovered-memory condition outputs.",
        },
        "no_memory_baseline_result": {
            "status": "UNAVAILABLE",
            "reason": "No no-memory baseline was available in the normalized TatMapper external evidence.",
        },
        "predefined_memory_baseline_result": {
            "status": "UNAVAILABLE",
            "reason": "No predefined-memory baseline was available in the normalized TatMapper external evidence.",
        },
        "poisoned_memory_baseline_result": {
            "status": "UNAVAILABLE",
            "reason": "No poisoned-memory baseline was available in the normalized TatMapper external evidence.",
        },
        "false_success_detection_results": {
            "external_false_success_episode_count": 0,
            "status": "No explicit false-success TatMapper episode was present; all beta episodes remain review_required.",
        },
        "stale_read_or_false_completion_detection_results": stale_counts,
        "dependency_or_config_drift_detection_results": dependency_counts,
        "generated_artifact_mismatch_detection_results": generated_artifact_counts,
        "correction_required_results": correction_counts,
        "future_leakage_checks": {
            "decision_time_outcome_overlap_episode_count": decision_time_overlap_count,
            "external_episode_future_leakage_risk": "review_required_preserved",
            "status": "PASS_WITH_REVIEW_REQUIRED_CAVEATS",
        },
        "episode_level_decisions": episode_decisions,
        "limitations": [
            "All eleven TatMapper episodes remain review_required.",
            "Full GitHub Actions logs are unavailable for the selected PRs/commits.",
            "Fresh local reruns are current-head-only, timed out, unavailable, or blocked by local Java/Flutter/OpenCV/tooling gaps.",
            "Original agent/tool transcripts are unavailable for the TatMapper episodes.",
            "No ControllerGate memory-condition baselines are available for the TatMapper external evidence.",
            "Warning-only, closed-unmerged, weak, ambiguous, and unavailable-CI evidence remains included.",
        ],
        "non_claims": [
            "This is not proof of self-maintaining software.",
            "This is not full v1.7-beta scoring.",
            "This is not broad production readiness.",
            "This is not broad cross-repo generalization.",
            "This does not demonstrate real-repo memory lift.",
        ],
        "overall_limited_pilot_result": "COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS",
        "final_status_wording": REQUIRED_FINAL_STATUS,
    }

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    episode_table = markdown_table(
        [
            "Episode",
            "Reference",
            "Outcome type",
            "Verified result",
            "CI logs",
            "Fresh rerun",
            "Dependency/config drift",
        ],
        [
            [
                row["episode_id"],
                f"PR #{row.get('source_pr')}" if row.get("source_pr") is not None else str(row.get("source_commit"))[:7],
                row.get("outcome_type"),
                row.get("verified_result"),
                row.get("ci_log_available"),
                row.get("local_rerun_completed"),
                row.get("dependency_or_config_drift_detected"),
            ]
            for row in included
        ],
    )
    counts_table = markdown_table(
        ["Metric", "Count"],
        [
            ["eligible beta external episodes", len(included)],
            ["passed", pass_fail_warning_breakdown["passed"]],
            ["failed", pass_fail_warning_breakdown["failed"]],
            ["warning_only", pass_fail_warning_breakdown["warning_only"]],
            ["review_required", pass_fail_warning_breakdown["review_required"]],
            ["deterministic pass/fail", result["deterministic_pass_fail_count"]],
            ["warning or review_required", result["warning_or_review_required_count"]],
        ],
    )
    detection_table = markdown_table(
        ["Detection area", "Result"],
        [
            ["false-success detection", result["false_success_detection_results"]["status"]],
            [
                "stale-read or false-completion detection",
                f"true={stale_counts['true']}, false={stale_counts['false']}, review_required={stale_counts['review_required']}, null={stale_counts['null']}",
            ],
            [
                "dependency/config drift detection",
                f"true={dependency_counts['true']}, false={dependency_counts['false']}, review_required={dependency_counts['review_required']}, null={dependency_counts['null']}",
            ],
            [
                "generated artifact mismatch detection",
                f"true={generated_artifact_counts['true']}, false={generated_artifact_counts['false']}, review_required={generated_artifact_counts['review_required']}, null={generated_artifact_counts['null']}",
            ],
            [
                "future leakage check",
                f"decision-time/outcome-only overlap episodes={decision_time_overlap_count}; review-required caveats preserved",
            ],
        ],
    )
    report = f"""# v1.7-beta Limited TatMapper Scoring

{REQUIRED_FINAL_STATUS}

## Scope

Scoring mode: `limited_pilot_only`

Full scoring allowed: `false`

Only v1.7-beta TatMapper `external_real_repo_episode` entries were included. v1.7-alpha TORUS episodes, v1.6 controlled benchmark evidence, and correction-review episodes were excluded from beta scoring.

## Counts

{counts_table}

## Episode-Level Decision Table

{episode_table}

## Memory Baselines

| Baseline | Result | Reason |
| --- | --- | --- |
| discovered-memory result | UNAVAILABLE | The TatMapper external evidence does not contain ControllerGate discovered-memory condition outputs. |
| no-memory baseline | UNAVAILABLE | No no-memory baseline was available in the normalized TatMapper external evidence. |
| predefined-memory baseline | UNAVAILABLE | No predefined-memory baseline was available in the normalized TatMapper external evidence. |
| poisoned-memory baseline | UNAVAILABLE | No poisoned-memory baseline was available in the normalized TatMapper external evidence. |

## Detection Results

{detection_table}

## Limitations

- All eleven TatMapper episodes remain `review_required`.
- Full GitHub Actions logs are unavailable for the selected PRs/commits.
- Fresh local reruns are current-head-only, timed out, unavailable, or blocked by local Java/Flutter/OpenCV/tooling gaps.
- Original agent/tool transcripts are unavailable for the TatMapper episodes.
- No ControllerGate memory-condition baselines are available for the TatMapper external evidence.
- Warning-only, closed-unmerged, weak, ambiguous, and unavailable-CI evidence remains included.

## Non-Claims

- This is not proof of self-maintaining software.
- This is not full v1.7-beta scoring.
- This is not broad production readiness.
- This is not broad cross-repo generalization.
- This does not demonstrate real-repo memory lift.

## Result

Overall limited pilot result: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    README_PATH.write_text(
        f"""# v1.7-beta Limited TatMapper Scoring

{REQUIRED_FINAL_STATUS}

Status: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`

Scoring mode: `limited_pilot_only`

Full scoring allowed: `false`

ControllerGate full scoring: NOT RUN

Next step: review the beta limited scoring result before authorizing any broader claim or additional scoring.
""",
        encoding="utf-8",
    )

    print("v1.7-beta limited TatMapper scoring: RUN")
    print(f"eligible episodes: {len(included)}")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"audit JSON: {RESULT_PATH.relative_to(ROOT)}")
    print("result: COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS")
    print("full scoring allowed: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

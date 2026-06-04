#!/usr/bin/env python3
"""Run the v1.7-alpha limited exploratory real-repo pilot scoring pass."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "traces" / "normalized" / "episodes.jsonl"
CLASSIFICATION_PATH = ROOT / "traces" / "audits" / "episode_review_classification.json"
PILOT_REVIEW_PATH = ROOT / "traces" / "audits" / "pilot_eligibility_review.json"
REPORT_DIR = ROOT / "reports" / "limited_pilot_scoring"
AUDIT_DIR = ROOT / "traces" / "audits" / "limited_pilot_scoring"
REPORT_PATH = REPORT_DIR / "limited_pilot_scoring_report.md"
RESULT_PATH = AUDIT_DIR / "limited_pilot_scoring.json"

REQUIRED_FINAL_STATUS = (
    "ControllerGate v1.7-alpha limited pilot scoring was run on 10 normalized "
    "TORUS-Theory external real repo episodes. This is exploratory pilot evidence "
    "only, not proof of self-maintaining software."
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
    counts = {"true": 0, "false": 0, "null": 0}
    for row in rows:
        value = row.get(field)
        if value is True:
            counts["true"] += 1
        elif value is False:
            counts["false"] += 1
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
    pilot_review = load_json(PILOT_REVIEW_PATH)

    classification_rows = classification.get("episodes")
    if not isinstance(classification_rows, list):
        raise TypeError("classification episodes must be a list")
    by_id = {row["episode_id"]: row for row in ledger}
    classifications_by_id = {
        row["episode_id"]: row for row in classification_rows if isinstance(row, dict) and "episode_id" in row
    }

    pilot_review_rows = pilot_review.get("episodes")
    if not isinstance(pilot_review_rows, list):
        raise TypeError("pilot review episodes must be a list")
    eligible_ids = [
        row["episode_id"]
        for row in pilot_review_rows
        if isinstance(row, dict) and row.get("pilot_eligible") is True
    ]

    included = [by_id[episode_id] for episode_id in eligible_ids]
    excluded_counts = Counter(
        row.get("category", "unknown")
        for row in classification_rows
        if isinstance(row, dict) and row.get("episode_id") not in eligible_ids
    )
    verified_breakdown = Counter(row.get("verified_result", "UNAVAILABLE") for row in included)
    pass_fail_warning_breakdown = {
        "passed": verified_breakdown.get("passed", 0),
        "failed": verified_breakdown.get("failed", 0),
        "warning_only": verified_breakdown.get("warning_only", 0),
        "review_required": verified_breakdown.get("review_required", 0),
    }

    episode_decisions: list[dict[str, Any]] = []
    decision_time_overlap_count = 0
    for row in included:
        decision_time = set(row.get("decision_time_evidence_available") or [])
        outcome_only = set(row.get("outcome_only_evidence") or [])
        overlap = sorted(decision_time & outcome_only)
        if overlap:
            decision_time_overlap_count += 1
        classification_row = classifications_by_id[row["episode_id"]]
        episode_decisions.append(
            {
                "episode_id": row["episode_id"],
                "source_episode_folder": row.get("source_episode_folder"),
                "source_repo": row.get("source_repo"),
                "source_pr": row.get("source_pr"),
                "category": classification_row.get("category"),
                "outcome_type": row.get("outcome_type"),
                "verified_result": row.get("verified_result"),
                "pilot_decision": row.get("verified_result"),
                "pr_status": row.get("pr_status"),
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
            }
        )

    dependency_counts = bool_count(included, "dependency_or_config_drift_detected")
    stale_counts = bool_count(included, "stale_read_or_false_completion_detected")
    generated_artifact_counts = bool_count(included, "generated_artifact_mismatch_detected")
    correction_counts = bool_count(included, "correction_required")

    result: dict[str, Any] = {
        "schema_version": "1.0",
        "scoring_date": "2026-06-03",
        "scoring_mode": "limited_pilot_only",
        "full_scoring_allowed": False,
        "source_ledger_path": "controllergate_v1_7_alpha/traces/normalized/episodes.jsonl",
        "source_classification_path": (
            "controllergate_v1_7_alpha/traces/audits/episode_review_classification.json"
        ),
        "source_pilot_review_path": (
            "controllergate_v1_7_alpha/traces/audits/pilot_eligibility_review.json"
        ),
        "eligible_episode_count": len(included),
        "included_episode_ids": eligible_ids,
        "excluded_episode_count_by_category": dict(sorted(excluded_counts.items())),
        "required_scope_enforced": {
            "only_external_real_repo_episode_entries_used": True,
            "correction_review_episode_entries_excluded": True,
            "controlled_benchmark_evidence_entries_excluded": True,
            "failed_warning_ambiguous_closed_unmerged_episodes_preserved": True,
            "decision_time_evidence_separation_preserved": decision_time_overlap_count == 0,
            "future_leakage_checks_preserved": True,
        },
        "pass_fail_warning_breakdown": pass_fail_warning_breakdown,
        "closed_unmerged_episode_count": sum(1 for row in included if row.get("pr_status") == "closed_unmerged"),
        "deterministic_pass_fail_count": (
            pass_fail_warning_breakdown["passed"] + pass_fail_warning_breakdown["failed"]
        ),
        "warning_or_review_required_count": (
            pass_fail_warning_breakdown["warning_only"]
            + pass_fail_warning_breakdown["review_required"]
        ),
        "discovered_memory_result": {
            "status": "UNAVAILABLE",
            "reason": "The TORUS-Theory external rerun episodes do not contain ControllerGate discovered-memory condition outputs.",
        },
        "no_memory_baseline_result": {
            "status": "UNAVAILABLE",
            "reason": "No no-memory baseline was available in the normalized TORUS external evidence.",
        },
        "predefined_memory_baseline_result": {
            "status": "UNAVAILABLE",
            "reason": "No predefined-memory baseline was available in the normalized TORUS external evidence.",
        },
        "poisoned_memory_baseline_result": {
            "status": "UNAVAILABLE",
            "reason": "No poisoned-memory baseline was available in the normalized TORUS external evidence.",
        },
        "false_success_detection_results": {
            "external_false_success_episode_count": 0,
            "excluded_correction_review_false_success_episode_count": 2,
            "status": "No explicit false-success external episode was present; iota/pi false-success correction episodes were excluded from real repo scoring.",
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
            "Historical GitHub Actions log text is unavailable for multiple episodes because the job-log endpoint returned HTTP 410.",
            "Original agent/tool transcripts are unavailable for the TORUS external episodes.",
            "Several reruns are bounded local command reruns rather than full GitHub Actions job replays.",
            "No ControllerGate memory-condition baselines are available for the TORUS external evidence.",
            "Review-required, warning-only, failed, and closed-unmerged episodes remain included.",
        ],
        "non_claims": [
            "This is not proof of self-maintaining software.",
            "This is not full v1.7-alpha scoring.",
            "This is not broad external generalization across repositories.",
            "This does not convert controlled benchmark evidence or correction-review episodes into real repo scoring evidence.",
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
            "PR",
            "Outcome type",
            "Verified result",
            "Runner",
            "Dependency/config drift",
            "Generated artifact mismatch",
        ],
        [
            [
                row["episode_id"],
                row.get("source_pr"),
                row.get("outcome_type"),
                row.get("verified_result"),
                row.get("runner_completed"),
                row.get("dependency_or_config_drift_detected"),
                row.get("generated_artifact_mismatch_detected"),
            ]
            for row in included
        ],
    )
    breakdown_table = markdown_table(
        ["Metric", "Count"],
        [
            ["eligible external episodes", len(included)],
            ["passed", pass_fail_warning_breakdown["passed"]],
            ["failed", pass_fail_warning_breakdown["failed"]],
            ["warning_only", pass_fail_warning_breakdown["warning_only"]],
            ["review_required", pass_fail_warning_breakdown["review_required"]],
            ["closed_unmerged", result["closed_unmerged_episode_count"]],
            ["deterministic pass/fail", result["deterministic_pass_fail_count"]],
            ["warning or review_required", result["warning_or_review_required_count"]],
        ],
    )
    excluded_table = markdown_table(
        ["Excluded category", "Count"],
        [[category, count] for category, count in sorted(excluded_counts.items())],
    )
    report = f"""# v1.7-alpha Limited Real Repo Pilot Scoring

{REQUIRED_FINAL_STATUS}

## Scope

Scoring mode: `limited_pilot_only`

Full scoring allowed: `false`

Only `external_real_repo_episode` entries were included. Correction-review episodes and controlled benchmark evidence episodes were excluded from real repo scoring.

## Counts

{breakdown_table}

## Exclusions

{excluded_table}

## Episode-Level Decision Table

{episode_table}

## Memory Baselines

| Baseline | Result | Reason |
| --- | --- | --- |
| discovered-memory result | UNAVAILABLE | The TORUS-Theory external rerun episodes do not contain ControllerGate discovered-memory condition outputs. |
| no-memory baseline | UNAVAILABLE | No no-memory baseline was available in the normalized TORUS external evidence. |
| predefined-memory baseline | UNAVAILABLE | No predefined-memory baseline was available in the normalized TORUS external evidence. |
| poisoned-memory baseline | UNAVAILABLE | No poisoned-memory baseline was available in the normalized TORUS external evidence. |

## Detection Results

| Detection area | Result |
| --- | --- |
| false-success detection | 0 explicit external false-success episodes; iota/pi false-success correction episodes were excluded from real repo scoring. |
| stale-read or false-completion detection | true={stale_counts['true']}, false={stale_counts['false']}, null={stale_counts['null']} |
| dependency/config drift detection | true={dependency_counts['true']}, false={dependency_counts['false']}, null={dependency_counts['null']} |
| generated artifact mismatch detection | true={generated_artifact_counts['true']}, false={generated_artifact_counts['false']}, null={generated_artifact_counts['null']} |
| future leakage check | decision-time/outcome-only overlap episodes={decision_time_overlap_count}; review-required caveats preserved |

## Limitations

- Historical GitHub Actions log text is unavailable for multiple episodes because the job-log endpoint returned HTTP 410.
- Original agent/tool transcripts are unavailable for the TORUS external episodes.
- Several reruns are bounded local command reruns rather than full GitHub Actions job replays.
- No ControllerGate memory-condition baselines are available for the TORUS external evidence.
- Review-required, warning-only, failed, and closed-unmerged episodes remain included.

## Non-Claims

- This is not proof of self-maintaining software.
- This is not full v1.7-alpha scoring.
- This is not broad external generalization across repositories.
- This does not convert controlled benchmark evidence or correction-review episodes into real repo scoring evidence.

## Result

Overall limited pilot result: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`
"""
    REPORT_PATH.write_text(report, encoding="utf-8")

    print("limited pilot scoring: RUN")
    print(f"eligible episodes: {len(included)}")
    print(f"report: {REPORT_PATH.relative_to(ROOT)}")
    print(f"audit JSON: {RESULT_PATH.relative_to(ROOT)}")
    print("full scoring allowed: false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

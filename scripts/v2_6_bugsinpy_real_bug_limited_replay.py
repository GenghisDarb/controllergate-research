#!/usr/bin/env python3
"""Generate v2.6 BugsInPy real-bug limited replay campaign artifacts.

This campaign refuses to execute memory-vs-no-memory scoring unless the v2.5
artifact ingestion has at least three target-failure-matched BugsInPy
candidates. Dependency/import/runtime failures are not counted as target bug
replay.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_6_bugsinpy_real_bug_limited_replay"
V25_SUMMARY = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner" / "parsed_runtime_artifact_summary.json"
V25_POOL = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner" / "promoted_real_bug_candidate_pool_from_artifacts.json"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest(directory: Path) -> None:
    paths = sorted(
        [path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [
        f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}"
        for path in paths
    ]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def update_shareable_summary(aggregate: str, promoted_count: int, blocked_count: int) -> None:
    section = f"""## v2.6 BugsInPy Real-Bug Limited Replay Execution

BugsInPy real-bug replay is stronger than QuixBugs and controlled fixture evidence, but target-failure matching is now a hard gate.

- Candidates reviewed: `black:2`, `youtube-dl:1`, `black:8`.
- Target-failure-matched promoted candidates: {promoted_count}.
- Blocked by target-failure guard: {blocked_count}.
- Executed episodes: 0.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Decision-time/outcome overlap count: 0.
- Corruption count: 0.
- Aggregate result: `{aggregate}`.

The two Black candidates were not accepted as target BugsInPy replay evidence because the ingested logs show dependency/import failures rather than the expected target BugsInPy failure. `youtube-dl:1` remains promoted and can support a future small real-bug probe.

Gold/fixed patches are outcome-only and excluded from decision-time inputs. Limited BugsInPy memory lift is still not self-maintaining software. Full scoring remains disallowed. Blocked runtime or target-failure mismatch is not negative capability evidence.
"""
    marker = "## v2.6 BugsInPy Real-Bug Limited Replay Execution"
    if SHAREABLE_SUMMARY.exists():
        text = SHAREABLE_SUMMARY.read_text(encoding="utf-8")
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n\n" + section
        else:
            text = text.rstrip() + "\n\n" + section
    else:
        text = section
    write_text(SHAREABLE_SUMMARY, text)


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    parsed = load_json(V25_SUMMARY)
    pool = load_json(V25_POOL)
    records = parsed.get("records", []) if isinstance(parsed.get("records"), list) else []
    promoted = [
        record
        for record in records
        if record.get("promotion_status") == "promoted_ready_for_v2_5_bugsinpy_real_bug"
        and record.get("target_failure_matched") is True
    ]
    blocked = [record for record in records if record not in promoted]
    aggregate = "insufficient_episode_count_for_bugsinpy_real_bug_memory_lift"
    execution_allowed = len(promoted) >= 3
    write_json(
        OUTPUT_DIR / "campaign_plan.json",
        {
            "campaign_id": "v2_6_bugsinpy_real_bug_limited_replay",
            "purpose": "Run limited replay scoring on promoted BugsInPy real-bug candidates only after target-failure matching.",
            "candidate_ids": ["black:2", "youtube-dl:1", "black:8"],
            "episode_label": "bugsinpy_real_bug_limited_replay_episode",
            "target_failure_matching_guard_required": True,
            "minimum_scoreable_episode_count_for_memory_lift": 3,
            "execution_allowed": execution_allowed,
            "execution_status": "not_executed_insufficient_target_matched_candidates"
            if not execution_allowed
            else "ready_for_limited_replay_execution",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "broad_organic_external_memory_lift_demonstrated": False,
            "gold_fixed_patches_decision_time_allowed": False,
        },
    )
    integrity_records = []
    for record in records:
        integrity_records.append(
            {
                "candidate": f"{record.get('project')}:{record.get('bug_id')}",
                "artifact_reported_promotion_status": record.get("artifact_reported_promotion_status"),
                "final_promotion_status": record.get("promotion_status"),
                "target_failure_matched": record.get("target_failure_matched"),
                "dependency_or_import_failure_detected": record.get("dependency_or_import_failure_detected"),
                "failure_signature": record.get("failure_signature"),
                "target_failure_match_reason": record.get("target_failure_match_reason"),
                "artifact_directory": record.get("artifact_directory"),
            }
        )
    write_json(
        OUTPUT_DIR / "candidate_source_integrity_check.json",
        {
            "source": "v2.5 parsed BugsInPy runtime artifacts",
            "target_failure_matching_guard_exists": True,
            "target_failure_matching_guard_enforced": True,
            "dependency_import_or_runtime_failure_counts_as_target_replay": False,
            "candidate_count": len(records),
            "target_matched_promoted_count": len(promoted),
            "blocked_target_mismatch_count": len(blocked),
            "records": integrity_records,
            "gold_fixed_patches_used_at_decision_time": False,
        },
    )
    write_json(
        OUTPUT_DIR / "campaign_results.json",
        {
            "campaign_id": "v2_6_bugsinpy_real_bug_limited_replay",
            "candidate_count": len(records),
            "promoted_target_matched_candidate_count": len(promoted),
            "blocked_target_mismatch_candidate_count": len(blocked),
            "executed_episode_count": 0,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "negative_episode_count": 0,
            "inconclusive_episode_count": 0,
            "blocked_episode_count": len(blocked),
            "decision_time_outcome_overlap_count": 0,
            "corruption_count": 0,
            "aggregate_result": aggregate,
            "handoff_recommendation": "v2_5_small_bugsinpy_probe_execution",
            "repair_scoring_run": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "broad_organic_external_memory_lift_demonstrated": False,
        },
    )
    write_json(
        OUTPUT_DIR / "aggregate_bugsinpy_real_bug_memory_lift_assessment.json",
        {
            "aggregate_result": aggregate,
            "limited_bugsinpy_real_bug_memory_lift_criteria_met": False,
            "scoreable_episode_count": 0,
            "positive_memory_episode_count": 0,
            "target_matched_promoted_candidate_count": len(promoted),
            "minimum_required_scoreable_episodes": 3,
            "gold_fixed_patches_excluded_from_decision_time_inputs": True,
            "decision_time_outcome_overlap_count": 0,
            "corruption_count": 0,
            "self_maintaining_software_demonstrated": False,
            "broad_organic_external_memory_lift_demonstrated": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "interpretation": "v2.6 limited replay execution did not run because target-failure matching left fewer than three BugsInPy real-bug candidates.",
        },
    )
    summary = f"""# v2.6 BugsInPy Real-Bug Limited Replay Execution

Result: `{aggregate}`.

## Candidate Source Integrity

- `black:2`: blocked after target-failure guard; log showed dependency/import failure rather than accepted target BugsInPy failure.
- `youtube-dl:1`: promoted after target-failure guard; log matched `BUGSINPY_REPRODUCED_FAILURE: youtube-dl:1`.
- `black:8`: blocked after target-failure guard; log showed dependency/import failure rather than accepted target BugsInPy failure.

## Execution

No limited replay scoring episodes were executed. The three-episode BugsInPy memory-lift gate cannot be entered with only one target-matched candidate.

Gold/fixed patches are outcome-only and excluded from decision-time inputs. Full scoring remains disallowed. Self-maintaining software remains undemonstrated. BugsInPy success or blockage does not prove arbitrary public repo maintenance.

Blocked runtime or target-failure mismatch is not negative capability evidence.
"""
    write_text(OUTPUT_DIR / "campaign_summary.md", summary)
    update_shareable_summary(aggregate, len(promoted), len(blocked))
    write_manifest(OUTPUT_DIR)
    print("v2.6 BugsInPy real-bug limited replay artifacts generated")
    print(f"target-matched promoted candidates: {len(promoted)}")
    print(f"aggregate: {aggregate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

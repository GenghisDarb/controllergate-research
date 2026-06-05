#!/usr/bin/env python3
"""Parse v2.5 BugsInPy GitHub Actions runtime probe artifacts.

Usage:
  python scripts/v2_5_parse_bugsinpy_runtime_artifacts.py <artifact_dir>

The parser does not execute repairs or scoring. It summarizes which BugsInPy
candidate smoke tests promoted to replay-ready status based on fresh runtime
artifact logs.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_5_bugsinpy_runtime_runner"
SHAREABLE_SUMMARY = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
CANDIDATE_DIRS = ["black_2", "youtube_dl_1", "black_8"]
TARGET_FAILURE_RULES = {
    "black_2": {
        "project": "black",
        "bug_id": "2",
        "required_any": [
            "FAIL: test_fmtonoff4",
            "AssertionError",
            "BlackTestCase.test_fmtonoff4",
        ],
        "block_if_any": [
            "ModuleNotFoundError",
            "ImportError: Failed to import test module",
            "No module named",
        ],
        "expected_failure_signature": "BUGSINPY_REPRODUCED_FAILURE: black:2",
    },
    "youtube_dl_1": {
        "project": "youtube-dl",
        "bug_id": "1",
        "required_any": [
            "FAIL: test_match_str",
            "AssertionError: True is not false",
            "TestUtil.test_match_str",
        ],
        "block_if_any": [
            "ModuleNotFoundError",
            "ImportError: Failed to import test module",
            "No module named",
        ],
        "expected_failure_signature": "BUGSINPY_REPRODUCED_FAILURE: youtube-dl:1",
    },
    "black_8": {
        "project": "black",
        "bug_id": "8",
        "required_any": [
            "FAIL: test_comments7",
            "AssertionError",
            "BlackTestCase.test_comments7",
        ],
        "block_if_any": [
            "ModuleNotFoundError",
            "ImportError: Failed to import test module",
            "No module named",
        ],
        "expected_failure_signature": "BUGSINPY_REPRODUCED_FAILURE: black:8",
    },
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


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
    (directory / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def update_shareable_summary(promoted_count: int, recommendation: str, records: list[dict[str, Any]]) -> None:
    classifications = "\n".join(
        f"- `{record.get('project')}:{record.get('bug_id')}`: `{record.get('promotion_status')}`"
        for record in records
    )
    section = f"""## v2.5 BugsInPy Runtime Artifact Ingestion Result

The v2.5 GitHub Actions BugsInPy runtime probe artifact was ingested.

- Candidate count: 3.
- Promoted real-bug candidates: {promoted_count}.
- Handoff recommendation: `{recommendation}`.
- Repair scoring: not run.
- Full scoring: disallowed.
- Self-maintaining software: not demonstrated.
- Broad organic external memory lift: not demonstrated.

Candidate classifications:

{classifications}

Fresh checkout/compile/test logs now exist in the ingested GitHub Actions artifact. Gold/fixed patches remain outcome-only and were not used as decision-time inputs. If three candidates promote, the next gated step is real BugsInPy limited replay execution, not a self-maintaining-software claim.

Target-failure matching is enforced at parser/audit time. A dependency/import/runtime failure is not enough to promote a BugsInPy candidate unless the expected BugsInPy target failure is also matched.
"""
    marker = "## v2.5 BugsInPy Runtime Artifact Ingestion Result"
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
    if len(sys.argv) != 2:
        print("usage: v2_5_parse_bugsinpy_runtime_artifacts.py <artifact_dir>")
        return 2
    artifact_dir = Path(sys.argv[1]).resolve()
    records = []
    errors = []
    for dirname in CANDIDATE_DIRS:
        candidate_dir = artifact_dir / dirname
        feasibility = load_json(candidate_dir / "replay_feasibility_result.json")
        metadata = load_json(candidate_dir / "candidate_metadata.json")
        rule = TARGET_FAILURE_RULES[dirname]
        test_log = (candidate_dir / "test_log_raw.txt").read_text(encoding="utf-8", errors="replace") if (candidate_dir / "test_log_raw.txt").exists() else ""
        required_matched = any(pattern in test_log for pattern in rule["required_any"])
        blocked_marker_matched = any(pattern in test_log for pattern in rule["block_if_any"])
        target_failure_matched = required_matched and not blocked_marker_matched
        if target_failure_matched:
            promotion_status = "promoted_ready_for_v2_5_bugsinpy_real_bug"
            failure_signature = rule["expected_failure_signature"]
            target_failure_match_reason = "expected BugsInPy target failure marker matched and no dependency/import blocker marker was present"
        else:
            promotion_status = "blocked_bugsinpy_test_not_reproducible"
            if blocked_marker_matched:
                target_failure_match_reason = "dependency/import/runtime failure marker was present, so this is not accepted as target BugsInPy failure replay"
            elif not required_matched:
                target_failure_match_reason = "expected BugsInPy target failure marker was not found"
            else:
                target_failure_match_reason = "target failure matching was inconclusive"
            failure_signature = f"TARGET_FAILURE_NOT_MATCHED: {rule['project']}:{rule['bug_id']}"
        if not candidate_dir.exists():
            errors.append(f"missing candidate directory: {dirname}")
        records.append(
            {
                "candidate_dir": dirname,
                "project": metadata.get("project") or rule["project"],
                "bug_id": metadata.get("bug_id") or rule["bug_id"],
                "artifact_reported_promotion_status": feasibility.get("promotion_status", "still_needs_manual_review"),
                "promotion_status": promotion_status,
                "runtime_replay_confirmed": target_failure_matched,
                "failing_test_reproduced": target_failure_matched,
                "target_failure_matched": target_failure_matched,
                "dependency_or_import_failure_detected": blocked_marker_matched,
                "target_failure_match_reason": target_failure_match_reason,
                "failure_signature": failure_signature,
                "artifact_directory": str(candidate_dir),
            }
        )
    promoted = [record for record in records if str(record["promotion_status"]).startswith("promoted_ready_for_v2_5")]
    if len(promoted) >= 3:
        recommendation = "v2_5_bugsinpy_real_bug_limited_replay_execution"
    elif len(promoted) >= 1:
        recommendation = "v2_5_small_bugsinpy_probe_execution"
    else:
        recommendation = "runner_environment_fix_required"
    summary = {
        "artifact_dir": str(artifact_dir),
        "candidate_count": len(records),
        "promoted_candidate_count": len(promoted),
        "records": records,
        "handoff_recommendation": recommendation,
        "parser_errors": errors,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
        "broad_organic_external_memory_lift_demonstrated": False,
    }
    ingestion_result = {
        "artifact_dir": str(artifact_dir),
        "artifact_ingested": True,
        "candidate_count": len(records),
        "promoted_candidate_count": len(promoted),
        "classification_by_candidate": {
            f"{record.get('project')}:{record.get('bug_id')}": record.get("promotion_status")
            for record in records
        },
        "handoff_recommendation": recommendation,
        "repair_scoring_run": False,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
        "broad_organic_external_memory_lift_demonstrated": False,
        "gold_fixed_patch_used_at_decision_time": False,
    }
    write_json(OUTPUT_DIR / "parsed_runtime_artifact_summary.json", summary)
    write_json(OUTPUT_DIR / "runtime_artifact_ingestion_result.json", ingestion_result)
    write_json(
        OUTPUT_DIR / "promoted_real_bug_candidate_pool_from_artifacts.json",
        {"count": len(promoted), "records": promoted, "handoff_recommendation": recommendation},
    )
    write_json(
        OUTPUT_DIR / "runner_status.json",
        {
            "runner_status": "artifact_ingested_promoted_candidates"
            if promoted
            else "artifact_ingested_no_promoted_candidates",
            "artifact_ingested": True,
            "artifact_dir": str(artifact_dir),
            "promoted_candidate_count": len(promoted),
            "recommended_handoff": recommendation,
            "repair_scoring_run": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_demonstrated": False,
            "broad_organic_external_memory_lift_demonstrated": False,
            "v2_4_result_preserved": "blocked_real_external_bug_candidate_acquisition_failure",
            "v2_4b_result_preserved": "blocked_real_bug_runtime_unavailable",
        },
    )
    update_shareable_summary(len(promoted), recommendation, records)
    write_manifest(OUTPUT_DIR)
    print(f"parsed v2.5 artifact dir: {artifact_dir}")
    print(f"promoted candidates: {len(promoted)}")
    print(f"handoff recommendation: {recommendation}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

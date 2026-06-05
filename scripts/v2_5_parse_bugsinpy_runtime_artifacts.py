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
CANDIDATE_DIRS = ["black_2", "youtube_dl_1", "black_8"]


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
        if not candidate_dir.exists():
            errors.append(f"missing candidate directory: {dirname}")
        records.append(
            {
                "candidate_dir": dirname,
                "project": metadata.get("project"),
                "bug_id": metadata.get("bug_id"),
                "promotion_status": feasibility.get("promotion_status", "still_needs_manual_review"),
                "runtime_replay_confirmed": feasibility.get("runtime_replay_confirmed", False),
                "failing_test_reproduced": feasibility.get("failing_test_reproduced", False),
                "failure_signature": (candidate_dir / "failure_signature.txt").read_text(encoding="utf-8").strip()
                if (candidate_dir / "failure_signature.txt").exists()
                else None,
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
    write_json(OUTPUT_DIR / "parsed_runtime_artifact_summary.json", summary)
    write_json(
        OUTPUT_DIR / "promoted_real_bug_candidate_pool_from_artifacts.json",
        {"count": len(promoted), "records": promoted, "handoff_recommendation": recommendation},
    )
    write_manifest(OUTPUT_DIR)
    print(f"parsed v2.5 artifact dir: {artifact_dir}")
    print(f"promoted candidates: {len(promoted)}")
    print(f"handoff recommendation: {recommendation}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

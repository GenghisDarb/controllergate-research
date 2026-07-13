from __future__ import annotations

import hashlib
from pathlib import Path
import re
from typing import Any

from controllergate.core.evidence import hash_record


FORBIDDEN = re.compile(r"(?i)(?:diff --git|suggested fix|replace the function|fixed by|resolved by|gold patch|future test|pull request)")


def assess_issue_reproducer(
    *, candidate_id: str, sanitized_text: str, platform: str, runtime: str | None, source_sha: str, author: str = "ControllerGate"
) -> dict[str, Any]:
    complete = all(re.search(pattern, sanitized_text, re.I) for pattern in (r"(?:command|usage:|python\s+-m|poetry\s+init)", r"(?:observed|error|actual|failed)", r"(?:expected|should)"))
    contaminated = bool(FORBIDDEN.search(sanitized_text))
    record = {
        "candidate_id": candidate_id,
        "lane": "ISSUE_DERIVED_REPRODUCER_LANE",
        "status": "ELIGIBLE_FOR_CONSTRUCTION" if complete and not contaminated else "BLOCK",
        "issue_body_lines_used": [line for line in sanitized_text.splitlines() if line.strip()][:120],
        "files_created": [],
        "commands_used": [],
        "expected_behavior_present": bool(re.search(r"(?:expected|should)", sanitized_text, re.I)),
        "observed_behavior_present": bool(re.search(r"(?:observed|error|actual|failed)", sanitized_text, re.I)),
        "platform": platform,
        "runtime": runtime,
        "source_commit_sha": source_sha,
        "author": author,
        "independent_verifier": "controllergate.issue_reproducer_lane.v1",
        "reproducer_outside_candidate_source": True,
        "committed_into_candidate_repository": False,
        "solution_contamination": contaminated,
        "duplicate_fresh_execution_count": 0,
        "candidate_failure_admitted": False,
    }
    record["reproducer_hash"] = hashlib.sha256((sanitized_text + source_sha).encode()).hexdigest() if complete else None
    record["record_hash"] = hash_record(record)
    return record


def verify_duplicate_reproducer(signatures: list[str], environment_ids: list[str]) -> dict[str, Any]:
    passed = len(signatures) == len(environment_ids) == 2 and len(set(environment_ids)) == 2 and all(signatures) and len(set(signatures)) == 1
    return {
        "status": "PASS" if passed else "BLOCK",
        "fresh_environment_count": len(set(environment_ids)),
        "signatures": signatures,
        "equivalent_nonempty_behavior_signatures": passed,
        "candidate_failure_admitted": passed,
    }

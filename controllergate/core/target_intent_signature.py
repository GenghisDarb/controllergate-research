from __future__ import annotations

import json
from hashlib import sha256
from typing import Any

ISSUE112_POSITIVE_INDICATORS = [
    "GIT_DIR=.git",
    "darker --check src",
    "Not a git repository",
    "git_get_modified_files",
    "_git_check_output_lines",
    "git diff --name-only --relative HEAD -- .",
]

ISSUE112_NEGATIVE_PRECONDITION_INDICATORS = [
    "config loading failure",
    "TypeError: unsupported operand type(s) for /: 'tuple' and 'str'",
    "ImportError",
    "ModuleNotFoundError",
    "dependency API mismatch",
    "missing dependency",
    "Python version incompatibility",
    "command-line parsing failure",
    "environment setup failure",
    "no git repository available",
]


def stable_hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def issue112_target_signature() -> dict[str, Any]:
    return {
        "status": "PASS",
        "candidate_id": "darker_issue_112_relative_git_dir",
        "source": "manual_redacted_issue_snapshot_no_solution_sections",
        "positive_indicators": ISSUE112_POSITIVE_INDICATORS,
        "negative_precondition_indicators": ISSUE112_NEGATIVE_PRECONDITION_INDICATORS,
        "any_failure_sufficient": False,
        "patch_authorized_without_alignment": False,
    }


def evaluate_target_intent(command: str, output_text: str) -> dict[str, Any]:
    combined = f"{command}\n{output_text}"
    positive_hits = [indicator for indicator in ISSUE112_POSITIVE_INDICATORS if indicator in combined]
    semantic_positive_hits = [
        indicator
        for indicator in ISSUE112_POSITIVE_INDICATORS
        if indicator in output_text and indicator not in {"GIT_DIR=.git", "darker --check src"}
    ]
    negative_hits = [indicator for indicator in ISSUE112_NEGATIVE_PRECONDITION_INDICATORS if indicator in combined]
    command_has_required_shape = "GIT_DIR=.git" in command and "darker" in command and "--check src" in command
    target_aligned = command_has_required_shape and bool(semantic_positive_hits) and not negative_hits
    if target_aligned:
        blocker = None
    elif negative_hits:
        blocker = "target_intent_precondition_failure"
    else:
        blocker = "issue_derived_harness_intent_mismatch"
    return {
        "status": "PASS" if target_aligned else "BLOCK",
        "target_intent_alignment": target_aligned,
        "command_has_required_shape": command_has_required_shape,
        "positive_indicator_hits": positive_hits,
        "semantic_positive_indicator_hits": semantic_positive_hits,
        "negative_precondition_hits": negative_hits,
        "blocker": blocker,
        "expected_signature_hash": stable_hash(issue112_target_signature()),
        "actual_failure_signature_hash": stable_hash({"command": command, "output": output_text}),
        "patch_authorized": target_aligned,
    }

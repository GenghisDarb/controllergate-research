#!/usr/bin/env python3
"""Deterministically classify a failed source patch from direct evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


ALLOWED_CLASSIFICATIONS = {
    "wrong_source_location",
    "incomplete_patch",
    "patch_application_mismatch",
    "target_validation_same_failure",
    "target_validation_new_failure",
    "import_compatibility_mismatch",
    "dependency_or_cofactor_mismatch",
    "fixture_materialization_incomplete",
    "target_expectation_mismatch",
    "source_only_constraint_violation",
    "test_modification_violation",
    "benchmark_expectation_modification_violation",
    "generated_fixture_modification_violation",
    "non_source_modification_violation",
    "degenerate_flatline_noop_patch",
    "evidence_leakage_risk",
    "insufficient_artifact_evidence",
    "unsafe_to_repair",
}


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def normalize_diff_path(raw: str) -> str | None:
    value = raw.strip().split("\t", 1)[0]
    if value == "/dev/null":
        return None
    if value.startswith(('"', "'")):
        try:
            parsed = shlex.split(value)
            value = parsed[0] if parsed else value
        except ValueError:
            pass
    value = value.replace("\\", "/")
    if value.startswith(("a/", "b/")):
        value = value[2:]
    parts = PurePosixPath(value).parts
    if not value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise ValueError(f"absolute or empty diff path: {raw!r}")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"unsafe diff path: {raw!r}")
    return "/".join(parts)


def parse_diff(text: str) -> dict[str, Any]:
    file_pairs: list[tuple[str | None, str | None]] = []
    pending_old: str | None | object = object()
    hunk_count = 0
    added: list[str] = []
    removed: list[str] = []
    malformed: list[str] = []
    unsafe_paths: list[str] = []
    rename_from: str | None = None
    rename_to: str | None = None

    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.startswith("rename from "):
            try:
                rename_from = normalize_diff_path(line[len("rename from ") :])
            except ValueError as exc:
                unsafe_paths.append(str(exc))
        elif line.startswith("rename to "):
            try:
                rename_to = normalize_diff_path(line[len("rename to ") :])
            except ValueError as exc:
                unsafe_paths.append(str(exc))
            if rename_from is not None or rename_to is not None:
                file_pairs.append((rename_from, rename_to))
                rename_from = rename_to = None
        elif line.startswith("--- "):
            try:
                pending_old = normalize_diff_path(line[4:])
            except ValueError as exc:
                unsafe_paths.append(str(exc))
                pending_old = object()
        elif line.startswith("+++ "):
            try:
                new_path = normalize_diff_path(line[4:])
            except ValueError as exc:
                unsafe_paths.append(str(exc))
                new_path = None
            if type(pending_old) is object:
                malformed.append(f"line {line_number}: +++ without a paired --- header")
            else:
                file_pairs.append((pending_old, new_path))
            pending_old = object()
        elif line.startswith("@@"):
            hunk_count += 1
        elif line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])

    if type(pending_old) is not object:
        malformed.append("unpaired --- header")
    touched = sorted({new or old for old, new in file_pairs if (new or old) is not None})

    def semantic_counter(lines: list[str]) -> Counter[str]:
        normalized: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            code = stripped.split("#", 1)[0].strip()
            token = re.sub(r"\s+", "", code)
            if token:
                normalized.append(token)
        return Counter(normalized)

    old_semantic = semantic_counter(removed)
    new_semantic = semantic_counter(added)
    semantic_delta = bool(old_semantic or new_semantic) and old_semantic != new_semantic
    nonempty = bool(text.strip() and hunk_count and touched)
    degenerate = not nonempty or not semantic_delta
    return {
        "file_pairs": file_pairs,
        "touched_files": touched,
        "hunk_count": hunk_count,
        "added_line_count": len(added),
        "removed_line_count": len(removed),
        "malformed": malformed,
        "unsafe_paths": unsafe_paths,
        "patch_nonempty": nonempty,
        "patch_semantic_delta_detected": semantic_delta,
        "degenerate_flatline_detected": degenerate,
    }


def failure_signature(text: str) -> str:
    candidates: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("E   "):
            candidates.append(line[4:].strip())
        elif re.search(r"(?:ImportError|ModuleNotFoundError|AssertionError|TypeError|AttributeError|NameError):", line):
            candidates.append(line)
    return candidates[-1] if candidates else "no_precise_failure_signature_found"


def matches_any(path: str, patterns: list[str]) -> bool:
    lowered = path.lower()
    return any(re.search(pattern, lowered) for pattern in patterns)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch", type=Path, required=True)
    parser.add_argument("--pre-log", type=Path)
    parser.add_argument("--post-log", type=Path, required=True)
    parser.add_argument("--target-command-file", type=Path, required=True)
    parser.add_argument("--application-result", type=Path)
    parser.add_argument("--source-root", default="pysnooper")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    required = [args.patch, args.post_log, args.target_command_file]
    if any(not path.exists() for path in required):
        missing = [str(path) for path in required if not path.exists()]
        raise SystemExit(f"missing classifier inputs: {missing}")

    patch_text = args.patch.read_text(encoding="utf-8", errors="strict")
    pre_text = args.pre_log.read_text(encoding="utf-8", errors="replace") if args.pre_log and args.pre_log.exists() else ""
    post_text = args.post_log.read_text(encoding="utf-8", errors="replace")
    parsed = parse_diff(patch_text)
    application = load_json(args.application_result)
    touched = parsed["touched_files"]
    test_patterns = [r"(^|/)tests?/", r"(^|/)test_[^/]+\.py$", r"_test\.py$"]
    expectation_patterns = [r"(^|/)(expected|expectations?|snapshots?)(/|$)", r"\.golden$"]
    fixture_patterns = [r"(^|/)(fixtures?|testdata|generated)(/|$)"]
    tests_modified = any(matches_any(path, test_patterns) for path in touched)
    expectations_modified = any(matches_any(path, expectation_patterns) for path in touched)
    fixtures_modified = any(matches_any(path, fixture_patterns) for path in touched)
    source_prefix = args.source_root.strip("/\\").replace("\\", "/") + "/"
    non_source = [path for path in touched if not path.startswith(source_prefix)]
    source_only = bool(touched) and not non_source
    pre_signature = failure_signature(pre_text) if pre_text else "not_available"
    post_signature = failure_signature(post_text)
    failure_changed = pre_signature != "not_available" and pre_signature != post_signature
    patch_applied = application.get("applied") is True if application else None

    if parsed["unsafe_paths"] or parsed["malformed"]:
        classification = "unsafe_to_repair"
        blocker = "patch diff contains unsafe paths or malformed structure"
    elif parsed["degenerate_flatline_detected"]:
        classification = "degenerate_flatline_noop_patch"
        blocker = "patch lacks a non-empty demonstrated semantic delta"
    elif patch_applied is False:
        classification = "patch_application_mismatch"
        blocker = "patch application evidence reports failure"
    elif tests_modified:
        classification = "test_modification_violation"
        blocker = "patch modifies test paths"
    elif expectations_modified:
        classification = "benchmark_expectation_modification_violation"
        blocker = "patch modifies benchmark expectation paths"
    elif fixtures_modified:
        classification = "generated_fixture_modification_violation"
        blocker = "patch modifies fixture or generated paths"
    elif not source_only:
        classification = "non_source_modification_violation"
        blocker = "patch contains changes outside the declared source root"
    elif re.search(r"cannot import name ['\"]mini_toolbox['\"] from ['\"]tests['\"]", post_text, re.IGNORECASE):
        classification = "fixture_materialization_incomplete"
        blocker = "target-test collection requires tests/mini_toolbox.py, which is absent from the materialized buggy checkout"
    elif pre_signature == post_signature:
        classification = "target_validation_same_failure"
        blocker = "target validation retained the pre-patch failure signature"
    elif "ImportError" in post_signature or "ModuleNotFoundError" in post_signature:
        classification = "target_validation_new_failure"
        blocker = "patch changed the failure to a new import-time validation failure"
    elif post_signature == "no_precise_failure_signature_found":
        classification = "insufficient_artifact_evidence"
        blocker = "post-patch log lacks a precise deterministic failure signature"
    else:
        classification = "incomplete_patch"
        blocker = "patch changed the target failure but did not produce a passing validation"

    assert classification in ALLOWED_CLASSIFICATIONS
    evidence_paths = [args.patch, args.post_log, args.target_command_file]
    if args.pre_log and args.pre_log.exists():
        evidence_paths.append(args.pre_log)
    if args.application_result and args.application_result.exists():
        evidence_paths.append(args.application_result)
    result = {
        "status": "PASS",
        "patch_applied_cleanly": patch_applied,
        "patch_nonempty": parsed["patch_nonempty"],
        "patch_semantic_delta_detected": parsed["patch_semantic_delta_detected"],
        "degenerate_flatline_detected": parsed["degenerate_flatline_detected"],
        "touched_files": touched,
        "source_only_patch": source_only,
        "tests_modified": tests_modified,
        "benchmark_expectations_modified": expectations_modified,
        "generated_fixtures_modified": fixtures_modified,
        "non_source_files_modified": non_source,
        "pre_failure_signature": pre_signature,
        "post_failure_signature": post_signature,
        "failure_changed_after_patch": failure_changed,
        "deterministic_classification": classification,
        "blocker_reason": blocker,
        "source_only_repair_actionable": classification not in {
            "fixture_materialization_incomplete",
            "source_only_constraint_violation",
            "test_modification_violation",
            "benchmark_expectation_modification_violation",
            "generated_fixture_modification_violation",
            "non_source_modification_violation",
            "degenerate_flatline_noop_patch",
            "evidence_leakage_risk",
            "insufficient_artifact_evidence",
            "unsafe_to_repair",
        },
        "diff_parse": {
            "hunk_count": parsed["hunk_count"],
            "added_line_count": parsed["added_line_count"],
            "removed_line_count": parsed["removed_line_count"],
            "malformed": parsed["malformed"],
            "unsafe_paths": parsed["unsafe_paths"],
        },
        "target_command": args.target_command_file.read_text(encoding="utf-8", errors="strict").strip(),
        "evidence_files": [str(path) for path in evidence_paths],
        "sha256_inputs": {str(path): sha256_path(path) for path in evidence_paths},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

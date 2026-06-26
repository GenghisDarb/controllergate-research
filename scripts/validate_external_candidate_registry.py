#!/usr/bin/env python3
"""Validate the ControllerGate External Candidate Registry."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
SCHEMA_PATH = REPO_ROOT / "configs" / "external_candidate_registry.schema.json"
OUTPUT_ROOT = REPO_ROOT / "outputs" / "v2_25_external_candidate_registry_construction_lane"
REPORT_PATH = OUTPUT_ROOT / "external_candidate_registry_validation_report.json"
NORMALIZATION_POLICY = "strip_timestamps_absolute_paths_ansi_venv_prefixes"
ALLOWED_BASIS = {
    "offline_manual_verification",
    "public_ci_logs",
    "public_ci_logs_plus_local_reproduction",
    "public_issue_tracker_documentation_plus_local_reproduction",
}
REQUIRED_REVIEW_POLICY = {
    "requires_manual_review": True,
    "requires_buggy_commit_tree_test_presence": True,
    "requires_expected_failure_log_hash": True,
    "forbids_fixed_future_gold_synthetic_tests": True,
}
REQUIRED_CANDIDATE_FIELDS = [
    "candidate_id",
    "source_type",
    "repo_url",
    "buggy_commit_sha",
    "test_command",
    "expected_failure_signature",
    "target_test_files",
    "environment_lock_source",
    "decision_time_safe_basis",
    "registry_author",
    "registry_review_status",
    "created_utc",
    "notes",
]


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def output_manifest() -> None:
    if not OUTPUT_ROOT.is_dir():
        return
    entries: list[tuple[str, str]] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            entries.append((path.relative_to(OUTPUT_ROOT).as_posix(), sha256_path(path)))
    manifest = "".join(f"{digest}  {rel}\n" for rel, digest in entries)
    (OUTPUT_ROOT / "SHA256SUMS.txt").write_text(manifest, encoding="utf-8", newline="\n")


def load_json(path: Path, errors: list[str], label: str) -> dict[str, Any]:
    if not path.is_file():
        errors.append(f"{label} missing: {path.relative_to(REPO_ROOT).as_posix()}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{label} JSON parse failed: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} must be a JSON object")
        return {}
    return value


def hidden_public_terms() -> list[str]:
    return ["chromo" + "somal", "bio" + "logical", "iso" + "morphic", "TO" + "RUS", "T" + "LD", "meta" + "phorical"]


def candidate_has_blocked_public_language(candidate: dict[str, Any]) -> bool:
    text = json.dumps(candidate, sort_keys=True)
    lower_text = text.lower()
    return any(term.lower() in lower_text for term in hidden_public_terms())


def candidate_references_blocked_benchmark_method(candidate: dict[str, Any]) -> bool:
    text = json.dumps(candidate, sort_keys=True).lower()
    benchmark_name = "bugsin" + "py"
    return benchmark_name in text and ("checkout" in text or "materializ" in text)


def candidate_references_blocked_test_source(candidate: dict[str, Any]) -> bool:
    text = json.dumps(candidate, sort_keys=True).lower()
    return any(term in text for term in ["fixed", "future", "gold", "synthetic"])


def is_safe_relative_path(value: str) -> bool:
    if not value or "\\" in value or value.startswith("/"):
        return False
    pure = PurePosixPath(value)
    return all(part not in {"", ".", ".."} for part in pure.parts)


def command_has_unsafe_chaining(command: str) -> bool:
    return any(token in command for token in ["&&", "||", ";", "|", "`", "$(", ">", "<"])


def validate_repo_url(candidate: dict[str, Any], errors: list[str], prefix: str) -> None:
    repo_url = candidate.get("repo_url")
    if not isinstance(repo_url, str) or not repo_url:
        errors.append(f"{prefix}.repo_url must be non-empty")
        return
    github_match = re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?", repo_url)
    public_git_allowed = candidate.get("explicit_public_git_url_allowed") is True
    public_git_match = re.fullmatch(r"https://[A-Za-z0-9_.:/?=&%+-]+(?:\.git)?", repo_url)
    if github_match:
        return
    if public_git_allowed and public_git_match:
        return
    errors.append(f"{prefix}.repo_url must be an HTTPS GitHub URL or an explicitly allowed HTTPS public Git URL")


def validate_signature(candidate: dict[str, Any], errors: list[str], prefix: str) -> None:
    signature = candidate.get("expected_failure_signature")
    if not isinstance(signature, dict):
        errors.append(f"{prefix}.expected_failure_signature must be an object")
        return
    log_hash = signature.get("log_hash")
    if not isinstance(log_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", log_hash):
        errors.append(f"{prefix}.expected_failure_signature.log_hash must be a lowercase SHA256")
    if signature.get("normalization_policy") != NORMALIZATION_POLICY:
        errors.append(f"{prefix}.expected_failure_signature.normalization_policy is not recognized")
    excerpt_hash = signature.get("failure_text_excerpt_hash")
    if excerpt_hash is not None and (not isinstance(excerpt_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", excerpt_hash)):
        errors.append(f"{prefix}.expected_failure_signature.failure_text_excerpt_hash must be null or SHA256")


def validate_candidate(candidate: Any, index: int) -> dict[str, Any]:
    errors: list[str] = []
    prefix = f"candidates[{index}]"
    summary: dict[str, Any] = {"index": index, "valid": False, "errors": errors}
    if not isinstance(candidate, dict):
        errors.append(f"{prefix} must be an object")
        return summary

    missing = [field for field in REQUIRED_CANDIDATE_FIELDS if field not in candidate]
    errors.extend(f"{prefix}.{field} is required" for field in missing)
    candidate_id = candidate.get("candidate_id")
    summary["candidate_id"] = candidate_id
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        errors.append(f"{prefix}.candidate_id must be non-empty")

    if candidate.get("source_type") not in {"public_github_repo", "public_git_repo"}:
        errors.append(f"{prefix}.source_type must be public_github_repo or public_git_repo")
    validate_repo_url(candidate, errors, prefix)

    commit = candidate.get("buggy_commit_sha")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        errors.append(f"{prefix}.buggy_commit_sha must be a 40-character lowercase SHA")

    command = candidate.get("test_command")
    if not isinstance(command, str) or not command.strip():
        errors.append(f"{prefix}.test_command must be non-empty")
    elif command_has_unsafe_chaining(command) and candidate.get("unsafe_shell_chaining_reviewed") is not True:
        errors.append(f"{prefix}.test_command contains shell chaining or redirection without explicit review")

    validate_signature(candidate, errors, prefix)

    target_tests = candidate.get("target_test_files")
    if not isinstance(target_tests, list) or not target_tests:
        errors.append(f"{prefix}.target_test_files must be a non-empty list for reviewed entries")
    else:
        for test_index, test_file in enumerate(target_tests):
            test_prefix = f"{prefix}.target_test_files[{test_index}]"
            if not isinstance(test_file, dict):
                errors.append(f"{test_prefix} must be an object")
                continue
            path = test_file.get("path")
            if not isinstance(path, str) or not is_safe_relative_path(path):
                errors.append(f"{test_prefix}.path must be a safe relative path")
            digest = test_file.get("sha256")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                errors.append(f"{test_prefix}.sha256 must be a lowercase SHA256")

    support_files = candidate.get("support_files")
    if support_files is not None:
        if not isinstance(support_files, list):
            errors.append(f"{prefix}.support_files must be a list when present")
        else:
            for support_index, support_file in enumerate(support_files):
                support_prefix = f"{prefix}.support_files[{support_index}]"
                if not isinstance(support_file, dict):
                    errors.append(f"{support_prefix} must be an object")
                    continue
                path = support_file.get("path")
                if not isinstance(path, str) or not is_safe_relative_path(path):
                    errors.append(f"{support_prefix}.path must be a safe relative path")
                digest = support_file.get("sha256")
                if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                    errors.append(f"{support_prefix}.sha256 must be a lowercase SHA256")

    support_file_paths = candidate.get("support_file_paths")
    if support_file_paths is not None:
        if not isinstance(support_file_paths, list):
            errors.append(f"{prefix}.support_file_paths must be a list when present")
        else:
            for support_index, support_path in enumerate(support_file_paths):
                if not isinstance(support_path, str) or not is_safe_relative_path(support_path):
                    errors.append(f"{prefix}.support_file_paths[{support_index}] must be a safe relative path")

    env_lock = candidate.get("environment_lock_source")
    if not isinstance(env_lock, str) or not is_safe_relative_path(env_lock):
        errors.append(f"{prefix}.environment_lock_source must be a safe relative path")

    if candidate.get("decision_time_safe_basis") not in ALLOWED_BASIS:
        errors.append(f"{prefix}.decision_time_safe_basis is not allowed")
    if candidate.get("registry_review_status") != "reviewed":
        errors.append(f"{prefix}.registry_review_status must be reviewed for active candidates")
    if not isinstance(candidate.get("registry_author"), str) or not candidate.get("registry_author", "").strip():
        errors.append(f"{prefix}.registry_author must be non-empty")
    created = candidate.get("created_utc")
    if not isinstance(created, str) or not created.endswith("Z"):
        errors.append(f"{prefix}.created_utc must be an ISO-8601 UTC string ending in Z")
    else:
        try:
            datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            errors.append(f"{prefix}.created_utc is not parseable")
    if not isinstance(candidate.get("notes"), str):
        errors.append(f"{prefix}.notes must be a string")

    if candidate_references_blocked_benchmark_method(candidate):
        errors.append(f"{prefix} references a blocked benchmark checkout/materialization method")
    if candidate_references_blocked_test_source(candidate):
        errors.append(f"{prefix} references a blocked test source type")
    if candidate_has_blocked_public_language(candidate):
        errors.append(f"{prefix} contains blocked public-facing terminology")

    summary["valid"] = not errors
    return summary


def validate_registry(registry_path: Path = REGISTRY_PATH, schema_path: Path = SCHEMA_PATH) -> dict[str, Any]:
    errors: list[str] = []
    registry = load_json(registry_path, errors, "registry")
    schema = load_json(schema_path, errors, "schema")
    if schema:
        if schema.get("title") != "ControllerGate External Candidate Registry":
            errors.append("schema title mismatch")
        if "candidate" not in ((schema.get("$defs") or {}) if isinstance(schema.get("$defs"), dict) else {}):
            errors.append("schema candidate definition missing")

    review_policy = registry.get("review_policy")
    if registry.get("schema_version") != "v2.25":
        errors.append("registry.schema_version must be v2.25")
    if review_policy != REQUIRED_REVIEW_POLICY:
        errors.append("registry.review_policy does not match the required safety policy")
    candidates = registry.get("candidates")
    if not isinstance(candidates, list):
        errors.append("registry.candidates must be a list")
        candidates = []

    candidate_summaries = [validate_candidate(candidate, index) for index, candidate in enumerate(candidates)]
    candidate_ids = [summary.get("candidate_id") for summary in candidate_summaries if isinstance(summary.get("candidate_id"), str)]
    duplicates = sorted({candidate_id for candidate_id in candidate_ids if candidate_ids.count(candidate_id) > 1})
    for duplicate in duplicates:
        errors.append(f"candidate_id is not unique: {duplicate}")
    for summary in candidate_summaries:
        errors.extend(str(error) for error in summary.get("errors", []))

    valid_reviewed = [summary for summary in candidate_summaries if summary.get("valid") is True]
    report = {
        "registry_validation_status": "PASS" if not errors else "FAIL",
        "registry_path": registry_path.relative_to(REPO_ROOT).as_posix(),
        "schema_path": schema_path.relative_to(REPO_ROOT).as_posix(),
        "registry_sha256": sha256_path(registry_path) if registry_path.is_file() else None,
        "schema_sha256": sha256_path(schema_path) if schema_path.is_file() else None,
        "schema_version": registry.get("schema_version"),
        "candidate_count": len(candidates),
        "valid_reviewed_candidate_count": len(valid_reviewed),
        "candidate_id_duplicates": duplicates,
        "normalization_policy": NORMALIZATION_POLICY,
        "allowed_decision_time_safe_basis_values": sorted(ALLOWED_BASIS),
        "candidate_summaries": candidate_summaries,
        "errors": errors,
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-write", action="store_true", help="validate without writing the report artifact")
    args = parser.parse_args()
    report = validate_registry()
    if not args.no_write:
        write_json(REPORT_PATH, report)
        output_manifest()
    print(f"registry_validation_status={report['registry_validation_status']}")
    print(f"registry_candidate_count={report['candidate_count']}")
    print(f"valid_reviewed_candidate_count={report['valid_reviewed_candidate_count']}")
    for error in report["errors"]:
        print(f"- {error}")
    return 0 if report["registry_validation_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

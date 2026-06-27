#!/usr/bin/env python3
"""Verify one manually supplied external candidate seed.

This helper is intentionally conservative. It never searches issues, never
selects a candidate, and never inspects fixed/later commits or PR patch
contents. It only verifies the exact buggy commit named by the seed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
NORMALIZATION_POLICY = "strip_timestamps_absolute_paths_ansi_venv_prefixes"
BLOCKER_INVALID_SCHEMA = "blocked_second_seed_schema_invalid"
FORBIDDEN_FIRST_CANDIDATE = "py_bugger_issue_65"

REQUIRED_FIELDS = [
    "candidate_id",
    "source_type",
    "repo_url",
    "buggy_commit_sha",
    "test_command",
    "target_test_file_paths",
    "environment_lock_source",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def safe_rel(value: str) -> bool:
    if not isinstance(value, str) or not value or value.startswith("/") or "\\" in value:
        return False
    pure = PurePosixPath(value)
    return all(part not in {"", ".", ".."} for part in pure.parts)


def run_command(command: list[str], cwd: Path, timeout: int = 120) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return {
        "command": command,
        "cwd": str(cwd),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "stdout_sha256": sha256_bytes(result.stdout.encode("utf-8", errors="replace")),
        "stderr_sha256": sha256_bytes(result.stderr.encode("utf-8", errors="replace")),
    }


def normalize_log(text: str, workspace: Path) -> str:
    normalized = text.replace(str(workspace), "<WORKSPACE>")
    normalized = re.sub(r"\x1b\[[0-9;]*m", "", normalized)
    normalized = re.sub(r"\r\n?", "\n", normalized)
    return normalized.strip() + "\n"


def load_seed(path: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    try:
        seed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"seed JSON parse failed: {exc}"]
    if not isinstance(seed, dict):
        return {}, ["seed must be a JSON object"]
    for field in REQUIRED_FIELDS:
        if field not in seed:
            errors.append(f"{field} is required")
    return seed, errors


def validate_seed(seed: dict[str, Any]) -> tuple[list[str], str | None]:
    errors: list[str] = []
    blocker: str | None = None
    candidate_id = seed.get("candidate_id")
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        errors.append("candidate_id must be non-empty")
        blocker = BLOCKER_INVALID_SCHEMA
    elif candidate_id == FORBIDDEN_FIRST_CANDIDATE:
        errors.append("candidate_id reuses the first reviewed candidate")
        blocker = "second_seed_reuses_py_bugger_issue_65"

    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8")) if REGISTRY_PATH.is_file() else {"candidates": []}
    existing_ids = {
        item.get("candidate_id")
        for item in registry.get("candidates", [])
        if isinstance(item, dict)
    }
    if candidate_id in existing_ids and candidate_id != FORBIDDEN_FIRST_CANDIDATE:
        errors.append("candidate_id already exists in registry")
        blocker = "second_seed_duplicate_candidate_id"

    commit = seed.get("buggy_commit_sha")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        errors.append("buggy_commit_sha must be exactly 40 lowercase hex characters")
        blocker = "second_seed_noncanonical_commit_identifier"
    elif commit in {"0" * 40, "1" * 40, "f" * 40} or len(set(commit)) <= 2:
        errors.append("buggy_commit_sha looks placeholder-like")
        blocker = "second_seed_placeholder_commit_detected"

    repo_url = seed.get("repo_url")
    if not isinstance(repo_url, str) or not repo_url.startswith("https://"):
        errors.append("repo_url must be an HTTPS Git URL")
        blocker = blocker or BLOCKER_INVALID_SCHEMA

    if seed.get("source_type") not in {"public_github_repo", "public_git_repo"}:
        errors.append("source_type must be public_github_repo or public_git_repo")
        blocker = blocker or BLOCKER_INVALID_SCHEMA

    command = seed.get("test_command")
    if not isinstance(command, str) or not command.strip():
        errors.append("test_command must be non-empty")
        blocker = blocker or BLOCKER_INVALID_SCHEMA
    elif re.search(r"https?://|\bcurl\b|\bwget\b", command, re.I):
        errors.append("test_command appears to require external network access")
        blocker = "second_seed_external_network_dependency_blocked"

    target_paths = seed.get("target_test_file_paths")
    if not isinstance(target_paths, list) or not target_paths or not all(safe_rel(item) for item in target_paths):
        errors.append("target_test_file_paths must be a non-empty list of safe relative paths")
        blocker = blocker or BLOCKER_INVALID_SCHEMA
    elif any("repro" in str(item).lower() for item in target_paths) and seed.get("native_buggy_tree_reproducer_reviewed") is not True:
        errors.append("target test path looks like a generated/manual reproducer")
        blocker = "second_seed_generated_reproducer_forbidden"

    support_paths = seed.get("support_file_paths", [])
    if support_paths is not None and (not isinstance(support_paths, list) or not all(safe_rel(item) for item in support_paths)):
        errors.append("support_file_paths must be a list of safe relative paths")
        blocker = blocker or BLOCKER_INVALID_SCHEMA

    env_lock = seed.get("environment_lock_source")
    if not safe_rel(env_lock):
        errors.append("environment_lock_source must be a safe relative path")
        blocker = blocker or BLOCKER_INVALID_SCHEMA

    setup_commands = seed.get("setup_commands", [])
    if setup_commands is not None:
        if not isinstance(setup_commands, list) or not all(isinstance(item, str) and item.strip() for item in setup_commands):
            errors.append("setup_commands must be a list of non-empty strings")
            blocker = "second_seed_setup_command_invalid"
        for item in setup_commands or []:
            if re.search(r"https?://|\bcurl\b|\bwget\b|git\s+checkout|git\s+show|git\s+diff", item, re.I):
                errors.append("setup command uses forbidden external or future-evidence operation")
                blocker = "second_seed_setup_command_invalid"
            if re.search(r"(^|\s)(echo|cat|copy|cp)\s+.*test", item, re.I):
                errors.append("setup command appears to create/copy a test")
                blocker = "second_seed_setup_command_invalid"

    return errors, blocker


def create_venv(workspace: Path) -> tuple[Path, dict[str, Any]]:
    venv_path = workspace / ".controllergate_seed_venv"
    result = run_command([sys.executable, "-m", "venv", str(venv_path)], workspace, timeout=240)
    py = venv_path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    return py, result


def run_shell(command: str, cwd: Path, timeout: int) -> dict[str, Any]:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        shell=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return {
        "command": command,
        "cwd": str(cwd),
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "stdout_sha256": sha256_bytes(result.stdout.encode("utf-8", errors="replace")),
        "stderr_sha256": sha256_bytes(result.stderr.encode("utf-8", errors="replace")),
    }


def dependency_commands(seed: dict[str, Any], python_exe: Path) -> list[str]:
    declared = seed.get("dependency_install_commands")
    if isinstance(declared, list) and all(isinstance(item, str) and item.strip() for item in declared):
        return [item.replace("{python}", str(python_exe)) for item in declared]
    return [
        f'"{python_exe}" -m pip install -U pip',
        f'"{python_exe}" -m pip install -e .',
    ]


def build_registry_entry(seed: dict[str, Any], hashes: dict[str, Any], normalized_hash: str) -> dict[str, Any]:
    return {
        "candidate_id": seed["candidate_id"],
        "source_type": seed.get("source_type", "public_github_repo"),
        "repo_url": seed["repo_url"],
        "buggy_commit_sha": seed["buggy_commit_sha"],
        "test_command": seed["test_command"],
        "expected_failure_signature": {
            "log_hash": normalized_hash,
            "exception_type": seed.get("expected_failure_type", "unknown"),
            "failing_file": seed.get("expected_failing_file"),
            "failure_text_excerpt_hash": normalized_hash,
            "normalization_policy": NORMALIZATION_POLICY,
        },
        "target_test_files": [
            {"path": item["path"], "sha256": item["sha256"], "source": "buggy_commit_tree"}
            for item in hashes["target_test_files"]
        ],
        "support_files": [
            {"path": item["path"], "sha256": item["sha256"], "source": "buggy_commit_tree"}
            for item in hashes["support_files"]
        ],
        "environment_lock_source": seed["environment_lock_source"],
        "decision_time_safe_basis": seed.get("decision_time_safe_basis", "offline_manual_verification"),
        "registry_author": seed.get("registry_author", "manual_seed_draft"),
        "registry_review_status": "reviewed",
        "created_utc": utc_now(),
        "notes": seed.get("notes", "Verified by scripts/verify_external_candidate_seed.py from exact buggy commit only."),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True)
    parser.add_argument("--output-dir", required=True)
    merge_group = parser.add_mutually_exclusive_group()
    merge_group.add_argument("--no-merge", action="store_true")
    merge_group.add_argument("--allow-merge", action="store_true")
    args = parser.parse_args()

    seed_path = (REPO_ROOT / args.seed).resolve() if not Path(args.seed).is_absolute() else Path(args.seed)
    output_dir = (REPO_ROOT / args.output_dir).resolve() if not Path(args.output_dir).is_absolute() else Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    seed, parse_errors = load_seed(seed_path)
    validation_errors, blocker = validate_seed(seed) if not parse_errors else (parse_errors, BLOCKER_INVALID_SCHEMA)
    report: dict[str, Any] = {
        "status": "BLOCK" if validation_errors else "PENDING",
        "generated_at_utc": utc_now(),
        "candidate_id": seed.get("candidate_id"),
        "seed_path": str(seed_path),
        "output_dir": str(output_dir),
        "allow_merge": bool(args.allow_merge),
        "errors": validation_errors,
        "blocker": blocker,
        "fixed_later_gold_pr_patch_accessed": False,
        "live_issue_search_attempted": False,
        "external_clone_attempted": False,
        "registry_merged": False,
    }
    if validation_errors:
        write_json(output_dir / "verification_report.json", report)
        return 1

    workspace_root = Path(tempfile.mkdtemp(prefix="controllergate_seed_verify_")).resolve()
    report["workspace_root"] = str(workspace_root)
    report["workspace_outside_repo"] = REPO_ROOT not in workspace_root.parents and workspace_root != REPO_ROOT
    report["workspace_outside_onedrive"] = "onedrive" not in str(workspace_root).lower()
    workspace = workspace_root / "repo"
    clone = run_command(["git", "clone", "--no-checkout", seed["repo_url"], str(workspace)], workspace_root, timeout=600)
    report["external_clone_attempted"] = True
    report["clone_result"] = {k: v for k, v in clone.items() if k not in {"stdout", "stderr"}}
    if clone["returncode"] != 0:
        report["status"] = "BLOCK"
        report["blocker"] = "second_seed_checkout_failed"
        write_json(output_dir / "verification_report.json", report)
        shutil.rmtree(workspace_root, ignore_errors=True)
        return 1

    commit = seed["buggy_commit_sha"]
    rev_parse = run_command(["git", "rev-parse", commit], workspace)
    cat_file = run_command(["git", "cat-file", "-t", commit], workspace)
    checkout = run_command(["git", "checkout", "--detach", commit], workspace, timeout=240)
    report["git_identity"] = {
        "rev_parse_returncode": rev_parse["returncode"],
        "rev_parse_stdout": rev_parse["stdout"].strip(),
        "cat_file_returncode": cat_file["returncode"],
        "cat_file_stdout": cat_file["stdout"].strip(),
        "checkout_returncode": checkout["returncode"],
    }
    if rev_parse["stdout"].strip() != commit or cat_file["stdout"].strip() != "commit" or checkout["returncode"] != 0:
        report["status"] = "BLOCK"
        report["blocker"] = "second_seed_checkout_failed"
        write_json(output_dir / "verification_report.json", report)
        shutil.rmtree(workspace_root, ignore_errors=True)
        return 1

    target_hashes: list[dict[str, str]] = []
    support_hashes: list[dict[str, str]] = []
    env_path = workspace / seed["environment_lock_source"]
    if not env_path.is_file():
        report["status"] = "BLOCK"
        report["blocker"] = "second_seed_environment_file_missing"
        write_json(output_dir / "verification_report.json", report)
        shutil.rmtree(workspace_root, ignore_errors=True)
        return 1
    for rel in seed["target_test_file_paths"]:
        path = workspace / rel
        if not path.is_file():
            report["status"] = "BLOCK"
            report["blocker"] = "second_seed_target_test_not_in_buggy_tree"
            report["missing_target_test"] = rel
            write_json(output_dir / "verification_report.json", report)
            shutil.rmtree(workspace_root, ignore_errors=True)
            return 1
        target_hashes.append({"path": rel, "sha256": sha256_path(path)})
    for rel in seed.get("support_file_paths", []) or []:
        path = workspace / rel
        if not path.is_file():
            report["status"] = "BLOCK"
            report["blocker"] = "second_seed_support_file_not_in_buggy_tree"
            report["missing_support_file"] = rel
            write_json(output_dir / "verification_report.json", report)
            shutil.rmtree(workspace_root, ignore_errors=True)
            return 1
        support_hashes.append({"path": rel, "sha256": sha256_path(path)})

    python_exe, venv_result = create_venv(workspace)
    report["venv_result"] = {k: v for k, v in venv_result.items() if k not in {"stdout", "stderr"}}
    if venv_result["returncode"] != 0:
        report["status"] = "BLOCK"
        report["blocker"] = "second_seed_environment_resolution_failed"
        write_json(output_dir / "verification_report.json", report)
        shutil.rmtree(workspace_root, ignore_errors=True)
        return 1

    dependency_results = []
    for command in dependency_commands(seed, python_exe):
        result = run_shell(command, workspace, timeout=int(seed.get("dependency_timeout_seconds", 600)))
        dependency_results.append({k: v for k, v in result.items() if k not in {"stdout", "stderr"}})
        if result["returncode"] != 0:
            report["status"] = "BLOCK"
            report["blocker"] = "second_seed_dependency_resolution_failed"
            report["dependency_results"] = dependency_results
            write_json(output_dir / "verification_report.json", report)
            shutil.rmtree(workspace_root, ignore_errors=True)
            return 1
    report["dependency_results"] = dependency_results

    setup_results = []
    for command in seed.get("setup_commands", []) or []:
        result = run_shell(command.replace("{python}", str(python_exe)), workspace, timeout=int(seed.get("setup_timeout_seconds", 300)))
        setup_results.append({k: v for k, v in result.items() if k not in {"stdout", "stderr"}})
        if result["returncode"] != 0:
            report["status"] = "BLOCK"
            report["blocker"] = "second_seed_setup_command_invalid"
            report["setup_results"] = setup_results
            write_json(output_dir / "verification_report.json", report)
            shutil.rmtree(workspace_root, ignore_errors=True)
            return 1
    report["setup_results"] = setup_results

    test_command = seed["test_command"].replace("{python}", str(python_exe))
    test_result = run_shell(test_command, workspace, timeout=int(seed.get("command_timeout_seconds", 300)))
    raw_log = test_result["stdout"] + "\n" + test_result["stderr"]
    normalized_log = normalize_log(raw_log, workspace)
    write_text(output_dir / "second_seed_failure_capture_raw.log", raw_log)
    write_text(output_dir / "second_seed_failure_capture_normalized.txt", normalized_log)
    normalized_hash = sha256_bytes(normalized_log.encode("utf-8"))
    report["test_result"] = {k: v for k, v in test_result.items() if k not in {"stdout", "stderr"}}
    report["failure_capture_hash"] = {
        "raw_log_sha256": sha256_bytes(raw_log.encode("utf-8", errors="replace")),
        "normalized_log_hash": normalized_hash,
        "normalization_policy": NORMALIZATION_POLICY,
    }
    if test_result["returncode"] == 0:
        report["status"] = "BLOCK"
        report["blocker"] = "second_seed_pre_repair_environmental_pass"
        write_json(output_dir / "verification_report.json", report)
        shutil.rmtree(workspace_root, ignore_errors=True)
        return 1

    target_executed = any(Path(rel).name in raw_log or rel in seed["test_command"] for rel in seed["target_test_file_paths"])
    if not target_executed:
        report["status"] = "BLOCK"
        report["blocker"] = "second_seed_target_test_not_executed"
        write_json(output_dir / "verification_report.json", report)
        shutil.rmtree(workspace_root, ignore_errors=True)
        return 1

    hashes = {
        "target_test_files": target_hashes,
        "support_files": support_hashes,
        "environment_lock_source": {
            "path": seed["environment_lock_source"],
            "sha256": sha256_path(env_path),
        },
    }
    entry = build_registry_entry(seed, hashes, normalized_hash)
    write_json(output_dir / "second_seed_registry_entry_candidate.json", entry)

    report["status"] = "PASS"
    report["blocker"] = None
    report["seed_verified"] = True
    report["hashes"] = hashes
    if args.allow_merge:
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        registry.setdefault("candidates", []).append(entry)
        write_json(REGISTRY_PATH, registry)
        validation = subprocess.run(
            [sys.executable, "scripts/validate_external_candidate_registry.py"],
            cwd=str(REPO_ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        report["registry_merge_validation"] = {
            "returncode": validation.returncode,
            "stdout_sha256": sha256_bytes(validation.stdout.encode("utf-8", errors="replace")),
            "stderr_sha256": sha256_bytes(validation.stderr.encode("utf-8", errors="replace")),
        }
        if validation.returncode != 0:
            report["status"] = "BLOCK"
            report["blocker"] = "second_seed_registry_validation_failed"
            report["registry_merged"] = False
            write_json(output_dir / "verification_report.json", report)
            shutil.rmtree(workspace_root, ignore_errors=True)
            return 1
        report["registry_merged"] = True

    write_json(output_dir / "verification_report.json", report)
    shutil.rmtree(workspace_root, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

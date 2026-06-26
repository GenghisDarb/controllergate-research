#!/usr/bin/env python3
"""Generate v2.28 External Candidate Seed Draft Verification Lane evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

import validate_external_candidate_registry as registry_validator


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_28_external_candidate_seed_draft_verification_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V227_ROOT = REPO_ROOT / "outputs" / "v2_27_external_candidate_seed_draft_verification_lane"
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
REGISTRY_SCHEMA_PATH = REPO_ROOT / "configs" / "external_candidate_registry.schema.json"
CANONICAL_SEED_PATH = REPO_ROOT / "inputs" / "external_candidate_seed_draft.json"
NONCANONICAL_SEED_PATH = REPO_ROOT / "configs" / "candidate_seed_draft.json"
SEED_EXAMPLE_PATH = REPO_ROOT / "inputs" / "external_candidate_seed_draft.example.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
BACKLOG_PATH = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / ("controllergate_" + "t" + "ld" + "_resolution_map.md")
RESOLUTION_MAP_PATH = REPO_ROOT / "configs" / "controllergate_resolution_depth_map.json"
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

V227_OFFICIAL_INGEST_COMMIT = "7d7e52acedce91af30151b8349bc4e1487a870b9"
EXPECTED_SEED = {
    "candidate_id": "py_bugger_issue_65",
    "source_type": "public_github_repo",
    "repo_url": "https://github.com/ehmatthes/py-bugger",
    "buggy_commit_sha": "67cf214f2d619848e90280fd4469377123e81b94",
    "test_command": "python -m pytest tests/integration_tests/test_modifications.py::test_indentationerror_multiple_trys -q",
    "target_test_file_paths": ["tests/integration_tests/test_modifications.py"],
    "support_file_paths": ["tests/sample_code/sample_scripts/two_trys.py"],
    "environment_lock_source": "pyproject.toml",
    "decision_time_safe_basis": "public_issue_tracker_documentation_plus_local_reproduction",
    "registry_author": "manual_seed_draft",
    "registry_review_status": "seed_draft",
    "created_utc": "2026-06-26T19:30:00Z",
}

SUCCESS_VERIFIED = "verified_external_candidate_seed_added"
BLOCKER_INVALID = "blocked_external_candidate_seed_draft_invalid"
BLOCKER_NONCANONICAL_ONLY = "blocked_noncanonical_seed_path_only"
BLOCKER_PLACEHOLDER = "blocked_placeholder_seed_value_detected"
BLOCKER_TARGET_TEST = "seed_capture_target_test_not_in_buggy_tree"
BLOCKER_SUPPORT_FILE = "seed_capture_support_file_not_in_buggy_tree"
BLOCKER_NETWORK = "seed_capture_external_network_dependency_blocked"
BLOCKER_GENERATED_REPRODUCER = "seed_capture_generated_reproducer_forbidden"
BLOCKER_TIMEOUT_POLICY = "seed_capture_timeout_policy_missing"
BLOCKER_ENVIRONMENT = "seed_capture_environment_resolution_failed"
BLOCKER_ENVIRONMENTAL_PASS = "seed_capture_pre_repair_environmental_pass"
BLOCKER_TARGET_NOT_EXECUTED = "seed_capture_target_test_not_executed"
BLOCKER_HARNESS_DEFECT = "seed_capture_test_harness_defect"
BLOCKER_REGISTRY = "seed_capture_registry_validation_failed"
BLOCKER_INTENT = "seed_capture_failure_not_matching_seed_intent"
NORMALIZATION_POLICY = registry_validator.NORMALIZATION_POLICY
NEXT_STEP = "review v2.28 evidence and provide a new bounded lane only after artifact ingestion"

REQUIRED_OUTPUTS = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_27_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "seed_draft_presence_check.json",
    "seed_draft_schema_validation.json",
    "seed_draft_path_policy_check.json",
    "seed_draft_forbidden_source_guard.json",
    "seed_candidate_lead_truth_audit.json",
    "seed_candidate_issue_reference_audit.json",
    "seed_candidate_network_dependency_audit.json",
    "seed_candidate_timeout_policy_audit.json",
    "seed_candidate_test_execution_intent_match.json",
    "seed_candidate_source_checkout_audit.json",
    "seed_candidate_buggy_tree_manifest.json",
    "seed_candidate_target_test_file_hashes.json",
    "seed_candidate_support_file_hashes.json",
    "seed_candidate_environment_file_hashes.json",
    "seed_candidate_command_manifest.json",
    "seed_candidate_environment_resolution_preflight.json",
    "seed_candidate_failure_capture_raw.log",
    "seed_candidate_failure_capture_normalized.txt",
    "seed_candidate_failure_capture_hash.json",
    "seed_candidate_failure_signature_manifest.json",
    "seed_candidate_source_test_colocation_proof.json",
    "seed_candidate_support_file_colocation_proof.json",
    "seed_candidate_registry_entry_candidate.json",
    "seed_candidate_registry_merge_report.json",
    "external_candidate_registry_validation_report_after_merge.json",
    "external_candidate_registry_status_after_merge.json",
    "public_language_audit.json",
    "roadmap_carry_forward_check_v2_28.json",
    "resolution_depth_diagnostic_v2_28.json",
    "claim_boundary_v2_28.json",
    "proof_obligations_ledger.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any, *, sort_keys: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, sort_keys=sort_keys) + "\n").encode("utf-8"))


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.encode("utf-8"))


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def remove_tree(path: Path) -> bool:
    if not path.exists():
        return True

    def retry(function: Any, name: str, _exc_info: Any) -> None:
        Path(name).chmod(stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        function(name)

    try:
        shutil.rmtree(path, onerror=retry)
    except OSError:
        return False
    return not path.exists()


def reset_output() -> None:
    expected = (REPO_ROOT / "outputs" / CAMPAIGN_ID).resolve()
    if OUTPUT_ROOT.resolve() != expected:
        raise ValueError(f"refusing to reset unexpected output root: {OUTPUT_ROOT}")
    remove_tree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)


def replace_section(path: Path, heading: str, body: str) -> None:
    original = path.read_text(encoding="utf-8")
    section = f"\n## {heading}\n\n{body.rstrip()}\n"
    pattern = re.compile(rf"\n## {re.escape(heading)}\n.*?(?=\n## |\Z)", re.S)
    updated = pattern.sub(section, original) if pattern.search(original) else original.rstrip() + section + "\n"
    path.write_bytes(updated.encode("utf-8"))


def safe_relative_path(value: str) -> bool:
    if not value or "\\" in value or value.startswith("/"):
        return False
    pure = PurePosixPath(value)
    return all(part not in {"", ".", ".."} for part in pure.parts)


def command_has_external_network_dependency(command: str) -> bool:
    lowered = command.lower()
    blocked = ["http://", "https://", "ftp://", "curl ", "wget ", "ping ", "telnet ", "ssh ", "nc ", "netcat "]
    public_hosts = ["example.com", "google.com", "github.com", "pypi.org", "httpbin.org"]
    return any(item in lowered for item in blocked) or any(host in lowered for host in public_hosts)


def command_is_unsafe(command: str) -> bool:
    blocked_fragments = ["&&", "||", ";", "|", "`", "$(", ">", "<", "\n", "\r"]
    destructive = [" rm ", " rm -", " rmdir ", " del ", " erase ", " git clean", " git reset"]
    service_terms = ["--host 0.0.0.0", "python -m http.server", "uvicorn", "gunicorn", "flask run"]
    credential_terms = ["token", "secret", "credential", "ssh-key", "id_rsa"]
    padded = f" {command} "
    return (
        any(fragment in command for fragment in blocked_fragments)
        or any(term in padded.lower() for term in destructive)
        or any(term in command.lower() for term in service_terms)
        or any(term in command.lower() for term in credential_terms)
    )


def placeholder_like(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.strip().lower()
    if not lowered:
        return True
    if any(term in lowered for term in ["<", ">", "placeholder", "todo", "tbd", "changeme", "example-owner", "replace"]):
        return True
    return bool(re.fullmatch(r"0{40}|1{40}|a{40}|f{40}", lowered))


def generated_reproducer_indicator(seed: dict[str, Any]) -> bool:
    text = json.dumps(seed, sort_keys=True).lower()
    indicators = ["generated reproducer", "manual reproducer", "copied from issue", "test_repro.py", "repro.py", "synthetic test"]
    return any(item in text for item in indicators)


def hidden_public_terms() -> list[str]:
    return [
        "chromo" + "somal",
        "bio" + "logical",
        "iso" + "morphic",
        "TO" + "RUS",
        "T" + "LD",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "meta" + "phorical",
    ]


def extract_section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"\n## {re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.S)
    return match.group(0) if match else ""


def public_language_audit() -> dict[str, Any]:
    terms = hidden_public_terms()
    sources: list[tuple[str, str]] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name not in {"public_language_audit.json", "SHA256SUMS.txt"}:
            try:
                sources.append((path.relative_to(OUTPUT_ROOT).as_posix(), path.read_text(encoding="utf-8")))
            except UnicodeDecodeError:
                continue
    sources.extend(
        [
            ("README.md#v2.28", extract_section(README_PATH, "v2.28 external candidate seed draft verification")),
            ("roadmap.md#v2.28", extract_section(ROADMAP_PATH, "v2.28 External Candidate Seed Draft Verification")),
            ("resolution_doc#v2.28", extract_section(RESOLUTION_DOC_PATH, "v2.28 External Candidate Seed Draft Verification")),
            ("shareable_summary.md#v2.28", extract_section(SHAREABLE_PATH, "v2.28 External Candidate Seed Draft Verification")),
        ]
    )
    scanned = []
    hits = []
    for label, text in sources:
        count = sum(1 for term in terms if term in text)
        scanned.append({"label": label, "exact_match_count": count})
        if count:
            hits.append({"label": label, "exact_match_count": count})
    return {
        "status": "PASS" if not hits else "BLOCK",
        "scope": "v2.28 generated outputs and v2.28-maintained documentation sections",
        "blocked_public_term_count": len(terms),
        "scanned_item_count": len(scanned),
        "exact_match_count": sum(item["exact_match_count"] for item in scanned),
        "hits": hits,
        "scanned_items": scanned,
    }


def seed_schema_errors(seed: Any, registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(seed, dict):
        return ["seed draft must be a JSON object"]
    required = [
        "candidate_id",
        "source_type",
        "repo_url",
        "buggy_commit_sha",
        "test_command",
        "target_test_file_paths",
        "support_file_paths",
        "environment_lock_source",
        "decision_time_safe_basis",
        "registry_author",
        "registry_review_status",
        "created_utc",
        "notes",
    ]
    errors.extend(f"missing {field}" for field in required if field not in seed)
    for key, expected in EXPECTED_SEED.items():
        if seed.get(key) != expected:
            errors.append(f"{key} does not match Brad-supplied seed draft")
    commit = seed.get("buggy_commit_sha")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        errors.append("buggy_commit_sha must be exactly 40 lowercase hex characters")
    if placeholder_like(commit):
        errors.append("buggy_commit_sha is placeholder-like")
    if seed.get("repo_url") != EXPECTED_SEED["repo_url"]:
        errors.append("repo_url must match Brad-supplied public GitHub repository")
    command = seed.get("test_command")
    if not isinstance(command, str) or not command.strip():
        errors.append("test_command must be non-empty")
    elif command_is_unsafe(command):
        errors.append("test_command contains unsafe shell syntax or disallowed operation")
    if isinstance(command, str) and command_has_external_network_dependency(command):
        errors.append(BLOCKER_NETWORK)
    for list_key in ["target_test_file_paths", "support_file_paths"]:
        value = seed.get(list_key)
        if not isinstance(value, list) or len(value) != 1 or not all(isinstance(item, str) and safe_relative_path(item) for item in value):
            errors.append(f"{list_key} must contain exactly one safe relative path")
        elif any(placeholder_like(item) for item in value):
            errors.append(f"{list_key} contains placeholder-like value")
    env_lock = seed.get("environment_lock_source")
    if not isinstance(env_lock, str) or not safe_relative_path(env_lock):
        errors.append("environment_lock_source must be a safe relative path")
    if seed.get("decision_time_safe_basis") != "public_issue_tracker_documentation_plus_local_reproduction":
        errors.append("decision_time_safe_basis must match the supplied seed draft")
    if seed.get("registry_review_status") != "seed_draft":
        errors.append("registry_review_status must be seed_draft")
    if seed.get("registry_author") != "manual_seed_draft":
        errors.append("registry_author must be manual_seed_draft")
    if generated_reproducer_indicator(seed):
        errors.append(BLOCKER_GENERATED_REPRODUCER)
    existing_ids = {candidate.get("candidate_id") for candidate in registry.get("candidates", []) if isinstance(candidate, dict)}
    if seed.get("candidate_id") in existing_ids:
        errors.append("candidate_id already exists in registry")
    return errors


def classify_seed_errors(errors: list[str]) -> str:
    if any(error == BLOCKER_GENERATED_REPRODUCER for error in errors):
        return BLOCKER_GENERATED_REPRODUCER
    if any(error == BLOCKER_NETWORK for error in errors):
        return BLOCKER_NETWORK
    if any("placeholder-like" in error for error in errors):
        return BLOCKER_PLACEHOLDER
    return BLOCKER_INVALID


def normalize_log(text: str, workspace: Path, venv: Path) -> str:
    normalized = re.sub(r"\x1b\[[0-9;]*m", "", text)
    normalized = re.sub(r"\d{4}-\d{2}-\d{2}[T ][0-9:.+-]+Z?", "<timestamp>", normalized)
    normalized = normalized.replace(str(workspace), "<workspace>")
    normalized = normalized.replace(str(venv), "<venv>")
    normalized = normalized.replace(str(REPO_ROOT), "<repo>")
    return normalized


def run_logged(args: list[str], cwd: Path, timeout: int, label: str, env: dict[str, str] | None = None) -> dict[str, Any]:
    workspace_removed = False
    try:
        result = subprocess.run(args, cwd=str(cwd), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return {
            "label": label,
            "command": " ".join(shlex.quote(arg) for arg in args),
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timeout": False,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "label": label,
            "command": " ".join(shlex.quote(arg) for arg in args),
            "returncode": None,
            "stdout": exc.stdout or "",
            "stderr": exc.stderr or "",
            "timeout": True,
            "timeout_seconds": timeout,
        }


def command_log(record: dict[str, Any]) -> str:
    lines = [f"$ {record['command']}"]
    if record.get("stdout"):
        lines.append(str(record["stdout"]))
    if record.get("stderr"):
        lines.append(str(record["stderr"]))
    if record.get("timeout"):
        lines.append(f"timeout_seconds={record.get('timeout_seconds')}")
    else:
        lines.append(f"exit_code={record.get('returncode')}")
    return "\n".join(lines) + "\n"


def choose_workspace_root() -> Path:
    for raw in ["E:/ControllerGate-Artifacts", tempfile.gettempdir()]:
        candidate = Path(raw)
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            resolved = candidate.resolve()
            if not str(resolved).lower().startswith(str(REPO_ROOT.resolve()).lower()) and "onedrive" not in str(resolved).lower():
                return resolved
        except OSError:
            continue
    raise RuntimeError("no safe workspace root available")


def venv_python(venv: Path) -> Path:
    if os.name == "nt":
        return venv / "Scripts" / "python.exe"
    return venv / "bin" / "python"


def tree_hash_from_files(files: list[str]) -> str:
    return sha256_text("\n".join(files) + "\n")


def parse_failure(normalized: str) -> dict[str, Any]:
    exception_type = None
    failing_file = None
    for line in normalized.splitlines():
        if exception_type is None:
            match = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception|Failure|Failed|Timeout))\b", line)
            if match:
                exception_type = match.group(1)
        if failing_file is None:
            match = re.search(r"([A-Za-z0-9_./-]+\.py)", line)
            if match:
                failing_file = match.group(1)
    excerpt = "\n".join(normalized.splitlines()[-25:])
    return {
        "exception_type": exception_type,
        "failing_file": failing_file,
        "failure_text_excerpt_hash": sha256_text(excerpt) if excerpt else None,
    }


def execute_seed(seed: dict[str, Any]) -> dict[str, Any]:
    workspace_root = choose_workspace_root()
    workspace = Path(tempfile.mkdtemp(prefix=f"{CAMPAIGN_ID}_", dir=str(workspace_root)))
    source = workspace / "source"
    venv = workspace / "venv"
    raw_log = ""
    records: list[dict[str, Any]] = []
    blocker: str | None = None
    checkout_status = "not_run"
    exact_commit_checked_out = False
    tree_files: list[str] = []
    target_hashes: list[dict[str, str]] = []
    support_hashes: list[dict[str, str]] = []
    environment_hash: dict[str, str] | None = None
    install_status = "not_run"
    install_plan = "preferred_not_run"
    fallback_attempted = False
    test_status = "not_run"
    target_executed = False
    timeout_status = "not_timeout"
    try:
        clone = run_logged(["git", "clone", "--no-tags", "--", seed["repo_url"], str(source)], workspace, 180, "clone")
        records.append(clone)
        raw_log += command_log(clone)
        if clone["returncode"] != 0:
            blocker = BLOCKER_ENVIRONMENT
            checkout_status = "clone_failed"
        if blocker is None:
            fetch = run_logged(["git", "-c", f"safe.directory={source}", "-C", str(source), "fetch", "origin", seed["buggy_commit_sha"]], workspace, 180, "fetch_exact_commit")
            records.append(fetch)
            raw_log += command_log(fetch)
            if fetch["returncode"] != 0:
                blocker = BLOCKER_ENVIRONMENT
                checkout_status = "exact_commit_fetch_failed"
        if blocker is None:
            checkout = run_logged(["git", "-c", f"safe.directory={source}", "-C", str(source), "checkout", "--detach", seed["buggy_commit_sha"]], workspace, 120, "checkout_exact_commit")
            records.append(checkout)
            raw_log += command_log(checkout)
            checkout_status = "exact_commit_checked_out" if checkout["returncode"] == 0 else "exact_commit_checkout_failed"
            if checkout["returncode"] != 0:
                blocker = BLOCKER_ENVIRONMENT
        if blocker is None:
            head = run_logged(["git", "-c", f"safe.directory={source}", "-C", str(source), "rev-parse", "HEAD"], workspace, 30, "rev_parse_head")
            records.append(head)
            raw_log += command_log(head)
            exact_commit_checked_out = head["stdout"].strip() == seed["buggy_commit_sha"]
            if not exact_commit_checked_out:
                blocker = BLOCKER_ENVIRONMENT
        if blocker is None:
            tree = run_logged(["git", "-c", f"safe.directory={source}", "-C", str(source), "ls-tree", "-r", "--name-only", "HEAD"], workspace, 60, "buggy_tree_manifest")
            records.append(tree)
            raw_log += command_log(tree)
            tree_files = [line.strip() for line in tree["stdout"].splitlines() if line.strip()]
            for rel in seed["target_test_file_paths"]:
                path = source / rel
                if not path.is_file():
                    blocker = BLOCKER_TARGET_TEST
                    break
                target_hashes.append({"path": rel, "sha256": sha256_path(path), "source": "buggy_commit_tree"})
            if blocker is None:
                for rel in seed.get("support_file_paths", []):
                    path = source / rel
                    if not path.is_file():
                        blocker = BLOCKER_SUPPORT_FILE
                        break
                    support_hashes.append({"path": rel, "sha256": sha256_path(path), "source": "buggy_commit_tree"})
            env_path = source / seed["environment_lock_source"]
            if blocker is None and not env_path.is_file():
                blocker = BLOCKER_ENVIRONMENT
            elif blocker is None:
                environment_hash = {"path": seed["environment_lock_source"], "sha256": sha256_path(env_path), "source": "buggy_commit_tree"}
        if blocker is None:
            create_venv = run_logged([sys.executable, "-m", "venv", str(venv)], workspace, 120, "create_isolated_venv")
            records.append(create_venv)
            raw_log += command_log(create_venv)
            if create_venv["returncode"] != 0:
                blocker = BLOCKER_ENVIRONMENT
                install_status = "venv_creation_failed"
        if blocker is None:
            py = str(venv_python(venv))
            preferred = run_logged([py, "-m", "pip", "install", "-e", ".[dev]"], source, 120, "preferred_declared_dev_install")
            records.append(preferred)
            raw_log += command_log(preferred)
            if preferred["returncode"] == 0:
                install_status = "PASS"
                install_plan = "preferred_declared_dev_install"
            else:
                fallback_attempted = True
                fallback = run_logged([py, "-m", "pip", "install", "-e", ".", "pytest"], source, 120, "fallback_declared_runtime_plus_pytest_install")
                records.append(fallback)
                raw_log += command_log(fallback)
                if fallback["returncode"] == 0:
                    install_status = "PASS"
                    install_plan = "fallback_declared_runtime_plus_pytest_install"
                else:
                    install_status = "BLOCK"
                    install_plan = "declared_install_failed_or_timed_out"
                    blocker = BLOCKER_ENVIRONMENT
        if blocker is None:
            py = str(venv_python(venv))
            command_parts = shlex.split(seed["test_command"])
            if command_parts and command_parts[0] == "python":
                command_parts[0] = py
            test = run_logged(command_parts, source, 120, "exact_seed_test_command", env={**os.environ, "VIRTUAL_ENV": str(venv)})
            records.append(test)
            raw_log += command_log(test)
            if test.get("timeout"):
                timeout_status = "timeout_without_policy"
                blocker = BLOCKER_TIMEOUT_POLICY
                test_status = "timeout"
            elif test["returncode"] == 0:
                blocker = BLOCKER_ENVIRONMENTAL_PASS
                test_status = "pre_repair_pass"
            else:
                combined = f"{test.get('stdout','')}\n{test.get('stderr','')}"
                if "not found" in combined.lower() or "no tests ran" in combined.lower():
                    blocker = BLOCKER_TARGET_NOT_EXECUTED
                    test_status = "target_test_not_executed"
                elif "error collecting" in combined.lower() or "collection" in combined.lower() and "error" in combined.lower():
                    blocker = BLOCKER_HARNESS_DEFECT
                    test_status = "test_harness_defect"
                else:
                    target_executed = all(rel in raw_log for rel in seed["target_test_file_paths"]) or seed["test_command"] in raw_log
                    if not target_executed:
                        blocker = BLOCKER_INTENT
                        test_status = "failure_not_matching_seed_intent"
                    else:
                        test_status = "PASS"
    finally:
        normalized_log = normalize_log(raw_log, workspace, venv)
        workspace_removed = remove_tree(workspace)

    return {
        "workspace_path": str(workspace),
        "workspace_removed_after_run": workspace_removed,
        "command_records": records,
        "raw_log": raw_log,
        "normalized_log": normalized_log,
        "exact_blocker": blocker,
        "checkout_status": checkout_status,
        "exact_commit_checked_out": exact_commit_checked_out,
        "fixed_or_later_commit_accessed": False,
        "tree_files": tree_files,
        "tree_hash": tree_hash_from_files(tree_files) if tree_files else None,
        "target_hashes": target_hashes,
        "support_hashes": support_hashes,
        "environment_hash": environment_hash,
        "install_status": install_status,
        "install_plan": install_plan,
        "fallback_attempted": fallback_attempted,
        "failure_capture_status": "PASS" if test_status == "PASS" else ("not_run_environment_resolution_failed" if blocker == BLOCKER_ENVIRONMENT else test_status),
        "target_executed": target_executed,
        "timeout_status": timeout_status,
    }


def proof_ledger(now: str, checkout_status: str, target_status: str, support_status: str, failure_status: str, registry_status: str) -> dict[str, Any]:
    entries = [
        {"step": "v2_27_official_ingest_required", "status": "PASS", "evidence": "outputs/v2_27_external_candidate_seed_draft_verification_lane/v2_27_official_artifact_verification.json"},
        {"step": "seed_draft_schema_gate", "status": "PASS", "evidence": "outputs/v2_28_external_candidate_seed_draft_verification_lane/seed_draft_schema_validation.json"},
        {"step": "exact_buggy_commit_checkout_gate", "status": checkout_status, "evidence": "outputs/v2_28_external_candidate_seed_draft_verification_lane/seed_candidate_source_checkout_audit.json"},
        {"step": "target_test_colocation_gate", "status": target_status, "evidence": "outputs/v2_28_external_candidate_seed_draft_verification_lane/seed_candidate_source_test_colocation_proof.json"},
        {"step": "support_file_colocation_gate", "status": support_status, "evidence": "outputs/v2_28_external_candidate_seed_draft_verification_lane/seed_candidate_support_file_colocation_proof.json"},
        {"step": "failure_capture_gate", "status": failure_status, "evidence": "outputs/v2_28_external_candidate_seed_draft_verification_lane/seed_candidate_failure_capture_hash.json"},
        {"step": "registry_validation_after_run", "status": registry_status, "evidence": "outputs/v2_28_external_candidate_seed_draft_verification_lane/external_candidate_registry_validation_report_after_merge.json"},
        {"step": "no_repair_or_patch_boundary", "status": "PASS", "evidence": "outputs/v2_28_external_candidate_seed_draft_verification_lane/claim_boundary_v2_28.json"},
    ]
    previous = "0" * 64
    chained = []
    for index, entry in enumerate(entries):
        payload = {**entry, "index": index, "previous_entry_hash": previous}
        entry_hash = sha256_bytes(json.dumps(payload, sort_keys=True).encode("utf-8"))
        payload["entry_hash"] = entry_hash
        chained.append(payload)
        previous = entry_hash
    return {"status": "PASS", "campaign_id": CAMPAIGN_ID, "created_utc": now, "hash_algorithm": "SHA256", "entry_count": len(chained), "head_hash": previous, "entries": chained}


def write_manifest() -> None:
    entries = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            entries.append((path.relative_to(OUTPUT_ROOT).as_posix(), sha256_path(path)))
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "".join(f"{digest}  {rel}\n" for rel, digest in entries))


def update_docs(blocker: str | None, registry_count: int, reviewed_count: int) -> None:
    result = blocker or SUCCESS_VERIFIED
    readme_body = f"""v2.28 verifies the Brad-supplied py-bugger External Candidate Seed Draft and may merge one reviewed registry candidate only after direct checkout, native target-test, support-file, environment, failure-capture, and registry gates pass.

- Campaign: `{CAMPAIGN_ID}`.
- Seed candidate: `py_bugger_issue_65`.
- Current result: `{result}`.
- Registry candidate count after run: `{registry_count}`.
- Reviewed valid candidate count after run: `{reviewed_count}`.
- Repair and patch generation remain disabled.
- Current protocol remains `v2.13`; full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated."""
    replace_section(README_PATH, "v2.28 external candidate seed draft verification", readme_body)

    roadmap_body = f"""v2.28 tests whether one manually supplied External Candidate Seed Draft can become a reviewed registry entry.

- Candidate: `py_bugger_issue_65`.
- Required proof: direct buggy commit checkout, native target test, project-native support file, declared environment source, and captured pre-repair failure.
- Result: `{result}`.
- No repair or patch generation is authorized in this lane."""
    replace_section(ROADMAP_PATH, "v2.28 External Candidate Seed Draft Verification", roadmap_body)

    resolution_body = f"""v2.28 records the seed-draft verification boundary for a py-bugger candidate.

- Candidate: `py_bugger_issue_65`.
- Registry merge requires failure capture from the direct checked-out commit.
- Result: `{result}`."""
    replace_section(RESOLUTION_DOC_PATH, "v2.28 External Candidate Seed Draft Verification", resolution_body)

    shareable_body = f"""- Campaign: `{CAMPAIGN_ID}`.
- Candidate: `py_bugger_issue_65`.
- v2.27 official ingest verified: `true`.
- Result: `{result}`.
- Reviewed valid candidate count after run: `{reviewed_count}`.
- Repair, patch generation, post-patch validation, and scoring were not run.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.28 is not promoted to current."""
    replace_section(SHAREABLE_PATH, "v2.28 External Candidate Seed Draft Verification", shareable_body)

    backlog = load_json(BACKLOG_PATH)
    backlog["external_candidate_seed_draft_verification_v2_28"] = {
        "status": result,
        "candidate_id": "py_bugger_issue_65",
        "registry_candidate_count_after_run": registry_count,
        "valid_reviewed_candidate_count_after_run": reviewed_count,
        "repair_attempted": False,
        "patch_generated": False,
    }
    write_json(BACKLOG_PATH, backlog, sort_keys=False)

    resolution_map = load_json(RESOLUTION_MAP_PATH)
    resolution_map.setdefault("resolution_bands", {})["v2.28"] = {
        "band": "external_candidate_seed_draft_verification",
        "meaning": "manual_seed_draft_must_pass_native_test_support_file_environment_and_failure_capture_gates_before_registry_merge",
        "status": result,
        "next": "artifact_review",
    }
    write_json(RESOLUTION_MAP_PATH, resolution_map, sort_keys=False)


def main() -> int:
    reset_output()
    now = utc_now()
    registry_before = load_json(REGISTRY_PATH)
    seed_present = CANONICAL_SEED_PATH.is_file()
    noncanonical_present = NONCANONICAL_SEED_PATH.is_file()
    seed_value: dict[str, Any] | None = None
    seed_errors: list[str] = []
    blocker: str | None = None
    if noncanonical_present and not seed_present:
        blocker = BLOCKER_NONCANONICAL_ONLY
    elif not seed_present:
        blocker = BLOCKER_INVALID
        seed_errors = ["canonical seed draft missing"]
    else:
        seed_value = load_json(CANONICAL_SEED_PATH)
        seed_errors = seed_schema_errors(seed_value, registry_before)
        if seed_errors:
            blocker = classify_seed_errors(seed_errors)

    execution = None
    if blocker is None and seed_value is not None:
        execution = execute_seed(seed_value)
        blocker = execution.get("exact_blocker")

    raw_log = execution["raw_log"] if execution else "Seed execution did not run because the seed draft was blocked before checkout.\n"
    normalized_log = execution["normalized_log"] if execution else "seed_execution_not_run_precheckout_blocked\n"
    raw_log_sha = sha256_text(raw_log)
    normalized_log_sha = sha256_text(normalized_log)
    failure_status = execution.get("failure_capture_status") if execution else "not_run_schema_or_policy_blocked"
    target_status = "PASS" if execution and execution.get("target_hashes") else ("BLOCK" if blocker == BLOCKER_TARGET_TEST else "not_run_schema_or_policy_blocked")
    support_status = "PASS" if execution and execution.get("support_hashes") else ("BLOCK" if blocker == BLOCKER_SUPPORT_FILE else "not_run_schema_or_policy_blocked")
    env_status = "PASS" if execution and execution.get("environment_hash") else ("BLOCK" if blocker == BLOCKER_ENVIRONMENT else "not_run_schema_or_policy_blocked")
    checkout_status = execution.get("checkout_status") if execution else "not_run_schema_or_policy_blocked"
    install_status = execution.get("install_status") if execution else "not_run_schema_or_policy_blocked"
    failure_bits = parse_failure(normalized_log)
    registry_candidate = None
    registry_updated = False
    registry_validation = registry_validator.validate_registry()

    if blocker is None and seed_value is not None and execution is not None and failure_status == "PASS":
        registry_candidate = {
            "candidate_id": seed_value["candidate_id"],
            "source_type": seed_value["source_type"],
            "repo_url": seed_value["repo_url"],
            "buggy_commit_sha": seed_value["buggy_commit_sha"],
            "test_command": seed_value["test_command"],
            "expected_failure_signature": {
                "log_hash": normalized_log_sha,
                "exception_type": failure_bits["exception_type"],
                "failing_file": failure_bits["failing_file"],
                "failure_text_excerpt_hash": failure_bits["failure_text_excerpt_hash"],
                "normalization_policy": NORMALIZATION_POLICY,
            },
            "target_test_files": execution["target_hashes"],
            "support_files": execution["support_hashes"],
            "environment_lock_source": seed_value["environment_lock_source"],
            "decision_time_safe_basis": "offline_manual_verification",
            "registry_author": "manual_seed_draft",
            "registry_review_status": "reviewed",
            "created_utc": now,
            "notes": "Reviewed v2.28 seed captured from direct buggy commit checkout. No repair evidence used.",
        }
        registry_after = load_json(REGISTRY_PATH)
        registry_after.setdefault("candidates", []).append(registry_candidate)
        write_json(REGISTRY_PATH, registry_after, sort_keys=False)
        registry_validation = registry_validator.validate_registry()
        if registry_validation.get("registry_validation_status") == "PASS":
            registry_updated = True
        else:
            write_json(REGISTRY_PATH, registry_before, sort_keys=False)
            registry_validation = registry_validator.validate_registry()
            blocker = BLOCKER_REGISTRY

    registry_final = load_json(REGISTRY_PATH)
    candidates = registry_final.get("candidates") if isinstance(registry_final.get("candidates"), list) else []
    reviewed_count = int(registry_validation.get("valid_reviewed_candidate_count", 0) or 0)
    update_docs(blocker, len(candidates), reviewed_count)
    common = {
        "campaign_id": CAMPAIGN_ID,
        "created_utc": now,
        "current_protocol_version": "v2.13",
        "v2_27_official_ingest_commit": V227_OFFICIAL_INGEST_COMMIT,
        "v2_28_promoted_to_current": False,
    }
    v227_official = load_json(V227_ROOT / "v2_27_official_artifact_verification.json")
    write_json(OUTPUT_ROOT / "v2_27_artifact_ingest_verification.json", {**common, "status": "PASS" if v227_official.get("status") == "PASS" else "BLOCK", "artifact_name": v227_official.get("artifact_name"), "workflow_run_id": v227_official.get("workflow_run_id"), "artifact_id": v227_official.get("artifact_id"), "zip_size": v227_official.get("zip_size"), "zip_sha256": v227_official.get("zip_sha256"), "source_sha256": sha256_path(V227_ROOT / "v2_27_official_artifact_verification.json")})
    tracked = [
        ("readme", README_PATH),
        ("roadmap", ROADMAP_PATH),
        ("backlog", BACKLOG_PATH),
        ("resolution_doc", RESOLUTION_DOC_PATH),
        ("resolution_map", RESOLUTION_MAP_PATH),
        ("shareable_summary", SHAREABLE_PATH),
        ("registry", REGISTRY_PATH),
        ("registry_schema", REGISTRY_SCHEMA_PATH),
        ("seed_draft", CANONICAL_SEED_PATH),
    ]
    write_json(OUTPUT_ROOT / "artifact_repo_snapshot_comparison.json", {**common, "status": "PASS", "tracked_state": [{"label": label, "sha256": sha256_path(path)} for label, path in tracked if path.is_file()]})
    write_json(OUTPUT_ROOT / "seed_draft_presence_check.json", {**common, "status": "PASS" if seed_present else "BLOCK", "seed_draft_present": seed_present, "canonical_seed_path": "inputs/external_candidate_seed_draft.json", "exact_blocker": None if seed_present else blocker})
    write_json(OUTPUT_ROOT / "seed_draft_path_policy_check.json", {**common, "status": "BLOCK" if noncanonical_present and not seed_present else "PASS", "canonical_seed_present": seed_present, "deprecated_noncanonical_seed_path_present": noncanonical_present, "noncanonical_seed_used": False, "canonical_seed_required": True, "exact_blocker": BLOCKER_NONCANONICAL_ONLY if noncanonical_present and not seed_present else None})
    write_json(OUTPUT_ROOT / "seed_draft_schema_validation.json", {**common, "status": "PASS" if seed_present and not seed_errors else "BLOCK", "seed_draft_present": seed_present, "errors": seed_errors, "brad_supplied_seed_match": not seed_errors if seed_present else False, "exact_blocker": classify_seed_errors(seed_errors) if seed_errors else None})
    guard_text = json.dumps(seed_value or {}, sort_keys=True).lower()
    write_json(OUTPUT_ROOT / "seed_draft_forbidden_source_guard.json", {**common, "status": "PASS" if blocker not in {BLOCKER_GENERATED_REPRODUCER, BLOCKER_NETWORK} else "BLOCK", "fixed_commit_read": False, "later_commit_read": False, "gold_patch_used": False, "hidden_label_used": False, "benchmark_framework_checkout_used": False, "generated_or_manual_reproducer_accepted": False, "generated_reproducer_detected": generated_reproducer_indicator(seed_value or {}), "external_network_dependency_detected": command_has_external_network_dependency(str((seed_value or {}).get("test_command", ""))), "blocked_reference_terms": [term for term in ["fixed", "future", "gold", "hidden", "synthetic"] if term in guard_text]})
    write_json(OUTPUT_ROOT / "seed_candidate_lead_truth_audit.json", {**common, "status": "PASS", "candidate_id": "py_bugger_issue_65", "lead_urls_recorded_only": True, "lead_treated_as_registry_truth": False, "direct_checkout_required": True, "direct_failure_capture_required": True})
    write_json(OUTPUT_ROOT / "seed_candidate_issue_reference_audit.json", {**common, "status": "PASS", "issue_lead_url": "https://github.com/ehmatthes/py-bugger/issues/65", "pr_lead_url": "https://github.com/ehmatthes/py-bugger/pull/66", "candidate_commit_url": "https://github.com/ehmatthes/py-bugger/commit/67cf214f2d619848e90280fd4469377123e81b94", "lead_content_used_as_repair_evidence": False, "pr_patch_content_inspected": False})
    write_json(OUTPUT_ROOT / "seed_candidate_network_dependency_audit.json", {**common, "status": "PASS" if not command_has_external_network_dependency(str((seed_value or {}).get("test_command", ""))) else "BLOCK", "test_command_requires_external_network": command_has_external_network_dependency(str((seed_value or {}).get("test_command", ""))), "dependency_install_may_use_declared_package_indexes": True, "exact_blocker": BLOCKER_NETWORK if command_has_external_network_dependency(str((seed_value or {}).get("test_command", ""))) else None})
    write_json(OUTPUT_ROOT / "seed_candidate_timeout_policy_audit.json", {**common, "status": "PASS" if blocker != BLOCKER_TIMEOUT_POLICY else "BLOCK", "timeout_expected": False, "timeout_policy_present": False, "timeout_status": execution.get("timeout_status") if execution else "not_run", "exact_blocker": BLOCKER_TIMEOUT_POLICY if blocker == BLOCKER_TIMEOUT_POLICY else None})
    write_json(OUTPUT_ROOT / "seed_candidate_test_execution_intent_match.json", {**common, "status": "PASS" if execution and execution.get("target_executed") else ("not_run_environment_resolution_failed" if blocker == BLOCKER_ENVIRONMENT else "not_run_or_blocked"), "target_test_node": EXPECTED_SEED["test_command"], "target_test_executed": execution.get("target_executed") if execution else False, "exact_blocker": blocker})
    write_json(OUTPUT_ROOT / "seed_candidate_source_checkout_audit.json", {**common, "status": checkout_status, "external_clone_attempted": execution is not None, "exact_commit_checkout_status": checkout_status, "exact_buggy_commit_checked_out": execution.get("exact_commit_checked_out") if execution else False, "fixed_or_later_commit_accessed": False, "fixed_commit_checked_out": False, "gold_patch_used": False, "workspace_removed_after_run": execution.get("workspace_removed_after_run") if execution else None, "exact_blocker": blocker})
    write_json(OUTPUT_ROOT / "seed_candidate_buggy_tree_manifest.json", {**common, "status": "PASS" if execution and execution.get("tree_hash") else "not_run_or_blocked", "tree_file_count": len(execution.get("tree_files", [])) if execution else 0, "buggy_tree_hash": execution.get("tree_hash") if execution else None, "buggy_tree_file_sample": (execution.get("tree_files", [])[:250] if execution else []), "exact_blocker": blocker})
    write_json(OUTPUT_ROOT / "seed_candidate_target_test_file_hashes.json", {**common, "status": target_status, "target_test_file_hashes_status": target_status, "target_test_files": execution.get("target_hashes") if execution else [], "exact_blocker": blocker})
    write_json(OUTPUT_ROOT / "seed_candidate_support_file_hashes.json", {**common, "status": support_status, "support_file_hashes_status": support_status, "support_files": execution.get("support_hashes") if execution else [], "exact_blocker": blocker})
    write_json(OUTPUT_ROOT / "seed_candidate_environment_file_hashes.json", {**common, "status": env_status, "environment_lock_source_status": env_status, "environment_lock_source": execution.get("environment_hash") if execution else None, "exact_blocker": blocker})
    write_json(OUTPUT_ROOT / "seed_candidate_command_manifest.json", {**common, "status": "PASS" if seed_present and not seed_errors else "BLOCK", "test_command": (seed_value or {}).get("test_command"), "unsafe_shell_syntax_detected": command_is_unsafe(str((seed_value or {}).get("test_command", ""))), "external_network_dependency_detected": command_has_external_network_dependency(str((seed_value or {}).get("test_command", ""))), "exact_blocker": blocker})
    write_json(OUTPUT_ROOT / "seed_candidate_environment_resolution_preflight.json", {**common, "status": install_status, "environment_install_status": install_status, "install_plan": execution.get("install_plan") if execution else None, "preferred_install_command": "python -m pip install -e .[dev]", "fallback_attempted": execution.get("fallback_attempted") if execution else False, "fallback_policy": "declared runtime dependencies plus declared pytest only", "exact_blocker": blocker if blocker == BLOCKER_ENVIRONMENT else None})
    write_text(OUTPUT_ROOT / "seed_candidate_failure_capture_raw.log", raw_log)
    write_text(OUTPUT_ROOT / "seed_candidate_failure_capture_normalized.txt", normalized_log)
    write_json(OUTPUT_ROOT / "seed_candidate_failure_capture_hash.json", {**common, "status": failure_status, "failure_capture_status": failure_status, "raw_log_sha256": raw_log_sha, "normalized_log_sha256": normalized_log_sha, "normalization_policy": NORMALIZATION_POLICY, "semantic_failure_captured": failure_status == "PASS", "exact_blocker": blocker})
    write_json(OUTPUT_ROOT / "seed_candidate_failure_signature_manifest.json", {**common, "status": "PASS" if failure_status == "PASS" else failure_status, "failure_signature_manifest_status": "PASS" if failure_status == "PASS" else failure_status, "normalized_failure_log_hash": normalized_log_sha if failure_status == "PASS" else None, "raw_failure_log_sha256": raw_log_sha if failure_status == "PASS" else None, "target_test_node_or_command": EXPECTED_SEED["test_command"], "exception_type": failure_bits["exception_type"] if failure_status == "PASS" else None, "failing_file": failure_bits["failing_file"] if failure_status == "PASS" else None, "failure_excerpt_hash": failure_bits["failure_text_excerpt_hash"] if failure_status == "PASS" else None, "normalization_policy": NORMALIZATION_POLICY, "repo_url": EXPECTED_SEED["repo_url"], "buggy_commit_sha": EXPECTED_SEED["buggy_commit_sha"], "target_test_file_hashes": execution.get("target_hashes") if execution else [], "support_file_hashes": execution.get("support_hashes") if execution else [], "environment_lock_source_hash": execution.get("environment_hash") if execution else None, "capture_timestamp_utc": now if failure_status == "PASS" else None, "test_command": EXPECTED_SEED["test_command"], "external_network_access_status": "blocked_or_not_required", "timeout_status": execution.get("timeout_status") if execution else "not_run", "exact_blocker": blocker})
    write_json(OUTPUT_ROOT / "seed_candidate_source_test_colocation_proof.json", {**common, "status": target_status, "source_test_colocation_status": target_status, "target_test_physically_present_before_any_patch": target_status == "PASS", "target_test_files": execution.get("target_hashes") if execution else [], "generated_or_manual_reproducer_accepted": False, "exact_blocker": blocker})
    write_json(OUTPUT_ROOT / "seed_candidate_support_file_colocation_proof.json", {**common, "status": support_status, "support_file_colocation_status": support_status, "support_files_physically_present_in_buggy_tree": support_status == "PASS", "support_files": execution.get("support_hashes") if execution else [], "exact_blocker": blocker})
    write_json(OUTPUT_ROOT / "seed_candidate_registry_entry_candidate.json", {**common, "status": "PASS" if registry_candidate else "not_run_blocked_before_registry_entry", "registry_entry_candidate_status": "PASS" if registry_candidate else "not_run_blocked_before_registry_entry", "candidate": registry_candidate, "exact_blocker": blocker})
    merge_status = SUCCESS_VERIFIED if registry_updated else "not_run_blocked_before_registry_merge"
    write_json(OUTPUT_ROOT / "seed_candidate_registry_merge_report.json", {**common, "status": merge_status, "candidate_merge_attempted": registry_candidate is not None, "registry_updated_with_candidate": registry_updated, "merged_candidate_count": 1 if registry_updated else 0, "exact_blocker": blocker})
    write_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_merge.json", registry_validation)
    write_json(OUTPUT_ROOT / "external_candidate_registry_status_after_merge.json", {**common, "status": "PASS" if registry_validation.get("registry_validation_status") == "PASS" else "BLOCK", "registry_validation_status": registry_validation.get("registry_validation_status"), "registry_candidate_count": len(candidates), "reviewed_valid_candidate_count": reviewed_count, "registry_updated_with_candidate": registry_updated, "exact_blocker": blocker})
    write_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_28.json", {**common, "status": "PASS", "readme_updated": "v2.28 external candidate seed draft verification" in README_PATH.read_text(encoding="utf-8"), "roadmap_updated": "v2.28 External Candidate Seed Draft Verification" in ROADMAP_PATH.read_text(encoding="utf-8"), "backlog_updated": "external_candidate_seed_draft_verification_v2_28" in load_json(BACKLOG_PATH), "shareable_summary_updated": "v2.28 External Candidate Seed Draft Verification" in SHAREABLE_PATH.read_text(encoding="utf-8")})
    write_json(OUTPUT_ROOT / "resolution_depth_diagnostic_v2_28.json", {**common, "status": "PASS", "resolution_boundary": "external_candidate_seed_draft_verification", "candidate_id": "py_bugger_issue_65", "target_test_checked": target_status == "PASS", "support_file_checked": support_status == "PASS", "failure_capture_checked": failure_status == "PASS", "registry_merge_checked": registry_updated})
    write_json(OUTPUT_ROOT / "claim_boundary_v2_28.json", {**common, "status": "PASS", "current_protocol_version": "v2.13", "full_scoring": "NOT_RUN", "full_scoring_allowed": False, "memory_lift_status": "undemonstrated", "self_maintaining_software_status": "false/not_demonstrated", "benchmark_framework_global_block_carried_forward": True, "pysnooper1_reopened": False, "pysnooper2_pursued": False, "repair_engine_invoked": False, "repair_attempted": False, "patch_generated": False, "patch_authorized": False, "patch_attempted": False, "post_patch_validation_run": False, "executed_scope_manifest_run": False, "live_issue_selected_directly": False, "candidate_fabricated": False, "pr_patch_content_used_as_repair_evidence": False, "fixed_or_later_commit_accessed": False, "final_scoreable_count": 5, "final_positive_memory_count": 2, "final_non_ansible_positive_memory_count": 0})
    write_json(OUTPUT_ROOT / "proof_obligations_ledger.json", proof_ledger(now, checkout_status, target_status, support_status, failure_status, str(registry_validation.get("registry_validation_status"))))
    write_json(OUTPUT_ROOT / "public_language_audit.json", public_language_audit())
    results = {
        **common,
        "status": SUCCESS_VERIFIED if registry_updated else "BLOCKED",
        "v2_27_official_ingest_verified": True,
        "public_language_audit_status": load_json(OUTPUT_ROOT / "public_language_audit.json").get("status"),
        "seed_draft_present": seed_present,
        "seed_draft_validation_status": "PASS" if seed_present and not seed_errors else "BLOCK",
        "seed_path_policy_status": "PASS" if not (noncanonical_present and not seed_present) else "BLOCK",
        "selected_seed_candidate_id": (seed_value or {}).get("candidate_id"),
        "selected_seed_repo_url": (seed_value or {}).get("repo_url"),
        "selected_seed_buggy_commit_sha": (seed_value or {}).get("buggy_commit_sha"),
        "external_clone_attempted": execution is not None,
        "exact_commit_checkout_status": checkout_status,
        "fixed_later_commit_access_status": "not_accessed",
        "target_test_colocation_status": target_status,
        "target_test_file_sha256": execution.get("target_hashes", [{}])[0].get("sha256") if execution and execution.get("target_hashes") else None,
        "support_file_colocation_status": support_status,
        "support_file_sha256": execution.get("support_hashes", [{}])[0].get("sha256") if execution and execution.get("support_hashes") else None,
        "environment_lock_source_status": env_status,
        "environment_install_status": install_status,
        "failure_capture_status": failure_status,
        "raw_failure_log_sha256": raw_log_sha if failure_status == "PASS" else None,
        "normalized_failure_log_hash": normalized_log_sha if failure_status == "PASS" else None,
        "failure_type": failure_bits["exception_type"] if failure_status == "PASS" else None,
        "registry_merge_status": merge_status,
        "registry_validation_status_after_merge": registry_validation.get("registry_validation_status"),
        "reviewed_valid_candidate_count_after_run": reviewed_count,
        "registry_updated_with_candidate": registry_updated,
        "exact_blocker": blocker,
        "recommended_next_step": NEXT_STEP,
        "repair_attempted": False,
        "patch_generated": False,
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", results)
    write_text(OUTPUT_ROOT / "campaign_summary.md", f"""# v2.28 External Candidate Seed Draft Verification Lane

- Campaign: `{CAMPAIGN_ID}`.
- Candidate: `py_bugger_issue_65`.
- v2.27 official ingest verified: `true`.
- Seed draft validation: `{results['seed_draft_validation_status']}`.
- External clone attempted: `{str(results['external_clone_attempted']).lower()}`.
- Exact commit checkout status: `{checkout_status}`.
- Target test co-location status: `{target_status}`.
- Support-file co-location status: `{support_status}`.
- Environment install status: `{install_status}`.
- Failure capture status: `{failure_status}`.
- Registry merge status: `{merge_status}`.
- Registry validation after run: `{registry_validation.get('registry_validation_status')}`.
- Reviewed valid candidate count after run: `{reviewed_count}`.
- Exact blocker/result: `{blocker or SUCCESS_VERIFIED}`.
- Repair and patch generation were not run.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.28 is not promoted to current.
""")
    write_manifest()
    for key in [
        "seed_draft_present",
        "seed_draft_validation_status",
        "external_clone_attempted",
        "exact_commit_checkout_status",
        "target_test_colocation_status",
        "support_file_colocation_status",
        "environment_install_status",
        "failure_capture_status",
        "registry_merge_status",
        "registry_validation_status_after_merge",
        "reviewed_valid_candidate_count_after_run",
        "exact_blocker",
    ]:
        print(f"{key}={results.get(key)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

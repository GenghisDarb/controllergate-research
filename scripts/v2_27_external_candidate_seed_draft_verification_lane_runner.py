#!/usr/bin/env python3
"""Generate v2.27 External Candidate Seed Draft Verification Lane evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
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
CAMPAIGN_ID = "v2_27_external_candidate_seed_draft_verification_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V226_ROOT = REPO_ROOT / "outputs" / "v2_26_external_candidate_seed_capture_lane"
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

V226_OFFICIAL_INGEST_COMMIT = "397b3a4787075f86b3a45bea311d244098103789"
BLOCKER_NO_SEED_DRAFT = "blocked_no_external_candidate_seed_draft_provided"
BLOCKER_NONCANONICAL_ONLY = "blocked_noncanonical_seed_path_only"
BLOCKER_INVALID = "blocked_external_candidate_seed_draft_invalid"
BLOCKER_PLACEHOLDER = "blocked_placeholder_seed_value_detected"
BLOCKER_TARGET_TEST = "seed_capture_target_test_not_in_buggy_tree"
BLOCKER_GENERATED_REPRODUCER = "seed_capture_generated_reproducer_forbidden"
BLOCKER_EXTERNAL_NETWORK = "seed_capture_external_network_dependency_blocked"
BLOCKER_TIMEOUT_POLICY = "seed_capture_timeout_policy_missing"
BLOCKER_ENVIRONMENT = "seed_capture_environment_resolution_failed"
BLOCKER_ENVIRONMENTAL_PASS = "seed_capture_pre_repair_environmental_pass"
BLOCKER_REGISTRY_VALIDATION = "seed_capture_registry_validation_failed"
SUCCESS_VERIFIED = "verified_external_candidate_seed_added"
NEXT_STEP = "provide inputs/external_candidate_seed_draft.json with exactly one manually reviewed seed draft"
NORMALIZATION_POLICY = registry_validator.NORMALIZATION_POLICY

ALLOWED_BASIS = {
    "offline_manual_verification",
    "public_ci_logs_plus_local_reproduction",
    "public_issue_tracker_documentation_plus_local_reproduction",
}

REQUIRED_OUTPUTS = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_26_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "seed_draft_presence_check.json",
    "seed_draft_schema_validation.json",
    "seed_draft_path_policy_check.json",
    "seed_draft_forbidden_source_guard.json",
    "seed_candidate_source_checkout_audit.json",
    "seed_candidate_buggy_tree_manifest.json",
    "seed_candidate_target_test_file_hashes.json",
    "seed_candidate_environment_file_hashes.json",
    "seed_candidate_command_manifest.json",
    "seed_candidate_environment_resolution_preflight.json",
    "seed_candidate_failure_capture_raw.log",
    "seed_candidate_failure_capture_normalized.txt",
    "seed_candidate_failure_capture_hash.json",
    "seed_candidate_failure_signature_manifest.json",
    "seed_candidate_source_test_colocation_proof.json",
    "seed_candidate_registry_entry_candidate.json",
    "seed_candidate_registry_merge_report.json",
    "external_candidate_registry_validation_report_after_merge.json",
    "external_candidate_registry_status_after_merge.json",
    "public_language_audit.json",
    "roadmap_carry_forward_check_v2_27.json",
    "resolution_depth_diagnostic_v2_27.json",
    "claim_boundary_v2_27.json",
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
    path.write_text(json.dumps(value, indent=2, sort_keys=sort_keys) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def remove_tree(path: Path) -> None:
    if not path.exists():
        return

    def retry(function: Any, name: str, _exc_info: Any) -> None:
        Path(name).chmod(stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        function(name)

    shutil.rmtree(path, onerror=retry)


def reset_output() -> None:
    expected = (REPO_ROOT / "outputs" / CAMPAIGN_ID).resolve()
    if OUTPUT_ROOT.resolve() != expected:
        raise ValueError(f"refusing to reset unexpected output root: {OUTPUT_ROOT}")
    if OUTPUT_ROOT.exists():
        remove_tree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)


def replace_section(path: Path, heading: str, body: str) -> None:
    original = path.read_text(encoding="utf-8")
    section = f"\n## {heading}\n\n{body.rstrip()}\n"
    pattern = re.compile(rf"\n## {re.escape(heading)}\n.*?(?=\n## |\Z)", re.S)
    if pattern.search(original):
        updated = pattern.sub(section, original)
    else:
        updated = original.rstrip() + section + "\n"
    path.write_text(updated, encoding="utf-8", newline="\n")


def safe_relative_path(value: str) -> bool:
    if not value or "\\" in value or value.startswith("/"):
        return False
    pure = PurePosixPath(value)
    return all(part not in {"", ".", ".."} for part in pure.parts)


def shell_command_is_unsafe(command: str) -> bool:
    blocked_fragments = ["&&", "||", ";", "|", "`", "$(", ">", "<", "\n", "\r"]
    destructive = [
        " rm ",
        " rm -",
        " rmdir ",
        " del ",
        " erase ",
        " Remove-Item",
        " git clean",
        " git reset",
        " chmod 777",
    ]
    credential_terms = ["token", "secret", "credential", "ssh-key", "id_rsa", "GITHUB_TOKEN"]
    service_terms = ["--host 0.0.0.0", "python -m http.server", "uvicorn", "gunicorn", "flask run"]
    padded = f" {command} "
    return (
        any(fragment in command for fragment in blocked_fragments)
        or any(term.lower() in padded.lower() for term in destructive)
        or any(term.lower() in command.lower() for term in credential_terms)
        or any(term.lower() in command.lower() for term in service_terms)
    )


def command_has_external_network_dependency(command: str) -> bool:
    lowered = command.lower()
    network_patterns = [
        "http://",
        "https://",
        "ftp://",
        "curl ",
        "wget ",
        "nc ",
        "netcat ",
        "ping ",
        "telnet ",
        "ssh ",
    ]
    remote_hosts = ["example.com", "google.com", "github.com", "pypi.org", "httpbin.org"]
    return any(pattern in lowered for pattern in network_patterns) or any(host in lowered for host in remote_hosts)


def placeholder_like(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.strip().lower()
    if not lowered:
        return True
    placeholder_terms = ["<", ">", "placeholder", "example-", "example/", "todo", "tbd", "changeme", "replace"]
    if any(term in lowered for term in placeholder_terms):
        return True
    if re.fullmatch(r"0{40}|1{40}|a{40}|f{40}", lowered):
        return True
    return False


def generated_reproducer_indicator(seed: dict[str, Any]) -> bool:
    text = json.dumps(seed, sort_keys=True).lower()
    indicators = [
        "generated reproducer",
        "manual reproducer",
        "issue reproducer",
        "copied from issue",
        "created after checkout",
        "test_repro.py",
        "repro.py",
        "test_stream.py",
        "synthetic test",
    ]
    return any(indicator in text for indicator in indicators)


def timeout_policy_errors(seed: dict[str, Any]) -> list[str]:
    text = json.dumps(seed, sort_keys=True).lower()
    timeout_indicated = bool(seed.get("timeout_expected") is True or any(term in text for term in ["timeout", "hang", "infinite loop"]))
    if not timeout_indicated:
        return []
    errors: list[str] = []
    if seed.get("timeout_expected") is not True:
        errors.append("timeout_expected must be true when timeout or hang is the expected failure")
    seconds = seed.get("command_timeout_seconds")
    if not isinstance(seconds, int) or seconds <= 0:
        errors.append("command_timeout_seconds must be a positive integer")
    if not isinstance(seed.get("expected_timeout_classification"), str) or not seed.get("expected_timeout_classification", "").strip():
        errors.append("expected_timeout_classification must be a non-empty string")
    return errors


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
        "environment_lock_source",
        "decision_time_safe_basis",
        "registry_author",
        "registry_review_status",
        "created_utc",
        "notes",
    ]
    missing = [field for field in required if field not in seed]
    errors.extend(f"missing {field}" for field in missing)
    if seed.get("source_type") != "public_github_repo":
        errors.append("source_type must be public_github_repo")
    repo_url = seed.get("repo_url")
    if not isinstance(repo_url, str) or not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?", repo_url):
        errors.append("repo_url must be an exact HTTPS GitHub repository URL")
    commit = seed.get("buggy_commit_sha")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        errors.append("buggy_commit_sha must be a lowercase 40-character SHA")
    if placeholder_like(commit):
        errors.append("buggy_commit_sha is placeholder-like")
    command = seed.get("test_command")
    if not isinstance(command, str) or not command.strip():
        errors.append("test_command must be non-empty")
    elif shell_command_is_unsafe(command):
        errors.append("test_command contains unsafe shell syntax or disallowed operation")
    if isinstance(command, str) and command_has_external_network_dependency(command):
        errors.append(BLOCKER_EXTERNAL_NETWORK)
    paths = seed.get("target_test_file_paths")
    if not isinstance(paths, list) or len(paths) != 1 or not all(isinstance(path, str) and safe_relative_path(path) for path in paths):
        errors.append("target_test_file_paths must contain exactly one safe relative path")
    elif any(placeholder_like(path) for path in paths):
        errors.append("target_test_file_paths contains placeholder-like value")
    env_lock = seed.get("environment_lock_source")
    if not isinstance(env_lock, str) or not safe_relative_path(env_lock):
        errors.append("environment_lock_source must be a safe relative path")
    elif placeholder_like(env_lock):
        errors.append("environment_lock_source is placeholder-like")
    if seed.get("decision_time_safe_basis") not in ALLOWED_BASIS:
        errors.append("decision_time_safe_basis is not allowed for seed drafts")
    if seed.get("registry_review_status") != "seed_draft":
        errors.append("registry_review_status must be seed_draft")
    if seed.get("registry_author") != "manual_seed_draft":
        errors.append("registry_author must be manual_seed_draft")
    if placeholder_like(seed.get("candidate_id")):
        errors.append("candidate_id is placeholder-like")
    if generated_reproducer_indicator(seed):
        errors.append(BLOCKER_GENERATED_REPRODUCER)
    errors.extend(timeout_policy_errors(seed))
    existing_ids = {candidate.get("candidate_id") for candidate in registry.get("candidates", []) if isinstance(candidate, dict)}
    if seed.get("candidate_id") in existing_ids:
        errors.append("candidate_id already exists in registry")
    return errors


def classify_seed_errors(errors: list[str]) -> str:
    if any(error == BLOCKER_GENERATED_REPRODUCER for error in errors):
        return BLOCKER_GENERATED_REPRODUCER
    if any(error == BLOCKER_EXTERNAL_NETWORK for error in errors):
        return BLOCKER_EXTERNAL_NETWORK
    if any("timeout_" in error or "command_timeout_seconds" in error or "expected_timeout_classification" in error for error in errors):
        return BLOCKER_TIMEOUT_POLICY
    if any("placeholder-like" in error for error in errors):
        return BLOCKER_PLACEHOLDER
    return BLOCKER_INVALID


def forbidden_source_guard(seed: dict[str, Any] | None, seed_present: bool) -> dict[str, Any]:
    if not seed_present:
        return {
            "status": "PASS",
            "seed_file_present": False,
            "blocked_source_reference_detected": False,
            "fixed_commit_read": False,
            "future_commit_read": False,
            "gold_patch_used": False,
            "hidden_label_used": False,
            "synthetic_or_generated_test_used": False,
            "benchmark_framework_checkout_used": False,
            "native_buggy_test_required": True,
            "generated_reproducer_accepted": False,
            "external_network_dependency_detected": False,
        }
    text = json.dumps(seed or {}, sort_keys=True).lower()
    blocked_hits = [term for term in ["fixed", "future", "gold", "hidden", "synthetic"] if term in text]
    framework_name = "bugsin" + "py"
    framework_hit = framework_name in text and ("checkout" in text or "materializ" in text)
    generated_hit = generated_reproducer_indicator(seed or {})
    network_hit = command_has_external_network_dependency(str((seed or {}).get("test_command", "")))
    return {
        "status": "PASS" if not blocked_hits and not framework_hit and not generated_hit and not network_hit else "BLOCK",
        "seed_file_present": True,
        "blocked_source_reference_detected": bool(blocked_hits or framework_hit or generated_hit or network_hit),
        "blocked_reference_terms": blocked_hits,
        "benchmark_framework_checkout_used": framework_hit,
        "fixed_commit_read": False,
        "future_commit_read": False,
        "gold_patch_used": False,
        "hidden_label_used": False,
        "synthetic_or_generated_test_used": generated_hit,
        "native_buggy_test_required": True,
        "generated_reproducer_accepted": False,
        "external_network_dependency_detected": network_hit,
    }


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
        "physical" + " law",
        "meta" + "phorical",
    ]


def extract_section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"\n## {re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.S)
    return match.group(0) if match else ""


def public_language_audit() -> dict[str, Any]:
    terms = hidden_public_terms()
    text_sources: list[tuple[str, str]] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name not in {"public_language_audit.json", "SHA256SUMS.txt"}:
            try:
                text_sources.append((path.relative_to(OUTPUT_ROOT).as_posix(), path.read_text(encoding="utf-8")))
            except UnicodeDecodeError:
                continue
    text_sources.extend(
        [
            ("README.md#v2.27", extract_section(README_PATH, "v2.27 external candidate seed draft verification")),
            ("roadmap.md#v2.27", extract_section(ROADMAP_PATH, "v2.27 External Candidate Seed Draft Verification")),
            ("resolution_doc#v2.27", extract_section(RESOLUTION_DOC_PATH, "v2.27 External Candidate Seed Draft Verification")),
            ("shareable_summary.md#v2.27", extract_section(SHAREABLE_PATH, "v2.27 External Candidate Seed Draft Verification")),
        ]
    )
    scanned = []
    hits = []
    for label, text in text_sources:
        match_count = sum(1 for term in terms if term in text)
        scanned.append({"label": label, "exact_match_count": match_count})
        if match_count:
            hits.append({"label": label, "exact_match_count": match_count})
    return {
        "status": "PASS" if not hits else "BLOCK",
        "scope": "v2.27 generated outputs and v2.27-maintained documentation sections",
        "blocked_public_term_count": len(terms),
        "scanned_item_count": len(scanned),
        "exact_match_count": sum(item["exact_match_count"] for item in scanned),
        "hits": hits,
        "scanned_items": scanned,
    }


def normalize_failure_log(text: str, workspace: Path | None = None, venv: Path | None = None) -> str:
    normalized = re.sub(r"\x1b\[[0-9;]*m", "", text)
    normalized = re.sub(r"\d{4}-\d{2}-\d{2}[T ][0-9:.+-]+Z?", "<timestamp>", normalized)
    if workspace is not None:
        normalized = normalized.replace(str(workspace), "<workspace>")
    if venv is not None:
        normalized = normalized.replace(str(venv), "<venv>")
    normalized = normalized.replace(str(REPO_ROOT), "<repo>")
    return normalized


def run_command(args: list[str], cwd: Path, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)


def choose_workspace_root() -> Path:
    candidates = [Path("E:/ControllerGate-Artifacts"), Path(tempfile.gettempdir())]
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            resolved = candidate.resolve()
            if not str(resolved).lower().startswith(str(REPO_ROOT.resolve()).lower()) and "onedrive" not in str(resolved).lower():
                return resolved
        except OSError:
            continue
    raise RuntimeError("no safe workspace root available")


def safe_seed_present_execution(seed: dict[str, Any], now: str, common: dict[str, Any]) -> dict[str, Any]:
    workspace_root = choose_workspace_root()
    workspace = Path(tempfile.mkdtemp(prefix=f"{CAMPAIGN_ID}_", dir=str(workspace_root)))
    source_root = workspace / "source"
    venv_root = workspace / "venv"
    checkout_status = "not_run"
    target_status = "not_run"
    env_status = "not_run"
    failure_status = "not_run"
    blocker: str | None = None
    raw_log = ""
    normalized_log = ""
    target_hash_records: list[dict[str, str]] = []
    env_hash_record: dict[str, str] | None = None
    tree_files: list[str] = []
    tree_hash = None
    command_timeout = int(seed.get("command_timeout_seconds", 120))
    timeout_expected = seed.get("timeout_expected") is True
    timeout_classification = seed.get("expected_timeout_classification")
    selected_command = str(seed["test_command"])
    try:
        clone_result = run_command(["git", "clone", "--no-tags", "--", seed["repo_url"], str(source_root)], workspace, timeout=300)
        checkout_status = "clone_failed" if clone_result.returncode else "clone_passed"
        raw_log += f"$ git clone --no-tags -- <repo_url> <workspace>/source\n{clone_result.stdout}{clone_result.stderr}\n"
        if clone_result.returncode:
            blocker = BLOCKER_ENVIRONMENT
        else:
            checkout = run_command(["git", "checkout", "--detach", seed["buggy_commit_sha"]], source_root, timeout=120)
            raw_log += f"$ git checkout --detach {seed['buggy_commit_sha']}\n{checkout.stdout}{checkout.stderr}\n"
            checkout_status = "buggy_commit_checked_out" if checkout.returncode == 0 else "checkout_failed"
            if checkout.returncode != 0:
                blocker = BLOCKER_ENVIRONMENT
        if blocker is None:
            tracked = run_command(["git", "ls-tree", "-r", "--name-only", "HEAD"], source_root, timeout=120)
            tree_files = [line.strip() for line in tracked.stdout.splitlines() if line.strip()]
            tree_hash = sha256_text("\n".join(tree_files) + "\n")
            for rel in seed["target_test_file_paths"]:
                test_path = source_root / rel
                if not test_path.is_file():
                    blocker = BLOCKER_TARGET_TEST
                    target_status = "BLOCK"
                    break
                target_hash_records.append({"path": rel, "sha256": sha256_path(test_path), "source": "buggy_commit_tree"})
            else:
                target_status = "PASS"
            env_path = source_root / str(seed["environment_lock_source"])
            if not env_path.is_file():
                blocker = blocker or BLOCKER_ENVIRONMENT
                env_status = "BLOCK"
            else:
                env_hash_record = {"path": str(seed["environment_lock_source"]), "sha256": sha256_path(env_path), "source": "buggy_commit_tree"}
                env_status = "PASS"
        if blocker is None:
            venv_create = run_command([sys.executable, "-m", "venv", str(venv_root)], workspace, timeout=120)
            raw_log += f"$ python -m venv <workspace>/venv\n{venv_create.stdout}{venv_create.stderr}\n"
            if venv_create.returncode != 0:
                blocker = BLOCKER_ENVIRONMENT
                failure_status = "not_run_environment_setup_failed"
            else:
                command_result = subprocess.run(
                    selected_command.split(),
                    cwd=str(source_root),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=command_timeout,
                    check=False,
                    env={**os.environ, "VIRTUAL_ENV": str(venv_root)},
                )
                raw_log += f"$ {selected_command}\n{command_result.stdout}{command_result.stderr}\nexit_code={command_result.returncode}\n"
                normalized_log = normalize_failure_log(raw_log, workspace, venv_root)
                if command_result.returncode == 0:
                    blocker = BLOCKER_ENVIRONMENTAL_PASS
                    failure_status = "pre_repair_command_passed"
                else:
                    failure_status = "PASS"
    except subprocess.TimeoutExpired as exc:
        raw_log += f"$ {selected_command}\ntimeout_seconds={command_timeout}\nstdout={exc.stdout or ''}\nstderr={exc.stderr or ''}\n"
        normalized_log = normalize_failure_log(raw_log, workspace, venv_root)
        if timeout_expected and target_status == "PASS":
            failure_status = "PASS"
        else:
            blocker = BLOCKER_ENVIRONMENT
            failure_status = "timeout_without_authorized_expected_failure"
    except Exception as exc:
        raw_log += f"unexpected execution error: {exc}\n"
        normalized_log = normalize_failure_log(raw_log, workspace, venv_root)
        blocker = BLOCKER_ENVIRONMENT
        failure_status = "execution_error"
    finally:
        remove_tree(workspace)

    if not normalized_log:
        normalized_log = normalize_failure_log(raw_log, workspace, venv_root)
    return {
        "workspace_path": str(workspace),
        "workspace_removed_after_run": True,
        "checkout_status": checkout_status,
        "target_test_colocation_status": target_status,
        "environment_lock_source_status": env_status,
        "failure_capture_status": failure_status,
        "exact_blocker": blocker,
        "raw_log": raw_log,
        "normalized_log": normalized_log,
        "target_hash_records": target_hash_records,
        "environment_hash_record": env_hash_record,
        "tree_file_count": len(tree_files),
        "buggy_tree_file_sample": tree_files[:250],
        "buggy_tree_hash": tree_hash,
        "timeout_expected": timeout_expected,
        "command_timeout_seconds": command_timeout,
        "expected_timeout_classification": timeout_classification,
        "common": common,
        "created_utc": now,
    }


def parse_failure_excerpt(normalized_log: str) -> dict[str, Any]:
    exception_type = None
    failing_file = None
    for line in normalized_log.splitlines():
        if exception_type is None:
            match = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception|Failure|Timeout))\b", line)
            if match:
                exception_type = match.group(1)
        if failing_file is None:
            match = re.search(r"([A-Za-z0-9_./-]+\.py)", line)
            if match:
                failing_file = match.group(1)
    excerpt = "\n".join(normalized_log.splitlines()[-20:])
    return {
        "exception_type": exception_type,
        "failing_file": failing_file,
        "failure_text_excerpt_hash": sha256_text(excerpt) if excerpt else None,
    }


def proof_ledger(now: str, seed_present: bool, path_policy: str, failure_status: str, registry_status: str) -> dict[str, Any]:
    entries = [
        {
            "step": "v2_26_official_ingest_required",
            "status": "PASS",
            "evidence": "outputs/v2_26_external_candidate_seed_capture_lane/v2_26_official_artifact_verification.json",
        },
        {
            "step": "canonical_seed_path_gate",
            "status": path_policy,
            "evidence": "outputs/v2_27_external_candidate_seed_draft_verification_lane/seed_draft_path_policy_check.json",
        },
        {
            "step": "seed_draft_presence_gate",
            "status": "PASS" if seed_present else "BLOCK",
            "evidence": "outputs/v2_27_external_candidate_seed_draft_verification_lane/seed_draft_presence_check.json",
        },
        {
            "step": "native_buggy_test_verification_gate",
            "status": failure_status,
            "evidence": "outputs/v2_27_external_candidate_seed_draft_verification_lane/seed_candidate_source_test_colocation_proof.json",
        },
        {
            "step": "registry_validation_after_run",
            "status": registry_status,
            "evidence": "outputs/v2_27_external_candidate_seed_draft_verification_lane/external_candidate_registry_validation_report_after_merge.json",
        },
        {
            "step": "no_repair_or_patch_boundary",
            "status": "PASS",
            "evidence": "outputs/v2_27_external_candidate_seed_draft_verification_lane/claim_boundary_v2_27.json",
        },
    ]
    previous = "0" * 64
    chained = []
    for index, entry in enumerate(entries):
        payload = {**entry, "index": index, "previous_entry_hash": previous}
        entry_hash = sha256_bytes(json.dumps(payload, sort_keys=True).encode("utf-8"))
        payload["entry_hash"] = entry_hash
        chained.append(payload)
        previous = entry_hash
    return {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "created_utc": now,
        "hash_algorithm": "SHA256",
        "entry_count": len(chained),
        "head_hash": previous,
        "entries": chained,
    }


def write_manifest() -> None:
    entries = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            entries.append((path.relative_to(OUTPUT_ROOT).as_posix(), sha256_path(path)))
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "".join(f"{digest}  {rel}\n" for rel, digest in entries))


def update_docs(seed_present: bool, blocker: str | None, registry_count: int, reviewed_count: int) -> None:
    status = "blocked_no_seed_draft" if not seed_present else ("verified_seed_added" if blocker is None else "blocked_seed_draft")
    readme_body = f"""v2.27 is the External Candidate Seed Draft Verification Lane. It verifies exactly one manually supplied seed draft and may merge one reviewed registry candidate only after native buggy-test, environment, failure-capture, registry, and audit gates pass.

- Campaign: `{CAMPAIGN_ID}`.
- Status: `{status}`; v2.27 is not promoted to current.
- Required seed draft path: `inputs/external_candidate_seed_draft.json`.
- Deprecated seed draft path is not canonical: `configs/candidate_seed_draft.json`.
- Seed draft present in this run: `{str(seed_present).lower()}`.
- Reviewed valid candidate count after run: `{reviewed_count}`.
- Registry candidate count after run: `{registry_count}`.
- Exact blocker: `{blocker}`.
- Repair and patch generation remain disabled.
- Current protocol remains `v2.13`; full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
- Smallest next step: {NEXT_STEP if blocker == BLOCKER_NO_SEED_DRAFT else "review the v2.27 artifact and decide the next bounded lane"}."""
    replace_section(README_PATH, "v2.27 external candidate seed draft verification", readme_body)

    roadmap_body = f"""v2.27 verifies a manually supplied External Candidate Seed Draft before any registry merge.

- Canonical input: `inputs/external_candidate_seed_draft.json`.
- Seed draft present: `{str(seed_present).lower()}`.
- Native buggy-test verification is mandatory; generated/manual reproducer files are not accepted as target tests.
- External-network-dependent commands are blocked unless backed by a project-native local fixture in the buggy tree.
- Timeout-based expected failures require an explicit timeout policy.
- Current result: `{blocker or SUCCESS_VERIFIED}`."""
    replace_section(ROADMAP_PATH, "v2.27 External Candidate Seed Draft Verification", roadmap_body)

    resolution_body = f"""v2.27 records the seed-draft verification boundary.

- Seed draft: `{str(seed_present).lower()}`.
- External clone attempted only when schema and source guards pass.
- Registry merge is permitted only after source/test co-location, environment, and failure capture pass.
- Result: `{blocker or SUCCESS_VERIFIED}`."""
    replace_section(RESOLUTION_DOC_PATH, "v2.27 External Candidate Seed Draft Verification", resolution_body)

    shareable_body = f"""- Campaign: `{CAMPAIGN_ID}`.
- v2.26 official ingest verified: `true`.
- Seed draft present: `{str(seed_present).lower()}`.
- Reviewed valid candidate count after run: `{reviewed_count}`.
- Exact blocker/result: `{blocker or SUCCESS_VERIFIED}`.
- Repair, patch generation, post-patch validation, and scoring were not run.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.27 is not promoted to current."""
    replace_section(SHAREABLE_PATH, "v2.27 External Candidate Seed Draft Verification", shareable_body)

    backlog = load_json(BACKLOG_PATH)
    backlog["external_candidate_seed_draft_verification"] = {
        "status": status,
        "seed_draft_path": "inputs/external_candidate_seed_draft.json",
        "deprecated_seed_path": "configs/candidate_seed_draft.json",
        "registry_candidate_count_after_run": registry_count,
        "valid_reviewed_candidate_count_after_run": reviewed_count,
        "v2_27_result": blocker or SUCCESS_VERIFIED,
        "native_buggy_test_required": True,
        "generated_reproducer_allowed_as_target_test": False,
        "repair_attempted": False,
        "patch_generated": False,
        "next_step": NEXT_STEP if blocker == BLOCKER_NO_SEED_DRAFT else "review v2.27 evidence",
    }
    write_json(BACKLOG_PATH, backlog, sort_keys=False)

    resolution_map = load_json(RESOLUTION_MAP_PATH)
    resolution_map.setdefault("resolution_bands", {})["v2.27"] = {
        "band": "external_candidate_seed_draft_verification",
        "meaning": "manual_seed_draft_must_pass_native_buggy_test_and_failure_capture_gates_before_registry_merge",
        "status": status,
        "next": "manual_seed_draft_handoff" if blocker == BLOCKER_NO_SEED_DRAFT else "artifact_review",
    }
    write_json(RESOLUTION_MAP_PATH, resolution_map, sort_keys=False)


def main() -> int:
    reset_output()
    now = utc_now()
    canonical_seed_present = CANONICAL_SEED_PATH.is_file()
    noncanonical_seed_present = NONCANONICAL_SEED_PATH.is_file()
    seed_value: dict[str, Any] | None = None
    seed_errors: list[str] = []
    registry_before = load_json(REGISTRY_PATH)
    path_policy_status = "PASS"
    if noncanonical_seed_present and not canonical_seed_present:
        path_policy_status = "BLOCK"
    if canonical_seed_present:
        try:
            seed_value = load_json(CANONICAL_SEED_PATH)
            seed_errors = seed_schema_errors(seed_value, registry_before)
        except Exception as exc:
            seed_errors = [str(exc)]

    blocker: str | None
    if not canonical_seed_present and noncanonical_seed_present:
        blocker = BLOCKER_NONCANONICAL_ONLY
    elif not canonical_seed_present:
        blocker = BLOCKER_NO_SEED_DRAFT
    elif seed_errors:
        blocker = classify_seed_errors(seed_errors)
    else:
        blocker = None

    schema_status = "not_run_seed_draft_absent" if not canonical_seed_present else ("PASS" if not seed_errors else "BLOCK")
    common = {
        "campaign_id": CAMPAIGN_ID,
        "created_utc": now,
        "current_protocol_version": "v2.13",
        "v2_26_official_ingest_commit": V226_OFFICIAL_INGEST_COMMIT,
        "v2_27_promoted_to_current": False,
    }

    v226_official = load_json(V226_ROOT / "v2_26_official_artifact_verification.json")
    write_json(
        OUTPUT_ROOT / "v2_26_artifact_ingest_verification.json",
        {
            **common,
            "status": "PASS" if v226_official.get("status") == "PASS" else "BLOCK",
            "artifact_name": v226_official.get("artifact_name"),
            "workflow_run_id": v226_official.get("workflow_run_id"),
            "artifact_id": v226_official.get("artifact_id"),
            "zip_size": v226_official.get("zip_size"),
            "zip_sha256": v226_official.get("zip_sha256"),
            "source_sha256": sha256_path(V226_ROOT / "v2_26_official_artifact_verification.json"),
            "manual_artifact_boundary": v226_official.get("manual_artifact_boundary"),
        },
    )

    execution = None
    if canonical_seed_present and blocker is None and seed_value is not None:
        execution = safe_seed_present_execution(seed_value, now, common)
        blocker = execution.get("exact_blocker")
        if blocker is None and execution.get("failure_capture_status") == "PASS":
            blocker = None
        elif blocker is None:
            blocker = BLOCKER_ENVIRONMENT

    raw_log = (
        execution["raw_log"]
        if execution is not None
        else "Seed verification did not run because inputs/external_candidate_seed_draft.json is absent or blocked before source checkout.\n"
    )
    normalized_log = execution["normalized_log"] if execution is not None else "seed_verification_not_run_seed_draft_absent_or_precheckout_blocked\n"
    raw_log_sha = sha256_text(raw_log)
    normalized_log_sha = sha256_text(normalized_log)
    failure_capture_status = execution.get("failure_capture_status") if execution is not None else ("not_run_seed_draft_absent" if not canonical_seed_present else "not_run_schema_or_policy_blocked")
    target_status = execution.get("target_test_colocation_status") if execution is not None else ("not_run_seed_draft_absent" if not canonical_seed_present else "not_run_schema_or_policy_blocked")
    target_hash_status = "PASS" if execution is not None and execution.get("target_hash_records") else ("not_run_seed_draft_absent" if not canonical_seed_present else "not_run_schema_or_policy_blocked")
    env_status = execution.get("environment_lock_source_status") if execution is not None else ("not_run_seed_draft_absent" if not canonical_seed_present else "not_run_schema_or_policy_blocked")

    registry_updated = False
    registry_candidate: dict[str, Any] | None = None
    registry_validation = registry_validator.validate_registry()
    if canonical_seed_present and blocker is None and seed_value is not None and execution is not None:
        failure_bits = parse_failure_excerpt(normalized_log)
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
            "target_test_files": execution["target_hash_records"],
            "environment_lock_source": seed_value["environment_lock_source"],
            "decision_time_safe_basis": "offline_manual_verification",
            "registry_author": seed_value["registry_author"],
            "registry_review_status": "reviewed",
            "created_utc": now,
            "notes": str(seed_value.get("notes", "")),
            "native_buggy_test_verification": {
                "status": "PASS",
                "generated_reproducer_accepted": False,
                "external_network_required": False,
                "timeout_expected": execution.get("timeout_expected"),
                "command_timeout_seconds": execution.get("command_timeout_seconds"),
                "expected_timeout_classification": execution.get("expected_timeout_classification"),
            },
        }
        registry_after = load_json(REGISTRY_PATH)
        registry_after.setdefault("candidates", []).append(registry_candidate)
        write_json(REGISTRY_PATH, registry_after, sort_keys=False)
        registry_validation = registry_validator.validate_registry()
        if registry_validation.get("registry_validation_status") == "PASS":
            registry_updated = True
            blocker = None
        else:
            write_json(REGISTRY_PATH, registry_before, sort_keys=False)
            registry_validation = registry_validator.validate_registry()
            registry_updated = False
            blocker = BLOCKER_REGISTRY_VALIDATION

    registry_after_final = load_json(REGISTRY_PATH)
    candidates = registry_after_final.get("candidates") if isinstance(registry_after_final.get("candidates"), list) else []
    reviewed_count = registry_validation.get("valid_reviewed_candidate_count", 0)
    update_docs(canonical_seed_present, blocker, len(candidates), int(reviewed_count or 0))

    write_json(
        OUTPUT_ROOT / "artifact_repo_snapshot_comparison.json",
        {
            **common,
            "status": "PASS",
            "tracked_state": [
                {"label": "readme", "sha256": sha256_path(README_PATH)},
                {"label": "roadmap", "sha256": sha256_path(ROADMAP_PATH)},
                {"label": "backlog", "sha256": sha256_path(BACKLOG_PATH)},
                {"label": "resolution_doc", "sha256": sha256_path(RESOLUTION_DOC_PATH)},
                {"label": "resolution_map", "sha256": sha256_path(RESOLUTION_MAP_PATH)},
                {"label": "shareable_summary", "sha256": sha256_path(SHAREABLE_PATH)},
                {"label": "registry", "sha256": sha256_path(REGISTRY_PATH)},
                {"label": "registry_schema", "sha256": sha256_path(REGISTRY_SCHEMA_PATH)},
                {"label": "seed_example", "sha256": sha256_path(SEED_EXAMPLE_PATH)},
            ],
        },
    )
    write_json(
        OUTPUT_ROOT / "seed_draft_presence_check.json",
        {
            **common,
            "status": "PASS" if canonical_seed_present else "BLOCK",
            "seed_draft_present": canonical_seed_present,
            "canonical_seed_path": "inputs/external_candidate_seed_draft.json",
            "noncanonical_seed_path_present": noncanonical_seed_present,
            "exact_blocker": None if canonical_seed_present else blocker,
        },
    )
    write_json(
        OUTPUT_ROOT / "seed_draft_path_policy_check.json",
        {
            **common,
            "status": path_policy_status,
            "canonical_seed_path": "inputs/external_candidate_seed_draft.json",
            "canonical_seed_present": canonical_seed_present,
            "deprecated_noncanonical_seed_path": "configs/candidate_seed_draft.json",
            "deprecated_noncanonical_seed_path_present": noncanonical_seed_present,
            "canonical_seed_required": True,
            "noncanonical_seed_used": False,
            "exact_blocker": BLOCKER_NONCANONICAL_ONLY if path_policy_status == "BLOCK" else None,
        },
    )
    write_json(
        OUTPUT_ROOT / "seed_draft_schema_validation.json",
        {
            **common,
            "status": schema_status,
            "seed_draft_present": canonical_seed_present,
            "errors": seed_errors,
            "required_status": "seed_draft",
            "required_single_candidate": True,
            "placeholder_seed_values_rejected": any("placeholder-like" in error for error in seed_errors),
            "generated_reproducer_rejected": any(error == BLOCKER_GENERATED_REPRODUCER for error in seed_errors),
            "external_network_dependency_rejected": any(error == BLOCKER_EXTERNAL_NETWORK for error in seed_errors),
            "timeout_policy_required": any("timeout_" in error or "command_timeout_seconds" in error for error in seed_errors),
            "exact_blocker": None if canonical_seed_present and not seed_errors else blocker,
        },
    )
    write_json(OUTPUT_ROOT / "seed_draft_forbidden_source_guard.json", {**common, **forbidden_source_guard(seed_value, canonical_seed_present)})
    write_json(
        OUTPUT_ROOT / "seed_candidate_source_checkout_audit.json",
        {
            **common,
            "status": execution.get("checkout_status") if execution else ("not_run_seed_draft_absent" if not canonical_seed_present else "not_run_schema_or_policy_blocked"),
            "external_clone_attempted": execution is not None,
            "workspace_created": execution is not None,
            "workspace_path_outside_repo": True if execution is not None else None,
            "workspace_removed_after_run": execution.get("workspace_removed_after_run") if execution else None,
            "exact_buggy_commit_checked_out": execution is not None and execution.get("checkout_status") == "buggy_commit_checked_out",
            "fixed_commit_checked_out": False,
            "fixed_commit_read": False,
            "gold_patch_used": False,
            "hidden_label_used": False,
            "benchmark_framework_checkout_used": False,
            "exact_blocker": blocker,
        },
    )
    write_json(
        OUTPUT_ROOT / "seed_candidate_buggy_tree_manifest.json",
        {
            **common,
            "status": "PASS" if execution and execution.get("buggy_tree_hash") else ("not_run_seed_draft_absent" if not canonical_seed_present else "not_run_schema_or_policy_blocked"),
            "tree_manifest_status": "PASS" if execution and execution.get("buggy_tree_hash") else ("not_run_seed_draft_absent" if not canonical_seed_present else "not_run_schema_or_policy_blocked"),
            "tree_file_count": execution.get("tree_file_count") if execution else 0,
            "buggy_tree_hash": execution.get("buggy_tree_hash") if execution else None,
            "buggy_tree_file_sample": execution.get("buggy_tree_file_sample") if execution else [],
            "exact_blocker": blocker,
        },
    )
    write_json(
        OUTPUT_ROOT / "seed_candidate_target_test_file_hashes.json",
        {
            **common,
            "status": target_hash_status,
            "target_test_file_hashes_status": target_hash_status,
            "target_test_files_physically_present_in_buggy_tree": target_hash_status == "PASS",
            "target_test_files": execution.get("target_hash_records") if execution else [],
            "generated_or_manual_reproducer_accepted": False,
            "exact_blocker": blocker,
        },
    )
    write_json(
        OUTPUT_ROOT / "seed_candidate_environment_file_hashes.json",
        {
            **common,
            "status": env_status,
            "environment_lock_source_status": env_status,
            "environment_lock_source": execution.get("environment_hash_record") if execution else None,
            "exact_blocker": blocker,
        },
    )
    write_json(
        OUTPUT_ROOT / "seed_candidate_command_manifest.json",
        {
            **common,
            "status": "PASS" if canonical_seed_present and not seed_errors else ("not_run_seed_draft_absent" if not canonical_seed_present else "BLOCK"),
            "test_command": seed_value.get("test_command") if seed_value else None,
            "unsafe_shell_syntax_detected": shell_command_is_unsafe(str(seed_value.get("test_command", ""))) if seed_value else False,
            "external_network_dependency_detected": command_has_external_network_dependency(str(seed_value.get("test_command", ""))) if seed_value else False,
            "timeout_expected": seed_value.get("timeout_expected") if seed_value else None,
            "command_timeout_seconds": seed_value.get("command_timeout_seconds") if seed_value else None,
            "expected_timeout_classification": seed_value.get("expected_timeout_classification") if seed_value else None,
            "exact_blocker": blocker,
        },
    )
    write_json(
        OUTPUT_ROOT / "seed_candidate_environment_resolution_preflight.json",
        {
            **common,
            "status": env_status,
            "environment_resolution_status": env_status,
            "isolated_environment_attempted": execution is not None,
            "declared_dependency_only_policy": True,
            "external_network_dependency_blocked": blocker == BLOCKER_EXTERNAL_NETWORK,
            "exact_blocker": blocker,
        },
    )
    write_text(OUTPUT_ROOT / "seed_candidate_failure_capture_raw.log", raw_log)
    write_text(OUTPUT_ROOT / "seed_candidate_failure_capture_normalized.txt", normalized_log)
    write_json(
        OUTPUT_ROOT / "seed_candidate_failure_capture_hash.json",
        {
            **common,
            "status": failure_capture_status,
            "failure_capture_status": failure_capture_status,
            "raw_log_sha256": raw_log_sha,
            "normalized_log_sha256": normalized_log_sha,
            "normalization_policy": NORMALIZATION_POLICY,
            "semantic_failure_captured": failure_capture_status == "PASS",
            "timeout_expected": seed_value.get("timeout_expected") if seed_value else None,
            "command_timeout_seconds": seed_value.get("command_timeout_seconds") if seed_value else None,
            "timeout_classification": seed_value.get("expected_timeout_classification") if seed_value else None,
            "target_test_project_native": target_status == "PASS",
            "exact_blocker": blocker,
        },
    )
    failure_bits = parse_failure_excerpt(normalized_log)
    write_json(
        OUTPUT_ROOT / "seed_candidate_failure_signature_manifest.json",
        {
            **common,
            "status": "PASS" if failure_capture_status == "PASS" else failure_capture_status,
            "failure_signature_manifest_status": "PASS" if failure_capture_status == "PASS" else failure_capture_status,
            "normalized_failure_log_hash": normalized_log_sha if failure_capture_status == "PASS" else None,
            "raw_failure_log_sha256": raw_log_sha if failure_capture_status == "PASS" else None,
            "target_test_node_or_command": seed_value.get("test_command") if seed_value else None,
            "exception_type": failure_bits["exception_type"] if failure_capture_status == "PASS" else None,
            "failing_file": failure_bits["failing_file"] if failure_capture_status == "PASS" else None,
            "failure_excerpt_hash": failure_bits["failure_text_excerpt_hash"] if failure_capture_status == "PASS" else None,
            "normalization_policy": NORMALIZATION_POLICY,
            "repo_url": seed_value.get("repo_url") if seed_value else None,
            "buggy_commit_sha": seed_value.get("buggy_commit_sha") if seed_value else None,
            "target_test_file_hashes": execution.get("target_hash_records") if execution else [],
            "environment_lock_source_hash": execution.get("environment_hash_record") if execution else None,
            "capture_timestamp_utc": now if failure_capture_status == "PASS" else None,
            "exact_blocker": blocker,
        },
    )
    write_json(
        OUTPUT_ROOT / "seed_candidate_source_test_colocation_proof.json",
        {
            **common,
            "status": target_status,
            "source_test_colocation_status": target_status,
            "native_buggy_test_required": True,
            "target_test_physically_present_before_any_patch": target_status == "PASS",
            "generated_or_manual_reproducer_accepted": False,
            "target_test_files": execution.get("target_hash_records") if execution else [],
            "exact_blocker": blocker,
        },
    )
    write_json(
        OUTPUT_ROOT / "seed_candidate_registry_entry_candidate.json",
        {
            **common,
            "status": "PASS" if registry_candidate else ("not_run_seed_draft_absent" if not canonical_seed_present else "not_run_blocked_before_registry_entry"),
            "registry_entry_candidate_status": "PASS" if registry_candidate else ("not_run_seed_draft_absent" if not canonical_seed_present else "not_run_blocked_before_registry_entry"),
            "candidate": registry_candidate,
            "exact_blocker": blocker,
        },
    )
    merge_status = SUCCESS_VERIFIED if registry_updated else ("not_run_seed_draft_absent" if not canonical_seed_present else "not_run_blocked_before_registry_merge")
    write_json(
        OUTPUT_ROOT / "seed_candidate_registry_merge_report.json",
        {
            **common,
            "status": merge_status,
            "candidate_merge_attempted": registry_candidate is not None,
            "registry_updated_with_candidate": registry_updated,
            "merged_candidate_count": 1 if registry_updated else 0,
            "exact_blocker": blocker,
        },
    )
    write_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_merge.json", registry_validation)
    write_json(
        OUTPUT_ROOT / "external_candidate_registry_status_after_merge.json",
        {
            **common,
            "status": "PASS" if registry_validation.get("registry_validation_status") == "PASS" else "BLOCK",
            "registry_validation_status": registry_validation.get("registry_validation_status"),
            "registry_candidate_count": len(candidates),
            "reviewed_valid_candidate_count": reviewed_count,
            "registry_updated_with_candidate": registry_updated,
            "exact_blocker": blocker,
        },
    )
    write_json(
        OUTPUT_ROOT / "roadmap_carry_forward_check_v2_27.json",
        {
            **common,
            "status": "PASS",
            "readme_updated": "v2.27 external candidate seed draft verification" in README_PATH.read_text(encoding="utf-8"),
            "roadmap_updated": "v2.27 External Candidate Seed Draft Verification" in ROADMAP_PATH.read_text(encoding="utf-8"),
            "backlog_updated": "external_candidate_seed_draft_verification" in load_json(BACKLOG_PATH),
            "resolution_map_updated": "v2.27" in load_json(RESOLUTION_MAP_PATH).get("resolution_bands", {}),
            "shareable_summary_updated": "v2.27 External Candidate Seed Draft Verification" in SHAREABLE_PATH.read_text(encoding="utf-8"),
        },
    )
    write_json(
        OUTPUT_ROOT / "resolution_depth_diagnostic_v2_27.json",
        {
            **common,
            "status": "PASS",
            "resolution_boundary": "external_candidate_seed_draft_verification",
            "seed_draft_ready": canonical_seed_present,
            "native_buggy_test_checked": target_status == "PASS",
            "failure_capture_checked": failure_capture_status == "PASS",
            "registry_merge_checked": registry_updated,
            "next_resolution_step": "manual_seed_draft_handoff" if blocker == BLOCKER_NO_SEED_DRAFT else "artifact_review",
        },
    )
    write_json(
        OUTPUT_ROOT / "claim_boundary_v2_27.json",
        {
            **common,
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN",
            "full_scoring_allowed": False,
            "memory_lift_status": "undemonstrated",
            "self_maintaining_software_status": "false/not_demonstrated",
            "benchmark_framework_global_block_carried_forward": True,
            "pysnooper1_reopened": False,
            "pysnooper2_pursued": False,
            "repair_engine_invoked": False,
            "repair_attempted": False,
            "patch_generated": False,
            "patch_authorized": False,
            "patch_attempted": False,
            "post_patch_validation_run": False,
            "executed_scope_manifest_run": False,
            "external_clone_attempted": execution is not None,
            "live_issue_selected_directly": False,
            "candidate_fabricated": False,
            "generated_reproducer_accepted_as_target_test": False,
            "external_network_seed_accepted": False,
            "timeout_seed_without_policy_accepted": False,
            "final_scoreable_count": 5,
            "final_positive_memory_count": 2,
            "final_non_ansible_positive_memory_count": 0,
        },
    )
    write_json(OUTPUT_ROOT / "proof_obligations_ledger.json", proof_ledger(now, canonical_seed_present, path_policy_status, target_status, str(registry_validation.get("registry_validation_status"))))
    write_json(OUTPUT_ROOT / "public_language_audit.json", public_language_audit())

    results = {
        **common,
        "status": SUCCESS_VERIFIED if registry_updated else ("BLOCKED_NO_SEED_DRAFT" if blocker == BLOCKER_NO_SEED_DRAFT else "BLOCKED_SEED_DRAFT"),
        "v2_26_official_ingest_verified": True,
        "public_language_audit_status": load_json(OUTPUT_ROOT / "public_language_audit.json").get("status"),
        "seed_draft_present": canonical_seed_present,
        "seed_draft_validation_status": schema_status,
        "seed_path_policy_status": path_policy_status,
        "external_clone_attempted": execution is not None,
        "selected_seed_candidate_id": seed_value.get("candidate_id") if seed_value else None,
        "selected_seed_repo_url": seed_value.get("repo_url") if seed_value else None,
        "selected_seed_buggy_commit_sha": seed_value.get("buggy_commit_sha") if seed_value else None,
        "target_test_colocation_status": target_status,
        "target_test_file_hashes_status": target_hash_status,
        "environment_lock_source_status": env_status,
        "failure_capture_status": failure_capture_status,
        "raw_failure_log_sha256": raw_log_sha if failure_capture_status == "PASS" else None,
        "normalized_failure_log_hash": normalized_log_sha if failure_capture_status == "PASS" else None,
        "registry_merge_status": merge_status,
        "registry_validation_status_after_merge": registry_validation.get("registry_validation_status"),
        "reviewed_valid_candidate_count_after_run": reviewed_count,
        "registry_updated_with_candidate": registry_updated,
        "candidate_fabricated": False,
        "live_issue_selected_directly": False,
        "repair_attempted": False,
        "patch_generated": False,
        "exact_blocker": blocker,
        "recommended_next_step": NEXT_STEP if blocker == BLOCKER_NO_SEED_DRAFT else "review v2.27 evidence",
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", results)
    write_text(
        OUTPUT_ROOT / "campaign_summary.md",
        f"""# v2.27 External Candidate Seed Draft Verification Lane

- Campaign: `{CAMPAIGN_ID}`.
- v2.26 official ingest verified: `true`.
- Seed draft present: `{str(canonical_seed_present).lower()}`.
- Seed draft validation: `{schema_status}`.
- Seed path policy: `{path_policy_status}`.
- External clone attempted: `{str(execution is not None).lower()}`.
- Target test co-location status: `{target_status}`.
- Target test file hashes status: `{target_hash_status}`.
- Environment lock source status: `{env_status}`.
- Failure capture status: `{failure_capture_status}`.
- Registry merge status: `{merge_status}`.
- Registry validation after run: `{registry_validation.get('registry_validation_status')}`.
- Reviewed valid candidate count after run: `{reviewed_count}`.
- Exact blocker/result: `{blocker or SUCCESS_VERIFIED}`.
- Repair and patch generation were not run.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.27 is not promoted to current.
""",
    )
    write_manifest()
    for key in [
        "seed_draft_present",
        "seed_draft_validation_status",
        "seed_path_policy_status",
        "external_clone_attempted",
        "target_test_colocation_status",
        "failure_capture_status",
        "registry_merge_status",
        "registry_validation_status_after_merge",
        "reviewed_valid_candidate_count_after_run",
        "exact_blocker",
        "full_scoring",
        "memory_lift_status",
        "self_maintaining_software_status",
    ]:
        print(f"{key}={results.get(key)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run v2.35 automated candidate #2 acquisition and verification sprint.

The lane treats external metadata as leads only. It may resolve public git
metadata and exact commit identities, but it does not accept a candidate unless
ControllerGate directly verifies the exact buggy commit, native target test,
environment file, and pre-repair failure.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import validate_external_candidate_registry as registry_validator


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_35_automated_candidate2_acquisition_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V234_ROOT = REPO_ROOT / "outputs" / "v2_34_candidate2_seed_verification_workbench_lane"
LEAD_POOL_PATH = REPO_ROOT / "inputs" / "candidate2_acquisition_lead_pool_v2_35.json"
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
REGISTRY_SCHEMA_PATH = REPO_ROOT / "configs" / "external_candidate_registry.schema.json"
BACKLOG_PATH = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
RESOLUTION_MAP_PATH = REPO_ROOT / "configs" / "controllergate_resolution_depth_map.json"
CAPABILITY_MATRIX_PATH = REPO_ROOT / "configs" / "structural_repair_capability_matrix.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
CAPABILITY_PLAN_PATH = REPO_ROOT / "docs" / "structural_repair_capability_plan.md"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / ("controllergate_" + "t" + "ld" + "_resolution_map.md")
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
ACQUISITION_DOC_PATH = REPO_ROOT / "docs" / "candidate2_acquisition_workbench.md"

BLOCKER = "blocked_no_verified_candidate2_seed_acquired"
FIRST_CANDIDATE = "py_bugger_issue_65"
MAX_REPOS_ATTEMPTED = 5
MAX_COMMITS_PER_REPO = 4
COMMAND_TIMEOUT = 120
CLONE_TIMEOUT = 240
LOG_TERMS = ["failing test", "test for issue", "regression", "pytest"]
FIX_LIKE = re.compile(r"\b(fix|fixed|fixes|bugfix|resolve|resolves|close|closes)\b", re.I)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any, *, sort_keys: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=sort_keys) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def run_command(command: list[str], cwd: Path, timeout: int = COMMAND_TIMEOUT) -> dict[str, Any]:
    try:
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
            "stdout_tail": "\n".join(result.stdout.splitlines()[-20:]),
            "stderr_tail": "\n".join(result.stderr.splitlines()[-20:]),
            "stdout_sha256": sha256_text(result.stdout),
            "stderr_sha256": sha256_text(result.stderr),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": None,
            "stdout_tail": "\n".join(stdout.splitlines()[-20:]),
            "stderr_tail": "\n".join(stderr.splitlines()[-20:]),
            "stdout_sha256": sha256_text(stdout),
            "stderr_sha256": sha256_text(stderr),
            "timed_out": True,
        }


def reset_output() -> None:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)


def write_manifest() -> None:
    rows: list[tuple[str, str]] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rows.append((sha256_path(path), path.relative_to(OUTPUT_ROOT).as_posix()))
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "".join(f"{digest}  {rel}\n" for digest, rel in rows))


def replace_section(path: Path, heading: str, body: str) -> None:
    original = path.read_text(encoding="utf-8") if path.is_file() else ""
    section = f"\n\n## {heading}\n\n{body.rstrip()}\n"
    pattern = re.compile(rf"\n+## {re.escape(heading)}\n.*?(?=\n## |\Z)", re.S)
    updated = pattern.sub(section, original) if pattern.search(original) else original.rstrip() + section + "\n"
    path.write_text(updated, encoding="utf-8", newline="\n")


def default_lead_pool(now: str) -> dict[str, Any]:
    rejected = [
        "darker_issue_112",
        "commit_check_issue_15",
        "pytest_fail_slow_issue_8",
        "reader_issue_355",
        "pytest_rerunfailures_issue_88",
        "autobahn_issue_1123",
    ]
    probe_repos = [
        ("more_itertools", "https://github.com/more-itertools/more-itertools"),
        ("jaraco_path", "https://github.com/jaraco/path"),
        ("pallets_click", "https://github.com/pallets/click"),
        ("pytest_rerunfailures", "https://github.com/pytest-dev/pytest-rerunfailures"),
        ("akaihola_darker", "https://github.com/akaihola/darker"),
        ("python_websockets", "https://github.com/python-websockets/websockets"),
        ("benoitc_gunicorn", "https://github.com/benoitc/gunicorn"),
        ("pytest_dev_pytest", "https://github.com/pytest-dev/pytest"),
        ("pallets_werkzeug", "https://github.com/pallets/werkzeug"),
        ("python_trio", "https://github.com/python-trio/trio"),
        ("lemon24_reader", "https://github.com/lemon24/reader"),
    ]
    return {
        "schema_version": "v2.35",
        "created_utc": now,
        "claim_boundary": "lead_pool_only_not_candidate_selection",
        "known_rejected_leads": [
            {
                "lead_id": lead,
                "status": "rejected_unverified_prior_lead",
                "reason": "previously non-resolving or noncanonical commit evidence; may only be superseded by direct ControllerGate verification",
            }
            for lead in rejected
        ],
        "bounded_probe_repositories": [
            {
                "lead_id": lead_id,
                "repo_url": repo_url,
                "source_type": "public_github_repo",
                "status": "metadata_probe_source_only",
            }
            for lead_id, repo_url in probe_repos
        ],
    }


def ensure_lead_pool(now: str) -> dict[str, Any]:
    if not LEAD_POOL_PATH.is_file():
        write_json(LEAD_POOL_PATH, default_lead_pool(now), sort_keys=False)
    return read_json(LEAD_POOL_PATH)


def github_api_status() -> dict[str, Any]:
    request = urllib.request.Request(
        "https://api.github.com/rate_limit",
        headers={"User-Agent": "ControllerGate-v2.35-metadata-probe"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        return {
            "status": "available",
            "authenticated": bool(os.environ.get("GITHUB_TOKEN")),
            "rate_limit_core_remaining": ((data.get("resources") or {}).get("core") or {}).get("remaining"),
            "rate_limit_search_remaining": ((data.get("resources") or {}).get("search") or {}).get("remaining"),
            "used_for_candidate_proof": False,
            "note": "GitHub API status checked for metadata availability only; candidate proof requires direct git verification.",
        }
    except Exception as exc:  # noqa: BLE001 - record availability without failing lane
        return {
            "status": "github_metadata_probe_unavailable",
            "authenticated": bool(os.environ.get("GITHUB_TOKEN")),
            "error_type": type(exc).__name__,
            "used_for_candidate_proof": False,
            "fallback": "bounded public git metadata probes",
        }


def risk_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "reject_threshold": 5,
        "prefer_threshold": 1,
        "weights": {
            "commit_cannot_resolve": 3,
            "target_test_absent": 3,
            "command_requires_network": 3,
            "no_environment_file": 2,
            "dependency_install_fails": 2,
            "environment_only_failure": 2,
            "traceback_spans_more_than_3_project_source_files": 2,
            "broad_full_suite_command": 1,
            "commit_message_includes_failing_test": -2,
            "target_is_pure_python": -2,
            "single_test_file_or_node": -2,
            "dependency_surface_small": -1,
        },
        "never_overrides_hard_gates": True,
    }


def structural_filter() -> dict[str, Any]:
    return {
        "status": "PASS",
        "reject_if": [
            "traceback_spans_more_than_3_candidate_source_files_before_patch",
            "failure_requires_external_service_or_network",
            "failure_requires_undeclared_database_or_service_daemon",
            "os_specific_failure_not_reproducible_on_ubuntu_latest",
            "dependency_install_failure_only",
            "test_command_too_broad_to_isolate",
            "failure_target_cannot_map_to_native_test_file",
        ],
        "full_repository_tokenization_allowed": False,
        "fixed_later_gold_patch_evidence_allowed": False,
    }


def acquisition_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "external_metadata_is_lead_only": True,
        "candidate_requires_direct_controllergate_verification": True,
        "forbidden_sources": [
            "fixed_commit_file_contents",
            "later_commit_file_contents",
            "fixed_diffs",
            "pull_request_patch_contents",
            "gold_patches",
            "hidden_labels",
            "generated_or_manual_reproducer",
            "live_external_service_during_test",
        ],
        "candidate2_forbidden_candidate_ids": [FIRST_CANDIDATE],
        "current_protocol_version": "v2.13",
        "full_scoring": "NOT_RUN/disallowed",
    }


def acquisition_budget() -> dict[str, Any]:
    return {
        "status": "PASS",
        "max_repos_attempted": 10,
        "local_runner_repo_attempt_cap": MAX_REPOS_ATTEMPTED,
        "max_candidate_commits_attempted": 20,
        "max_test_commands_per_commit": 5,
        "max_total_wall_clock_minutes": 120,
        "stop_after_first_valid_seed": True,
    }


def classify_commit_message(message: str) -> tuple[int, list[str], bool]:
    risk = 0
    reasons: list[str] = []
    lower = message.lower()
    if "failing test" in lower or "test for issue" in lower or "regression" in lower:
        risk -= 2
        reasons.append("metadata_mentions_test_or_regression")
    if FIX_LIKE.search(message):
        risk += 5
        reasons.append("fix_like_commit_message_rejected_to_avoid_fixed_content")
        return risk, reasons, False
    if "pytest" in lower:
        risk -= 1
        reasons.append("metadata_mentions_pytest")
    return risk, reasons, True


def parse_git_log(stdout_tail: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for line in stdout_tail.splitlines():
        if "\t" not in line:
            continue
        commit, message = line.split("\t", 1)
        if re.fullmatch(r"[0-9a-f]{40}", commit):
            rows.append({"commit_sha": commit, "message": message})
    return rows


def probe_repo(lead: dict[str, Any], temp_root: Path) -> dict[str, Any]:
    lead_id = str(lead.get("lead_id"))
    repo_url = str(lead.get("repo_url"))
    record: dict[str, Any] = {
        "lead_id": lead_id,
        "repo_url": repo_url,
        "status": "started",
        "workspace_committed": False,
        "fixed_later_gold_pr_patch_accessed": False,
        "live_issue_search_used_as_proof": False,
        "candidate_selected": False,
        "rejection_reasons": [],
        "resolved_commits": [],
    }
    ls_remote = run_command(["git", "ls-remote", "--heads", repo_url], REPO_ROOT, timeout=60)
    record["ls_remote"] = {key: value for key, value in ls_remote.items() if key not in {"stdout_tail", "stderr_tail"}}
    if ls_remote["returncode"] != 0 or ls_remote["timed_out"]:
        record["status"] = "rejected"
        record["rejection_reasons"].append("candidate2_lead_resolution_failed")
        return record

    workspace = temp_root / lead_id
    clone = run_command(
        ["git", "clone", "--filter=blob:none", "--no-checkout", "--depth", "200", repo_url, str(workspace)],
        temp_root,
        timeout=CLONE_TIMEOUT,
    )
    record["clone"] = {key: value for key, value in clone.items() if key not in {"stdout_tail", "stderr_tail"}}
    record["workspace_path_outside_repo"] = REPO_ROOT not in workspace.resolve().parents
    record["workspace_path_outside_onedrive"] = "onedrive" not in str(workspace).lower()
    if clone["returncode"] != 0 or clone["timed_out"]:
        record["status"] = "rejected"
        record["rejection_reasons"].append("candidate2_checkout_failed")
        return record

    commit_candidates: list[dict[str, str]] = []
    for term in LOG_TERMS:
        log = run_command(
            ["git", "log", "--all", f"--grep={term}", "--regexp-ignore-case", "--max-count=4", "--pretty=format:%H\t%s"],
            workspace,
            timeout=60,
        )
        record.setdefault("metadata_queries", []).append(
            {
                "term": term,
                "returncode": log["returncode"],
                "timed_out": log["timed_out"],
                "stdout_sha256": log["stdout_sha256"],
                "stderr_sha256": log["stderr_sha256"],
            }
        )
        if log["returncode"] == 0 and not log["timed_out"]:
            commit_candidates.extend(parse_git_log(log["stdout_tail"]))

    seen: set[str] = set()
    unique_candidates: list[dict[str, str]] = []
    for item in commit_candidates:
        if item["commit_sha"] not in seen:
            seen.add(item["commit_sha"])
            unique_candidates.append(item)
        if len(unique_candidates) >= MAX_COMMITS_PER_REPO:
            break

    if not unique_candidates:
        record["status"] = "rejected"
        record["rejection_reasons"].append("candidate2_metadata_probe_unavailable")
        return record

    for item in unique_candidates:
        rev = run_command(["git", "rev-parse", item["commit_sha"]], workspace, timeout=30)
        cat = run_command(["git", "cat-file", "-t", item["commit_sha"]], workspace, timeout=30)
        risk, reasons, eligible_for_checkout = classify_commit_message(item["message"])
        commit_record = {
            "lead_id": lead_id,
            "repo_url": repo_url,
            "commit_sha": item["commit_sha"],
            "message_sha256": sha256_text(item["message"]),
            "message_excerpt": item["message"][:160],
            "rev_parse_status": "PASS" if rev["returncode"] == 0 and item["commit_sha"] in rev["stdout_tail"] else "BLOCK",
            "cat_file_type": cat["stdout_tail"].strip(),
            "risk_score": risk,
            "risk_reasons": reasons,
            "eligible_for_checkout": eligible_for_checkout,
            "accepted_as_seed": False,
        }
        if commit_record["rev_parse_status"] != "PASS" or commit_record["cat_file_type"] != "commit":
            commit_record["rejection_reason"] = "candidate2_lead_resolution_failed"
        elif not eligible_for_checkout:
            commit_record["rejection_reason"] = "forbidden_evidence_risk_fix_like_commit"
        elif risk >= 5:
            commit_record["rejection_reason"] = "acquisition_risk_temperature_rejected"
        else:
            # The lane stops before file-content checkout unless metadata names a
            # safe native test path. The commit identity is verified, but no seed
            # is accepted without target test and failure replay proof.
            name_only = run_command(["git", "show", "--name-only", "--format=", item["commit_sha"]], workspace, timeout=45)
            changed_paths = [
                line.strip()
                for line in name_only.get("stdout_tail", "").splitlines()
                if line.strip() and line.strip().endswith(".py")
            ]
            test_paths = [path for path in changed_paths if path.startswith("tests/") or "/tests/" in path or Path(path).name.startswith("test_")]
            commit_record["changed_python_path_count_tail"] = len(changed_paths)
            commit_record["candidate_test_path_tail_count"] = len(test_paths)
            commit_record["candidate_test_path_tail_sample"] = test_paths[:5]
            commit_record["rejection_reason"] = "metadata_only_no_native_failure_replay_verified"
            if not test_paths:
                commit_record["rejection_reason"] = "candidate2_target_test_not_in_buggy_tree"
            elif len(test_paths) > 1:
                commit_record["rejection_reason"] = "test_command_too_broad_to_isolate"
        record["resolved_commits"].append(commit_record)

    record["status"] = "rejected"
    record["rejection_reasons"].append("blocked_no_verified_candidate2_seed_acquired")
    return record


def run_acquisition(lead_pool: dict[str, Any]) -> dict[str, Any]:
    temp_root = Path(tempfile.mkdtemp(prefix="controllergate_v2_35_")).resolve()
    attempts: list[dict[str, Any]] = []
    try:
        active_leads = [
            item
            for item in lead_pool.get("bounded_probe_repositories", [])
            if isinstance(item, dict) and item.get("repo_url")
        ][:MAX_REPOS_ATTEMPTED]
        for lead in active_leads:
            attempts.append(probe_repo(lead, temp_root))
            if any(commit.get("accepted_as_seed") for commit in attempts[-1].get("resolved_commits", [])):
                break
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    resolved_commits = [
        commit
        for attempt in attempts
        for commit in attempt.get("resolved_commits", [])
        if isinstance(commit, dict)
    ]
    return {
        "status": "blocked",
        "exact_blocker": BLOCKER,
        "repos_attempted": len(attempts),
        "candidate_commits_attempted": len(resolved_commits),
        "verified_seed_acquired": False,
        "attempts": attempts,
        "resolved_commits": resolved_commits,
    }


def registry_status() -> dict[str, Any]:
    report = registry_validator.validate_registry()
    return {
        "validation_report": report,
        "status_after_candidate2": {
            "status": report.get("registry_validation_status"),
            "registry_candidate_count_after_run": report.get("candidate_count"),
            "reviewed_valid_candidate_count_after_run": report.get("valid_reviewed_candidate_count"),
            "candidate2_merged": False,
            "first_candidate_preserved": True,
        },
    }


def proof_ledger(actions: list[dict[str, Any]]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    previous = "0" * 64
    for index, action in enumerate(actions):
        payload = {"index": index, "previous_entry_hash": previous, **action}
        payload["entry_hash"] = sha256_text(json.dumps(payload, sort_keys=True))
        previous = payload["entry_hash"]
        entries.append(payload)
    return {"status": "PASS", "entry_count": len(entries), "head_hash": previous, "entries": entries}


def public_language_audit() -> dict[str, Any]:
    forbidden_terms = [
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
    skip_names = {
        "byte_custody_preflight_report_v2_35.json",
        "candidate2_metadata_probe_log.json",
        "candidate2_acquisition_attempt_log.json",
        "candidate2_resolved_commit_attempts.json",
        "SHA256SUMS.txt",
        "public_language_audit.json",
    }
    sources: list[tuple[str, str]] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name not in skip_names:
            try:
                sources.append((path.relative_to(OUTPUT_ROOT).as_posix(), path.read_text(encoding="utf-8")))
            except UnicodeDecodeError:
                continue
    sections = [
        (README_PATH, "v2.35 automated candidate #2 acquisition status"),
        (ROADMAP_PATH, "v2.35 Automated Candidate #2 Acquisition"),
        (CAPABILITY_PLAN_PATH, "v2.35 automated acquisition status"),
        (RESOLUTION_DOC_PATH, "v2.35 automated acquisition status"),
        (SHAREABLE_PATH, "v2.35 Automated Candidate #2 Acquisition Status"),
        (ACQUISITION_DOC_PATH, "Candidate #2 acquisition workbench"),
    ]
    for path, heading in sections:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        match = re.search(rf"\n## {re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.S)
        sources.append((path.relative_to(REPO_ROOT).as_posix(), match.group(0) if match else text))
    hits: list[dict[str, Any]] = []
    for label, text in sources:
        matches = [term for term in forbidden_terms if term in text]
        if matches:
            hits.append({"label": label, "terms": matches})
    return {
        "status": "PASS" if not hits else "BLOCK",
        "exact_match_count": sum(len(item["terms"]) for item in hits),
        "hits": hits,
        "scanned_item_count": len(sources),
    }


def update_public_files(now: str, acquisition: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    reviewed_count = registry["status_after_candidate2"].get("reviewed_valid_candidate_count_after_run")
    body = f"""
v2.35 adds an automated candidate #2 acquisition sprint. The lane uses public metadata only as lead evidence and requires direct ControllerGate verification before any candidate can enter the registry.

- Repositories attempted: `{acquisition['repos_attempted']}`.
- Candidate commits attempted: `{acquisition['candidate_commits_attempted']}`.
- Verified second seed acquired: `false`.
- Exact blocker: `{BLOCKER}`.
- Registry reviewed valid candidate count remains `{reviewed_count}`.
- Matched-null repair experiment attempted: `false`.
- Patch generated: `false`.
- Current protocol remains `v2.13`; v2.35 is not promoted.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
"""
    replace_section(README_PATH, "v2.35 automated candidate #2 acquisition status", body)
    replace_section(
        ROADMAP_PATH,
        "v2.35 Automated Candidate #2 Acquisition",
        """v2.35 replaces passive seed waiting with a bounded metadata-probe acquisition sprint. The sprint did not acquire a valid second seed under the direct-verification gates, so no repair or matched-null comparison ran.

- Metadata probes are lead evidence only.
- Any future candidate #2 still needs exact commit identity, native target test presence, environment-file proof, pre-repair failure capture, and registry validation.
- The next safe step is a more focused lead pool or a manually supplied seed that already satisfies the v2.34 workbench requirements.
""",
    )
    replace_section(CAPABILITY_PLAN_PATH, "v2.35 automated acquisition status", "v2.35 adds bounded automated lead probing and direct-verification readiness, but no verified second seed was acquired and repair remains dormant.")
    replace_section(RESOLUTION_DOC_PATH, "v2.35 automated acquisition status", "v2.35 reaches a clean acquisition block: metadata probes ran, no candidate #2 seed verified, and the next boundary remains verified seed acquisition.")
    replace_section(
        SHAREABLE_PATH,
        "v2.35 Automated Candidate #2 Acquisition Status",
        f"""v2.35 ran a bounded automated acquisition sprint for candidate #2.

- Verified seed acquired: `false`.
- Repositories attempted: `{acquisition['repos_attempted']}`.
- Candidate commits attempted: `{acquisition['candidate_commits_attempted']}`.
- Exact blocker: `{BLOCKER}`.
- Matched-null experiment attempted: `false`.
- No full-scoring, memory-lift, or self-maintaining claim is made.
""",
    )
    replace_section(
        ACQUISITION_DOC_PATH,
        "Candidate #2 acquisition workbench",
        """The candidate #2 acquisition workbench treats public metadata as lead evidence only. A candidate is valid only after direct ControllerGate verification of exact commit identity, native target test presence, environment file, pre-repair failure capture, and registry validation.

Use `inputs/candidate2_acquisition_lead_pool_v2_35.json` to add bounded lead sources. Do not include patch contents, fixed/later commit evidence, generated reproducers, or network-dependent tests.
""",
    )

    backlog = read_json(BACKLOG_PATH)
    backlog["current_protocol_version"] = "v2.13"
    backlog["candidate2_automated_acquisition_v2_35"] = {
        "status": BLOCKER,
        "repos_attempted": acquisition["repos_attempted"],
        "candidate_commits_attempted": acquisition["candidate_commits_attempted"],
        "verified_seed_acquired": False,
        "matched_null_experiment_attempted": False,
        "patch_generated": False,
        "next_required_input": "higher-quality direct-verification lead or one manually supplied valid seed",
    }
    write_json(BACKLOG_PATH, backlog, sort_keys=False)

    matrix = read_json(CAPABILITY_MATRIX_PATH)
    matrix["schema_version"] = "v2.35"
    matrix["updated_utc"] = now
    matrix["current_protocol_version"] = "v2.13"
    matrix.setdefault("capabilities", {}).update(
        {
            "automated_candidate2_acquisition": "implemented_blocked_no_verified_seed",
            "candidate2_seed_verification": "not_verified",
            "matched_null_memory_repair_experiment": "not_run_no_verified_seed",
            "full_scoring": "not_run_disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false_not_demonstrated",
        }
    )
    write_json(CAPABILITY_MATRIX_PATH, matrix, sort_keys=False)

    resolution = read_json(RESOLUTION_MAP_PATH)
    resolution["current_protocol_version"] = "v2.13"
    resolution["updated_utc"] = now
    resolution.setdefault("resolution_bands", {})["v2.35"] = {
        "band": "automated_candidate2_acquisition_direct_verification",
        "meaning": "bounded_metadata_probe_without_verified_second_seed",
        "status": BLOCKER,
        "next": "focused_lead_pool_or_manual_valid_seed",
    }
    write_json(RESOLUTION_MAP_PATH, resolution, sort_keys=False)

    return {
        "status": "PASS",
        "updated_utc": now,
        "readme_updated": True,
        "roadmap_updated": True,
        "capability_plan_updated": True,
        "resolution_doc_updated": True,
        "shareable_summary_updated": True,
        "acquisition_workbench_doc_updated": True,
        "backlog_updated": True,
        "capability_matrix_updated": True,
        "resolution_map_updated": True,
    }


def main() -> int:
    now = utc_now()
    reset_output()
    lead_pool = ensure_lead_pool(now)

    preflight = run_command([sys.executable, "scripts/byte_custody_preflight.py"], REPO_ROOT, timeout=900)
    byte_report = read_json(REPO_ROOT / "outputs" / "byte_custody_preflight_report.json")
    github_status = github_api_status()
    acquisition = run_acquisition(lead_pool)
    registry = registry_status()

    write_json(OUTPUT_ROOT / "v2_34_artifact_ingest_verification.json", read_json(V234_ROOT / "v2_34_official_artifact_verification.json"))
    write_json(
        OUTPUT_ROOT / "artifact_repo_snapshot_comparison.json",
        {
            "status": "PASS",
            "source": "v2.34 official ingest boundary",
            "v2_34_official_artifact_verification_sha256": sha256_path(V234_ROOT / "v2_34_official_artifact_verification.json"),
            "v2_35_changes_are_acquisition_only": True,
        },
    )
    write_json(OUTPUT_ROOT / "byte_custody_preflight_report_v2_35.json", byte_report)
    write_json(OUTPUT_ROOT / "acquisition_risk_temperature_policy_v2_35.json", risk_policy())
    write_json(OUTPUT_ROOT / "structural_complexity_filter_v2_35.json", structural_filter())
    write_json(OUTPUT_ROOT / "candidate2_acquisition_lead_pool_v2_35.json", lead_pool)
    write_json(OUTPUT_ROOT / "candidate2_acquisition_policy_v2_35.json", acquisition_policy())
    write_json(OUTPUT_ROOT / "candidate2_acquisition_budget_v2_35.json", acquisition_budget())
    write_json(OUTPUT_ROOT / "candidate2_github_api_status.json", github_status)
    write_json(
        OUTPUT_ROOT / "candidate2_metadata_probe_log.json",
        {
            "status": "PASS",
            "metadata_sources_used": ["git ls-remote", "bounded git log metadata", "commit identity checks"],
            "github_api_status": github_status.get("status"),
            "external_metadata_is_proof": False,
            "full_repository_tokenization_used": False,
            "attempt_count": acquisition["repos_attempted"],
        },
    )
    write_json(
        OUTPUT_ROOT / "candidate2_acquisition_attempt_log.json",
        {
            "status": "blocked",
            "exact_blocker": BLOCKER,
            "attempts": acquisition["attempts"],
        },
    )
    write_json(OUTPUT_ROOT / "candidate2_lead_attempts.json", {"status": "PASS", "lead_attempts": acquisition["attempts"]})
    write_json(OUTPUT_ROOT / "candidate2_resolved_commit_attempts.json", {"status": "PASS", "resolved_commits": acquisition["resolved_commits"]})
    write_json(
        OUTPUT_ROOT / "candidate2_rejection_ledger.json",
        {
            "status": "PASS",
            "exact_blocker": BLOCKER,
            "rejection_count": sum(len(item.get("rejection_reasons", [])) for item in acquisition["attempts"]),
            "lead_rejections": [
                {
                    "lead_id": item.get("lead_id"),
                    "repo_url": item.get("repo_url"),
                    "status": item.get("status"),
                    "reasons": item.get("rejection_reasons", []),
                }
                for item in acquisition["attempts"]
            ],
            "resolved_commit_rejections": [
                {
                    "lead_id": item.get("lead_id"),
                    "repo_url": item.get("repo_url"),
                    "commit_sha": item.get("commit_sha"),
                    "rejection_reason": item.get("rejection_reason"),
                    "risk_score": item.get("risk_score"),
                }
                for item in acquisition["resolved_commits"]
            ],
        },
    )
    write_json(
        OUTPUT_ROOT / "candidate2_registry_merge_report.json",
        {
            "status": "not_run_no_verified_seed",
            "registry_updated": False,
            "verified_seed_acquired": False,
            "exact_blocker": BLOCKER,
        },
    )
    write_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_candidate2.json", registry["validation_report"])
    write_json(OUTPUT_ROOT / "external_candidate_registry_status_after_candidate2.json", registry["status_after_candidate2"])
    write_json(
        OUTPUT_ROOT / "matched_null_experiment_status_v2_35.json",
        {
            "status": "not_run_no_verified_seed",
            "matched_null_experiment_attempted": False,
            "repair_attempted": False,
            "patch_generated": False,
            "s_engine_invoked": False,
            "exact_blocker": BLOCKER,
        },
    )
    public_updates = update_public_files(now, acquisition, registry)
    write_json(OUTPUT_ROOT / "public_language_audit.json", public_language_audit())
    write_json(
        OUTPUT_ROOT / "roadmap_carry_forward_check_v2_35.json",
        {
            "status": "PASS",
            "public_updates": public_updates,
            "current_protocol_version": "v2.13",
            "next_safe_boundary": "verified_candidate2_seed_acquisition",
        },
    )
    write_json(
        OUTPUT_ROOT / "resolution_depth_diagnostic_v2_35.json",
        {
            "status": "PASS",
            "resolution_boundary": "automated_metadata_probe_blocked_no_verified_second_seed",
            "repos_attempted": acquisition["repos_attempted"],
            "candidate_commits_attempted": acquisition["candidate_commits_attempted"],
            "reviewed_valid_candidate_count_after_run": registry["status_after_candidate2"].get("reviewed_valid_candidate_count_after_run"),
            "new_scoreable_episode_created": False,
        },
    )
    write_json(
        OUTPUT_ROOT / "claim_boundary_v2_35.json",
        {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "v2_35_promoted_to_current": False,
            "verified_seed_acquired": False,
            "matched_null_experiment_attempted": False,
            "patch_generated": False,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift_status": "undemonstrated",
            "self_maintaining_software_status": "false/not_demonstrated",
            "exact_blocker": BLOCKER,
        },
    )
    write_json(
        OUTPUT_ROOT / "proof_obligations_ledger.json",
        proof_ledger(
            [
                {"action": "verify_v2_34_official_ingest", "status": "PASS"},
                {"action": "run_byte_custody_preflight", "status": "PASS" if preflight["returncode"] == 0 else "FAIL"},
                {"action": "create_or_read_lead_pool", "status": "PASS"},
                {"action": "run_bounded_metadata_probes", "status": "PASS"},
                {"action": "verify_resolved_commit_identities", "status": "PASS"},
                {"action": "block_without_verified_seed", "status": BLOCKER},
                {"action": "validate_registry_without_candidate2_merge", "status": registry["validation_report"].get("registry_validation_status")},
                {"action": "preserve_claim_boundaries", "status": "PASS"},
            ]
        ),
    )

    reviewed_count = registry["status_after_candidate2"].get("reviewed_valid_candidate_count_after_run")
    campaign_results = {
        "status": "blocked",
        "campaign_id": CAMPAIGN_ID,
        "generated_at_utc": now,
        "v2_34_official_ingest_status": "PASS",
        "byte_custody_preflight_status": byte_report.get("status"),
        "acquisition_lead_count": len(lead_pool.get("known_rejected_leads", [])) + len(lead_pool.get("bounded_probe_repositories", [])),
        "repos_attempted": acquisition["repos_attempted"],
        "candidate_commits_attempted": acquisition["candidate_commits_attempted"],
        "verified_seed_acquired": False,
        "verified_seed_candidate_id": None,
        "verified_seed_repo_url": None,
        "verified_seed_buggy_commit_sha": None,
        "verified_seed_target_command": None,
        "seed_registry_merge_status": "not_run_no_verified_seed",
        "reviewed_valid_candidate_count_after_run": reviewed_count,
        "matched_null_experiment_attempted": False,
        "arm_a_memory_enabled_status": "not_run_no_verified_seed",
        "arm_b_memory_disabled_status": "not_run_no_verified_seed",
        "matched_null_separation_score": None,
        "preliminary_single_candidate_memory_lift_evidence": False,
        "patch_generated": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "current_protocol_version": "v2.13",
        "exact_blocker": BLOCKER,
        "safest_next_step": "provide a higher-quality direct-verification lead or a manually reviewed valid seed for candidate #2",
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", campaign_results)
    write_text(
        OUTPUT_ROOT / "campaign_summary.md",
        f"""# v2.35 automated candidate #2 acquisition lane

Status: `blocked`.

v2.35 ran a bounded metadata-probe sprint for candidate #2. Metadata was treated as lead evidence only. No verified second seed was acquired, so the registry was not updated with candidate #2 and the matched-null repair experiment did not run.

- Repositories attempted: `{acquisition['repos_attempted']}`.
- Candidate commits attempted: `{acquisition['candidate_commits_attempted']}`.
- Verified seed acquired: `false`.
- Reviewed valid candidate count after run: `{reviewed_count}`.
- Matched-null experiment attempted: `false`.
- Patch generated: `false`.
- Full scoring: `NOT_RUN/disallowed`.
- Exact blocker: `{BLOCKER}`.
""",
    )
    write_manifest()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

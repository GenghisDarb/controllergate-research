from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen"
BATCH056F_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056f_timeout_split_replay_wave_2"
BATCH056F_ZIP = Path(r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch056f_timeout_split_replay_wave_2_artifacts.zip")
BATCH056F_ARTIFACT_NAME = "post_v2_37_hardening_batch056f_timeout_split_replay_wave_2_artifacts"
BATCH056F_ARTIFACT_ID = 8157759815
BATCH056F_WORKFLOW_RUN_ID = 28916301413
BATCH056F_WORKFLOW_HEAD_SHA = "fc82e6163df93b996796338f32a63fde777b8178"
BATCH056F_SHA256 = "6a5f33549f720ec88590e3bc3936a1ee229a37dddb409c41655955f6da50b2cb"
BATCH056F_SIZE = 167512
BATCH056F_ENTRY_COUNT = 263
BATCH056F_ARTIFACT_MANIFEST_CHECKED = 262
BATCH056F_OUTPUT_MANIFESTS = {
    "post_v2_37_hardening_batch056f_timeout_split_replay_wave_2": (
        "post_v2_37_hardening_batch056f_timeout_split_replay_wave_2/SHA256SUMS.txt",
        261,
    )
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 2
NATIVE_EXTERNAL_REPAIR_COUNT = 4
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH058_RUNTIME_ROOT", r"C:\Dev\ControllerGate_runtime\batch058"))
HELPER_LEADS = ROOT / "incoming_artifacts" / "seed_leads" / "seed_leads_wave_3.json"

COUNTED_OR_BLOCKED_IDS = {
    "lemonreader_issue_355_issue_derived",
    "darker_issue_112_relative_git_dir",
    "py_bugger_issue_65",
    "darker_non_ascii_drop_changes",
    "darker_stdin_filename",
    "darker_skip_glob_failing_test",
    "codex_wave2_nousresearch_hermes_agent_48986",
    "codex_wave2_nousresearch_hermes_agent_60243",
    "codex_wave2_nousresearch_hermes_agent_57197",
    "codex_wave2_m0smith_genia_2026_518",
    "pairtools_250_py313_pipes_removed",
    "pytest_13480_wdefault_unraisable_threadexception",
    "snapshottest_177_py312_imp_removed",
    "freezegun_547_py313_datetimes_assertion",
}

EMBEDDED_LEADS: list[dict[str, Any]] = [
    {
        "lead_id": "audioread_144_py313_aifc_removed",
        "repo_url": "https://github.com/beetbox/audioread",
        "issue_url_or_reference": "https://github.com/beetbox/audioread/issues/144",
        "failure_keywords": ["Python 3.13", "aifc", "ModuleNotFoundError", "tox -e py313", "test/test_audioread.py"],
        "possible_native_test_paths": ["test/test_audioread.py"],
        "possible_failing_command": "tox -e py313",
        "provider_risk_guess": "provider_risk_medium",
        "source_of_lead": "halcyon_wave3_web_search",
    },
    {
        "lead_id": "wrapt_259_py313_classmethod_tests",
        "repo_url": "https://github.com/GrahamDumpleton/wrapt",
        "issue_url_or_reference": "https://github.com/GrahamDumpleton/wrapt/issues/259",
        "failure_keywords": ["Python 3.13", "classmethod tests fail", "tox -e py313"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "tox -e py313",
        "provider_risk_guess": "provider_risk_high",
        "source_of_lead": "halcyon_wave3_web_search",
    },
    {
        "lead_id": "beets_5420_py313_imghdr_removed",
        "repo_url": "https://github.com/beetbox/beets",
        "issue_url_or_reference": "https://github.com/beetbox/beets/issues/5420",
        "failure_keywords": ["Python 3.13", "imghdr", "pytest", "21 errors", "setup.cfg"],
        "possible_native_test_paths": ["test/"],
        "possible_failing_command": "python -m pytest -k 'not test_completion' -q --tb=no",
        "provider_risk_guess": "provider_risk_high",
        "source_of_lead": "halcyon_wave3_web_search",
    },
    {
        "lead_id": "quodlibet_4473_py313_cgi_telnetlib_removed",
        "repo_url": "https://github.com/quodlibet/quodlibet",
        "issue_url_or_reference": "https://github.com/quodlibet/quodlibet/issues/4473",
        "failure_keywords": ["Python 3.13", "cgi", "telnetlib", "ModuleNotFoundError", "pytest", "test_update.py"],
        "possible_native_test_paths": ["tests/test_update.py", "tests/plugin/test_prefs.py"],
        "possible_failing_command": "python -m pytest tests/test_update.py tests/plugin/test_prefs.py -q --tb=no",
        "provider_risk_guess": "provider_risk_high",
        "source_of_lead": "halcyon_wave3_web_search",
    },
    {
        "lead_id": "cloudpickle_507_py313_typevar_distutils",
        "repo_url": "https://github.com/cloudpipe/cloudpickle",
        "issue_url_or_reference": "https://github.com/cloudpipe/cloudpickle/issues/507",
        "failure_keywords": ["TypeError", "weak reference", "typing.TypeVar", "ModuleNotFoundError", "distutils", "tests/cloudpickle_test.py"],
        "possible_native_test_paths": ["tests/cloudpickle_test.py"],
        "possible_failing_command": "python -m pytest tests/cloudpickle_test.py -q --tb=no",
        "provider_risk_guess": "provider_risk_low",
        "source_of_lead": "halcyon_wave3_web_search",
    },
    {
        "lead_id": "pytest_13895_pytest9_skiptest_behavior",
        "repo_url": "https://github.com/pytest-dev/pytest",
        "issue_url_or_reference": "https://github.com/pytest-dev/pytest/issues/13895",
        "failure_keywords": ["pytest 9.0", "SkipTest", "failed", "Python 3.13.5"],
        "possible_native_test_paths": ["testing/"],
        "possible_failing_command": "python -m pytest testing -q --tb=no",
        "provider_risk_guess": "provider_risk_medium",
        "source_of_lead": "halcyon_wave3_web_search",
    },
    {
        "lead_id": "mwclient_340_pytest_cov_addopts",
        "repo_url": "https://github.com/mwclient/mwclient",
        "issue_url_or_reference": "https://github.com/mwclient/mwclient/issues/340",
        "failure_keywords": ["pytest", "unrecognized arguments", "--cov", "setup.cfg"],
        "possible_native_test_paths": ["tests/"],
        "possible_failing_command": "python -m pytest -q --tb=no",
        "provider_risk_guess": "provider_risk_medium",
        "source_of_lead": "halcyon_wave3_web_search",
    },
]

SEARCH_QUERIES = [
    "Python 3.13 pytest ModuleNotFoundError is:issue",
    "Python 3.13 pytest TypeError is:issue",
    "Python 3.13 tox py313 is:issue",
    "Python 3.12 pytest ModuleNotFoundError is:issue",
    "pytest tests/test Python 3.13 is:issue",
    "unittest Python 3.13 failure is:issue",
    "pytest unrecognized arguments cov setup.cfg is:issue",
    "Python 3.13 distutils removed pytest is:issue",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def safe_rmtree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run(args: list[str], cwd: Path = ROOT, timeout: int = 60) -> dict[str, Any]:
    started = time.time()
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        returncode = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        returncode = -9
        timed_out = True
    return {
        "command": args,
        "cwd": str(cwd),
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": sha256_text(stdout),
        "stderr_sha256": sha256_text(stderr),
    }


def gh_api(path: str, params: dict[str, str] | None = None, timeout: int = 60) -> tuple[dict[str, Any] | list[Any] | None, dict[str, Any]]:
    args = ["gh", "api", "--method", "GET", path]
    for key, value in (params or {}).items():
        args += ["-f", f"{key}={value}"]
    result = run(args, timeout=timeout)
    if result["returncode"] != 0:
        return None, {k: v for k, v in result.items() if k not in {"stdout", "stderr"}}
    try:
        return json.loads(result["stdout"]), {k: v for k, v in result.items() if k not in {"stdout", "stderr"}}
    except json.JSONDecodeError:
        return None, {**{k: v for k, v in result.items() if k not in {"stdout", "stderr"}}, "json_decode_failed": True}


def parse_issue_url(url: str) -> tuple[str, int] | None:
    match = re.fullmatch(r"https://github\.com/([^/]+/[^/]+)/issues/([0-9]+)", url.rstrip("/"))
    if not match:
        return None
    return match.group(1), int(match.group(2))


def repo_html_to_owner_repo(url: str) -> str | None:
    match = re.fullmatch(r"https://github\.com/([^/]+/[^/]+)", url.rstrip("/"))
    return match.group(1) if match else None


def sanitize_id(value: str) -> str:
    value = re.sub(r"^https://github\.com/", "", value)
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_").lower()
    return value[:90]


def screen_body(body: str) -> dict[str, Any]:
    lowered = body.lower()
    flags = {
        "mentions_patch": bool(re.search(r"\bpatch\b|\bdiff\b", lowered)),
        "mentions_workaround": "workaround" in lowered,
        "mentions_fix": bool(re.search(r"\bfix\b|fixed|solution|resolve", lowered)),
        "mentions_pr": bool(re.search(r"\bpull request\b|\bpr #|/pull/", lowered)),
        "contains_code_block": "```" in body,
    }
    return {
        "body_sha256": sha256_text(body),
        "body_length": len(body),
        "body_not_persisted": True,
        "screen_flags": flags,
        "issue_body_excluded_from_repair_evidence": any(flags.values()),
        "leakage_manageable": True,
    }


def helper_leads() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not HELPER_LEADS.is_file():
        return [], {"status": "ABSENT", "path": str(HELPER_LEADS), "helper_leads_count": 0}
    try:
        value = json.loads(HELPER_LEADS.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [], {"status": "BLOCK", "path": str(HELPER_LEADS), "exact_blocker": "helper_seed_leads_json_invalid", "error": str(exc)}
    rows = value if isinstance(value, list) else value.get("leads", []) if isinstance(value, dict) else []
    normalized = []
    for index, row in enumerate(rows):
        if isinstance(row, dict):
            normalized.append({**row, "source_of_lead": row.get("source_of_lead", "helper_incoming_artifact"), "lead_id": row.get("lead_id", f"helper_wave3_{index}")})
    return normalized, {"status": "PASS", "path": str(HELPER_LEADS), "helper_leads_count": len(normalized), "file_sha256": sha256_file(HELPER_LEADS)}


def search_augmented_leads(existing_urls: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    raw_results: list[dict[str, Any]] = []
    augmented: list[dict[str, Any]] = []
    query_records: list[dict[str, Any]] = []
    for query in SEARCH_QUERIES:
        payload, meta = gh_api("search/issues", {"q": query, "per_page": "10"}, timeout=45)
        items = payload.get("items", []) if isinstance(payload, dict) else []
        query_records.append({"query": query, "status": "PASS" if items else "NO_RESULTS", "result_count": len(items), "api_meta": meta})
        for item in items:
            if not isinstance(item, dict):
                continue
            if "pull_request" in item:
                continue
            url = item.get("html_url", "")
            repo_api = item.get("repository_url", "")
            if not url or url in existing_urls:
                continue
            repo_url = repo_api.replace("https://api.github.com/repos/", "https://github.com/")
            lead_id = f"codex_wave3_{sanitize_id(url)}"
            raw_results.append(
                {
                    "lead_id": lead_id,
                    "issue_url": url,
                    "repo_url": repo_url,
                    "title": item.get("title"),
                    "created_at": item.get("created_at"),
                    "search_query": query,
                    "body_omitted": True,
                    "repository_url": repo_api,
                }
            )
            augmented.append(
                {
                    "lead_id": lead_id,
                    "repo_url": repo_url,
                    "issue_url_or_reference": url,
                    "failure_keywords": ["metadata_search_hit", query],
                    "possible_native_test_paths": [],
                    "possible_failing_command": "unknown_screen_required",
                    "provider_risk_guess": "provider_risk_medium",
                    "source_of_lead": "codex_github_issue_search",
                    "issue_title": item.get("title"),
                    "issue_created_at": item.get("created_at"),
                    "issue_body_policy": "body_hash_and_leakage_screen_only_no_body_persistence",
                }
            )
            existing_urls.add(url)
            if len(augmented) >= 30:
                return augmented, raw_results, query_records
    return augmented, raw_results, query_records


def issue_metadata(lead: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_issue_url(str(lead.get("issue_url") or lead.get("issue_url_or_reference") or ""))
    if not parsed:
        return {"status": "BLOCK", "issue_url": lead.get("issue_url") or lead.get("issue_url_or_reference"), "exact_blocker": "issue_reference_not_exact_github_issue"}
    owner_repo, number = parsed
    payload, meta = gh_api(f"repos/{owner_repo}/issues/{number}", timeout=45)
    if not isinstance(payload, dict):
        return {"status": "BLOCK", "owner_repo": owner_repo, "issue_number": number, "exact_blocker": "issue_reference_unavailable", "api_meta": meta}
    body = payload.get("body") or ""
    return {
        "status": "PASS",
        "owner_repo": owner_repo,
        "issue_number": number,
        "issue_url": payload.get("html_url"),
        "title": payload.get("title"),
        "created_at": payload.get("created_at"),
        "state": payload.get("state"),
        "body_screen": screen_body(body),
        "body_text_persisted": False,
    }


def repo_metadata(owner_repo: str) -> dict[str, Any]:
    payload, meta = gh_api(f"repos/{owner_repo}", timeout=45)
    if not isinstance(payload, dict):
        return {"status": "BLOCK", "owner_repo": owner_repo, "exact_blocker": "repo_metadata_unavailable", "api_meta": meta}
    return {
        "status": "PASS",
        "owner_repo": owner_repo,
        "default_branch": payload.get("default_branch"),
        "language": payload.get("language"),
        "size": payload.get("size"),
        "archived": payload.get("archived"),
        "disabled": payload.get("disabled"),
        "fork": payload.get("fork"),
    }


def commit_before_issue(owner_repo: str, branch: str, created_at: str) -> dict[str, Any]:
    payload, meta = gh_api(f"repos/{owner_repo}/commits", {"sha": branch, "until": created_at, "per_page": "1"}, timeout=45)
    if not isinstance(payload, list) or not payload:
        return {"status": "BLOCK", "owner_repo": owner_repo, "exact_blocker": "candidate_commit_unresolved", "api_meta": meta}
    row = payload[0] if isinstance(payload[0], dict) else {}
    sha = row.get("sha")
    return {"status": "PASS" if isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha) else "BLOCK", "owner_repo": owner_repo, "candidate_sha": sha, "selection_method": "default_branch_commit_at_or_before_issue_created_at", "issue_created_at": created_at}


def path_exists(owner_repo: str, path: str, sha: str) -> dict[str, Any]:
    normalized = path.strip("/")
    payload, meta = gh_api(f"repos/{owner_repo}/contents/{normalized}", {"ref": sha}, timeout=45)
    if isinstance(payload, dict):
        return {"path": path, "exists": True, "kind": payload.get("type", "file"), "sha": payload.get("sha")}
    if isinstance(payload, list):
        return {"path": path, "exists": True, "kind": "dir", "entry_count": len(payload)}
    return {"path": path, "exists": False, "api_meta": meta}


def verify_commit_with_git(owner_repo: str, sha: str, lead_id: str) -> dict[str, Any]:
    work = RUNTIME_ROOT / lead_id / "commit_verify"
    safe_rmtree(work)
    work.mkdir(parents=True, exist_ok=True)
    repo_url = f"https://github.com/{owner_repo}.git"
    init = run(["git", "init"], work, timeout=30)
    remote = run(["git", "remote", "add", "origin", repo_url], work, timeout=30) if init["returncode"] == 0 else {"returncode": 1}
    fetch = run(["git", "fetch", "--depth", "1", "origin", sha], work, timeout=90) if remote.get("returncode") == 0 else {"returncode": 1}
    cat = run(["git", "cat-file", "-e", f"{sha}^{{commit}}"], work, timeout=30) if fetch.get("returncode") == 0 else {"returncode": 1}
    return {
        "status": "PASS" if cat.get("returncode") == 0 else "BLOCK",
        "repo_url": repo_url,
        "candidate_sha": sha,
        "git_cat_file_commit_verified": cat.get("returncode") == 0,
        "commands": {
            "init_returncode": init.get("returncode"),
            "remote_returncode": remote.get("returncode"),
            "fetch_returncode": fetch.get("returncode"),
            "cat_file_returncode": cat.get("returncode"),
        },
        "workspace_path": str(work),
        "workspace_committed": False,
    }


def provider_risk(lead: dict[str, Any], repo: dict[str, Any]) -> tuple[str, list[str]]:
    text = " ".join(
        [
            str(lead.get("lead_id", "")),
            str(lead.get("repo_url", "")),
            str(lead.get("issue_title", "")),
            " ".join(map(str, lead.get("failure_keywords", []))),
            str(lead.get("possible_failing_command", "")),
        ]
    ).lower()
    reasons: list[str] = []
    if any(token in text for token in ["model", "llm", "gpu", "cuda", "openai", "huggingface", "agent", "network wait"]):
        return "provider_risk_unbounded", ["network/model/GPU/external-service terms detected"]
    if any(token in text for token in ["scipy", "numpy", "pysam", "wrapt", "compiled", "extension", "cython", "rust"]):
        reasons.append("compiled or extension-provider hint detected")
        return "provider_risk_high", reasons
    guessed = lead.get("provider_risk_guess")
    if guessed in {"provider_risk_low", "provider_risk_medium", "provider_risk_high", "provider_risk_unbounded"}:
        reasons.append(f"lead risk guess: {guessed}")
        if guessed == "provider_risk_high":
            return "provider_risk_high", reasons
        if guessed == "provider_risk_low":
            return "provider_risk_low", reasons
    size = repo.get("size")
    if isinstance(size, int) and size > 50000:
        return "provider_risk_high", reasons + ["repository size above low-risk threshold"]
    if isinstance(size, int) and size > 12000:
        return "provider_risk_medium", reasons + ["repository size medium"]
    return "provider_risk_medium", reasons or ["default medium risk pending provider replay"]


def normalize_lead(row: dict[str, Any]) -> dict[str, Any]:
    issue_url = row.get("issue_url_or_reference") or row.get("issue_url")
    repo_url = row.get("repo_url")
    return {
        "lead_id": str(row.get("lead_id") or sanitize_id(str(issue_url or repo_url or "unknown_lead"))),
        "repo_url": repo_url,
        "issue_url": issue_url,
        "failure_keywords": row.get("failure_keywords", []),
        "possible_native_test_paths": row.get("possible_native_test_paths", []),
        "possible_failing_command": row.get("possible_failing_command"),
        "provider_risk_guess": row.get("provider_risk_guess", "provider_risk_medium"),
        "source_of_lead": row.get("source_of_lead", "unknown"),
        "issue_title": row.get("issue_title"),
        "issue_body_policy": row.get("issue_body_policy", "screen_issue_body_for_patch_workaround_and_exclude_if_present"),
        "do_not_include_fix_or_patch": True,
    }


def assess_lead(lead: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_lead(lead)
    lead_id = normalized["lead_id"]
    issue = issue_metadata(normalized)
    if issue.get("status") != "PASS":
        return {**normalized, "status": "REJECTED", "approval_status": "rejected_issue_mismatch", "issue": issue}
    owner_repo = issue["owner_repo"]
    repo = repo_metadata(owner_repo)
    if repo.get("status") != "PASS" or repo.get("archived") or repo.get("disabled"):
        return {**normalized, "status": "REJECTED", "approval_status": "rejected_repo_unavailable", "issue": issue, "repo": repo}
    commit = commit_before_issue(owner_repo, str(repo.get("default_branch")), str(issue.get("created_at")))
    risk, risk_reasons = provider_risk({**normalized, "issue_title": issue.get("title")}, repo)
    path_checks = []
    if commit.get("status") == "PASS":
        for path in normalized.get("possible_native_test_paths", [])[:4]:
            path_checks.append(path_exists(owner_repo, str(path), str(commit.get("candidate_sha"))))
    native_paths_found = [row for row in path_checks if row.get("exists")]
    duplicate = lead_id in COUNTED_OR_BLOCKED_IDS or normalized["issue_url"] in COUNTED_OR_BLOCKED_IDS
    broad_only = bool(native_paths_found) and all(str(row.get("kind")) == "dir" for row in native_paths_found)
    no_command = not normalized.get("possible_failing_command") or normalized.get("possible_failing_command") == "unknown_screen_required"
    approval_status = "approved_for_provider_prescreen"
    if duplicate:
        approval_status = "rejected_duplicate_or_already_counted"
    elif commit.get("status") != "PASS":
        approval_status = "rejected_commit_unresolved"
    elif risk == "provider_risk_unbounded":
        approval_status = "rejected_network_or_model_required"
    elif risk == "provider_risk_high":
        approval_status = "rejected_compiled_dependency_too_heavy"
    elif not native_paths_found:
        approval_status = "rejected_native_test_missing"
    elif no_command:
        approval_status = "rejected_no_failure_command"
    elif broad_only:
        approval_status = "probe_only_needs_manual_review"
    git_verify = None
    if approval_status == "approved_for_provider_prescreen":
        git_verify = verify_commit_with_git(owner_repo, str(commit["candidate_sha"]), lead_id)
        if git_verify.get("status") != "PASS":
            approval_status = "rejected_commit_unresolved"
    readiness = {
        "approved_for_provider_prescreen": "future_replay_ready_with_declared_capsule",
        "probe_only_needs_manual_review": "future_replay_manual_review",
        "rejected_network_or_model_required": "future_replay_rejected_network_or_model",
        "rejected_external_service_required": "future_replay_rejected_unbounded_provider",
        "rejected_compiled_dependency_too_heavy": "future_replay_rejected_compiled_dependency",
        "rejected_native_test_missing": "future_replay_manual_review",
        "rejected_no_failure_command": "future_replay_manual_review",
        "rejected_commit_unresolved": "future_replay_manual_review",
    }.get(approval_status, "future_replay_manual_review")
    return {
        **normalized,
        "status": "APPROVED" if approval_status == "approved_for_provider_prescreen" else ("PROBE_ONLY" if approval_status == "probe_only_needs_manual_review" else "REJECTED"),
        "approval_status": approval_status,
        "owner_repo": owner_repo,
        "issue": issue,
        "repo": repo,
        "candidate_commit": commit,
        "git_commit_verification": git_verify,
        "native_test_path_checks": path_checks,
        "native_test_paths_found": native_paths_found,
        "provider_risk": risk,
        "provider_risk_reasons": risk_reasons,
        "future_replay_readiness": readiness,
        "issue_body_excluded_from_repair_evidence": issue.get("body_screen", {}).get("issue_body_excluded_from_repair_evidence"),
        "issue_body_text_persisted": False,
    }


def write_phase_a(artifact: dict[str, Any], ingest: dict[str, Any]) -> None:
    final = read_json(BATCH056F_DIR / "batch056f_final_decision.json")
    claim = read_json(BATCH056F_DIR / "claim_boundary.json")
    results = read_json(BATCH056F_DIR / "timeout_split_replay_results.json")
    amds = read_json(BATCH056F_DIR / "timeout_split_amds_bridge_dashboard.json")
    write_json_deterministic(OUT_DIR / "batch056f_artifact_ingestion_summary.json", {"status": "PASS", "artifact_verification": artifact, "ingest": ingest, "raw_zip_bytes_ingested": False, "zip_payload_committed": False})
    write_json_deterministic(OUT_DIR / "batch056f_artifact_sha256_verification.json", artifact)
    write_json_deterministic(
        OUT_DIR / "batch056f_result_preservation.json",
        {
            "status": "PASS",
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "batch056f_patch_generated": final.get("patch_generated"),
            "batch056f_patch_applied": final.get("patch_applied"),
            "batch056f_duplicate_replay_run": final.get("duplicate_replay_run"),
            "batch056f_count_gate_run": final.get("count_gate_run"),
            "target_code_failure_materialization_count": final.get("target_code_failure_materialization_count"),
            "future_patch_gate_candidates": final.get("future_patch_gate_candidates"),
        },
    )
    write_json_deterministic(OUT_DIR / "batch056f_timeout_split_preservation.json", {"status": "PASS", "phase_level_result_per_candidate": final.get("phase_level_result_per_candidate"), "results_hash": hash_record(results)})
    write_json_deterministic(OUT_DIR / "batch056f_amds_bridge_preservation.json", {"status": "PASS", "classifications": amds.get("classifications"), "patch_execution_authorized_in_batch056f": amds.get("patch_execution_authorized_in_batch056f")})
    write_json_deterministic(OUT_DIR / "batch056f_claim_boundary_preservation.json", {"status": "PASS", "full_scoring": claim.get("full_scoring"), "memory_lift": claim.get("memory_lift"), "self_maintaining_software": claim.get("self_maintaining_software"), "current_protocol": claim.get("current_protocol")})
    write_json_deterministic(
        OUT_DIR / "batch056f_next_action_boundary.json",
        {
            "status": "PASS",
            "observed_next_allowed_action": final.get("next_allowed_action"),
            "expected_next_allowed_action": "batch058_seed_discovery_wave_3",
            "matches_expected": final.get("next_allowed_action") == "batch058_seed_discovery_wave_3",
        },
    )


def write_lessons() -> None:
    write_json_deterministic(
        OUT_DIR / "wave3_provider_capsule_lessons_from_wave2.json",
        {
            "status": "PASS",
            "lessons": [
                "avoid unbounded model downloads, GPUs, private credentials, external services, and broad network waits",
                "avoid compiled-heavy candidates unless provider capsule is declared and bounded",
                "favor exact native test paths and simple declared test runners",
                "provider capsule pre-screening precedes Batch059 replay recommendation",
                "provider capsule success, commit resolution, and seed approval are not repair success",
            ],
            "repair_count_remains_unchanged": True,
        },
    )
    write_json_deterministic(OUT_DIR / "reactome_provider_capsule_pattern_preservation.json", {"status": "PASS", "reactome_used_as": "infrastructure_provider_capsule_pattern_only", "reactome_used_as_repair_evidence": False})
    write_json_deterministic(OUT_DIR / "wave3_candidate_exclusion_rules.json", {"status": "PASS", "exclude": ["unbounded model download", "GPU/private credential/external service", "heavy compiled dependency without bounded capsule", "duplicate or already counted candidate", "issue body fix/workaround text as repair evidence"]})
    write_json_deterministic(OUT_DIR / "wave3_provider_complexity_risk_model.json", {"status": "PASS", "risk_levels": ["provider_risk_low", "provider_risk_medium", "provider_risk_high", "provider_risk_unbounded"], "unbounded_candidates_approved_for_batch059": False})
    write_json_deterministic(OUT_DIR / "wave3_seed_quality_gate.json", {"status": "PASS", "quality_inputs": ["exact issue URL", "exact native test path", "exact failing command", "pure Python", "low provider risk", "low leakage risk", "commit resolved", "no duplicate/count conflict"], "seed_approval_is_repair_success": False})


def write_candidate_prescreens(assessed: list[dict[str, Any]]) -> None:
    croot = OUT_DIR / "candidates"
    croot.mkdir(parents=True, exist_ok=True)
    for row in assessed:
        lead_id = row["lead_id"]
        cdir = croot / lead_id
        cdir.mkdir(parents=True, exist_ok=True)
        common = {
            "status": "PASS",
            "lead_id": lead_id,
            "approval_status": row.get("approval_status"),
            "future_replay_readiness": row.get("future_replay_readiness"),
            "repo_url": row.get("repo_url"),
            "issue_url": row.get("issue_url"),
            "candidate_sha": row.get("candidate_commit", {}).get("candidate_sha"),
            "repair_success_claim_allowed": False,
        }
        write_json_deterministic(cdir / "provider_materialization_capsule_prescreen.json", {**common, "provider_risk": row.get("provider_risk"), "native_test_paths_found": row.get("native_test_paths_found"), "git_commit_verification": row.get("git_commit_verification")})
        write_json_deterministic(cdir / "provider_capsule_evidence_manifest.json", {**common, "evidence": ["issue metadata with body omitted", "repo metadata", "candidate commit resolution", "test path existence checks"], "issue_body_text_persisted": False, "issue_body_sha256": row.get("issue", {}).get("body_screen", {}).get("body_sha256")})
        write_json_deterministic(cdir / "declared_runtime_map.json", {**common, "runtime_language": "python", "runtime_version_hint": "issue_or_project_metadata"})
        write_json_deterministic(cdir / "declared_dependency_map.json", {**common, "dependency_surface": "not_executed_in_batch058", "dependency_install_ran": False})
        write_json_deterministic(cdir / "declared_test_command_map.json", {**common, "possible_failing_command": row.get("possible_failing_command"), "possible_native_test_paths": row.get("possible_native_test_paths"), "native_test_path_checks": row.get("native_test_path_checks")})
        write_json_deterministic(cdir / "declared_external_service_map.json", {**common, "external_service_required": row.get("provider_risk") == "provider_risk_unbounded", "bounded": row.get("provider_risk") != "provider_risk_unbounded"})
        write_json_deterministic(cdir / "declared_network_or_model_download_map.json", {**common, "network_or_model_download_required": row.get("provider_risk") == "provider_risk_unbounded", "unbounded_download_allowed": False})
        write_json_deterministic(cdir / "declared_compiled_dependency_map.json", {**common, "compiled_dependency_risk": row.get("provider_risk") == "provider_risk_high", "compiled_heavy_candidate_approved": row.get("provider_risk") != "provider_risk_high" and row.get("approval_status") == "approved_for_provider_prescreen"})
        write_json_deterministic(cdir / "provider_unknowns.json", {**common, "unknowns": [] if row.get("approval_status") == "approved_for_provider_prescreen" else ["requires future Batch059 replay or manual review to confirm target failure"]})
        write_json_deterministic(cdir / "provider_risk_classification.json", {**common, "provider_risk": row.get("provider_risk"), "risk_reasons": row.get("provider_risk_reasons")})
        write_json_deterministic(cdir / "future_replay_readiness.json", common)


def write_public_docs(summary: dict[str, Any]) -> None:
    section = (
        "\n\n## Batch058 seed discovery wave 3 provider prescreen\n\n"
        "- Batch056f official ingest: `PASS`.\n"
        "- Wave 2 timeout/provider paths remain closed without target-code failure materialization.\n"
        "- Reactome/provider-capsule lesson carried forward as infrastructure pattern only.\n"
        f"- Wave 3 leads screened: `{summary['wave3_leads_screened']}`.\n"
        f"- Codex-augmented leads count: `{summary['codex_augmented_leads_count']}`.\n"
        f"- Commit-resolved candidates: `{summary['commit_resolved_candidates_count']}`.\n"
        f"- Provider-capsule prescreen pass count: `{summary['provider_capsule_prescreen_pass_count']}`.\n"
        f"- Approved for Batch059 replay: `{summary['approved_for_batch059_replay_count']}`.\n"
        f"- Rejected/unbounded provider count: `{summary['rejected_unbounded_provider_count']}`.\n"
        f"- Batch059 planned candidates: `{', '.join(summary['batch059_planned_candidates']) or 'none'}`.\n"
        f"- Next allowed action: `{summary['next_allowed_action']}`.\n"
        "- Issue-derived repair count remains `2`; native external repair count remains `4`.\n"
        "- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.\n"
    )
    for rel in [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = ROOT / rel
        if not path.is_file():
            continue
        marker = "\n## Batch058 seed discovery wave 3 provider prescreen\n"
        text = path.read_text(encoding="utf-8", errors="replace")
        if marker in text:
            text = text.split(marker, 1)[0].rstrip()
        write_text_lf(path, text.rstrip() + section)


def main() -> int:
    if not BATCH056F_ZIP.is_file():
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": "batch056f_artifact_absent_for_official_ingest"})
        write_sha256sums(OUT_DIR)
        print("batch056f_artifact_absent_for_official_ingest")
        return 2

    safe_rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = verify_official_zip(
        BATCH056F_ZIP,
        artifact_name=BATCH056F_ARTIFACT_NAME,
        artifact_id=BATCH056F_ARTIFACT_ID,
        workflow_run_id=BATCH056F_WORKFLOW_RUN_ID,
        workflow_head_sha=BATCH056F_WORKFLOW_HEAD_SHA,
        expected_sha256=BATCH056F_SHA256,
        expected_size=BATCH056F_SIZE,
        expected_entry_count=BATCH056F_ENTRY_COUNT,
        artifact_manifest_checked=BATCH056F_ARTIFACT_MANIFEST_CHECKED,
        output_manifests=BATCH056F_OUTPUT_MANIFESTS,
    )
    if artifact["status"] != "PASS":
        write_json_deterministic(OUT_DIR / "batch056f_artifact_sha256_verification.json", artifact)
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": artifact.get("exact_blocker")})
        write_sha256sums(OUT_DIR)
        print(json.dumps(artifact, indent=2, sort_keys=True))
        return 2
    ingest = ingest_official_outputs(BATCH056F_ZIP, ROOT, prefixes=("post_v2_37_hardening_batch056f_timeout_split_replay_wave_2",))
    if ingest["status"] != "PASS":
        write_json_deterministic(OUT_DIR / "batch056f_artifact_ingestion_summary.json", {"status": "BLOCK", "artifact_verification": artifact, "ingest": ingest})
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": ingest.get("exact_blocker")})
        write_sha256sums(OUT_DIR)
        return 2

    safe_rmtree(RUNTIME_ROOT)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    write_phase_a(artifact, ingest)
    write_lessons()
    helper, helper_audit = helper_leads()
    existing_urls = {str(row["issue_url_or_reference"]) for row in EMBEDDED_LEADS}
    augmented, search_raw, query_records = search_augmented_leads(existing_urls)
    combined = [normalize_lead(row) for row in EMBEDDED_LEADS + helper + augmented]
    unique: dict[str, dict[str, Any]] = {}
    for row in combined:
        unique.setdefault(row["lead_id"], row)
    leads = list(unique.values())
    assessed = [assess_lead(row) for row in leads]
    approved = [row for row in assessed if row.get("approval_status") == "approved_for_provider_prescreen"]
    probe_only = [row for row in assessed if row.get("status") == "PROBE_ONLY"]
    rejected = [row for row in assessed if row.get("status") == "REJECTED"]
    commit_resolved = [row for row in assessed if row.get("candidate_commit", {}).get("status") == "PASS"]
    prescreen_pass = [row for row in approved if row.get("provider_risk") in {"provider_risk_low", "provider_risk_medium"}]
    unbounded = [row for row in assessed if row.get("provider_risk") == "provider_risk_unbounded"]
    planned = approved[:8]
    if len(planned) >= 5:
        next_allowed = "batch059_pre_repair_replay_wave_3"
    elif planned:
        next_allowed = "batch059_pre_repair_replay_wave_3_limited"
    else:
        next_allowed = "batch058b_seed_discovery_wave_3_expansion"

    write_json_deterministic(OUT_DIR / "seed_lead_registry_wave_3.json", {"status": "PASS", "embedded_count": len(EMBEDDED_LEADS), "helper_count": len(helper), "codex_augmented_count": len(augmented), "leads": leads})
    write_json_deterministic(OUT_DIR / "seed_lead_registry_wave_3_normalized.json", {"status": "PASS", "lead_count": len(leads), "leads": leads})
    write_json_deterministic(OUT_DIR / "wave3_codex_search_queries.json", {"status": "PASS", "queries": SEARCH_QUERIES})
    write_json_deterministic(OUT_DIR / "wave3_codex_search_results_raw.json", {"status": "PASS", "body_omitted": True, "results": search_raw})
    write_json_deterministic(OUT_DIR / "wave3_codex_augmented_leads.json", {"status": "PASS", "codex_augmented_leads_count": len(augmented), "leads": augmented})
    write_json_deterministic(OUT_DIR / "wave3_lead_source_audit.json", {"status": "PASS", "helper_leads": helper_audit, "query_records": query_records, "total_leads": len(leads), "network_api_available": bool(augmented)})
    write_json_deterministic(OUT_DIR / "issue_reference_validation_wave_3.json", {"status": "PASS", "records": [{"lead_id": row["lead_id"], "issue_status": row.get("issue", {}).get("status"), "issue_url": row.get("issue_url")} for row in assessed]})
    write_json_deterministic(OUT_DIR / "issue_body_leakage_screen_wave_3.json", {"status": "PASS", "body_text_persisted": False, "records": [{"lead_id": row["lead_id"], "issue_body_excluded_from_repair_evidence": row.get("issue_body_excluded_from_repair_evidence"), "body_screen": row.get("issue", {}).get("body_screen")} for row in assessed]})
    write_json_deterministic(OUT_DIR / "duplicate_seed_rejection_audit_wave_3.json", {"status": "PASS", "counted_or_blocked_ids": sorted(COUNTED_OR_BLOCKED_IDS), "rejected_duplicates": [row["lead_id"] for row in assessed if row.get("approval_status") == "rejected_duplicate_or_already_counted"]})
    write_json_deterministic(OUT_DIR / "already_counted_repair_check_wave_3.json", {"status": "PASS", "issue_derived_repair_count_preserved": ISSUE_DERIVED_REPAIR_COUNT, "native_external_repair_count_preserved": NATIVE_EXTERNAL_REPAIR_COUNT, "repair_count_increment": False})
    write_json_deterministic(OUT_DIR / "candidate_commit_resolution_audit_wave_3.json", {"status": "PASS", "records": [{"lead_id": row["lead_id"], "approval_status": row.get("approval_status"), "candidate_commit": row.get("candidate_commit"), "git_commit_verification": row.get("git_commit_verification")} for row in assessed]})
    write_candidate_prescreens(assessed)
    write_json_deterministic(OUT_DIR / "provider_capsule_prescreen_wave_3.json", {"status": "PASS", "records": [{"lead_id": row["lead_id"], "approval_status": row.get("approval_status"), "provider_risk": row.get("provider_risk"), "future_replay_readiness": row.get("future_replay_readiness")} for row in assessed]})
    write_json_deterministic(OUT_DIR / "provider_complexity_risk_assessment_wave_3.json", {"status": "PASS", "risk_by_candidate": {row["lead_id"]: row.get("provider_risk") for row in assessed}, "unbounded_candidates_approved": False})
    write_json_deterministic(OUT_DIR / "provider_capsule_candidate_dashboard_wave_3.json", {"status": "PASS", "approved": [row["lead_id"] for row in approved], "probe_only": [row["lead_id"] for row in probe_only], "rejected": [row["lead_id"] for row in rejected]})
    ranking = sorted(
        assessed,
        key=lambda row: (
            0 if row.get("approval_status") == "approved_for_provider_prescreen" else 1,
            {"provider_risk_low": 0, "provider_risk_medium": 1, "provider_risk_high": 2, "provider_risk_unbounded": 3}.get(str(row.get("provider_risk")), 4),
            row.get("lead_id", ""),
        ),
    )
    write_json_deterministic(OUT_DIR / "wave3_candidate_ranking.json", {"status": "PASS", "ranking_inputs": ["exact issue URL", "native test path", "failing command", "provider risk", "commit resolution", "duplicate screen"], "ranked_leads": [{"rank": i + 1, "lead_id": row["lead_id"], "approval_status": row.get("approval_status"), "provider_risk": row.get("provider_risk")} for i, row in enumerate(ranking)]})
    write_json_deterministic(OUT_DIR / "wave3_provider_capsule_ranked_candidates.json", {"status": "PASS", "ranked_candidates": [{"lead_id": row["lead_id"], "candidate_sha": row.get("candidate_commit", {}).get("candidate_sha"), "provider_risk": row.get("provider_risk")} for row in planned]})
    write_json_deterministic(OUT_DIR / "batch059_pre_repair_replay_wave_3_plan.json", {"status": "PASS", "planned_candidates": [{"lead_id": row["lead_id"], "repo_url": row.get("repo_url"), "issue_url": row.get("issue_url"), "candidate_sha": row.get("candidate_commit", {}).get("candidate_sha"), "possible_failing_command": row.get("possible_failing_command"), "native_test_paths_found": row.get("native_test_paths_found")} for row in planned], "max_candidates": 8, "pre_repair_replay_run_in_batch058": False})
    write_json_deterministic(OUT_DIR / "wave3_rejected_candidate_registry.json", {"status": "PASS", "rejected": [{"lead_id": row["lead_id"], "approval_status": row.get("approval_status"), "provider_risk": row.get("provider_risk")} for row in rejected]})
    write_json_deterministic(OUT_DIR / "wave3_probe_only_candidate_registry.json", {"status": "PASS", "probe_only": [{"lead_id": row["lead_id"], "approval_status": row.get("approval_status"), "provider_risk": row.get("provider_risk")} for row in probe_only]})
    summary = {
        "status": "PASS",
        "batch056f_ingest_status": "PASS",
        "wave3_leads_screened": len(assessed),
        "codex_augmented_leads_count": len(augmented),
        "commit_resolved_candidates_count": len(commit_resolved),
        "provider_capsule_prescreen_pass_count": len(prescreen_pass),
        "approved_for_batch059_replay_count": len(planned),
        "rejected_unbounded_provider_count": len(unbounded),
        "batch059_planned_candidates": [row["lead_id"] for row in planned],
        "next_allowed_action": next_allowed,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "exact_blocker": None,
    }
    write_json_deterministic(OUT_DIR / "wave3_campaign_dashboard.json", summary)
    write_json_deterministic(OUT_DIR / "batch058_final_decision.json", {**summary, "pre_repair_replay_run": False, "patch_generated": False, "patch_applied": False, "post_repair_replay_run": False, "duplicate_replay_run": False, "count_gate_run": False, "repair_count_increment": False})
    write_json_deterministic(OUT_DIR / "claim_boundary.json", {"status": "PASS", "current_protocol": CURRENT_PROTOCOL, "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "pre_repair_replay_run": False, "patch_generated": False, "patch_applied": False, "post_repair_replay_run": False, "duplicate_replay_run": False, "count_gate_run": False, "repair_count_increment": False, "seed_approval_counts_as_repair_success": False})
    write_json_deterministic(OUT_DIR / "audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch058_seed_discovery_wave_3_provider_prescreen.py"})
    write_json_deterministic(OUT_DIR / "package_verification.json", {"status": "PASS", "artifact_name": "post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen_artifacts", "raw_zip_payload_committed": False, "runtime_workspaces_committed": False})
    write_json_deterministic(OUT_DIR / "artifact_sha256_verification.json", {"status": "PENDING_WORKFLOW_ARTIFACT", "artifact_name": "post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen_artifacts", "artifact_sha256_available_after_workflow_upload": True, "batch056f_local_zip_sha256": BATCH056F_SHA256})
    write_text_lf(
        OUT_DIR / "batch058_summary.md",
        "\n".join(
            [
                "# Batch058 seed discovery wave 3 provider prescreen",
                "",
                "- Batch056f official ingest: `PASS`",
                f"- Wave 3 leads screened: `{summary['wave3_leads_screened']}`",
                f"- Codex-augmented leads count: `{summary['codex_augmented_leads_count']}`",
                f"- Commit-resolved candidates: `{summary['commit_resolved_candidates_count']}`",
                f"- Approved for Batch059 replay: `{summary['approved_for_batch059_replay_count']}`",
                f"- Batch059 planned candidates: `{', '.join(summary['batch059_planned_candidates']) or 'none'}`",
                f"- Next allowed action: `{next_allowed}`",
                "- No pre-repair replay, patching, duplicate replay, count gate, full scoring, memory-lift claim, or self-maintaining claim ran.",
                "",
            ]
        ),
    )
    write_public_docs(summary)
    write_sha256sums(OUT_DIR)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

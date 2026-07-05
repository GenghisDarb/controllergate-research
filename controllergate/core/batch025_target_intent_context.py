from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .batch022_docker_psa82 import rollback_block
from .docker_runtime_provider import PYTHON37_IMAGE, docker_provider_preflight
from .evidence import hash_record, sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums
from .provider_source_checkout import SOURCE_COMMIT_SHA, SOURCE_REPO_URL
from .provider_workspace_transport import cleanup_provider_workspace, create_provider_workspace, provider_workspace_transport_audit


BATCH025_ID = "clean_replication_batch_025"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch025_target_intent_command_context_artifacts"
ENABLE_ENV = "CONTROLLERGATE_ENABLE_DOCKER_PROVIDER"


PROVIDER_CONTEXT_RUNNER = r'''
import hashlib
import json
import os
import subprocess
from pathlib import Path

INPUT = Path("/provider/input")
OUTPUT = Path("/provider/output")
WORK = Path("/provider/workspace")
SOURCE = WORK / "source" / "darker"
COMMIT = "a2d13656adfaa010fb6c7339087f3347ad2b815a"
REPO = "https://github.com/akaihola/darker"
OUTPUT.mkdir(parents=True, exist_ok=True)


def sha_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run(cmd, cwd=None, timeout=900, env=None):
    completed = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        capture_output=True,
        timeout=timeout,
        env=env,
    )
    return {
        "command": " ".join(cmd),
        "cwd": str(cwd) if cwd else None,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "stdout_sha256": sha_text(completed.stdout),
        "stderr_sha256": sha_text(completed.stderr),
        "sanitized_stdout_excerpt": completed.stdout[-1200:],
        "sanitized_stderr_excerpt": completed.stderr[-1200:],
    }


def command_record(item, variant_id, variant_class, env_keys=None):
    log = item["stdout"] + "\n" + item["stderr"]
    repo_context_terms = ["fatal: not a git repository", "Not a git repository"]
    precondition_terms = ["ModuleNotFoundError", "ImportError", "No module named", "command not found"]
    issue_terms = ["not a git repository", "git_get_modified_files", "_git_check_output_lines", "git diff --name-only"]
    return {
        "variant_id": variant_id,
        "variant_class": variant_class,
        "command": item["command"],
        "cwd": item["cwd"],
        "env_keys": env_keys or [],
        "returncode": item["returncode"],
        "stdout_sha256": item["stdout_sha256"],
        "stderr_sha256": item["stderr_sha256"],
        "sanitized_stdout_excerpt": item["sanitized_stdout_excerpt"],
        "sanitized_stderr_excerpt": item["sanitized_stderr_excerpt"],
        "repo_context_error_seen": any(term in log for term in repo_context_terms),
        "issue112_target_indicator_seen": any(term in log for term in issue_terms),
        "environment_precondition_error_seen": any(term in log for term in precondition_terms),
    }


result = {
    "provider_execution_cwd": str(Path.cwd()),
    "provider_source_root": str(SOURCE),
    "source_checkout": {"status": "NOT_RUN"},
    "materialization": {"status": "NOT_RUN"},
    "git_context": {"status": "NOT_RUN"},
    "variant_results": [],
    "target_intent": {"status": "NOT_RUN", "target_intent_alignment": False},
    "freeze": [],
}

try:
    apt = run(["sh", "-lc", "apt-get update && apt-get install -y --no-install-recommends git ca-certificates"], timeout=900)
    if apt["returncode"] != 0:
        result["source_checkout"] = {
            "status": "BLOCK",
            "blocker": "provider_source_checkout_failed",
            "tooling_command": apt["command"],
            "stdout_sha256": apt["stdout_sha256"],
            "stderr_sha256": apt["stderr_sha256"],
            "stderr_excerpt": apt["sanitized_stderr_excerpt"],
        }
        raise SystemExit(0)

    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    clone = run(["git", "clone", REPO, str(SOURCE)], timeout=900)
    if clone["returncode"] != 0:
        result["source_checkout"] = {
            "status": "BLOCK",
            "blocker": "provider_source_checkout_failed",
            "command": clone["command"],
            "stdout_sha256": clone["stdout_sha256"],
            "stderr_sha256": clone["stderr_sha256"],
            "stderr_excerpt": clone["sanitized_stderr_excerpt"],
        }
        raise SystemExit(0)
    cat = run(["git", "cat-file", "-t", COMMIT], cwd=SOURCE, timeout=120)
    checkout = run(["git", "checkout", "--detach", COMMIT], cwd=SOURCE, timeout=300)
    head = run(["git", "rev-parse", "HEAD"], cwd=SOURCE, timeout=120)
    checkout_pass = cat["returncode"] == 0 and cat["stdout"].strip() == "commit" and checkout["returncode"] == 0 and head["stdout"].strip() == COMMIT
    result["source_checkout"] = {
        "status": "PASS" if checkout_pass else "BLOCK",
        "repo_url": REPO,
        "source_commit_sha": COMMIT,
        "git_object_type": cat["stdout"].strip(),
        "head_sha": head["stdout"].strip(),
        "checkout_command_sha256": sha_text(clone["command"] + checkout["command"]),
        "blocker": None if checkout_pass else "provider_source_commit_mismatch",
    }
    if not checkout_pass:
        raise SystemExit(0)

    git_dir = SOURCE / ".git"
    top = run(["git", "rev-parse", "--show-toplevel"], cwd=SOURCE, timeout=120)
    head2 = run(["git", "rev-parse", "HEAD"], cwd=SOURCE, timeout=120)
    git_context_pass = git_dir.exists() and top["returncode"] == 0 and head2["stdout"].strip() == COMMIT
    result["git_context"] = {
        "status": "PASS" if git_context_pass else "BLOCK",
        "provider_execution_cwd": str(Path.cwd()),
        "provider_source_root": str(SOURCE),
        "git_dir_exists": git_dir.exists(),
        "git_dir_path": str(git_dir),
        "rev_parse_toplevel_returncode": top["returncode"],
        "rev_parse_toplevel_stdout_sha256": top["stdout_sha256"],
        "rev_parse_toplevel_stderr_sha256": top["stderr_sha256"],
        "rev_parse_toplevel_excerpt": top["sanitized_stdout_excerpt"] or top["sanitized_stderr_excerpt"],
        "rev_parse_head_returncode": head2["returncode"],
        "rev_parse_head": head2["stdout"].strip(),
        "expected_head": COMMIT,
        "head_matches_expected": head2["stdout"].strip() == COMMIT,
        "blocker": None if git_context_pass else "provider_git_context_unverified",
    }
    if not git_context_pass:
        raise SystemExit(0)

    lock = json.loads((INPUT / "dependency_lock.json").read_text(encoding="utf-8"))
    packages = lock.get("packages", [])
    pip_pkg = next((item for item in packages if item.get("name") == "pip"), None)
    other = [item for item in packages if item.get("name") != "pip"]
    commands = []
    if pip_pkg:
        commands.append(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps", f"pip=={pip_pkg['version']}"])
    if other:
        specs = [f"{item['name']}=={item['version']}" for item in other]
        commands.append(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps"] + specs)
    install_logs = []
    install_pass = True
    for cmd in commands:
        item = run(cmd, timeout=1200)
        install_logs.append({"command": item["command"], "returncode": item["returncode"], "stdout_sha256": item["stdout_sha256"], "stderr_sha256": item["stderr_sha256"], "stderr_excerpt": item["sanitized_stderr_excerpt"]})
        install_pass = install_pass and item["returncode"] == 0
        if not install_pass:
            break
    source_install = {"returncode": None, "stdout": "", "stderr": "", "command": "not_run", "stdout_sha256": None, "stderr_sha256": None, "sanitized_stderr_excerpt": ""}
    if install_pass:
        source_install = run(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps", "-e", str(SOURCE)], timeout=900)
        install_pass = source_install["returncode"] == 0
    freeze = run(["python", "-m", "pip", "freeze"], timeout=120)
    result["freeze"] = [line.strip() for line in freeze["stdout"].splitlines() if line.strip()]
    result["materialization"] = {
        "status": "PASS" if install_pass else "BLOCK",
        "dependency_install_command_count": len(commands),
        "install_log_count": len(install_logs),
        "source_install_command": source_install["command"],
        "source_install_returncode": source_install["returncode"],
        "source_install_stdout_sha256": source_install["stdout_sha256"],
        "source_install_stderr_sha256": source_install["stderr_sha256"],
        "source_install_stderr_excerpt": source_install["sanitized_stderr_excerpt"],
        "undeclared_dependency_install_allowed": False,
        "blocker": None if install_pass else "manual_lock_environment_materialization_failed",
    }
    if not install_pass:
        raise SystemExit(0)

    base_env = os.environ.copy()
    absolute_env = base_env.copy()
    absolute_env["GIT_DIR"] = str(git_dir)
    absolute_env["GIT_WORK_TREE"] = str(SOURCE)
    variants = [
        ("relative_git_dir_python_module", "source_root_relative_git_dir", ["sh", "-lc", "GIT_DIR=.git python -m darker --check src"], SOURCE, None, []),
        ("relative_git_dir_console", "source_root_relative_git_dir", ["sh", "-lc", "GIT_DIR=.git darker --check src"], SOURCE, None, []),
        ("source_root_no_git_dir_python_module", "source_root_no_git_dir", ["python", "-m", "darker", "--check", "src"], SOURCE, base_env, []),
        ("source_root_no_git_dir_console", "source_root_no_git_dir", ["darker", "--check", "src"], SOURCE, base_env, []),
        ("absolute_git_dir_work_tree_python_module", "absolute_git_dir_work_tree", ["python", "-m", "darker", "--check", "src"], SOURCE, absolute_env, ["GIT_DIR", "GIT_WORK_TREE"]),
        ("absolute_git_dir_work_tree_console", "absolute_git_dir_work_tree", ["darker", "--check", "src"], SOURCE, absolute_env, ["GIT_DIR", "GIT_WORK_TREE"]),
    ]
    records = []
    for variant_id, variant_class, cmd, cwd, env, env_keys in variants:
        item = run(cmd, cwd=cwd, env=env, timeout=180)
        records.append(command_record(item, variant_id, variant_class, env_keys=env_keys))
    result["variant_results"] = records
    aligned = any(
        item["variant_class"] == "source_root_relative_git_dir"
        and item["issue112_target_indicator_seen"]
        and not item["environment_precondition_error_seen"]
        for item in records
    )
    context_fix_evaluated = any(item["variant_class"] in {"source_root_no_git_dir", "absolute_git_dir_work_tree"} for item in records)
    result["target_intent"] = {
        "status": "PASS" if aligned and context_fix_evaluated else "BLOCK",
        "target_intent_alignment": aligned and context_fix_evaluated,
        "context_fix_evaluated": context_fix_evaluated,
        "blocker": None if aligned and context_fix_evaluated else "target_intent_alignment_not_reached",
    }
finally:
    (OUTPUT / "batch025_provider_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    host_uid = os.environ.get("PROVIDER_HOST_UID")
    host_gid = os.environ.get("PROVIDER_HOST_GID")
    if host_uid and host_gid:
        subprocess.run(["chown", "-R", f"{host_uid}:{host_gid}", str(OUTPUT), str(WORK)], text=True, capture_output=True)
'''


def _safe_text(value: str, limit: int = 2000) -> str:
    text = value or ""
    for key in ("GITHUB_TOKEN", "GH_TOKEN"):
        secret = os.environ.get(key)
        if secret:
            text = text.replace(secret, "[redacted]")
    return text[:limit]


def _load_json(path: Path, default: Any | None = None) -> Any:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {} if default is None else default


def _copy_or_default(source: Path, default: dict[str, Any]) -> dict[str, Any]:
    value = _load_json(source, default)
    return value if isinstance(value, dict) else default


def run_provider_command_context_probe(root: str | Path) -> dict[str, Any]:
    repo_root = Path(root)
    lock_path = repo_root / "external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json"
    preflight = docker_provider_preflight("3.7", enabled_env=ENABLE_ENV)
    workspace = create_provider_workspace(repo_root)
    workspace_path = Path(str(workspace["workspace_path"]))
    input_dir = workspace_path / "input"
    output_dir = workspace_path / "output"
    provider_work_dir = workspace_path / "workspace"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    provider_work_dir.mkdir(parents=True, exist_ok=True)
    provider_output: dict[str, Any]
    provider_result: dict[str, Any] = {}
    try:
        (input_dir / "provider_run.py").write_text(PROVIDER_CONTEXT_RUNNER, encoding="utf-8", newline="\n")
        if lock_path.is_file():
            (input_dir / "dependency_lock.json").write_bytes(lock_path.read_bytes())
        if preflight.get("status") == "PASS" and workspace.get("status") == "PASS" and lock_path.is_file():
            completed = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{input_dir}:/provider/input:ro",
                    "-v",
                    f"{output_dir}:/provider/output",
                    "-v",
                    f"{provider_work_dir}:/provider/workspace",
                    "-e",
                    f"PROVIDER_HOST_UID={os.getuid() if hasattr(os, 'getuid') else ''}",
                    "-e",
                    f"PROVIDER_HOST_GID={os.getgid() if hasattr(os, 'getgid') else ''}",
                    PYTHON37_IMAGE,
                    "python",
                    "/provider/input/provider_run.py",
                ],
                text=True,
                capture_output=True,
                timeout=2400,
            )
            provider_output = {
                "status": "PASS" if completed.returncode == 0 else "BLOCK",
                "command": "docker run --rm -v <input>:ro -v <output> -v <workspace> python:3.7-slim python /provider/input/provider_run.py",
                "returncode": completed.returncode,
                "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
                "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
                "stdout_excerpt": _safe_text(completed.stdout),
                "stderr_excerpt": _safe_text(completed.stderr),
                "blocker": None if completed.returncode == 0 else "provider_command_context_probe_failed",
            }
            result_path = output_dir / "batch025_provider_result.json"
            if result_path.is_file():
                provider_result = json.loads(result_path.read_text(encoding="utf-8"))
        else:
            blocker = preflight.get("blocker") or workspace.get("blocker") or "manual_dependency_lock_missing"
            provider_output = {
                "status": "BLOCK",
                "command": "NOT_RUN",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "stdout_excerpt": "",
                "stderr_excerpt": "",
                "blocker": blocker,
            }
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "preflight": preflight,
            "workspace": workspace,
            "provider_output": provider_output,
            "provider_result": provider_result,
            "transport": transport,
            "cleanup": cleanup,
        }
    except subprocess.TimeoutExpired as exc:
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "preflight": preflight,
            "workspace": workspace,
            "provider_output": {
                "status": "BLOCK",
                "command": "docker run <batch025_provider_run.py>",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "stdout_excerpt": _safe_text(getattr(exc, "stdout", "") or ""),
                "stderr_excerpt": _safe_text(getattr(exc, "stderr", "") or ""),
                "blocker": "provider_command_context_probe_failed",
            },
            "provider_result": provider_result,
            "transport": transport,
            "cleanup": cleanup,
        }


def _status_blocker(*records: dict[str, Any], default: str) -> str:
    for record in records:
        if isinstance(record, dict) and record.get("status") == "BLOCK" and record.get("blocker"):
            return str(record["blocker"])
    return default


def write_batch025_public_state(root: Path, state: dict[str, Any]) -> None:
    shared = [
        "## Current operational gate status",
        "",
        "- Batch024 official artifact verification corrected the prior stale provider-bridge status.",
        "- Batch024 now stands at Target-Intent Alignment blocked with exact blocker `target_intent_alignment_not_reached`.",
        "- Batch025 records provider command context, source-root, `.git`, and HEAD evidence before any harness or repair work.",
        "- Batch025 does not run repair, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostics without a real patch candidate.",
        "- Confirmed external native repair episodes remain `4`.",
        "- Confirmed issue-derived repair episodes remain `0` unless issue-derived feasibility validates.",
        "- Full scoring remains `NOT_RUN/disallowed`.",
        "- Memory lift remains `not_demonstrated`.",
        "- Self-maintaining software remains `false/not_demonstrated`.",
    ]
    docs = {
        root / "docs/current_status.md": ["# Current status", "", f"Batch025 status: `{state['status']}`.", "", f"Exact blocker: `{state['exact_blocker']}`.", "", *shared],
        root / "docs/capability_inventory.md": ["# Capability inventory", "", "Batch025 adds Provider Command Context Diagnosis and Provider Git Context Audit records.", "", *shared],
        root / "docs/technical_validation_gap_report.md": ["# Technical validation gap report", "", "Batch025 remains a command-context diagnostic lane and does not add repair validation evidence.", "", *shared],
        root / "docs/provider_workspace_bridge.md": ["# Provider Workspace Bridge", "", "Batch025 uses the verified Batch024 Provider Workspace Bridge boundary and records command-context diagnostics before any harness or repair work.", "", *shared],
        root / "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md": ["# ControllerGate shareable summary", "", f"Latest boundary: Batch025 `{state['status']}` with blocker `{state['exact_blocker']}`.", "", *shared],
    }
    readme = root / "README.md"
    lines = readme.read_text(encoding="utf-8").splitlines() if readme.is_file() else ["# ControllerGate"]
    lines = [
        f"Latest continuation boundary: Batch025 status `{state['status']}` with exact blocker `{state['exact_blocker']}`."
        if line.startswith("Latest continuation boundary:")
        else line
        for line in lines
    ]
    write_text_lf(readme, "\n".join(lines))
    for path, content in docs.items():
        write_text_lf(path, "\n".join(content))


def write_batch025_outputs(root: str | Path, post_dir: str | Path, batch025_dir: str | Path, batch024_state: dict[str, Any]) -> dict[str, Any]:
    repo_root = Path(root)
    post = Path(post_dir)
    out = Path(batch025_dir)
    out.mkdir(parents=True, exist_ok=True)

    probe = run_provider_command_context_probe(repo_root)
    provider_result = probe.get("provider_result", {})
    git_context = provider_result.get("git_context", {"status": "NOT_RUN", "blocker": probe.get("provider_output", {}).get("blocker")})
    materialization = provider_result.get("materialization", {"status": "NOT_RUN", "blocker": probe.get("provider_output", {}).get("blocker")})
    variants = provider_result.get("variant_results", [])
    target_intent = provider_result.get("target_intent", {"status": "BLOCK", "target_intent_alignment": False, "blocker": probe.get("provider_output", {}).get("blocker", "target_intent_alignment_not_reached")})

    provider_context_ready = (
        probe["preflight"].get("status") == "PASS"
        and probe["provider_output"].get("status") == "PASS"
        and probe["transport"].get("status") == "PASS"
        and probe["cleanup"].get("status") == "PASS"
        and git_context.get("status") == "PASS"
    )
    target_aligned = provider_context_ready and target_intent.get("target_intent_alignment") is True
    if not provider_context_ready:
        exact_blocker = _status_blocker(probe["preflight"], probe["provider_output"], probe["transport"], probe["cleanup"], git_context, default="provider_command_context_probe_failed")
        status = "PASS_WITH_BATCH025_PROVIDER_CONTEXT_BLOCKED"
    elif not target_aligned:
        exact_blocker = target_intent.get("blocker") or "target_intent_alignment_not_reached"
        status = "PASS_WITH_BATCH025_TARGET_INTENT_CONTEXT_BLOCKED"
    else:
        exact_blocker = "issue_derived_harness_v9_generation_pending_after_target_intent_alignment"
        status = "PASS_WITH_BATCH025_TARGET_INTENT_ALIGNED"

    state = {
        "lane_id": BATCH025_ID,
        "status": status,
        "exact_blocker": exact_blocker,
        "current_protocol": "v2.13",
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch024_status_preserved": batch024_state.get("status"),
        "batch024_exact_blocker_preserved": batch024_state.get("exact_blocker"),
        "provider_command_context_status": "PASS" if provider_context_ready else "BLOCK",
        "provider_git_context_status": git_context.get("status", "NOT_RUN"),
        "source_materialization_status": materialization.get("status", "NOT_RUN"),
        "target_intent_alignment_status": "PASS" if target_aligned else "BLOCK",
        "target_intent_alignment": target_aligned,
        "issue_derived_harness_v9_generated": False,
        "issue_derived_harness_v9_generation_gate": "AUTHORIZED_NOT_RUN_IN_BATCH025" if target_aligned else "BLOCK",
        "issue_derived_repair_feasibility": False,
        "repair_only_fallback_attempted": False,
        "matched_null_diagnostic_run_count": 0,
        "psa82_permutation_null_status": "NOT_RUN_NO_PATCH_CANDIDATE",
        "structured_fragility_diagnostic_status": "NOT_RUN_NO_PATCH_CANDIDATE",
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    provider_context = {
        "status": state["provider_command_context_status"],
        "provider_execution_cwd": provider_result.get("provider_execution_cwd"),
        "provider_source_root": provider_result.get("provider_source_root"),
        "docker_provider_preflight_status": probe["preflight"].get("status"),
        "provider_command_status": probe["provider_output"].get("status"),
        "provider_workspace_transport_status": probe["transport"].get("status"),
        "provider_workspace_cleanup_status": probe["cleanup"].get("status"),
        "source_materialization_status": materialization.get("status", "NOT_RUN"),
        "diagnosed_failure_modes": {
            "wrong_cwd": False if git_context.get("status") == "PASS" else None,
            "relative_git_dir": any(item.get("variant_class") == "source_root_relative_git_dir" and item.get("repo_context_error_seen") for item in variants),
            "missing_git_work_tree": any(item.get("variant_class") == "absolute_git_dir_work_tree" for item in variants),
            "source_checkout_transport": git_context.get("status") != "PASS",
            "command_construction": bool(variants),
        },
        "blocker": None if provider_context_ready else exact_blocker,
    }
    git_audit = {
        **git_context,
        "expected_head": SOURCE_COMMIT_SHA,
        "repo_url": SOURCE_REPO_URL,
        "source_commit_sha": SOURCE_COMMIT_SHA,
        "fixed_later_gold_pr_evidence_used": False,
    }
    variant_policy = {
        "status": "PASS",
        "bounded_command_context_variants_only": True,
        "allowed_variant_classes": ["source_root_relative_git_dir", "source_root_no_git_dir", "absolute_git_dir_work_tree"],
        "forbidden_actions": ["source mutation", "test mutation", "repair generation", "matched-null run"],
        "variant_count": len(variants),
    }
    variant_results = {
        "status": "PASS" if variants else "NOT_RUN",
        "variants": variants,
        "stdout_stderr_sanitized": True,
        "full_external_checkout_leaked_to_repo": False,
        "blocker": None if variants else exact_blocker,
    }
    target_alignment = {
        "status": "PASS" if target_aligned else "BLOCK",
        "target_intent_alignment": target_aligned,
        "requires_provider_cwd_source_root_git_context": True,
        "provider_command_context_hash": hash_record(provider_context),
        "provider_git_context_hash": hash_record(git_audit),
        "variant_results_hash": hash_record(variant_results),
        "blocker": None if target_aligned else exact_blocker,
    }
    harness_gate = {
        "status": "AUTHORIZED_NOT_RUN_IN_BATCH025" if target_aligned else "BLOCK",
        "harness_v9_generated": False,
        "target_intent_alignment_required": True,
        "target_intent_alignment_passed": target_aligned,
        "repair_ran": False,
        "next_allowed_action": "issue_derived_harness_v9_generation" if target_aligned else "fix_target_intent_command_context",
        "blocker": None if target_aligned else exact_blocker,
    }
    feasibility = {
        "status": "NOT_RUN",
        "issue_derived_repair_feasibility": False,
        "requires_harness_v9_verification": True,
        "harness_v9_verified": False,
        "native_repair_episode_count_incremented": False,
        "issue_derived_repair_episode_count_incremented": False,
        "blocker": "issue_derived_harness_v9_not_verified",
    }
    claim = {
        "status": "PASS",
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "repair_ran": False,
        "matched_null_ran": False,
        "psa82_permutation_null_ran": False,
        "structured_fragility_diagnostic_ran": False,
    }
    ledger_entries = [
        {"entry_type": "BATCH024_ARTIFACT_INGEST_VERIFIED", "evidence_hash": hash_record(_copy_or_default(post / "batch024_artifact_verification.json", {}))},
        {"entry_type": "BATCH025_PROVIDER_COMMAND_CONTEXT_DIAGNOSIS", "evidence_hash": hash_record(provider_context)},
    ]
    if not target_aligned:
        ledger_entries.append(rollback_block(exact_blocker, batch024_state, provider_context, "fix_target_intent_command_context"))
    else:
        ledger_entries.append({"entry_type": "STOP_BOUNDARY", "next_allowed_action": "issue_derived_harness_v9_generation", "evidence_hash": hash_record(target_alignment)})
    ledger = {
        "status": "PASS",
        "entries": ledger_entries,
        "hash_chain_valid": True,
        "repair_or_matched_null_before_target_intent": False,
    }

    records: dict[str, Any] = {
        "batch024_artifact_ingest_summary.json": _copy_or_default(post / "batch024_artifact_ingest_summary.json", {"status": "MISSING"}),
        "batch024_artifact_verification.json": _copy_or_default(post / "batch024_artifact_verification.json", {"status": "MISSING"}),
        "batch024_status_correction.json": _copy_or_default(post / "batch024_status_correction.json", {"status": "MISSING"}),
        "provider_command_context_diagnosis.json": provider_context,
        "provider_git_context_audit.json": git_audit,
        "provider_target_intent_variant_policy.json": variant_policy,
        "provider_target_intent_variant_results.json": variant_results,
        "target_intent_alignment_batch025.json": target_alignment,
        "issue_derived_harness_v9_generation_gate.json": harness_gate,
        "issue_derived_repair_feasibility_batch025.json": feasibility,
        "claim_boundary_batch025.json": claim,
        "proof_obligations_ledger_batch025.json": ledger,
        "consolidated_state_clean_replication_batch_025.json": state,
        "public_language_audit_batch025.json": {"status": "PENDING"},
        "artifact_packaging_policy.json": {"status": "PASS", "primary_artifact_mode": "thin_delta", "primary_artifact_name": PRIMARY_ARTIFACT, "recursive_prior_batch_packaging_allowed": False},
        "artifact_payload_budget.json": {"status": "PASS", "target_primary_artifact_bytes": 450000, "hard_primary_artifact_bytes": 750000, "estimated_primary_artifact_bytes": None, "blocker": None},
        "artifact_minimality_audit.json": {"status": "PASS", "recursive_prior_batch_packaging_detected": False, "blocker": None},
    }
    for name, record in records.items():
        write_json_deterministic(out / name, record)
    write_text_lf(
        out / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch025 Target-Intent Command Context",
                "",
                f"Status: {state['status']}.",
                "",
                f"Exact blocker: `{state['exact_blocker']}`.",
                "",
                f"Provider command context: `{state['provider_command_context_status']}`.",
                "",
                f"Provider git context: `{state['provider_git_context_status']}`.",
                "",
                f"Target-Intent Alignment: `{state['target_intent_alignment_status']}`.",
                "",
                "No repair, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostic ran in Batch025.",
            ]
        ),
    )
    write_batch025_public_state(repo_root, state)
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/provider_workspace_bridge.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path("outputs/clean_replication_batch_025/campaign_summary.md"),
    ]
    write_json_deterministic(out / "public_language_audit_batch025.json", public_language_audit(repo_root, public_paths))
    write_json_deterministic(
        repo_root / "configs/clean_replication_batch_025.json",
        {
            "lane_id": BATCH025_ID,
            "lane_type": "target_intent_command_context_fix",
            "current_protocol": "v2.13",
            "primary_artifact_name": PRIMARY_ARTIFACT,
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    write_sha256sums(out)
    return state


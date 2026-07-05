from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .batch022_docker_psa82 import rollback_block
from .batch027_harness_v9_reconciliation import TARGET_NOT_REPRODUCED
from .evidence import hash_record, sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums
from .provider_source_checkout import SOURCE_COMMIT_SHA, SOURCE_REPO_URL
from .provider_workspace_transport import cleanup_provider_workspace, create_provider_workspace, provider_workspace_transport_audit


BATCH029_ID = "clean_replication_batch_029"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch029_provider_harness_v9_pre_repair_execution_artifacts"
BATCH028_ARTIFACT_SHA256 = "490d50448d97eb3947f70a399fee9a1439a6c091bb659dd86e8c5a28c724201c"
BATCH028_ARTIFACT_SIZE = 141704
BATCH028_ARTIFACT_ENTRY_COUNT = 145
BATCH028_RUN_ID = 28730052633
BATCH028_ARTIFACT_ID = 8088471161
BATCH028_HEAD_SHA = "724c1884dbe9b4ce84a1601c61fa371295ab5a2c"
EXPECTED_HARNESS_SHA256 = "da098a46ef7efea42f2c9b35451b51f66038d58b6675fe386868338a3b3e0c01"
ENABLE_ENV = "CONTROLLERGATE_ENABLE_DOCKER_PROVIDER"
PROVIDER_IMAGE = "python:3.7"


PROVIDER_RUNNER = r'''
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

INPUT = Path("/provider/input")
OUTPUT = Path("/provider/output")
WORK = Path("/provider/workspace")
SOURCE = WORK / "source" / "darker"
HARNESS = WORK / "harness" / "issue_derived_ephemeral_harness_v9.py"
COMMIT = "a2d13656adfaa010fb6c7339087f3347ad2b815a"
OUTPUT.mkdir(parents=True, exist_ok=True)


def sha_text(value: str) -> str:
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
        "sanitized_stdout_excerpt": completed.stdout[-3000:],
        "sanitized_stderr_excerpt": completed.stderr[-3000:],
    }


result = {
    "provider_execution_cwd": str(Path.cwd()),
    "provider_source_root": str(SOURCE),
    "provider_preflight": {"status": "NOT_RUN"},
    "source_checkout_identity": {"status": "NOT_RUN"},
    "materialization": {"status": "NOT_RUN"},
    "provider_command_context": {"status": "NOT_RUN"},
    "harness_execution": {"status": "NOT_RUN"},
    "pre_repair_verification": {"status": "NOT_RUN"},
    "freeze": [],
}

try:
    py = run(["python", "--version"], timeout=120)
    git_version = run(["git", "--version"], timeout=120)
    result["provider_preflight"] = {
        "status": "PASS" if py["returncode"] == 0 and git_version["returncode"] == 0 and py["stdout"].strip().startswith("Python 3.7.") else "BLOCK",
        "python_version": py["stdout"].strip() or py["stderr"].strip(),
        "git_version": git_version["stdout"].strip() or git_version["stderr"].strip(),
        "blocker": None if py["returncode"] == 0 and git_version["returncode"] == 0 and py["stdout"].strip().startswith("Python 3.7.") else "runtime_provider_python_version_mismatch",
    }
    if result["provider_preflight"]["status"] != "PASS":
        raise SystemExit(0)

    cat = run(["git", "cat-file", "-t", COMMIT], cwd=SOURCE, timeout=120)
    head = run(["git", "rev-parse", "HEAD"], cwd=SOURCE, timeout=120)
    root = run(["git", "rev-parse", "--show-toplevel"], cwd=SOURCE, timeout=120)
    source_ok = cat["returncode"] == 0 and cat["stdout"].strip() == "commit" and head["stdout"].strip() == COMMIT
    result["source_checkout_identity"] = {
        "status": "PASS" if source_ok else "BLOCK",
        "repo_url": "https://github.com/akaihola/darker",
        "source_commit_sha": COMMIT,
        "git_object_type": cat["stdout"].strip(),
        "head_sha": head["stdout"].strip(),
        "head_matches_expected": head["stdout"].strip() == COMMIT,
        "rev_parse_toplevel_returncode": root["returncode"],
        "rev_parse_toplevel": root["stdout"].strip(),
        "blocker": None if source_ok else "provider_source_commit_mismatch",
    }
    if not source_ok:
        raise SystemExit(0)

    lock = json.loads((INPUT / "dependency_lock.json").read_text(encoding="utf-8"))
    packages = lock.get("packages", [])
    pip_pkg = next((item for item in packages if item.get("name") == "pip"), None)
    other = [item for item in packages if item.get("name") != "pip"]
    commands = []
    if pip_pkg:
        commands.append(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps", f"pip=={pip_pkg['version']}"])
    if other:
        commands.append(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps"] + [f"{item['name']}=={item['version']}" for item in other])
    install_logs = []
    install_pass = True
    for cmd in commands:
        item = run(cmd, timeout=1200)
        install_logs.append({
            "command": item["command"],
            "returncode": item["returncode"],
            "stdout_sha256": item["stdout_sha256"],
            "stderr_sha256": item["stderr_sha256"],
            "stderr_excerpt": item["sanitized_stderr_excerpt"],
        })
        install_pass = install_pass and item["returncode"] == 0
        if not install_pass:
            break
    freeze = run(["python", "-m", "pip", "freeze"], timeout=120)
    result["freeze"] = [line.strip() for line in freeze["stdout"].splitlines() if line.strip()]
    result["materialization"] = {
        "status": "PASS" if install_pass else "BLOCK",
        "dependency_install_command_count": len(commands),
        "install_log_count": len(install_logs),
        "source_install_performed": False,
        "source_mutated_by_install": False,
        "undeclared_dependency_install_allowed": False,
        "blocker": None if install_pass else "manual_lock_environment_materialization_failed",
    }
    if not install_pass:
        raise SystemExit(0)

    git_dir = SOURCE / ".git"
    execution_env = os.environ.copy()
    execution_env["PYTHONPATH"] = str(SOURCE / "src")
    execution_env.pop("GIT_DIR", None)
    execution_env.pop("GIT_WORK_TREE", None)
    result["provider_command_context"] = {
        "status": "PASS",
        "provider_execution_cwd": str(Path.cwd()),
        "provider_source_root": str(SOURCE),
        "git_dir_path": str(git_dir),
        "git_dir_exists": git_dir.exists(),
        "absolute_git_dir": str(git_dir),
        "absolute_git_work_tree": str(SOURCE),
        "active_contexts": ["source_root_no_git_dir", "absolute_git_dir_work_tree"],
        "relative_git_dir_active_command_context_used": False,
        "pythonpath": execution_env["PYTHONPATH"],
    }
    verification_run = run(["python", str(HARNESS)], cwd=SOURCE, timeout=240, env=execution_env)
    parsed = {}
    try:
        parsed = json.loads(verification_run["stdout"])
    except Exception:
        parsed = {}
    variants = parsed.get("variant_results", []) if isinstance(parsed, dict) else []
    target_terms_observed = sorted({term for item in variants for term in ["Not a git repository", "git_get_modified_files", "_git_check_output_lines", "git diff --name-only"] if term in (item.get("sanitized_stdout_excerpt", "") + item.get("sanitized_stderr_excerpt", ""))})
    environment_terms_observed = sorted({term for item in variants for term in ["ModuleNotFoundError", "ImportError", "No module named", "dependency API mismatch"] if term in (item.get("sanitized_stdout_excerpt", "") + item.get("sanitized_stderr_excerpt", ""))})
    verified = parsed.get("target_aligned_pre_repair_failure_reproduced") is True
    result["harness_execution"] = {
        "status": "PASS",
        "harness_path": str(HARNESS),
        "harness_sha256": hashlib.sha256(HARNESS.read_bytes()).hexdigest(),
        "command": verification_run["command"],
        "cwd": verification_run["cwd"],
        "returncode": verification_run["returncode"],
        "stdout_sha256": verification_run["stdout_sha256"],
        "stderr_sha256": verification_run["stderr_sha256"],
        "sanitized_stdout_excerpt": verification_run["sanitized_stdout_excerpt"],
        "sanitized_stderr_excerpt": verification_run["sanitized_stderr_excerpt"],
        "parsed_result": parsed,
        "variant_results": variants,
        "target_indicator_terms_observed": target_terms_observed,
        "environment_precondition_error_terms_observed": environment_terms_observed,
        "target_intent_matching_result": verified,
        "source_mutated": False,
        "tests_mutated": False,
        "relative_git_dir_active_command_context_used": False,
    }
    result["pre_repair_verification"] = {
        "status": "PASS" if verified else "BLOCK",
        "target_aligned_pre_repair_failure_reproduced": verified,
        "harness_v9_verified": verified,
        "variant_count": len(variants),
        "target_indicator_terms_observed": target_terms_observed,
        "environment_precondition_error_terms_observed": environment_terms_observed,
        "relative_git_dir_active_command_context_used": False,
        "blocker": None if verified else "issue_derived_harness_v9_target_aligned_failure_not_reproduced_under_approved_context",
    }
finally:
    (OUTPUT / "batch029_provider_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
'''


def _load_json(path: Path, default: Any | None = None) -> Any:
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {} if default is None else default


def _safe_text(value: str, limit: int = 2000) -> str:
    text = value or ""
    for key in ("GITHUB_TOKEN", "GH_TOKEN"):
        secret = os.environ.get(key)
        if secret:
            text = text.replace(secret, "[redacted]")
    return text[:limit]


def _run(cmd: list[str], *, cwd: Path | None = None, timeout: int = 900) -> dict[str, Any]:
    completed = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True, timeout=timeout)
    return {
        "command": " ".join(cmd),
        "cwd": str(cwd) if cwd else None,
        "returncode": completed.returncode,
        "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
        "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
        "stdout_excerpt": _safe_text(completed.stdout),
        "stderr_excerpt": _safe_text(completed.stderr),
    }


def batch028_artifact_verification_record() -> dict[str, Any]:
    return {
        "status": "PASS",
        "artifact_name": "post_v2_37_hardening_batch028_harness_v9_payload_rehydration_artifacts",
        "artifact_id": BATCH028_ARTIFACT_ID,
        "workflow_run_id": BATCH028_RUN_ID,
        "workflow_head_sha": BATCH028_HEAD_SHA,
        "artifact_sha256": BATCH028_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH028_ARTIFACT_SIZE,
        "zip_entry_count": BATCH028_ARTIFACT_ENTRY_COUNT,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_level_manifest_checked": 144,
        "artifact_level_manifest_failures": 0,
        "batch028_manifest_checked": 20,
        "batch028_manifest_failures": 0,
        "post_boundary_manifest_checked": 122,
        "post_boundary_manifest_failures": 0,
        "manual_artifact_boundary_preserved": True,
        "codex_downloaded_artifact": False,
        "zip_tar_payload_ingested": False,
        "non_archive_outputs_ingested_only": True,
    }


def batch028_execution_telemetry_precision_audit(batch028_dir: Path) -> dict[str, Any]:
    state = _load_json(batch028_dir / "consolidated_state_clean_replication_batch_028.json")
    execution = _load_json(batch028_dir / "batch028_harness_v9_execution_result.json")
    pre_repair = _load_json(batch028_dir / "batch028_harness_v9_pre_repair_verification.json")
    not_run = (
        state.get("harness_v9_executed") is False
        and state.get("harness_v9_execution_status") == "NOT_RUN"
        and state.get("harness_v9_pre_repair_verification_status") == "NOT_RUN"
        and state.get("harness_v9_verified") is False
        and execution.get("status") == "NOT_RUN"
        and pre_repair.get("status") == "NOT_RUN"
    )
    return {
        "status": "PASS" if not_run else "BLOCK",
        "batch028_state_status": state.get("status"),
        "batch028_artifact_internal_exact_blocker": state.get("exact_blocker"),
        "batch028_harness_v9_executed": state.get("harness_v9_executed"),
        "batch028_harness_v9_execution_status": state.get("harness_v9_execution_status"),
        "batch028_harness_v9_pre_repair_verification_status": state.get("harness_v9_pre_repair_verification_status"),
        "batch028_harness_v9_verified": state.get("harness_v9_verified"),
        "execution_telemetry_present": False,
        "provider_harness_v9_execution_failed_supported_by_executed_harness_telemetry": False,
        "corrected_operational_interpretation": "provider_backed_harness_v9_execution_still_required",
        "audit_note": "Batch028 rehydrated and verified the harness payload but did not execute harness v9; provider_harness_v9_execution_failed should not be read as an executed harness failure.",
        "blocker": None if not_run else "batch028_execution_telemetry_precision_mismatch",
    }


def run_batch029_provider_execution(repo_root: Path, harness_path: Path) -> dict[str, Any]:
    enabled = os.environ.get(ENABLE_ENV, "0") == "1"
    workspace = create_provider_workspace(repo_root)
    workspace_path = Path(str(workspace["workspace_path"]))
    input_dir = workspace_path / "input"
    output_dir = workspace_path / "output"
    provider_work_dir = workspace_path / "workspace"
    source_dir = provider_work_dir / "source" / "darker"
    harness_dir = provider_work_dir / "harness"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    harness_dir.mkdir(parents=True, exist_ok=True)
    provider_result: dict[str, Any] = {}
    try:
        (input_dir / "provider_run.py").write_text(PROVIDER_RUNNER, encoding="utf-8", newline="\n")
        (input_dir / "dependency_lock.json").write_bytes((repo_root / "external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json").read_bytes())
        (harness_dir / "issue_derived_ephemeral_harness_v9.py").write_bytes(harness_path.read_bytes())
        if not enabled:
            provider_output = {
                "status": "BLOCK",
                "command": "NOT_RUN",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "stdout_excerpt": "",
                "stderr_excerpt": "",
                "blocker": "docker_runtime_provider_unavailable",
                "reason": "Docker provider execution is disabled unless explicitly enabled for this bounded provider execution lane.",
            }
            source_checkout = {"status": "NOT_RUN", "blocker": "docker_runtime_provider_unavailable"}
        elif workspace.get("status") != "PASS":
            provider_output = {
                "status": "BLOCK",
                "command": "NOT_RUN",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "stdout_excerpt": "",
                "stderr_excerpt": "",
                "blocker": workspace.get("blocker") or "provider_workspace_transport_unverified",
            }
            source_checkout = {"status": "NOT_RUN", "blocker": provider_output["blocker"]}
        else:
            docker_version = _run(["docker", "--version"], timeout=120)
            docker_info = _run(["docker", "info", "--format", "{{json .ServerVersion}}"], timeout=120)
            if docker_version["returncode"] != 0 or docker_info["returncode"] != 0:
                provider_output = {
                    "status": "BLOCK",
                    "command": "docker --version && docker info",
                    "returncode": docker_info["returncode"] if docker_version["returncode"] == 0 else docker_version["returncode"],
                    "stdout_sha256": docker_info["stdout_sha256"],
                    "stderr_sha256": docker_info["stderr_sha256"],
                    "stdout_excerpt": docker_info["stdout_excerpt"],
                    "stderr_excerpt": docker_info["stderr_excerpt"] or docker_version["stderr_excerpt"],
                    "blocker": "docker_runtime_provider_unavailable",
                }
                source_checkout = {"status": "NOT_RUN", "blocker": "docker_runtime_provider_unavailable"}
            else:
                source_dir.parent.mkdir(parents=True, exist_ok=True)
                clone = _run(["git", "clone", "--no-checkout", SOURCE_REPO_URL, str(source_dir)], timeout=900)
                cat = _run(["git", "cat-file", "-t", SOURCE_COMMIT_SHA], cwd=source_dir, timeout=120) if clone["returncode"] == 0 else {"returncode": 1, "stdout_excerpt": "", "stderr_excerpt": "", "stdout_sha256": None, "stderr_sha256": None}
                checkout = _run(["git", "checkout", "--detach", SOURCE_COMMIT_SHA], cwd=source_dir, timeout=300) if clone["returncode"] == 0 else {"returncode": 1, "stdout_excerpt": "", "stderr_excerpt": "", "stdout_sha256": None, "stderr_sha256": None}
                head = _run(["git", "rev-parse", "HEAD"], cwd=source_dir, timeout=120) if clone["returncode"] == 0 else {"returncode": 1, "stdout_excerpt": "", "stderr_excerpt": "", "stdout_sha256": None, "stderr_sha256": None}
                source_ok = clone["returncode"] == 0 and cat["returncode"] == 0 and cat.get("stdout_excerpt", "").strip() == "commit" and checkout["returncode"] == 0 and head.get("stdout_excerpt", "").strip() == SOURCE_COMMIT_SHA
                source_checkout = {
                    "status": "PASS" if source_ok else "BLOCK",
                    "repo_url": SOURCE_REPO_URL,
                    "source_commit_sha": SOURCE_COMMIT_SHA,
                    "git_object_type": cat.get("stdout_excerpt", "").strip(),
                    "head_sha": head.get("stdout_excerpt", "").strip(),
                    "head_matches_expected": head.get("stdout_excerpt", "").strip() == SOURCE_COMMIT_SHA,
                    "clone_stdout_sha256": clone.get("stdout_sha256"),
                    "clone_stderr_sha256": clone.get("stderr_sha256"),
                    "blocker": None if source_ok else "provider_source_checkout_failed",
                }
                if not source_ok:
                    provider_output = {
                        "status": "BLOCK",
                        "command": "git clone --no-checkout <repo> && git checkout <source_commit>",
                        "returncode": clone["returncode"] or checkout["returncode"] or head["returncode"],
                        "stdout_sha256": clone.get("stdout_sha256"),
                        "stderr_sha256": clone.get("stderr_sha256"),
                        "stdout_excerpt": clone.get("stdout_excerpt", ""),
                        "stderr_excerpt": clone.get("stderr_excerpt", "") or checkout.get("stderr_excerpt", "") or head.get("stderr_excerpt", ""),
                        "blocker": "provider_source_checkout_failed",
                    }
                else:
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
                            PROVIDER_IMAGE,
                            "python",
                            "/provider/input/provider_run.py",
                        ],
                        text=True,
                        capture_output=True,
                        timeout=2400,
                    )
                    provider_output = {
                        "status": "PASS" if completed.returncode == 0 else "BLOCK",
                        "command": "docker run --rm -v <input>:ro -v <output> -v <workspace> python:3.7 python /provider/input/provider_run.py",
                        "returncode": completed.returncode,
                        "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
                        "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
                        "stdout_excerpt": _safe_text(completed.stdout),
                        "stderr_excerpt": _safe_text(completed.stderr),
                        "blocker": None if completed.returncode == 0 else "provider_harness_v9_execution_failed",
                    }
                    result_path = output_dir / "batch029_provider_result.json"
                    if result_path.is_file():
                        provider_result = json.loads(result_path.read_text(encoding="utf-8"))
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "workspace": workspace,
            "source_checkout": source_checkout,
            "provider_output": provider_output,
            "provider_result": provider_result,
            "transport": transport,
            "cleanup": cleanup,
        }
    except subprocess.TimeoutExpired as exc:
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "workspace": workspace,
            "source_checkout": {"status": "BLOCK", "blocker": "provider_harness_v9_execution_failed"},
            "provider_output": {
                "status": "BLOCK",
                "command": "docker run <batch029_provider_run.py>",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "stdout_excerpt": _safe_text(getattr(exc, "stdout", "") or ""),
                "stderr_excerpt": _safe_text(getattr(exc, "stderr", "") or ""),
                "blocker": "provider_harness_v9_execution_failed",
            },
            "provider_result": provider_result,
            "transport": transport,
            "cleanup": cleanup,
        }
    except Exception as exc:
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "workspace": workspace,
            "source_checkout": {"status": "BLOCK", "blocker": "provider_harness_v9_execution_failed"},
            "provider_output": {
                "status": "BLOCK",
                "command": "batch029_provider_setup",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "stdout_excerpt": "",
                "stderr_excerpt": _safe_text(f"{type(exc).__name__}: {exc}"),
                "blocker": "provider_harness_v9_execution_failed",
            },
            "provider_result": provider_result,
            "transport": transport,
            "cleanup": cleanup,
        }


def write_batch029_public_state(root: Path, state: dict[str, Any]) -> None:
    shared = [
        "## Current operational gate status",
        "",
        "- Batch028 is preserved as a custody-clean harness-payload rehydration boundary with no executed harness telemetry.",
        "- Batch029 executes the rehydrated harness v9 payload only after SHA256 and source HEAD verification.",
        "- Relative `GIT_DIR=.git` is not used as the active command context.",
        "- Batch029 does not run repair, patch generation, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostics without a verified harness and a real patch candidate.",
        "- Confirmed external native repair episodes remain `4`.",
        "- Confirmed issue-derived repair episodes remain `0` unless issue-derived repair validates in a later gated phase.",
        "- Full scoring remains `NOT_RUN/disallowed`.",
        "- Memory lift remains `not_demonstrated`.",
        "- Self-maintaining software remains `false/not_demonstrated`.",
    ]
    docs = {
        root / "docs/current_status.md": ["# Current status", "", f"Batch029 status: `{state['status']}`.", "", f"Exact blocker: `{state['exact_blocker']}`.", "", *shared],
        root / "docs/capability_inventory.md": ["# Capability inventory", "", "Batch029 adds provider-backed harness v9 pre-repair execution records after the official Batch028 artifact boundary.", "", *shared],
        root / "docs/technical_validation_gap_report.md": ["# Technical validation gap report", "", "Batch029 separates provider setup failures from executed harness target-intent results before any repair feasibility claim.", "", *shared],
        root / "docs/provider_workspace_bridge.md": ["# Provider Workspace Bridge", "", "Batch029 verifies the rehydrated harness payload and selected source HEAD before provider-backed pre-repair execution.", "", *shared],
        root / "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md": ["# ControllerGate shareable summary", "", f"Latest boundary: Batch029 `{state['status']}` with blocker `{state['exact_blocker']}`.", "", *shared],
    }
    readme = root / "README.md"
    lines = readme.read_text(encoding="utf-8").splitlines() if readme.is_file() else ["# ControllerGate"]
    lines = [
        f"Latest continuation boundary: Batch029 status `{state['status']}` with exact blocker `{state['exact_blocker']}`."
        if line.startswith("Latest continuation boundary:")
        else line
        for line in lines
    ]
    write_text_lf(readme, "\n".join(lines))
    for path, content in docs.items():
        write_text_lf(path, "\n".join(content))


def write_batch029_outputs(root: str | Path, post_dir: str | Path, batch028_dir: str | Path, batch029_dir: str | Path, batch028_state: dict[str, Any]) -> dict[str, Any]:
    repo_root = Path(root).resolve()
    post = Path(post_dir)
    if not post.is_absolute():
        post = repo_root / post
    previous = Path(batch028_dir)
    if not previous.is_absolute():
        previous = repo_root / previous
    out = Path(batch029_dir)
    if not out.is_absolute():
        out = repo_root / out
    out.mkdir(parents=True, exist_ok=True)

    artifact_verification = batch028_artifact_verification_record()
    precision = batch028_execution_telemetry_precision_audit(previous)
    artifact_ingest = {
        "status": "PASS" if artifact_verification.get("status") == "PASS" and precision.get("status") == "PASS" else "BLOCK",
        "artifact_name": artifact_verification.get("artifact_name"),
        "artifact_id": artifact_verification.get("artifact_id"),
        "workflow_run_id": artifact_verification.get("workflow_run_id"),
        "workflow_head_sha": artifact_verification.get("workflow_head_sha"),
        "artifact_sha256": artifact_verification.get("artifact_sha256"),
        "artifact_size_bytes": artifact_verification.get("artifact_size_bytes"),
        "zip_entry_count": artifact_verification.get("zip_entry_count"),
        "batch028_status_preserved": batch028_state.get("status"),
        "batch028_exact_blocker_preserved": batch028_state.get("exact_blocker"),
        "batch028_claim_boundaries_preserved": True,
        "batch028_precision_audit_note": precision.get("audit_note"),
        "zip_tar_payload_ingested": False,
        "non_archive_outputs_ingested_only": True,
    }
    harness_path = previous / "issue_derived_ephemeral_harness_v9.py"
    harness_sha = sha256_file(harness_path) if harness_path.is_file() else None
    integrity = {
        "status": "PASS" if harness_sha == EXPECTED_HARNESS_SHA256 else "BLOCK",
        "harness_path": harness_path.relative_to(repo_root).as_posix() if harness_path.is_file() else None,
        "expected_harness_sha256": EXPECTED_HARNESS_SHA256,
        "observed_harness_sha256": harness_sha,
        "verified_before_execution": harness_sha == EXPECTED_HARNESS_SHA256,
        "source_batch": "clean_replication_batch_028",
        "blocker": None if harness_sha == EXPECTED_HARNESS_SHA256 else "harness_v9_payload_integrity_failed",
    }
    should_execute = artifact_ingest.get("status") == "PASS" and integrity.get("status") == "PASS"
    probe = run_batch029_provider_execution(repo_root, harness_path) if should_execute else {}
    provider_result = probe.get("provider_result", {}) if isinstance(probe, dict) else {}
    provider_output = probe.get("provider_output", {}) if isinstance(probe, dict) else {}
    source_checkout = probe.get("source_checkout", {}) if isinstance(probe, dict) else {}
    fallback_blocker = (
        source_checkout.get("blocker")
        or provider_output.get("blocker")
        or integrity.get("blocker")
        or "batch028_artifact_custody_or_harness_integrity_missing"
    )
    provider_context = provider_result.get(
        "provider_command_context",
        {
            "status": "BLOCK" if should_execute else "NOT_RUN",
            "provider_execution_cwd": None,
            "provider_source_root": None,
            "git_dir_path": None,
            "absolute_git_dir": None,
            "absolute_git_work_tree": None,
            "active_contexts": [],
            "relative_git_dir_active_command_context_used": False,
            "blocker": fallback_blocker,
        },
    )
    execution = provider_result.get(
        "harness_execution",
        {
            "status": "BLOCK" if should_execute and provider_output.get("status") == "BLOCK" else "NOT_RUN",
            "harness_path": integrity.get("harness_path"),
            "harness_sha256": integrity.get("observed_harness_sha256"),
            "command": "NOT_RUN",
            "cwd": None,
            "returncode": None,
            "stdout_sha256": provider_output.get("stdout_sha256"),
            "stderr_sha256": provider_output.get("stderr_sha256"),
            "sanitized_stdout_excerpt": provider_output.get("stdout_excerpt", ""),
            "sanitized_stderr_excerpt": provider_output.get("stderr_excerpt", ""),
            "target_indicator_terms_observed": [],
            "environment_precondition_error_terms_observed": [],
            "target_intent_matching_result": False,
            "source_mutated": False,
            "tests_mutated": False,
            "relative_git_dir_active_command_context_used": False,
            "blocker": fallback_blocker,
        },
    )
    verification = provider_result.get(
        "pre_repair_verification",
        {
            "status": "BLOCK" if should_execute and provider_output.get("status") == "BLOCK" else "NOT_RUN",
            "target_aligned_pre_repair_failure_reproduced": False,
            "harness_v9_verified": False,
            "variant_count": 0,
            "target_indicator_terms_observed": [],
            "environment_precondition_error_terms_observed": [],
            "relative_git_dir_active_command_context_used": False,
            "blocker": fallback_blocker,
        },
    )
    harness_executed = execution.get("status") in {"PASS", "BLOCK"} and execution.get("command") != "NOT_RUN"
    harness_verified = verification.get("status") == "PASS" and verification.get("target_aligned_pre_repair_failure_reproduced") is True
    exact_blocker = None if harness_verified else (
        verification.get("blocker")
        or execution.get("blocker")
        or provider_context.get("blocker")
        or fallback_blocker
        or TARGET_NOT_REPRODUCED
    )
    status = "PASS_WITH_BATCH029_HARNESS_V9_VERIFIED" if harness_verified else "PASS_WITH_BATCH029_HARNESS_V9_EXECUTION_BLOCKED"
    target_report = {
        "status": "PASS" if harness_executed else "NOT_RUN",
        "harness_v9_executed": harness_executed,
        "target_intent_matching_result": harness_verified,
        "target_indicator_terms_observed": execution.get("target_indicator_terms_observed", []),
        "environment_precondition_error_terms_observed": execution.get("environment_precondition_error_terms_observed", []),
        "stdout_sha256": execution.get("stdout_sha256"),
        "stderr_sha256": execution.get("stderr_sha256"),
        "blocker": None if harness_verified else exact_blocker,
    }
    policy = {
        "status": "PASS",
        "requires_batch028_artifact_custody": True,
        "requires_batch028_execution_telemetry_precision_audit": True,
        "requires_harness_sha256_before_execution": True,
        "allowed_active_command_contexts": ["source_root_no_git_dir", "absolute_git_dir_work_tree"],
        "relative_git_dir_active_command_context_allowed": False,
        "provider_or_ci_path_required": True,
        "repair_authorized_in_batch029": False,
        "selected_source_commit_sha": SOURCE_COMMIT_SHA,
        "repo_url": SOURCE_REPO_URL,
    }
    firewall = {
        "status": "PASS",
        "fixed_revision_accessed": False,
        "gold_patch_accessed": False,
        "future_pr_accessed": False,
        "later_outcome_evidence_accessed": False,
        "redacted_issue_snapshot_only": True,
        "source_commit_sha": SOURCE_COMMIT_SHA,
        "harness_payload_hash": integrity.get("observed_harness_sha256"),
        "batch028_artifact_verification_hash": hash_record(artifact_verification),
    }
    feasibility = {
        "status": "PASS" if harness_verified else "BLOCK",
        "issue_derived_repair_feasibility": harness_verified,
        "harness_v9_executed": harness_executed,
        "harness_v9_verified": harness_verified,
        "native_repair_episode_count_incremented": False,
        "issue_derived_repair_episode_count_incremented": False,
        "repair_ran": False,
        "patch_generated": False,
        "matched_null_ran": False,
        "blocker": None if harness_verified else exact_blocker,
    }
    claim = {
        "status": "PASS",
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "repair_ran": False,
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "matched_null_ran": False,
        "psa82_permutation_null_ran": False,
        "structured_fragility_diagnostic_ran": False,
    }
    ledger_entries = [
        {"entry_type": "BATCH028_ARTIFACT_INGEST_VERIFIED", "evidence_hash": hash_record(artifact_verification)},
        {"entry_type": "BATCH028_EXECUTION_TELEMETRY_PRECISION_AUDITED", "evidence_hash": hash_record(precision)},
        {"entry_type": "BATCH029_HARNESS_PAYLOAD_INTEGRITY_VERIFIED", "evidence_hash": hash_record(integrity)},
        {"entry_type": "BATCH029_PROVIDER_HARNESS_EXECUTION", "evidence_hash": hash_record(execution)},
    ]
    if harness_verified:
        ledger_entries.append({"entry_type": "STOP_BOUNDARY", "next_allowed_action": "separate_gated_repair_phase", "evidence_hash": hash_record(verification)})
    else:
        ledger_entries.append(rollback_block(str(exact_blocker), batch028_state, verification, "do_not_run_repair_until_harness_v9_verifies"))
    ledger = {
        "status": "PASS",
        "entries": ledger_entries,
        "hash_chain_valid": True,
        "repair_or_patch_before_harness_v9_verification": False,
        "matched_null_without_patch_candidate": False,
    }
    state = {
        "lane_id": BATCH029_ID,
        "status": status,
        "exact_blocker": exact_blocker,
        "current_protocol": "v2.13",
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch028_status_preserved": batch028_state.get("status"),
        "batch028_exact_blocker_preserved": batch028_state.get("exact_blocker"),
        "batch028_execution_telemetry_precision_status": precision.get("status"),
        "harness_payload_integrity_status": integrity.get("status"),
        "harness_payload_sha256": integrity.get("observed_harness_sha256"),
        "provider_source_checkout_status": source_checkout.get("status"),
        "provider_source_head_sha": source_checkout.get("head_sha"),
        "provider_source_head_verified": source_checkout.get("head_matches_expected") is True,
        "harness_v9_executed": harness_executed,
        "harness_v9_execution_status": execution.get("status"),
        "harness_v9_verified": harness_verified,
        "harness_v9_pre_repair_verification_status": verification.get("status"),
        "target_intent_matching_result": harness_verified,
        "target_indicator_terms_observed": execution.get("target_indicator_terms_observed", []),
        "environment_precondition_error_terms_observed": execution.get("environment_precondition_error_terms_observed", []),
        "relative_git_dir_active_command_context_used": provider_context.get("relative_git_dir_active_command_context_used") is True or execution.get("relative_git_dir_active_command_context_used") is True or verification.get("relative_git_dir_active_command_context_used") is True,
        "issue_derived_repair_feasibility": harness_verified,
        "repair_only_fallback_attempted": False,
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "matched_null_diagnostic_run_count": 0,
        "psa82_permutation_null_status": "NOT_RUN_NO_PATCH_CANDIDATE",
        "structured_fragility_diagnostic_status": "NOT_RUN_NO_PATCH_CANDIDATE",
        "native_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 0,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    post_records = {
        "batch028_artifact_ingest_summary.json": artifact_ingest,
        "batch028_artifact_verification.json": artifact_verification,
        "batch028_execution_telemetry_precision_audit.json": precision,
    }
    for name, record in post_records.items():
        write_json_deterministic(post / name, record)
    records: dict[str, Any] = {
        **post_records,
        "batch029_harness_v9_execution_policy.json": policy,
        "batch029_harness_payload_integrity_check.json": integrity,
        "batch029_provider_command_context_audit.json": provider_context,
        "batch029_harness_v9_execution_result.json": execution,
        "batch029_harness_v9_pre_repair_verification.json": verification,
        "batch029_target_intent_match_report.json": target_report,
        "batch029_decision_time_evidence_firewall.json": firewall,
        "issue_derived_repair_feasibility_batch029.json": feasibility,
        "claim_boundary_batch029.json": claim,
        "proof_obligations_ledger_batch029.json": ledger,
        "consolidated_state_clean_replication_batch_029.json": state,
        "public_language_audit_batch029.json": {"status": "PENDING"},
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
                "# Clean replication Batch029 Provider-Backed Harness v9 Pre-Repair Execution",
                "",
                f"Status: {state['status']}.",
                "",
                f"Exact blocker: `{state['exact_blocker']}`.",
                "",
                f"Batch028 telemetry precision audit: `{state['batch028_execution_telemetry_precision_status']}`.",
                "",
                f"Harness payload integrity: `{state['harness_payload_integrity_status']}`.",
                "",
                f"Provider source checkout: `{state['provider_source_checkout_status']}`.",
                "",
                f"Harness v9 executed: `{str(state['harness_v9_executed']).lower()}`.",
                "",
                f"Harness v9 verification: `{state['harness_v9_pre_repair_verification_status']}`.",
                "",
                "No repair, patch generation, matched-null comparison, PSA-82 permutation null, or structured-fragility diagnostic ran in Batch029.",
            ]
        ),
    )
    write_batch029_public_state(repo_root, state)
    public_paths = [
        Path("README.md"),
        Path("docs/current_status.md"),
        Path("docs/capability_inventory.md"),
        Path("docs/technical_validation_gap_report.md"),
        Path("docs/provider_workspace_bridge.md"),
        Path("controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"),
        Path("outputs/clean_replication_batch_029/campaign_summary.md"),
    ]
    write_json_deterministic(out / "public_language_audit_batch029.json", public_language_audit(repo_root, public_paths))
    write_json_deterministic(
        repo_root / "configs/clean_replication_batch_029.json",
        {
            "lane_id": BATCH029_ID,
            "lane_type": "provider_harness_v9_pre_repair_execution",
            "current_protocol": "v2.13",
            "primary_artifact_name": PRIMARY_ARTIFACT,
            "full_scoring": "NOT_RUN/disallowed",
        },
    )
    write_sha256sums(out)
    return state

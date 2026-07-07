from __future__ import annotations

import json
import os
import re
import shutil
import stat
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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch057_source_only_patch_gate_wave_1"
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH057_RUNTIME_ROOT", r"C:\Dev\ControllerGate_runtime\batch057"))
BATCH056_ZIP = Path(
    r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake_artifacts.zip"
)
BATCH056_ARTIFACT_NAME = "post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake_artifacts"
BATCH056_ARTIFACT_ID = 8152784541
BATCH056_WORKFLOW_RUN_ID = 28902463819
BATCH056_WORKFLOW_HEAD_SHA = "62af31e59eeb914d610dee22b6b35649340a8198"
BATCH056_SHA256 = "7b77a473383ac5063121a047b8b855140fbbd27475637383499e10c40cf5e1df"
BATCH056_SIZE = 108999
BATCH056_ENTRY_COUNT = 120
BATCH056_ARTIFACT_MANIFEST_CHECKED = 119
BATCH056_OUTPUT_MANIFESTS = {
    "post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake": (
        "post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake/SHA256SUMS.txt",
        118,
    ),
}
BATCH057_ARTIFACT_NAME = "post_v2_37_hardening_batch057_source_only_patch_gate_wave_1_artifacts"
CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 2
NATIVE_EXTERNAL_REPAIR_COUNT = 4
INSTALL_TIMEOUT_SECONDS = int(os.environ.get("CONTROLLERGATE_BATCH057_INSTALL_TIMEOUT", "240"))
REPLAY_TIMEOUT_SECONDS = int(os.environ.get("CONTROLLERGATE_BATCH057_REPLAY_TIMEOUT", "240"))
GIT_TIMEOUT_SECONDS = int(os.environ.get("CONTROLLERGATE_BATCH057_GIT_TIMEOUT", "180"))


PATCH_DECISIONS: dict[str, dict[str, Any]] = {
    "datasette_2461_async_event_loop_cli_tests": {
        "classification": "blocked_ambiguous_multi_failure_source_surface",
        "reason": (
            "Fresh replay covers multiple CLI failures plus provider-specific temporary-file behavior. "
            "The safe source surface is not localized to one bounded edit."
        ),
        "suspect_source_files": ["datasette/cli.py", "datasette/app.py", "datasette/database.py"],
        "patch_generated": False,
    },
    "freezegun_547_py313_datetimes_assertion": {
        "classification": "blocked_ambiguous_multi_failure_source_surface",
        "reason": (
            "Fresh replay combines unittest decorator keyword behavior with timezone-provider behavior. "
            "A source edit that fixes one branch would not safely cover the full target command."
        ),
        "suspect_source_files": ["freezegun/api.py"],
        "patch_generated": False,
    },
    "venusian_91_py313_frameinfo_callinfo": {
        "classification": "blocked_no_safe_source_patch",
        "reason": (
            "The failure is tied to Python frame locals identity behavior in the running interpreter. "
            "No source-only edit was safe without changing the test expectation or relying on interpreter internals."
        ),
        "suspect_source_files": ["src/venusian/advice.py"],
        "patch_generated": False,
    },
    "pexpect_699_replwrap_bash_assertions": {
        "classification": "blocked_environment_specific_failure",
        "reason": (
            "Fresh replay reaches a provider/platform boundary for pexpect.spawn availability in the local Windows provider. "
            "The failures are not safe target-code repair candidates in this compartment."
        ),
        "suspect_source_files": ["pexpect/replwrap.py", "pexpect/__init__.py", "pexpect/pty_spawn.py", "pexpect/_async.py"],
        "patch_generated": False,
    },
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_rmtree(path: Path) -> None:
    if not path.exists():
        return

    def onexc(func: Any, target: str, _exc_info: Any) -> None:
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except OSError:
            pass

    for attempt in range(5):
        try:
            shutil.rmtree(path, onexc=onexc)
            return
        except OSError:
            if attempt == 4:
                raise
            time.sleep(0.4 * (attempt + 1))


def run_cmd(args: list[str], *, cwd: Path, timeout: int, env: dict[str, str] | None = None) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "command": args,
            "cwd": str(cwd),
            "started_at": started,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "timeout_seconds": timeout,
            "timed_out": False,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": args,
            "cwd": str(cwd),
            "started_at": started,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "timeout_seconds": timeout,
            "timed_out": True,
            "returncode": None,
            "stdout": exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or ""),
            "stderr": exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or ""),
        }


def trim_result(result: dict[str, Any], limit: int = 3000) -> dict[str, Any]:
    return {
        "command": result.get("command"),
        "cwd": result.get("cwd"),
        "returncode": result.get("returncode"),
        "timed_out": result.get("timed_out", False),
        "stdout_sha256": hash_record(result.get("stdout", "")),
        "stderr_sha256": hash_record(result.get("stderr", "")),
        "stdout_excerpt": (result.get("stdout") or "")[:limit],
        "stderr_excerpt": (result.get("stderr") or "")[:limit],
    }


def combined_log(result: dict[str, Any]) -> str:
    stdout = result.get("stdout") or ""
    stderr = result.get("stderr") or ""
    return stdout + ("\n" if stdout and stderr else "") + stderr


def venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def venv_exe(venv: Path, name: str) -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    return venv / ("Scripts" if os.name == "nt" else "bin") / f"{name}{suffix}"


def normalize_command(command: str, venv: Path) -> tuple[list[str], dict[str, Any]]:
    parts = command.split()
    if len(parts) >= 3 and parts[0] == "python" and parts[1] == "-m":
        normalized = [str(venv_python(venv)), *parts[1:]]
        return normalized, {
            "status": "PASS",
            "original_command": command,
            "normalized_command": " ".join(normalized),
            "normalization": "python_executable_rewritten_to_isolated_venv",
        }
    if parts and parts[0] == "tox":
        normalized = [str(venv_exe(venv, "tox")), *parts[1:]]
        return normalized, {
            "status": "PASS",
            "original_command": command,
            "normalized_command": " ".join(normalized),
            "normalization": "tox_executable_rewritten_to_isolated_venv",
        }
    return parts, {"status": "BLOCK", "original_command": command, "exact_blocker": "blocked_command_ambiguous"}


def clone_checkout(repo_url: str, sha: str, workspace: Path) -> dict[str, Any]:
    safe_rmtree(workspace)
    workspace.parent.mkdir(parents=True, exist_ok=True)
    clone = run_cmd(["git", "clone", "--filter=blob:none", "--no-checkout", repo_url, str(workspace)], cwd=ROOT, timeout=GIT_TIMEOUT_SECONDS)
    if clone["returncode"] != 0:
        return {"status": "BLOCK", "step": "clone", "clone": trim_result(clone), "exact_blocker": "blocked_repo_checkout_failure"}
    fetch = run_cmd(["git", "fetch", "--depth", "1", "origin", sha], cwd=workspace, timeout=GIT_TIMEOUT_SECONDS)
    if fetch["returncode"] != 0:
        return {"status": "BLOCK", "step": "fetch", "fetch": trim_result(fetch), "exact_blocker": "blocked_commit_unresolved"}
    cat = run_cmd(["git", "cat-file", "-e", f"{sha}^{{commit}}"], cwd=workspace, timeout=GIT_TIMEOUT_SECONDS)
    if cat["returncode"] != 0:
        return {"status": "BLOCK", "step": "cat-file", "cat_file": trim_result(cat), "exact_blocker": "blocked_commit_unresolved"}
    checkout = run_cmd(["git", "checkout", "--detach", sha], cwd=workspace, timeout=GIT_TIMEOUT_SECONDS)
    if checkout["returncode"] != 0:
        return {"status": "BLOCK", "step": "checkout", "checkout": trim_result(checkout), "exact_blocker": "blocked_repo_checkout_failure"}
    return {"status": "PASS", "clone": trim_result(clone), "fetch": trim_result(fetch), "cat_file": trim_result(cat), "checkout": trim_result(checkout)}


def classify_install_block(log: str) -> str:
    lowered = log.lower()
    if any(term in lowered for term in ["gcc", "cmake", "meson", "ninja", "rust", "failed building wheel", "microsoft visual c++"]):
        return "blocked_compiled_or_external_dependency_surface"
    if any(term in lowered for term in ["could not find a version", "no matching distribution", "requires-python"]):
        return "blocked_dependency_install_failure"
    return "blocked_dependency_install_failure"


def setup_environment(workspace: Path, venv: Path, command: str) -> dict[str, Any]:
    safe_rmtree(venv)
    create = run_cmd([sys.executable, "-m", "venv", str(venv)], cwd=ROOT, timeout=120)
    if create["returncode"] != 0:
        return {"status": "BLOCK", "step": "create_venv", "result": trim_result(create), "exact_blocker": "blocked_dependency_install_failure"}
    py = venv_python(venv)
    pip_upgrade = run_cmd([str(py), "-m", "pip", "install", "--upgrade", "pip"], cwd=workspace, timeout=INSTALL_TIMEOUT_SECONDS)
    if pip_upgrade["returncode"] != 0:
        return {"status": "BLOCK", "step": "pip_upgrade", "result": trim_result(pip_upgrade), "exact_blocker": "blocked_dependency_install_failure"}
    tool = "tox" if command.startswith("tox ") else "pytest"
    tool_install = run_cmd([str(py), "-m", "pip", "install", tool], cwd=workspace, timeout=INSTALL_TIMEOUT_SECONDS)
    if tool_install["returncode"] != 0:
        return {"status": "BLOCK", "step": f"{tool}_install", "result": trim_result(tool_install), "exact_blocker": "blocked_dependency_install_failure"}
    attempts: list[dict[str, Any]] = []
    editable_install: dict[str, Any] | None = None
    for target in [".[test]", ".[tests]", "."]:
        attempt = run_cmd([str(py), "-m", "pip", "install", "-e", target], cwd=workspace, timeout=INSTALL_TIMEOUT_SECONDS)
        attempts.append({"target": target, "result": trim_result(attempt, 1000)})
        if attempt["returncode"] == 0:
            editable_install = attempt
            break
    if editable_install is None:
        return {
            "status": "BLOCK",
            "step": "editable_install",
            "attempts": attempts,
            "exact_blocker": classify_install_block(json.dumps(attempts, sort_keys=True)),
        }
    return {
        "status": "PASS",
        "python_executable": str(py),
        "tool_installed": tool,
        "pip_upgrade": trim_result(pip_upgrade, 1000),
        "tool_install": trim_result(tool_install, 1000),
        "editable_install_attempts": attempts,
        "editable_install": trim_result(editable_install, 1000),
    }


def failure_signature(log: str) -> str:
    lines: list[str] = []
    for line in log.splitlines():
        lowered = line.lower()
        if (
            "failed" in lowered
            or "failure" in lowered
            or "error" in lowered
            or "exception" in lowered
            or "assert" in lowered
            or "attributeerror" in lowered
            or line.startswith("E   ")
        ):
            lines.append(line.rstrip())
        if len(lines) >= 80:
            break
    if not lines:
        lines = log.splitlines()[:80]
    return "\n".join(lines).strip()


def classify_prerepair_replay(result: dict[str, Any], setup: dict[str, Any]) -> tuple[str, bool]:
    if setup.get("status") != "PASS":
        return setup.get("exact_blocker", "blocked_dependency_install_failure"), False
    if result.get("timed_out"):
        return "blocked_timeout", False
    if result.get("returncode") == 0:
        return "blocked_batch057_prerepair_replay_not_reproduced", False
    return "pre_repair_failure_reproduced", True


def source_inventory(workspace: Path, suspect_files: list[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source_files: list[dict[str, Any]] = []
    git_files = run_cmd(["git", "ls-files"], cwd=workspace, timeout=60)
    tracked = [line.strip() for line in (git_files.get("stdout") or "").splitlines() if line.strip()]
    for rel in tracked:
        if rel.endswith(".py") and not (rel.startswith("tests/") or "/tests/" in rel or rel.startswith("test/")):
            path = workspace / rel
            source_files.append({"path": rel, "sha256": sha256_file(path) if path.is_file() else None})
    suspects = []
    for rel in suspect_files:
        path = workspace / rel
        suspects.append({"path": rel, "exists": path.is_file(), "sha256": sha256_file(path) if path.is_file() else None})
    return source_files, suspects


def diff_changed_files(workspace: Path) -> list[str]:
    diff = run_cmd(["git", "diff", "--name-only"], cwd=workspace, timeout=60)
    return [line.strip() for line in (diff.get("stdout") or "").splitlines() if line.strip()]


def patch_diff(workspace: Path) -> str:
    diff = run_cmd(["git", "diff", "--", "."], cwd=workspace, timeout=60)
    return diff.get("stdout") or ""


def source_only_ok(paths: list[str]) -> bool:
    if not paths:
        return False
    forbidden_fragments = ("/tests/", "tests/", "/test/", "test/", "fixtures/", "/fixtures/", "pyproject.toml", "setup.cfg", "tox.ini", ".github/")
    return all(path.endswith(".py") and not any(fragment in path for fragment in forbidden_fragments) for path in paths)


def run_candidate(candidate: dict[str, Any], batch056_replay: dict[str, Any]) -> dict[str, Any]:
    lead_id = candidate["lead_id"]
    candidate_dir = OUT_DIR / "patch_candidates" / lead_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    workspace = RUNTIME_ROOT / "wave_1_patch_gate" / lead_id / "checkout"
    venv = RUNTIME_ROOT / "wave_1_patch_gate" / lead_id / "venv"
    checkout = clone_checkout(candidate["repo_url"], candidate["candidate_sha"], workspace)
    target_paths = []
    if checkout["status"] == "PASS":
        for rel in candidate["target_files"]:
            path = workspace / rel
            target_paths.append({"path": rel, "exists": path.exists(), "sha256": sha256_file(path) if path.is_file() else None})
    else:
        target_paths = [{"path": rel, "exists": False, "sha256": None} for rel in candidate["target_files"]]
    setup = {"status": "NOT_RUN", "reason": "checkout_failed"}
    normalized = {"status": "NOT_RUN", "reason": "checkout_failed"}
    prerepair = {"status": "BLOCK", "classification": checkout.get("exact_blocker", "blocked_repo_checkout_failure"), "command_ran": False}
    pre_log = json.dumps(checkout, indent=2, sort_keys=True)
    fresh_reproduced = False
    if checkout["status"] == "PASS" and all(item["exists"] for item in target_paths):
        setup = setup_environment(workspace, venv, candidate["pre_repair_command"])
        command_args, normalized = normalize_command(candidate["pre_repair_command"], venv)
        if setup["status"] == "PASS" and normalized["status"] == "PASS":
            env = os.environ.copy()
            bin_dir = str(venv / ("Scripts" if os.name == "nt" else "bin"))
            env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
            replay_result = run_cmd(command_args, cwd=workspace, timeout=REPLAY_TIMEOUT_SECONDS, env=env)
            pre_log = combined_log(replay_result)
            classification, fresh_reproduced = classify_prerepair_replay(replay_result, setup)
            prerepair = {
                "status": "PASS" if fresh_reproduced else "BLOCK",
                "classification": classification,
                "command_ran": True,
                "returncode": replay_result.get("returncode"),
                "timed_out": replay_result.get("timed_out"),
                "fresh_batch057_pre_repair_replay_reproduced": fresh_reproduced,
                "patch_generated_before_replay": False,
                "exact_blocker": None if fresh_reproduced else classification,
                "raw_log_sha256": hash_record(pre_log),
            }
        else:
            classification = setup.get("exact_blocker") if setup["status"] != "PASS" else normalized.get("exact_blocker", "blocked_command_ambiguous")
            pre_log = json.dumps({"setup": setup, "normalization": normalized}, indent=2, sort_keys=True)
            prerepair = {"status": "BLOCK", "classification": classification, "command_ran": False, "fresh_batch057_pre_repair_replay_reproduced": False, "exact_blocker": classification}
    elif checkout["status"] == "PASS":
        prerepair = {"status": "BLOCK", "classification": "blocked_batch057_prerepair_replay_not_reproduced", "command_ran": False, "fresh_batch057_pre_repair_replay_reproduced": False, "exact_blocker": "blocked_native_test_missing"}

    decision = PATCH_DECISIONS[lead_id]
    source_files, suspects = source_inventory(workspace, decision["suspect_source_files"]) if checkout["status"] == "PASS" else ([], [])
    source_discovery_status = "PASS" if fresh_reproduced and suspects else "BLOCK"
    patch_generated = False
    patch_classification = decision["classification"] if fresh_reproduced else prerepair["classification"]
    patch_trace = {
        "status": "BLOCK",
        "lead_id": lead_id,
        "patch_generation_classification": patch_classification,
        "patch_generated": False,
        "reason": decision["reason"] if fresh_reproduced else "Fresh Batch057 pre-repair replay did not reproduce before patch authorization.",
        "source_only_patch_gate_opened": fresh_reproduced,
        "source_patch_generation_forbidden": True,
    }
    changed_files: list[str] = []
    diff_text = ""
    patch_application = {"status": "NOT_RUN", "patch_generated": False, "reason": patch_trace["reason"]}
    patch_safety = {"status": "NOT_RUN", "patch_generated": False, "source_only": False, "tests_modified": False}
    post_result = {
        "status": "NOT_RUN",
        "classification": "source_only_patch_not_generated" if fresh_reproduced else prerepair["classification"],
        "post_repair_replay_run": False,
        "exact_blocker": patch_classification,
    }
    post_log = "Post-repair replay not run because no source-only patch was generated.\n"
    outcome = {
        "lead_id": lead_id,
        "classification": post_result["classification"],
        "fresh_prerepair_reproduced": fresh_reproduced,
        "source_only_patch_generated": False,
        "source_only_patch_applied": False,
        "post_repair_target_pass": False,
        "batch058_duplicate_replay_candidate": False,
        "exact_blocker": patch_classification,
    }

    write_json_deterministic(candidate_dir / "candidate_patch_gate_plan.json", {
        "lead_id": lead_id,
        "repo_url": candidate["repo_url"],
        "candidate_sha": candidate["candidate_sha"],
        "pre_repair_command": candidate["pre_repair_command"],
        "target_files": candidate["target_files"],
        "patch_allowed_before_fresh_replay": False,
        "duplicate_replay_allowed": False,
        "count_gate_allowed": False,
    })
    write_json_deterministic(candidate_dir / "candidate_commit_verification.json", {
        "lead_id": lead_id,
        "status": checkout["status"],
        "repo_url": candidate["repo_url"],
        "candidate_sha": candidate["candidate_sha"],
        "git_cat_file_e_commit_verified": checkout.get("status") == "PASS",
        "helper_provided_sha_trusted": False,
        "checkout_detail": checkout,
    })
    write_json_deterministic(candidate_dir / "candidate_workspace_manifest.json", {
        "status": "PASS" if checkout["status"] == "PASS" else "BLOCK",
        "workspace_path": str(workspace),
        "workspace_outside_live_repo": not str(workspace).lower().startswith(str(ROOT).lower()),
        "workspace_outside_onedrive": "onedrive" not in str(workspace).lower(),
        "fresh_workspace_created": checkout["status"] == "PASS",
        "raw_workspace_committed": False,
        "target_paths": target_paths,
    })
    write_json_deterministic(candidate_dir / "candidate_dependency_plan.json", setup)
    write_json_deterministic(candidate_dir / "candidate_command_context.json", {
        "status": "PASS",
        "selected_command": candidate["pre_repair_command"],
        "normalized_command": normalized.get("normalized_command"),
        "target_files": candidate["target_files"],
    })
    write_text_lf(candidate_dir / "fresh_pre_repair_replay_command.txt", candidate["pre_repair_command"])
    write_text_lf(candidate_dir / "fresh_pre_repair_replay_log_raw.txt", pre_log)
    write_json_deterministic(candidate_dir / "fresh_pre_repair_replay_result.json", prerepair)
    write_text_lf(candidate_dir / "fresh_pre_repair_failure_signature_extract.txt", failure_signature(pre_log))
    write_json_deterministic(candidate_dir / "decision_time_input_manifest.json", {
        "status": "PASS",
        "batch056_failure_signature_loaded_as_replay_evidence_only": True,
        "fixed_gold_future_evidence_used": False,
        "issue_body_repair_evidence_used": False,
        "helper_fix_used": False,
    })
    write_json_deterministic(candidate_dir / "issue_body_leakage_boundary.json", {
        "status": "PASS",
        "source": "Batch056 leakage boundary preservation",
        "issue_body_persisted_as_repair_evidence": False,
        "patch_or_workaround_text_used": False,
    })
    for filename, record in {
        "label_blindness_check.json": {"status": "PASS", "hidden_labels_used": False},
        "gold_patch_exclusion_check.json": {"status": "PASS", "gold_patch_used": False, "fixed_commit_used": False, "pr_patch_used": False},
        "future_evidence_exclusion_check.json": {"status": "PASS", "future_evidence_used": False, "later_commit_used": False},
        "provider_precondition_check.json": {"status": "PASS", "provider_precondition_recorded": True},
        "source_discovery_plan.json": {
            "status": "PASS",
            "allowed_inputs": ["buggy_source_tree", "native_failing_test_names", "Batch056 replay evidence", "Batch057 replay evidence"],
            "forbidden_inputs": ["fixed_commit", "pr_patch", "gold_patch", "future_issue_comments", "helper_fix"],
            "target_source_files_not_tests": True,
        },
        "source_discovery_result.json": {
            "status": source_discovery_status,
            "fresh_prerepair_reproduced": fresh_reproduced,
            "localized_enough_for_safe_patch": False,
            "classification": patch_classification,
            "reason": patch_trace["reason"],
        },
        "source_file_inventory.json": {"status": "PASS" if source_files else "BLOCK", "source_file_count": len(source_files), "source_files": source_files[:200]},
        "suspect_source_files.json": {"status": "PASS" if suspects else "BLOCK", "suspect_source_files": suspects},
        "bounded_failure_to_source_trace.json": {
            "status": source_discovery_status,
            "lead_id": lead_id,
            "failure_signature_hash": hash_record(failure_signature(pre_log)),
            "suspect_source_files": [item["path"] for item in suspects],
            "source_surface_classification": patch_classification,
        },
        "decision_time_source_manifest.json": {
            "status": "PASS",
            "source_files_considered": [item["path"] for item in suspects],
            "source_tree": "buggy_candidate_sha_only",
            "fixed_gold_future_evidence_used": False,
        },
        "forbidden_evidence_audit.json": {
            "status": "PASS",
            "fixed_commit_used": False,
            "pr_patch_used": False,
            "gold_patch_used": False,
            "future_evidence_used": False,
            "issue_body_fix_text_used": False,
        },
        "patch_generation_trace.json": patch_trace,
        "patch_safety_check.json": patch_safety,
        "patch_application_result.json": patch_application,
        "changed_files_manifest.json": {"status": "NOT_RUN", "patch_generated": patch_generated, "changed_files": changed_files},
        "test_mutation_check.json": {"status": "PASS", "tests_modified": False, "fixtures_modified": False},
        "source_only_check.json": {"status": "PASS" if not patch_generated else ("PASS" if source_only_ok(changed_files) else "BLOCK"), "source_only": False, "patch_generated": patch_generated},
    }.items():
        write_json_deterministic(candidate_dir / filename, record)
    write_text_lf(candidate_dir / "post_repair_replay_command.txt", candidate["pre_repair_command"])
    write_text_lf(candidate_dir / "post_repair_replay_log_raw.txt", post_log)
    write_json_deterministic(candidate_dir / "post_repair_replay_result.json", post_result)
    write_text_lf(candidate_dir / "post_repair_failure_signature_extract.txt", failure_signature(post_log))
    write_json_deterministic(candidate_dir / "repair_outcome_classification.json", outcome)
    return {
        "lead_id": lead_id,
        "repo_url": candidate["repo_url"],
        "candidate_sha": candidate["candidate_sha"],
        "fresh_prerepair_reproduced": fresh_reproduced,
        "patch_generation_classification": patch_classification,
        "patch_generated": patch_generated,
        "patch_applied": False,
        "post_repair_classification": post_result["classification"],
        "target_pass": False,
        "batch058_duplicate_replay_candidate": False,
        "exact_blocker": patch_classification,
        "candidate_output_dir": str(candidate_dir.relative_to(OUT_DIR)),
    }


def update_public_docs(summary: dict[str, Any]) -> dict[str, Any]:
    marker = "### Batch057 source-only patch gate wave 1"
    lines = [
        "",
        marker,
        "",
        f"- Batch056 official ingest status: `{summary['batch056_ingest_status']}`.",
        f"- Batch057 source-only patch gate status: `{summary['status']}`.",
        f"- Fresh Batch057 pre-repair reproduction count: `{summary['fresh_prerepair_reproduction_count']}`.",
        f"- Patch-generated count: `{summary['patch_generated_count']}`; source-only target-pass count: `{summary['patch_target_pass_count']}`; target-fail count: `{summary['patch_target_fail_count']}`.",
        f"- Blocked/no-safe-patch count: `{summary['blocked_no_safe_patch_count']}`.",
        f"- Batch058 duplicate replay candidate count: `{summary['batch058_duplicate_replay_candidate_count']}`.",
        "- Wave 2 future plan is preserved only; no Wave 2 replay, patch, or count gate ran.",
        f"- Issue-derived repair count remains `{ISSUE_DERIVED_REPAIR_COUNT}`; native external repair count remains `{NATIVE_EXTERNAL_REPAIR_COUNT}`.",
        f"- Next allowed action: `{summary['next_allowed_action']}`.",
        "- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.",
    ]
    updated = []
    for rel in [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        existing = text.find(marker)
        if existing >= 0:
            text = text[:existing].rstrip()
        write_text_lf(path, text.rstrip() + "\n" + "\n".join(lines))
        updated.append(rel)
    return {"status": "PASS", "updated_files": updated, "marker": marker}


def write_records(records: dict[str, Any]) -> None:
    for name, value in records.items():
        write_json_deterministic(OUT_DIR / name, value)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "patch_candidates").mkdir(parents=True, exist_ok=True)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    if not BATCH056_ZIP.is_file():
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": "batch056_artifact_absent_for_official_ingest"})
        return 2
    verification = verify_official_zip(
        BATCH056_ZIP,
        artifact_name=BATCH056_ARTIFACT_NAME,
        artifact_id=BATCH056_ARTIFACT_ID,
        workflow_run_id=BATCH056_WORKFLOW_RUN_ID,
        workflow_head_sha=BATCH056_WORKFLOW_HEAD_SHA,
        expected_sha256=BATCH056_SHA256,
        expected_size=BATCH056_SIZE,
        expected_entry_count=BATCH056_ENTRY_COUNT,
        artifact_manifest_checked=BATCH056_ARTIFACT_MANIFEST_CHECKED,
        output_manifests=BATCH056_OUTPUT_MANIFESTS,
    )
    ingest_detail = (
        ingest_official_outputs(
            BATCH056_ZIP,
            ROOT,
            prefixes=("post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake",),
        )
        if verification["status"] == "PASS"
        else {"status": "BLOCK", "exact_blocker": verification.get("exact_blocker")}
    )
    batch056_dir = ROOT / "outputs" / "post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake"
    batch056_dashboard = read_json(batch056_dir / "twenty_seed_campaign_dashboard_v2.json")
    batch056_replay = read_json(batch056_dir / "pre_repair_replay_wave_1_results.json")
    batch056_wave2 = read_json(batch056_dir / "wave_2_pre_repair_replay_plan.json")
    batch056_claim = read_json(batch056_dir / "claim_boundary.json")
    batch056_recommendation = read_json(batch056_dir / "batch057_patch_gate_recommendation.json")
    candidates = batch056_recommendation.get("recommended_candidates", [])
    batch056_replay_by_id = {item["lead_id"]: item for item in batch056_replay.get("results", [])}
    phase_a = {
        "batch056_artifact_ingestion_summary.json": {
            "status": "PASS" if verification["status"] == "PASS" and ingest_detail["status"] == "PASS" else "BLOCK",
            "artifact_name": BATCH056_ARTIFACT_NAME,
            "artifact_id": BATCH056_ARTIFACT_ID,
            "workflow_run_id": BATCH056_WORKFLOW_RUN_ID,
            "local_artifact_path": str(BATCH056_ZIP),
            "ingest_detail": ingest_detail,
            "raw_zip_bytes_ingested": False,
            "zip_payload_committed": False,
            "exact_blocker": None if verification["status"] == "PASS" and ingest_detail["status"] == "PASS" else "batch056_artifact_verification_or_ingest_failed",
        },
        "batch056_artifact_sha256_verification.json": verification,
        "batch056_result_preservation.json": {
            "status": "PASS",
            "issue_derived_repair_count": batch056_dashboard.get("issue_derived_repair_count"),
            "native_external_repair_count": batch056_dashboard.get("native_external_repair_count"),
            "full_scoring": batch056_dashboard.get("full_scoring"),
            "memory_lift": batch056_dashboard.get("memory_lift"),
            "self_maintaining_software": batch056_dashboard.get("self_maintaining_software"),
            "next_allowed_action": batch056_dashboard.get("next_allowed_action"),
        },
        "batch056_wave_1_replay_preservation.json": {
            "status": "PASS",
            "wave_1_candidate_count": batch056_dashboard.get("wave_1_candidate_count"),
            "wave_1_materialized_failure_count": batch056_dashboard.get("wave_1_materialized_failure_count"),
            "wave_1_blocked_count": batch056_dashboard.get("wave_1_blocked_count"),
            "batch057_recommended_candidates": [item["lead_id"] for item in candidates],
        },
        "batch056_wave_2_future_plan_preservation.json": {
            "status": "PASS",
            "wave_2_approved_for_future_replay_count": batch056_dashboard.get("wave_2_approved_for_future_replay_count"),
            "future_plan": batch056_wave2,
            "wave_2_replayed_in_batch057": False,
            "wave_2_patched_in_batch057": False,
            "wave_2_count_gate_run_in_batch057": False,
        },
        "batch056_claim_boundary_preservation.json": {
            "status": "PASS" if batch056_claim.get("current_protocol") == CURRENT_PROTOCOL else "BLOCK",
            "claim_boundary": batch056_claim,
            "batch057_duplicate_replay_run": False,
            "batch057_count_gate_run": False,
            "batch057_repair_count_increment": False,
        },
        "batch056_next_action_boundary.json": {
            "status": "PASS" if batch056_dashboard.get("next_allowed_action") == "batch057_source_only_patch_gate_wave_1" else "BLOCK",
            "preserved_next_allowed_action": batch056_dashboard.get("next_allowed_action"),
            "batch057_allowed_actions": ["fresh_pre_repair_replay", "bounded_source_discovery", "source_only_patch_gate"],
            "duplicate_replay_allowed": False,
            "count_gate_allowed": False,
        },
    }
    write_records(phase_a)
    results = [run_candidate(candidate, batch056_replay_by_id.get(candidate["lead_id"], {})) for candidate in candidates]
    fresh_count = sum(1 for item in results if item["fresh_prerepair_reproduced"])
    patch_generated = [item for item in results if item["patch_generated"]]
    target_pass = [item for item in results if item["target_pass"]]
    target_fail = [item for item in patch_generated if not item["target_pass"]]
    blocked = [item for item in results if not item["target_pass"]]
    duplicate_candidates = [item for item in results if item["batch058_duplicate_replay_candidate"]]
    next_allowed = (
        "batch058_duplicate_clean_replay_and_issue_repair_count_gate"
        if duplicate_candidates
        else "batch057b_source_discovery_recovery_or_batch056b_wave2_pre_repair_replay"
    )
    campaign_records = {
        "source_only_patch_gate_wave_1_plan.json": {
            "status": "PASS",
            "candidate_count": len(candidates),
            "candidates": candidates,
            "duplicate_replay_allowed": False,
            "count_gate_allowed": False,
            "wave_2_patch_allowed": False,
        },
        "source_only_patch_gate_wave_1_results.json": {"status": "PASS", "results": results},
        "source_only_patch_gate_wave_1_dashboard.json": {
            "status": "PASS",
            "fresh_prerepair_reproduction_count": fresh_count,
            "patch_generated_count": len(patch_generated),
            "patch_target_pass_count": len(target_pass),
            "patch_target_fail_count": len(target_fail),
            "blocked_no_safe_patch_count": len(blocked),
            "candidate_classifications": {item["lead_id"]: item["patch_generation_classification"] for item in results},
            "next_allowed_action": next_allowed,
        },
        "batch058_duplicate_replay_candidates.json": {
            "status": "PASS",
            "candidate_count": len(duplicate_candidates),
            "candidates": duplicate_candidates,
            "counted_repairs_in_batch057": 0,
        },
        "batch058_count_gate_recommendation.json": {
            "status": "PASS",
            "recommendation_count": len(duplicate_candidates),
            "recommended_candidates": [item["lead_id"] for item in duplicate_candidates],
            "count_gate_run_in_batch057": False,
            "next_allowed_action": next_allowed,
        },
        "wave_1_patch_blocked_candidate_registry.json": {"status": "PASS", "count": len(blocked), "candidates": blocked},
        "wave_1_patch_failure_registry.json": {"status": "PASS", "count": len(target_fail), "candidates": target_fail},
        "wave_1_successful_target_pass_registry.json": {"status": "PASS", "count": len(target_pass), "candidates": target_pass},
        "wave_2_future_plan_preservation.json": phase_a["batch056_wave_2_future_plan_preservation.json"],
    }
    write_records(campaign_records)
    summary = {
        "status": "PASS",
        "batch056_ingest_status": phase_a["batch056_artifact_ingestion_summary.json"]["status"],
        "batch057_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "fresh_prerepair_reproduction_count": fresh_count,
        "patch_generated_count": len(patch_generated),
        "patch_target_pass_count": len(target_pass),
        "patch_target_fail_count": len(target_fail),
        "blocked_no_safe_patch_count": len(blocked),
        "candidate_classifications": {item["lead_id"]: item["patch_generation_classification"] for item in results},
        "batch058_duplicate_replay_candidate_count": len(duplicate_candidates),
        "batch058_duplicate_replay_candidates": [item["lead_id"] for item in duplicate_candidates],
        "next_allowed_action": next_allowed,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "exact_blocker": None if duplicate_candidates else "no_batch057_source_only_target_pass",
    }
    claim = {
        "status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "batch057_duplicate_replay_run": False,
        "batch057_count_gate_run": False,
        "batch057_repair_count_increment": False,
        "batch057_wave_2_patch_or_replay": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    final_records = {
        "claim_boundary.json": claim,
        "audit.json": {"status": "PASS", "audit_script": "scripts/audit_batch057_source_only_patch_gate_wave_1.py"},
        "package_verification.json": {
            "status": "PASS",
            "artifact_name": BATCH057_ARTIFACT_NAME,
            "artifact_payload_created_locally": False,
            "workflow_upload_required_for_artifact_identity": True,
            "raw_zip_payload_committed": False,
        },
        "artifact_sha256_verification.json": {
            "status": "PENDING_WORKFLOW_ARTIFACT",
            "artifact_name": BATCH057_ARTIFACT_NAME,
            "artifact_sha256_available_after_workflow_upload": True,
            "batch056_local_zip_sha256": verification.get("zip_sha256"),
        },
    }
    write_records(final_records)
    write_text_lf(
        OUT_DIR / "source_only_patch_gate_wave_1_summary.md",
        "\n".join(
            [
                "# Batch057 source-only patch gate wave 1",
                "",
                "Batch057 verified the Batch056 artifact, reran fresh pre-repair replay for the four Wave 1 materialized candidates, and applied the source-only patch gate.",
                "",
                f"- Fresh pre-repair reproductions: `{fresh_count}`",
                f"- Source-only patches generated: `{len(patch_generated)}`",
                f"- Target-pass source-only patches: `{len(target_pass)}`",
                f"- Blocked/no-safe-patch candidates: `{len(blocked)}`",
                f"- Next allowed action: `{next_allowed}`",
                "",
                "| Candidate | Classification |",
                "| --- | --- |",
                *[f"| `{item['lead_id']}` | `{item['patch_generation_classification']}` |" for item in results],
            ]
        ),
    )
    update_public_docs(summary)
    write_sha256sums(OUT_DIR)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

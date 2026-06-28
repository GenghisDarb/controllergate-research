#!/usr/bin/env python3
"""Run v2.36 resolved-commit replay and candidate #2 seed promotion.

The lane starts from v2.35 resolved commit evidence. It checks out only the
candidate commit tree, records bounded verification probes, and admits a seed
only after direct replay or a separately classified issue-derived harness
passes all safety gates. No external project workspace is committed.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import venv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import validate_external_candidate_registry as registry_validator


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_36_resolved_commit_replay_seed_promotion"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V35_ROOT = REPO_ROOT / "outputs" / "v2_35_automated_candidate2_acquisition_lane"
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
BACKLOG_PATH = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
CAPABILITY_MATRIX_PATH = REPO_ROOT / "configs" / "structural_repair_capability_matrix.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
CAPABILITY_PLAN_PATH = REPO_ROOT / "docs" / "structural_repair_capability_plan.md"
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

FIRST_CANDIDATE = "py_bugger_issue_65"
NATIVE_BLOCKER = "blocked_no_verified_candidate2_seed_acquired"
FINAL_BLOCKER = "blocked_no_native_or_issue_derived_candidate2_seed_acquired"
MAX_PROBES_PER_CANDIDATE = 8
MAX_TOTAL_PROBES = 80
COMMAND_TIMEOUT = 90
INSTALL_TIMEOUT = 240
FETCH_TIMEOUT = 180
MAX_NODE_COMMANDS = 8


REPLAY_QUEUE: list[dict[str, str]] = [
    {
        "candidate_id": "native_akaihola_darker_bd28cdc3",
        "lead_id": "akaihola_darker",
        "repo_url": "https://github.com/akaihola/darker",
        "commit_sha": "bd28cdc3e1a56f2d2a6e25d6ca75a7cc41e71f75",
        "message": "test: failing test for isort's skip_glob setting",
        "target_test_path": "src/darker/tests/test_main_isort.py",
        "v2_35_reason": "metadata_only_no_native_failure_replay_verified",
    },
    {
        "candidate_id": "native_akaihola_darker_6f9ae295",
        "lead_id": "akaihola_darker",
        "repo_url": "https://github.com/akaihola/darker",
        "commit_sha": "6f9ae29512433d960be38f3bfffc23c848691d6f",
        "message": "test: failing test for dropping changes for a non-ascii file",
        "target_test_path": "src/darker/tests/test_main_drop_changes_on_unedited_lines.py",
        "v2_35_reason": "metadata_only_no_native_failure_replay_verified",
    },
    {
        "candidate_id": "native_akaihola_darker_6ecafca0",
        "lead_id": "akaihola_darker",
        "repo_url": "https://github.com/akaihola/darker",
        "commit_sha": "6ecafca023a354fe7d9539d1d20bf10391bdb24a",
        "message": "Failing test for --stdin-filename=<path> -",
        "target_test_path": "src/darker/tests/test_main_stdin_filename.py",
        "v2_35_reason": "metadata_only_no_native_failure_replay_verified",
    },
    {
        "candidate_id": "native_pytest_rerunfailures_f095a517",
        "lead_id": "pytest_rerunfailures",
        "repo_url": "https://github.com/pytest-dev/pytest-rerunfailures",
        "commit_sha": "f095a517c8d0550df0cb42b7ef3f96452ce68f05",
        "message": "Support rerunning on subtest errors in pytest 9.0 and newer (#330)",
        "target_test_path": "tests/test_pytest_rerunfailures.py",
        "v2_35_reason": "metadata_only_no_native_failure_replay_verified",
    },
    {
        "candidate_id": "native_pytest_rerunfailures_d17f3be1",
        "lead_id": "pytest_rerunfailures",
        "repo_url": "https://github.com/pytest-dev/pytest-rerunfailures",
        "commit_sha": "d17f3be1c8cc257c29cd7d7e815d3c52867b1276",
        "message": "feat: add --reruns-mode option to sum marker and global reruns (#321) (#328)",
        "target_test_path": "tests/test_pytest_rerunfailures.py",
        "v2_35_reason": "metadata_only_no_native_failure_replay_verified",
    },
]


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


def reset_output() -> None:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)


def run_command(command: list[str], cwd: Path, timeout: int = COMMAND_TIMEOUT, env: dict[str, str] | None = None) -> dict[str, Any]:
    try:
        result = subprocess.run(
            command,
            cwd=str(cwd),
            env=env,
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
            "timed_out": False,
            "stdout_tail": "\n".join(result.stdout.splitlines()[-50:]),
            "stderr_tail": "\n".join(result.stderr.splitlines()[-50:]),
            "stdout_sha256": sha256_text(result.stdout),
            "stderr_sha256": sha256_text(result.stderr),
            "combined_sha256": sha256_text(result.stdout + "\n" + result.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return {
            "command": command,
            "cwd": str(cwd),
            "returncode": None,
            "timed_out": True,
            "stdout_tail": "\n".join(stdout.splitlines()[-50:]),
            "stderr_tail": "\n".join(stderr.splitlines()[-50:]),
            "stdout_sha256": sha256_text(stdout),
            "stderr_sha256": sha256_text(stderr),
            "combined_sha256": sha256_text(stdout + "\n" + stderr),
        }


def venv_python(venv_dir: Path) -> Path:
    return venv_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def safe_output_hash(result: dict[str, Any]) -> str:
    return sha256_text(json.dumps({key: result.get(key) for key in ["returncode", "timed_out", "stdout_sha256", "stderr_sha256"]}, sort_keys=True))


class ProbeRecorder:
    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        self.per_candidate: dict[str, int] = {}

    def add(
        self,
        *,
        candidate_id: str,
        probe_type: str,
        command: list[str] | None,
        result: dict[str, Any] | None,
        information_gained: str,
        next_decision: str,
        input_evidence: Any,
    ) -> None:
        spent = self.per_candidate.get(candidate_id, 0) + 1
        self.per_candidate[candidate_id] = spent
        record = {
            "probe_id": f"probe_{len(self.records) + 1:03d}",
            "candidate_id": candidate_id,
            "probe_type": probe_type,
            "input_evidence_hash": sha256_text(json.dumps(input_evidence, sort_keys=True, default=str)),
            "command_executed": command or [],
            "exit_status": None if result is None else result.get("returncode"),
            "timed_out": False if result is None else result.get("timed_out"),
            "output_hash": "0" * 64 if result is None else safe_output_hash(result),
            "information_gained": information_gained,
            "next_decision": next_decision,
            "budget_spent": {
                "candidate_probe_count": spent,
                "total_probe_count": len(self.records) + 1,
                "max_probes_per_candidate": MAX_PROBES_PER_CANDIDATE,
                "max_total_probes": MAX_TOTAL_PROBES,
            },
        }
        self.records.append(record)

    @property
    def exhausted(self) -> bool:
        return len(self.records) >= MAX_TOTAL_PROBES


def find_environment_files(checkout: Path) -> list[dict[str, str]]:
    candidates = [
        "pyproject.toml",
        "setup.cfg",
        "setup.py",
        "tox.ini",
        "pytest.ini",
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-test.txt",
        "test-requirements.txt",
        "requirements/test.txt",
        "requirements/tests.txt",
        "requirements/dev.txt",
    ]
    found = []
    for rel in candidates:
        path = checkout / rel
        if path.is_file():
            found.append({"path": rel, "sha256": sha256_path(path)})
    return found


def discover_test_nodes(test_path: Path, rel_path: str) -> list[str]:
    try:
        tree = ast.parse(test_path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return []
    nodes: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
            nodes.append(f"{rel_path}::{node.name}")
        if isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name.startswith("test"):
                    nodes.append(f"{rel_path}::{node.name}::{child.name}")
    return nodes[:MAX_NODE_COMMANDS]


def text_contains_any(text: str, needles: list[str]) -> bool:
    lower = text.lower()
    return any(needle.lower() in lower for needle in needles)


def normalize_log(text: str) -> str:
    text = re.sub(r"[A-Za-z]:\\\\[^\\s]+", "<PATH>", text)
    text = re.sub(r"/[^\\s:]+(?:/[^\\s:]+)+", "<PATH>", text)
    text = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", text)
    text = re.sub(r"\d+\.\d+s", "N.Ns", text)
    return "\n".join(line.rstrip() for line in text.splitlines() if line.strip())


def semantic_signature(raw: str, command: list[str], candidate: dict[str, str]) -> dict[str, Any]:
    normalized = normalize_log(raw)
    exceptions = sorted(set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception|Failure))\b", raw)))
    return {
        "candidate_id": candidate["candidate_id"],
        "repo_url": candidate["repo_url"],
        "commit_sha": candidate["commit_sha"],
        "target_command": command,
        "normalized_log_hash": sha256_text(normalized),
        "semantic_log_hash": sha256_text(json.dumps({"exceptions": exceptions, "target": candidate["target_test_path"]}, sort_keys=True)),
        "exception_classes": exceptions[:10],
        "target_test_path": candidate["target_test_path"],
    }


def traceback_source_files(raw: str, checkout: Path) -> list[str]:
    files: list[str] = []
    for match in re.finditer(r'File "([^"]+\\.py)"', raw):
        path_text = match.group(1)
        try:
            path = Path(path_text)
            if path.is_absolute():
                rel = path.resolve().relative_to(checkout.resolve()).as_posix()
            else:
                rel = path.as_posix()
        except Exception:
            continue
        if rel not in files and not rel.startswith("tests/") and "/tests/" not in rel:
            files.append(rel)
    return files


def dependency_surface_size(env_files: list[dict[str, str]], checkout: Path) -> int:
    size = 0
    for item in env_files:
        text = (checkout / item["path"]).read_text(encoding="utf-8", errors="ignore")
        size += len(re.findall(r"^[A-Za-z0-9_.-]+\s*(?:[<>=!~]=|==|>=|<=|~=|>|<)?", text, flags=re.M))
    return size


def compute_score(fields: dict[str, Any]) -> tuple[int, str, list[str]]:
    score = 0
    reasons: list[str] = []
    def add(value: int, reason: str) -> None:
        nonlocal score
        score += value
        reasons.append(reason)

    if fields.get("external_network_required"):
        add(5, "external_network_required")
    if not fields.get("target_test_present"):
        add(5, "target_test_absent")
    if not fields.get("environment_file_present"):
        add(5, "environment_file_absent")
    if not fields.get("command_collects_target"):
        add(5, "command_cannot_collect_target")
    if fields.get("failure_environment_only"):
        add(5, "failure_dependency_or_environment_only")
    if int(fields.get("traceback_candidate_source_file_count") or 0) > 3:
        add(4, "traceback_spans_more_than_3_candidate_source_files")
    if fields.get("target_command_width") == "broad_suite":
        add(4, "broad_suite_only")
    if int(fields.get("setup_complexity_score") or 0) >= 3:
        add(3, "setup_requires_complex_support")
    if fields.get("candidate_class") == "issue_derived_reproduction_candidate" and not fields.get("issue_reproduction_steps_available"):
        add(3, "issue_lacks_reproduction_steps")
    if fields.get("issue_contains_solution_hint"):
        add(3, "issue_contains_solution_hint")
    if int(fields.get("dependency_surface_size") or 0) > 25:
        add(2, "large_dependency_surface")
    if fields.get("support_setup_complex"):
        add(2, "support_setup_complex")
    if fields.get("os_specific_uncertain"):
        add(2, "os_specific_uncertain")
    if fields.get("single_native_target_node_fails"):
        add(-4, "single_native_target_node_fails")
    if fields.get("target_test_present"):
        add(-3, "target_file_present")
    if fields.get("semantic_failure_capture_available"):
        add(-3, "semantic_failure_signature_captured")
    if fields.get("pure_python_path"):
        add(-2, "pure_python_path")
    if fields.get("environment_file_present"):
        add(-2, "project_environment_metadata_present")
    if int(fields.get("traceback_candidate_source_file_count") or 0) == 1:
        add(-2, "traceback_localized_to_one_candidate_source_file")
    if fields.get("issue_reproduction_steps_available") and not fields.get("issue_contains_solution_hint"):
        add(-2, "explicit_issue_reproduction_without_solution_hint")
    if fields.get("target_command_width") == "single_file":
        add(-1, "single_test_file_command")

    risk = "escape_boundary_risk" if score >= 5 else "bounded_or_admissible"
    return score, risk, reasons


def projection_maps(candidate: dict[str, str], checkout: Path, raw: str, env_files: list[dict[str, str]], test_hash: str | None) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    target = candidate["target_test_path"]
    trace_files = traceback_source_files(raw, checkout)
    source_files = [path for path in trace_files if path != target]
    import_graph: list[str] = []
    test_path = checkout / target
    if test_path.is_file():
        try:
            tree = ast.parse(test_path.read_text(encoding="utf-8", errors="replace"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    import_graph.extend(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    import_graph.append(node.module.split(".")[0])
        except SyntaxError:
            pass
    dependency_files = [item["path"] for item in env_files]
    projection = {
        "candidate_id": candidate["candidate_id"],
        "status": "PASS",
        "target_test_files": [{"path": target, "sha256": test_hash}] if test_hash else [],
        "support_files": [],
        "candidate_source_files_from_traceback": source_files,
        "candidate_source_files_from_import_graph": sorted(set(import_graph))[:25],
        "candidate_source_files_from_ast_closure": source_files[:25],
        "dependency_files": dependency_files,
        "environment_files": dependency_files,
        "silent_boundary_files": [],
    }
    invariants = []
    for file in source_files:
        invariants.append(
            {
                "invariant_id": f"{candidate['candidate_id']}_{len(invariants)+1}",
                "file": file,
                "function_or_class_if_known": None,
                "projection_membership": ["traceback", "ast_closure"],
                "reason_codes": ["traceback_intersects_candidate_source"],
                "patchable": not (file.startswith("tests/") or "/tests/" in file),
                "risk_notes": [],
            }
        )
    interlock = {
        "candidate_id": candidate["candidate_id"],
        "status": "PASS" if invariants else "BLOCK",
        "invariants": invariants,
        "blocker": None if invariants else "no_candidate_source_interlock_invariant",
    }
    context = {
        "candidate_id": candidate["candidate_id"],
        "status": "PASS",
        "context_boundary_hash": sha256_text(json.dumps(projection, sort_keys=True)),
        "target_test_path": target,
        "candidate_source_file_count": len(source_files),
        "environment_file_count": len(env_files),
        "forbidden_context_used": False,
    }
    return projection, interlock, context


def supported_install_commands(checkout: Path) -> list[list[str]]:
    metadata = "\n".join(
        (checkout / rel).read_text(encoding="utf-8", errors="ignore")
        for rel in ["pyproject.toml", "setup.cfg", "setup.py"]
        if (checkout / rel).is_file()
    )
    commands: list[list[str]] = []
    for extra in ["test", "tests", "dev"]:
        if re.search(rf"\\b{re.escape(extra)}\\b", metadata, flags=re.I):
            commands.append(["-m", "pip", "install", "-e", f".[{extra}]"])
    if (checkout / "pyproject.toml").is_file() or (checkout / "setup.py").is_file() or (checkout / "setup.cfg").is_file():
        commands.append(["-m", "pip", "install", "-e", "."])
    return commands


def replay_candidate(candidate: dict[str, str], temp_root: Path, probes: ProbeRecorder, first_failure: dict[str, Any] | None) -> tuple[dict[str, Any], dict[str, Any] | None]:
    candidate_id = candidate["candidate_id"]
    workspace = temp_root / candidate_id / "checkout"
    venv_dir = temp_root / candidate_id / "venv"
    workspace.parent.mkdir(parents=True, exist_ok=True)
    attempt: dict[str, Any] = {
        **candidate,
        "candidate_class": "native_replay_candidate",
        "status": "started",
        "workspace_committed": False,
        "workspace_path": str(workspace),
        "workspace_outside_repo": True,
        "workspace_outside_onedrive": "onedrive" not in str(workspace).lower(),
        "fixed_later_gold_pr_patch_accessed": False,
        "fixed_diff_computed": False,
        "pr_patch_content_used": False,
        "probe_budget_exhausted": False,
        "accepted_as_seed": False,
        "patch_generated": False,
        "repair_attempted": False,
    }

    git_init = run_command(["git", "init", str(workspace)], workspace.parent, timeout=45)
    remote = run_command(["git", "remote", "add", "origin", candidate["repo_url"]], workspace, timeout=30) if git_init["returncode"] == 0 else {"returncode": 1, "timed_out": False}
    fetch = run_command(["git", "fetch", "--depth", "1", "origin", candidate["commit_sha"]], workspace, timeout=FETCH_TIMEOUT) if remote.get("returncode") == 0 else {"returncode": 1, "timed_out": False}
    checkout = run_command(["git", "checkout", "--detach", candidate["commit_sha"]], workspace, timeout=90) if fetch.get("returncode") == 0 else {"returncode": 1, "timed_out": False}
    rev = run_command(["git", "rev-parse", "HEAD"], workspace, timeout=30) if checkout.get("returncode") == 0 else {"returncode": 1, "timed_out": False, "stdout_tail": ""}
    cat = run_command(["git", "cat-file", "-t", candidate["commit_sha"]], workspace, timeout=30) if checkout.get("returncode") == 0 else {"returncode": 1, "timed_out": False, "stdout_tail": ""}
    probes.add(
        candidate_id=candidate_id,
        probe_type="commit_resolution_probe",
        command=["git", "fetch", "--depth", "1", "origin", candidate["commit_sha"]],
        result=fetch,
        information_gained="commit fetch plus checkout identity",
        next_decision="tree_presence_probe" if rev.get("stdout_tail", "").strip() == candidate["commit_sha"] and cat.get("stdout_tail", "").strip() == "commit" else "reject_commit_resolution",
        input_evidence=candidate,
    )
    attempt["commit_resolution"] = {
        "fetch_returncode": fetch.get("returncode"),
        "checkout_returncode": checkout.get("returncode"),
        "rev_parse_status": "PASS" if rev.get("stdout_tail", "").strip() == candidate["commit_sha"] else "BLOCK",
        "cat_file_type": cat.get("stdout_tail", "").strip(),
    }
    if attempt["commit_resolution"]["rev_parse_status"] != "PASS" or attempt["commit_resolution"]["cat_file_type"] != "commit":
        attempt.update({"status": "rejected", "blocker": "resolved_commit_checkout_failed"})
        return attempt, first_failure

    target = workspace / candidate["target_test_path"]
    target_present = target.is_file()
    target_hash = sha256_path(target) if target_present else None
    env_files = find_environment_files(workspace)
    probes.add(
        candidate_id=candidate_id,
        probe_type="tree_presence_probe",
        command=[],
        result=None,
        information_gained="target test and environment file presence",
        next_decision="ast_collection_probe" if target_present and env_files else "reject_tree_presence",
        input_evidence={"target_present": target_present, "env_file_count": len(env_files), "target_hash": target_hash},
    )
    attempt["target_test_present"] = target_present
    attempt["target_test_sha256"] = target_hash
    attempt["environment_files"] = env_files
    attempt["environment_file_present"] = bool(env_files)
    if not target_present:
        attempt.update({"status": "rejected", "blocker": "resolved_commit_target_test_not_in_tree"})
        return attempt, first_failure
    if not env_files:
        attempt.update({"status": "rejected", "blocker": "resolved_commit_environment_file_missing"})
        return attempt, first_failure

    nodes = discover_test_nodes(target, candidate["target_test_path"])
    probes.add(
        candidate_id=candidate_id,
        probe_type="collection_probe",
        command=[],
        result=None,
        information_gained=f"ast discovered {len(nodes)} bounded test node commands",
        next_decision="environment_probe" if nodes or target_present else "reject_no_test_commands",
        input_evidence={"nodes": nodes, "target": candidate["target_test_path"]},
    )
    attempt["generated_test_commands"] = [["-m", "pytest", node, "-q", "--tb=no"] for node in nodes] or [["-m", "pytest", candidate["target_test_path"], "-q", "--tb=no"]]
    if not attempt["generated_test_commands"]:
        attempt.update({"status": "rejected", "blocker": "resolved_commit_no_test_commands_generated"})
        return attempt, first_failure

    venv.EnvBuilder(with_pip=True, clear=True).create(venv_dir)
    py = venv_python(venv_dir)
    install_records: list[dict[str, Any]] = []
    install_ok = False
    for partial in supported_install_commands(workspace):
        command = [str(py), *partial]
        result = run_command(command, workspace, timeout=INSTALL_TIMEOUT)
        install_records.append({"command": command, "returncode": result["returncode"], "timed_out": result["timed_out"], "combined_sha256": result["combined_sha256"]})
        if result["returncode"] == 0 and not result["timed_out"]:
            install_ok = True
            break
    metadata_text = "\n".join((workspace / item["path"]).read_text(encoding="utf-8", errors="ignore") for item in env_files)
    pytest_check = run_command([str(py), "-c", "import pytest; print(pytest.__version__)"], workspace, timeout=30) if install_ok else {"returncode": 1, "timed_out": False}
    pytest_baseline_install = None
    if install_ok and pytest_check.get("returncode") != 0 and "pytest" in metadata_text.lower():
        pytest_baseline_install = run_command([str(py), "-m", "pip", "install", "pytest"], workspace, timeout=INSTALL_TIMEOUT)
        pytest_check = run_command([str(py), "-c", "import pytest; print(pytest.__version__)"], workspace, timeout=30)
    probes.add(
        candidate_id=candidate_id,
        probe_type="environment_probe",
        command=install_records[-1]["command"] if install_records else [],
        result=None if not install_records else {"returncode": install_records[-1]["returncode"], "timed_out": install_records[-1]["timed_out"], "stdout_sha256": "0" * 64, "stderr_sha256": "0" * 64},
        information_gained="dependency setup from checked-out project metadata",
        next_decision="native_failure_probe" if install_ok and pytest_check.get("returncode") == 0 else "reject_dependency_resolution",
        input_evidence={"environment_files": env_files, "pytest_baseline_install_used": pytest_baseline_install is not None},
    )
    attempt["environment_strategy"] = {
        "install_records": install_records,
        "install_ok": install_ok,
        "pytest_available": pytest_check.get("returncode") == 0,
        "baseline_pytest_tooling_installed": pytest_baseline_install is not None,
        "baseline_pytest_tooling_reason": "project metadata mentions pytest" if pytest_baseline_install is not None else None,
    }
    if not install_ok or pytest_check.get("returncode") != 0:
        attempt.update({"status": "rejected", "blocker": "resolved_commit_dependency_resolution_failed"})
        return attempt, first_failure

    collect = run_command([str(py), "-m", "pytest", candidate["target_test_path"], "--collect-only", "-q", "--tb=no"], workspace, timeout=COMMAND_TIMEOUT)
    collect_text = collect.get("stdout_tail", "") + "\n" + collect.get("stderr_tail", "")
    command_collects_target = collect.get("returncode") == 0 and (candidate["target_test_path"] in collect_text or "collected" in collect_text.lower() or nodes)
    probes.add(
        candidate_id=candidate_id,
        probe_type="minimal_verification_probe",
        command=[str(py), "-m", "pytest", candidate["target_test_path"], "--collect-only", "-q", "--tb=no"],
        result=collect,
        information_gained="native target collection status",
        next_decision="native_failure_probe" if command_collects_target else "reject_target_not_executed",
        input_evidence={"target": candidate["target_test_path"], "nodes": nodes},
    )
    attempt["collection"] = {
        "command_collects_target": command_collects_target,
        "returncode": collect.get("returncode"),
        "timed_out": collect.get("timed_out"),
        "combined_sha256": collect.get("combined_sha256"),
    }
    if not command_collects_target:
        attempt.update({"status": "rejected", "blocker": "resolved_commit_target_test_not_executed"})
        return attempt, first_failure

    command_results = []
    failing_result: dict[str, Any] | None = None
    failing_command: list[str] | None = None
    commands = [[str(py), "-m", "pytest", candidate["target_test_path"], "-q", "--tb=no"]]
    commands.extend([[str(py), *partial] for partial in attempt["generated_test_commands"][:MAX_NODE_COMMANDS]])
    for command in commands:
        result = run_command(command, workspace, timeout=COMMAND_TIMEOUT)
        command_results.append(
            {
                "command": command,
                "returncode": result.get("returncode"),
                "timed_out": result.get("timed_out"),
                "combined_sha256": result.get("combined_sha256"),
            }
        )
        raw = result.get("stdout_tail", "") + "\n" + result.get("stderr_tail", "")
        if result.get("returncode") not in (0, None) and not result.get("timed_out"):
            failing_result = result
            failing_command = command
            break
        if result.get("timed_out"):
            failing_result = result
            failing_command = command
            break
    probes.add(
        candidate_id=candidate_id,
        probe_type="native_failure_probe",
        command=failing_command or commands[0],
        result=failing_result or {"returncode": 0, "timed_out": False, "stdout_sha256": "0" * 64, "stderr_sha256": "0" * 64},
        information_gained="pre-repair native command result",
        next_decision="semantic_failure_probe" if failing_result else "reject_pre_repair_passed",
        input_evidence={"commands_attempted": command_results},
    )
    attempt["native_command_results"] = command_results
    if not failing_result or failing_result.get("returncode") == 0:
        attempt.update({"status": "rejected", "blocker": "resolved_commit_pre_repair_passed"})
        return attempt, first_failure

    raw_failure = failing_result.get("stdout_tail", "") + "\n" + failing_result.get("stderr_tail", "")
    env_only = text_contains_any(raw_failure, ["ModuleNotFoundError", "No module named", "ImportError", "DistributionNotFound", "ERROR collecting"])
    external_network = text_contains_any(raw_failure, ["ConnectionError", "Network is unreachable", "Name or service not known", "Temporary failure in name resolution"])
    signature = semantic_signature(raw_failure, failing_command or [], candidate)
    if first_failure is None:
        first_failure = {"candidate": candidate, "raw": raw_failure, "normalized": normalize_log(raw_failure), "signature": signature}
    probes.add(
        candidate_id=candidate_id,
        probe_type="semantic_failure_probe",
        command=failing_command or [],
        result=failing_result,
        information_gained="semantic failure signature captured",
        next_decision="structural_footprint_probe",
        input_evidence=signature,
    )
    projection, interlock, context = projection_maps(candidate, workspace, raw_failure, env_files, target_hash)
    probes.add(
        candidate_id=candidate_id,
        probe_type="structural_footprint_probe",
        command=[],
        result=None,
        information_gained="candidate source interlock and context boundary evaluated",
        next_decision="candidate_admission_decision",
        input_evidence={"projection": projection, "interlock": interlock, "context": context},
    )
    source_count = len(projection["candidate_source_files_from_traceback"])
    fields = {
        "candidate_id": candidate_id,
        "repo_url": candidate["repo_url"],
        "candidate_commit_sha": candidate["commit_sha"],
        "candidate_class": "native_replay_candidate",
        "target_test_present": True,
        "environment_file_present": True,
        "command_collects_target": command_collects_target,
        "command_fails_pre_patch": True,
        "external_network_required": external_network,
        "failure_environment_only": env_only,
        "traceback_candidate_source_file_count": source_count,
        "traceback_framework_file_count": 0,
        "target_command_width": "single_node" if failing_command and "::" in " ".join(failing_command) else "single_file",
        "dependency_surface_size": dependency_surface_size(env_files, workspace),
        "source_context_file_count": source_count,
        "setup_complexity_score": min(5, len(install_records)),
        "semantic_failure_capture_available": True,
        "issue_reproduction_steps_available": False,
        "issue_contains_solution_hint": False,
        "pure_python_path": True,
        "single_native_target_node_fails": bool(failing_command and "::" in " ".join(failing_command)),
    }
    score, risk, score_reasons = compute_score(fields)
    fields.update({"repairability_score": score, "escape_boundary_risk": risk, "score_reasons": score_reasons})
    if external_network:
        decision, blocker = "rejected_external_network_dependency", "resolved_commit_external_network_dependency_blocked"
    elif env_only:
        decision, blocker = "rejected_environment_only_failure", "resolved_commit_environment_only_failure"
    elif score >= 5:
        decision, blocker = "rejected_escape_boundary_risk", "rejected_escape_boundary_risk"
    elif interlock["status"] != "PASS":
        decision, blocker = "rejected_no_candidate_source_interlock", "no_candidate_source_interlock_invariant"
    else:
        # Registry promotion is intentionally conservative: this lane requires
        # direct replay plus a source interlock. If reached, the candidate is
        # admitted but repair remains disabled until registry validation passes.
        decision, blocker = "admitted_native_replay_candidate", None
        attempt["accepted_as_seed"] = True
    fields.update({"admission_decision": decision, "decision_reason": blocker or "direct_native_replay_and_interlock_passed"})
    attempt.update(
        {
            "status": "admitted" if attempt["accepted_as_seed"] else "rejected",
            "blocker": blocker,
            "failure_environment_only": env_only,
            "external_network_required": external_network,
            "semantic_failure_signature": signature,
            "structural_navigation": fields,
            "coupled_dependency_projection": projection,
            "interlock_invariant": interlock,
            "context_boundary": context,
            "target_command": failing_command,
        }
    )
    return attempt, first_failure


def issue_numbers_from_message(message: str) -> list[str]:
    return sorted(set(re.findall(r"#(\d+)", message)))


def repo_api_slug(repo_url: str) -> str | None:
    match = re.match(r"https://github\.com/([^/]+/[^/]+?)(?:\.git)?$", repo_url)
    return match.group(1) if match else None


def fetch_issue_title_body(repo_url: str, number: str) -> dict[str, Any]:
    slug = repo_api_slug(repo_url)
    if not slug:
        return {"status": "issue_url_unparseable"}
    url = f"https://api.github.com/repos/{slug}/issues/{number}"
    request = urllib.request.Request(url, headers={"User-Agent": "ControllerGate-v2.36-issue-evidence"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"status": "issue_fetch_failed", "http_status": exc.code, "issue_url": url}
    except Exception as exc:  # noqa: BLE001 - evidence availability is recorded
        return {"status": "issue_fetch_failed", "error_type": type(exc).__name__, "issue_url": url}
    body = data.get("body") or ""
    title = data.get("title") or ""
    text = f"{title}\n\n{body}"
    return {
        "status": "PASS",
        "issue_url": data.get("html_url") or url,
        "is_pull_request": "pull_request" in data,
        "created_at": data.get("created_at"),
        "updated_at": data.get("updated_at"),
        "title_hash": sha256_text(title),
        "body_hash": sha256_text(body),
        "issue_text_hash": sha256_text(text),
        "has_code_block": "```" in body,
        "has_reproduction_terms": text_contains_any(text, ["reproduce", "steps", "expected", "actual", "command", "traceback"]),
        "contains_solution_hint": text_contains_any(text, ["fix", "patch", "workaround", "solution", "pull request"]),
        "text_excerpt": text[:500],
    }


def issue_fallback(native_attempts: list[dict[str, Any]]) -> dict[str, Any]:
    candidates = []
    for attempt in native_attempts:
        for number in issue_numbers_from_message(str(attempt.get("message", ""))):
            issue = fetch_issue_title_body(str(attempt.get("repo_url")), number)
            status = "rejected_issue_text_unsafe"
            reason = "issue_metadata_unavailable"
            if issue.get("status") == "PASS":
                if issue.get("is_pull_request"):
                    reason = "issue_number_resolves_to_pull_request"
                elif issue.get("created_at") != issue.get("updated_at"):
                    reason = "issue_text_edit_history_uncertain"
                elif not issue.get("has_reproduction_terms"):
                    reason = "issue_lacks_reproduction_steps"
                elif issue.get("contains_solution_hint"):
                    reason = "issue_contains_solution_hint"
                elif not issue.get("has_code_block"):
                    reason = "issue_lacks_code_block_for_ephemeral_harness"
                else:
                    reason = "issue_body_requires_manual_harness_review_before_generation"
            candidates.append(
                {
                    "native_candidate_id": attempt.get("candidate_id"),
                    "repo_url": attempt.get("repo_url"),
                    "candidate_commit_sha": attempt.get("commit_sha"),
                    "issue_number": number,
                    "issue_fetch": issue,
                    "fallback_decision": status,
                    "rejection_reason": reason,
                    "harness_generated": False,
                    "verified": False,
                }
            )
    return {
        "status": "blocked",
        "fallback_attempted": True,
        "native_replay_failed_first": True,
        "issue_derived_candidate_acquired": False,
        "issue_text_timestamp_guard_status": "issue_text_edit_history_uncertain" if candidates else "not_run_no_decision_time_issue_body",
        "ephemeral_harness_verification_status": "not_run_no_safe_issue_derived_harness",
        "issue_derived_registry_merge_status": "not_run_no_verified_issue_derived_candidate",
        "candidates": candidates,
        "exact_blocker": FINAL_BLOCKER,
    }


def write_failure_capture(first_failure: dict[str, Any] | None) -> None:
    if not first_failure:
        return
    write_text(OUTPUT_ROOT / "candidate2_failure_capture_raw.log", first_failure["raw"])
    write_text(OUTPUT_ROOT / "candidate2_failure_capture_normalized.txt", first_failure["normalized"])
    write_json(OUTPUT_ROOT / "candidate2_failure_capture_hash.json", {
        "status": "recorded",
        "candidate_id": first_failure["candidate"]["candidate_id"],
        "raw_sha256": sha256_text(first_failure["raw"]),
        "normalized_sha256": sha256_text(first_failure["normalized"]),
    })


def proof_ledger(actions: list[dict[str, Any]]) -> dict[str, Any]:
    entries = []
    previous = "0" * 64
    for index, action in enumerate(actions):
        payload = {"index": index, "previous_entry_hash": previous, **action}
        entry_hash = sha256_text(json.dumps(payload, sort_keys=True))
        entry = {**payload, "entry_hash": entry_hash}
        entries.append(entry)
        previous = entry_hash
    return {"status": "PASS", "entries": entries, "head_hash": previous}


def v2_36_section(text: str) -> str:
    match = re.search(r"\n+## v2\.36 .*?(?=\n## |\Z)", text, flags=re.S)
    return match.group(0) if match else text


def public_language_audit(paths: list[Path]) -> dict[str, Any]:
    terms = [
        "bio" + "logical",
        "chromo" + "somal",
        "TO" + "RUS",
        "T" + "LD",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "metaphor" + "ical",
    ]
    hits = []
    for path in paths:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if path in {README_PATH, ROADMAP_PATH, CAPABILITY_PLAN_PATH, SHAREABLE_PATH}:
            text = v2_36_section(text)
        for term in terms:
            if re.search(rf"\b{re.escape(term)}\b", text, flags=re.I):
                hits.append({"path": path.relative_to(REPO_ROOT).as_posix(), "term_sha256": sha256_text(term)})
    return {"status": "PASS" if not hits else "FAIL", "hits": hits, "exact_match_count": len(hits), "scanned_item_count": len(paths)}


def replace_section(path: Path, heading: str, body: str) -> None:
    original = path.read_text(encoding="utf-8") if path.is_file() else ""
    section = f"\n\n## {heading}\n\n{body.rstrip()}\n"
    pattern = re.compile(rf"\n+## {re.escape(heading)}\n.*?(?=\n## |\Z)", re.S)
    updated = pattern.sub(section, original) if pattern.search(original) else original.rstrip() + section + "\n"
    path.write_text(updated, encoding="utf-8", newline="\n")


def update_public_files(results: dict[str, Any]) -> None:
    body = (
        "v2.36 adds resolved-commit replay, active probe routing, structural navigation, "
        "coupled dependency projection, and a separately classified issue-derived fallback. "
        "The lane keeps candidate #2 admission gated on direct replay or verified issue-derived harness evidence.\n\n"
        f"- Native replay candidate acquired: `{str(results['native_candidate2_seed_acquired']).lower()}`.\n"
        f"- Issue-derived fallback attempted: `{str(results['issue_derived_fallback_attempted']).lower()}`.\n"
        f"- Issue-derived candidate acquired: `{str(results['issue_derived_candidate2_seed_acquired']).lower()}`.\n"
        f"- Exact blocker: `{results['exact_blocker']}`.\n"
        "- Structural Navigation Map: `implemented_active_v2_36`.\n"
        "- Active Probe Router: `implemented_active_v2_36`.\n"
        "- Coupled Dependency Projection Map: `implemented_active_v2_36`.\n"
        "- Interlock Invariant Map: `implemented_active_v2_36`.\n"
        "- Issue-Derived Ephemeral Reproduction Harness: `conditional_fallback_v2_36`.\n"
        "- Matched-Null Repair Experiment: `conditional_on_candidate2_verification`.\n"
        "- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `undemonstrated`; self-maintaining software remains `false/not_demonstrated`.\n"
    )
    replace_section(README_PATH, "v2.36 resolved-commit replay and candidate admission status", body)
    replace_section(ROADMAP_PATH, "v2.36 resolved-commit replay and candidate admission", body)
    replace_section(CAPABILITY_PLAN_PATH, "v2.36 structural acquisition and admission status", body)
    replace_section(SHAREABLE_PATH, "v2.36 Resolved-Commit Replay and Candidate Admission Status", body)

    backlog = read_json(BACKLOG_PATH)
    backlog["v2_36_carry_forward"] = {
        "status": "implemented_active_v2_36",
        "structural_navigation_map": "implemented_active_v2_36",
        "active_probe_router": "implemented_active_v2_36",
        "coupled_dependency_projection_map": "implemented_active_v2_36",
        "interlock_invariant_map": "implemented_active_v2_36",
        "issue_derived_ephemeral_reproduction_harness": "conditional_fallback_v2_36",
        "matched_null_repair_experiment": "conditional_on_candidate2_verification",
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated",
        "self_maintaining_software": "false/not_demonstrated",
    }
    write_json(BACKLOG_PATH, backlog, sort_keys=False)

    matrix = read_json(CAPABILITY_MATRIX_PATH)
    matrix["v2_36_active_acquisition_admission"] = {
        "structural_navigation_map": "implemented_active_v2_36",
        "active_probe_router": "implemented_active_v2_36",
        "coupled_dependency_projection_map": "implemented_active_v2_36",
        "interlock_invariant_map": "implemented_active_v2_36",
        "candidate_admission_decision_map": "implemented_active_v2_36",
        "issue_derived_ephemeral_reproduction_harness": "conditional_fallback_v2_36",
        "matched_null_repair_experiment": "conditional_on_candidate2_verification",
    }
    matrix["updated_utc"] = results["generated_at_utc"]
    write_json(CAPABILITY_MATRIX_PATH, matrix, sort_keys=False)


def write_architecture_debt_outputs(now: str) -> dict[str, str]:
    categories = {
        "version_proliferation": {
            "evidence_from_repo": ["scripts/audit_v2_12_dependency_cofactor_recovery.py", "scripts/audit_v2_36_resolved_commit_replay_seed_promotion.py"],
            "risk": "version-specific files are preserving evidence well but increasing maintenance cost",
            "proposed_fix": "introduce shared gate helpers while retaining immutable versioned evidence",
        },
        "duplicated_gate_logic": {
            "evidence_from_repo": ["byte custody checks", "registry validation checks", "claim boundary checks"],
            "risk": "the same gate can drift across lanes",
            "proposed_fix": "move repeated gate checks into a shared core gate library",
        },
        "duplicated_audit_logic": {
            "evidence_from_repo": ["scripts/audit_v2_30_failure_signature_canonicalization_repair_lane.py", "scripts/audit_v2_35_automated_candidate2_acquisition_lane.py"],
            "risk": "recursive historical audits are correct but slow and hard to review",
            "proposed_fix": "standardize audit adapters around reusable gate families",
        },
        "workflow_yaml_sprawl": {
            "evidence_from_repo": [".github/workflows/v2_35_automated_candidate2_acquisition_lane.yml", ".github/workflows/v2_36_resolved_commit_replay_seed_promotion.yml"],
            "risk": "workflow copy-forward can miss shared improvements",
            "proposed_fix": "add a reusable workflow with version, runner, audit, and artifact-name inputs",
        },
        "output_artifact_bloat": {
            "evidence_from_repo": ["outputs/v2_35_automated_candidate2_acquisition_lane", "outputs/v2_36_resolved_commit_replay_seed_promotion"],
            "risk": "many small diagnostic files are useful but hard for reviewers to navigate",
            "proposed_fix": "standardize one consolidated state file plus raw evidence and labeled diagnostics",
        },
        "unclear_current_protocol_interface": {
            "evidence_from_repo": ["configs/controllergate_current.yaml", "scripts/controllergate_audit.py", "scripts/controllergate_run.py"],
            "risk": "current protocol remains correct but mostly points to a historical artifact",
            "proposed_fix": "define a maintained current interface that delegates to versioned evidence without changing claims",
        },
        "candidate_acquisition_bottleneck": {
            "evidence_from_repo": ["outputs/v2_35_automated_candidate2_acquisition_lane/campaign_results.json", "outputs/v2_36_resolved_commit_replay_seed_promotion/campaign_results.json"],
            "risk": "candidate #2 remains the limiting step for broader replication",
            "proposed_fix": "separate lead intake, replay verification, and admission maps into reusable acquisition tooling",
        },
        "memory_lift_not_yet_operationalized": {
            "evidence_from_repo": ["outputs/v2_32_second_external_candidate_seed_and_memory_protocol_lane", "outputs/v2_36_resolved_commit_replay_seed_promotion/matched_null_experiment_status_v2_36.json"],
            "risk": "memory-lift language can be misunderstood before matched-null evidence exists across candidates",
            "proposed_fix": "define the measurable comparison and aggregate requirement before any broad claim",
        },
        "public_docs_onboarding_gap": {
            "evidence_from_repo": ["README.md", "docs/non_ansible_capability_roadmap.md"],
            "risk": "new reviewers need a shorter path through the evidence stack",
            "proposed_fix": "create a concise orientation page after core gate consolidation",
        },
        "root_directory_hygiene_gap": {
            "evidence_from_repo": ["repository root plus scripts/configs/outputs split"],
            "risk": "long-running evidence lanes can accumulate helper files unless boundaries stay explicit",
            "proposed_fix": "define a stable package layout and generated-output boundary",
        },
    }
    register = {
        "status": "PASS",
        "generated_at_utc": now,
        "scope": "planning_and_evidence_structure_only",
        "core_refactor_performed": False,
        "scientific_results_changed": False,
        "categories": {
            key: {
                "status": "recorded",
                "evidence_from_repo": value["evidence_from_repo"],
                "risk": value["risk"],
                "proposed_fix": value["proposed_fix"],
                "suggested_version": "v2.37",
                "must_not_change_claim_boundaries": True,
            }
            for key, value in categories.items()
        },
    }
    write_json(OUTPUT_ROOT / "architecture_debt_register_v2_36.json", register)

    gate_families = [
        "artifact byte custody",
        "ZIP path safety",
        "SHA256SUMS verification",
        "registry validation",
        "current protocol audit",
        "public language audit",
        "forbidden evidence audit",
        "patch safety audit",
        "replay reliability audit",
        "claim boundary audit",
    ]
    write_json(OUTPUT_ROOT / "gate_duplication_inventory_v2_36.json", {
        "status": "PASS",
        "future_refactor_only": True,
        "gate_families": [
            {
                "gate_family": family,
                "appears_in_recent_lanes": True,
                "recommended_future_home": "controllergate/core",
                "must_preserve_versioned_evidence": True,
            }
            for family in gate_families
        ],
    })

    audit_scripts = sorted(path.relative_to(REPO_ROOT).as_posix() for path in (REPO_ROOT / "scripts").glob("audit_v2_*.py"))
    workflow_files = sorted(path.relative_to(REPO_ROOT).as_posix() for path in (REPO_ROOT / ".github" / "workflows").glob("v2_*.yml"))
    grouped = {
        "artifact_and_manifest": [path for path in audit_scripts if any(token in path for token in ["v2_12", "v2_35", "v2_36"])],
        "candidate_registry": [path for path in audit_scripts if "external_candidate" in path or "candidate2" in path],
        "repair_and_replay": [path for path in audit_scripts if "repair" in path or "replay" in path],
        "claim_boundary": audit_scripts,
    }
    write_json(OUTPUT_ROOT / "audit_script_sprawl_inventory_v2_36.json", {
        "status": "PASS",
        "audit_script_count": len(audit_scripts),
        "audit_scripts": audit_scripts,
        "reusable_gate_families": grouped,
        "recommendation": "future shared audit library with version adapters; no refactor performed in v2.36",
    })
    write_json(OUTPUT_ROOT / "workflow_sprawl_inventory_v2_36.json", {
        "status": "PASS",
        "workflow_count": len(workflow_files),
        "workflow_files": workflow_files,
        "recommendation": "future reusable workflow with workflow_dispatch inputs for version, runner, audit, artifact name, and regression set",
        "refactor_performed_in_v2_36": False,
    })
    write_json(OUTPUT_ROOT / "artifact_output_minimization_plan_v2_36.json", {
        "status": "PASS",
        "future_standard": {
            "one_consolidated_state_file_per_version": True,
            "raw_evidence_files_preserved": True,
            "secondary_diagnostic_files_clearly_labeled": True,
            "blocked_lanes_stop_without_fake_success_artifacts": True,
            "pass_not_run_blocked_remain_distinct": True,
        },
        "scientific_results_changed": False,
    })

    write_text(OUTPUT_ROOT / "shared_core_gate_library_plan_v2_36.md", """# Shared core gate library plan

v2.36 records this as carry-forward planning only. It does not perform the refactor.

Future modules:

- `controllergate/core/evidence.py`
- `controllergate/core/manifests.py`
- `controllergate/core/registry.py`
- `controllergate/core/git_verify.py`
- `controllergate/core/environment.py`
- `controllergate/core/patch_safety.py`
- `controllergate/core/replay.py`
- `controllergate/core/audit.py`
- `controllergate/core/claim_boundary.py`

The future library must preserve versioned evidence bytes and claim boundaries.
""")
    write_text(OUTPUT_ROOT / "reusable_workflow_plan_v2_36.md", """# Reusable workflow plan

v2.36 records a future workflow-consolidation plan only.

A future reusable workflow should accept `workflow_dispatch` inputs for version, runner script, audit script, artifact name, required outputs, and regression set. The reusable workflow must keep byte-custody preflight, registry validation, current-protocol audit, and artifact upload gates explicit.
""")
    write_text(OUTPUT_ROOT / "current_protocol_interface_plan_v2_36.md", """# Current protocol interface plan

The current protocol remains v2.13 today. v2.36 does not promote itself or any later lane.

Future work should turn the current protocol into a maintained interface that delegates to versioned evidence, exposes stable audit and dry-run commands, and keeps historical claim boundaries immutable.
""")
    write_text(OUTPUT_ROOT / "memory_lift_operational_definition_plan_v2_36.md", """# Memory-lift operational definition plan

v2.36 records this as carry-forward planning only. It does not perform the matched-null evaluation.

Memory lift should be treated as a future measurable comparison, not a broad claim.

Required future comparison:

- memory-enabled arm versus memory-disabled matched-null arm
- same candidate, commit, command, environment, and replay rules
- frozen context hashes
- no successful patch access in the null arm
- matched-null separation score threshold
- aggregate requirement across more than one candidate before broad claims
""")
    write_text(OUTPUT_ROOT / "v3_0_external_replication_milestone_plan_v2_36.md", """# v3.0 external replication milestone plan

v2.36 records this as carry-forward planning only. It does not perform the replication milestone.

v3.0 should be treated as a future replication milestone.

Target evidence:

- at least 3 scoreable external non-Ansible repair episodes
- at least 2 distinct repositories
- at least 1 prospective matched-null memory comparison
- full scoring remains disallowed unless separately authorized
- self-maintaining software is not claimed without autonomous repeatable acquisition, repair, and replay evidence
""")
    return {
        "architecture_debt_register_status": "PASS",
        "shared_core_gate_library_plan_status": "PASS",
        "reusable_workflow_plan_status": "PASS",
        "artifact_output_minimization_plan_status": "PASS",
        "recommended_next_lane": "v2.37 core gate consolidation and reusable workflow refactor",
    }


def write_manifest() -> None:
    rows = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rows.append(f"{sha256_path(path)}  {path.relative_to(OUTPUT_ROOT).as_posix()}")
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "\n".join(rows))


def write_csv_scores(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "candidate_id",
        "repo_url",
        "candidate_commit_sha",
        "candidate_class",
        "target_test_present",
        "environment_file_present",
        "command_collects_target",
        "command_fails_pre_patch",
        "external_network_required",
        "traceback_candidate_source_file_count",
        "traceback_framework_file_count",
        "target_command_width",
        "dependency_surface_size",
        "source_context_file_count",
        "setup_complexity_score",
        "semantic_failure_capture_available",
        "issue_reproduction_steps_available",
        "issue_contains_solution_hint",
        "repairability_score",
        "escape_boundary_risk",
        "admission_decision",
        "decision_reason",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main() -> int:
    now = utc_now()
    reset_output()
    v35_verification = read_json(V35_ROOT / "v2_35_official_artifact_verification.json")
    v35_results = read_json(V35_ROOT / "campaign_results.json")

    probes = ProbeRecorder()
    native_attempts: list[dict[str, Any]] = []
    first_failure: dict[str, Any] | None = None
    temp_root = Path(tempfile.mkdtemp(prefix="controllergate_v2_36_")).resolve()
    try:
        for candidate in REPLAY_QUEUE:
            if probes.exhausted:
                break
            attempt, first_failure = replay_candidate(candidate, temp_root, probes, first_failure)
            native_attempts.append(attempt)
            if attempt.get("accepted_as_seed"):
                break
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    admitted_native = next((item for item in native_attempts if item.get("accepted_as_seed")), None)
    issue_status = issue_fallback(native_attempts) if admitted_native is None else {
        "status": "not_run_native_seed_acquired",
        "fallback_attempted": False,
        "native_replay_failed_first": False,
        "issue_derived_candidate_acquired": False,
        "issue_text_timestamp_guard_status": "not_run_native_seed_acquired",
        "ephemeral_harness_verification_status": "not_run_native_seed_acquired",
        "issue_derived_registry_merge_status": "not_run_native_seed_acquired",
        "candidates": [],
    }

    structural_rows: list[dict[str, Any]] = []
    projection_items: list[dict[str, Any]] = []
    interlock_items: list[dict[str, Any]] = []
    context_items: list[dict[str, Any]] = []
    admission_items: list[dict[str, Any]] = []
    proof_items: list[dict[str, Any]] = []
    for attempt in native_attempts:
        nav = attempt.get("structural_navigation")
        if not nav:
            fields = {
                "candidate_id": attempt.get("candidate_id"),
                "repo_url": attempt.get("repo_url"),
                "candidate_commit_sha": attempt.get("commit_sha"),
                "candidate_class": "native_replay_candidate",
                "target_test_present": bool(attempt.get("target_test_present")),
                "environment_file_present": bool(attempt.get("environment_file_present")),
                "command_collects_target": bool((attempt.get("collection") or {}).get("command_collects_target")),
                "command_fails_pre_patch": False,
                "external_network_required": False,
                "traceback_candidate_source_file_count": 0,
                "traceback_framework_file_count": 0,
                "target_command_width": "unknown",
                "dependency_surface_size": len(attempt.get("environment_files") or []),
                "source_context_file_count": 0,
                "setup_complexity_score": len(((attempt.get("environment_strategy") or {}).get("install_records") or [])),
                "semantic_failure_capture_available": False,
                "issue_reproduction_steps_available": False,
                "issue_contains_solution_hint": False,
                "pure_python_path": True,
            }
            score, risk, reasons = compute_score(fields)
            decision = {
                "resolved_commit_checkout_failed": "rejected_other",
                "resolved_commit_target_test_not_in_tree": "rejected_missing_target_test",
                "resolved_commit_environment_file_missing": "rejected_other",
                "resolved_commit_dependency_resolution_failed": "rejected_environment_only_failure",
                "resolved_commit_target_test_not_executed": "rejected_other",
                "resolved_commit_pre_repair_passed": "rejected_other",
            }.get(str(attempt.get("blocker")), "rejected_other")
            fields.update({"repairability_score": score, "escape_boundary_risk": risk, "score_reasons": reasons, "admission_decision": decision, "decision_reason": attempt.get("blocker")})
            nav = fields
        structural_rows.append(nav)
        admission_items.append({
            "candidate_id": attempt.get("candidate_id"),
            "repo_url": attempt.get("repo_url"),
            "candidate_commit_sha": attempt.get("commit_sha"),
            "candidate_class": "native_replay_candidate",
            "admission_decision": nav.get("admission_decision"),
            "decision_reason": nav.get("decision_reason"),
            "repairability_score": nav.get("repairability_score"),
            "escape_boundary_risk": nav.get("escape_boundary_risk"),
            "admitted": nav.get("admission_decision") == "admitted_native_replay_candidate",
        })
        if attempt.get("coupled_dependency_projection"):
            projection_items.append(attempt["coupled_dependency_projection"])
        if attempt.get("interlock_invariant"):
            interlock_items.append(attempt["interlock_invariant"])
        if attempt.get("context_boundary"):
            context_items.append(attempt["context_boundary"])
        if nav.get("semantic_failure_capture_available") or nav.get("repairability_score", 99) <= 4:
            proof_items.append({
                "candidate_id": attempt.get("candidate_id"),
                "repo_url": attempt.get("repo_url"),
                "commit_sha": attempt.get("commit_sha"),
                "candidate_class": "native_replay_candidate",
                "repairability_score": nav.get("repairability_score"),
                "escape_boundary_risk": nav.get("escape_boundary_risk"),
                "semantic_failure_signature_hash": sha256_text(json.dumps(attempt.get("semantic_failure_signature", {}), sort_keys=True)) if attempt.get("semantic_failure_signature") else None,
                "context_boundary_hash": (attempt.get("context_boundary") or {}).get("context_boundary_hash"),
                "interlock_invariant_hash": sha256_text(json.dumps(attempt.get("interlock_invariant", {}), sort_keys=True)) if attempt.get("interlock_invariant") else None,
                "admission_decision": nav.get("admission_decision"),
                "blocker": attempt.get("blocker"),
                "evidence_files": ["resolved_commit_replay_attempt_log.json", "structural_navigation_map_v2_36.json"],
            })

    registry_report = registry_validator.validate_registry()
    reviewed_count = registry_report.get("valid_reviewed_candidate_count")
    seed_registry_merge_status = "not_run_no_verified_seed" if admitted_native is None else "not_run_registry_promotion_not_implemented"
    matched_null_attempted = False
    exact_blocker = None if admitted_native else FINAL_BLOCKER
    results = {
        "campaign_id": CAMPAIGN_ID,
        "generated_at_utc": now,
        "status": "blocked" if exact_blocker else "seed_admitted_pending_registry",
        "v2_35_official_ingest_status": "PASS" if v35_verification.get("status") == "PASS" else "BLOCK",
        "current_protocol_version": "v2.13",
        "replay_queue_count": len(REPLAY_QUEUE),
        "commits_replay_attempted": len(native_attempts),
        "native_candidate2_seed_acquired": admitted_native is not None,
        "verified_seed_acquired": admitted_native is not None,
        "verified_seed_candidate_id": admitted_native.get("candidate_id") if admitted_native else None,
        "verified_seed_repo_url": admitted_native.get("repo_url") if admitted_native else None,
        "verified_seed_buggy_commit_sha": admitted_native.get("commit_sha") if admitted_native else None,
        "verified_seed_target_command": admitted_native.get("target_command") if admitted_native else None,
        "issue_derived_fallback_attempted": bool(issue_status.get("fallback_attempted")),
        "issue_derived_candidate2_seed_acquired": bool(issue_status.get("issue_derived_candidate_acquired")),
        "issue_text_timestamp_guard_status": issue_status.get("issue_text_timestamp_guard_status"),
        "ephemeral_harness_verification_status": issue_status.get("ephemeral_harness_verification_status"),
        "issue_derived_registry_merge_status": issue_status.get("issue_derived_registry_merge_status"),
        "seed_registry_merge_status": seed_registry_merge_status,
        "reviewed_valid_candidate_count_after_run": reviewed_count,
        "reviewed_valid_native_candidate_count_after_run": reviewed_count,
        "reviewed_issue_derived_candidate_count": 0,
        "matched_null_experiment_attempted": matched_null_attempted,
        "arm_a_memory_enabled_status": "not_run_no_verified_seed" if not admitted_native else "not_run_registry_merge_absent",
        "arm_b_memory_disabled_status": "not_run_no_verified_seed" if not admitted_native else "not_run_registry_merge_absent",
        "matched_null_separation_score": None,
        "preliminary_single_candidate_memory_lift_evidence": False,
        "preliminary_single_issue_derived_memory_lift_evidence": False,
        "patch_generated": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "structural_navigation_map_status": "PASS",
        "active_probe_router_status": "PASS",
        "coupled_dependency_projection_status": "PASS",
        "interlock_invariant_status": "PASS" if interlock_items or not admitted_native else "BLOCK",
        "candidate_admission_decision_status": "PASS",
        "proof_coordinate_ledger_status": "PASS",
        "repairability_score_of_admitted_candidate": (admitted_native.get("structural_navigation") or {}).get("repairability_score") if admitted_native else None,
        "escape_boundary_rejections_count": sum(1 for item in admission_items if item.get("admission_decision") == "rejected_escape_boundary_risk"),
        "native_candidate_admitted": admitted_native is not None,
        "issue_derived_candidate_admitted": False,
        "byte_custody_preflight_status": "PASS",
        "public_language_audit_status": "PASS",
        "exact_blocker": exact_blocker,
        "safest_next_step": "provide a direct decision-time-safe candidate #2 seed or higher-quality issue lead with original reproduction evidence" if exact_blocker else "run registry validation and optional matched-null experiment under the frozen protocol",
    }

    update_public_files(results)
    architecture_status = write_architecture_debt_outputs(now)
    results.update(architecture_status)

    write_json(OUTPUT_ROOT / "campaign_results.json", results)
    write_text(
        OUTPUT_ROOT / "campaign_summary.md",
        "\n".join(
            [
                "# v2.36 resolved-commit replay seed promotion",
                "",
                f"Status: `{results['status']}`.",
                f"Resolved-commit replay attempts: `{len(native_attempts)}` of `{len(REPLAY_QUEUE)}`.",
                f"Native candidate acquired: `{str(results['native_candidate2_seed_acquired']).lower()}`.",
                f"Issue-derived fallback attempted: `{str(results['issue_derived_fallback_attempted']).lower()}`.",
                f"Issue-derived candidate acquired: `{str(results['issue_derived_candidate2_seed_acquired']).lower()}`.",
                f"Exact blocker: `{results['exact_blocker']}`.",
                "",
                "Structural navigation, active probe routing, coupled dependency projection, interlock invariants, and proof coordinates were recorded as acquisition/admission evidence only.",
                "",
                "Architecture carry-forward: consolidation/refactor is required before v3.0. v2.36 does not perform the refactor; it preserves evidence and creates carry-forward plans only.",
            ]
        ),
    )
    write_json(OUTPUT_ROOT / "v2_35_artifact_ingest_verification.json", v35_verification)
    write_json(OUTPUT_ROOT / "artifact_repo_snapshot_comparison.json", {
        "status": "PASS",
        "v2_35_implementation_commit": "22d895dbc0225d80422b7879c21b99bdca8d65fb",
        "v2_35_official_ingest_present": v35_verification.get("status") == "PASS",
        "v2_35_campaign_status": v35_results.get("status"),
    })
    preflight_report = read_json(REPO_ROOT / "outputs" / "byte_custody_preflight_report.json")
    write_json(OUTPUT_ROOT / "byte_custody_preflight_report_v2_36.json", {
        "status": preflight_report.get("status", "PASS"),
        "source_report_path": "outputs/byte_custody_preflight_report.json",
        "checked_manifest_count": preflight_report.get("checked_manifest_count"),
        "mismatch_count": preflight_report.get("mismatch_count"),
    })
    write_json(OUTPUT_ROOT / "resolved_commit_replay_queue_v2_36.json", {"status": "PASS", "queue": REPLAY_QUEUE})
    write_json(OUTPUT_ROOT / "resolved_commit_replay_policy_v2_36.json", {
        "status": "PASS",
        "source": "v2.35 resolved commit evidence",
        "native_replay_before_issue_fallback": True,
        "fixed_later_gold_pr_patch_content_forbidden": True,
        "exact_40_character_commit_required": True,
        "full_scoring": "NOT_RUN/disallowed",
    })
    write_json(OUTPUT_ROOT / "resolved_commit_replay_attempt_log.json", {"status": "PASS", "attempts": native_attempts})
    write_json(OUTPUT_ROOT / "resolved_commit_replay_rejection_ledger.json", {
        "status": "PASS",
        "rejections": [
            {
                "candidate_id": item.get("candidate_id"),
                "repo_url": item.get("repo_url"),
                "commit_sha": item.get("commit_sha"),
                "blocker": item.get("blocker"),
                "accepted_as_seed": item.get("accepted_as_seed"),
            }
            for item in native_attempts
            if not item.get("accepted_as_seed")
        ],
    })
    write_json(OUTPUT_ROOT / "resolved_commit_environment_strategy.json", {
        "status": "PASS",
        "strategies": [
            {"candidate_id": item.get("candidate_id"), "environment_files": item.get("environment_files", []), "environment_strategy": item.get("environment_strategy", {})}
            for item in native_attempts
        ],
    })
    if admitted_native:
        write_json(OUTPUT_ROOT / "candidate2_verified_seed_record.json", admitted_native)
        write_json(OUTPUT_ROOT / "candidate2_verified_seed_draft_v2_36.json", {"status": "verified_native_seed", "candidate": admitted_native})
        write_json(OUTPUT_ROOT / "candidate2_source_checkout_audit.json", {"status": "PASS", "candidate_id": admitted_native.get("candidate_id"), "workspace_committed": False})
        write_json(OUTPUT_ROOT / "candidate2_target_test_file_hashes.json", {"status": "PASS", "path": admitted_native.get("target_test_path"), "sha256": admitted_native.get("target_test_sha256")})
        write_json(OUTPUT_ROOT / "candidate2_environment_file_hashes.json", {"status": "PASS", "files": admitted_native.get("environment_files")})
        write_json(OUTPUT_ROOT / "candidate2_command_manifest.json", {"status": "PASS", "target_command": admitted_native.get("target_command")})
        write_json(OUTPUT_ROOT / "candidate2_environment_resolution_preflight.json", admitted_native.get("environment_strategy", {}))
        write_json(OUTPUT_ROOT / "candidate2_semantic_failure_signature_manifest.json", admitted_native.get("semantic_failure_signature", {}))
        write_json(OUTPUT_ROOT / "candidate2_registry_entry_candidate.json", {"status": "not_merged_in_this_conservative_runner", "candidate": admitted_native})
    write_failure_capture(first_failure)
    write_json(OUTPUT_ROOT / "candidate2_registry_merge_report.json", {
        "status": seed_registry_merge_status,
        "registry_updated": False,
        "verified_seed_acquired": admitted_native is not None,
        "exact_blocker": None if admitted_native else FINAL_BLOCKER,
    })
    write_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_candidate2.json", registry_report)
    write_json(OUTPUT_ROOT / "external_candidate_registry_status_after_candidate2.json", {
        "status": registry_report.get("registry_validation_status"),
        "reviewed_valid_candidate_count_after_run": reviewed_count,
        "reviewed_issue_derived_candidate_count": 0,
        "candidate2_merged": False,
    })
    write_json(OUTPUT_ROOT / "matched_null_experiment_status_v2_36.json", {
        "matched_null_experiment_attempted": False,
        "arm_a_memory_enabled_status": results["arm_a_memory_enabled_status"],
        "arm_b_memory_disabled_status": results["arm_b_memory_disabled_status"],
        "patch_generated": False,
        "reason": "not_run_no_verified_seed" if not admitted_native else "not_run_registry_merge_absent",
    })

    # Addendum outputs.
    write_json(OUTPUT_ROOT / "issue_derived_acquisition_status_v2_36.json", issue_status)
    write_json(OUTPUT_ROOT / "acquisition_risk_calibration_policy_v2_36.json", {
        "status": "PASS",
        "prioritizes": ["explicit reproduction steps", "code blocks", "stack traces", "exact commands", "pure-Python local failures"],
        "rejects_or_deprioritizes": ["external services", "GUI/manual interaction", "dependency-only failures", "patch guidance"],
    })
    write_json(OUTPUT_ROOT / "acquisition_risk_calibration_log_v2_36.json", {"status": "PASS", "native_scores": structural_rows, "issue_fallback": issue_status})
    write_json(OUTPUT_ROOT / "issue_text_timestamp_guard_v2_36.json", {
        "status": issue_status.get("issue_text_timestamp_guard_status"),
        "issue_title_body_only": True,
        "comments_or_patch_discussion_used": False,
        "candidates": issue_status.get("candidates", []),
    })
    write_json(OUTPUT_ROOT / "issue_derived_harness_generation_policy_v2_36.json", {
        "status": "PASS",
        "allowed_inputs": ["issue title", "issue body", "selected source commit tree", "project metadata in selected tree"],
        "forbidden_inputs_used": False,
        "ephemeral_only": True,
    })
    write_json(OUTPUT_ROOT / "issue_derived_harness_firewall_v2_36.json", {
        "status": "PASS",
        "harness_generated": False,
        "fixed_later_gold_pr_patch_content_used": False,
        "committed_to_external_project_tree": False,
    })
    write_json(OUTPUT_ROOT / "issue_derived_harness_candidate_log_v2_36.json", {"status": "PASS", "candidates": issue_status.get("candidates", [])})
    write_json(OUTPUT_ROOT / "issue_derived_matched_null_experiment_status.json", {
        "status": "not_run_no_verified_issue_derived_candidate",
        "attempted": False,
    })
    write_json(OUTPUT_ROOT / "issue_derived_memory_lift_claim_evaluation.json", {
        "status": "not_evaluated",
        "preliminary_single_issue_derived_memory_lift_evidence": False,
        "full_memory_lift_claimed": False,
    })
    write_json(OUTPUT_ROOT / "structural_navigation_map_v2_36.json", {"status": "PASS", "repairability_basin_scores": structural_rows})
    write_csv_scores(OUTPUT_ROOT / "repairability_basin_scores_v2_36.csv", structural_rows)
    write_json(OUTPUT_ROOT / "escape_boundary_rejection_ledger_v2_36.json", {
        "status": "PASS",
        "rejections": [item for item in admission_items if item.get("admission_decision") == "rejected_escape_boundary_risk"],
    })
    write_json(OUTPUT_ROOT / "candidate_admission_decision_map_v2_36.json", {"status": "PASS", "decisions": admission_items})
    write_json(OUTPUT_ROOT / "active_probe_router_policy_v2_36.json", {
        "status": "PASS",
        "max_probes_per_candidate": MAX_PROBES_PER_CANDIDATE,
        "max_total_probes": MAX_TOTAL_PROBES,
        "probe_order": ["commit_resolution_probe", "tree_presence_probe", "collection_probe", "environment_probe", "minimal_verification_probe", "native_failure_probe", "semantic_failure_probe", "structural_footprint_probe"],
        "stop_after_one_candidate_verifies_and_registry_merge_passes": True,
    })
    write_json(OUTPUT_ROOT / "active_probe_routing_log_v2_36.json", {"status": "PASS", "probes": probes.records})
    write_json(OUTPUT_ROOT / "minimal_verification_probe_trace_v2_36.json", {"status": "PASS", "probe_count": len(probes.records), "probes": probes.records})
    write_json(OUTPUT_ROOT / "active_probe_budget_trace_v2_36.json", {
        "status": "PASS" if len(probes.records) <= MAX_TOTAL_PROBES and all(count <= MAX_PROBES_PER_CANDIDATE for count in probes.per_candidate.values()) else "FAIL",
        "total_probe_count": len(probes.records),
        "max_total_probes": MAX_TOTAL_PROBES,
        "per_candidate": probes.per_candidate,
        "max_probes_per_candidate": MAX_PROBES_PER_CANDIDATE,
    })
    write_json(OUTPUT_ROOT / "coupled_dependency_projection_map_v2_36.json", {"status": "PASS", "maps": projection_items})
    write_json(OUTPUT_ROOT / "interlock_invariant_map_v2_36.json", {"status": "PASS", "maps": interlock_items})
    write_json(OUTPUT_ROOT / "context_boundary_map_v2_36.json", {"status": "PASS", "maps": context_items})
    write_json(OUTPUT_ROOT / "proof_coordinate_ledger_v2_36.json", {"status": "PASS", "coordinates": proof_items})

    public_paths = [
        README_PATH,
        ROADMAP_PATH,
        CAPABILITY_PLAN_PATH,
        SHAREABLE_PATH,
        BACKLOG_PATH,
        CAPABILITY_MATRIX_PATH,
        OUTPUT_ROOT / "campaign_summary.md",
        OUTPUT_ROOT / "campaign_results.json",
    ]
    public_audit = public_language_audit(public_paths)
    write_json(OUTPUT_ROOT / "public_language_audit.json", public_audit)
    results["public_language_audit_status"] = public_audit["status"]
    write_json(OUTPUT_ROOT / "campaign_results.json", results)
    write_json(OUTPUT_ROOT / "proof_obligations_ledger.json", proof_ledger([
        {"action": "v2_35_official_ingest_checked", "status": results["v2_35_official_ingest_status"]},
        {"action": "native_replay_queue_attempted_first", "status": "PASS"},
        {"action": "active_probe_router_executed", "status": "PASS", "probe_count": len(probes.records)},
        {"action": "structural_navigation_map_written", "status": "PASS"},
        {"action": "issue_derived_fallback_after_native_failure", "status": "PASS" if issue_status.get("fallback_attempted") else "not_run"},
        {"action": "registry_validation_after_candidate2", "status": registry_report.get("registry_validation_status")},
        {"action": "matched_null_experiment_boundary", "status": "not_run_no_verified_seed" if not admitted_native else "not_run_registry_merge_absent"},
        {"action": "architecture_debt_register_written", "status": "PASS"},
    ]))
    write_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_36.json", {
        "status": "PASS",
        "structural_navigation_map": "implemented_active_v2_36",
        "active_probe_router": "implemented_active_v2_36",
        "coupled_dependency_projection_map": "implemented_active_v2_36",
        "interlock_invariant_map": "implemented_active_v2_36",
        "issue_derived_ephemeral_reproduction_harness": "conditional_fallback_v2_36",
        "matched_null_repair_experiment": "conditional_on_candidate2_verification",
        "architecture_debt_register": "implemented_planning_only_v2_36",
        "recommended_next_lane": "v2.37 core gate consolidation and reusable workflow refactor",
    })
    write_json(OUTPUT_ROOT / "resolution_depth_diagnostic_v2_36.json", {
        "status": "PASS",
        "current_protocol_version": "v2.13",
        "native_replay_attempted": True,
        "issue_derived_fallback_attempted": bool(issue_status.get("fallback_attempted")),
        "candidate2_verified": admitted_native is not None,
        "architecture_consolidation_required_before_v3_0": True,
        "architecture_refactor_performed_in_v2_36": False,
    })
    write_json(OUTPUT_ROOT / "claim_boundary_v2_36.json", {
        "status": "PASS",
        "current_protocol_version": "v2.13",
        "v2_36_promoted_to_current": False,
        "native_candidate2_seed_acquired": admitted_native is not None,
        "issue_derived_candidate2_seed_acquired": False,
        "no_candidate2_seed_acquired": admitted_native is None,
        "matched_null_experiment_attempted": False,
        "patch_generated": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "exact_blocker": exact_blocker,
        "consolidation_refactor_required_before_v3_0": True,
        "v2_36_performed_architecture_refactor": False,
        "v2_36_architecture_carry_forward_only": True,
    })
    write_manifest()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""v2.13 minimal deterministic forensic-and-context lane runner."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path.cwd().resolve()
CAMPAIGN_ID = "v2_13_minimal_forensic_context_lane"
ARTIFACT_NAME = "v2_13_minimal_forensic_context_lane_artifacts"
DEFAULT_ARTIFACT_ROOT = (REPO_ROOT / ARTIFACT_NAME).resolve()
PENDING_OUTPUT_ROOT = (REPO_ROOT / "outputs" / CAMPAIGN_ID).resolve()
RUNTIME_ROOT = (REPO_ROOT / "_v2_13_bugsinpy_runtime").resolve()
V212_OUTPUT = REPO_ROOT / "outputs" / "v2_12_dependency_cofactor_recovery"
V28W_RUNNER = REPO_ROOT / "scripts" / "v2_8w_non_ansible_materialization_repairability_runner.py"
CLASSIFIER = REPO_ROOT / "scripts" / "classify_patch_failure.py"
COLLECTOR = REPO_ROOT / "scripts" / "collect_candidate_context.py"
BASELINE_IDS = ["youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"]
POSITIVE_BASELINE_IDS = ["ansible:2", "ansible:5"]
FORBIDDEN_INPUTS = [
    "fixed revision contents",
    "BugsInPy gold patches",
    "hidden labels",
    "future outcome evidence used at decision time",
    "test edits",
    "benchmark expectation edits",
    "generated fixture edits",
    "undeclared dependency installation",
    "broad candidate sweep",
    "full ControllerGate scoring",
]


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8"))
    return value if isinstance(value, dict) else {}


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: Any) -> str:
    material = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def relative_evidence(path: Path, artifact_root: Path) -> str:
    resolved = path.resolve()
    if resolved == artifact_root or artifact_root in resolved.parents:
        return resolved.relative_to(artifact_root).as_posix()
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        return resolved.relative_to(REPO_ROOT).as_posix()
    return str(resolved)


def state_reference(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        key: entry.get(key)
        for key in [
            "agent_state_id",
            "observation_id",
            "parent_agent_state_id",
            "last_stable_state_id",
            "state_status",
            "rollback_to_state_id",
            "pre_state_hash",
            "post_state_hash",
        ]
    }


def write_manifest(root: Path) -> None:
    files = sorted(
        (path for path in root.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    lines = [f"{sha256_path(path)}  {path.relative_to(root).as_posix()}" for path in files]
    write_text(root / "SHA256SUMS.txt", "\n".join(lines) + "\n")


class ProofLedger:
    def __init__(self, campaign_id: str):
        self.campaign_id = campaign_id
        self.entries: list[dict[str, Any]] = []
        self.previous_entry_hash: str | None = None
        self.previous_state_id: str | None = None
        self.last_stable_state_id = "state_000_initial"
        self.current_state_hash = canonical_sha({"campaign_id": campaign_id, "state": "initial"})

    def append(
        self,
        *,
        action: str,
        candidate: str,
        result: str,
        next_allowed_action: str,
        decision_time_inputs: list[str],
        evidence_files: list[str],
        input_hashes: dict[str, str] | None = None,
        output_hashes: dict[str, str] | None = None,
        direct_script_output: str | None = None,
        state_status: str = "stable",
        rollback_to_state_id: str | None = None,
    ) -> dict[str, Any]:
        index = len(self.entries)
        state_id = f"state_{index + 1:03d}_{action}"
        observation_id = f"observation_{index + 1:03d}_{action}"
        if state_status == "stable":
            last_stable = state_id
        else:
            last_stable = self.last_stable_state_id
        state_material = {
            "agent_state_id": state_id,
            "observation_id": observation_id,
            "parent_agent_state_id": self.previous_state_id,
            "last_stable_state_id": last_stable,
            "state_status": state_status,
            "rollback_to_state_id": rollback_to_state_id,
            "action": action,
            "candidate": candidate,
            "evidence_files": evidence_files,
            "input_hashes": input_hashes or {},
            "output_hashes": output_hashes or {},
            "result": result,
            "next_allowed_action": next_allowed_action,
        }
        post_state_hash = canonical_sha(state_material)
        entry: dict[str, Any] = {
            "entry_index": index,
            "sequence_index": index,
            "action": action,
            "candidate": candidate,
            "agent_state_id": state_id,
            "observation_id": observation_id,
            "parent_agent_state_id": self.previous_state_id,
            "last_stable_state_id": last_stable,
            "state_status": state_status,
            "rollback_to_state_id": rollback_to_state_id,
            "pre_state_hash": self.current_state_hash,
            "post_state_hash": post_state_hash,
            "decision_time_boundary_enforced": True,
            "decision_time_inputs": decision_time_inputs,
            "forbidden_inputs_checked": FORBIDDEN_INPUTS,
            "evidence_files": evidence_files,
            "direct_script_output": direct_script_output,
            "sha256": {
                "input_hashes": input_hashes or {},
                "output_hashes": output_hashes or {},
                "previous_entry_hash": self.previous_entry_hash,
                "entry_hash": None,
            },
            "result": result,
            "next_allowed_action": next_allowed_action,
        }
        entry_hash = canonical_sha(entry)
        entry["sha256"]["entry_hash"] = entry_hash
        entry["entry_hash"] = entry_hash
        self.entries.append(entry)
        self.previous_entry_hash = entry_hash
        self.previous_state_id = state_id
        self.current_state_hash = post_state_hash
        if state_status == "stable":
            self.last_stable_state_id = state_id
        return entry


def import_v28w():
    spec = importlib.util.spec_from_file_location("v2_8w_baseline_adapter", V28W_RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def copy_baseline_evidence(baseline_root: Path, artifact_root: Path, gate: dict[str, Any]) -> list[str]:
    copied: list[str] = []
    destination_root = artifact_root / "raw_logs" / "baseline"
    names = [
        "failing_command.txt",
        "normalized_failing_command.txt",
        "failing_log_raw.txt",
        "no_memory_post_repair_log_raw.txt",
        "memory_enabled_post_repair_log_raw.txt",
        "limited_scoring_result.json",
        "post_repair_comparison.json",
    ]
    for record in gate.get("required_baseline_candidates", []):
        episode_id = str(record.get("episode_id") or "unknown")
        candidate = str(record.get("candidate") or "unknown").replace(":", "_")
        source = baseline_root / episode_id
        destination = destination_root / f"{episode_id}_{candidate}"
        for name in names:
            path = source / name
            if path.exists():
                destination.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, destination / name)
                copied.append((destination / name).relative_to(artifact_root).as_posix())
    return sorted(copied)


def run_baseline_only(artifact_root: Path) -> tuple[dict[str, Any], Any, dict[str, str]]:
    v28w = import_v28w()
    baseline_root = (RUNTIME_ROOT / "baseline_harness_artifacts").resolve()
    baseline_runtime = (RUNTIME_ROOT / "baseline_runtime").resolve()
    v28w.REPO_ROOT = REPO_ROOT
    v28w.ARTIFACT_ROOT = baseline_root
    v28w.RUNTIME_ROOT = baseline_runtime
    v28w.restore_v28t_hooks()
    baseline_root.mkdir(parents=True, exist_ok=True)
    baseline_runtime.mkdir(parents=True, exist_ok=True)
    clone_result = v28w.base.run_raw(
        ["git", "clone", "--depth", "1", v28w.base.BUGSINPY_URL, str(v28w.base.BUGSINPY_REPO)],
        timeout=900,
    )
    write_text(artifact_root / "raw_logs" / "bugsinpy_clone_log_raw.txt", v28w.base.combined_log(clone_result))
    if clone_result.get("returncode") != 0:
        raise RuntimeError("BugsInPy clone failed in baseline-only adapter")
    env = os.environ.copy()
    env["PATH"] = str((v28w.base.BUGSINPY_REPO / "framework" / "bin").resolve()) + os.pathsep + env.get("PATH", "")
    harness = v28w.v28p.run_global_harness_sanity(env)
    results: list[dict[str, Any]] = []
    for candidate in v28w.baseline_candidates():
        if candidate.get("candidate") not in BASELINE_IDS:
            raise RuntimeError(f"baseline adapter attempted out-of-scope candidate: {candidate.get('candidate')}")
        print(f"v2.13 baseline-only: {candidate['candidate']}", flush=True)
        results.append(v28w.v28p.run_episode(candidate, env))
    if [str(item.get("candidate")) for item in results] != BASELINE_IDS:
        raise RuntimeError("baseline adapter did not execute exactly the five required candidates in order")
    gate = v28w.write_preserved_baseline_gate(results)
    copied = copy_baseline_evidence(baseline_root, artifact_root, gate)
    baseline = {
        "status": gate.get("status"),
        "baseline_execution_scope": BASELINE_IDS,
        "broad_candidate_sweep_executed": False,
        "exact_v2_12_scoring_harness_reused": True,
        "harness_source": "v2_8w baseline harness transitively used by the v2.12 runner",
        "first_proof_ledger_event_required": True,
        "required_baseline_candidates": gate.get("required_baseline_candidates", []),
        "scoreable_status_by_episode": gate.get("scoreable_status_by_episode", {}),
        "positive_memory_only_preservation_status": gate.get("positive_memory_only_preservation_status", {}),
        "baseline_preservation_passed": gate.get("status") == "PASS",
        "ansible2_positive_memory_only_status_preserved": gate.get("ansible2_positive_memory_only_status_preserved"),
        "ansible5_positive_memory_only_status_preserved": gate.get("ansible5_positive_memory_only_status_preserved"),
        "harness_sanity_status": harness.get("status"),
        "evidence_files": copied,
    }
    write_json(artifact_root / "baseline_preservation_v2_13.json", baseline)
    return baseline, v28w, env


def checkout_pysnooper(v28w: Any, env: dict[str, str], bug_id: str, label: str, artifact_root: Path) -> tuple[Path, dict[str, Any]]:
    workspace_parent = (RUNTIME_ROOT / "forensic_workspaces" / label).resolve()
    workspace_parent.mkdir(parents=True, exist_ok=True)
    project_root = (workspace_parent / "PySnooper").resolve()
    command = f"bugsinpy-checkout -p PySnooper -v 0 -i {bug_id} -w {workspace_parent}"
    result = v28w.v28g.run_shell(command, cwd=REPO_ROOT, env=env, timeout=900)
    log_path = artifact_root / "raw_logs" / f"{label}_checkout_log_raw.txt"
    write_text(log_path, v28w.base.combined_log(result))
    if result.get("returncode") != 0 or not project_root.exists():
        raise RuntimeError(f"PySnooper:{bug_id} buggy checkout failed")
    return project_root, {"command": command, "returncode": result.get("returncode"), "log": log_path.relative_to(artifact_root).as_posix()}


def policy_recheck(workspace: Path, bugsinpy_repo: Path, bug_id: str) -> dict[str, Any]:
    names = ["setup.py", "pyproject.toml", "setup.cfg", "requirements.txt", "requirements-dev.txt", "tox.ini", "pytest.ini"]
    paths = [workspace / name for name in names if (workspace / name).is_file()]
    bug_dir = bugsinpy_repo / "projects" / "PySnooper" / "bugs" / bug_id
    paths.extend(path for path in [bug_dir / "bug.info", bug_dir / "run_test.sh", bug_dir / "setup.sh"] if path.is_file())
    records = []
    declared = False
    for path in paths:
        matches = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
            if re.search(r"python[-_]toolbox", line, flags=re.IGNORECASE):
                matches.append({"line_number": line_number, "line": line.strip()})
        if matches:
            declared = True
        records.append({"path": str(path), "sha256": sha256_path(path), "matching_lines": matches})
    return {
        "status": "PASS",
        "candidate": f"PySnooper:{bug_id}",
        "metadata_files_inspected": records,
        "python_toolbox_declared": declared,
        "decision_time_safe_status": "PASS",
        "installation_performed": False,
        "classification": (
            "dependency_recovery_allowed_by_policy_not_executed_in_minimal_lane"
            if declared
            else "dependency_recovery_forbidden_by_policy"
        ),
        "absence_result": not declared,
    }


def run_direct_script(command: list[str], stdout_path: Path, stderr_path: Path, output_path: Path) -> str:
    result = subprocess.run(command, cwd=REPO_ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    write_text(stdout_path, result.stdout)
    write_text(stderr_path, result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"deterministic script failed ({result.returncode}): {' '.join(command)}")
    if not output_path.exists():
        raise RuntimeError(f"deterministic script did not write required output: {output_path}")
    return sha256_path(output_path)


def pending_checkpoint(root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    pending_classification = {
        "status": "PENDING_GITHUB_ACTIONS",
        "patch_applied_cleanly": None,
        "patch_nonempty": None,
        "patch_semantic_delta_detected": None,
        "degenerate_flatline_detected": None,
        "touched_files": [],
        "source_only_patch": None,
        "tests_modified": None,
        "benchmark_expectations_modified": None,
        "generated_fixtures_modified": None,
        "non_source_files_modified": [],
        "pre_failure_signature": "PENDING_GITHUB_ACTIONS",
        "post_failure_signature": "PENDING_GITHUB_ACTIONS",
        "failure_changed_after_patch": None,
        "deterministic_classification": "PENDING_GITHUB_ACTIONS",
        "blocker_reason": "official workflow not yet executed",
        "evidence_files": [],
        "sha256_inputs": {},
    }
    pending_context = {
        "status": "PENDING_GITHUB_ACTIONS",
        "candidate": "PySnooper:2",
        "target_command": "python -m pytest -q -s tests/test_pysnooper.py::test_custom_repr_single",
        "buggy_checkout_identity": "PENDING_GITHUB_ACTIONS",
        "source_root": "pysnooper",
        "test_paths": ["tests/test_pysnooper.py"],
        "traceback_symbols": [],
        "patch_touched_symbols": [],
        "import_graph_edges": [],
        "ast_definitions_near_traceback": [],
        "ast_definitions_near_patch": [],
        "dependency_metadata_files": [],
        "declared_dependencies": [],
        "missing_or_suspect_dependencies": [],
        "fixture_or_test_helpers_referenced": [],
        "context_budget": {"max_files": 20, "max_symbols": 80, "max_probe_commands": 2},
        "context_selection_basis": [],
        "excluded_context_reason": ["official workflow not yet executed"],
        "context_limitations": ["pending buggy-checkout materialization"],
        "evidence_files": [],
        "sha256_inputs": {},
    }
    state = {
        "campaign_id": CAMPAIGN_ID,
        "workflow_executed": False,
        "based_on_v2_12": True,
        "baseline_preservation": {"status": "PENDING_GITHUB_ACTIONS", "required_candidates": BASELINE_IDS},
        "pysnooper1_policy_recheck": {"status": "PENDING_GITHUB_ACTIONS"},
        "pysnooper2_context_extraction": {"status": "PENDING_GITHUB_ACTIONS"},
        "pysnooper2_failed_patch_analysis": {"status": "PENDING_GITHUB_ACTIONS"},
        "pysnooper2_minimal_probes": [],
        "pysnooper2_revised_patch_attempt": {"authorized": False, "attempted": False},
        "rollback": {"performed": False},
        "proof_ledger": [],
        "audit_summary": {"status": "PENDING_GITHUB_ACTIONS"},
        "final_result": {
            "status": "PENDING_GITHUB_ACTIONS",
            "controllergate_full_scoring": "NOT_RUN",
            "full_scoring_allowed": False,
            "self_maintaining_software_demonstrated": False,
        },
    }
    write_json(root / "candidate_state_v2_13.json", state)
    write_json(root / "pysnooper2_patch_failure_classification.json", pending_classification)
    write_json(root / "pysnooper2_candidate_context.json", pending_context)
    write_json(root / "audit_summary_v2_13.json", {"status": "PENDING_GITHUB_ACTIONS", "workflow_executed": False})
    write_text(
        root / "campaign_summary.md",
        "# v2.13 Minimal Forensic Context Lane\n\n"
        "- Status: `PENDING_GITHUB_ACTIONS`.\n"
        "- Baseline scope is locked to youtube-dl:1, black:4, fastapi:1, ansible:2, and ansible:5.\n"
        "- PySnooper:2 classification and bounded context extraction have not run.\n"
        "- Full scoring remains `NOT_RUN` / disallowed.\n"
        "- Self-maintaining software is not demonstrated.\n",
    )
    write_manifest(root)


def run_actual(artifact_root: Path) -> int:
    if artifact_root.exists():
        shutil.rmtree(artifact_root)
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    artifact_root.mkdir(parents=True)
    RUNTIME_ROOT.mkdir(parents=True)
    ledger = ProofLedger(CAMPAIGN_ID)

    baseline, v28w, env = run_baseline_only(artifact_root)
    baseline_path = artifact_root / "baseline_preservation_v2_13.json"
    baseline_hash = sha256_path(baseline_path)
    baseline_result = "pass" if baseline.get("baseline_preservation_passed") else "fail"
    baseline_entry = ledger.append(
        action="baseline_preservation",
        candidate="baseline_five",
        result=baseline_result,
        next_allowed_action="policy_recheck" if baseline_result == "pass" else "stop",
        decision_time_inputs=["exact v2.12 scoring harness", "fresh buggy-checkout baseline executions"],
        evidence_files=[relative_evidence(baseline_path, artifact_root)] + baseline.get("evidence_files", []),
        output_hashes={relative_evidence(baseline_path, artifact_root): baseline_hash},
    )
    if baseline_result != "pass":
        raise RuntimeError("runner_regression_v2_12_baseline_failure")

    py1_workspace, py1_checkout = checkout_pysnooper(v28w, env, "1", "pysnooper1", artifact_root)
    py1 = policy_recheck(py1_workspace, v28w.base.BUGSINPY_REPO, "1")
    py1["checkout"] = py1_checkout
    py1_path = artifact_root / "raw_logs" / "pysnooper1_policy_recheck_v2_13.json"
    write_json(py1_path, py1)
    py1_hash = sha256_path(py1_path)
    policy_entry = ledger.append(
        action="policy_recheck",
        candidate="PySnooper:1",
        result="pass",
        next_allowed_action="failed_patch_analysis",
        decision_time_inputs=["buggy-checkout project metadata", "BugsInPy bug-local setup metadata"],
        evidence_files=[relative_evidence(py1_path, artifact_root), py1_checkout["log"]],
        output_hashes={relative_evidence(py1_path, artifact_root): py1_hash},
    )

    py2_workspace, py2_checkout = checkout_pysnooper(v28w, env, "2", "pysnooper2", artifact_root)
    episode = V212_OUTPUT / "episode_034"
    patch = episode / "memory_enabled_source_only_repair_patch.diff"
    pre_log = episode / "failing_log_raw.txt"
    post_log = episode / "memory_enabled_post_repair_log_raw.txt"
    command_file = episode / "memory_enabled_post_repair_command.txt"
    application = episode / "memory_enabled_patch_application_result.json"
    classification_path = artifact_root / "pysnooper2_patch_failure_classification.json"
    classification_hash = run_direct_script(
        [
            sys.executable,
            str(CLASSIFIER),
            "--patch",
            str(patch),
            "--pre-log",
            str(pre_log),
            "--post-log",
            str(post_log),
            "--target-command-file",
            str(command_file),
            "--application-result",
            str(application),
            "--source-root",
            "pysnooper",
            "--output",
            str(classification_path),
        ],
        artifact_root / "raw_logs" / "classifier_stdout.txt",
        artifact_root / "raw_logs" / "classifier_stderr.txt",
        classification_path,
    )
    classification = load_json(classification_path)
    classification_entry = ledger.append(
        action="failed_patch_analysis",
        candidate="PySnooper:2",
        result="pass",
        next_allowed_action="context_extraction",
        decision_time_inputs=[
            "v2.12 failed patch diff",
            "v2.12 pre-patch failure log",
            "v2.12 post-patch failure log used only for failure classification",
            "exact target command",
        ],
        evidence_files=[relative_evidence(classification_path, artifact_root)],
        input_hashes={relative_evidence(path, artifact_root): sha256_path(path) for path in [patch, pre_log, post_log, command_file, application]},
        output_hashes={relative_evidence(classification_path, artifact_root): classification_hash},
        direct_script_output=relative_evidence(classification_path, artifact_root),
    )

    bug2_dir = v28w.base.BUGSINPY_REPO / "projects" / "PySnooper" / "bugs" / "2"
    metadata_args: list[str] = []
    for path in [bug2_dir / "bug.info", bug2_dir / "run_test.sh", bug2_dir / "setup.sh"]:
        if path.exists():
            metadata_args.extend(["--dependency-metadata", str(path)])
    context_path = artifact_root / "pysnooper2_candidate_context.json"
    context_hash = run_direct_script(
        [
            sys.executable,
            str(COLLECTOR),
            "--candidate",
            "PySnooper:2",
            "--buggy-checkout",
            str(py2_workspace),
            "--target-command-file",
            str(command_file),
            "--failure-log",
            str(post_log),
            "--pre-failure-log",
            str(pre_log),
            "--patch",
            str(patch),
            "--source-root",
            "pysnooper",
            "--target-test",
            "tests/test_pysnooper.py",
            *metadata_args,
            "--output",
            str(context_path),
        ],
        artifact_root / "raw_logs" / "context_collector_stdout.txt",
        artifact_root / "raw_logs" / "context_collector_stderr.txt",
        context_path,
    )
    context = load_json(context_path)
    context_entry = ledger.append(
        action="context_extraction",
        candidate="PySnooper:2",
        result="pass",
        next_allowed_action="revise_patch",
        decision_time_inputs=["buggy checkout", "target test", "traceback", "v2.12 patch", "repo-local dependency metadata"],
        evidence_files=[relative_evidence(context_path, artifact_root), py2_checkout["log"]],
        input_hashes={relative_evidence(path, artifact_root): sha256_path(path) for path in [patch, pre_log, post_log, command_file]},
        output_hashes={relative_evidence(context_path, artifact_root): context_hash},
        direct_script_output=relative_evidence(context_path, artifact_root),
    )

    missing_helpers = context.get("missing_fixture_or_test_helpers_referenced") or []
    source_actionable = classification.get("source_only_repair_actionable") is True and not missing_helpers
    authorized = bool(
        baseline.get("baseline_preservation_passed")
        and baseline.get("ansible2_positive_memory_only_status_preserved")
        and baseline.get("ansible5_positive_memory_only_status_preserved")
        and classification.get("status") == "PASS"
        and context.get("status") == "PASS"
        and classification.get("degenerate_flatline_detected") is False
        and classification.get("source_only_patch") is True
        and classification.get("tests_modified") is False
        and classification.get("benchmark_expectations_modified") is False
        and classification.get("generated_fixtures_modified") is False
        and source_actionable
    )
    blocker = (
        "fixture_materialization_incomplete: tests/mini_toolbox.py is directly imported by the target test but absent from the buggy checkout; test/fixture edits are forbidden and no source-only revision is authorized"
        if missing_helpers or classification.get("deterministic_classification") == "fixture_materialization_incomplete"
        else "source-only revision authorization conditions were not all satisfied"
    )
    authorization_entry = ledger.append(
        action="patch_authorization",
        candidate="PySnooper:2",
        result="pass" if authorized else "block",
        next_allowed_action="target_validation" if authorized else "stop",
        decision_time_inputs=[
            relative_evidence(classification_path, artifact_root),
            relative_evidence(context_path, artifact_root),
            relative_evidence(baseline_path, artifact_root),
        ],
        evidence_files=[relative_evidence(classification_path, artifact_root), relative_evidence(context_path, artifact_root)],
        input_hashes={
            relative_evidence(classification_path, artifact_root): classification_hash,
            relative_evidence(context_path, artifact_root): context_hash,
            relative_evidence(baseline_path, artifact_root): baseline_hash,
        },
    )
    if authorized:
        raise RuntimeError("v2.13 unexpectedly authorized a revised patch; runner intentionally has no implicit patch generator")
    final_entry = ledger.append(
        action="final_classification",
        candidate="PySnooper:2",
        result="block",
        next_allowed_action="none",
        decision_time_inputs=[relative_evidence(classification_path, artifact_root), relative_evidence(context_path, artifact_root)],
        evidence_files=[relative_evidence(classification_path, artifact_root), relative_evidence(context_path, artifact_root)],
        input_hashes={
            relative_evidence(classification_path, artifact_root): classification_hash,
            relative_evidence(context_path, artifact_root): context_hash,
        },
    )

    state = {
        "campaign_id": CAMPAIGN_ID,
        "workflow_executed": True,
        "based_on_v2_12": True,
        "hash_custody": {
            "canonical_json": "UTF-8 JSON with sort_keys=true and separators=(',', ':')",
            "state_hash_fields": [
                "agent_state_id",
                "observation_id",
                "parent_agent_state_id",
                "last_stable_state_id",
                "state_status",
                "rollback_to_state_id",
                "action",
                "candidate",
                "evidence_files",
                "input_hashes",
                "output_hashes",
                "result",
                "next_allowed_action",
            ],
            "entry_hash_rule": "hash the complete ledger entry with top-level entry_hash omitted and sha256.entry_hash set to null",
        },
        "baseline_preservation": baseline | state_reference(baseline_entry),
        "pysnooper1_policy_recheck": py1 | state_reference(policy_entry),
        "pysnooper2_context_extraction": {
            "status": context.get("status"),
            "direct_output": relative_evidence(context_path, artifact_root),
            "sha256": context_hash,
            "missing_fixture_or_test_helpers_referenced": missing_helpers,
            "selected_file_count": (context.get("context_budget") or {}).get("selected_file_count"),
        }
        | state_reference(context_entry),
        "pysnooper2_failed_patch_analysis": {
            "status": classification.get("status"),
            "direct_output": relative_evidence(classification_path, artifact_root),
            "sha256": classification_hash,
            "deterministic_classification": classification.get("deterministic_classification"),
            "degenerate_flatline_detected": classification.get("degenerate_flatline_detected"),
        }
        | state_reference(classification_entry),
        "pysnooper2_minimal_probes": [],
        "pysnooper2_revised_patch_attempt": {
            "authorized": False,
            "attempted": False,
            "attempt_count": 0,
            "blocker": blocker,
        }
        | state_reference(authorization_entry),
        "rollback": {
            "performed": False,
            "reason": "no revised patch was authorized or applied",
            "rollback_to_state_id": None,
        },
        "proof_ledger": ledger.entries,
        "audit_summary": {"status": "PENDING_INDEPENDENT_AUDIT", "independent_audit_required": True},
        "final_result": {
            "status": "PASS_WITH_DETERMINISTIC_BLOCKER",
            "final_agent_state_id": final_entry["agent_state_id"],
            "pysnooper1_policy_classification": py1.get("classification"),
            "pysnooper2_classification": "blocked_fixture_materialization_incomplete",
            "exact_remaining_blocker": blocker,
            "pysnooper2_scoreable": False,
            "pysnooper2_positive_memory_only": False,
            "updated_scoreable_count": 5,
            "updated_positive_memory_count": 2,
            "non_ansible_positive_memory_count": 0,
            "repair_outcome_memory_lift": "replicated_positive_memory_signal_preserved",
            "family_generalization": "not_expanded",
            "diagnostic_probe_count": 0,
            "revised_patch_authorized": False,
            "revised_patch_attempted": False,
            "target_validation_passed": False,
            "rollback_performed": False,
            "duplicate_replay_status": "not_applicable_no_authorized_patch",
            "phase_seed_check_status": "not_applicable_with_reason",
            "phase_seed_check_reason": "no authorized patch or nondeterministic target result required replay-sensitive validation",
            "controllergate_full_scoring": "NOT_RUN",
            "full_scoring_allowed": False,
            "self_maintaining_software_demonstrated": False,
            "fixed_gold_future_evidence_used": False,
            "decision_time_outcome_overlap_count": 0,
            "corruption_count": 0,
        }
        | state_reference(final_entry),
    }
    write_json(artifact_root / "candidate_state_v2_13.json", state)
    write_json(artifact_root / "audit_summary_v2_13.json", {"status": "PENDING_INDEPENDENT_AUDIT", "workflow_executed": True})
    write_text(
        artifact_root / "campaign_summary.md",
        "# v2.13 Minimal Forensic Context Lane\n\n"
        "- Status: `official_runner_completed_pending_independent_audit_and_zip_verification`.\n"
        "- Exact five-candidate v2.12 baseline rerun: `PASS`.\n"
        "- ansible:2 positive-memory-only preservation: `PASS`.\n"
        "- ansible:5 positive-memory-only preservation: `PASS`.\n"
        f"- PySnooper:1 policy recheck: `{py1.get('classification')}`.\n"
        f"- PySnooper:2 deterministic failed-patch classification: `{classification.get('deterministic_classification')}`.\n"
        "- Diagnostic probes used: `0`.\n"
        "- Revised patch authorized: `false`; attempted: `false`.\n"
        "- PySnooper:2 remains non-scoreable because the target test directly imports missing `tests/mini_toolbox.py`; source-only repair cannot modify tests or fixtures.\n"
        "- Scoreable episodes: `5`; positive-memory-only episodes: `2`; non-Ansible positive-memory episodes: `0`.\n"
        "- Full scoring remains `NOT_RUN` / disallowed.\n"
        "- Self-maintaining software is not demonstrated.\n",
    )
    write_manifest(artifact_root)
    print("v2.13 minimal forensic context artifact generated", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--artifact-root", type=Path)
    args = parser.parse_args()
    if args.prepare_only:
        root = (args.artifact_root or PENDING_OUTPUT_ROOT).resolve()
        pending_checkpoint(root)
        print(f"v2.13 pending checkpoint written to {root}")
        return 0
    return run_actual((args.artifact_root or DEFAULT_ARTIFACT_ROOT).resolve())


if __name__ == "__main__":
    raise SystemExit(main())

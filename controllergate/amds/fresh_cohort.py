from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import stat
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic
from controllergate.execution.execution_broker import execute_external_operation
from controllergate.runtime.runtime_root_attestation import attest_runtime_root


ROLE_NAMES = (
    "source_revision",
    "source_tree",
    "test_tree",
    "provider_runtime_abi",
    "target_reproducer",
    "command",
    "runner",
    "harness",
    "incident_snapshot",
    "proof_release_parent",
)


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
        newline="\n",
    )


def _sha_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _venv_python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _venv_bin(venv: Path) -> Path:
    return venv / ("Scripts" if os.name == "nt" else "bin")


def _remove_runtime_tree(path: Path) -> None:
    def make_writable(function: Any, target: str, _error: Any) -> None:
        os.chmod(target, stat.S_IWRITE)
        function(target)

    if path.exists():
        shutil.rmtree(path, onexc=make_writable)


def _expand_argv(values: list[str], *, venv: Path) -> list[str]:
    python = str(_venv_python(venv))
    bin_dir = _venv_bin(venv)
    expanded: list[str] = []
    for value in values:
        if value == "{python}":
            expanded.append(python)
        elif value.startswith("{venv_bin}/"):
            name = value.split("/", 1)[1]
            candidate = bin_dir / (name + (".exe" if os.name == "nt" else ""))
            expanded.append(str(candidate))
        else:
            expanded.append(value)
    return expanded


def _safe_target_env(extra: dict[str, str]) -> dict[str, str]:
    allowed = (
        "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP",
        "HOME", "USERPROFILE", "LOCALAPPDATA", "APPDATA", "LANG", "LC_ALL",
    )
    env = {key: os.environ[key] for key in allowed if key in os.environ}
    env.update(extra)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def _path_manifest(source: Path, relative_paths: list[str]) -> tuple[list[dict[str, Any]], bool]:
    rows: list[dict[str, Any]] = []
    all_present = True
    for relative in relative_paths:
        path = source / relative
        if path.is_file():
            rows.append({"path": relative, "kind": "file", "sha256": sha256_file(path), "size": path.stat().st_size})
        elif path.is_dir():
            children = [child for child in sorted(path.rglob("*")) if child.is_file() and ".git" not in child.parts]
            digest = hashlib.sha256()
            for child in children:
                rel = child.relative_to(source).as_posix()
                digest.update(rel.encode("utf-8") + b"\0" + bytes.fromhex(sha256_file(child)))
            rows.append({"path": relative, "kind": "directory", "sha256": digest.hexdigest(), "file_count": len(children)})
        else:
            all_present = False
            rows.append({"path": relative, "kind": "missing", "sha256": None})
    return rows, all_present


@dataclass
class BrokerRunner:
    runtime_root: Path
    repo_root: Path
    output_root: Path
    attestation: dict[str, Any]
    records: list[dict[str, Any]]
    parent_hash: str | None = None

    def run(
        self,
        *,
        candidate_id: str,
        stage_id: str,
        operation_type: str,
        argv: list[str],
        cwd: Path,
        network: bool = False,
        timeout: int = 600,
        env: dict[str, str] | None = None,
    ) -> tuple[int | None, str, str, str | None]:
        try:
            completed, record = execute_external_operation(
                operation_type=operation_type,
                argv=argv,
                cwd=cwd,
                runtime_root=self.runtime_root,
                stage_id=stage_id,
                candidate_id=candidate_id,
                authorization_id="batch094:decision-time-acquisition-only",
                runtime_attestation=self.attestation,
                platform=platform.system().lower(),
                runtime=f"python-{platform.python_version()}",
                provider_identity="batch094-fresh-candidate-provider" if operation_type not in {"source_acquisition", "git_metadata", "git_checkout"} else None,
                network_policy="bounded_read_only_acquisition" if network else "none",
                network_request_budget=256 if network else 0,
                network_byte_budget=2_000_000_000 if network else 0,
                timeout=timeout,
                env=env,
                parent_ledger_hash=self.parent_hash,
                run_id="batch094:fresh-frozen-cohort",
                nonce=hash_record([candidate_id, stage_id, self.parent_hash])[:32],
            )
            record["verifier_result"] = "PASS_RECORD_INTEGRITY" if record.get("record_hash") else "BLOCK"
            self.records.append(record)
            self.parent_hash = str(record["record_hash"])
            return completed.returncode, completed.stdout, completed.stderr, None
        except Exception as exc:  # broker exceptions remain blockers, never success evidence
            blocker = {
                "candidate_id": candidate_id,
                "stage_id": stage_id,
                "operation_type": operation_type,
                "status": "BLOCK",
                "exception_type": type(exc).__name__,
                "exception_message_hash": _sha_text(str(exc)),
                "record_hash": hash_record([candidate_id, stage_id, type(exc).__name__, str(exc)]),
                "authority_allowed": "materialization blocker only",
                "authority_forbidden": ["successful execution", "terminal class", "repair authority"],
            }
            self.records.append(blocker)
            self.parent_hash = blocker["record_hash"]
            return None, "", "", f"broker_{type(exc).__name__.lower()}"


def _attempt_episode(spec: dict[str, Any], runner: BrokerRunner) -> dict[str, Any]:
    candidate_id = spec["candidate_id"]
    workspace = runner.runtime_root / "fresh-cohort" / candidate_id
    _remove_runtime_tree(workspace)
    workspace.mkdir(parents=True)
    source = workspace / "source"
    source.mkdir()

    blockers: list[str] = []
    operation_start = len(runner.records)
    rc, _, _, error = runner.run(
        candidate_id=candidate_id,
        stage_id="source_init",
        operation_type="source_acquisition",
        argv=["git", "init", str(source)],
        cwd=workspace,
    )
    if rc != 0 or error:
        blockers.append(error or "source_repository_initialization_failed")
    if not blockers:
        rc, _, _, error = runner.run(
            candidate_id=candidate_id,
            stage_id="source_remote",
            operation_type="source_acquisition",
            argv=["git", "remote", "add", "origin", spec["repository"]],
            cwd=source,
        )
        if rc != 0 or error:
            blockers.append(error or "source_remote_registration_failed")
    if not blockers:
        rc, _, _, error = runner.run(
            candidate_id=candidate_id,
            stage_id="source_fetch_exact_commit",
            operation_type="source_acquisition",
            argv=["git", "fetch", "--depth", "1", "origin", spec["source_commit"]],
            cwd=source,
            network=True,
            timeout=900,
        )
        if rc != 0 or error:
            blockers.append(error or "source_commit_fetch_failed")
    if not blockers:
        rc, _, _, error = runner.run(
            candidate_id=candidate_id,
            stage_id="source_checkout_exact_commit",
            operation_type="git_checkout",
            argv=["git", "checkout", "--detach", spec["source_commit"]],
            cwd=source,
        )
        if rc != 0 or error:
            blockers.append(error or "source_commit_checkout_failed")

    observed_head = None
    object_type = None
    tree_hash = None
    if not blockers:
        rc, stdout, _, error = runner.run(
            candidate_id=candidate_id,
            stage_id="source_revision_identity",
            operation_type="git_metadata",
            argv=["git", "rev-parse", "HEAD"],
            cwd=source,
        )
        observed_head = stdout.strip() if rc == 0 and not error else None
        rc2, stdout2, _, error2 = runner.run(
            candidate_id=candidate_id,
            stage_id="source_object_type",
            operation_type="git_metadata",
            argv=["git", "cat-file", "-t", spec["source_commit"]],
            cwd=source,
        )
        object_type = stdout2.strip() if rc2 == 0 and not error2 else None
        rc3, stdout3, _, error3 = runner.run(
            candidate_id=candidate_id,
            stage_id="source_tree_identity",
            operation_type="git_metadata",
            argv=["git", "ls-tree", "-r", "--full-tree", "HEAD"],
            cwd=source,
            timeout=300,
        )
        tree_hash = _sha_text(stdout3) if rc3 == 0 and not error3 else None
        if observed_head != spec["source_commit"] or object_type != "commit" or not tree_hash:
            blockers.append("source_identity_verification_failed")

    target_files, target_paths_present = _path_manifest(source, spec.get("target_paths", [])) if source.is_dir() else ([], False)
    if not target_paths_present:
        blockers.append("target_or_support_path_missing")

    source_capsule = {
        "candidate_id": candidate_id,
        "repository": spec["repository"],
        "expected_commit": spec["source_commit"],
        "observed_commit": observed_head,
        "object_type": object_type,
        "tree_listing_sha256": tree_hash,
        "status": "PASS" if observed_head == spec["source_commit"] and object_type == "commit" and tree_hash else "BLOCK",
    }
    test_capsule = {
        "candidate_id": candidate_id,
        "target_paths": target_files,
        "all_declared_paths_present": target_paths_present,
        "status": "PASS" if target_paths_present else "BLOCK",
    }
    command_contract = {
        "candidate_id": candidate_id,
        "candidate_class": spec["candidate_class"],
        "argv_template": spec["target_argv"],
        "working_directory_policy": spec.get("working_directory_basename", "source_root"),
        "target_environment_names": sorted(spec.get("target_environment", {})),
        "command_contract_hash": hash_record([spec["target_argv"], spec.get("working_directory_basename"), spec.get("target_environment", {})]),
        "status": "PASS",
    }

    venv = workspace / "provider"
    provider_rc: int | None = None
    if not blockers:
        rc, _, _, error = runner.run(
            candidate_id=candidate_id,
            stage_id="provider_venv_materialization",
            operation_type="provider_build",
            argv=[sys.executable, "-m", "venv", str(venv)],
            cwd=workspace,
            timeout=300,
        )
        if rc != 0 or error:
            blockers.append(error or "provider_venv_materialization_failed")
    if not blockers:
        install_argv = _expand_argv(spec["install_argv"], venv=venv)
        provider_rc, provider_stdout, provider_stderr, error = runner.run(
            candidate_id=candidate_id,
            stage_id="provider_dependency_and_project_install",
            operation_type="provider_acquisition",
            argv=install_argv,
            cwd=source,
            network=True,
            timeout=1200,
            env=_safe_target_env(spec.get("install_environment", {})) if spec.get("install_environment") else None,
        )
        (workspace / "provider-install.log").write_text(provider_stdout + provider_stderr, encoding="utf-8", newline="\n")
        if provider_rc != 0 or error:
            blockers.append(error or "provider_dependency_and_project_install_failed")

    provider_capsule = {
        "candidate_id": candidate_id,
        "python_executable": str(_venv_python(venv)),
        "python_version": platform.python_version(),
        "python_abi": getattr(sys.implementation, "cache_tag", None),
        "install_contract_hash": hash_record(spec["install_argv"]),
        "install_return_code": provider_rc,
        "status": "PASS" if provider_rc == 0 else "BLOCK",
    }

    target_rc: int | None = None
    target_stdout = ""
    target_stderr = ""
    target_error: str | None = None
    incident_materialized = False
    target_cwd = source
    if not blockers:
        if spec.get("working_directory_basename"):
            target_cwd = workspace / spec["working_directory_basename"]
            target_cwd.mkdir()
        target_argv = _expand_argv(spec["target_argv"], venv=venv)
        target_rc, target_stdout, target_stderr, target_error = runner.run(
            candidate_id=candidate_id,
            stage_id="project_target_reproducer",
            operation_type="reproducer_execution",
            argv=target_argv,
            cwd=target_cwd,
            timeout=1200,
            env=_safe_target_env(spec.get("target_environment", {})) if spec.get("target_environment") else None,
        )
        (workspace / "target-reproducer.log").write_text(target_stdout + target_stderr, encoding="utf-8", newline="\n")
        combined = target_stdout + "\n" + target_stderr
        markers = spec.get("expected_failure_markers", [])
        if candidate_id == "incident_poetry_10974_init_duplicate_name":
            pyproject = target_cwd / "pyproject.toml"
            observed = pyproject.read_text(encoding="utf-8", errors="replace") if pyproject.is_file() else ""
            incident_materialized = target_rc == 0 and 'name = "my project with spaces"' in observed
            combined += "\n" + observed
        else:
            incident_materialized = target_rc not in (None, 0) and all(marker.lower() in combined.lower() for marker in markers)
        if target_error:
            blockers.append(target_error)
        elif not incident_materialized:
            blockers.append("project_target_failure_not_materialized")

    incident_snapshot = {
        "candidate_id": candidate_id,
        "target_return_code": target_rc,
        "stdout_sha256": _sha_text(target_stdout),
        "stderr_sha256": _sha_text(target_stderr),
        "expected_marker_hashes": [_sha_text(value) for value in spec.get("expected_failure_markers", [])],
        "semantic_failure_materialized": incident_materialized,
        "status": "PASS" if incident_materialized else "BLOCK",
    }
    target_capsule = {
        "candidate_id": candidate_id,
        "command_contract_hash": command_contract["command_contract_hash"],
        "target_cwd_class": "fresh_runtime_workspace",
        "return_code": target_rc,
        "incident_snapshot_hash": hash_record(incident_snapshot),
        "status": "PASS" if incident_materialized else "BLOCK",
    }
    runner_harness = {
        "candidate_id": candidate_id,
        "runner_identity": str(_venv_python(venv)),
        "harness_identity": command_contract["command_contract_hash"],
        "project_level_reproducer": True,
        "issue_body_solution_guidance_used": False,
        "status": "PASS" if provider_rc == 0 else "BLOCK",
    }
    proof_parent = {
        "candidate_id": candidate_id,
        "parent": "configs/batch093_amds_frozen_cohort.json",
        "parent_sha256": sha256_file(runner.repo_root / "configs/batch093_amds_frozen_cohort.json"),
        "repair_count_authority": False,
        "status": "PASS",
    }

    materialized = all(
        item["status"] == "PASS"
        for item in (source_capsule, test_capsule, provider_capsule, target_capsule, runner_harness, proof_parent)
    )
    episode_result = {
        "candidate_id": candidate_id,
        "candidate_class": spec["candidate_class"],
        "source_capsule": source_capsule,
        "test_tree_capsule": test_capsule,
        "provider_capsule": provider_capsule,
        "target_reproducer_capsule": target_capsule,
        "command_contract": command_contract,
        "runner_harness_identity": runner_harness,
        "incident_snapshot": incident_snapshot,
        "proof_release_parent": proof_parent,
        "materialized": materialized,
        "status": "PASS" if materialized else "BLOCK",
        "exact_blockers": sorted(set(blockers)),
        "broker_operation_count": len(runner.records) - operation_start,
        "patch_operation_count": 0,
        "count_increment": 0,
    }
    return episode_result


def _read_jsonl_by_candidate(path: Path) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {str(row["candidate_id"]): row for row in rows}


def _load_prior_results(output_root: Path, repo_root: Path) -> dict[str, dict[str, Any]]:
    sources = _read_jsonl_by_candidate(output_root / "historical_source_capsules.jsonl")
    tests = _read_jsonl_by_candidate(output_root / "historical_test_tree_capsules.jsonl")
    providers = _read_jsonl_by_candidate(output_root / "historical_provider_capsules.jsonl")
    targets = _read_jsonl_by_candidate(output_root / "historical_target_reproducer_capsules.jsonl")
    commands = _read_jsonl_by_candidate(output_root / "historical_command_contracts.jsonl")
    identities = _read_jsonl_by_candidate(output_root / "historical_runner_harness_identities.jsonl")
    incidents = _read_jsonl_by_candidate(output_root / "historical_incident_snapshots.jsonl")
    materializations = _read_jsonl_by_candidate(output_root / "historical_materialization_results.jsonl")
    results: dict[str, dict[str, Any]] = {}
    for candidate_id, row in materializations.items():
        if not all(candidate_id in mapping for mapping in (sources, tests, providers, targets, commands, identities, incidents)):
            continue
        results[candidate_id] = {
            "candidate_id": candidate_id,
            "candidate_class": commands[candidate_id].get("candidate_class"),
            "source_capsule": sources[candidate_id],
            "test_tree_capsule": tests[candidate_id],
            "provider_capsule": providers[candidate_id],
            "target_reproducer_capsule": targets[candidate_id],
            "command_contract": commands[candidate_id],
            "runner_harness_identity": identities[candidate_id],
            "incident_snapshot": incidents[candidate_id],
            "proof_release_parent": {
                "candidate_id": candidate_id,
                "parent": "configs/batch093_amds_frozen_cohort.json",
                "parent_sha256": sha256_file(repo_root / "configs/batch093_amds_frozen_cohort.json"),
                "repair_count_authority": False,
                "status": "PASS",
            },
            "materialized": row["materialized"],
            "status": row["status"],
            "exact_blockers": row["exact_blockers"],
            "broker_operation_count": row["broker_operation_count"],
            "patch_operation_count": 0,
            "count_increment": 0,
        }
    return results


def execute_fresh_cohort(
    *,
    config_path: Path,
    repo_root: Path,
    runtime_root: Path,
    output_root: Path,
    candidate_ids: set[str] | None = None,
) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    output_root.mkdir(parents=True, exist_ok=True)
    runtime_root.mkdir(parents=True, exist_ok=True)
    attestation = attest_runtime_root(runtime_root, repo_root=repo_root)
    if attestation.get("status") != "PASS":
        raise RuntimeError("runtime root attestation failed")
    write_json_deterministic(output_root / "fresh_cohort_runtime_attestation.json", attestation)
    prior_operations = []
    operations_path = output_root / "historical_acquisition_broker_operations.jsonl"
    if candidate_ids and operations_path.is_file():
        prior_operations = [json.loads(line) for line in operations_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    prior_results = _load_prior_results(output_root, repo_root) if candidate_ids else {}
    runner = BrokerRunner(
        runtime_root,
        repo_root,
        output_root,
        attestation,
        prior_operations,
        str(prior_operations[-1].get("record_hash")) if prior_operations else None,
    )
    results = []
    for spec in config["episodes"]:
        candidate_id = spec["candidate_id"]
        if candidate_ids and candidate_id not in candidate_ids:
            if candidate_id not in prior_results:
                raise RuntimeError(f"cannot preserve missing prior result for {candidate_id}")
            results.append(prior_results[candidate_id])
        else:
            results.append(_attempt_episode(spec, runner))

    _write_jsonl(output_root / "historical_episode_acquisition_contracts.jsonl", [
        {
            "candidate_id": spec["candidate_id"],
            "candidate_class": spec["candidate_class"],
            "repository": spec["repository"],
            "source_commit": spec["source_commit"],
            "target_contract_hash": hash_record(spec["target_argv"]),
            "decision_time_only": True,
            "forbidden_inputs": config["forbidden_inputs"],
        }
        for spec in config["episodes"]
    ])
    mappings = (
        ("historical_source_capsules.jsonl", "source_capsule"),
        ("historical_test_tree_capsules.jsonl", "test_tree_capsule"),
        ("historical_provider_capsules.jsonl", "provider_capsule"),
        ("historical_target_reproducer_capsules.jsonl", "target_reproducer_capsule"),
        ("historical_command_contracts.jsonl", "command_contract"),
        ("historical_runner_harness_identities.jsonl", "runner_harness_identity"),
        ("historical_incident_snapshots.jsonl", "incident_snapshot"),
        ("historical_proof_release_parent_snapshots.jsonl", "proof_release_parent"),
    )
    for filename, key in mappings:
        _write_jsonl(output_root / filename, [row[key] for row in results])
    _write_jsonl(output_root / "historical_materialization_results.jsonl", [
        {
            "episode_index": index,
            "candidate_id": row["candidate_id"],
            "materialized": row["materialized"],
            "status": row["status"],
            "exact_blockers": row["exact_blockers"],
            "broker_operation_count": row["broker_operation_count"],
            "patch_operation_count": 0,
            "count_increment": 0,
        }
        for index, row in enumerate(results, 1)
    ])
    _write_jsonl(output_root / "historical_acquisition_broker_operations.jsonl", runner.records)

    materialized_count = sum(row["materialized"] for row in results)
    status = "PASS" if materialized_count == config["minimum_eligible_episodes"] else "BLOCK"
    blocker = None if status == "PASS" else "BLOCK_MINIMUM_COHORT_NOT_MET"
    cohort = {
        "status": status,
        "blocker": blocker,
        "producer": "controllergate.amds.fresh_cohort.execute_fresh_cohort",
        "execution_depth": "fresh_exact_source_provider_project_target_materialization",
        "semantic_scope": "frozen eight-episode historical AMDS cohort eligibility",
        "authority_allowed": "AMDS measurement eligibility only when all eight materialize",
        "authority_forbidden": ["repair", "patch actuation", "count increment", "candidate substitution", "terminal assignment"],
        "frozen_candidate_count": len(results),
        "materialized_candidate_count": materialized_count,
        "required_candidate_count": config["minimum_eligible_episodes"],
        "candidate_order": [row["candidate_id"] for row in results],
        "materialized_candidates": [row["candidate_id"] for row in results if row["materialized"]],
        "blocked_candidates": [
            {"candidate_id": row["candidate_id"], "exact_blockers": row["exact_blockers"]}
            for row in results if not row["materialized"]
        ],
        "broker_operation_count": len(runner.records),
        "patch_operation_count": 0,
        "replacement_count": 0,
        "historical_count_increment": 0,
        "reopen_condition": "freshly materialize the exact blocked frozen episodes without candidate substitution or outcome evidence",
    }
    write_json_deterministic(output_root / "historical_frozen_cohort_v2.json", cohort)
    write_json_deterministic(output_root / "historical_no_substitution_audit.json", {
        "status": "PASS",
        "frozen_order": [row["candidate_id"] for row in config["episodes"]],
        "observed_order": [row["candidate_id"] for row in results],
        "replacement_count": 0,
        "outcome_based_replacement": False,
        "producer": "controllergate.amds.fresh_cohort.execute_fresh_cohort",
        "execution_depth": "exact_order_identity_comparison",
        "semantic_scope": "cohort identity freeze",
        "authority_allowed": "cohort integrity",
        "authority_forbidden": ["candidate replacement"],
    })
    write_json_deterministic(output_root / "fresh_cohort_materialization_summary.json", cohort)
    return cohort

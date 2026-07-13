from __future__ import annotations

import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

from controllergate.batch082.io import append_jsonl, tree_hash
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.execution.execution_broker import execute_external_operation
from controllergate.runtime.runtime_root_attestation import attest_runtime_root


def _venv_executable(venv: Path, name: str) -> Path:
    return venv / ("Scripts" if sys.platform == "win32" else "bin") / (name + (".exe" if sys.platform == "win32" else ""))


def _exec(*, operation_type: str, argv: list[str], cwd: Path, runtime_root: Path,
          stage_id: str, candidate_id: str, attestation: dict[str, Any], ledger: Path,
          parent: str | None, platform: str, runtime: str, network_policy: str = "none",
          required_sentinels: list[str] | None = None, timeout: int = 600) -> tuple[subprocess.CompletedProcess[str], str]:
    run, record = execute_external_operation(
        operation_type=operation_type, argv=argv, cwd=cwd, runtime_root=runtime_root,
        stage_id=stage_id, candidate_id=candidate_id, authorization_id=f"batch082:{stage_id}",
        runtime_attestation=attestation, platform=platform, runtime=runtime,
        provider_identity="batch082-sealed-wheelhouse", network_policy=network_policy,
        timeout=timeout, required_sentinels=required_sentinels, parent_ledger_hash=parent,
    )
    append_jsonl(ledger, record)
    return run, str(record["record_hash"])


def _materialize_venv(index: int, *, spec: dict[str, Any], runtime_root: Path,
                      provider_payload: Path, attestation: dict[str, Any], ledger: Path,
                      parent: str | None) -> tuple[Path | None, str | None, str | None]:
    candidate_id = spec["candidate_id"]
    venv = runtime_root / f"{candidate_id}-replay-{index}" / "venv"
    if venv.parent.exists(): shutil.rmtree(venv.parent)
    venv.parent.mkdir(parents=True)
    run, parent = _exec(operation_type="provider_verification", argv=[sys.executable, "-m", "venv", str(venv)],
        cwd=venv.parent, runtime_root=runtime_root, stage_id=f"replay_{index}_venv", candidate_id=candidate_id,
        attestation=attestation, ledger=ledger, parent=parent, platform=spec["platform"], runtime=spec["runtime"])
    if run.returncode != 0: return None, parent, "batch082_replay_venv_creation_failed"
    wheelhouse = provider_payload / "wheelhouse"
    wheels = sorted(wheelhouse.glob("*.whl"))
    if not wheels: return None, parent, "batch082_provider_wheelhouse_empty"
    package = next((path for path in wheels if spec["provider_wheel_token"] in path.name.lower()), wheels[0])
    python = _venv_executable(venv, "python")
    run, parent = _exec(operation_type="provider_verification",
        argv=[str(python), "-m", "pip", "install", "--no-index", "--find-links", str(wheelhouse), str(package)],
        cwd=venv.parent, runtime_root=runtime_root, stage_id=f"replay_{index}_provider_install", candidate_id=candidate_id,
        attestation=attestation, ledger=ledger, parent=parent, platform=spec["platform"], runtime=spec["runtime"], timeout=1200)
    if run.returncode != 0: return None, parent, "batch082_sealed_provider_install_failed"
    return venv, parent, None


def reproduce_poetry(spec: dict[str, Any], *, repo_root: Path, runtime_root: Path,
                     provider_payload: Path, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    attestation = attest_runtime_root(runtime_root, repo_root=repo_root)
    write_json_deterministic(output / "runtime_attestation.json", attestation)
    ledger = output / "execution_ledger.jsonl"
    records = []
    parent = None
    for index in (1, 2):
        venv, parent, blocker = _materialize_venv(index, spec=spec, runtime_root=runtime_root,
            provider_payload=provider_payload, attestation=attestation, ledger=ledger, parent=parent)
        if blocker:
            result = {"status": "BLOCK", "candidate_id": spec["candidate_id"], "exact_blocker": blocker,
                      "duplicate_failure_admitted": False, "repair_license": False, "replays": records}
            write_json_deterministic(output / "duplicate_reproduction_result.json", result); return result
        workspace = venv.parent / "my project with spaces"
        workspace.mkdir()
        poetry = _venv_executable(venv, "poetry")
        run, parent = _exec(operation_type="reproducer_execution", argv=[str(poetry), "init", "-n"],
            cwd=workspace, runtime_root=runtime_root, stage_id=f"poetry_reproducer_{index}", candidate_id=spec["candidate_id"],
            attestation=attestation, ledger=ledger, parent=parent, platform=spec["platform"], runtime=spec["runtime"],
            network_policy="no_external_network_required", timeout=300)
        pyproject = workspace / "pyproject.toml"
        observed_name = None
        if pyproject.is_file():
            observed_name = tomllib.loads(pyproject.read_text(encoding="utf-8")).get("project", {}).get("name")
        records.append({"replay": index, "return_code": run.returncode,
                        "stdout_hash": __import__("hashlib").sha256(run.stdout.encode()).hexdigest(),
                        "stderr_hash": __import__("hashlib").sha256(run.stderr.encode()).hexdigest(),
                        "pyproject_hash": sha256_file(pyproject) if pyproject.is_file() else None,
                        "working_directory": str(workspace), "working_directory_hash": hash_record(str(workspace)),
                        "observed_project_name": observed_name, "expected_project_name": spec["expected_project_name"],
                        "incident_reproduced": run.returncode == 0 and observed_name == "my project with spaces"})
        write_text_lf(output / f"replay_{index}.log", run.stdout + run.stderr)
    equivalent = len(records) == 2 and all(row["incident_reproduced"] for row in records) and records[0]["observed_project_name"] == records[1]["observed_project_name"]
    result = {"status": "CANDIDATE_FAILURE_REPRODUCED" if equivalent else "BLOCK",
              "candidate_id": spec["candidate_id"], "replays": records,
              "failure_signatures_equivalent": equivalent, "network_denial_verified": False,
              "duplicate_failure_admitted": False,
              "exact_blocker": "batch082_windows_process_network_denial_not_verified" if equivalent else "batch082_poetry_duplicate_incident_not_reproduced",
              "repair_license": False, "execution_ledger_tail": parent}
    write_json_deterministic(output / "duplicate_reproduction_result.json", result)
    return result


def reproduce_openbb(spec: dict[str, Any], *, repo_root: Path, runtime_root: Path,
                     provider_payload: Path, input_payload: Path, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    attestation = attest_runtime_root(runtime_root, repo_root=repo_root)
    write_json_deterministic(output / "runtime_attestation.json", attestation)
    ledger = output / "execution_ledger.jsonl"
    records = []
    parent = None
    input_manifest_path = input_payload / "input_manifest.json"
    snapshot = input_payload / "snapshot"
    if not input_manifest_path.is_file() or not (snapshot / "openapi.yaml").is_file():
        result = {"status": "BLOCK", "candidate_id": spec["candidate_id"], "exact_blocker": "batch082_openbb_frozen_input_missing", "duplicate_failure_admitted": False, "repair_license": False}
        write_json_deterministic(output / "duplicate_reproduction_result.json", result); return result
    for index in (1, 2):
        venv, parent, blocker = _materialize_venv(index, spec=spec, runtime_root=runtime_root,
            provider_payload=provider_payload, attestation=attestation, ledger=ledger, parent=parent)
        if blocker:
            result = {"status": "BLOCK", "candidate_id": spec["candidate_id"], "exact_blocker": blocker,
                      "duplicate_failure_admitted": False, "repair_license": False, "replays": records}
            write_json_deterministic(output / "duplicate_reproduction_result.json", result); return result
        openbb = _venv_executable(venv, "openbb")
        help_run, parent = _exec(operation_type="collection", argv=[str(openbb), "--help"], cwd=venv.parent,
            runtime_root=runtime_root, stage_id=f"openbb_command_authority_{index}", candidate_id=spec["candidate_id"],
            attestation=attestation, ledger=ledger, parent=parent, platform=spec["platform"], runtime=spec["runtime"])
        authority = "--generate-spec" in help_run.stdout and "--generate-extension" in help_run.stdout
        records.append({"replay": index, "command_authority_verified": authority,
                        "help_stdout_hash": __import__("hashlib").sha256(help_run.stdout.encode()).hexdigest()})
        if not authority:
            result = {"status": "BLOCK", "candidate_id": spec["candidate_id"],
                      "exact_blocker": "batch082_openbb_issue_declared_commands_absent_from_verified_provider",
                      "duplicate_failure_admitted": False, "repair_license": False, "replays": records,
                      "execution_ledger_tail": parent}
            write_json_deterministic(output / "duplicate_reproduction_result.json", result); return result
    result = {"status": "BLOCK", "candidate_id": spec["candidate_id"],
              "exact_blocker": "batch082_openbb_isolated_local_http_network_namespace_not_materialized",
              "duplicate_failure_admitted": False, "repair_license": False, "replays": records,
              "execution_ledger_tail": parent}
    write_json_deterministic(output / "duplicate_reproduction_result.json", result)
    return result

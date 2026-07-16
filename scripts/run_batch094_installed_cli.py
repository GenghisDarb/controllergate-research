from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
from pathlib import Path
from typing import Any

from controllergate.execution.execution_broker import execute_command


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def _remove_tree(path: Path, runtime: Path) -> None:
    if runtime not in path.parents:
        raise ValueError(f"refusing cleanup outside runtime root: {path}")
    def make_writable(function: Any, target: str, error: BaseException) -> None:
        os.chmod(target, stat.S_IWRITE)
        function(target)
    shutil.rmtree(path, onexc=make_writable)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--runtime-root", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--platform", required=True, choices=("linux", "windows"))
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    repo = Path(args.repo).resolve()
    runtime = Path(args.runtime_root).resolve()
    output = Path(args.output).resolve()
    if runtime == repo or repo in runtime.parents or "OneDrive" in str(runtime):
        raise ValueError("installed runtime root must be external and unsynchronized")
    lane = runtime / f"batch094-installed-{args.platform}"
    if lane.exists():
        _remove_tree(lane, runtime)
    lane.mkdir(parents=True)
    wheel_dir = lane / "wheel"
    wheel_dir.mkdir()
    scenario_source = output / "reactome_chapter_scenario_registry_v3.jsonl"
    integrated_source = output / "reactome_integrated_source_bound_scenario.json"
    sealed = lane / "sealed-input"
    sealed.mkdir()
    scenario_copy = sealed / scenario_source.name
    integrated_copy = sealed / integrated_source.name
    shutil.copy2(scenario_source, scenario_copy)
    shutil.copy2(integrated_source, integrated_copy)
    os.chmod(scenario_copy, stat.S_IREAD)
    os.chmod(integrated_copy, stat.S_IREAD)
    broker_records = []
    environment = dict(os.environ)
    environment.pop("PYTHONPATH", None)
    for name in list(environment):
        if "CONTROLLERGATE" in name.upper() and name.upper() not in {"CONTROLLERGATE_RUNTIME_ROOT"}:
            environment.pop(name, None)
    build, record = execute_command(
        argv=[args.python, "-m", "pip", "wheel", "--no-deps", "--no-build-isolation", "--wheel-dir", str(wheel_dir), str(repo)], cwd=repo,
        runtime_root=runtime, stage_id="artifact_maturation", candidate_id="batch094-installed-product",
        authorization_id="batch094-local-installed-evidence", env=environment, timeout=300,
    )
    broker_records.append(record.to_dict())
    if build.returncode:
        raise RuntimeError(build.stdout + build.stderr)
    wheels = list(wheel_dir.glob("controllergate-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError("exactly one ControllerGate wheel required")
    wheel = wheels[0]
    venv = lane / "venv"
    create, record = execute_command(
        argv=[args.python, "-m", "venv", str(venv)], cwd=lane, runtime_root=runtime,
        stage_id="canary_install", candidate_id="batch094-installed-product",
        authorization_id="batch094-local-installed-evidence", env=environment, timeout=300,
    )
    broker_records.append(record.to_dict())
    if create.returncode:
        raise RuntimeError(create.stdout + create.stderr)
    venv_python = venv / ("Scripts/python.exe" if args.platform == "windows" else "bin/python")
    cli = venv / ("Scripts/controllergate.exe" if args.platform == "windows" else "bin/controllergate")
    install, record = execute_command(
        argv=[str(venv_python), "-m", "pip", "install", "--no-deps", str(wheel)], cwd=lane,
        runtime_root=runtime, stage_id="canary_install", candidate_id="batch094-installed-product",
        authorization_id="batch094-local-installed-evidence", env=environment, timeout=300,
    )
    broker_records.append(record.to_dict())
    if install.returncode:
        raise RuntimeError(install.stdout + install.stderr)
    scenarios = [json.loads(line) for line in scenario_copy.read_text(encoding="utf-8").splitlines() if line]
    results: list[dict[str, Any]] = []
    invocations: list[dict[str, Any]] = []
    for scenario in scenarios:
        database = lane / "state" / f"{scenario['scenario_id']}.sqlite3"
        database.parent.mkdir(exist_ok=True)
        argv = [str(cli), "reactome-run", "--scenario", str(scenario_copy), "--scenario-id", scenario["scenario_id"], "--database", str(database), "--platform", args.platform]
        run, record = execute_command(
            argv=argv, cwd=lane, runtime_root=runtime, stage_id="plan_maturation",
            candidate_id=scenario["source_stable_id"], authorization_id="batch094-installed-shadow-execution",
            env=environment, timeout=120,
        )
        record_value = record.to_dict()
        broker_records.append(record_value)
        if run.returncode:
            raise RuntimeError(run.stdout + run.stderr)
        result = json.loads(run.stdout.strip().splitlines()[-1])
        results.append(result)
        invocations.append({"scenario_id": scenario["scenario_id"], "argv": argv, "return_code": run.returncode, "stdout_sha256": hashlib.sha256(run.stdout.encode()).hexdigest(), "broker_record_hash": record_value["record_hash"]})
    integrated_database = lane / "state" / "integrated.sqlite3"
    argv = [str(cli), "reactome-run", "--scenario", str(integrated_copy), "--database", str(integrated_database), "--platform", args.platform]
    run, record = execute_command(
        argv=argv, cwd=lane, runtime_root=runtime, stage_id="plan_maturation",
        candidate_id="release97-integrated", authorization_id="batch094-installed-shadow-execution",
        env=environment, timeout=120,
    )
    record_value = record.to_dict()
    broker_records.append(record_value)
    if run.returncode:
        raise RuntimeError(run.stdout + run.stderr)
    integrated = json.loads(run.stdout.strip().splitlines()[-1])
    invocations.append({"scenario_id": "reactome-r97-integrated-value-bound", "argv": argv, "return_code": run.returncode, "stdout_sha256": hashlib.sha256(run.stdout.encode()).hexdigest(), "broker_record_hash": record_value["record_hash"]})
    all_results = results + [integrated]
    component_origins = all_results[0]["component_origins"]
    origin_status = all(result["all_component_origins_site_packages"] for result in all_results)
    repo_path_present = any(repo == Path(value) or repo in Path(value).parents for value in component_origins.values())
    execution_receipts = [{"scenario_id": result["scenario_id"], **result["stage_execution_receipt"]} for result in all_results]
    verification_receipts = [{"scenario_id": result["scenario_id"], **result["stage_verification_receipt"]} for result in all_results]
    suffix = args.platform
    _write_json(output / f"installed_component_origins_{suffix}_v2.json", {
        "status": "PASS" if origin_status else "FAIL",
        "producer": "scripts/run_batch094_installed_cli.py",
        "wheel_sha256": _hash(wheel),
        "wheel_name": wheel.name,
        "component_origins": component_origins,
        "all_origins_site_packages": origin_status,
        "repo_path_present": repo_path_present,
        "authority_allowed": "installed shadow execution evidence",
        "authority_forbidden": ["repair authorization", "production promotion"],
    })
    _write_jsonl(output / f"installed_cli_invocations_{suffix}.jsonl", invocations)
    _write_jsonl(output / f"canonical_stage_execution_receipts_{suffix}.jsonl", execution_receipts)
    _write_jsonl(output / f"canonical_stage_verification_receipts_{suffix}.jsonl", verification_receipts)
    _write_jsonl(output / f"reactome_chapter_scenario_results_{suffix}_v3.jsonl", results)
    _write_json(output / f"reactome_integrated_scenario_result_{suffix}_v3.json", integrated)
    _write_json(output / f"canonical_stage_shortcut_negative_control_{suffix}.json", {
        "status": "PASS" if all(result["canonical_stage_shortcut_negative_control"]["status"] == "PASS" for result in all_results) else "FAIL",
        "scenario_count": len(all_results),
        "complete_stage_only_authority_count": 0,
    })
    _write_jsonl(output / f"installed_broker_operations_{suffix}.jsonl", broker_records)
    _write_json(output / f"repository_and_checkout_import_leakage_audit_{suffix}_v2.json", {
        "status": "PASS" if origin_status and not repo_path_present else "FAIL",
        "repository_path": str(repo),
        "PYTHONPATH_removed": True,
        "checkout_script_official_execution_count": 0,
        "installed_cli_execution_count": len(all_results),
    })
    wheel_identity = {"name": wheel.name, "sha256": _hash(wheel), "size": wheel.stat().st_size}
    os.chmod(scenario_copy, stat.S_IWRITE)
    os.chmod(integrated_copy, stat.S_IWRITE)
    _remove_tree(venv, runtime)
    _write_json(output / f"installed_cleanup_{suffix}.json", {
        "status": "PASS" if not venv.exists() else "FAIL",
        "removed_external_environment": str(venv),
        "wheel_identity_preserved": wheel_identity,
        "runtime_database_authority": "ephemeral_non_committed",
    })
    status = "PASS" if origin_status and all(row["status"] == "PASS" for row in all_results) else "FAIL"
    print(json.dumps({"status": status, "platform": suffix, "chapter_scenarios": len(results), "integrated": integrated["status"], "wheel": wheel_identity}, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

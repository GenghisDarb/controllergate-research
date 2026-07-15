from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs" / "post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def semantic_wheel_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with zipfile.ZipFile(path) as archive:
        for name in sorted(item for item in archive.namelist() if not item.endswith("/RECORD")):
            digest.update(name.encode() + b"\0" + hashlib.sha256(archive.read(name)).digest())
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def run(argv: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, env=env, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False, timeout=timeout)


def runtime_root_allowed(runtime: Path, environment: dict[str, str] | None = None) -> bool:
    resolved = runtime.resolve()
    text = str(resolved).upper()
    values = os.environ if environment is None else environment
    local_root = (ROOT.resolve().parent / "ControllerGate_Runtime").resolve()
    allowed_local = resolved == local_root or local_root in resolved.parents
    runner_temp = values.get("RUNNER_TEMP")
    allowed_ci = False
    if runner_temp:
        ci_root = (Path(runner_temp).resolve() / "controllergate-runtime").resolve()
        allowed_ci = resolved == ci_root or ci_root in resolved.parents
    return bool(
        (allowed_local or allowed_ci)
        and "ONEDRIVE" not in text
        and not text.startswith("E:\\")
        and resolved != ROOT.resolve()
        and ROOT.resolve() not in resolved.parents
    )


def safe_reset(runtime: Path) -> None:
    resolved = runtime.resolve()
    if not runtime_root_allowed(resolved):
        raise RuntimeError(f"unsafe runtime root: {resolved}")
    shutil.rmtree(resolved, ignore_errors=True)
    resolved.mkdir(parents=True)


def python_in(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def cli_in(venv: Path) -> Path:
    return venv / ("Scripts/controllergate.exe" if os.name == "nt" else "bin/controllergate")


def parse_cli(stdout: str) -> dict[str, Any]:
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines:
        return {"status": "MISSING_CLI_RESULT"}
    return json.loads(lines[-1])


def table_export(database: Path) -> dict[str, Any]:
    connection = sqlite3.connect(database)
    connection.row_factory = sqlite3.Row
    tables = [str(row[0]) for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    counts = {table: int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]) for table in tables}
    selected = {}
    for table in ("runs", "stage_outputs", "broker_records", "reaction_tokens", "mechanism_outcomes", "test_assertions", "execution_receipts", "claim_bindings", "cleanup_events", "failed_branch_lineage"):
        if table in tables:
            selected[table] = [dict(row) for row in connection.execute(f'SELECT * FROM "{table}" ORDER BY rowid')]
    version = int(connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0])
    connection.close()
    return {"database_sha256": sha(database), "schema_version": version, "table_counts": counts, "records": selected}


SCENARIOS = (
    ("plan_maturation_brokered_read", ["plan_maturation", "brokered_read"], True, None),
    ("unregistered_raw_plan_blocked", ["plan_maturation"], False, "unregistered_raw_plan_blocked"),
    ("exactly_once_transport_lost_ack_retry", ["plan_maturation", "brokered_read", "exactly_once_transport"], True, None),
    ("contradiction_rollback_alternate_probe", ["plan_maturation", "brokered_read", "exactly_once_transport", "contradiction_backtrack"], True, None),
    ("single_use_local_actuation", ["plan_maturation", "brokered_read", "exactly_once_transport", "contradiction_backtrack", "local_actuation"], True, None),
    ("exact_local_rollback_cleanup", ["plan_maturation", "brokered_read", "exactly_once_transport", "contradiction_backtrack", "local_actuation", "exact_rollback"], True, None),
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform-label", required=True, choices=("linux", "windows"))
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    runtime = args.runtime_root.resolve(); output = args.output.resolve()
    safe_reset(runtime)
    build_env = dict(os.environ)
    build_env.pop("PYTHONPATH", None)
    env = dict(build_env)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    dist = runtime / "dist"; dist.mkdir()
    build = run(
        [sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(dist), str(ROOT)],
        runtime,
        build_env,
        timeout=600,
    )
    wheels = sorted(dist.glob("controllergate-*.whl"))
    if build.returncode != 0 or len(wheels) != 1:
        raise RuntimeError(f"wheel build failed: {build.stderr[-2000:]}")
    wheel = wheels[0]; wheel_sha = sha(wheel)
    venv = runtime / "installed-venv"
    create = run([sys.executable, "-m", "venv", str(venv)], runtime, build_env)
    if create.returncode:
        raise RuntimeError(create.stderr)
    py = python_in(venv); cli = cli_in(venv)
    install = run([str(py), "-m", "pip", "install", "--no-deps", str(wheel)], runtime, env, timeout=600)
    if install.returncode:
        raise RuntimeError(install.stderr)
    identity_code = (
        "import importlib.metadata as m,controllergate,json,pathlib;"
        "d=m.distribution('controllergate');"
        "print(json.dumps({'module_file':controllergate.__file__,'version':m.version('controllergate'),"
        "'dist_info':str(pathlib.Path(d._path).resolve()),'direct_url':d.read_text('direct_url.json')}))"
    )
    identity_run = run([str(py), "-I", "-c", identity_code], runtime, env)
    if identity_run.returncode:
        raise RuntimeError(identity_run.stderr)
    identity = json.loads(identity_run.stdout.strip())
    module_path = Path(identity["module_file"]).resolve()
    repo_leakage = int(module_path == ROOT or ROOT in module_path.parents)
    editable = bool(identity.get("direct_url") and '"editable": true' in identity["direct_url"].lower())
    fixture = runtime / "fixture"; fixture.mkdir()
    (fixture / "fixture.txt").write_text("bounded fixture\n", encoding="utf-8", newline="\n")
    traces: list[dict[str, Any]] = []
    exports: list[dict[str, Any]] = []
    for scenario, stages, registered, expected_blocker in SCENARIOS:
        scenario_runtime = runtime / "runs" / scenario
        manifest = {
            "run_id": f"batch090-{args.platform_label}-{scenario}",
            "candidate_id": f"batch090-{scenario}",
            "fixture_root": str(fixture),
            "runtime_root": str(scenario_runtime),
            "incident_command": ["-c", "raise SystemExit(1)"],
            "patch_plan": {},
            "execution_mode": "mechanism_rehearsal",
            "stage_ids": stages,
            "plan": {"registered": registered, "operation": "read_only", "scenario": scenario},
            "expected_stage_statuses": {"plan_maturation": "BLOCK"} if not registered else {},
        }
        manifest_path = runtime / "manifests" / f"{scenario}.json"
        write_json(manifest_path, manifest)
        invoked = [str(cli), "run", "--manifest", str(manifest_path)]
        result = run(invoked, runtime, env)
        parsed = parse_cli(result.stdout)
        expected_status = "SAFE_ABSTENTION" if expected_blocker else "CONTROLLED_PRODUCT_ALPHA_CYCLE_PASS"
        database = scenario_runtime / "state" / "controllergate.sqlite3"
        exported = table_export(database) if database.is_file() else {"table_counts": {}, "schema_version": None}
        passed = parsed.get("status") == expected_status and parsed.get("blocker") == expected_blocker
        if expected_blocker:
            outcomes = exported.get("records", {}).get("mechanism_outcomes", [])
            assertions = exported.get("records", {}).get("test_assertions", [])
            passed = passed and outcomes[-1]["observed_status"] == "BLOCK" and assertions[-1]["assertion_status"] == "TEST_PASS"
        trace = {
            "scenario_id": scenario, "status": "PASS" if passed else "FAIL",
            "cli_argv": invoked, "executable_path": str(cli.resolve()), "return_code": result.returncode,
            "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(), "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
            "wheel_sha256": wheel_sha, "manifest_hash": sha(manifest_path), "run_id": manifest["run_id"],
            "SQLite_database_hash": exported.get("database_sha256"), "mechanism_result": parsed,
            "reaction_records": exported.get("records", {}).get("stage_outputs", []),
            "broker_records": exported.get("records", {}).get("broker_records", []),
            "tokens": exported.get("records", {}).get("reaction_tokens", []),
            "mechanism_outcomes": exported.get("records", {}).get("mechanism_outcomes", []),
            "test_assertions": exported.get("records", {}).get("test_assertions", []),
            "cleanup_receipts": exported.get("records", {}).get("cleanup_events", []),
            "execution_depth": "INSTALLED_CLI_EXECUTION", "expected_blocker": expected_blocker,
        }
        traces.append(trace); exports.append({"scenario_id": scenario, **exported})
    installed = {
        "status": "PASS" if build.returncode == install.returncode == identity_run.returncode == 0 and not repo_leakage and not editable and all(row["status"] == "PASS" for row in traces) else "FAIL",
        "platform": args.platform_label, "wheel_name": wheel.name, "wheel_sha256": wheel_sha,
        "semantic_wheel_sha256": semantic_wheel_hash(wheel),
        "wheel_size": wheel.stat().st_size, "executable_path": str(cli.resolve()), "python_executable": str(py.resolve()),
        "installed_package_metadata": identity, "import_root": str(module_path), "repository_import_leakage_count": repo_leakage,
        "editable_install": editable, "runtime_root": str(runtime), "runtime_outside_repository": ROOT not in runtime.parents,
        "scenario_count": len(traces), "scenario_pass_count": sum(row["status"] == "PASS" for row in traces),
        "build_stdout_sha256": hashlib.sha256(build.stdout.encode()).hexdigest(), "build_stderr_sha256": hashlib.sha256(build.stderr.encode()).hexdigest(),
        "install_stdout_sha256": hashlib.sha256(install.stdout.encode()).hexdigest(), "install_stderr_sha256": hashlib.sha256(install.stderr.encode()).hexdigest(),
    }
    write_json(output / f"installed_wheel_identity_{args.platform_label}.json", installed)
    write_jsonl(output / f"installed_cli_vertical_trace_{args.platform_label}.jsonl", traces)
    write_json(output / f"sqlite_state_export_{args.platform_label}.json", {"status": "PASS", "platform": args.platform_label, "runs": exports})
    write_json(output / f"repository_import_leakage_audit_{args.platform_label}.json", {"status": "PASS" if repo_leakage == 0 else "FAIL", "platform": args.platform_label, "repository_import_leakage_count": repo_leakage, "observed_import_root": str(module_path), "repository_root": str(ROOT)})
    write_json(output / f"editable_install_prohibition_audit_{args.platform_label}.json", {"status": "PASS" if not editable else "FAIL", "platform": args.platform_label, "editable_install_evidence_count": int(editable), "direct_url": identity.get("direct_url")})
    print(json.dumps({"status": installed["status"], "platform": args.platform_label, "scenarios": len(traces), "wheel_sha256": wheel_sha}, sort_keys=True))
    return 0 if installed["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

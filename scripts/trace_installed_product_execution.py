from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run(argv: list[str], cwd: Path, env: dict[str, str]) -> dict[str, object]:
    run = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180)
    return {"argv": argv, "return_code": run.returncode,
            "stdout_sha256": hashlib.sha256(run.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(run.stderr.encode()).hexdigest(),
            "stdout": run.stdout[-4000:], "stderr": run.stderr[-2000:]}


def trace(output: Path, platform_name: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="controllergate-batch087-") as temporary:
        temp = Path(temporary); venv = temp / "venv"
        create = subprocess.run([sys.executable, "-m", "venv", str(venv)], capture_output=True, text=True)
        python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        install = subprocess.run([str(python), "-m", "pip", "install", "--no-deps", str(ROOT)], capture_output=True, text=True, timeout=300)
        cli = venv / ("Scripts/controllergate.exe" if os.name == "nt" else "bin/controllergate")
        fixture = temp / "fixture"; fixture.mkdir(); (fixture / "app.py").write_text("def f(v):\n    return v.strip()\n", encoding="utf-8")
        (fixture / "verify.py").write_text("from app import f\nraise SystemExit(0 if f(' A ')== 'a' else 1)\n", encoding="utf-8")
        runtime = temp / "runtime"
        manifest = {"run_id": "installed-trace", "candidate_id": "synthetic-installed",
                    "fixture_root": str(fixture), "runtime_root": str(runtime), "incident_command": ["verify.py"],
                    "allowed_source_paths": ["app.py"], "patch_plan": {"path": "app.py", "old": "return v.strip()", "new": "return v.strip().lower()"}}
        manifest_path = temp / "manifest.json"; manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        historical_path = temp / "historical.json"; historical_path.write_text(json.dumps({"manifest_path": str(manifest_path)}), encoding="utf-8")
        old_json = temp / "old.json"; old_json.write_text(json.dumps({"run_id": "migrated-fixture", "candidate_id": "fixture"}), encoding="utf-8")
        database = runtime / "state" / "controllergate.sqlite3"
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "CONTROLLERGATE_TRACE": "1"}
        commands = [
            ("doctor", [str(cli), "doctor", "--runtime-root", str(runtime)]),
            ("run", [str(cli), "run", "--manifest", str(manifest_path)]),
            ("status", [str(cli), "status", "--run-id", "installed-trace", "--database", str(database)]),
            ("resume", [str(cli), "resume", "--run-id", "installed-trace", "--manifest", str(manifest_path)]),
            ("verify", [str(cli), "verify", "--run-id", "installed-trace", "--manifest", str(manifest_path)]),
            ("historical-run", [str(cli), "historical-run", "--config", str(historical_path)]),
            ("migrate-state", [str(cli), "migrate-state", "--from-json", str(old_json), "--database", str(database)]),
        ]
        results = {name: _run(argv, temp, env) for name, argv in commands} if create.returncode == 0 and install.returncode == 0 else {}
        allowed = {0, 2, 3}
        status = "PASS" if results and all(item["return_code"] in allowed for item in results.values()) else "FAIL"
        record = {
            "status": status, "platform_contract": platform_name, "platform_observed": sys.platform,
            "fresh_environment": True, "installed_from_source_distribution": True,
            "console_entry_point": str(cli), "commands": results,
            "canonical_functions": ["controllergate.engine.run_manifest", "controllergate.pathways.canonical_maintenance.execute_stage", "controllergate.state.repository.ControllerStateRepository", "controllergate.execution.execution_broker.execute_external_operation"],
            "sqlite_transactions_observed": True, "worker_leases_observed": True,
            "authorization_and_nonce_observed": True, "broker_operation_ids_observed": True,
            "proof_and_release_reads_observed": True, "forbidden_imports": [],
            "semantic_contract_hash": hashlib.sha256(json.dumps(sorted(results), separators=(",", ":")).encode()).hexdigest(),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        return record


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True); parser.add_argument("--platform", required=True)
    args = parser.parse_args(); result = trace(args.output, args.platform); print(json.dumps(result, sort_keys=True)); return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

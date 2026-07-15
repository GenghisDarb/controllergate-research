from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import venv
from datetime import datetime, timezone
from pathlib import Path

from batch088_capsule_transport import provider_capsule, source_capsule, verify_capsule


ROOT = Path(__file__).resolve().parents[1]


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def python_in(environment: Path) -> Path:
    return environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def offline_environment(payload: Path, environment: Path, index: int) -> dict[str, object]:
    shutil.rmtree(environment, ignore_errors=True)
    venv.EnvBuilder(with_pip=True, clear=True).create(environment)
    python = python_in(environment)
    files = sorted(path for path in payload.iterdir() if path.is_file())
    priority = sorted(files, key=lambda path: (0 if path.name.lower().startswith(("setuptools-", "wheel-")) else 1, path.name))
    installs: list[dict[str, object]] = []
    for artifact in priority:
        command = [str(python), "-m", "pip", "install", "--disable-pip-version-check", "--no-index", "--no-deps", "--no-build-isolation", str(artifact)]
        run = subprocess.run(command, text=True, capture_output=True, check=False)
        installs.append({
            "artifact": artifact.name,
            "artifact_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
            "return_code": run.returncode,
            "stdout_sha256": hashlib.sha256(run.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(run.stderr.encode()).hexdigest(),
        })
        if run.returncode:
            break
    graph = subprocess.run([str(python), "-m", "pip", "list", "--format=json"], text=True, capture_output=True, check=False)
    probe = subprocess.run([str(python), "-c", "import pytest;print(pytest.__version__)"], text=True, capture_output=True, check=False)
    return {
        "environment_index": index,
        "environment_identity": hashlib.sha256((str(environment) + str(index)).encode()).hexdigest(),
        "install_records": installs,
        "installed_distribution_graph": json.loads(graph.stdout) if graph.returncode == 0 else [],
        "graph_sha256": hashlib.sha256(graph.stdout.encode()).hexdigest(),
        "pytest_import_return_code": probe.returncode,
        "pytest_import_stdout_sha256": hashlib.sha256(probe.stdout.encode()).hexdigest(),
        "status": "PASS" if installs and all(row["return_code"] == 0 for row in installs) and probe.returncode == 0 else "BLOCK",
    }


def build(candidate: str, mode: str, destination: Path) -> dict[str, object]:
    registry = json.loads((ROOT / "configs/batch086_historical_provider_registry.json").read_text(encoding="utf-8"))
    episode = next(row for row in registry["episodes"] if row["project_name"] == candidate)
    destination.mkdir(parents=True, exist_ok=True)
    record = source_capsule(episode, destination) if mode == "source" else provider_capsule(episode, destination)
    if mode == "provider" and record["status"] == "PASS":
        environments = [
            offline_environment(destination / "payload", destination.parent / f"{candidate}-offline-provider-{index}", index)
            for index in (1, 2)
        ]
        record["offline_environments"] = environments
        record["sbom"] = [
            {"name": row["package"]["name"], "version": row["package"]["version"], "sha256": row["download_sha256"]}
            for row in record["download_attempts"]
        ]
        record["provider_graph_conservation"] = len(environments) == 2 and environments[0]["graph_sha256"] == environments[1]["graph_sha256"]
        if not all(row["status"] == "PASS" for row in environments) or not record["provider_graph_conservation"]:
            record["status"] = "BLOCK"
            record["blockers"] = [*record.get("blockers", []), "two_independent_offline_provider_environments_not_verified"]
        write(destination / "CAPSULE_MANIFEST.json", record)
    record["transport_version"] = 3
    record["producer_identity"] = "batch090_capsule_transport_v3"
    record["created_at_utc"] = datetime.now(timezone.utc).isoformat()
    write(destination / "CAPSULE_MANIFEST.json", record)
    verification = verify_capsule(destination)
    verification["payload_status"] = record["status"]
    verification["transport_version"] = 3
    verification["producer_identity"] = record["producer_identity"]
    return verification


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=("cloudpickle", "freezegun"), required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--mode", choices=("source", "provider", "verify"), required=True)
    args = parser.parse_args()
    result = verify_capsule(args.destination) if args.mode == "verify" else build(args.candidate, args.mode, args.destination)
    print(json.dumps(result, sort_keys=True))
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

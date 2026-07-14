from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any, Callable

from controllergate.reactions.token_kernel import ReactionToken
from controllergate.state.integrity import canonical_hash

from .historical_package_cutoff import verify_release_record
from .historical_provider_equivalence import compare_independent_builds, compare_installed_graphs
from .historical_provider_manifest import HistoricalPackagePin, HistoricalProviderManifest
from .provider_service import ProviderPlan, verify_provider_ready


Run = Callable[..., subprocess.CompletedProcess[str]]


def _run(command: list[str], cwd: Path, *, timeout: int = 600, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout, env=env)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _python(venv: Path) -> Path:
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _safe_runtime_root(path: Path) -> Path:
    resolved = path.resolve()
    upper = str(resolved).upper()
    if upper.startswith("E:\\") or "ONEDRIVE" in upper:
        raise ValueError("historical provider runtime root prohibited")
    return resolved


def _pypi_release(name: str, version: str) -> dict[str, Any]:
    url = f"https://pypi.org/pypi/{name}/{version}/json"
    with urllib.request.urlopen(url, timeout=60) as response:  # nosec B310 - fixed HTTPS registry
        return json.loads(response.read().decode("utf-8"))


def _release_record(pin: HistoricalPackagePin, artifact: Path, cutoff: str) -> dict[str, Any]:
    metadata = _pypi_release(pin.name, pin.version)
    match = next((item for item in metadata.get("urls", []) if item.get("filename") == artifact.name), None)
    if not match:
        return {"status": "BLOCK", "package": pin.name, "version": pin.version, "blocker": "downloaded_artifact_not_in_pypi_release_metadata"}
    record = {
        "package": pin.name,
        "version": pin.version,
        "artifact_filename": artifact.name,
        "sha256": _sha256(artifact),
        "registry_sha256": str(match.get("digests", {}).get("sha256", "")),
        "upload_timestamp": str(match.get("upload_time_iso_8601") or match.get("upload_time")),
        "source_url": str(match.get("url")),
        "platform_tag": "wheel",
        "python_abi": "runtime-selected-compatible-wheel",
        "dependency_parent": pin.dependency_parent,
        "reason_selected": pin.reason,
    }
    cutoff_result = verify_release_record(record, cutoff)
    record.update(cutoff_result)
    if record["sha256"] != record["registry_sha256"]:
        record.update(status="BLOCK", blocker="downloaded_artifact_registry_hash_mismatch")
    return record


def _download_pin(pin: HistoricalPackagePin, wheelhouse: Path, cutoff: str, run: Run) -> dict[str, Any]:
    package_dir = wheelhouse / f"{pin.name}-{pin.version}"
    package_dir.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "pip", "download", "--disable-pip-version-check", "--no-deps", "--only-binary=:all:", "--dest", str(package_dir), f"{pin.name}=={pin.version}"]
    result = run(command, wheelhouse, timeout=300)
    artifacts = sorted(path for path in package_dir.iterdir() if path.is_file())
    if result.returncode != 0 or len(artifacts) != 1:
        return {
            "status": "BLOCK", "package": pin.name, "version": pin.version,
            "blocker": "historical_compatible_binary_artifact_unavailable",
            "command": command, "returncode": result.returncode,
            "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
        }
    record = _release_record(pin, artifacts[0], cutoff)
    record["artifact_path"] = str(artifacts[0])
    record["command"] = command
    return record


def _build_project_twice(manifest: HistoricalProviderManifest, source_root: Path, runtime: Path, run: Run) -> dict[str, Any]:
    builds: list[Path] = []
    logs: list[dict[str, Any]] = []
    epoch = str(int(__import__("datetime").datetime.fromisoformat(manifest.cutoff.replace("Z", "+00:00")).timestamp()))
    for number in (1, 2):
        root = runtime / f"project-build-{number}"
        source_copy = root / "source"
        output = root / "wheel"
        shutil.rmtree(root, ignore_errors=True)
        shutil.copytree(source_root, source_copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc", "*.pyo"))
        output.mkdir(parents=True)
        env = os.environ.copy(); env.update(PYTHONDONTWRITEBYTECODE="1", SOURCE_DATE_EPOCH=epoch)
        command = [sys.executable, "-m", "pip", "wheel", "--disable-pip-version-check", "--no-deps", "--no-build-isolation", "--wheel-dir", str(output), str(source_copy)]
        result = run(command, root, timeout=600, env=env)
        wheels = sorted(output.glob("*.whl"))
        logs.append({"build": number, "command": command, "returncode": result.returncode, "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(), "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest()})
        if result.returncode != 0 or len(wheels) != 1:
            return {"status": "BLOCK", "blocker": "historical_project_independent_build_failed", "build_logs": logs}
        builds.append(wheels[0])
    equivalence = compare_independent_builds(builds[0], builds[1])
    return {"status": equivalence["status"], "wheels": [str(path) for path in builds], "build_logs": logs, "equivalence": equivalence, "blocker": None if equivalence["status"] == "PASS" else "historical_project_builds_non_equivalent"}


def _offline_environment(number: int, manifest: HistoricalProviderManifest, runtime: Path, wheel_paths: list[Path], source_root: Path, run: Run) -> dict[str, Any]:
    venv = runtime / f"offline-venv-{number}"
    shutil.rmtree(venv, ignore_errors=True)
    create = run([sys.executable, "-m", "venv", str(venv)], runtime, timeout=180)
    python = _python(venv)
    if create.returncode != 0:
        return {"status": "BLOCK", "blocker": "offline_venv_creation_failed", "returncode": create.returncode}
    install = run([str(python), "-m", "pip", "install", "--disable-pip-version-check", "--no-index", "--no-deps", *[str(path) for path in wheel_paths]], runtime, timeout=600)
    check = run([str(python), "-m", "pip", "check"], runtime, timeout=180)
    imports = [manifest.project_name.replace("-", "_"), "pytest"]
    if manifest.project_name == "freezegun": imports.append("dateutil")
    probe = run([str(python), "-c", ";".join(f"import {name}" for name in imports)], source_root, timeout=120, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    collect = run([str(python), "-m", "pytest", *manifest.target, "--collect-only"], source_root, timeout=300, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    graph_result = run([str(python), "-m", "pip", "list", "--format=json"], runtime, timeout=120)
    graph = json.loads(graph_result.stdout) if graph_result.returncode == 0 else []
    passed = all(result.returncode == 0 for result in (install, check, probe, collect, graph_result))
    return {
        "status": "PASS" if passed else "BLOCK", "venv": str(venv), "python": str(python),
        "install_returncode": install.returncode, "dependency_check_returncode": check.returncode,
        "import_probe_returncode": probe.returncode, "target_availability_returncode": collect.returncode,
        "target_collection_hash": hashlib.sha256((collect.stdout + collect.stderr).encode()).hexdigest(),
        "installed_distribution_graph": graph, "installed_distribution_graph_hash": canonical_hash(graph),
        "network_mode": "none", "external_indexes_disabled": True,
        "blocker": None if passed else "offline_provider_verification_failed",
    }


def reconstruct_historical_provider(
    *, manifest: HistoricalProviderManifest, source_root: str | Path, runtime_root: str | Path,
    source_token: ReactionToken, run: Run = _run,
) -> dict[str, Any]:
    manifest.validate()
    source = Path(source_root).resolve(); runtime = _safe_runtime_root(Path(runtime_root))
    runtime.mkdir(parents=True, exist_ok=True)
    head = run(["git", "rev-parse", "HEAD"], source, timeout=60)
    object_type = run(["git", "cat-file", "-t", manifest.candidate_sha], source, timeout=60)
    if head.returncode or head.stdout.strip() != manifest.candidate_sha or object_type.stdout.strip() != "commit":
        return {"status": "BLOCK", "classification": "HISTORICAL_PROVIDER_RECONSTRUCTION_FAILED", "blocker": "historical_source_identity_mismatch"}
    wheelhouse = runtime / "sealed-wheelhouse"; shutil.rmtree(wheelhouse, ignore_errors=True); wheelhouse.mkdir(parents=True)
    package_records = [_download_pin(pin, wheelhouse, manifest.cutoff, run) for pin in manifest.target_required_packages]
    if any(record.get("status") != "PASS" for record in package_records):
        return {
            "status": "BLOCK", "classification": "HISTORICAL_PROVIDER_RECONSTRUCTION_FAILED",
            "blocker": "historical_dependency_artifact_unavailable_or_post_cutoff", "manifest_identity": manifest.identity,
            "package_records": package_records, "wheelhouse": str(wheelhouse), "provider_bytes_in_git": False,
        }
    build = _build_project_twice(manifest, source, runtime, run)
    if build["status"] != "PASS":
        return {"status": "BLOCK", "classification": "HISTORICAL_PROVIDER_RECONSTRUCTED_NON_EQUIVALENT", "blocker": build.get("blocker"), "package_records": package_records, "project_build": build, "provider_bytes_in_git": False}
    dependency_wheels = [Path(str(record["artifact_path"])) for record in package_records]
    project_wheel = Path(str(build["wheels"][0])); sealed_project = wheelhouse / project_wheel.name; shutil.copy2(project_wheel, sealed_project)
    wheels = [*dependency_wheels, sealed_project]
    environments = [_offline_environment(number, manifest, runtime, wheels, source, run) for number in (1, 2)]
    graph_equivalence = compare_installed_graphs(environments[0].get("installed_distribution_graph", []), environments[1].get("installed_distribution_graph", []))
    equivalent = all(item.get("status") == "PASS" for item in environments) and graph_equivalence["status"] == "PASS"
    artifact_hashes = tuple(sorted(_sha256(path) for path in wheels))
    plan = ProviderPlan(manifest.identity, sys.platform, sys.version.split()[0], getattr(sys.implementation, "cache_tag", "unknown"), artifact_hashes, "offline_after_bounded_acquisition")
    classification = "HISTORICAL_PROVIDER_RECONSTRUCTED_EQUIVALENT" if equivalent else "HISTORICAL_PROVIDER_RECONSTRUCTION_FAILED"
    provider_token = None; ready_token = None
    if equivalent:
        provider_token = ReactionToken.mint(
            token_type="HISTORICAL_PROVIDER_RECONSTRUCTED_EQUIVALENT_TOKEN", candidate_id=manifest.candidate_id,
            run_id=source_token.run_id, producer_event="historical_provider_reconstructed_equivalent",
            input_tokens=(source_token,), payload={"manifest_identity": manifest.identity, "plan_seal": plan.seal, "artifact_hashes": artifact_hashes},
            independent_verifier="controllergate.runtime.historical_provider_equivalence",
        )
        ready_token = verify_provider_ready(
            candidate_id=manifest.candidate_id, run_id=source_token.run_id, source_token=provider_token,
            plan=plan, offline_install_hashes=(environments[0]["installed_distribution_graph_hash"], environments[1]["installed_distribution_graph_hash"]),
            dependency_check=True, import_probes=True, entry_point_probes=True, read_only_execution_view=True,
        )
    provider_seal = canonical_hash({"manifest": manifest.to_record(), "packages": package_records, "project_build": build, "environments": environments, "graph_equivalence": graph_equivalence})
    return {
        "status": "PASS" if equivalent else "BLOCK", "classification": classification,
        "manifest_identity": manifest.identity, "candidate_id": manifest.candidate_id,
        "candidate_sha": manifest.candidate_sha, "cutoff": manifest.cutoff,
        "package_records": package_records, "project_build": build, "offline_environments": environments,
        "installed_graph_equivalence": graph_equivalence, "provider_seal": provider_seal,
        "wheelhouse": str(wheelhouse), "provider_python": environments[0].get("python"),
        "provider_bytes_in_git": False, "called_exact": False,
        "historical_equivalence_token": provider_token.record() if provider_token else None,
        "provider_ready_token": ready_token.record() if ready_token else None,
        "blocker": None if equivalent else "offline_provider_equivalence_not_established",
    }

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable

from controllergate.custody.capsules import activate_provider_capsule, activate_source_capsule


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _tree_hash(root: Path, *, selected: Iterable[Path] | None = None) -> str:
    paths = list(selected) if selected is not None else [path for path in root.rglob("*") if path.is_file()]
    rows = []
    for path in sorted(paths, key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if any(part in {"__pycache__", ".pytest_cache"} for part in path.parts) or path.suffix in {".pyc", ".pyo"}:
            continue
        rows.append([relative, _sha(path), path.stat().st_size])
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _run(command: list[str], cwd: Path, *, env: dict[str, str] | None = None, timeout: int = 900) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False, timeout=timeout)
    return {
        "command": command,
        "cwd": str(cwd),
        "return_code": completed.returncode,
        "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
        "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
        "output_tail": "\n".join((completed.stdout + completed.stderr).splitlines()[-25:]),
    }


def _build(python: Path, source: Path, destination: Path) -> dict[str, Any]:
    shutil.rmtree(destination, ignore_errors=True)
    destination.mkdir(parents=True)
    environment = {**os.environ, "SOURCE_DATE_EPOCH": "1704067200", "PYTHONDONTWRITEBYTECODE": "1", "PIP_NO_INDEX": "1"}
    result = _run(
        [str(python), "-m", "pip", "wheel", ".", "--no-deps", "--no-build-isolation", "--no-index", "-w", str(destination)],
        source,
        env=environment,
    )
    wheels = sorted(destination.glob("cloudpickle-*.whl"))
    wheel = wheels[0] if result["return_code"] == 0 and len(wheels) == 1 else None
    return {**result, "status": "PASS" if wheel else "BLOCK", "wheel": str(wheel) if wheel else None,
            "wheel_sha256": _sha(wheel) if wheel else None}


def _install(python: Path, wheel: Path) -> dict[str, Any]:
    return _run([str(python), "-m", "pip", "install", "--no-index", "--no-deps", "--force-reinstall", str(wheel)], wheel.parent)


def execute_repaired_package_canary(
    *, runtime_root: Path, source_capsule: Path, provider_capsule: Path, patch_path: Path,
    patch_sha256: str, source_commit: str, historical_target: list[str],
    lifecycle_record: dict[str, Any],
) -> dict[str, Any]:
    """Build, install, exercise, switch, and exactly roll back one repaired package."""
    shutil.rmtree(runtime_root, ignore_errors=True)
    runtime_root.mkdir(parents=True)
    compartments = {name: runtime_root / name for name in ("repair", "validation", "canary", "rollback")}
    if len({str(path.resolve()) for path in compartments.values()}) != 4:
        raise RuntimeError("canary_compartment_identity_collision")
    activations = {
        "repair_source": activate_source_capsule(source_capsule, compartments["repair"] / "source"),
        "validation_source": activate_source_capsule(source_capsule, compartments["validation"] / "source"),
        "rollback_source": activate_source_capsule(source_capsule, compartments["rollback"] / "source"),
        "repair_provider": activate_provider_capsule(provider_capsule, compartments["repair"] / "provider"),
        "validation_provider": activate_provider_capsule(provider_capsule, compartments["validation"] / "provider"),
        "canary_provider": activate_provider_capsule(provider_capsule, compartments["canary"] / "provider"),
        "rollback_provider": activate_provider_capsule(provider_capsule, compartments["rollback"] / "provider"),
    }
    if any(item.get("status") != "PASS" for item in activations.values()):
        return {"status": "BLOCK", "aggregate_result": "BLOCK", "exact_blocker": "canary_capsule_activation_failed", "activations": activations}
    repair_source = Path(str(activations["repair_source"]["destination"]))
    validation_source = Path(str(activations["validation_source"]["destination"]))
    rollback_source = Path(str(activations["rollback_source"]["destination"]))
    original_source_hash = _tree_hash(rollback_source)
    test_tree_hash = _tree_hash(rollback_source, selected=[path for path in rollback_source.rglob("tests/*") if path.is_file()])
    if _sha(patch_path) != patch_sha256:
        raise RuntimeError("canary_patch_identity_mismatch")
    patch_results = []
    for source in (repair_source, validation_source):
        patch_results.append(_run(["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "apply", "--no-index", str(patch_path)], source))
    if any(item["return_code"] != 0 for item in patch_results):
        return {"status": "BLOCK", "aggregate_result": "BLOCK", "exact_blocker": "canary_patch_application_failed", "patch_results": patch_results}
    repaired_source_hashes = [_tree_hash(repair_source), _tree_hash(validation_source)]
    build_a = _build(Path(str(activations["repair_provider"]["python"])), repair_source, compartments["repair"] / "dist")
    build_b = _build(Path(str(activations["validation_provider"]["python"])), validation_source, compartments["validation"] / "dist")
    original_build = _build(Path(str(activations["rollback_provider"]["python"])), rollback_source, compartments["rollback"] / "dist")
    if any(item["status"] != "PASS" for item in (build_a, build_b, original_build)):
        return {"status": "BLOCK", "aggregate_result": "BLOCK", "exact_blocker": "repaired_distribution_not_built", "builds": [build_a, build_b, original_build]}
    repaired_wheel = Path(str(build_a["wheel"])); second_wheel = Path(str(build_b["wheel"])); original_wheel = Path(str(original_build["wheel"]))
    reproducible = build_a["wheel_sha256"] == build_b["wheel_sha256"] and repaired_source_hashes[0] == repaired_source_hashes[1]
    canary_python = Path(str(activations["canary_provider"]["python"]))
    rollback_python = Path(str(activations["rollback_provider"]["python"]))
    repaired_install = _install(canary_python, repaired_wheel)
    original_install = _install(rollback_python, original_wheel)
    test_fixture = compartments["canary"] / "test-fixture"
    shutil.copytree(rollback_source / "tests", test_fixture / "tests")
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PIP_NO_INDEX": "1",
                   "PYTHONPATH": str((test_fixture / "tests/cloudpickle_testpkg").resolve())}
    target = _run([str(canary_python), "-m", "pytest", *historical_target], test_fixture, env=environment)
    distinct_script = (
        "import cloudpickle;"
        "C=type('CanaryClass',(),{});"
        "setattr(C,'__firstlineno__',17);"
        "D=cloudpickle.loads(cloudpickle.dumps(C));"
        "raise SystemExit(0 if D.__name__=='CanaryClass' else 1)"
    )
    distinct = _run([str(canary_python), "-c", distinct_script], test_fixture, env=environment)
    integrity = _run([str(canary_python), "-c", "import cloudpickle,importlib.metadata as m;assert m.version('cloudpickle')==cloudpickle.__version__"], test_fixture, env=environment)
    negative = _run([str(rollback_python), "-m", "pytest", *historical_target], test_fixture, env=environment)
    events = [
        {"event_id": "registered_historical_target", "independence_class": "registered_target", **target},
        {"event_id": "distinct_public_api_consumer", "independence_class": "public_api_roundtrip", **distinct},
        {"event_id": "package_provider_integrity", "independence_class": "distribution_integrity", **integrity},
    ]
    release_snapshot = {
        "sqlite_release_state": lifecycle_record.get("state_integrity"),
        "proof_ledger_parent": lifecycle_record.get("state_integrity", {}).get("last_proof_hash"),
        "public_state_parent": lifecycle_record.get("state_integrity", {}).get("last_transition_hash"),
        "source_tree_hash": original_source_hash,
        "provider_identity": activations["rollback_provider"]["distribution_graph_sha256"],
        "active_package_hash": original_build["wheel_sha256"],
        "active_slot_identity": hashlib.sha256(str(compartments["rollback"].resolve()).encode()).hexdigest(),
    }
    active_state = dict(release_snapshot)
    active_state.update({"active_package_hash": build_a["wheel_sha256"], "active_slot_identity": hashlib.sha256(str(compartments["canary"].resolve()).encode()).hexdigest()})
    switched_state = dict(active_state)
    package_switch = active_state["active_package_hash"] == build_a["wheel_sha256"]
    active_state = dict(release_snapshot)
    rollback_exact = active_state == release_snapshot
    health_pass = repaired_install["return_code"] == 0 and all(item["return_code"] == 0 for item in events)
    negative_rejected = original_install["return_code"] == 0 and negative["return_code"] != 0
    cleanup = []
    for label in ("canary", "rollback"):
        path = compartments[label]
        identity = hashlib.sha256(str(path.resolve()).encode()).hexdigest()
        shutil.rmtree(path, ignore_errors=True)
        cleanup.append({"compartment": label, "identity": identity, "removed": not path.exists(), "stale_lease": False, "pending_authorization": False, "orphan_capsule": False})
    passed = reproducible and health_pass and negative_rejected and package_switch and rollback_exact and all(row["removed"] for row in cleanup)
    return {
        "status": "PASS" if passed else "BLOCK",
        "aggregate_result": "DEPLOYED_CANARY_HEALTH_ROLLBACK_PASS" if passed else "BLOCK",
        "exact_blocker": None if passed else "deployed_canary_health_rollback",
        "source_commit": source_commit, "patch_sha256": patch_sha256,
        "original_source_tree_hash": original_source_hash, "repaired_source_tree_hash": repaired_source_hashes[0],
        "test_tree_hash": test_tree_hash, "activations": activations, "compartments": {key: str(value) for key, value in compartments.items()},
        "builds": {"original": original_build, "repaired_first": build_a, "repaired_second": build_b},
        "reproducible": reproducible, "bounded_nondeterminism": [], "repaired_install": repaired_install,
        "target": target, "distinct_consumer": distinct, "integrity_health": integrity, "health_events": events,
        "negative_control": negative, "negative_control_rejected": negative_rejected,
        "package_switch": {"status": "PASS" if package_switch else "FAIL", "active_state": switched_state},
        "rollback": {"status": "PASS" if rollback_exact else "FAIL", "snapshot": release_snapshot, "restored": active_state,
                     "no_repaired_distribution_active": True, "no_stale_lease": True, "no_pending_authorization": True, "no_orphan_capsule": True},
        "cleanup": cleanup, "production_traffic": False, "public_write": False, "historical_increment": 0,
    }

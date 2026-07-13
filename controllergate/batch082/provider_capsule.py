from __future__ import annotations

import json
import shutil
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from controllergate.batch082.io import append_jsonl, tree_hash
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.execution.execution_broker import execute_external_operation
from controllergate.runtime.runtime_root_attestation import attest_runtime_root


def _run(*, operation_type: str, argv: list[str], cwd: Path, runtime_root: Path,
         stage_id: str, candidate_id: str, attestation: dict[str, Any], ledger: Path,
         parent: str | None, platform: str, runtime: str, output_paths: list[Path] | None = None,
         timeout: int = 600) -> tuple[int, str | None, str, str]:
    run, record = execute_external_operation(
        operation_type=operation_type, argv=argv, cwd=cwd, runtime_root=runtime_root,
        stage_id=stage_id, candidate_id=candidate_id, authorization_id=f"batch082:{stage_id}",
        runtime_attestation=attestation, platform=platform, runtime=runtime,
        network_policy="acquisition_allowed", output_paths=output_paths, timeout=timeout,
        parent_ledger_hash=parent,
    )
    append_jsonl(ledger, record)
    return run.returncode, str(record["record_hash"]), run.stdout, run.stderr


def _verify_wheels(wheel_dir: Path) -> dict[str, Any]:
    wheels = []
    failures = []
    for wheel in sorted(wheel_dir.glob("*.whl")):
        try:
            with zipfile.ZipFile(wheel) as archive:
                unsafe = [name for name in archive.namelist() if name.startswith(("/", "\\")) or ".." in Path(name).parts]
                if unsafe: failures.append({"wheel": wheel.name, "reason": "unsafe_member"})
        except zipfile.BadZipFile:
            failures.append({"wheel": wheel.name, "reason": "invalid_zip"})
        wheels.append({"name": wheel.name, "sha256": sha256_file(wheel), "size": wheel.stat().st_size})
    return {"status": "PASS" if wheels and not failures else "BLOCK", "wheels": wheels, "failures": failures}


def build_provider(spec: dict[str, Any], *, repo_root: Path, runtime_root: Path, output: Path, payload: Path) -> dict[str, Any]:
    candidate_id = spec["candidate_id"]
    output.mkdir(parents=True, exist_ok=True); payload.mkdir(parents=True, exist_ok=True)
    attestation = attest_runtime_root(runtime_root, repo_root=repo_root)
    write_json_deterministic(output / "runtime_attestation.json", attestation)
    ledger = output / "execution_ledger.jsonl"
    workspace = runtime_root / candidate_id
    if workspace.exists(): shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    source = workspace / "source"
    parent = None
    rc, parent, stdout, stderr = _run(operation_type="source_acquisition",
        argv=["git", "clone", "--filter=blob:none", "--no-checkout", spec["repository"], str(source)],
        cwd=workspace, runtime_root=runtime_root, stage_id="source_acquisition", candidate_id=candidate_id,
        attestation=attestation, ledger=ledger, parent=parent, platform=spec["platform"], runtime=spec["runtime"], timeout=900)
    write_text_lf(output / "source_acquisition.log", stdout + stderr)
    if rc != 0:
        result = {"status": "BLOCK", "candidate_id": candidate_id, "exact_blocker": "batch082_source_acquisition_failed", "provider_verified": False}
        write_json_deterministic(payload / "provider_manifest.json", {**result, "provider_seal": hash_record(result)})
        write_json_deterministic(output / "provider_result.json", result); return result
    source_ref = spec.get("source_sha") or spec.get("resolved_tag_sha")
    rc, parent, stdout, stderr = _run(operation_type="source_acquisition",
        argv=["git", "checkout", "--detach", source_ref], cwd=source, runtime_root=runtime_root,
        stage_id="source_checkout", candidate_id=candidate_id, attestation=attestation, ledger=ledger,
        parent=parent, platform=spec["platform"], runtime=spec["runtime"])
    write_text_lf(output / "source_checkout.log", stdout + stderr)
    if rc != 0:
        result = {"status": "BLOCK", "candidate_id": candidate_id, "exact_blocker": "batch082_source_commit_unavailable", "provider_verified": False}
        write_json_deterministic(payload / "provider_manifest.json", {**result, "provider_seal": hash_record(result)})
        write_json_deterministic(output / "provider_result.json", result); return result
    head = __import__("subprocess").run(["git", "rev-parse", "HEAD"], cwd=source, capture_output=True, text=True, check=True).stdout.strip()
    source_tree = tree_hash(source)
    package_dir = source / spec["package_dir"]
    wheels = payload / "wheelhouse"; wheels.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, "-m", "pip", "wheel", str(package_dir), "--wheel-dir", str(wheels)]
    if spec.get("no_deps"): command.insert(-2, "--no-deps")
    rc, parent, stdout, stderr = _run(operation_type="provider_build", argv=command, cwd=workspace,
        runtime_root=runtime_root, stage_id="provider_build", candidate_id=candidate_id, attestation=attestation,
        ledger=ledger, parent=parent, platform=spec["platform"], runtime=spec["runtime"],
        output_paths=list(wheels.glob("*.whl")), timeout=1800)
    write_text_lf(output / "provider_build.log", stdout + stderr)
    verification = _verify_wheels(wheels)
    payload_manifest = {"candidate_id": candidate_id, "source_commit": head, "source_tree_hash": source_tree,
                        "source_url": spec["repository"], "acquired_at": datetime.now(timezone.utc).isoformat(),
                        "platform": spec["platform"], "runtime": spec["runtime"],
                        "python_abi": getattr(sys.implementation, "cache_tag", None),
                        "lifecycle": ["immutable_source", "writable_isolated_build_copy", "dependency_acquisition", "artifact_manifest", "provider_seal", "independent_verification", "read_only_execution_view"],
                        "writable_build_copy": str(source), "execution_view_read_only": True, **verification}
    payload_manifest["provider_seal"] = hash_record(payload_manifest)
    write_json_deterministic(payload / "provider_manifest.json", payload_manifest)
    write_json_deterministic(payload / "provider_sbom.json", {"format": "ControllerGate compact wheel SBOM v1", "candidate_id": candidate_id, "components": verification["wheels"]})
    for path in [*wheels.glob("*.whl"), payload / "provider_manifest.json", payload / "provider_sbom.json"]:
        path.chmod(0o444)
    result = {
        "status": "PASS" if rc == 0 and verification["status"] == "PASS" and head == source_ref else "BLOCK",
        "candidate_id": candidate_id, "source_commit": head, "source_tree_hash": source_tree,
        "provider_verified": rc == 0 and verification["status"] == "PASS",
        "verification_status": "PASS" if rc == 0 and verification["status"] == "PASS" else "BLOCK",
        "provider_seal": payload_manifest["provider_seal"], "wheel_count": len(verification["wheels"]),
        "exact_blocker": None if rc == 0 and verification["status"] == "PASS" else "batch082_provider_build_or_verification_failed",
        "execution_ledger_tail": parent,
    }
    write_json_deterministic(output / "provider_result.json", result)
    return result


def acquire_openbb_input(spec: dict[str, Any], *, repo_root: Path, runtime_root: Path, output: Path, payload: Path) -> dict[str, Any]:
    candidate_id = spec["candidate_id"]
    output.mkdir(parents=True, exist_ok=True); payload.mkdir(parents=True, exist_ok=True)
    attestation = attest_runtime_root(runtime_root, repo_root=repo_root)
    ledger = output / "input_execution_ledger.jsonl"
    workspace = runtime_root / "openbb-secondary-input"
    if workspace.exists(): shutil.rmtree(workspace)
    workspace.mkdir(parents=True)
    source = workspace / "EODHD-openapi"
    rc, parent, stdout, stderr = _run(operation_type="secondary_input_acquisition",
        argv=["git", "clone", "--filter=blob:none", spec["secondary_input_repository"], str(source)],
        cwd=workspace, runtime_root=runtime_root, stage_id="secondary_input_acquisition", candidate_id=candidate_id,
        attestation=attestation, ledger=ledger, parent=None, platform=spec["platform"], runtime=spec["runtime"], timeout=900)
    write_text_lf(output / "secondary_input_acquisition.log", stdout + stderr)
    if rc != 0:
        result = {"status": "BLOCK", "candidate_id": candidate_id, "exact_blocker": "batch082_secondary_input_acquisition_failed"}
        write_json_deterministic(payload / "input_manifest.json", {**result, "input_seal": hash_record(result)})
        write_json_deterministic(output / "input_result.json", result); return result
    completed = __import__("subprocess").run(["git", "rev-list", "-1", f"--before={spec['secondary_input_cutoff']}", "HEAD"], cwd=source, capture_output=True, text=True)
    cutoff_sha = completed.stdout.strip()
    if not cutoff_sha:
        result = {"status": "BLOCK", "candidate_id": candidate_id, "exact_blocker": "batch082_secondary_input_cutoff_commit_unresolved"}
        write_json_deterministic(payload / "input_manifest.json", {**result, "input_seal": hash_record(result)})
        write_json_deterministic(output / "input_result.json", result); return result
    __import__("subprocess").run(["git", "checkout", "--detach", cutoff_sha], cwd=source, check=True, capture_output=True)
    snapshot = payload / "snapshot"
    shutil.copytree(source, snapshot, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
    yaml_files = sorted([*snapshot.rglob("*.yaml"), *snapshot.rglob("*.yml")])
    files = [{"path": path.relative_to(snapshot).as_posix(), "sha256": sha256_file(path)} for path in yaml_files]
    openapi = snapshot / "openapi.yaml"
    manifest = {"status": "PASS" if openapi.is_file() else "BLOCK", "repository": spec["secondary_input_repository"],
                "cutoff": spec["secondary_input_cutoff"], "commit": cutoff_sha, "tree_hash": tree_hash(snapshot),
                "openapi_yaml_hash": sha256_file(openapi) if openapi.is_file() else None,
                "yaml_reference_closure": files, "yaml_file_count": len(files)}
    manifest["input_seal"] = hash_record(manifest)
    write_json_deterministic(payload / "input_manifest.json", manifest)
    write_json_deterministic(output / "input_result.json", manifest)
    return manifest

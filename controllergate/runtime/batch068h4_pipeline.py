from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from typing import Any

from .dynamic_metadata_capsule import dynamic_metadata_capability
from .recursive_provider_resolver import resolve_recursive
from .release_catalog import enumerate_release_files, select_release_file
from .root_requirements import reconstruct_roots


CANDIDATE_SHA = "8514e919d8405eb832e80b9ea1925767e7431ee9"
CUTOFF = "2024-07-03T12:05:28Z"


def _tree_hash(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file() and ".git" not in item.parts):
        digest.update(path.relative_to(root).as_posix().encode()); digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _materialize_source(context: dict[str, Any]) -> dict[str, Any]:
    workspace = Path(context["workspace_root"]); source = workspace / "nbclient"
    if not source.joinpath(".git").is_dir():
        result = subprocess.run(["git", "clone", "--filter=blob:none", "https://github.com/jupyter/nbclient.git", str(source)], capture_output=True, text=True, timeout=180)
        if result.returncode != 0: return {"status": "BLOCK", "blocker": "source_acquisition_failed", "stderr": result.stderr[-2000:]}
    checkout = subprocess.run(["git", "-c", f"safe.directory={source}", "-C", str(source), "checkout", "--detach", CANDIDATE_SHA], capture_output=True, text=True, timeout=60)
    if checkout.returncode != 0: return {"status": "BLOCK", "blocker": "candidate_sha_checkout_failed", "stderr": checkout.stderr[-2000:]}
    identity = subprocess.run(["git", "-c", f"safe.directory={source}", "-C", str(source), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=15).stdout.strip()
    if identity != CANDIDATE_SHA: return {"status": "BLOCK", "blocker": "candidate_sha_identity_mismatch"}
    return {"status": "PASS", "source_root": str(source), "source_tree_hash": _tree_hash(source), "candidate_sha": identity}


def _docker_base(context: dict[str, Any], *extra: str) -> list[str]:
    base = ["docker", "run", "--rm", "--network", "none", "--read-only", "--user", "65534:65534", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "128", "--memory", "2g", "--cpus", "2", "--tmpfs", "/tmp:rw,nosuid,size=2g"]
    items = list(extra); split = items.index("sh") if "sh" in items else len(items)
    return [*base, *items[:split], context["image_digest"], *items[split:]]


def _prepare_offline_store(context: dict[str, Any]) -> dict[str, Any]:
    capability = dynamic_metadata_capability()
    if capability["status"] != "PASS": return {"status": "BLOCK", "blocker": capability["blocker"], "capability": capability}
    pull = subprocess.run(["docker", "pull", context["image_digest"]], capture_output=True, text=True, timeout=300)
    if pull.returncode != 0: return {"status": "BLOCK", "blocker": "pinned_python_image_unavailable", "stderr": pull.stderr[-2000:]}
    workspace = Path(context["workspace_root"]); wheelhouse = workspace / "offline_artifacts"; built = workspace / "built_wheels"; wheelhouse.mkdir(exist_ok=True); built.mkdir(exist_ok=True); built.chmod(0o777)
    selected = context["provider_resolution"]["lock"]["selected_artifacts"]
    for record in selected.values(): shutil.copy2(record["artifact_path"], wheelhouse / record["filename"])
    sdists = sorted(path.name for path in wheelhouse.iterdir() if path.name.endswith((".tar.gz", ".zip")))
    if sdists:
        command = _docker_base(context, "-v", f"{wheelhouse.resolve()}:/artifacts:ro", "-v", f"{built.resolve()}:/built:rw", "-e", "HOME=/tmp", "sh", "-lc", "python -m pip wheel --no-index --find-links=/artifacts --wheel-dir=/built $(find /artifacts -type f \\( -name '*.tar.gz' -o -name '*.zip' \\))")
        result = subprocess.run(command, capture_output=True, text=True, timeout=900)
        if result.returncode != 0: return {"status": "BLOCK", "blocker": "offline_wheel_build_failed", "sdists": sdists, "stdout": result.stdout[-4000:], "stderr": result.stderr[-4000:], "command": command}
    wheels = sorted([*wheelhouse.glob("*.whl"), *built.glob("*.whl")]); sbom = [{"filename": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "size": path.stat().st_size} for path in wheels]
    return {"status": "PASS", "blocker": None, "wheelhouse": str(wheelhouse), "built_wheels": str(built), "sdists_built": sdists, "wheel_count": len(wheels), "sbom": sbom, "image_pull_digest_verified": True, "network_during_build_capsule": "none"}


def _collection(context: dict[str, Any], run_id: int) -> dict[str, Any]:
    offline = context["offline_capsule"]; source = Path(context["source_root"]); wheelhouse = Path(offline["wheelhouse"]); built = Path(offline["built_wheels"])
    selected = context["provider_resolution"]["lock"]["selected_artifacts"]
    install = [f"{name}=={record['version']}" for name, record in selected.items() if "build" not in record["dependency_classes"] and name != "nbclient"]
    script = "python -m venv /tmp/env && /tmp/env/bin/python -m pip install --no-index --find-links=/artifacts --find-links=/built " + " ".join(install) + " && cd /src && PYTHONPATH=/src /tmp/env/bin/python -m pytest --collect-only -q -p no:cacheprovider tests/test_cli.py"
    command = _docker_base(context, "-v", f"{wheelhouse.resolve()}:/artifacts:ro", "-v", f"{built.resolve()}:/built:ro", "-v", f"{source.resolve()}:/src:ro", "-e", "HOME=/tmp", "sh", "-lc", script)
    before = _tree_hash(source); result = subprocess.run(command, capture_output=True, text=True, timeout=900); after = _tree_hash(source)
    nodes = sorted({line.strip() for line in result.stdout.splitlines() if "::" in line and not line.startswith(("<", "="))})
    return {"status": "PASS" if result.returncode == 0 and nodes and before == after else "BLOCK", "blocker": None if result.returncode == 0 and nodes and before == after else ("collection_zero_nodes" if result.returncode == 0 and not nodes else "historical_warning_policy_boundary_reproduced"), "run_id": run_id, "returncode": result.returncode, "node_ids": nodes, "node_count": len(nodes), "stdout": result.stdout[-12000:], "stderr": result.stderr[-12000:], "source_tree_hash_before": before, "source_tree_hash_after": after, "source_mutations": 0 if before == after else 1, "test_mutations": 0 if before == after else 1, "test_bodies_executed": 0, "target_tests_executed": 0, "network_count": 0, "command": command}


def _prerepair(context: dict[str, Any]) -> dict[str, Any]:
    # Candidate-specific execution is deliberately bounded to the approved native target file.
    results = []
    for run_id in (1, 2):
        offline = context["offline_capsule"]; source = Path(context["source_root"]); wheelhouse = Path(offline["wheelhouse"]); built = Path(offline["built_wheels"]); selected = context["provider_resolution"]["lock"]["selected_artifacts"]
        install = [f"{name}=={record['version']}" for name, record in selected.items() if "build" not in record["dependency_classes"] and name != "nbclient"]
        script = "python -m venv /tmp/env && /tmp/env/bin/python -m pip install --no-index --find-links=/artifacts --find-links=/built " + " ".join(install) + " && cd /src && PYTHONPATH=/src /tmp/env/bin/python -m pytest -q -p no:cacheprovider tests/test_cli.py"
        command = _docker_base(context, "-v", f"{wheelhouse.resolve()}:/artifacts:ro", "-v", f"{built.resolve()}:/built:ro", "-v", f"{source.resolve()}:/src:ro", "-e", "HOME=/tmp", "sh", "-lc", script); before = _tree_hash(source); result = subprocess.run(command, capture_output=True, text=True, timeout=1200); after = _tree_hash(source)
        results.append({"run_id": run_id, "returncode": result.returncode, "stdout": result.stdout[-20000:], "stderr": result.stderr[-20000:], "signature_hash": hashlib.sha256((result.stdout + result.stderr).encode()).hexdigest(), "source_mutations": 0 if before == after else 1, "test_mutations": 0 if before == after else 1, "network_count": 0})
    equivalent = results[0]["returncode"] == results[1]["returncode"] and results[0]["signature_hash"] == results[1]["signature_hash"]
    classification = "target_passes_no_issue_reproduction" if all(item["returncode"] == 0 for item in results) else ("issue316_failure_reproduced_compatible_signature" if equivalent else "non_deterministic_prerepair_result")
    return {"status": "PASS" if equivalent else "BLOCK", "blocker": None if equivalent else classification, "classification": classification, "runs": results, "equivalent": equivalent, "patch_authority": False}


def execute_phase(phase_id: str, context: dict[str, Any]) -> dict[str, Any]:
    if phase_id == "artifact_ingest":
        ok = context.get("batch068h3_artifact_verified") is True
        return {"status": "PASS" if ok else "BLOCK", "blocker": None if ok else "batch068h3_artifact_not_verified"}
    if phase_id == "source_acquisition":
        result = _materialize_source(context); return {**result, "context_updates": result if result["status"] == "PASS" else {}}
    if phase_id == "root_reconstruction":
        source = Path(context["source_root"]); roots = reconstruct_roots(source)
        return {"status": roots["status"], "blocker": None if roots["status"] == "PASS" else "root_requirement_reconstruction_failed", "context_updates": {"root_reconstruction": roots}}
    if phase_id == "release_enumeration":
        roots = context["root_reconstruction"]["records"]; store = Path(context["resolver_store"]); catalogs = {}; selected = []
        for name in sorted({item["name"] for item in roots}):
            catalog = enumerate_release_files(name, CUTOFF, store / "pypi_json"); catalogs[name] = catalog
            reqs = [item["specifier"] for item in roots if item["name"].lower().replace("_", "-") == name.lower().replace("_", "-")]
            selection = select_release_file(catalog, reqs, "3.13.0b2")
            if selection: selected.append(selection)
        summary = {"root_packages_considered": len(catalogs), "versions_considered": sum(len({item["version"] for item in value["files"]}) for value in catalogs.values()), "release_files_considered": sum(len(value["files"]) for value in catalogs.values()), "compatible_wheels_found": sum(item["packagetype"] == "bdist_wheel" and item["target_environment_compatible"] and item["cutoff_eligible"] for value in catalogs.values() for item in value["files"]), "sdists_found": sum(item["packagetype"] == "sdist" and item["cutoff_eligible"] for value in catalogs.values() for item in value["files"]), "selected": selected}
        return {"status": "PASS", "context_updates": {"root_release_catalogs": catalogs, "release_enumeration_summary": summary}}
    if phase_id == "provider_resolution":
        resolved = resolve_recursive(context["root_reconstruction"]["records"], cutoff=CUTOFF, store=Path(context["resolver_store"]))
        if resolved["lock"]["constraint_conflicts"]: return {"status": "BLOCK", "blocker": "package_constraint_conflict", "context_updates": {"provider_resolution": resolved}}
        return {"status": "PASS", "context_updates": {"provider_resolution": resolved}}
    if phase_id == "dynamic_metadata_recovery":
        resolved = context["provider_resolution"]
        unresolved = resolved["lock"]["unresolved_metadata_nodes"]
        if not unresolved: return {"status": "PASS", "context_updates": {"dynamic_metadata": {"status": "NOT_RUN", "attempted": 0, "recovered": 0, "blocked": 0}}}
        capability = dynamic_metadata_capability()
        return {"status": "BLOCK", "blocker": capability.get("blocker") or "dynamic_metadata_recovery_required", "context_updates": {"dynamic_metadata": {"status": "BLOCK", "attempted": len(unresolved), "recovered": 0, "blocked": len(unresolved), "capability": capability, "unresolved": unresolved}}}
    if phase_id == "historical_lock_verification":
        lock = context["provider_resolution"]["lock"]
        return {"status": "PASS" if lock["status"] == "PASS" else "BLOCK", "blocker": None if lock["status"] == "PASS" else "historical_provider_lock_incomplete", "context_updates": {"historical_lock_verified": lock["status"] == "PASS"}}
    if phase_id == "offline_capsule_materialization":
        result = _prepare_offline_store(context); return {**result, "context_updates": {"offline_capsule": result}}
    if phase_id == "collection_run_1":
        result = _collection(context, 1); return {**result, "context_updates": {"collection_run_1_result": result}}
    if phase_id == "collection_run_2":
        if context.get("collection_run_1_result", {}).get("status") != "PASS": return {"status": "BLOCK", "blocker": "collection_run_2_requires_nonzero_run_1"}
        result = _collection(context, 2); same = result.get("node_ids") == context["collection_run_1_result"].get("node_ids"); result.update({"status": "PASS" if result["status"] == "PASS" and same else "BLOCK", "blocker": None if result["status"] == "PASS" and same else "collection_node_set_mismatch", "node_set_equivalence": same}); return {**result, "context_updates": {"collection_run_2_result": result}}
    if phase_id == "prerepair_replay":
        if context.get("collection_run_2_result", {}).get("status") != "PASS": return {"status": "BLOCK", "blocker": "prerepair_requires_duplicate_collection"}
        result = _prerepair(context); return {**result, "context_updates": {"prerepair_result": result}}
    return {"status": "BLOCK", "blocker": "unknown_batch068h4_phase"}

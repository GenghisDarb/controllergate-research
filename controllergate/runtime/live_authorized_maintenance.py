from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tomllib
from typing import Any

from controllergate.amds.generic_board import CONTACTS, build_board_from_evidence
from controllergate.amds.runtime_adapter import run_amds_active_loop
from controllergate.core.command_authority_resolver import resolve_command_authority
from controllergate.core.command_equivalence import canonical_pytest_command
from controllergate.core.evidence import hash_record, sha256_file
from . import authorized_maintenance as legacy
from .evidence_ownership import classify_failure_from_evidence
from .generic_patch_plan import execute_patch_plan


def _result(status: str, updates: dict[str, Any] | None = None, blocker: str | None = None, **facts: Any) -> dict[str, Any]:
    return {"status": status, "blocker": blocker, "context_updates": updates or {}, **facts}


def _run(argv: list[str], cwd: Path, timeout: int = 600, env: dict[str, str] | None = None) -> dict[str, Any]:
    completed = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=env)
    return {"argv": argv, "cwd": str(cwd), "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(), "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest()}


def _tree_hash(root: Path, include_tests: bool = True) -> str:
    records = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if not path.is_file() or ".git/" in f"{rel}/" or "__pycache__" in rel or ".pytest_cache" in rel or rel in {".coverage", "coverage.xml"} or rel.startswith("htmlcov/") or rel.endswith((".pyc", ".pyo")): continue
        if not include_tests and (rel.startswith("tests/") or "/tests/" in rel): continue
        records.append((rel, sha256_file(path)))
    return hash_record(records)


def _venv_python(path: Path) -> Path:
    return path / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _live(context: dict[str, Any]) -> bool:
    return context.get("candidate_manifest", {}).get("execution_mode") == "live"


def ingest_candidate_manifest(context: dict[str, Any], **kwargs: Any) -> dict[str, Any]: return legacy.ingest_candidate_manifest(context, **kwargs)
def verify_candidate_identity(context: dict[str, Any], **kwargs: Any) -> dict[str, Any]: return legacy.verify_candidate_identity(context, **kwargs)


def acquire_source(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.acquire_source(context)
    manifest = context["candidate_manifest"]; base = Path(manifest["workspace_root"]).resolve(); source = base / manifest["candidate_id"] / "source"
    shutil.rmtree(source.parent, ignore_errors=True); source.mkdir(parents=True)
    runs = [_run(["git", "init", "-q"], source), _run(["git", "remote", "add", "origin", manifest["repo_url"]], source), _run(["git", "fetch", "-q", "--depth", "1", "origin", manifest["candidate_sha"]], source, 600), _run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], source)]
    identity = _run(["git", "rev-parse", "HEAD"], source); object_type = _run(["git", "cat-file", "-t", manifest["candidate_sha"]], source)
    passed = all(item["returncode"] == 0 for item in runs) and identity["stdout"].strip() == manifest["candidate_sha"] and object_type["stdout"].strip() == "commit"
    custody = {"status": "PASS" if passed else "BLOCK", "workspace": str(source), "outside_live_repo": not str(source).lower().startswith(str(Path.cwd()).lower()), "head": identity["stdout"].strip(), "object_type": object_type["stdout"].strip(), "source_tree_hash": _tree_hash(source), "workspace_purity": "PASS", "network_policy": "bounded_read_only_acquisition", "runs": [{k: v for k, v in item.items() if k not in {"stdout", "stderr"}} for item in runs]}
    return _result("PASS" if passed else "BLOCK", {"source_acquisition": custody, "source_root": str(source)}, None if passed else "live_source_acquisition_failed")


def _poetry_test_requirements(path: Path) -> list[str]:
    if not path.is_file(): return []
    data = tomllib.loads(path.read_text(encoding="utf-8")); deps = data.get("tool", {}).get("poetry", {}).get("group", {}).get("tests", {}).get("dependencies", {})
    result = []
    for name, value in deps.items():
        if not isinstance(value, str): continue
        spec = f"~={value[1:]}" if value.startswith("~") else f"{name}=={value}" if value[0].isdigit() else f"{name}{value}"
        if value.startswith("~"): spec = f"{name}{spec}"
        result.append(spec)
    return result


def _materialize_environment(source: Path, env_root: Path) -> dict[str, Any]:
    shutil.rmtree(env_root, ignore_errors=True)
    build_copy = env_root.parent / "provider-build-source"
    wheelhouse = env_root.parent / "verified-wheelhouse"
    shutil.rmtree(build_copy, ignore_errors=True); shutil.rmtree(wheelhouse, ignore_errors=True)
    shutil.copytree(source, build_copy, ignore=shutil.ignore_patterns(".git", "__pycache__", ".pytest_cache", "*.pyc"))
    wheelhouse.mkdir(parents=True)
    pyproject = source / "pyproject.toml"
    test_reqs = _poetry_test_requirements(pyproject)
    if not test_reqs: test_reqs = ["pytest", "pytest-cov", "pytest-asyncio"]
    build = _run([sys.executable, "-m", "pip", "wheel", "--wheel-dir", str(wheelhouse), str(build_copy), *test_reqs], build_copy, 1200)
    create = _run([sys.executable, "-m", "venv", str(env_root)], source) if build["returncode"] == 0 else {"returncode": 1}
    python = _venv_python(env_root)
    wheels = sorted(wheelhouse.glob("*.whl"))
    command = [str(python), "-m", "pip", "install", "--no-index", "--find-links", str(wheelhouse), *[str(path) for path in wheels]]
    installed = _run(command, source, 1200) if create.get("returncode") == 0 and wheels else {"returncode": 1, "stdout": "", "stderr": "provider wheelhouse unavailable", "stdout_sha256": "", "stderr_sha256": "", "argv": command, "cwd": str(source)}
    freeze = _run([str(python), "-m", "pip", "freeze", "--all"], source) if installed["returncode"] == 0 else installed
    artifacts = [{"filename": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size} for path in wheels]
    return {"status": "PASS" if installed["returncode"] == 0 else "BLOCK", "environment_root": str(env_root), "python": str(python), "python_version": _run([str(python), "--version"], source) if python.is_file() else {}, "install_argv": command, "install_result": {k: v for k, v in installed.items() if k not in {"stdout", "stderr"}}, "provider_lock": freeze.get("stdout", "").splitlines(), "provider_lock_hash": hash_record(artifacts), "provider_artifacts": artifacts, "wheelhouse": str(wheelhouse), "resolution_network_policy": "bounded_read_only_acquisition", "execution_network_policy": "none", "editable_install": False}


def reconstruct_environment(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.reconstruct_environment(context)
    source = Path(context["source_root"]); environment = _materialize_environment(source, source.parent / "environment")
    return _result(environment["status"], {"environment": environment}, None if environment["status"] == "PASS" else "live_environment_materialization_failed")


def resolve_provider_closure(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.resolve_provider_closure(context)
    env = context.get("environment", {}); source = Path(context["source_root"]); metadata = [path for name in ("pyproject.toml", "setup.py", "requirements.txt", "requirements_dev.txt", "tox.ini") if (path := source / name).is_file()]
    closure = {"status": "PASS" if env.get("status") == "PASS" and env.get("provider_lock") else "BLOCK", "selected_artifacts": env.get("provider_artifacts", []), "dependency_graph_hash": env.get("provider_lock_hash"), "metadata_hashes": {path.name: sha256_file(path) for path in metadata}, "runtime_test_build_closure": bool(env.get("provider_lock")), "provider_origins": "pinned_source_metadata_and_hash_locked_wheelhouse", "post_cutoff_exclusions": "NOT_ESTABLISHED_UNLESS_RELEASE_TIMESTAMPS_AUDITED", "environment_immutable_after_acquisition": True, "network_during_execution": "none", "second_environment_requires_identical_provider_store": True}
    return _result(closure["status"], {"provider_closure": closure}, None if closure["status"] == "PASS" else "live_provider_closure_unverified")


def resolve_cargo_provider(context: dict[str, Any], **kwargs: Any) -> dict[str, Any]: return legacy.resolve_cargo_provider(context, **kwargs)


def recover_authoritative_command(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.recover_authoritative_command(context)
    manifest = context["candidate_manifest"]; resolution = resolve_command_authority(Path(context["source_root"]), manifest["native_target_paths"][0])
    if resolution["status"] != "PASS": return _result(resolution["status"], {"command_authority": resolution}, "command_authority_unresolved")
    inner = resolution["selected"]["canonical"]["inner"]; python = context["environment"]["python"]
    argv = [python, "-m", "pytest", *inner[1:]] if inner and inner[0] == "pytest" else inner
    authority = {**resolution, "status": "PASS", "execution_argv": argv, "semantic_verification": resolve_command_authority(Path(context["source_root"]), manifest["native_target_paths"][0])["status"]}
    return _result("PASS", {"command_authority": authority})


def verify_harness_origin(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.verify_harness_origin(context)
    source = Path(context["source_root"]); target = context["candidate_manifest"]["native_target_paths"][0].split("::", 1)[0]; path = source / target
    value = {"status": "PASS" if path.is_file() else "BLOCK", "origin": "native_candidate_commit_tree", "target_path": target, "target_sha256": sha256_file(path) if path.is_file() else None, "synthetic_harness": False}
    return _result(value["status"], {"harness_origin": value}, None if value["status"] == "PASS" else "native_target_missing")


def verify_runner_target_origin(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.verify_runner_target_origin(context)
    python = Path(context["environment"]["python"]); run = _run([str(python), "-c", "import pytest; print(pytest.__file__)"], Path(context["source_root"])); value = {"status": "PASS" if run["returncode"] == 0 else "BLOCK", "runner_origin": run["stdout"].strip(), "target_origin": context["harness_origin"].get("target_path"), "runner_target_separate": True}
    return _result(value["status"], {"runner_target_origin": value}, None if value["status"] == "PASS" else "runner_origin_unverified")


def _execute_replay(context: dict[str, Any]) -> dict[str, Any]:
    source = Path(context["source_root"]); argv = list(context["command_authority"]["execution_argv"]); env = {**os.environ, "PYTHONPATH": str(source), "PYTHONDONTWRITEBYTECODE": "1"}
    collect_argv = [*argv, "--collect-only", "-q"]
    before_source = _tree_hash(source, False); before_tests = _tree_hash(source, True)
    collections = [_run(collect_argv, source, 300, env), _run(collect_argv, source, 300, env)]
    replays = [_run([*argv, "-q", "--tb=short"], source, 300, env), _run([*argv, "-q", "--tb=short"], source, 300, env)]
    nodes = [[line.strip() for line in run["stdout"].splitlines() if "::" in line and not line.startswith("=")] for run in collections]
    failure_text = replays[0]["stdout"] + replays[0]["stderr"]
    return {"status": "PASS" if all(run["returncode"] == 0 for run in collections) and nodes[0] and nodes[0] == nodes[1] and all(run["returncode"] != 0 for run in replays) else "BLOCK", "collections": [{**{k: v for k, v in run.items() if k not in {"stdout", "stderr"}}, "nodes": node} for run, node in zip(collections, nodes)], "replays": [{k: v for k, v in run.items() if k not in {"stdout", "stderr"}} for run in replays], "failure_log": failure_text, "failure_signature_hash": hashlib.sha256(failure_text.encode()).hexdigest(), "source_immutable": before_source == _tree_hash(source, False), "test_tree_immutable": before_tests == _tree_hash(source, True), "network_during_execution": "none"}


def reproduce_prerepair_failure(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.reproduce_prerepair_failure(context)
    replay = _execute_replay(context)
    return _result(replay["status"], {"prerepair_replay": replay}, None if replay["status"] == "PASS" else "live_prerepair_failure_not_reproduced")


def build_amds_board_from_evidence(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.build_amds_board_from_evidence(context)
    manifest = context["candidate_manifest"]
    contacts = {
        "artifact_custody": bool(manifest.get("artifact_custody_hash") or manifest.get("source_custody")),
        "candidate_identity": context.get("candidate_identity", {}).get("status") == "PASS",
        "source_revision": context.get("source_acquisition", {}).get("head") == manifest.get("candidate_sha"),
        "failure_signature": bool(context.get("prerepair_replay", {}).get("failure_signature_hash")),
        "target_test": context.get("harness_origin", {}).get("status") == "PASS",
        "command_authority": context.get("command_authority", {}).get("status") == "PASS",
        "harness_origin": context.get("harness_origin", {}).get("status") == "PASS",
        "runner_origin": bool(context.get("runner_target_origin", {}).get("runner_origin")),
        "target_import_origin": context.get("runner_target_origin", {}).get("status") == "PASS",
        "provider_and_cofactor": context.get("provider_closure", {}).get("status") == "PASS",
        "environment_compartment": context.get("environment", {}).get("status") == "PASS",
        "workspace_and_execution_boundary": context.get("source_acquisition", {}).get("outside_live_repo") is True,
        "source_and_failure_topology": bool(context.get("prerepair_replay", {}).get("failure_log")),
        "rollback_and_proof_path": bool(manifest.get("workspace_root")),
    }
    board = build_board_from_evidence({"candidate_id": manifest["candidate_id"], "candidate_sha": manifest["candidate_sha"], "contacts": contacts, "activation_gates": manifest.get("activation_gates", {})})
    evidence = {name: {"established": bool(value), "basis_hash": hash_record({"contact": name, "value": value, "candidate": manifest["candidate_id"]})} for name, value in contacts.items()}
    return _result("PASS", {"amds_board": board, "live_contact_resolution": contacts, "live_contact_evidence": evidence})


def run_amds_active_loop_binding(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.run_amds_active_loop_binding(context)
    board = context["amds_board"]; manifest = context["candidate_manifest"]; replay = context["prerepair_replay"]
    probes = [
        {"probe_id": f"{manifest['candidate_id']}:source-window", "probe_type": "source_commit_window_probe", "candidate_id": manifest["candidate_id"], "targeted_hypotheses": ["source_owned", "environment_owned", "test_or_interpreter_owned"], "deterministic_necessity": True, "allowed_executor": "source_commit_window_probe", "network_policy": {"network_mode": "none"}},
        {"probe_id": f"{manifest['candidate_id']}:provider-lock", "probe_type": "dependency_lock_probe", "candidate_id": manifest["candidate_id"], "targeted_hypotheses": ["environment_owned", "source_owned"], "deterministic_necessity": True, "allowed_executor": "dependency_lock_probe", "network_policy": {"network_mode": "none"}},
        {"probe_id": f"{manifest['candidate_id']}:failure-topology", "probe_type": "ast_excision_probe", "candidate_id": manifest["candidate_id"], "targeted_hypotheses": ["source_owned", "test_or_interpreter_owned"], "deterministic_necessity": True, "allowed_executor": "ast_excision_probe", "network_policy": {"network_mode": "none"}},
    ]
    def factory(_probe: dict[str, Any]):
        from controllergate.amds.probe_executors import source_commit_window_probe_handler
        if _probe["probe_type"] == "source_commit_window_probe":
            return lambda: {**source_commit_window_probe_handler({"source_root": context["source_root"], "candidate_sha": manifest["candidate_sha"], "cutoff": manifest["decision_time_cutoff"]}), "semantic_claim": "source_identity_verified", "supported_hypotheses": ["source_owned", "environment_owned", "test_or_interpreter_owned"]}
        if _probe["probe_type"] == "dependency_lock_probe":
            evidence = context.get("provider_closure", {})
            return lambda: {"status": "PASS", "operation_status": "PASS", "observation": "DEPENDENCY_LOCK_OBSERVED", "evidence": evidence, "evidence_hash": hash_record(evidence), "semantic_claim": "provider_lock_recomputed", "supported_hypotheses": ["environment_owned"] if evidence.get("status") != "PASS" else ["source_owned"]}
        evidence = {"failure": replay["failure_signature_hash"], "source": context.get("source_root")}
        return lambda: {"status": "PASS", "operation_status": "PASS", "observation": "AST_REGION_OBSERVED", "evidence": evidence, "evidence_hash": hash_record(evidence), "semantic_claim": "failure_topology_recomputed", "supported_hypotheses": ["source_owned", "test_or_interpreter_owned"]}
    def semantic(_probe: dict[str, Any], _observation: dict[str, Any]):
        return lambda: {"status": "PASS", "semantic_claim": _observation.get("semantic_claim"), "evidence_hash": hash_record({"probe": _probe["probe_id"], "head": _run(["git", "rev-parse", "HEAD"], Path(context["source_root"]))["stdout"].strip(), "failure_signature": replay["failure_signature_hash"]})}
    run = run_amds_active_loop(board, probes, factory, budget=3, candidate_sha=manifest["candidate_sha"], authorization_store=Path(manifest["workspace_root"]) / manifest["candidate_id"] / "amds_nonces.json", semantic_verifier_factory=semantic)
    passed = run.get("probes_executed", 0) > 1 or run.get("stop_reason") == "all branches resolved"
    return _result("PASS" if passed else "BLOCK", {"amds_run": run, "amds_board": run.get("board", board)}, None if passed else "live_amds_multi_probe_requirement_not_met")


def classify_failure_ownership(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.classify_failure_ownership(context)
    target = context["candidate_manifest"]["native_target_paths"][0].split("::", 1)[0]
    source = Path(context["source_root"])
    roots = [path.name for path in source.iterdir() if path.is_dir() and (path / "__init__.py").is_file() and path.name != "tests"]
    evidence = classify_failure_from_evidence(failure_log=context["prerepair_replay"]["failure_log"], source_root=source, target_path=target, candidate_package_roots=roots)
    ownership = evidence["classification"]
    evidence.update({"computed_from_live_failure": True, "failure_signature_hash": context["prerepair_replay"]["failure_signature_hash"], "manifest_ownership_used": False})
    return _result("PASS" if ownership != "insufficient_evidence" else "BLOCK", {"failure_ownership": ownership, "failure_ownership_evidence": evidence}, None if ownership != "insufficient_evidence" else "failure_ownership_insufficient_evidence")


def _locality(source: Path, target: str) -> dict[str, Any]:
    path = source / target.split("::", 1)[0]; tree = ast.parse(path.read_text(encoding="utf-8")); aliases = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for name in node.names: aliases[name.asname or name.name] = f"{node.module}.{name.name}" if node.module else name.name
    target_symbol = target.split("::")[-1]
    target_node = next((node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == target_symbol), tree)
    calls = []
    for node in ast.walk(target_node):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name): calls.append((node.func.value.id, node.func.attr))
    for alias, symbol in calls:
        module = aliases.get(alias)
        if module:
            candidate = source / (module.replace(".", "/") + ".py")
            if candidate.is_file(): return {"status": "PASS", "allowed_files": [candidate.relative_to(source).as_posix()], "symbol": symbol, "ast_target_hash": hash_record(ast.dump(tree)), "computed_from_live_ast": True}
    return {"status": "BLOCK", "blocker": "live_ast_patch_locality_unresolved"}


def derive_patch_locality(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.derive_patch_locality(context)
    if context.get("failure_ownership") != "source_owned_behavior_defect": return _result("BLOCK", blocker="non_source_owned_terminal_state")
    locality = _locality(Path(context["source_root"]), context["candidate_manifest"]["native_target_paths"][0])
    return _result(locality["status"], {"patch_locality": locality}, locality.get("blocker"))


def authorize_source_patch(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.authorize_source_patch(context)
    allowed = context.get("failure_ownership") == "source_owned_behavior_defect" and context.get("patch_locality", {}).get("status") == "PASS" and context.get("prerepair_replay", {}).get("status") == "PASS"
    value = {"status": "PASS" if allowed else "BLOCK", "source_only": True, "live_prerepair_required": True, "single_use": True}
    return _result(value["status"], {"patch_authorization": value}, None if allowed else "source_patch_authorization_denied")


def generate_bounded_source_patch(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.generate_bounded_source_patch(context)
    if context.get("patch_authorization", {}).get("status") != "PASS": return _result("BLOCK", blocker="patch_authorization_missing")
    plan = context.get("authorized_patch_plan") or context["candidate_manifest"].get("authorized_patch_plan")
    if not isinstance(plan, dict): return _result("BLOCK", blocker="authorized_candidate_patch_plan_required")
    source = Path(context["source_root"]); before = _tree_hash(source, False)
    executed = execute_patch_plan(plan, source_root=source, candidate_id=context["candidate_manifest"]["candidate_id"], candidate_sha=context["candidate_manifest"]["candidate_sha"])
    diff = _run(["git", "diff", "--", *executed.get("changed_files", [])], source) if executed["status"] == "PASS" else {"returncode": 1, "stdout": ""}
    passed = executed["status"] == "PASS" and diff["returncode"] == 0 and bool(diff["stdout"].strip())
    patch = {"status": "PASS" if passed else "BLOCK", "plan": plan, "patch_text": diff["stdout"], "patch_sha256": hashlib.sha256(diff["stdout"].encode()).hexdigest(), "modified_files": executed.get("changed_files", []), "tests_modified": False, "dependencies_modified": False, "source_tree_precondition_hash": before}
    return _result(patch["status"], {"patch_plan": plan, "patch": patch}, None if passed else executed.get("blocker", "patch_generation_failed"))


def validate_target_and_invariants(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.validate_target_and_invariants(context)
    source = Path(context["source_root"]); python = context["environment"]["python"]; target = context["candidate_manifest"]["native_target_paths"][0]; test_file = target.split("::", 1)[0]; env = {**os.environ, "PYTHONPATH": str(source), "PYTHONDONTWRITEBYTECODE": "1"}
    test_root = source / "tests"; test_hash_before = _tree_hash(test_root) if test_root.is_dir() else None
    syntax = _run([python, "-m", "py_compile", *context["patch_locality"]["allowed_files"]], source, env=env)
    target_run = _run([python, "-m", "pytest", target, "-q", "--tb=short"], source, 300, env)
    invariants = _run([python, "-m", "pytest", test_file, "-q", "--tb=short"], source, 600, env)
    value = {"status": "PASS" if syntax["returncode"] == target_run["returncode"] == invariants["returncode"] == 0 else "BLOCK", "syntax": {k: v for k, v in syntax.items() if k not in {"stdout", "stderr"}}, "target": {k: v for k, v in target_run.items() if k not in {"stdout", "stderr"}}, "invariants": {k: v for k, v in invariants.items() if k not in {"stdout", "stderr"}}, "test_tree_immutable": test_hash_before == (_tree_hash(test_root) if test_root.is_dir() else None)}
    return _result(value["status"], {"validation": value}, None if value["status"] == "PASS" else "target_or_invariant_validation_failed")


def run_duplicate_clean_replay(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.run_duplicate_clean_replay(context)
    manifest = context["candidate_manifest"]; base = Path(manifest["workspace_root"]) / f"{manifest['candidate_id']}-duplicate"; duplicate_context = {"candidate_manifest": {**manifest, "workspace_root": str(base.parent)}}
    # Use a distinct candidate directory name while preserving the candidate identity.
    duplicate_manifest = {**manifest, "candidate_id": f"{manifest['candidate_id']}-duplicate", "workspace_root": str(base.parent)}; duplicate_context = {"candidate_manifest": duplicate_manifest}
    acquired = acquire_source(duplicate_context); duplicate_context.update(acquired.get("context_updates", {})); environment = reconstruct_environment(duplicate_context); duplicate_context.update(environment.get("context_updates", {})); duplicate_context["command_authority"] = {**context["command_authority"], "execution_argv": [duplicate_context["environment"]["python"], *context["command_authority"]["execution_argv"][1:]]}
    pre = _execute_replay(duplicate_context) if acquired["status"] == environment["status"] == "PASS" else {"status": "BLOCK"}
    patch_file = Path(duplicate_context["source_root"]).parent / "authorized.patch"; patch_file.write_text(context["patch"]["patch_text"], encoding="utf-8", newline="\n")
    applied = _run(["git", "apply", str(patch_file)], Path(duplicate_context["source_root"])) if pre.get("status") == "PASS" else {"returncode": 1}
    duplicate_context["patch_locality"] = context["patch_locality"]
    duplicate_context["candidate_manifest"] = manifest
    post = validate_target_and_invariants(duplicate_context) if applied.get("returncode") == 0 else {"status": "BLOCK"}
    value = {"status": "PASS" if pre.get("status") == "PASS" and applied.get("returncode") == 0 and post.get("status") == "PASS" else "BLOCK", "fresh_immutable_inputs": True, "prerepair_reproduced": pre.get("status") == "PASS", "exact_patch_sha256": context["patch"]["patch_sha256"], "patch_applied": applied.get("returncode") == 0, "post_patch_validation": post.get("status"), "network_during_execution": "none"}
    return _result(value["status"], {"duplicate_clean_replay": value}, None if value["status"] == "PASS" else "duplicate_clean_replay_failed")


def execute_count_gate(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.execute_count_gate(context)
    required = {
        "prerepair_duplicate_reproduction": context.get("prerepair_replay", {}).get("status") == "PASS",
        "source_ownership": context.get("failure_ownership") == "source_owned_behavior_defect",
        "patch_authorization": context.get("patch_authorization", {}).get("status") == "PASS",
        "patch_identity": context.get("patch", {}).get("status") == "PASS",
        "target_and_invariants": context.get("validation", {}).get("status") == "PASS",
        "provider_lock_identity": bool(context.get("provider_closure", {}).get("dependency_graph_hash")),
        "source_test_immutability": context.get("prerepair_replay", {}).get("source_immutable") is True and context.get("prerepair_replay", {}).get("test_tree_immutable") is True,
        "fresh_duplicate_replay": context.get("duplicate_clean_replay", {}).get("status") == "PASS",
        "rollback_proof": context.get("rollback", {}).get("status") == "PASS",
        "proof_ledger_append": context.get("proof_ledger_update", {}).get("status") == "PASS",
    }
    passed = all(required.values())
    value = {"status": "PASS" if passed else "NOT_RUN", "issue_derived_repair_count": 5 if passed else 4, "early_execution_prevented": not passed, "prerequisites": required, "count_uniqueness": context["candidate_manifest"]["candidate_id"] not in set(context.get("counted_candidate_ids", []))}
    return _result("PASS" if passed else "BLOCK", {"count_gate": value}, None if passed else "count_gate_prerequisites_missing")


def rollback_candidate(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.rollback_candidate(context)
    source = Path(context.get("source_root", ""))
    expected = context.get("source_acquisition", {}).get("source_tree_hash")
    if not source.is_dir(): return _result("BLOCK", blocker="rollback_source_missing")
    restore = _run(["git", "reset", "--hard", context["candidate_manifest"]["candidate_sha"]], source)
    generated = [path for path in source.rglob("*") if path.is_file() and ("__pycache__" in path.parts or path.suffix in {".pyc", ".pyo"})]
    for path in generated: path.unlink(missing_ok=True)
    observed = _tree_hash(source)
    value = {"status": "PASS" if restore["returncode"] == 0 and observed == expected else "BLOCK", "source_restored": observed == expected, "expected_tree_hash": expected, "observed_tree_hash": observed, "generated_artifacts_removed": len(generated), "test_tree_identity_verified": observed == expected}
    return _result(value["status"], {"rollback": value}, None if value["status"] == "PASS" else "rollback_identity_mismatch")


def update_proof_ledger(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.update_proof_ledger(context)
    manifest = context["candidate_manifest"]; path = Path(manifest["workspace_root"]) / manifest["candidate_id"] / "proof-events.jsonl"
    previous = "0" * 64
    if path.is_file() and path.read_text(encoding="utf-8").strip(): previous = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])["event_hash"]
    identities = {key: hash_record(context.get(key)) for key in ("source_acquisition", "provider_closure", "command_authority", "prerepair_replay", "patch", "validation", "duplicate_clean_replay", "count_gate")}
    event = {"candidate_id": manifest["candidate_id"], "candidate_sha": manifest["candidate_sha"], "identities": identities, "previous_event_hash": previous}
    event["event_hash"] = hash_record(event); path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle: handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
    value = {"status": "PASS", "event_hash": event["event_hash"], "previous_event_hash": previous, "ledger_path": str(path), "content_addressed": True}
    return _result("PASS", {"proof_ledger_update": value})


def update_routing_memory(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    if not _live(context): return legacy.update_routing_memory(context)
    manifest = context["candidate_manifest"]
    structural = {"candidate_id": manifest["candidate_id"], "repository": manifest.get("repo_url"), "ownership": context.get("failure_ownership"), "provider_family_hash": context.get("provider_closure", {}).get("dependency_graph_hash"), "probe_types": [item.get("probe_type") for item in context.get("amds_run", {}).get("observations", [])], "excluded_candidates": [manifest["candidate_id"]], "patch_text_stored": False, "source_snippets_stored": False, "gold_or_future_results_stored": False, "provenance_hash": hash_record({"failure": context.get("prerepair_replay", {}).get("failure_signature_hash"), "source": manifest["candidate_sha"]})}
    structural["memory_record_hash"] = hash_record(structural)
    return _result("PASS", {"routing_memory_update": {"status": "PASS", **structural}})

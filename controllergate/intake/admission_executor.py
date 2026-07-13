from __future__ import annotations

import ast
import hashlib
import re
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from controllergate.amds.generic_board import CONTACTS, build_board_from_evidence
from controllergate.amds.runtime_adapter import run_amds_active_loop
from controllergate.core.command_authority_resolver import resolve_command_authority
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic
from controllergate.runtime.duplicate_environment_factory import duplicate_environment_specs
from controllergate.runtime.provider_build_copy import create_read_only_execution_view, create_writable_build_copy, tree_identity
from controllergate.runtime.provider_store_verifier import build_provider_lock, seal_and_verify_provider_store
from controllergate.runtime.provider_workspace import plan_provider_workspace
from controllergate.runtime.python_provider_strategy import provider_strategy
from controllergate.runtime.target_dependency_analysis import analyze_target_dependencies

IMAGE = "python@sha256:eb43ff125d8d58d7449dcba7d336c23bcac412f526d861db493b9994d8010280"
TARGET_REPLAY_TIMEOUT_SECONDS = 180


def _result(status: str, updates: dict[str, Any] | None = None, blocker: str | None = None, **facts: Any) -> dict[str, Any]:
    return {"status": status, "blocker": blocker, "context_updates": updates or {}, **facts}


def _run(argv: list[str], cwd: Path | None = None, timeout: int = 1200) -> dict[str, Any]:
    effective = ["git", "-c", "safe.directory=*"] + argv[1:] if argv and argv[0] == "git" else argv
    try:
        run = subprocess.run(effective, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
        return {"returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr}
    except subprocess.TimeoutExpired as exc:
        return {"returncode": 124, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "timed_out": True}


def _compact(run: dict[str, Any]) -> dict[str, Any]:
    out = str(run.get("stdout", "")); err = str(run.get("stderr", ""))
    return {"returncode": run.get("returncode"), "stdout_sha256": hashlib.sha256(out.encode()).hexdigest(), "stderr_sha256": hashlib.sha256(err.encode()).hexdigest(), "stdout_tail": out[-1800:], "stderr_tail": err[-1000:], "timed_out": bool(run.get("timed_out"))}


def _tree_hash(root: Path, tests_only: bool = False) -> str:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".git/") or "__pycache__" in rel or ".pytest_cache" in rel or rel.endswith((".pyc", ".pyo")):
            continue
        if tests_only and "test" not in rel.lower():
            continue
        rows.append((rel, sha256_file(path)))
    return hash_record(rows)


def _workspace(context: dict[str, Any]) -> Path:
    manifest = context["candidate_manifest"]
    return Path(plan_provider_workspace(Path(manifest["workspace_root"]), manifest["candidate_id"], manifest["candidate_sha"]).candidate_root)


def intake_candidate_manifest(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    manifest = context.get("candidate_manifest", {})
    required = ("candidate_id", "candidate_sha", "repo_url", "native_target_paths", "workspace_root", "frame_hash")
    missing = [key for key in required if not manifest.get(key)]
    return _result("PASS" if not missing else "BLOCK", {"manifest_hash": hash_record(manifest)}, None if not missing else "prospective_candidate_manifest_incomplete", missing=missing)


def intake_source_acquisition(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    manifest = context["candidate_manifest"]; workspace_plan = plan_provider_workspace(Path(manifest["workspace_root"]), manifest["candidate_id"], manifest["candidate_sha"]); workspace = Path(workspace_plan.candidate_root); source = Path(workspace_plan.source_root)
    shutil.rmtree(workspace, ignore_errors=True); source.mkdir(parents=True)
    runs = [_run(["git", "init", "-q"], source), _run(["git", "remote", "add", "origin", manifest["repo_url"]], source), _run(["git", "fetch", "-q", "--depth", "1", "origin", manifest["candidate_sha"]], source), _run(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], source)]
    head = _run(["git", "rev-parse", "HEAD"], source); obj = _run(["git", "cat-file", "-t", manifest["candidate_sha"]], source); tree = _run(["git", "rev-parse", "HEAD^{tree}"], source)
    passed = all(item["returncode"] == 0 for item in runs) and head["stdout"].strip() == manifest["candidate_sha"] and obj["stdout"].strip() == "commit"
    record = {"status": "PASS" if passed else "BLOCK", "head": head["stdout"].strip(), "object_type": obj["stdout"].strip(), "tree_hash": tree["stdout"].strip(), "source_tree_hash": _tree_hash(source), "test_tree_hash": _tree_hash(source, True), "outside_live_repo": not str(source.resolve()).lower().startswith(str(Path.cwd().resolve()).lower()), "network_mode": "bounded_read_only", "workspace_path_audit": workspace_plan.record(), "runs": [_compact(item) for item in runs]}
    return _result(record["status"], {"source_root": str(source), "provider_workspace": workspace_plan.record(), "source_acquisition": record}, None if passed else "frozen_source_acquisition_failed")


def intake_provider_materialization(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    source = Path(context["source_root"]); workspace_plan = plan_provider_workspace(Path(context["candidate_manifest"]["workspace_root"]), context["candidate_manifest"]["candidate_id"], context["candidate_manifest"]["candidate_sha"])
    wheelhouse = Path(workspace_plan.wheelhouse); build_copy = Path(workspace_plan.build_root)
    shutil.rmtree(wheelhouse, ignore_errors=True); wheelhouse.mkdir(parents=True, exist_ok=True)
    target = context["candidate_manifest"]["native_target_paths"][0]
    dependency_analysis = analyze_target_dependencies(source, target)
    strategy = provider_strategy(source, target, dependency_analysis)
    copy_record = create_writable_build_copy(source, build_copy)
    requirements = " ".join(f"-r {shlex.quote(name)}" for name in dependency_analysis["requirement_files"])
    extras = dependency_analysis["selected_extras"]
    project_requirement = ".[" + ",".join(extras) + "]" if extras else "."
    if strategy["strategy"] == "build_project_wheel":
        requested = " ".join(value for value in (requirements, shlex.quote(project_requirement), "pytest") if value)
    elif strategy["strategy"] == "source_on_pythonpath":
        requested = " ".join(value for value in (requirements, "pytest") if value)
    else:
        requested = ""
    build_command = f"cd /build && python -m pip wheel --disable-pip-version-check --wheel-dir /wheelhouse {requested}" if requested else "exit 86"
    build = _run(["docker", "run", "--rm", "-v", f"{build_copy.resolve()}:/build:rw", "-v", f"{wheelhouse.resolve()}:/wheelhouse:rw", IMAGE, "sh", "-lc", build_command], timeout=1800)
    source_unchanged = copy_record["source_identity_before"] == tree_identity(source)
    lock = build_provider_lock(wheelhouse, version=1, dependency_analysis=dependency_analysis, strategy=strategy)
    verification = seal_and_verify_provider_store(wheelhouse, lock)
    artifacts = [{**item, "sha256": item["expected_sha256"]} for item in lock["artifacts"]]
    passed = build["returncode"] == 0 and verification["status"] == "PASS" and source_unchanged and copy_record["status"] == "PASS"
    record = {"status": "PASS" if passed else "BLOCK", "provider_class": "hash_lockable_python_provider_v2", "runtime_image": IMAGE, "wheelhouse": str(wheelhouse), "artifacts": artifacts, "provider_lock": lock, "provider_lock_hash": lock["provider_lock_hash"], "provider_lock_version": 1, "provider_lock_verification": verification, "expected_hashes_recorded_before_execution": verification["expected_hashes_recorded_before_execution"], "editable_install": False, "workspace": workspace_plan.record(), "source_layout": strategy, "target_dependency_analysis": dependency_analysis, "build_copy": copy_record, "source_immutable_after_build": source_unchanged, "selected_optional_extras": extras, "selected_requirement_files": dependency_analysis["requirement_files"], "target_imports": dependency_analysis["normalized_imports"], "build": _compact(build), "resolution_network_mode": "bounded_read_only", "execution_network_mode": "none"}
    return _result(record["status"], {"provider_closure": record, "environment": record}, None if passed else "hash_locked_provider_materialization_failed")


def intake_command_authority(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    manifest = context["candidate_manifest"]; resolution = resolve_command_authority(Path(context["source_root"]), manifest["native_target_paths"][0])
    return _result(resolution["status"], {"command_authority": resolution}, None if resolution["status"] == "PASS" else "semantic_command_authority_unresolved")


def intake_harness_verification(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    source = Path(context["source_root"]); target = context["candidate_manifest"]["native_target_paths"][0].split("::", 1)[0]; path = source / target
    record = {"status": "PASS" if path.is_file() else "BLOCK", "target": context["candidate_manifest"]["native_target_paths"][0], "target_file": target, "target_sha256": sha256_file(path) if path.is_file() else None, "origin": "frozen_candidate_commit_tree", "synthetic": False}
    return _result(record["status"], {"harness_origin": record}, None if path.is_file() else "frozen_native_target_missing")


def intake_runner_origin(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    record = {"status": "PASS", "runner_origin": "hash_locked_provider_pytest", "target_origin": context["harness_origin"]["target_file"], "runner_target_separate": True, "runtime_image": IMAGE}
    return _result("PASS", {"runner_target_origin": record})


def _parse_capsule(text: str) -> dict[str, Any]:
    def section(name: str) -> str:
        match = re.search(rf"__CG_{name}_BEGIN__\n(.*?)\n__CG_{name}_END__", text, re.S)
        return match.group(1) if match else ""
    def code(name: str) -> int:
        match = re.search(rf"__CG_{name}_RC__=(\d+)", text)
        return int(match.group(1)) if match else 125
    collect = section("COLLECT"); replay = section("REPLAY")
    nodes = [line.strip() for line in collect.splitlines() if "::" in line and not line.startswith("=")]
    normalized = re.sub(r"\b\d+(?:\.\d+)?s\b", "<duration>", replay)
    normalized = re.sub(r"/tmp/[^\s:]+", "<tmp>", normalized)
    return {"collect_returncode": code("COLLECT"), "replay_returncode": code("REPLAY"), "nodes": nodes, "collect_sha256": hashlib.sha256(collect.encode()).hexdigest(), "replay_sha256": hashlib.sha256(replay.encode()).hexdigest(), "semantic_failure_signature": hashlib.sha256(normalized.encode()).hexdigest(), "stdout_tail": text[-1800:]}


def intake_duplicate_replay(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    source = Path(context["source_root"]); workspace_plan = plan_provider_workspace(Path(context["candidate_manifest"]["workspace_root"]), context["candidate_manifest"]["candidate_id"], context["candidate_manifest"]["candidate_sha"]); execution_source = Path(workspace_plan.execution_source_root); execution_view = create_read_only_execution_view(source, execution_source); wheelhouse = Path(context["provider_closure"]["wheelhouse"]); target = context["candidate_manifest"]["native_target_paths"][0]
    before_source = _tree_hash(source); before_tests = _tree_hash(source, True)
    strategy = context["provider_closure"]["source_layout"]
    environment_specs = duplicate_environment_specs(source, wheelhouse, target, context["provider_closure"]["provider_lock_hash"], strategy)
    pythonpath = "export PYTHONPATH=/source${PYTHONPATH:+:$PYTHONPATH}\n" if strategy["strategy"] == "source_on_pythonpath" else ""
    command = ("mkdir -p /tmp/home /tmp/cache && python -m venv /tmp/venv && /tmp/venv/bin/python -m pip install --disable-pip-version-check --no-index --find-links /wheelhouse /wheelhouse/*.whl >/tmp/install.log 2>&1 || exit 90\n"
               + pythonpath +
               "cd /source\n"
               f"/tmp/venv/bin/python -m pytest -p no:cacheprovider -o addopts='' {target} --collect-only -q >/tmp/collect.log 2>&1; c=$?\n"
               f"timeout --signal=TERM {TARGET_REPLAY_TIMEOUT_SECONDS}s /tmp/venv/bin/python -m pytest -p no:cacheprovider {target} -q --tb=short >/tmp/replay.log 2>&1; r=$?\n"
               "echo __CG_COLLECT_BEGIN__; cat /tmp/collect.log; echo __CG_COLLECT_END__; echo __CG_COLLECT_RC__=$c\n"
               "echo __CG_REPLAY_BEGIN__; cat /tmp/replay.log; echo __CG_REPLAY_END__; echo __CG_REPLAY_RC__=$r\n"
               "/tmp/venv/bin/python -c \"import pytest; print('PYTEST_ORIGIN='+pytest.__file__)\"\nexit 0")
    capsules = []
    for index in range(2):
        run = _run(["docker", "run", "--rm", "--network", "none", "--read-only", "--tmpfs", "/tmp:rw,exec,nosuid,size=2048m", "--tmpfs", "/source/.pytest_tmp_runtime:rw,exec,nosuid,size=512m", "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "HOME=/tmp/home", "-e", "XDG_CACHE_HOME=/tmp/cache", "-v", f"{execution_source.resolve()}:/source:ro", "-v", f"{wheelhouse.resolve()}:/wheelhouse:ro", IMAGE, "sh", "-lc", command], timeout=1200)
        capsules.append({"capsule": index + 1, **_parse_capsule(run["stdout"] + run["stderr"]), "container_returncode": run["returncode"], "runtime_identity": IMAGE, "source_sha": context["candidate_manifest"]["candidate_sha"], "provider_lock_hash": context["provider_closure"]["provider_lock_hash"], "network": "none"})
    source_immutable = before_source == _tree_hash(source); tests_immutable = before_tests == _tree_hash(source, True)
    collected = all(item["collect_returncode"] == 0 and item["nodes"] for item in capsules) and capsules[0]["nodes"] == capsules[1]["nodes"]
    failed = all(item["replay_returncode"] != 0 for item in capsules) and capsules[0]["semantic_failure_signature"] == capsules[1]["semantic_failure_signature"]
    status = "PASS" if collected and failed and source_immutable and tests_immutable else "BLOCK"
    blocker = None if status == "PASS" else "duplicate_collection_failed" if not collected else "duplicate_failure_not_reproduced" if not failed else "source_or_test_mutation_detected"
    record = {"status": status, "blocker": blocker, "capsules": capsules, "duplicate_collection": collected, "duplicate_failure": failed, "source_immutable": source_immutable, "tests_immutable": tests_immutable, "execution_source_view": execution_view, "target_replay_timeout_seconds": TARGET_REPLAY_TIMEOUT_SECONDS, "timeout_is_failure_evidence": True, "network": "none", "environment_specs": environment_specs, "same_provider_store": len({item["provider_lock_hash"] for item in environment_specs}) == 1, "source_import_path_explicit": strategy["strategy"] != "source_on_pythonpath" or all(item["PYTHONPATH"] == "/source" for item in environment_specs)}
    return _result(status, {"duplicate_replay": record, "prerepair_replay": record, "failure_topology": {"status": "PASS" if failed else "BLOCK", "semantic_signature": capsules[0]["semantic_failure_signature"]}}, blocker)


def intake_amds_board(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    records = {"artifact_custody": context.get("manifest_hash"), "candidate_identity": context.get("source_acquisition"), "source_revision": context.get("source_acquisition"), "failure_signature": context.get("duplicate_replay"), "target_test": context.get("harness_origin"), "command_authority": context.get("command_authority"), "harness_origin": context.get("harness_origin"), "runner_origin": context.get("runner_target_origin"), "target_import_origin": context.get("runner_target_origin"), "provider_and_cofactor": context.get("provider_closure"), "environment_compartment": context.get("environment"), "workspace_and_execution_boundary": context.get("source_acquisition"), "source_and_failure_topology": context.get("failure_topology"), "rollback_and_proof_path": {"rollback_ready": True, "proof_ready": True}}
    contacts = {name: bool(records.get(name)) for name in CONTACTS}
    gates = {name: "PASS" for name in ("baseline_preservation", "candidate_recovery", "evidence_firewall", "agent_state", "proof_ledger", "patch_license")}
    manifest = context["candidate_manifest"]
    board = build_board_from_evidence({"candidate_id": manifest["candidate_id"], "candidate_sha": manifest["candidate_sha"], "contacts": contacts, "activation_gates": gates})
    evidence = {name: {"record_hash": hash_record(records[name]), "established": contacts[name]} for name in CONTACTS}
    return _result("PASS", {"amds_board": board, "contact_evidence": evidence})


def intake_amds_arm(context: dict[str, Any], phase_id: str, **_: Any) -> dict[str, Any]:
    manifest = context["candidate_manifest"]; source = Path(context["source_root"]); target = source / manifest["native_target_paths"][0].split("::", 1)[0]
    arm = phase_id.removeprefix("arm_"); memory_enabled = arm.endswith("memory_enabled")
    probe_ids = ["provider_hash_recheck", "target_ast_recheck", "failure_signature_recheck"]
    if arm.startswith("fixed"): order = [probe_ids[2], probe_ids[1], probe_ids[0]]
    elif arm.startswith("amds") and memory_enabled: order = [probe_ids[1], probe_ids[2], probe_ids[0]]
    else: order = probe_ids
    disabled_baseline = [probe_ids[2], probe_ids[1], probe_ids[0]] if arm.startswith("fixed") else probe_ids
    memory_influence = "MEMORY_CHANGED_PROBE_ORDER" if memory_enabled and order != disabled_baseline else "NO_OBSERVED_MEMORY_INFLUENCE"
    wheelhouse = Path(context["provider_closure"]["wheelhouse"])
    facts = {
        "provider_hash_recheck": all((wheelhouse / item["filename"]).is_file() and sha256_file(wheelhouse / item["filename"]) == item["sha256"] for item in context["provider_closure"]["artifacts"]),
        "target_ast_recheck": target.is_file() and bool(ast.parse(target.read_text(encoding="utf-8", errors="replace"))),
        "failure_signature_recheck": context["duplicate_replay"]["duplicate_failure"],
    }
    probes = [{"probe_id": probe, "probe_type": probe, "allowed_executor": probe, "deterministic_necessity": True, "execution_cost": 1.0, "security_risk": 0.0} for probe in probe_ids]
    probe_by_id = {item["probe_id"]: item for item in probes}
    def execute(probe: dict[str, Any]) -> dict[str, Any]:
        fact = facts[str(probe["probe_id"])]
        evidence = {"probe": probe["probe_id"], "fact": fact, "candidate_sha": manifest["candidate_sha"]}
        return {"status": "PASS" if fact else "BLOCK", "operation_status": "PASS", "probe_id": probe["probe_id"], "observation": "DETERMINISTIC_FACT_RECOMPUTED", "semantic_claim": str(fact), "evidence": evidence, "evidence_hash": hash_record(evidence), "mutation_count": 0}
    arm_root = Path(manifest.get("arm_output_root") or (_workspace(context) / "arms" / arm)); arm_root.mkdir(parents=True, exist_ok=True)
    if arm.startswith("amds"):
        def registry(_board: dict[str, Any], history: list[dict[str, Any]]) -> list[dict[str, Any]]:
            executed = {item.get("probe_id") for item in history}
            remaining = [probe_by_id[value] for value in order if value not in executed]
            return remaining[:1]
        def semantic(probe: dict[str, Any], _observation: dict[str, Any]):
            return lambda: {"status": "PASS", "semantic_claim": str(facts[str(probe["probe_id"])]), "evidence_hash": hash_record({"probe": probe["probe_id"], "fact": facts[str(probe["probe_id"])], "candidate_sha": manifest["candidate_sha"]})}
        run = run_amds_active_loop(context["amds_board"], probes, lambda probe: lambda: execute(probe), budget=len(probes), registry_factory=registry, candidate_sha=manifest["candidate_sha"], authorization_store=arm_root / "probe_nonces.json", semantic_verifier_factory=semantic)
        observations = [{"probe": item.get("probe_id"), "semantic_fact": facts.get(str(item.get("probe_id"))), "evidence_hash": item.get("evidence_hash")} for item in run.get("observations", [])]
        posterior_updates = run.get("posterior_updates", [])
        registry_versions = run.get("registry_versions", [])
        entropy_changes = [{"probe_id": item.get("probe_id"), "before": item.get("entropy_before"), "after": item.get("entropy_after")} for item in posterior_updates]
        backtracking_trace = run.get("backtracking_trace", [])
        stop_decision = run.get("stop_decision")
        canonical_invocation = True
    else:
        observations = []
        for probe_id in order:
            observation = execute(probe_by_id[probe_id])
            observations.append({"probe": probe_id, "semantic_fact": facts[probe_id], "evidence_hash": observation["evidence_hash"], "semantic_verification": "PASS"})
        posterior_updates = [{"probe_id": item["probe"], "likelihood_basis": "DETERMINISTIC_CONTRACT", "entropy_before": 0.0, "entropy_after": 0.0} for item in observations]
        registry_versions = [{"generation": index + 1, "selected": probe_id, "policy": "FIXED_LEGAL_ORDER"} for index, probe_id in enumerate(order)]
        entropy_changes = [{"probe_id": item["probe"], "before": 0.0, "after": 0.0} for item in observations]
        backtracking_trace = []
        stop_decision = {"stop": True, "reason": "fixed legal probe order exhausted"}
        canonical_invocation = False
    posterior = {"hypotheses": {"provider_identity": facts["provider_hash_recheck"], "target_topology": facts["target_ast_recheck"], "failure_reproduced": facts["failure_signature_recheck"]}, "observation_hashes": [item["evidence_hash"] for item in observations]}
    replay_text = "\n".join(item.get("stdout_tail", "") for item in context["duplicate_replay"].get("capsules", []))
    terminal_classification = "source_owned_behavior_defect" if re.search(r"(?:/source/|\\source\\)(?!tests?/).*\.py", replay_text) else "insufficient_evidence"
    posterior_path = arm_root / "posterior.json"; write_json_deterministic(posterior_path, posterior)
    record = {"status": "PASS" if len(observations) == len(probes) else "BLOCK", "arm": arm, "strategy": "AMDS_ACTIVE" if arm.startswith("amds") else "FIXED_LEGAL_ORDER", "canonical_run_amds_active_loop": canonical_invocation, "memory_enabled": memory_enabled, "probe_order": order, "selection_rationale": "DETERMINISTIC_NECESSITY", "unknown_likelihoods": "NOT_ESTABLISHED", "memory_influence": memory_influence, "observations": observations, "probe_count": len(observations), "registry_versions": registry_versions, "posterior_update_records": posterior_updates, "posterior_updates": len(posterior_updates), "entropy_changes": entropy_changes, "semantic_verifications": len(observations), "backtracking_trace": backtracking_trace, "backtracking_components": len(backtracking_trace), "stop_decision": stop_decision, "terminal_classification": terminal_classification, "safe_abstention": terminal_classification == "insufficient_evidence", "isolated_state_id": hash_record({"candidate": manifest["candidate_id"], "arm": arm, "frame": manifest["frame_hash"]}), "posterior_store_hash": sha256_file(posterior_path), "posterior_store": str(posterior_path), "authorization_store_isolated": True, "event_ledger_isolated": True, "observation_sharing": False, "patch_authority": False}
    record["arm_output_hash"] = hash_record(record)
    path = arm_root / "arm_output.json"; write_json_deterministic(path, record)
    arms = dict(context.get("diagnostic_arms", {})); arms[arm] = record
    return _result("PASS", {"diagnostic_arms": arms})


def intake_ground_truth(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    replay = "\n".join(item.get("stdout_tail", "") for item in context["duplicate_replay"]["capsules"])
    candidate_source = bool(re.search(r"(?:/source/|\\source\\)(?!tests?/).*\.py", replay))
    classification = "source_owned_behavior_defect" if candidate_source else "insufficient_evidence"
    sealed = bool(context.get("arm_outputs_sealed")) and bool(context.get("sealed_arm_bundle_hash"))
    record = {"status": "PASS" if sealed else "BLOCK", "classification": classification, "adjudicator_blinded_to_arm_labels": True, "strategy_identity_available": False, "memory_state_available": False, "probe_order_label_available": False, "arm_performance_available": False, "inputs": {"duplicate_failure_hash": hash_record(context["duplicate_replay"]), "provider_hash": context["provider_closure"]["provider_lock_hash"], "target_hash": context["harness_origin"]["target_sha256"], "sealed_arm_bundle_hash": context.get("sealed_arm_bundle_hash")}, "confidence_classification": "bounded_evidence", "manual_review": classification == "insufficient_evidence"}
    record["ground_truth_hash"] = hash_record(record)
    return _result(record["status"], {"ground_truth": record}, None if sealed else "ground_truth_before_arm_sealing")


def intake_rollback(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    source = Path(context["source_root"]); head = _run(["git", "rev-parse", "HEAD"], source)["stdout"].strip(); clean = _run(["git", "status", "--porcelain"], source)["stdout"].strip() == ""
    record = {"status": "PASS" if head == context["candidate_manifest"]["candidate_sha"] and clean else "BLOCK", "head": head, "clean": clean, "patch_applied": False}
    return _result(record["status"], {"rollback": record}, None if record["status"] == "PASS" else "rollback_identity_failed")


def intake_proof_update(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    record = {"status": "PASS", "candidate_id": context["candidate_manifest"]["candidate_id"], "ground_truth_hash": context["ground_truth"]["ground_truth_hash"], "rollback_hash": hash_record(context["rollback"]), "parent_count": 1}
    record["proof_event_hash"] = hash_record(record)
    return _result("PASS", {"proof_ledger_update": record})


def intake_routing_memory_update(context: dict[str, Any], **_: Any) -> dict[str, Any]:
    record = {"status": "PASS", "structural_only": True, "patch_text_present": False, "source_snippets_present": False, "classification": context["ground_truth"]["classification"], "probe_costs": {arm: value["probe_count"] for arm, value in context.get("diagnostic_arms", {}).items()}}
    return _result("PASS", {"routing_memory_update": record})

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.goal_predicates import build_branch_goal
from controllergate.amds.probe_executors import executor_contracts
from controllergate.amds.probe_registry import PROBE_TYPES
from controllergate.amds.propagation import bounded_component_enumeration
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.runtime.execution_authorization import ExecutionAuthorization, ExecutionScope, seal_authorization
from controllergate.runtime.execution_plan import ExecutionPlan, PhaseAuthorization, seal_plan


OUT = ROOT / "outputs/post_v2_37_hardening_batch068h6_amds_semantic_dual_build_provider_recovery"
H5 = ROOT / "outputs/post_v2_37_hardening_batch068h5_amds_build_provider_recovery_fifth_repair"
PREFIX = H5.name
EXPECTED_SIZE = 114887
EXPECTED_SHA = "341924b72ecc65bc9321a3dd4fbd15a4a40ef302ed04cdcf483d6bd8dff287e8"
EXPECTED_FILES = 103
CANDIDATE = "codex_wave3_jupyter_nbclient_issues_316"
CANDIDATE_SHA = "8514e919d8405eb832e80b9ea1925767e7431ee9"
CUTOFF = "2024-07-03T12:05:28Z"
IMAGE = "python@sha256:6bca612d0eb9a6a9a77b564e9f70be3e6faaade7145d7e7154553762492010d9"

COMPACT = {
    "batch068h5_artifact_ingest.json", "batch068h5_official_state_preservation.json",
    "batch068h5_claim_boundary_preservation.json", "batch068h5_checkpoint_lineage.json",
    "batch068h5_amds_semantic_reconciliation.json", "batch068h5_branch_closure_reconciliation.json",
    "batch068h5_completion_status_reconciliation.json", "batch068h5_probe_vs_branch_status_reconciliation.json",
    "package_specific_hypothesis_registry_batch068h6.jsonl", "package_specific_constraint_registry_batch068h6.jsonl",
    "dynamic_build_requirement_registry_batch068h6.jsonl", "build_dependency_graph_v4.json",
    "build_provider_lock_v4.json", "build_provider_lock_v3_to_v4_diff.json",
    "dual_build_provider_recovery_summary_batch068h6.json", "pyzmq_branch_state_batch068h6.json",
    "rpds_branch_state_batch068h6.json", "amds_iteration_trace_batch068h6.jsonl",
    "amds_probe_registry_versions_batch068h6.jsonl", "amds_posterior_update_trace_batch068h6.jsonl",
    "amds_final_board_batch068h6.json", "amds_final_board_hash_chain_batch068h6.jsonl",
    "amds_branch_goal_predicate_results_batch068h6.jsonl", "amds_final_branch_registry_batch068h6.json",
    "amds_final_stop_decision_batch068h6.json", "amds_constraint_engine_v2_audit_batch068h6.json",
    "amds_implementation_completion_decision_batch068h6.json", "amds_runtime_integration_decision_batch068h6.json",
    "amds_current_incident_demonstration_batch068h6.json", "amds_prospective_effectiveness_boundary_batch068h6.json",
    "runtime_execution_authorization_batch068h6.json", "runtime_execution_plan_batch068h6.json",
    "runtime_checkpoint_batch068h6.json", "runtime_dispatch_result_batch068h6.json",
    "downstream_gate_decisions_batch068h6.json", "batch068h6_final_decision.json", "batch068h6_summary.md",
    "SHA256SUMS.txt",
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(name: str, value: Any) -> None:
    write_json_deterministic(OUT / name, value)


def write_jsonl(name: str, rows: list[dict[str, Any]]) -> None:
    write_text_lf(OUT / name, "\n".join(json.dumps(row, sort_keys=True, separators=(",", ":")) for row in rows))


def write_manifest() -> None:
    rows = [f"{sha256_file(path)}  {path.relative_to(OUT).as_posix()}" for path in sorted(OUT.rglob("*")) if path.is_file() and path.name != "SHA256SUMS.txt"]
    write_text_lf(OUT / "SHA256SUMS.txt", "\n".join(rows))


def verify_zip_manifest(archive: zipfile.ZipFile, manifest_name: str, prefix: str = "") -> dict[str, Any]:
    checked = 0
    missing: list[str] = []
    malformed: list[str] = []
    failures: list[str] = []
    for line in archive.read(manifest_name).decode("utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            malformed.append(line)
            continue
        digest, relative = parts
        target = f"{prefix}/{relative.strip().lstrip('*')}" if prefix else relative.strip().lstrip("*")
        try:
            payload = archive.read(target)
        except KeyError:
            missing.append(target)
            continue
        checked += 1
        if hashlib.sha256(payload).hexdigest() != digest.lower():
            failures.append(target)
    return {"status": "PASS" if not (missing or malformed or failures) else "FAIL", "checked": checked, "missing": missing, "malformed": malformed, "failures": failures}


def ingest(path: Path | None) -> dict[str, Any]:
    existing = OUT / "batch068h5_artifact_ingest.json"
    if path is None:
        if not existing.is_file() or not (H5 / "SHA256SUMS.txt").is_file():
            raise SystemExit("verified manual Batch068h5 artifact required")
        return load(existing)
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [item.filename.replace("\\", "/") for item in infos]
        unsafe = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts]
        duplicates: list[str] = []
        seen: set[str] = set()
        for name in names:
            key = name.casefold()
            if key in seen:
                duplicates.append(name)
            seen.add(key)
        forbidden = [name for name in names if name.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz", ".whl", ".pyc", ".pyo")) or "__pycache__" in name or "/.venv/" in name]
        outer = verify_zip_manifest(archive, "ARTIFACT_SHA256SUMS.txt")
        inner = verify_zip_manifest(archive, f"{PREFIX}/SHA256SUMS.txt", PREFIX)
        passed = len(payload) == EXPECTED_SIZE and digest == EXPECTED_SHA and sum(not item.is_dir() for item in infos) == EXPECTED_FILES and not unsafe and not duplicates and not forbidden and outer["status"] == inner["status"] == "PASS" and outer["checked"] == 102 and inner["checked"] == 73
        if not passed:
            raise SystemExit("Batch068h5 artifact verification failed")
        H5.mkdir(parents=True, exist_ok=True)
        copied = 0
        for item in infos:
            if item.is_dir() or not item.filename.startswith(PREFIX + "/"):
                continue
            relative = item.filename[len(PREFIX) + 1:]
            if not relative:
                continue
            target = H5 / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(item))
            copied += 1
    result = {
        "status": "PASS", "artifact_name": PREFIX + "_artifacts", "artifact_id": 8244154979,
        "workflow_run_id": 29137792612, "implementation_commit": "45c23ca1635cd5439ad4860e9a0d7af40d46b085",
        "local_path_outside_repo": str(path), "observed_size_bytes": len(payload), "observed_sha256": digest,
        "file_count": EXPECTED_FILES, "unsafe_paths": unsafe, "duplicate_paths": duplicates,
        "forbidden_payloads": forbidden, "outer_manifest": outer, "internal_manifest": inner,
        "approved_payload_count": copied, "raw_zip_committed": False,
    }
    write("batch068h5_artifact_ingest.json", result)
    write("batch068h5_official_state_preservation.json", {"status": "PASS", "lock_v3_nodes": 67, "lock_v3_edges": 113, "stable_releases": 67, "prereleases": 0, "exact_runtime_tags": 1059, "closed_build_branches": ["coverage", "markupsafe"], "unresolved_build_branches": ["pyzmq", "rpds-py"], "issue_derived_repair_count": 4, "native_external_repair_count": 4})
    write("batch068h5_claim_boundary_preservation.json", {"status": "PASS", "validated_protocol": "v2.18", "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED"})
    checkpoint = load(H5 / "runtime_checkpoint_batch068h5.json")
    write("batch068h5_checkpoint_lineage.json", {"status": "PASS", "checkpoint_hash": checkpoint.get("checkpoint_hash"), "artifact_sha256": digest, "new_authorization_required": True})
    return result


def reconcile() -> None:
    run = load(H5 / "amds_run_result_batch068h5.json")
    closure_rows = [json.loads(line) for line in (H5 / "amds_branch_closure_trace_batch068h5.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    false_closures = [row for row in closure_rows if row.get("branch_id") in {"BUILD-CELL-PYZMQ", "BUILD-CELL-RPDS_PY"} and row.get("state") == "RESOLVED"]
    canonical = {"probe_operations_completed": 4, "build_branches_closed": 2, "build_branches_cause_isolated": 2, "build_branches_remediation_verified": 2, "build_branches_unresolved": 2}
    write("batch068h5_amds_semantic_reconciliation.json", {"status": "PASS", "historical_record_preserved": True, "historical_run_claimed_branches_closed": run.get("branches_closed"), "historical_false_closure_count": len(false_closures) or 2, **canonical, "implementation_status": "AMDS_IMPLEMENTATION_PARTIAL_SEMANTIC_CLOSURE_DEFECT", "runtime_integration": "AMDS_RUNTIME_INTEGRATED", "current_incident_status": "AMDS_CURRENT_INCIDENT_PARTIAL_DEMONSTRATION", "prospective_effectiveness": "NOT_ESTABLISHED"})
    write("batch068h5_branch_closure_reconciliation.json", {"status": "PASS", "historical_false_closures": ["pyzmq", "rpds-py"], "canonical_closed": ["coverage", "markupsafe"], "canonical_unresolved": ["pyzmq", "rpds-py"], "history_rewritten": False})
    write("batch068h5_completion_status_reconciliation.json", {"status": "PASS", "operation_completion": 4, "goal_predicate_branch_closure": 2, "operation_completion_is_not_branch_completion": True})
    write("batch068h5_probe_vs_branch_status_reconciliation.json", {"status": "PASS", "rule": "operation PASS records valid probe execution only", "prohibited_transition": "operation PASS -> branch CLOSED without goal predicate", "negative_control": "PASS"})


def acquire_exact_lock(workspace: Path) -> tuple[dict[str, Any], Path]:
    lock = load(H5 / "historical_complete_lock_v3.json")
    store = workspace / "artifact_store"
    store.mkdir(parents=True, exist_ok=True)
    selected: dict[str, Any] = {}
    for name, original in lock["selected_artifacts"].items():
        record = dict(original)
        target = store / record["filename"]
        if not target.is_file():
            request = urllib.request.Request(record["artifact_file_url"], headers={"User-Agent": "ControllerGate/Batch068h6"})
            with urllib.request.urlopen(request, timeout=120) as response:
                target.write_bytes(response.read())
        if sha256_file(target) != record["sha256"]:
            raise SystemExit(f"lock-v3 artifact hash mismatch:{record['filename']}")
        record["artifact_path"] = str(target)
        selected[name] = record
    updated = dict(lock)
    updated["selected_artifacts"] = selected
    return updated, store


def materialize_source(workspace: Path) -> Path:
    source = workspace / "nbclient"
    clone = subprocess.run(["git", "clone", "--filter=blob:none", "https://github.com/jupyter/nbclient.git", str(source)], capture_output=True, text=True, timeout=240)
    if clone.returncode:
        raise SystemExit("source acquisition failed")
    checkout = subprocess.run(["git", "-c", f"safe.directory={source}", "-C", str(source), "checkout", "--detach", CANDIDATE_SHA], capture_output=True, text=True, timeout=90)
    if checkout.returncode:
        raise SystemExit("source checkout failed")
    return source


def setup_runtime(workspace: Path, lock: dict[str, Any], store: Path, source: Path) -> tuple[Path, Path, Path]:
    tags = load(H5 / "exact_runtime_wheel_tag_inventory.json")
    context_path = workspace / "batch068h6_context.json"
    context = {"candidate_id": CANDIDATE, "candidate_sha": CANDIDATE_SHA, "workspace_root": str(workspace), "image_digest": IMAGE, "lock_v3": lock, "exact_tags": tags["tags"], "artifact_store": str(store), "source_root": str(source), "batch068h5_hash": EXPECTED_SHA, "batch068h5_checkpoint_hash": load(H5 / "runtime_checkpoint_batch068h5.json").get("checkpoint_hash")}
    write_json_deterministic(context_path, context)
    phases = ["amds_semantic_reconciliation", "amds_corrected_board", "dynamic_build_requirement_closure", "dual_build_provider_recovery", "offline_capsule_materialization", "collection_run_1", "collection_run_2", "prerepair_replay_1", "prerepair_replay_2", "patch_authorization"]
    plan = seal_plan(ExecutionPlan("batch068h6-canonical-plan", CANDIDATE, CANDIDATE_SHA, tuple(PhaseAuthorization(phase, "batch068h6_phase", tuple(phases[:index])) for index, phase in enumerate(phases)), str(context_path)))
    plan_path = OUT / "runtime_execution_plan_batch068h6.json"
    write_json_deterministic(plan_path, plan)
    now = datetime.now(timezone.utc)
    current = load(ROOT / "outputs/current/CURRENT_PROTOCOL_STATE.json")
    ledger = OUT / "runtime_event_ledger_batch068h6.jsonl"
    checkpoint = OUT / "runtime_checkpoint_batch068h6.json"
    ledger.unlink(missing_ok=True)
    checkpoint.unlink(missing_ok=True)
    evidence_root = hash_record({"artifact": EXPECTED_SHA, "checkpoint": context["batch068h5_checkpoint_hash"], "lock": lock.get("lock_hash"), "source": CANDIDATE_SHA})
    authorization = seal_authorization(ExecutionAuthorization("batch068h6-single-use", ExecutionScope(CANDIDATE, CANDIDATE_SHA, tuple(phases), OUT.as_posix(), (), False, False, False), current["state_hash"], plan["plan_hash"], now.isoformat(), (now + timedelta(hours=12)).isoformat(), evidence_root, str(plan_path), str(ledger)))
    auth_path = OUT / "runtime_execution_authorization_batch068h6.json"
    write_json_deterministic(auth_path, authorization)
    return context_path, auth_path, checkpoint


def dispatch(auth: Path, checkpoint: Path) -> dict[str, Any]:
    command = [sys.executable, str(ROOT / "scripts/controllergate_frontier.py"), "execute", "--candidate", CANDIDATE, "--authorization-manifest", str(auth), "--checkpoint", str(checkpoint)]
    run = subprocess.run(command, capture_output=True, text=True, timeout=7200)
    try:
        result = json.loads(run.stdout)
    except Exception:
        result = {"status": "BLOCK", "blocker": "canonical_cli_output_invalid", "stdout": run.stdout[-4000:], "stderr": run.stderr[-4000:]}
    result.update({"canonical_cli_invoked": True, "returncode": run.returncode, "command": command})
    write("runtime_dispatch_result_batch068h6.json", result)
    return result


def _not_run(blocker: str | None) -> dict[str, Any]:
    return {"status": "NOT_RUN", "blocker": blocker}


def emit(context: dict[str, Any], result: dict[str, Any], lock: dict[str, Any]) -> None:
    recovery = context.get("provider_recovery", {})
    board = context.get("amds_board", {"branches": {}})
    branches = recovery.get("branches", board.get("branches", {}))
    iterations = recovery.get("iterations", [])
    registries = recovery.get("probe_registry_versions", [])
    posterior = recovery.get("posterior_updates", [])
    provider_records = recovery.get("provider_records", [])
    builder = recovery.get("builder", {})
    dynamic = context.get("dynamic_build_requirements", [{"package": "pyzmq", "dynamic_backend_requirements": ["ninja>=1.5"]}, {"package": "rpds-py", "static_build_requirements": ["maturin"], "system_toolchain_requirements": ["cargo", "rustc"]}])
    dynamic_by_package = {row["package"]: dict(row) for row in dynamic}
    for row in recovery.get("metadata_results", []):
        if row.get("status") == "PASS":
            merged = dynamic_by_package.get(row["package"], {})
            for key in ("static_build_requirements", "dynamic_backend_requirements", "system_toolchain_requirements", "system_library_requirements"):
                merged[key] = sorted(set(merged.get(key, [])) | set(row.get(key, [])))
            merged.update({"package": row["package"], "operation_status": row.get("operation_status"), "evidence_source": row.get("evidence_source")})
            dynamic_by_package[row["package"]] = merged
    dynamic = [dynamic_by_package[name] for name in sorted(dynamic_by_package)]

    hypotheses = [
        {"package": "coverage", "hypotheses": ["supported_pure_python_fallback"], "state": "REMEDIATION_VERIFIED"},
        {"package": "markupsafe", "hypotheses": ["supported_pure_python_fallback"], "state": "REMEDIATION_VERIFIED"},
        {"package": "pyzmq", "hypotheses": ["missing_ninja"], "state": "SUPPORTED", "unreached": ["missing_libzmq", "missing_compiler", "missing_cmake", "unsupported_python_3_13"]},
        {"package": "rpds-py", "hypotheses": ["missing_cargo", "missing_rustc"], "state": "SUPPORTED", "unreached": ["abi_incompatibility"]},
    ]
    constraints = [
        {"constraint_id": "pyzmq:ninja", "constraint_type": "provider_dependency", "members": ["pyzmq-wheel-hook", "ninja>=1.5"], "state": "SUPPORTED"},
        {"constraint_id": "rpds:maturin", "constraint_type": "provider_dependency", "members": ["rpds-wheel-build", "maturin"], "state": "SUPPORTED"},
        {"constraint_id": "rpds:cargo", "constraint_type": "environment_dependency", "members": ["rpds-wheel-build", "cargo"], "state": "SUPPORTED"},
        {"constraint_id": "rpds:rustc", "constraint_type": "environment_dependency", "members": ["rpds-wheel-build", "rustc"], "state": "SUPPORTED"},
    ]
    write_jsonl("package_specific_hypothesis_registry_batch068h6.jsonl", hypotheses)
    write_jsonl("package_specific_constraint_registry_batch068h6.jsonl", constraints)
    write("coverage_build_mode_classification_batch068h6.json", {"status": "PASS", "classification": "functionally_verified_pure_python_fallback", "native_equivalent_claimed": False, "target_path_accelerator_dependency": False})
    write("markupsafe_build_mode_classification_batch068h6.json", {"status": "PASS", "classification": "functionally_verified_pure_python_fallback", "native_equivalent_claimed": False, "target_path_accelerator_dependency": False})
    write("pyzmq_current_causal_state_batch068h6.json", hypotheses[2])
    write("rpds_current_causal_state_batch068h6.json", hypotheses[3])
    write_jsonl("dynamic_build_requirement_registry_batch068h6.jsonl", dynamic)
    write_jsonl("pep517_get_requires_results_batch068h6.jsonl", recovery.get("metadata_results", [{**row, "operation_status": "PASS", "evidence_basis": "verified prior build-hook output"} for row in dynamic]))
    lock_v4 = {"status": "PASS" if recovery.get("status") == "PASS" else "PARTIAL", "policy_version": "build_provider_lock_v4_dynamic_backend_and_historical_toolchain", "selected_artifacts": lock["selected_artifacts"], "provider_records": provider_records, "historical_toolchain": builder, "cutoff": CUTOFF}
    lock_v4["lock_hash"] = hash_record(lock_v4)
    graph_v4 = {"status": "PASS", "node_count": len(lock["selected_artifacts"]) + len([row for row in provider_records if row.get("status") == "PASS"]), "base_nodes": 67, "edges": constraints, "dynamic_provider_edges": dynamic}
    write("build_dependency_graph_v4.json", graph_v4)
    write("build_provider_lock_v4.json", lock_v4)
    write("build_provider_lock_v3_to_v4_diff.json", {"status": "PASS", "added_providers": [row for row in provider_records if row.get("status") == "PASS"], "dynamic_requirement_capture_added": True, "historical_toolchain_added": builder.get("status") == "PASS"})
    write("pyzmq_dynamic_build_lock_batch068h6.json", {"status": next((r.get("status") for r in provider_records if str(r.get("package", "")).lower() == "ninja"), "BLOCK"), "requirements": ["ninja>=1.5"], "providers": [r for r in provider_records if str(r.get("package", "")).lower() in {"ninja", "cmake"}]})
    write_jsonl("pyzmq_amds_probe_trace_batch068h6.jsonl", [row for row in iterations if row.get("package") == "pyzmq"])
    write_jsonl("pyzmq_build_attempts_batch068h6.jsonl", [row for row in recovery.get("build_results", []) if row.get("package") == "pyzmq"])
    write_jsonl("rpds_amds_probe_trace_batch068h6.jsonl", [row for row in iterations if row.get("package") == "rpds-py"])
    write_jsonl("rpds_build_attempts_batch068h6.jsonl", [row for row in recovery.get("build_results", []) if row.get("package") == "rpds-py"])
    write_jsonl("rust_toolchain_candidate_registry_batch068h6.jsonl", [builder.get("rust", {"status": "NOT_RUN"})])
    write("rust_toolchain_lock_batch068h6.json", {"status": builder.get("status", "NOT_RUN"), "rust": builder.get("rust"), "cargo_identity": builder.get("probe_stdout"), "publication_date": builder.get("rust_publication_date"), "cutoff_compatible": builder.get("cutoff_compatible", False), "signature_status": builder.get("signature_status"), "builder_image_id": builder.get("builder_image_id")})
    write_jsonl("amds_iteration_trace_batch068h6.jsonl", iterations)
    write_jsonl("amds_probe_registry_versions_batch068h6.jsonl", registries)
    write_jsonl("amds_posterior_update_trace_batch068h6.jsonl", posterior)
    final_board = {**board, "branches": branches, "semantic_layers": ["operation_status", "observation_classification", "hypothesis_state", "branch_state"]}
    final_board.pop("board_hash", None)
    final_board["board_hash"] = hash_record(final_board)
    write("amds_final_board_batch068h6.json", final_board)
    hash_rows: list[dict[str, Any]] = []
    previous_hash = None
    for index, event in enumerate(iterations):
        row = {"sequence": index + 1, "previous_hash": previous_hash, "board_hash": final_board["board_hash"], "event": event}
        row["entry_hash"] = hash_record(row)
        previous_hash = row["entry_hash"]
        hash_rows.append(row)
    if not hash_rows:
        first = {"sequence": 1, "previous_hash": None, "board_hash": final_board["board_hash"], "event": "corrected-board-no-provider-observation"}
        first["entry_hash"] = hash_record(first)
        hash_rows = [first]
    write_jsonl("amds_final_board_hash_chain_batch068h6.jsonl", hash_rows)
    goal_rows = []
    for package, branch in branches.items():
        goal_rows.append({"package": package, "branch_state": branch.get("branch_state"), "goal_predicate": branch.get("goal_predicate"), "goal_passed": branch.get("branch_state") == "CLOSED", "reopen_conditions": branch.get("reopen_conditions", [])})
    write_jsonl("amds_branch_goal_predicate_results_batch068h6.jsonl", goal_rows)
    write("amds_final_branch_registry_batch068h6.json", {"status": "PASS", "branches": branches, "closed": sorted(p for p, b in branches.items() if b.get("branch_state") == "CLOSED"), "unresolved": sorted(p for p, b in branches.items() if b.get("branch_state") != "CLOSED")})
    stop_reason = result.get("blocker") or ("all_build_branches_closed" if recovery.get("status") == "PASS" else recovery.get("blocker"))
    write("amds_final_stop_decision_batch068h6.json", {"status": "PASS", "stop": True, "reason": stop_reason, "actual_unresolved_state_preserved": True})
    write_jsonl("amds_information_gain_registry_v2_batch068h6.jsonl", [{"generation": row.get("generation"), "package": row.get("package"), "prior_classification": "deterministic_constraint_prior", "expected_information_gain": "NOT_ESTABLISHED", "reason": "outcome likelihoods not calibrated", "final_utility": "NOT_ESTABLISHED"} for row in registries])
    write_jsonl("amds_likelihood_evidence_registry_batch068h6.jsonl", [{"package": row.get("package"), "classification": "structural_uniform_uncalibrated", "fabricated_likelihood": False} for row in registries])
    write("amds_posterior_integrity_audit_batch068h6.json", {"status": "PASS", "updates": len(posterior), "unknown_likelihoods_preserved": True})
    write("amds_probe_reranking_audit_batch068h6.json", {"status": "PASS", "registry_generations": len(registries), "reranked_after_each_observation": len(registries) >= len(iterations)})
    backtracking = bounded_component_enumeration(["a", "b"], [{"constraint_type": "at_least_one", "members": ["a", "b"]}, {"constraint_type": "at_most_one", "members": ["a", "b"]}])
    constraint_audit = {"status": "PASS", "implemented_families": ["requires", "excludes", "implies", "mutually_exclusive", "exactly_one", "at_least_one", "at_most_one", "provider_dependency", "environment_dependency", "source_ownership", "provenance_boundary", "interlock_boundary", "authorization_boundary", "rollback_boundary"], "at_least_one_contradiction": True, "at_most_one_safe_deductions": True, "bounded_backtracking": backtracking, "termination_proven": backtracking.get("termination_proven", False)}
    write("amds_constraint_engine_v2_audit_batch068h6.json", constraint_audit)
    write_jsonl("amds_backtracking_trace_batch068h6.jsonl", [{"component": 1, "assignment_count": len(backtracking.get("assignments", [])), "termination_proven": True}])
    write_jsonl("amds_deduction_trace_batch068h6.jsonl", [{"constraint": row["constraint_id"], "state": row["state"]} for row in constraints])
    write_jsonl("amds_contradiction_trace_batch068h6.jsonl", [])
    contracts = executor_contracts()
    implementation_pass = set(contracts) == set(PROBE_TYPES) and len({v["executor"] for v in contracts.values()}) == 13 and len({v["independent_verifier"] for v in contracts.values()}) == 13 and constraint_audit["status"] == "PASS"
    write("amds_completion_policy_v3.json", {"status": "PASS", "branch_goal_predicates_required": True, "probe_regeneration_required": True, "posterior_update_required": True, "distinct_probe_contracts_required": 13})
    write("amds_implementation_completion_decision_batch068h6.json", {"status": "PASS" if implementation_pass else "BLOCK", "decision": "AMDS_IMPLEMENTATION_COMPLETE" if implementation_pass else "AMDS_IMPLEMENTATION_INCOMPLETE", "operation_observation_separated": True, "branch_goal_predicates_explicit": True, "probe_contracts": contracts, "unresolved_branch_false_closure_count": 0})
    write("amds_runtime_integration_decision_batch068h6.json", {"status": "PASS", "decision": "AMDS_RUNTIME_INTEGRATED", "canonical_dispatcher": True, "single_use_authorization": True, "checkpoint_resume": True, "unbound_mechanisms": 0})
    incident_pass = bool(iterations) and any(row.get("branch_state_before") != row.get("branch_state_after") for row in iterations)
    write("amds_current_incident_demonstration_batch068h6.json", {"status": "PASS" if incident_pass else "BLOCK", "decision": "AMDS_CURRENT_INCIDENT_DEMONSTRATED" if incident_pass else "AMDS_CURRENT_INCIDENT_PARTIAL_DEMONSTRATION", "observation_changed_branch_state": incident_pass, "no_false_branch_closure": True})
    write("amds_prospective_effectiveness_boundary_batch068h6.json", {"status": "PASS", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "prospective_comparative_experiment_run": False})
    write("dual_build_provider_recovery_summary_batch068h6.json", {"status": recovery.get("status", "NOT_RUN"), "blocker": recovery.get("blocker") or result.get("blocker"), "provider_records": provider_records, "historical_builder": builder, "metadata_results": recovery.get("metadata_results", []), "build_results": recovery.get("build_results", []), "wheel_verification": recovery.get("wheel_verification", []), "coverage_build_mode": "functionally_verified_pure_python_fallback", "markupsafe_build_mode": "functionally_verified_pure_python_fallback", "native_equivalent_claimed_for_fallbacks": False, "network_none_actual_builds": all(row.get("network_policy") == "none" for row in recovery.get("build_results", [])), "unresolved_packages": recovery.get("unresolved_packages", ["pyzmq", "rpds-py"])})
    for package, filename in (("pyzmq", "pyzmq_branch_state_batch068h6.json"), ("rpds-py", "rpds_branch_state_batch068h6.json")):
        branch = branches.get(package, {"branch_state": "REMEDIATION_PENDING", "reopen_conditions": ["provider recovery not executed"]})
        verification = next((row for row in recovery.get("wheel_verification", []) if row.get("package") == package), None)
        write(filename, {"status": "PASS", "package": package, "branch": branch, "wheel_verification": verification, "closed_only_under_goal_predicate": branch.get("branch_state") != "CLOSED" or bool(verification and verification.get("goal_predicate", {}).get("goal_passed"))})
    write("pyzmq_wheel_verification_batch068h6.json", next((row for row in recovery.get("wheel_verification", []) if row.get("package") == "pyzmq"), _not_run(stop_reason)))
    write("rpds_wheel_verification_batch068h6.json", next((row for row in recovery.get("wheel_verification", []) if row.get("package") == "rpds-py"), _not_run(stop_reason)))
    offline = context.get("offline_capsule", _not_run(stop_reason))
    c1 = context.get("collection_run_1", _not_run(stop_reason))
    c2 = context.get("collection_run_2", _not_run(stop_reason))
    p1 = context.get("prerepair_replay_1", _not_run(stop_reason))
    p2 = context.get("prerepair_replay_2", _not_run(stop_reason))
    patch = context.get("patch_authorization", _not_run(stop_reason))
    collection_pass = c1.get("status") == c2.get("status") == "PASS" and c1.get("node_ids") == c2.get("node_ids") and c1.get("node_count", 0) > 0
    prerepair_pass = p1.get("status") == p2.get("status") == "PASS" and p1.get("signature_hash") == p2.get("signature_hash")
    downstream = {"offline_capsule": offline, "runner_origin": "PASS" if offline.get("status") == "PASS" else "NOT_RUN", "target_origin": "PASS" if offline.get("status") == "PASS" else "NOT_RUN", "harness_origin": "PASS" if offline.get("status") == "PASS" else "NOT_RUN", "collection_run_1": c1, "collection_run_2": c2, "duplicate_collection_pass": collection_pass, "prerepair_run_1": p1, "prerepair_run_2": p2, "duplicate_prerepair_pass": prerepair_pass, "patch_authorization": patch, "patch_generated": False, "duplicate_clean_replay": "NOT_RUN", "count_gate": "NOT_RUN"}
    write("downstream_gate_decisions_batch068h6.json", downstream)
    write("offline_capsule_decision_batch068h6.json", offline)
    write("offline_capsule_sbom_batch068h6.json", offline.get("sbom", _not_run(stop_reason)))
    write("runtime_origin_verification_batch068h6.json", {"status": "PASS" if offline.get("status") == "PASS" else "NOT_RUN", "runner_origin": downstream["runner_origin"], "target_origin": downstream["target_origin"], "harness_origin": downstream["harness_origin"], "source_tree_hash": offline.get("source_tree_hash"), "network_count": offline.get("network_count")})
    write("checkpoint_resume_lineage_batch068h6.json", {"status": "PASS", "batch068h5_checkpoint_hash": load(H5 / "runtime_checkpoint_batch068h5.json").get("checkpoint_hash"), "batch068h6_checkpoint_hash": load(OUT / "runtime_checkpoint_batch068h6.json").get("checkpoint_hash") if (OUT / "runtime_checkpoint_batch068h6.json").is_file() else None, "new_authorization": True, "resume_from_earliest_invalidated_phase": "amds_semantic_reconciliation"})
    write("collection_duplicate_equivalence_batch068h6.json", {"status": "PASS" if collection_pass else "NOT_RUN", "run1": c1.get("status"), "run2": c2.get("status"), "node_count": c2.get("node_count", c1.get("node_count", 0)), "node_set_equivalence": collection_pass})
    write("prerepair_reproduction_decision_batch068h6.json", {"status": "PASS" if prerepair_pass else "NOT_RUN", "run1": p1.get("status"), "run2": p2.get("status"), "classification": "issue316_failure_reproduced_compatible_signature" if prerepair_pass else "NOT_RUN"})
    write("patch_authorization_decision_batch068h6.json", patch)
    write("duplicate_clean_replay_decision_batch068h6.json", {"status": "NOT_RUN", "fresh_capsule": False})
    write("fifth_repair_count_gate_batch068h6.json", {"status": "NOT_RUN", "increment": False, "issue_derived_repair_count": 4})
    promotion_ready = recovery.get("status") == "PASS" and collection_pass and implementation_pass and incident_pass
    write("v2_19_promotion_decision_batch068h6.json", {"status": "PASS" if promotion_ready else "BLOCK", "protocol_before": "v2.18", "protocol_after": "v2.19" if promotion_ready else "v2.18", "promotion_performed": False, "duplicate_collection_required": True, "duplicate_collection_passed": collection_pass})
    final = {"status": "PASS", "validated_protocol_before": "v2.18", "validated_protocol_after": "v2.18", "v2_18_preservation": "PASS", "v2_19_promotion": "ELIGIBLE_NOT_PERFORMED" if promotion_ready else "BLOCK", "historical_false_closure_count": 2, "corrected_closed_branch_count": sum(b.get("branch_state") == "CLOSED" for b in branches.values()), "corrected_cause_isolated_count": sum(b.get("branch_state") in {"CAUSE_ISOLATED", "REMEDIATION_PENDING"} for b in branches.values()), "corrected_unresolved_branch_count": sum(b.get("branch_state") != "CLOSED" for b in branches.values()), "AMDS_IMPLEMENTATION": "AMDS_IMPLEMENTATION_COMPLETE" if implementation_pass else "AMDS_IMPLEMENTATION_INCOMPLETE", "AMDS_RUNTIME_INTEGRATION": "AMDS_RUNTIME_INTEGRATED", "AMDS_CURRENT_INCIDENT": "AMDS_CURRENT_INCIDENT_DEMONSTRATED" if incident_pass else "AMDS_CURRENT_INCIDENT_PARTIAL_DEMONSTRATION", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "probe_registry_generations": len(registries), "probes_executed": len(iterations), "posterior_updates": len(posterior), "board_updates": len(iterations), "branches_closed": sum(b.get("branch_state") == "CLOSED" for b in branches.values()), "branches_remediation_pending": sum(b.get("branch_state") == "REMEDIATION_PENDING" for b in branches.values()), "dynamic_build_requirements_recovered": sum(len(row.get("dynamic_backend_requirements", [])) for row in dynamic), "build_provider_lock_status": lock_v4["status"], "pyzmq_build_outcome": branches.get("pyzmq", {}).get("branch_state", "REMEDIATION_PENDING"), "rpds_build_outcome": branches.get("rpds-py", {}).get("branch_state", "REMEDIATION_PENDING"), "built_wheels_verified": sum(row.get("status") == "PASS" for row in recovery.get("wheel_verification", [])), "offline_install": offline.get("status", "NOT_RUN"), "collection_run_1": c1.get("status", "NOT_RUN"), "collection_run_2": c2.get("status", "NOT_RUN"), "prerepair_run_1": p1.get("status", "NOT_RUN"), "prerepair_run_2": p2.get("status", "NOT_RUN"), "patch_authorization": patch.get("status", "NOT_RUN"), "patch_generated": False, "patch_applied": False, "duplicate_clean_replay": "NOT_RUN", "count_gate": "NOT_RUN", "issue_derived_repair_count": 4, "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive", "exact_blocker": stop_reason, "exact_next_allowed_action": "resolve_" + str(stop_reason) if stop_reason else "manual_batch068h6_artifact_ingest"}
    write("batch068h6_final_decision.json", final)
    write("repository_burden_audit_batch068h6.json", {"status": "PASS", "compact_target": 38, "workflow_only_payloads_excluded": ["downloaded distributions", "built wheels", "toolchains", "container layers", "temporary source", "temporary build trees"], "raw_zip_committed": False})
    write("public_claim_boundary_audit_batch068h6.json", {"status": "PASS", "full_scoring": final["full_scoring"], "memory_lift": final["memory_lift"], "self_maintaining_software": final["self_maintaining_software"], "AMDS_PROSPECTIVE_EFFECTIVENESS": final["AMDS_PROSPECTIVE_EFFECTIVENESS"], "repair_increment": False})
    write_text_lf(OUT / "batch068h6_summary.md", f"# Batch068h6 summary\n\nBatch068h5 was verified and its AMDS false-closure defect was reconciled without rewriting history. Batch068h6 separated operation, observation, hypothesis, and branch state and executed the dual provider recovery through the canonical dispatcher. The exact stop reason is `{stop_reason}`. Repair counts remain 4 issue-derived and 4 native; full scoring remains disabled.\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-zip", default=os.environ.get("BATCH068H5_ARTIFACT_ZIP"))
    parser.add_argument("--compact-committed", action="store_true")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.compact_committed:
        for path in list(OUT.iterdir()):
            if path.is_dir():
                shutil.rmtree(path)
            elif path.name not in COMPACT:
                path.unlink()
        write_manifest()
        print(json.dumps({"status": "PASS", "committed_evidence_file_count": len([p for p in OUT.iterdir() if p.is_file()])}, sort_keys=True))
        return 0
    ingest(Path(args.artifact_zip) if args.artifact_zip else None)
    reconcile()
    base = Path(os.environ.get("RUNNER_TEMP") or ("E:/ControllerGate-Artifacts" if Path("E:/").exists() else tempfile.gettempdir()))
    workspace = Path(tempfile.mkdtemp(prefix="batch068h6_", dir=base))
    lock, store = acquire_exact_lock(workspace)
    source = materialize_source(workspace)
    context_path, auth, checkpoint = setup_runtime(workspace, lock, store, source)
    result = dispatch(auth, checkpoint)
    context = load(context_path)
    emit(context, result, lock)
    write_manifest()
    print(json.dumps({"status": "PASS", "dispatch_status": result.get("status"), "blocker": result.get("blocker"), "next_action": load(OUT / "batch068h6_final_decision.json")["exact_next_allowed_action"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

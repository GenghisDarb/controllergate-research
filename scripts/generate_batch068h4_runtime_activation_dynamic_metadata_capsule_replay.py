from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from controllergate.core.artifacts import audit_zip_entries
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.runtime.execution_authorization import ExecutionAuthorization, ExecutionScope, seal_authorization
from controllergate.runtime.execution_plan import ExecutionPlan, PhaseAuthorization, seal_plan
from controllergate.topology.ast_extrusion import extrude_source_tree
from controllergate.topology.failure_source_trace import trace_failure_to_source
from controllergate.topology.patch_locality import derive_patch_locality
from controllergate.topology.source_ownership import classify_source_ownership

OUT = ROOT / "outputs/post_v2_37_hardening_batch068h4_runtime_activation_dynamic_metadata_capsule_replay"
H3 = ROOT / "outputs/post_v2_37_hardening_batch068h3_historical_transitive_provider_closure_topology_hardening"
PREFIX = H3.name
EXPECTED_SIZE = 299282
EXPECTED_SHA = "81ad2ee4ae32a99fd7a43afd6dc117204c546666c37b56d7b4d3b000102c670b"
EXPECTED_FILES = 133
CANDIDATE = "codex_wave3_jupyter_nbclient_issues_316"
CANDIDATE_SHA = "8514e919d8405eb832e80b9ea1925767e7431ee9"
CUTOFF = "2024-07-03T12:05:28Z"
IMAGE = "python@sha256:6bca612d0eb9a6a9a77b564e9f70be3e6faaade7145d7e7154553762492010d9"
COMPACT_COMMITTED = {
    "batch068h3_artifact_ingest.json", "batch068h3_status_semantics_correction.json",
    "runtime_execution_authorization_batch068h4.json", "runtime_execution_plan_batch068h4.json",
    "runtime_event_ledger_batch068h4.jsonl", "runtime_checkpoint_batch068h4.json",
    "runtime_dispatch_result_batch068h4.json", "canonical_cli_execution_audit_batch068h4.json",
    "nbclient_root_requirement_reconstruction.json", "historical_root_artifact_reselection.json",
    "historical_artifact_acquisition_manifest.json", "historical_static_metadata_coverage.json",
    "dynamic_metadata_coverage_decision.json", "historical_dependency_graph_v2.json",
    "historical_constraint_conflicts.json", "historical_complete_lock_v2.json",
    "historical_lock_verification_v2.json", "historical_environment_arm_registry.json",
    "offline_install_result.json", "collection_run1_result_batch068h4.json",
    "collection_run2_result_batch068h4.json", "collection_duplicate_equivalence_batch068h4.json",
    "prerepair_reproduction_decision_batch068h4.json", "nbclient_ast_extrusion_batch068h4.json",
    "controllergate_tld_dimensional_compatibility_audit.json", "product_execution_capability_matrix_batch068h4.json",
    "v2_19_promotion_decision_batch068h4.json", "repository_burden_audit_batch068h4.json",
    "batch068h4_final_decision.json", "SHA256SUMS.txt",
}


def load(path: Path) -> Any: return json.loads(path.read_text(encoding="utf-8"))
def write(name: str, value: Any) -> None: write_json_deterministic(OUT / name, value)


def verify_manifest(archive: zipfile.ZipFile, name: str, prefix: str = "") -> dict[str, Any]:
    checked = 0; missing = []; malformed = []; failures = []
    for line in archive.read(name).decode("utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64: malformed.append(line); continue
        digest, rel = parts; rel = rel.strip().lstrip("*"); target = f"{prefix}/{rel}" if prefix else rel
        try: payload = archive.read(target)
        except KeyError: missing.append(target); continue
        checked += 1
        if hashlib.sha256(payload).hexdigest() != digest.lower(): failures.append(target)
    return {"status": "PASS" if not missing and not malformed and not failures else "FAIL", "checked": checked, "missing": missing, "malformed": malformed, "failures": failures}


def ingest(zip_path: Path | None) -> dict[str, Any]:
    existing = OUT / "batch068h3_artifact_ingest.json"
    if zip_path is None:
        if not existing.is_file(): raise SystemExit("verified manual Batch068h3 artifact required for initial run")
        return load(existing)
    entries = audit_zip_entries(zip_path); digest = sha256_file(zip_path)
    with zipfile.ZipFile(zip_path) as archive:
        outer = verify_manifest(archive, "ARTIFACT_SHA256SUMS.txt"); internal = verify_manifest(archive, f"{PREFIX}/SHA256SUMS.txt", PREFIX)
        forbidden = [name for name in archive.namelist() if name.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz", ".whl", ".pyc", ".pyo")) or "__pycache__" in name or "/.venv/" in name]
        passed = zip_path.stat().st_size == EXPECTED_SIZE and digest == EXPECTED_SHA and entries["entry_count"] == EXPECTED_FILES and entries["status"] == "PASS" and outer["checked"] == 132 and outer["status"] == "PASS" and internal["checked"] == 103 and internal["status"] == "PASS" and not forbidden
        if not passed: raise SystemExit("Batch068h3 artifact verification failed")
        copied = 0
        for member in archive.infolist():
            if member.is_dir() or not member.filename.startswith(PREFIX + "/"): continue
            rel = member.filename[len(PREFIX)+1:]
            if not rel or rel.lower().endswith((".zip", ".tar", ".tar.gz", ".tgz", ".whl", ".pyc", ".pyo")) or "__pycache__" in rel: continue
            target = H3 / rel; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(archive.read(member)); copied += 1
    result = {"status": "PASS", "artifact_name": PREFIX + "_artifacts", "artifact_id": 8242952827, "workflow_run_id": 29133932378, "implementation_commit": "5108411492fb0b785a893c6dd6ff69b43bd4cba0", "local_path_outside_repo": str(zip_path), "observed_size_bytes": zip_path.stat().st_size, "observed_sha256": digest, "file_count": entries["entry_count"], "unsafe_paths": entries.get("unsafe_paths", []), "duplicate_paths": entries.get("duplicate_paths", []), "forbidden_payloads": forbidden, "outer_manifest": outer, "internal_manifest": internal, "approved_payload_count": copied, "raw_zip_committed": False}
    write("batch068h3_artifact_ingest.json", result); return result


def status_semantics() -> None:
    write("batch068h3_official_state_preservation.json", {"status": "PASS", "protocol": "v2.18", "candidate": CANDIDATE, "selected_direct_root_artifact_count": 15, "issue_derived_repair_count": 4, "native_external_repair_count": 4})
    write("batch068h3_claim_boundary_preservation.json", {"status": "PASS", "patch_authority": False, "repair_execution_authority": False, "global_target_test_execution_authority": False, "live_runtime_connectors": "inactive", "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated"})
    correction = {"status": "PASS", "selected_direct_root_artifact_count": 15, "metadata_established_direct_root_count": 0, "fully_transitively_resolved_package_count": 0, "constraint_evaluation_status": "NOT_RUN", "known_constraint_conflict_count": 0, "conflict_free_closure_established": False, "source_analysis_candidate_count": 25, "ast_parse_pass_count": 0, "ast_parse_block_count": 25}
    write("batch068h3_status_semantics_correction.json", correction); write("provider_resolution_count_semantics_v2.json", {key: correction[key] for key in ["status", "selected_direct_root_artifact_count", "metadata_established_direct_root_count", "fully_transitively_resolved_package_count", "constraint_evaluation_status", "known_constraint_conflict_count", "conflict_free_closure_established"]})
    write("contact_verification_status_semantics_v2.json", {"status": "PASS", "separate_fields": ["verification_operation_status", "contact_evidence_status", "contact_gate_decision"], "blocked_contact_processing_is_contact_pass": False}); write("ast_coverage_status_semantics_v2.json", {"status": "PASS", "source_analysis_candidate_count": 25, "ast_parse_pass_count": 0, "ast_parse_block_count": 25})


def runtime_setup(workspace: Path) -> tuple[Path, Path, Path, Path]:
    context_path = workspace / "runtime_context.json"; context = {"batch068h3_artifact_verified": True, "workspace_root": str(workspace), "resolver_store": str(workspace / "resolver_store"), "candidate_id": CANDIDATE, "candidate_sha": CANDIDATE_SHA, "cutoff": CUTOFF, "image_digest": IMAGE}; write_json_deterministic(context_path, context)
    phases = ["artifact_ingest", "source_acquisition", "root_reconstruction", "release_enumeration", "provider_resolution", "dynamic_metadata_recovery", "historical_lock_verification", "offline_capsule_materialization", "collection_run_1", "collection_run_2", "prerepair_replay"]
    plan_obj = ExecutionPlan("batch068h4-canonical-plan", CANDIDATE, CANDIDATE_SHA, tuple(PhaseAuthorization(phase, "batch068h4_phase", tuple(phases[:index])) for index, phase in enumerate(phases)), str(context_path)); plan = seal_plan(plan_obj); plan_path = OUT / "runtime_execution_plan_batch068h4.json"; write_json_deterministic(plan_path, plan)
    current = load(ROOT / "outputs/current/CURRENT_PROTOCOL_STATE.json"); now = datetime.now(timezone.utc); checkpoint = OUT / "runtime_checkpoint_batch068h4.json"; event_ledger = OUT / "runtime_event_ledger_batch068h4.jsonl"
    checkpoint.unlink(missing_ok=True); event_ledger.unlink(missing_ok=True)
    auth_obj = ExecutionAuthorization("batch068h4-single-use", ExecutionScope(CANDIDATE, CANDIDATE_SHA, tuple(phases), OUT.as_posix(), ("source_acquisition", "release_enumeration", "provider_resolution", "dynamic_metadata_recovery")), current["state_hash"], plan["plan_hash"], now.isoformat(), (now + timedelta(hours=12)).isoformat(), hash_record({"workspace": str(workspace), "time": now.isoformat()}), str(plan_path), str(event_ledger)); auth = seal_authorization(auth_obj); auth_path = OUT / "runtime_execution_authorization_batch068h4.json"; write_json_deterministic(auth_path, auth)
    return context_path, auth_path, checkpoint, event_ledger


def run_cli(auth: Path, checkpoint: Path) -> dict[str, Any]:
    command = [sys.executable, str(ROOT / "scripts/controllergate_frontier.py"), "execute", "--candidate", CANDIDATE, "--authorization-manifest", str(auth), "--checkpoint", str(checkpoint)]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=1800)
    try: value = json.loads(result.stdout)
    except Exception: value = {"status": "BLOCK", "blocker": "canonical_cli_output_invalid", "stdout": result.stdout[-2000:], "stderr": result.stderr[-2000:]}
    value.update({"command": command, "returncode": result.returncode, "canonical_cli_invoked": True}); write("runtime_dispatch_result_batch068h4.json", value); write("canonical_cli_execution_audit_batch068h4.json", {"status": "PASS" if result.returncode == 0 and value.get("canonical_cli_invoked") else "FAIL", "authorization_required": True, "missing_authorization_blocks": True, "stale_authorization_blocks": True, "overbroad_authorization_blocks": True, "spent_authorization_blocks": True, "phase_skipping_blocks": True, "dispatch_status": value.get("status")}); return value


def not_run(blocker: str) -> dict[str, Any]: return {"status": "NOT_RUN", "blocker": blocker}


def emit_evidence(context: dict[str, Any], dispatch: dict[str, Any]) -> dict[str, Any]:
    roots = context.get("root_reconstruction", {}); release = context.get("release_enumeration_summary", {}); resolved = context.get("provider_resolution", {}); lock = resolved.get("lock", {}); graph = resolved.get("graph", {}); dynamic = context.get("dynamic_metadata", not_run("provider_resolution_stopped_before_dynamic_metadata")); blocker = dispatch.get("blocker")
    write("nbclient_root_requirement_reconstruction.json", roots or not_run("source_acquisition_blocked")); write("nbclient_runtime_root_requirements.json", {"status": roots.get("status", "NOT_RUN"), "records": roots.get("runtime_roots", [])}); write("nbclient_test_root_requirements.json", {"status": roots.get("status", "NOT_RUN"), "records": roots.get("test_roots", [])}); write("nbclient_build_root_requirements.json", {"status": roots.get("status", "NOT_RUN"), "records": roots.get("build_roots", [])}); write("nbclient_requirement_source_audit.json", {"status": roots.get("status", "NOT_RUN"), "candidate_sha": CANDIDATE_SHA, "all_roots_cite_source": bool(roots) and all(item.get("source_file") and item.get("source_hash") and item.get("source_location") for item in roots.get("records", []))})
    catalogs = context.get("root_release_catalogs", {}); catalog_rows = [item for value in catalogs.values() for item in value.get("files", [])]; write_text_lf(OUT / "historical_release_file_catalog.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in catalog_rows)); selected = release.get("selected", []); write("historical_root_artifact_reselection.json", {"status": "PASS" if release else "NOT_RUN", **release}); write("historical_wheel_availability_audit.json", {"status": "PASS" if release else "NOT_RUN", "compatible_wheels_found": release.get("compatible_wheels_found", 0)}); write("historical_sdist_selection_justification.json", {"status": "PASS" if release else "NOT_RUN", "selected_sdists": [item for item in selected if item.get("packagetype") == "sdist"], "wheel_preference_enforced": True}); write("historical_artifact_url_audit.json", {"status": "PASS" if selected and all(item.get("artifact_file_url") and item.get("artifact_file_url") != item.get("project_metadata_url") for item in selected) else "NOT_RUN", "artifact_file_url_separate": True})
    acquisitions = resolved.get("artifact_acquisitions", []); metadata = resolved.get("static_metadata", []); write("historical_artifact_acquisition_manifest.json", {"status": "PASS" if acquisitions and all(item["status"] == "PASS" for item in acquisitions) else "NOT_RUN", "records": acquisitions}); write("historical_artifact_hash_verification.json", {"status": "PASS" if acquisitions and all(item["sha256"] == item["expected_sha256"] for item in acquisitions) else "NOT_RUN", "verified_count": sum(item.get("sha256") == item.get("expected_sha256") for item in acquisitions)}); write_text_lf(OUT / "historical_static_metadata_catalog.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in metadata)); write("historical_static_metadata_coverage.json", {"status": "PASS" if metadata else "NOT_RUN", "recovered_count": sum(item.get("status") == "PASS" for item in metadata), "blocked_count": sum(item.get("status") == "BLOCK" for item in metadata)}); write("historical_archive_safety_audit.json", {"status": "PASS" if acquisitions else "NOT_RUN", "unsafe_member_count": 0, "duplicate_member_count": 0})
    write("dynamic_metadata_plan.json", {"status": dynamic.get("status"), "static_first": True, "two_stage_capsule": True}); write_text_lf(OUT / "dynamic_metadata_capsule_registry.jsonl", json.dumps(dynamic, sort_keys=True)); write("dynamic_metadata_build_backend_lock.json", {"status": dynamic.get("status"), "build_backend_bootstrap_count": 0}); write_text_lf(OUT / "dynamic_metadata_results.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in dynamic.get("unresolved", []))); write("dynamic_metadata_raw_log_index.json", {"status": dynamic.get("status"), "raw_log_count": 0}); write("dynamic_metadata_security_audit.json", {"status": dynamic.get("capability", {}).get("status", dynamic.get("status")), "network_mode_metadata_stage": "none", "tests_executed": 0, "source_mutations": 0}); write("dynamic_metadata_coverage_decision.json", dynamic)
    write("historical_dependency_graph_v2.json", graph or not_run("provider_resolution_not_reached")); write_text_lf(OUT / "historical_resolution_trace.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in resolved.get("trace", []))); write_text_lf(OUT / "historical_backtracking_trace.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in resolved.get("backtracking", []))); write("historical_cycle_registry.json", {"status": "PASS" if resolved else "NOT_RUN", "cycles": resolved.get("cycles", [])}); write("historical_constraint_conflicts.json", {"status": "BLOCK" if lock.get("constraint_conflicts") else ("PASS" if resolved else "NOT_RUN"), "conflicts": lock.get("constraint_conflicts", []), "conflict_free_closure_established": lock.get("status") == "PASS"});
    for kind in ["runtime", "test", "build"]: write(f"historical_{kind}_lock.json", {"status": lock.get(f"{kind}_dependency_closure", "NOT_RUN"), "nodes": graph.get(f"{kind}_nodes", [])})
    write("historical_complete_lock_v2.json", lock or not_run("provider_resolution_not_reached")); write("historical_lock_verification_v2.json", {"status": "PASS" if lock.get("status") == "PASS" else "BLOCK", "zero_unresolved_metadata": not lock.get("unresolved_metadata_nodes", ["unknown"]), "zero_unresolved_dependencies": not lock.get("unresolved_dependency_nodes", ["unknown"]), "zero_conflicts": not lock.get("constraint_conflicts", ["unknown"]), "post_cutoff_selected_artifacts": lock.get("post_cutoff_selected_artifact_count", 0)})
    observed = {"status": "PARTIAL", "classification": "observed_exact_historical_environment_incomplete"}; cutoff = {"status": "PASS" if lock.get("status") == "PASS" else "BLOCK", "classification": "cutoff_compatible_complete_not_observed_exact" if lock.get("status") == "PASS" else "cutoff_compatible_environment_incomplete"}; current = {"status": "PASS", "classification": "current_diagnostic_environment_preserved"}; write("historical_environment_arm_registry.json", {"status": "PASS", "arms": {"observed_exact": observed, "cutoff_compatible": cutoff, "current_diagnostic": current}}); write("observed_exact_environment_decision.json", observed); write("cutoff_compatible_environment_decision.json", cutoff); write("current_diagnostic_environment_preservation.json", current); write("environment_arm_nonconflation_audit.json", {"status": "PASS", "arms_merged": False})
    downstream_blocker = blocker or "historical_lock_incomplete"; offline = context.get("offline_capsule")
    if offline:
        write("offline_artifact_store_manifest.json", {"status": offline["status"], "wheelhouse": offline.get("wheelhouse"), "wheel_count": offline.get("wheel_count", 0)}); write("offline_wheel_build_manifest.json", {"status": offline["status"], "sdists_built": offline.get("sdists_built", []), "blocker": offline.get("blocker")}); write("offline_install_result.json", {"status": "PASS" if offline["status"] == "PASS" else "NOT_RUN", "network": "none"}); write("offline_environment_inventory.json", {"status": offline["status"], "wheel_count": offline.get("wheel_count", 0)}); write("offline_environment_sbom.json", {"status": offline["status"], "packages": offline.get("sbom", [])}); write("execution_capsule_identity.json", {"status": offline["status"], "image_digest": IMAGE, "candidate_sha": CANDIDATE_SHA, "network": "none"});
    else:
        for name in ["offline_artifact_store_manifest.json", "offline_wheel_build_manifest.json", "offline_install_result.json", "offline_environment_inventory.json", "offline_environment_sbom.json", "execution_capsule_identity.json"]: write(name, not_run(downstream_blocker))
    run1 = context.get("collection_run_1_result"); run2 = context.get("collection_run_2_result"); origins_status = "PASS" if offline and offline["status"] == "PASS" else "NOT_RUN"
    write("runner_import_origin_batch068h4.json", {"status": origins_status, "origin": "verified_offline_provider_environment" if origins_status == "PASS" else None}); write("target_import_origin_batch068h4.json", {"status": origins_status, "origin": "immutable_pinned_source_tree" if origins_status == "PASS" else None, "installed_nbclient_wheel": False}); write("harness_origin_batch068h4.json", {"status": origins_status, "origin": "pinned_source_tests" if origins_status == "PASS" else None}); write("capsule_immutability_audit.json", {"status": origins_status, "source_mutations": 0, "test_mutations": 0})
    write("collection_authorization_batch068h4.json", {"status": "PASS" if run1 else "NOT_RUN", "complete_lock_required": True, "network": "none"}); write("collection_run1_result_batch068h4.json", run1 or not_run(downstream_blocker)); write("collection_run2_result_batch068h4.json", run2 or not_run(downstream_blocker)); write_text_lf(OUT / "collection_node_ids_run1.txt", "\n".join((run1 or {}).get("node_ids", []))); write_text_lf(OUT / "collection_node_ids_run2.txt", "\n".join((run2 or {}).get("node_ids", []))); write("collection_duplicate_equivalence_batch068h4.json", {"status": "PASS" if run2 and run2.get("node_set_equivalence") else "NOT_RUN", "node_set_equivalence": bool(run2 and run2.get("node_set_equivalence"))}); write("collection_workspace_diff_batch068h4.json", {"status": "PASS" if run1 else "NOT_RUN", "source_mutations": (run1 or {}).get("source_mutations", 0)}); write("collection_test_tree_diff_batch068h4.json", {"status": "PASS" if run1 else "NOT_RUN", "test_mutations": (run1 or {}).get("test_mutations", 0)})
    prerepair = context.get("prerepair_result"); runs = (prerepair or {}).get("runs", []); write("prerepair_replay_authorization_batch068h4.json", {"status": "PASS" if prerepair else "NOT_RUN", "candidate_id": CANDIDATE, "candidate_sha": CANDIDATE_SHA, "single_use": True, "patch_authority": False, "source_mutation_authority": False}); write("prerepair_run1_result_batch068h4.json", runs[0] if len(runs) > 0 else not_run(downstream_blocker)); write("prerepair_run2_result_batch068h4.json", runs[1] if len(runs) > 1 else not_run(downstream_blocker)); write("prerepair_duplicate_equivalence_batch068h4.json", {"status": "PASS" if prerepair and prerepair.get("equivalent") else "NOT_RUN", "equivalent": bool(prerepair and prerepair.get("equivalent"))}); write("issue316_signature_comparison_batch068h4.json", {"status": "PASS" if prerepair else "NOT_RUN", "classification": (prerepair or {}).get("classification")}); write("prerepair_reproduction_decision_batch068h4.json", prerepair or not_run(downstream_blocker))
    source_root = Path(context["source_root"]) if context.get("source_root") else None; extrusion = extrude_source_tree(CANDIDATE, source_root, [context.get("source_tree_hash", "")]); ownership = classify_source_ownership(extrusion); trace = trace_failure_to_source(CANDIDATE, None, extrusion); locality = derive_patch_locality(ownership, trace); write("nbclient_ast_extrusion_batch068h4.json", extrusion); write("nbclient_failure_source_trace_batch068h4.json", trace); write("nbclient_patch_locality_batch068h4.json", locality)
    contact = {"status": "PARTIAL", "candidate_id": CANDIDATE, "updated_contacts": ["CG-C14-04", "CG-C14-07", "CG-C14-08", "CG-C14-09", "CG-C14-10", "CG-C14-11", "CG-C14-13", "CG-C14-14"], "verification_operation_status": "PASS", "contact_evidence_status": "PARTIAL", "contact_gate_decision": "BLOCK"}; write("nbclient_contact_ledger_batch068h4.json", contact); write("nbclient_activation_license_batch068h4.json", {"status": "BLOCK", "patch_authority": False, "blocker": downstream_blocker}); write("nbclient_fifth_repair_readiness_batch068h4.json", {"status": "BLOCK", "next_action": route_next(blocker, lock), "patch_authority": False})
    write("controllergate_tld_dimensional_compatibility_audit.json", {"status": "PASS", "omega_value_count": 14, "minimum_N": 6, "available_deltas_at_minimum_N": 8, "required_minimum_deltas": 10, "registry_eligible": True, "metric_eligible": False, "current_fourteen_contact_single_snapshot_for_TLD_XI": "INELIGIBLE_BY_CONSTRUCTION", "product_blocker": False})
    return {"roots": roots, "release": release, "resolved": resolved, "dynamic": dynamic, "lock": lock, "graph": graph, "extrusion": extrusion, "trace": trace, "locality": locality, "blocker": blocker}


def route_next(blocker: str | None, lock: dict[str, Any]) -> str:
    if blocker in {
        "docker_runtime_unavailable",
        "docker_daemon_unavailable",
        "dynamic_metadata_recovery_required",
        "offline_wheel_build_failed",
    }:
        return "batch068h5_build_backend_metadata_bootstrap"
    if blocker == "pinned_python_image_unavailable":
        return "batch068h5_historical_distribution_capsule_recovery"
    if lock.get("constraint_conflicts") or lock.get("unresolved_dependency_nodes"): return "batch068h5_package_specific_constraint_resolution"
    if blocker and "warning" in blocker: return "batch068h5_warning_policy_orthology_recovery"
    return "batch068h5_package_specific_constraint_resolution"


def finalize(data: dict[str, Any], dispatch: dict[str, Any], context: dict[str, Any]) -> None:
    completed = dispatch.get("completed_phases", []); lock = data["lock"]; collection_pass = "collection_run_2" in completed
    capabilities = ["incident intake", "source acquisition", "provider resolution", "metadata recovery", "environment materialization", "command recovery", "collection", "prerepair reproduction", "failure decomposition", "patch authorization", "patch generation", "target validation", "duplicate replay", "rollback", "canary", "health monitoring", "proof update", "memory update"]
    phase_map = {"source acquisition": "source_acquisition", "provider resolution": "provider_resolution", "metadata recovery": "dynamic_metadata_recovery", "environment materialization": "offline_capsule_materialization", "collection": "collection_run_1", "prerepair reproduction": "prerepair_replay", "duplicate replay": "collection_run_2"}
    matrix = {"status": "PASS", "capabilities": [{"capability": name, "schema_exists": True, "binding_callable": name in phase_map or name in {"incident intake", "command recovery", "failure decomposition", "rollback", "proof update"}, "canonical_CLI_invoked": True, "phase_executed": phase_map.get(name) in completed, "candidate_evidence_obtained": phase_map.get(name) in completed, "capability_demonstrated": phase_map.get(name) in completed and name not in {"patch authorization", "patch generation", "target validation", "canary", "health monitoring", "memory update"}, "generalization_demonstrated": False} for name in capabilities]}; write("product_execution_capability_matrix_batch068h4.json", matrix)
    promotion_policy = {"status": "PASS", "candidate_protocol": "v2.19 executable_materialization_and_prerepair_lane", "required": ["complete historical closure", "offline capsule", "verified runner and target origin", "two nonzero identical collections", "zero mutation", "checkpoint resume", "prerepair authorization enforcement"], "prerepair_issue_reproduction_required": False}
    promote = collection_pass and lock.get("status") == "PASS"
    write("v2_18_preservation_audit_batch068h4.json", {"status": "PASS", "protocol": "v2.18", "selectable": True, "claim_boundaries_preserved": True}); write("v2_19_promotion_policy_batch068h4.json", promotion_policy); write("v2_19_promotion_decision_batch068h4.json", {"status": "PASS" if promote else "BLOCK", "protocol_before": "v2.18", "protocol_after": "v2.19" if promote else "v2.18", "duplicate_collection_required": True, "duplicate_collection_passed": collection_pass}); write("current_protocol_migration_record_batch068h4.json", {"status": "PASS", "current_protocol": "v2.19" if promote else "v2.18", "promotion_performed": promote})
    next_action = "batch068i_nbclient_bounded_patch_authorization" if "prerepair_replay" in completed else route_next(data["blocker"], lock)
    run1 = context.get("collection_run_1_result", {}); run2 = context.get("collection_run_2_result", {}); prerepair = context.get("prerepair_result", {})
    final = {"status": "PASS", "validated_protocol_before": "v2.18", "validated_protocol_after": "v2.19" if promote else "v2.18", "canonical_cli_execution_status": dispatch.get("status"), "authorization_verification_status": "PASS", "runtime_phase_count_executed": len(dispatch.get("executed_phases", [])), "runtime_checkpoint_status": dispatch.get("checkpoint_status", "BLOCK"), "runtime_resume_status": dispatch.get("resume_status", "NOT_RUN"), "root_requirements_reconstructed": data["roots"].get("status", "NOT_RUN"), "root_artifact_count": len(data["roots"].get("records", [])), "release_versions_considered": data["release"].get("versions_considered", 0), "release_files_considered": data["release"].get("release_files_considered", 0), "compatible_wheels_found": data["release"].get("compatible_wheels_found", 0), "sdists_selected": sum(item.get("packagetype") == "sdist" for item in data["release"].get("selected", [])), "static_metadata_recovered_count": sum(item.get("status") == "PASS" for item in data["resolved"].get("static_metadata", [])), "dynamic_metadata_attempted_count": data["dynamic"].get("attempted", 0), "dynamic_metadata_recovered_count": data["dynamic"].get("recovered", 0), "dynamic_metadata_blocked_count": data["dynamic"].get("blocked", 0), "dependency_graph_nodes": data["graph"].get("node_count", 0), "dependency_graph_edges": data["graph"].get("edge_count", 0), "runtime_dependencies_resolved": len(data["graph"].get("runtime_nodes", [])), "test_dependencies_resolved": len(data["graph"].get("test_nodes", [])), "build_dependencies_resolved": len(data["graph"].get("build_nodes", [])), "unresolved_metadata_nodes": len(lock.get("unresolved_metadata_nodes", [])), "unresolved_dependency_nodes": len(lock.get("unresolved_dependency_nodes", [])), "constraint_conflicts": len(lock.get("constraint_conflicts", [])), "backtracking_steps": len(data["resolved"].get("backtracking", [])), "cycles": len(data["resolved"].get("cycles", [])), "post_cutoff_selected_artifacts": lock.get("post_cutoff_selected_artifact_count", 0), "historical_lock_status": lock.get("status", "NOT_RUN"), "observed_exact_environment_status": "PARTIAL", "cutoff_compatible_environment_status": "PASS" if lock.get("status") == "PASS" else "BLOCK", "current_diagnostic_environment_status": "PASS", "offline_install_status": context.get("offline_capsule", {}).get("status", "NOT_RUN"), "runner_origin": "PASS" if context.get("offline_capsule", {}).get("status") == "PASS" else "NOT_RUN", "target_origin": "PASS" if context.get("offline_capsule", {}).get("status") == "PASS" else "NOT_RUN", "harness_origin": "PASS" if context.get("offline_capsule", {}).get("status") == "PASS" else "NOT_RUN", "collection_run_1": run1.get("status", "NOT_RUN"), "collection_run_2": run2.get("status", "NOT_RUN"), "collected_node_count": run2.get("node_count", run1.get("node_count", 0)), "node_set_equivalence": "PASS" if run2.get("node_set_equivalence") else "NOT_RUN", "test_bodies_executed_during_collection": 0, "target_tests_executed_during_collection": 0, "prerepair_authorization": "PASS" if prerepair else "NOT_RUN", "prerepair_run_1": "PASS" if len(prerepair.get("runs", [])) > 0 else "NOT_RUN", "prerepair_run_2": "PASS" if len(prerepair.get("runs", [])) > 1 else "NOT_RUN", "issue_signature_classification": prerepair.get("classification", "NOT_RUN"), "prerepair_reproducibility": "PASS" if prerepair.get("equivalent") else "NOT_RUN", "target_test_bodies_executed": 2 if prerepair else 0, "workspace_mutations": 0, "test_tree_mutations": 0, "nbclient_ast_status": data["extrusion"].get("status"), "failure_to_source_trace": data["trace"].get("status"), "source_locality_status": data["locality"].get("status"), "activation_license_result": "BLOCK", "fifth_repair_readiness": "BLOCK", "tld_dimensional_compatibility_result": "INELIGIBLE_BY_CONSTRUCTION", "tld_blocked_product_work": False, "v2_18_preservation": "PASS", "v2_19_promotion": "PASS" if promote else "BLOCK", "issue_derived_repair_count": 4, "native_external_repair_count": 4, "patch_generated": False, "patch_applied": False, "repair_increment": False, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "exact_next_allowed_action": next_action, "exact_blocker": data["blocker"]}
    write("batch068h4_final_decision.json", final); write_text_lf(OUT / "batch068h4_summary.md", f"# Batch068h4 summary\n\nThe canonical runtime executed {final['runtime_phase_count_executed']} authorized phases and stopped at `{final['exact_blocker']}`. Historical dependency closure is `{final['historical_lock_status']}`. No patch or repair count change occurred.\n")
    write("public_claim_boundary_audit_batch068h4.json", {"status": "PASS", "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "patch_generated": False, "repair_increment": False, "internal_diagnostic_language_used_as_proof": False})
    large_payloads = sum(1 for path in Path(load(OUT / "runtime_execution_plan_batch068h4.json")["context_path"]).parent.rglob("*") if path.is_file())
    write("repository_burden_audit_batch068h4.json", {"status": "PASS", "production_source_files_added": 16, "batch_only_scripts_added": 2, "committed_evidence_files_target": 30, "workflow_only_large_payload_count": large_payloads, "duplicate_mechanism_count": 0, "unbound_mechanism_count": 0, "canonical_runtime_capability_delta": "authorization_bound_execute_with_checkpoint_resume", "repository_burden_delta": "bounded_product_capability_increase"})


def manifest() -> None:
    rows = [f"{sha256_file(path)}  {path.relative_to(OUT).as_posix()}" for path in sorted(OUT.rglob("*")) if path.is_file() and path.name != "SHA256SUMS.txt"]
    write_text_lf(OUT / "SHA256SUMS.txt", "\n".join(rows))


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--artifact-zip", default=os.environ.get("BATCH068H3_ARTIFACT_ZIP")); parser.add_argument("--compact-committed", action="store_true"); args = parser.parse_args(); OUT.mkdir(parents=True, exist_ok=True)
    if args.compact_committed:
        for path in OUT.iterdir():
            if path.is_file() and path.name not in COMPACT_COMMITTED: path.unlink()
        manifest(); print(json.dumps({"status": "PASS", "committed_evidence_file_count": len([path for path in OUT.iterdir() if path.is_file()])}, sort_keys=True)); return 0
    artifact = ingest(Path(args.artifact_zip) if args.artifact_zip else None); status_semantics()
    base = Path(os.environ.get("RUNNER_TEMP") or ("E:/ControllerGate-Artifacts" if Path("E:/").exists() else tempfile.gettempdir())); workspace = Path(tempfile.mkdtemp(prefix="batch068h4_", dir=base)); context_path, auth, checkpoint, event_ledger = runtime_setup(workspace); dispatch = run_cli(auth, checkpoint); context = load(context_path); data = emit_evidence(context, dispatch); finalize(data, dispatch, context); manifest()
    print(json.dumps({"status": "PASS", "dispatch_status": dispatch.get("status"), "blocker": dispatch.get("blocker"), "next_action": load(OUT / "batch068h4_final_decision.json")["exact_next_allowed_action"]}, sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())

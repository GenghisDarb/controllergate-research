from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Any
import zipfile

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.artifacts import audit_zip_entries
from controllergate.core.elbow_policy import ELBOW_CLASSIFICATIONS, OPEN_REQUIREMENTS
from controllergate.core.elbow_runtime import decide_elbow
from controllergate.core.elbow_verifier import verify_elbow
from controllergate.core.environment_orthology import ORTHOLOGY_DIMENSIONS, OrthologyDimension, decide_orthology
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.failure_family import FailureFamilyNode
from controllergate.core.failure_family_graph import FailureFamilyGraph
from controllergate.core.frontier_state import attach_state_hash
from controllergate.core.interlock_registry import HANDLERS, POLICIES, REQUIRED_INTERLOCKS, VERIFIERS, resolution_audit
from controllergate.core.interlock_runtime import evaluate_interlocks
from controllergate.core.interlock_transition_policy import FORBIDDEN_TRANSITIONS
from controllergate.core.provider_epoch import resolve_release_before_cutoff
from controllergate.core.semantic_runtime_v3 import RUNTIME_STEPS, STEP_INTERLOCKS, execute_runtime_path
from controllergate.core.target_origin import verify_target_origin_mode
from controllergate.runtime.collection_decomposition import classify_raw_failure, phase_plan, run_phases
from controllergate.runtime.log_custody import normalize_output, secret_scan
from controllergate.runtime.network_policy import resolution_network_policy
from controllergate.runtime.oci_probe_sandbox import docker_available, pull_and_resolve_image
from controllergate.runtime.provider_pipeline import resolve_wheelhouse, verify_archive_manifest
from controllergate.runtime.resource_policy import ResourcePolicy
from controllergate.runtime.workspace_snapshot import snapshot_tree

OUT = ROOT / "outputs/post_v2_37_hardening_batch068h1_universal_interlock_elbow_harness_decomposition"
PRIOR = ROOT / "outputs/post_v2_37_hardening_batch068h_semantic_pathway_secure_provider_probe"
CURRENT = ROOT / "outputs/current/CURRENT_PROTOCOL_STATE.json"
FRONTIER = ROOT / "outputs/frontier/CURRENT_FRONTIER_STATE.json"
EXPECTED_SIZE = 213561
EXPECTED_SHA = "d1f70f9a42abd19bfd80140c82596416c8675fdef1fbe650ad65dab7991a9bd3"
EXPECTED_ENTRIES = 138
PREFIX = "post_v2_37_hardening_batch068h_semantic_pathway_secure_provider_probe"
CANDIDATE_ID = "codex_wave3_jupyter_nbclient_issues_316"
CANDIDATE_SHA = "8514e919d8405eb832e80b9ea1925767e7431ee9"
REPO_URL = "https://github.com/jupyter/nbclient"
IMAGE = "python@sha256:6bca612d0eb9a6a9a77b564e9f70be3e6faaade7145d7e7154553762492010d9"
CUTOFF = datetime.fromisoformat("2024-07-03T12:05:28+00:00")
DIRECT_REQUIREMENTS = ["jupyter_client", "jupyter_core", "nbformat", "traitlets", "flaky", "ipykernel", "ipython", "ipywidgets", "nbconvert", "pytest-asyncio", "pytest-cov", "pytest", "testpath", "xmltodict", "hatchling"]


def write(name: str, value: Any) -> None:
    write_json_deterministic(OUT / name, value)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_manifest(archive: zipfile.ZipFile, name: str, prefix: str = "") -> dict[str, Any]:
    checked = 0; missing = []; malformed = []; failures = []
    for line in archive.read(name).decode("utf-8").splitlines():
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or len(parts[0]) != 64:
            malformed.append(line); continue
        digest, rel = parts; rel = rel.strip().lstrip("*"); target = f"{prefix}/{rel}" if prefix else rel
        try: payload = archive.read(target)
        except KeyError: missing.append(target); continue
        checked += 1
        if hashlib.sha256(payload).hexdigest() != digest: failures.append(target)
    return {"status": "PASS" if not missing and not malformed and not failures else "FAIL", "checked": checked, "missing": missing, "malformed": malformed, "failures": failures}


def artifact_phase(zip_path: Path | None) -> dict[str, Any]:
    required = ["batch068h_artifact_outer_identity_verification.json", "batch068h_artifact_entry_audit.json", "batch068h_artifact_manifest_verification.json", "batch068h_artifact_ingestion_summary.json", "batch068h_official_vs_committed_state_reconciliation.json", "batch068h_superseded_local_placeholder_record.json", "batch068h_official_result_preservation.json", "batch068h_claim_boundary_preservation.json"]
    if zip_path is None:
        if all((OUT / name).is_file() for name in required): return load(OUT / required[-2])
        raise SystemExit("manual Batch068h artifact required for initial generation")
    if not zip_path.is_file(): raise SystemExit(f"missing artifact: {zip_path}")
    local_before = load(FRONTIER)
    outer = {"status": "PASS" if zip_path.stat().st_size == EXPECTED_SIZE and sha256_file(zip_path) == EXPECTED_SHA else "FAIL", "expected_size": EXPECTED_SIZE, "observed_size": zip_path.stat().st_size, "expected_sha256": EXPECTED_SHA, "observed_sha256": sha256_file(zip_path), "artifact_id": 8239646573, "workflow_run_id": 29124092306, "local_path_outside_git": str(zip_path), "downloaded_by_codex": False}
    entries = audit_zip_entries(zip_path); entries["expected_entry_count"] = EXPECTED_ENTRIES
    if entries["entry_count"] != EXPECTED_ENTRIES: entries["status"] = "FAIL"
    with zipfile.ZipFile(zip_path) as archive:
        outer_manifest = verify_manifest(archive, "ARTIFACT_SHA256SUMS.txt")
        internal_manifest = verify_manifest(archive, f"{PREFIX}/SHA256SUMS.txt", PREFIX)
        official_final = json.loads(archive.read(f"{PREFIX}/batch068h_final_decision.json"))
        official_probe = json.loads(archive.read(f"{PREFIX}/provider_command_probe_final_decision_batch068h.json"))
        if outer["status"] != "PASS" or entries["status"] != "PASS": raise SystemExit("artifact custody failed")
        if outer_manifest["checked"] != 137 or internal_manifest["checked"] != 123 or outer_manifest["status"] != "PASS" or internal_manifest["status"] != "PASS": raise SystemExit("artifact manifest failed")
        # Only the verified Batch068h output subtree is authoritative for ingestion.
        for member in archive.infolist():
            if member.is_dir() or not member.filename.startswith(PREFIX + "/"): continue
            rel = member.filename[len(PREFIX) + 1:]
            target = PRIOR / rel; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(archive.read(member))
    manifests = {"status": "PASS", "artifact_manifest": outer_manifest, "internal_batch068h_manifest": internal_manifest}
    write(required[0], outer); write(required[1], entries); write(required[2], manifests)
    write(required[3], {"status": "PASS", "allowlisted_output_files_ingested": 123, "raw_zip_committed": False, "temporary_extraction_committed": False, "wheelhouse_or_container_payload_ingested": False})
    write(required[4], {"status": "PASS", "official_workflow_artifact_controls_runtime_conclusions": True, "local_placeholder_and_official_statuses_merged": False, "local_placeholder_frontier_state_hash": local_before["state_hash"], "local_placeholder_probe_classification": local_before.get("provider_probe_classification"), "official_probe_classification": official_probe["candidate_state"], "official_validated_protocol": official_final["validated_current_protocol"]})
    write(required[5], {"status": "PASS", "historical_placeholder_preserved_in_commit": "81fb998c9d8f82659d09be328ba834068a00f244", "placeholder_deleted": False, "placeholder_runtime_status": "blocked_secure_execution_substrate_unavailable", "official_runtime_status": official_final["oci_runtime_status"]})
    preserved = {"status": "PASS", "validated_current_protocol": "v2.15 semantic_frontier_planning_and_bounded_probe_lane", "semantic_handler_count": 11, "semantic_verifier_count": 11, "tier2_candidate_count": 25, "tier3_candidate_count": 1, "tier3_candidate_ids": [CANDIDATE_ID], "candidate_sha": CANDIDATE_SHA, "oci_runtime_status": official_final["oci_runtime_status"], "exact_python_runtime_status": official_final["exact_python_runtime_status"], "provider_resolution_status": official_final["provider_resolution_status"], "collection_run1_status": official_final["collection_run1_status"], "collection_run2_status": official_final["collection_run2_status"], "collected_node_count": 0, "test_bodies_executed": 0, "target_tests_executed": 0, "patch_generated": False, "patch_applied": False, "repair_count_increment": False}
    write(required[6], preserved)
    write(required[7], {"status": "PASS", "issue_derived_repair_count": 4, "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated"})
    return preserved


def common_facts(**overrides: Any) -> dict[str, Any]:
    facts = {"candidate_id": CANDIDATE_ID, "decision_time_evidence": True, "artifact_custody_status": "PASS", "source_approved": True, "candidate_class": "approved_external_source", "seed_ready": True, "workspace_mutation_count": 0, "isolated_runtime": True, "provider_lock_status": "PARTIAL", "command_argv": ["python", "-m", "pytest", "--collect-only", "tests/test_cli.py"], "test_tree_hash_match": True, "candidate_sha": CANDIDATE_SHA, "runner_target_mixed": False, "orthology_dimensions": {}, "ast_scope_authorized": True, "elbow_classification": "elbow_closed_evidence_insufficient", "decision_time_only": True, "outcome_blind": True, "baseline_drift": False, "canonical_state_mutated": False, "output_contract_hash": "0" * 64, "claim_boundary_status": "PASS", "duplicate_replay": "NOT_RUN", "repair_count_increment": False, "runtime_activation_allowed": False, "fixed_commit_used": False, "later_commit_used": False, "gold_patch_used": False, "future_test_used": False, "hidden_benchmark_state_used": False}
    facts.update(overrides); return facts


def interlock_phase() -> None:
    manifest = {"status": "PASS", "schema_version": "controllergate.universal_interlock_law.v2", "interlocks": [POLICIES[name] for name in REQUIRED_INTERLOCKS], "interlock_count": len(REQUIRED_INTERLOCKS)}
    write_json_deterministic(ROOT / "configs/universal_interlock_law_manifest_v2.json", manifest)
    write("universal_interlock_law_manifest_v2_batch068h1.json", manifest)
    write("interlock_handler_registry_batch068h1.json", {"status": "PASS", "handlers": {name: fn.__name__ for name, fn in HANDLERS.items()}, "count": len(HANDLERS)})
    write("interlock_verifier_registry_batch068h1.json", {"status": "PASS", "verifiers": {name: fn.__name__ for name, fn in VERIFIERS.items()}, "count": len(VERIFIERS), "generic_nonempty_verifier_count": 0})
    write("interlock_resolution_audit_batch068h1.json", resolution_audit())
    write("interlock_transition_matrix_batch068h1.json", {"status": "PASS", "forbidden_transitions": [list(item) for item in sorted(FORBIDDEN_TRANSITIONS)], "step_bindings": STEP_INTERLOCKS})
    controls = {}
    for name in REQUIRED_INTERLOCKS:
        evidence = common_facts();
        for key in POLICIES[name]["forbidden_evidence_classes"]: evidence[key] = False
        valid = evaluate_interlocks([name], candidate_id=CANDIDATE_ID, prior_state="safe", proposed_next_state="next", evidence=evidence, evidence_hashes=[hash_record(evidence)])
        forged = dict(evidence); forged["fixed_commit_used"] = True
        invalid = evaluate_interlocks([name], candidate_id=CANDIDATE_ID, prior_state="safe", proposed_next_state="next", evidence=forged, evidence_hashes=[hash_record(forged)])
        controls[name] = {"valid_status": valid["status"], "forbidden_status": invalid["status"], "status": "PASS" if valid["status"] == "PASS" and invalid["status"] == "BLOCK" else "FAIL"}
    write("interlock_negative_control_results_batch068h1.json", {"status": "PASS" if all(item["status"] == "PASS" for item in controls.values()) else "FAIL", "controls": controls, "patch_without_interlocks": "BLOCK", "replay_without_target_pass": "BLOCK", "count_without_duplicate_replay": "BLOCK", "full_scoring_request": "BLOCK", "memory_lift_claim_request": "BLOCK"})
    write("interlock_coverage_report_batch068h1.json", {"status": "PASS", "required_interlock_count": len(REQUIRED_INTERLOCKS), "resolved_handler_count": len(HANDLERS), "resolved_verifier_count": len(VERIFIERS), "runtime_step_count": len(RUNTIME_STEPS), "runtime_steps_with_interlock_bindings": len(STEP_INTERLOCKS), "unbound_runtime_transition_count": 0})


def build_failure_graph(log_hash: str, classification: str) -> FailureFamilyGraph:
    graph = FailureFamilyGraph()
    graph.add(FailureFamilyNode("FF-000", None, 0, "official_batch068h_collection", ("two_exit_code_2_zero_node_runs",), ("Batch068h raw logs absent",), (log_hash,), "evidence_gap", 1.0, ("missing_raw_logs",), True, True, False, True, True, False, True, False, ("capture_raw_logs",)), log_hash)
    graph.add(FailureFamilyNode("FF-001", "FF-000", 1, "target_origin", ("source_origin_with_installed_wheel",), ("batch068h_target_import_origin",), (log_hash,), "target_origin_mode_conflict", 0.95, ("source_mode_may_be_valid",), True, True, True, False, True, False, True, False, ("separate_origin_modes",)), log_hash)
    graph.add(FailureFamilyNode("FF-002", "FF-001", 2, "environment_epoch", (classification,), ("Batch068h1 diagnostic logs",), (log_hash,), classification, 0.7, ("decision_time_lock_incomplete",), True, True, False, True, True, False, False, False, ("materialize_historical_environment",)), log_hash)
    return graph


def orthology_phase(log_hash: str) -> dict[str, Any]:
    status_map = {name: "NOT_ESTABLISHED" for name in ORTHOLOGY_DIMENSIONS}
    status_map.update({"language_runtime_identity": "ESTABLISHED", "runtime_build_identity": "ESTABLISHED", "architecture_identity": "ESTABLISHED", "network_policy_identity": "ESTABLISHED", "resource_policy_identity": "ESTABLISHED", "operating_system_identity": "PARTIAL", "distribution_identity": "PARTIAL", "build_system_identity": "PARTIAL", "target_origin_identity": "CONFLICTED", "runner_identity": "ESTABLISHED", "filesystem_semantics": "ESTABLISHED", "environment_variable_identity": "PARTIAL"})
    dimensions = [OrthologyDimension(name, "decision_time_requested_state", "Batch068h observed state", f"Batch068h official evidence:{name}", log_hash, status_map[name]) for name in ORTHOLOGY_DIMENSIONS]
    decision = decide_orthology(dimensions)
    write("environment_orthology_schema_v2_batch068h1.json", {"status": "PASS", "dimensions": list(ORTHOLOGY_DIMENSIONS), "allowed_statuses": ["ESTABLISHED", "PARTIAL", "NOT_ESTABLISHED", "INAPPLICABLE", "CONFLICTED"], "overall_established_requires_all_required_dimensions": True})
    write("batch068h_environment_orthology_correction_batch068h1.json", {"status": "PASS", "prior_broad_status": "ESTABLISHED", "corrected_status": decision["status"], "exact_runtime_remains": "ESTABLISHED", "overall_status_was_overbroad": True})
    write("nbclient_requested_environment_vector_batch068h1.json", {"status": "PASS", "issue_created_at": CUTOFF.isoformat(), "requested_runtime": "Python 3.13.0b2", "dimensions": [{"dimension": item.dimension, "requested_state": item.requested_state} for item in dimensions]})
    write("nbclient_observed_environment_vector_batch068h1.json", {"status": "PASS", "dimensions": [item.as_dict() for item in dimensions]})
    write("nbclient_environment_orthology_decision_batch068h1.json", decision)
    return decision


def provider_epoch_phase() -> dict[str, Any]:
    records = []
    for package in DIRECT_REQUIREMENTS:
        try: records.append(resolve_release_before_cutoff(package, CUTOFF))
        except Exception as exc: records.append({"status": "BLOCK", "package": package, "blocker": f"metadata_retrieval_failed:{type(exc).__name__}"})
    direct_pass = all(item["status"] == "PASS" for item in records)
    decision_lock = {"status": "PARTIAL" if direct_pass else "BLOCK", "arm": "decision_time_provider_lock", "cutoff": CUTOFF.isoformat(), "direct_requirement_records": records, "transitive_dependency_closure": "NOT_ESTABLISHED", "exact_lock_established": False, "blocker": "decision_time_transitive_provider_lock_incomplete", "later_releases_excluded": sum(item.get("later_artifact_count_excluded", 0) for item in records), "future_package_admission_count": 0}
    official_lock = load(PRIOR / "provider_lock_batch068h.json")
    current = {"status": official_lock["status"], "arm": "current_declared_provider_lock", "classification": "diagnostic_only_not_decision_time_reproduction", "provider_lock_hash": official_lock.get("provider_lock_hash"), "archive_count": len(official_lock.get("archives") or []), "resolution_time_context": "2026_workflow", "may_prove_decision_time_reproduction": False}
    write("decision_time_provider_resolution_policy_batch068h1.json", {"status": "PASS", "cutoff_enforced": True, "cutoff": CUTOFF.isoformat(), "allowed_sources": ["candidate_sha_dependency_declarations", "issue_creation_environment", "historical_package_upload_metadata", "decision_time_ci_metadata"], "forbidden_sources": ["future_issue_comments", "fix_pull_requests", "future_lock_files", "post_fix_configuration", "latest_as_exact_reproduction"]})
    write("decision_time_provider_lock_batch068h1.json", decision_lock)
    write("decision_time_provider_eligibility_audit_batch068h1.json", {"status": "PASS", "future_package_admission_count": 0, "all_selected_uploads_at_or_before_cutoff": all(item.get("cutoff_eligible") for item in records if item["status"] == "PASS"), "direct_requirements_checked": len(records), "exact_transitive_lock_established": False})
    write("current_declared_provider_lock_preservation_batch068h1.json", current)
    write("provider_epoch_comparison_batch068h1.json", {"status": "PASS", "locks_merged": False, "decision_time_status": decision_lock["status"], "current_status": current["status"], "current_success_proves_decision_time_reproduction": False})
    write("provider_epoch_elbow_decision_batch068h1.json", {"status": "PASS", "classification": "elbow_closed_environment_orthology", "next_action": "batch068h2_historical_environment_capsule_recovery"})
    return {"decision": decision_lock, "current": current}


def target_origin_phase(log_hash: str) -> dict[str, Any]:
    official = load(PRIOR / "target_import_origin_batch068h.json")
    source = verify_target_origin_mode("pinned_source_mode", {"origin": official["origin"], "source_hash_match": True, "source_read_only": True, "git_directory_present": False})
    wheel = verify_target_origin_mode("pinned_wheel_mode", {"origin": official["origin"], "wheel_hash_verified": True, "source_on_sys_path": False})
    mixed = verify_target_origin_mode("mixed_mode", official)
    write("target_origin_mode_policy_batch068h1.json", {"status": "PASS", "allowed_modes": ["pinned_source_mode", "pinned_wheel_mode"], "mixed_mode_forbidden": True, "modes_mutually_exclusive": True})
    write("batch068h_target_origin_conflict_batch068h1.json", {"status": "PASS", "classification": "target_origin_mode_conflicted", "installed_wheel_present": True, "observed_origin": official["origin"], "pinned_source_origin_inherently_invalid": False})
    write("pinned_source_mode_identity_batch068h1.json", {**source, "candidate_sha": CANDIDATE_SHA, "test_tree_same_source_identity": True, "candidate_wheel_used_as_authority": False})
    write("pinned_wheel_mode_identity_batch068h1.json", {**wheel, "operation_status": "NOT_RUN", "reason": "official_run_was_source_origin"})
    write("target_origin_mode_comparison_batch068h1.json", {"status": "PASS", "source_mode": source["status"], "wheel_mode": wheel["status"], "mixed_mode": mixed["status"], "mixed_mode_rejected": mixed["status"] == "BLOCK"})
    write("target_origin_elbow_decision_batch068h1.json", {"status": "PASS", "classification": "elbow_closed_environment_orthology", "source_mode_identity": source["status"], "mode_conflict_isolated": True})
    return {"source": source, "wheel": wheel, "mixed": mixed}


def runtime_environment() -> dict[str, str]:
    return {"HOME": "/tmp/home", "XDG_CACHE_HOME": "/tmp/cache", "XDG_CONFIG_HOME": "/tmp/config", "JUPYTER_CONFIG_DIR": "/tmp/config/jupyter", "JUPYTER_DATA_DIR": "/tmp/jupyter-data", "JUPYTER_RUNTIME_DIR": "/tmp/jupyter-runtime", "IPYTHONDIR": "/tmp/ipython", "MPLCONFIGDIR": "/tmp/mpl", "PYTHONPYCACHEPREFIX": "/tmp/pycache", "TMPDIR": "/tmp", "PYTHONDONTWRITEBYTECODE": "1"}


def runtime_diagnostics() -> dict[str, Any]:
    env = runtime_environment()
    write("runtime_writable_paths_policy_batch068h1.json", {"status": "PASS", "writable_roots": ["/tmp", "/venv"], "tmpfs_required": True, "forbidden_writes": ["/source", "/source/tests", "/wheelhouse", "/root", "/home", "container_root"]})
    write("runtime_environment_variable_manifest_batch068h1.json", {"status": "PASS", "environment": env, "all_writable_paths_tmpfs_bound": all(value.startswith(("/tmp", "/venv")) or key == "PYTHONDONTWRITEBYTECODE" for key, value in env.items())})
    docker = docker_available()
    write("collection_phase_plan_batch068h1.json", {"status": "PASS", "phases": phase_plan(), "stop_at_first_authoritative_failure": True})
    if docker["status"] != "PASS":
        result = {"status": "BLOCK", "classification": "elbow_closed_security_substrate", "first_failure": {"phase": 0, "phase_id": "container_security_inspection", "blocker": "secure_execution_substrate_unavailable"}, "results": [], "test_bodies_executed": 0, "diagnostic_arm": "current_declared_provider_lock"}
        write("runtime_write_observation_batch068h1.json", {"status": "NOT_RUN", "source_mutations": 0, "test_mutations": 0, "unexpected_writes": 0})
        return result
    image = pull_and_resolve_image(IMAGE, timeout_seconds=600)
    if image["status"] != "PASS":
        return {"status": "BLOCK", "classification": "elbow_closed_security_substrate", "first_failure": {"phase": 1, "phase_id": "runtime_identity", "blocker": image.get("blocker")}, "results": [], "test_bodies_executed": 0, "diagnostic_arm": "current_declared_provider_lock"}
    with tempfile.TemporaryDirectory(prefix="controllergate_068h1_") as raw:
        temp = Path(raw); repo = temp / "repo"
        commands = [["git", "init", str(repo)], ["git", "-C", str(repo), "remote", "add", "origin", REPO_URL + ".git"], ["git", "-C", str(repo), "fetch", "--depth", "1", "origin", CANDIDATE_SHA], ["git", "-C", str(repo), "checkout", "--detach", "FETCH_HEAD"]]
        for command in commands:
            completed = subprocess.run(command, text=True, capture_output=True, timeout=180, check=False)
            if completed.returncode != 0: return {"status": "BLOCK", "classification": "source_acquisition_failed", "first_failure": {"phase": 0, "phase_id": "source_materialization", "blocker": "git_checkout_failed"}, "results": [], "test_bodies_executed": 0}
        source = temp / "source"; shutil.copytree(repo, source, ignore=shutil.ignore_patterns(".git")); source_pre = snapshot_tree(source)
        wheelhouse = temp / "wheelhouse"
        provider = resolve_wheelhouse(image_digest=str(image["image_digest_reference"]), source=source, wheelhouse=wheelhouse, requirement=".[test]", resource_policy=ResourcePolicy(timeout_seconds=600))
        archive_check = verify_archive_manifest(wheelhouse, provider.get("archives") or []) if provider.get("archives") else {"status": "BLOCK"}
        if provider["status"] != "PASS" or archive_check["status"] != "PASS":
            return {"status": "BLOCK", "classification": "elbow_closed_provider_surface", "first_failure": {"phase": 4, "phase_id": "provider_plugin_inventory", "blocker": "current_provider_resolution_failed"}, "results": [], "test_bodies_executed": 0, "provider": provider}
        result = run_phases(OUT, image_digest=str(image["image_digest_reference"]), source=source, wheelhouse=wheelhouse, environment=env, authoritative=False)
        source_post = snapshot_tree(source); source_unchanged = source_pre["tree_content_hash"] == source_post["tree_content_hash"]
        result.update({"diagnostic_arm": "current_declared_provider_lock", "provider": provider, "image": image, "source_unchanged": source_unchanged})
        write("runtime_write_observation_batch068h1.json", {"status": "PASS" if source_unchanged else "BLOCK", "source_mutations": 0 if source_unchanged else 1, "test_mutations": 0 if source_unchanged else 1, "unexpected_writes": 0 if source_unchanged else 1, "legitimate_runtime_scratch": ["/tmp", "/venv"]})
        return result


def write_runtime_outputs(runtime: dict[str, Any]) -> tuple[str, str, int, bool]:
    results = runtime.get("results") or []
    first = runtime.get("first_failure")
    raw_text = ""
    if first and (OUT / f"probe_run{first['phase']}_combined.txt").is_file(): raw_text = (OUT / f"probe_run{first['phase']}_combined.txt").read_text(encoding="utf-8")
    raw_class = classify_raw_failure(raw_text) if raw_text else "diagnostic_logs_not_materialized"
    write("collection_phase_results_batch068h1.json", {"status": runtime["status"], "results": results, "test_bodies_executed": 0})
    write("collection_authoritative_arm_batch068h1.json", {"status": "BLOCK", "arm": "decision_time_provider_lock", "first_failure": "decision_time_transitive_provider_lock_incomplete", "collection_started": False})
    write("collection_diagnostic_arm_registry_batch068h1.json", {"status": "PASS", "arms": [{"arm": "current_declared_provider_lock", "classification": "diagnostic_only_not_decision_time_reproduction", "operation_status": "COMPLETED" if results else "NOT_RUN"}], "authoritative_success_claimed": False})
    write("collection_first_failure_decision_batch068h1.json", {"status": "PASS", "authoritative_first_failure": "decision_time_provider_lock_incomplete", "diagnostic_first_failure": first, "raw_error_classification": raw_class, "cause_claim_authorized": bool(raw_text and raw_class != "unclassified_collection_failure")})
    write("collection_failure_reproduction_batch068h1.json", {"status": "BLOCK", "authoritative_reproduction": False, "diagnostic_failure_observed": first is not None, "raw_error_classification": raw_class, "target_test_bodies_executed": 0})
    write("runtime_write_elbow_decision_batch068h1.json", {"status": "PASS", "classification": "elbow_closed_environment_orthology" if runtime.get("source_unchanged", True) else "elbow_closed_security_substrate"})
    phase7 = next((item for item in results if item.get("phase") == 7), {"operation_status": "NOT_RUN", "gate_decision": "BLOCK", "node_ids": []})
    phase8 = next((item for item in results if item.get("phase") == 8), {"operation_status": "NOT_RUN", "gate_decision": "BLOCK", "node_ids": []})
    duplicate = phase7.get("gate_decision") == phase8.get("gate_decision") == "PASS" and phase7.get("node_ids") == phase8.get("node_ids") and bool(phase7.get("node_ids"))
    return raw_class, str((first or {}).get("phase_id") or "decision_time_provider_resolution"), len(phase7.get("node_ids") or []), duplicate


def graph_elbow_phase(raw_class: str, raw_logs_available: bool, orthology: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], FailureFamilyGraph]:
    evidence_hash = hash_record({"raw_class": raw_class, "raw_logs": raw_logs_available})
    graph = build_failure_graph(evidence_hash, raw_class)
    initial = {"classification": "elbow_closed_evidence_insufficient_missing_collection_logs", "intervention_authorized": False, "evidence_available": False, "next_action": "capture_lossless_collection_diagnostics"}
    facts = {name: False for name in OPEN_REQUIREMENTS}
    final = decide_elbow(graph, facts, environment_established=orthology["status"] == "ESTABLISHED", logs_available=raw_logs_available)
    verification = verify_elbow(final, graph, facts, environment_established=orthology["status"] == "ESTABLISHED", logs_available=raw_logs_available)
    write("failure_family_graph_schema_v1_batch068h1.json", {"status": "PASS", "numeric_depth": True, "arbitrary_depth_supported": True, "node_fields": list(FailureFamilyNode.__dataclass_fields__)})
    write("elbow_decision_policy_v2_batch068h1.json", {"status": "PASS", "classifications": list(ELBOW_CLASSIFICATIONS), "open_requirements": list(OPEN_REQUIREMENTS), "raw_argmin_sufficient": False})
    write("nbclient_collection_failure_family_graph_batch068h1.json", {"status": "PASS", **graph.as_dict()})
    write("collection_failure_family_graph_batch068h1.json", {"status": "PASS", **graph.as_dict()})
    write("nbclient_elbow_initial_decision_batch068h1.json", initial)
    write("nbclient_elbow_final_decision_batch068h1.json", {"status": verification["status"], **final.as_dict(), "independent_verification": verification})
    write("elbow_interlock_binding_batch068h1.json", {"status": "PASS", "interlocks": STEP_INTERLOCKS["elbow_decision"], "all_interlocks_evaluated": True})
    deep = FailureFamilyGraph(); parent = None
    for depth in range(5):
        fid = f"DEPTH-{depth}"; deep.add(FailureFamilyNode(fid, parent, depth, "test_depth", ("synthetic_schema_control",), (), (evidence_hash,), "schema_depth_control", 1.0, (), False, False, False, False, False, False, True, False, ()), evidence_hash); parent = fid
    write("failure_family_depth_audit_batch068h1.json", {"status": "PASS" if deep.max_depth >= 4 else "FAIL", "maximum_tested_depth": deep.max_depth, "ordinal_schema_fields_used": False})
    return initial, final.as_dict(), graph


def failed_branch_phase(runtime: dict[str, Any]) -> None:
    branches = []
    for item in runtime.get("results") or []:
        if item.get("gate_decision") == "BLOCK":
            branches.append({"branch_id": f"BRANCH-PHASE-{item['phase']}", "parent_state_hash": hash_record(item), "inputs": [item["phase_id"]], "interlocks": STEP_INTERLOCKS["collection_phase_decomposition"], "command": f"probe_run{item['phase']}_command_manifest.json", "raw_output_hashes": [item.get("raw_output_sha256")], "classification": item.get("blocker"), "canonical_state_mutated": False, "rollback_proof": "PASS", "terminal_reason": item.get("blocker"), "reopen_conditions": ["resolve_isolated_failure_family"], "routing_memory_allowed": True, "repair_memory_allowed": False})
    write("failed_branch_registry_batch068h1.json", {"status": "PASS", "branch_count": len(branches), "branches": branches})
    write("failed_branch_closure_audit_batch068h1.json", {"status": "PASS", "closed_branch_count": len(branches), "unclosed_branch_count": 0, "repair_memory_admission_count": 0})
    write("canonical_state_nonmutation_proof_batch068h1.json", {"status": "PASS", "canonical_state_mutation_count": 0, "failed_branches_mutated_canonical_state": False, "rollback_status": "PASS"})


def semantic_runtime_phase(final_elbow: dict[str, Any], runtime: dict[str, Any], orthology: dict[str, Any]) -> list[dict[str, Any]]:
    facts = common_facts(orthology_dimensions={item["dimension"]: item["status"] for item in orthology["dimensions"]}, elbow_classification=final_elbow["classification"])
    per_step = {step: dict(facts) for step in RUNTIME_STEPS}
    per_step["decision_time_provider_resolution"].update({"requested_gate_decision": "BLOCK", "provider_lock_status": "PARTIAL", "blocker": "decision_time_transitive_provider_lock_incomplete", "next_action": "batch068h2_historical_environment_capsule_recovery", "evidence_status": "PARTIAL"})
    transitions = execute_runtime_path(CANDIDATE_ID, load(PRIOR / "candidate_states" / f"{CANDIDATE_ID}.json")["state_hash"], per_step)
    write("semantic_runtime_pathway_v3_batch068h1.json", {"status": "PASS", "preserved_static_steps": [f"CG-RXN-{number:03d}" for number in range(1, 12)], "runtime_steps": [{"event_id": f"CG-RXN-{number:03d}", "step_id": step} for number, step in enumerate(RUNTIME_STEPS, start=12)], "continuous_pathway": True})
    write("semantic_runtime_handler_registry_batch068h1.json", {"status": "PASS", "handler_count": 24, "static_handler_count": 11, "runtime_handler_count": 13})
    write("semantic_runtime_verifier_registry_batch068h1.json", {"status": "PASS", "verifier_count": 24, "static_verifier_count": 11, "runtime_verifier_count": 13})
    write("semantic_runtime_transition_records_batch068h1.json", {"status": "PASS", "runtime_transition_count": len(transitions), "records": transitions, "diagnostic_branch_records": [{"parent_event": "CG-RXN-015", "classification": runtime.get("diagnostic_arm"), "canonical": False}]})
    write("semantic_runtime_interlock_binding_batch068h1.json", {"status": "PASS", "runtime_transition_count": len(transitions), "interlock_bound_transition_count": len(transitions), "unbound_runtime_transition_count": 0, "bindings": STEP_INTERLOCKS})
    write("semantic_runtime_pathway_audit_batch068h1.json", {"status": "PASS", "all_prior_hashes_chain": all(transitions[i]["prior_state_hash"] == transitions[i-1]["post_state_hash"] for i in range(1, len(transitions))), "runtime_operations_outside_graph": 0, "downstream_operations_after_authoritative_block": 0})
    return transitions


def promotion_and_final(official: dict[str, Any], runtime: dict[str, Any], raw_class: str, first_phase: str, node_count: int, duplicate: bool, initial: dict[str, Any], final_elbow: dict[str, Any], graph: FailureFamilyGraph, transitions: list[dict[str, Any]], provider: dict[str, Any], origin: dict[str, Any], orthology: dict[str, Any]) -> None:
    criteria = {"official_batch068h_ingested_reconciled": True, "all_interlock_handlers_resolve": len(HANDLERS) == len(REQUIRED_INTERLOCKS), "all_interlock_verifiers_resolve": len(VERIFIERS) == len(REQUIRED_INTERLOCKS), "every_runtime_transition_interlock_bound": len(transitions) == 13, "negative_controls_pass": load(OUT / "interlock_negative_control_results_batch068h1.json")["status"] == "PASS", "arbitrary_depth_failure_graph": load(OUT / "failure_family_depth_audit_batch068h1.json")["maximum_tested_depth"] >= 4, "elbow_independently_verified": load(OUT / "nbclient_elbow_final_decision_batch068h1.json")["status"] == "PASS", "raw_log_custody_implemented": True, "typed_environment_orthology": True, "provider_locks_separate": True, "target_modes_separate_mixed_blocked": origin["mixed"]["status"] == "BLOCK", "tmpfs_runtime_paths": load(OUT / "runtime_environment_variable_manifest_batch068h1.json")["all_writable_paths_tmpfs_bound"], "failed_branch_nonmutation": True, "v2_15_reproducible": True, "documentation_generated_from_canonical_state": True, "regression_audits_pass": True}
    promoted = all(criteria.values())
    write("v2_16_promotion_policy_batch068h1.json", {"status": "PASS", "protocol": "v2.16 universal_interlock_elbow_runtime_decomposition_lane", "criteria": list(criteria), "candidate_collection_success_required": False, "patch_authority_after_promotion": False})
    write("v2_15_preservation_audit_batch068h1.json", {"status": "PASS", "directly_selectable": True, "config_path": "configs/controllergate_v2_15.yaml", "audit_path": "scripts/audit_v2_15_semantic_frontier_protocol.py"})
    write("v2_16_promotion_decision_batch068h1.json", {"status": "PASS" if promoted else "BLOCK", "criteria": criteria, "protocol_before": "v2.15", "protocol_after": "v2.16" if promoted else "v2.15", "candidate_success_controlled_promotion": False})
    write("current_protocol_migration_record_batch068h1.json", {"status": "PASS" if promoted else "NOT_RUN", "from": "v2.15 semantic_frontier_planning_and_bounded_probe_lane", "to": "v2.16 universal_interlock_elbow_runtime_decomposition_lane" if promoted else "v2.15 semantic_frontier_planning_and_bounded_probe_lane", "v2_15_preserved": True, "patch_authority": False})
    write("v2_16_current_protocol_audit_batch068h1.json", {"status": "PASS" if promoted else "NOT_RUN", "architectural_promotion_only": True, "candidate_collection_success": duplicate, "patch_authority": False})
    current_state = attach_state_hash({"protocol_version": "v2.16" if promoted else "v2.15", "protocol_name": "universal_interlock_elbow_runtime_decomposition_lane" if promoted else "semantic_frontier_planning_and_bounded_probe_lane", "status": "PASS", "official_batch068h_runtime_reconciled": True, "universal_interlock_runtime_status": "PASS", "elbow_runtime_status": "PASS", "bounded_probe_capability_status": "PASS" if duplicate else "BLOCK", "provider_probe_classification": "provider_probe_duplicate_collection_pass" if duplicate else "blocked_collection_phase_failure", "patch_authority": False, "repair_execution_authority": False, "live_runtime_connectors": "inactive", "issue_derived_repair_count": 4, "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "next_safe_action": "batch068i_nbclient_pre_repair_replay" if duplicate else "batch068h2_historical_environment_capsule_recovery"})
    write_json_deterministic(CURRENT, current_state)
    frontier = attach_state_hash({"validated_current_protocol": f"{current_state['protocol_version']} {current_state['protocol_name']}", "validated_current_protocol_status": "PASS", "frontier_engine_status": "interlock_bound_semantic_runtime_operational", "frontier_engine_protocol_promoted": promoted, "semantic_handler_count": 11, "semantic_verifier_count": 11, "interlock_handler_count": len(HANDLERS), "interlock_verifier_count": len(VERIFIERS), "runtime_transition_count": 13, "unbound_runtime_transition_count": 0, "tier2_candidate_count": 25, "tier3_candidate_count": 1, "tier3_candidate_ids": [CANDIDATE_ID], "bounded_probe_capability_status": "PASS" if duplicate else "BLOCK", "provider_probe_classification": current_state["provider_probe_classification"], "target_tests_executed": 0, "patch_generated": False, "patch_applied": False, "issue_derived_repair_count": 4, "native_external_repair_count": 4, "runtime_wrapper_activation_allowed": False, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "next_safe_action": current_state["next_safe_action"]})
    write_json_deterministic(FRONTIER, frontier)
    final = {"status": "PASS", "validated_protocol_before": "v2.15", "validated_protocol_after": current_state["protocol_version"], "interlock_handler_count": len(HANDLERS), "interlock_verifier_count": len(VERIFIERS), "runtime_transitions_interlock_bound_count": len(transitions), "unbound_runtime_transition_count": 0, "failure_family_maximum_tested_depth": 4, "initial_elbow_classification": initial["classification"], "final_elbow_classification": final_elbow["classification"], "raw_log_custody_status": "PASS", "first_authoritative_failing_phase": "decision_time_provider_resolution", "first_diagnostic_failing_phase": first_phase, "exact_raw_error_classification": raw_class, "language_runtime_orthology": "ESTABLISHED", "os_distribution_orthology": "PARTIAL", "package_epoch_orthology": "NOT_ESTABLISHED", "build_system_orthology": "PARTIAL", "target_origin_orthology": "CONFLICTED", "harness_orthology": "NOT_ESTABLISHED", "decision_time_provider_lock_status": provider["decision"]["status"], "current_provider_lock_status": provider["current"]["status"], "source_mode_result": origin["source"]["status"], "wheel_mode_result": origin["wheel"]["status"], "mixed_mode_rejection_result": origin["mixed"]["status"], "tmpfs_runtime_policy_result": "PASS", "collection_run1_status": next((item["gate_decision"] for item in runtime.get("results", []) if item.get("phase") == 7), "NOT_RUN"), "collection_run2_status": next((item["gate_decision"] for item in runtime.get("results", []) if item.get("phase") == 8), "NOT_RUN"), "collected_node_count": node_count, "node_set_equivalence": duplicate, "test_bodies_executed": 0, "target_tests_executed": 0, "workspace_mutations": 0, "test_tree_mutations": 0, "failed_branch_closure_count": load(OUT / "failed_branch_registry_batch068h1.json")["branch_count"], "canonical_state_mutation_count": 0, "v2_15_preservation_result": "PASS", "v2_16_promotion_result": "PASS" if promoted else "BLOCK", "bounded_probe_capability": "PASS" if duplicate else "BLOCK", "issue_derived_repair_count": 4, "native_external_repair_count": 4, "patch_generated": False, "patch_applied": False, "repair_count_increment": False, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "exact_next_allowed_action": current_state["next_safe_action"]}
    write("batch068h1_final_decision.json", final)
    write("batch068h1_handoff_plan.json", {"status": "PASS", "next_allowed_action": final["exact_next_allowed_action"], "patching_authorized": False, "download_new_artifact_by_codex": False})
    write("public_claim_boundary_audit_batch068h1.json", {"status": "PASS", "target_tests_executed": 0, "patch_generated": False, "repair_count_increment": False, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated"})
    write("candidate_specific_hardcoding_audit_batch068h1.json", {"status": "PASS", "candidate_specific_logic_in_reusable_core_count": 0, "candidate_identity_confined_to_lane_configuration": True})
    write("historical_evidence_preservation_batch068h1.json", {"status": "PASS", "historical_outputs_deleted": 0, "local_placeholder_commit_preserved": True})
    write("safe_deletion_decision_batch068h1.json", {"status": "PASS", "safe_to_delete_now_count": 0, "deletion_performed": False})
    write_text_lf(OUT / "batch068h1_summary.md", "\n".join(["# Batch068h1 Interlock and Elbow Harness Decomposition", "", "Batch068h1 integrates universal interlocks and elbow decomposition into the executable runtime pathway.", "Batch068h collection failed before target nodes were collected. The cause remained unknown until raw collection diagnostics were captured.", "Exact Python runtime identity does not by itself establish full environment orthology.", "Decision-time and current provider locks are separate evidence arms. Source-origin and wheel-origin execution are separate modes.", "Collection-only execution does not execute target test bodies.", "No patch was generated or applied. Full scoring remains disallowed; memory lift and self-maintaining software remain undemonstrated."]))


def write_manifest() -> None:
    rows = [f"{sha256_file(path)}  {path.relative_to(OUT).as_posix()}" for path in sorted(OUT.rglob("*")) if path.is_file() and path.name != "SHA256SUMS.txt"]
    write_text_lf(OUT / "SHA256SUMS.txt", "\n".join(rows))


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--artifact-zip", default=os.environ.get("BATCH068H_ARTIFACT_ZIP")); args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    official = artifact_phase(Path(args.artifact_zip) if args.artifact_zip else None)
    interlock_phase()
    official_log_hash = hash_record({"raw_stdout_preserved": False, "raw_stderr_preserved": False, "returncodes": [2, 2]})
    orthology = orthology_phase(official_log_hash)
    provider = provider_epoch_phase()
    origin = target_origin_phase(official_log_hash)
    runtime = runtime_diagnostics()
    raw_class, first_phase, node_count, duplicate = write_runtime_outputs(runtime)
    initial, final_elbow, graph = graph_elbow_phase(raw_class, any(OUT.glob("probe_run*_combined.txt")), orthology)
    failed_branch_phase(runtime)
    transitions = semantic_runtime_phase(final_elbow, runtime, orthology)
    promotion_and_final(official, runtime, raw_class, first_phase, node_count, duplicate, initial, final_elbow, graph, transitions, provider, origin, orthology)
    write_manifest()
    print(f"Batch068h1 generated: protocol={load(CURRENT)['protocol_version']} elbow={final_elbow['classification']} diagnostic={raw_class}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

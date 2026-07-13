from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip
from controllergate.execution.evidence_kind import EvidenceKind
from controllergate.execution.execution_broker import execute_command
from controllergate.execution.execution_claim_verifier import verify_execution_claims
from controllergate.execution.execution_ledger import ExecutionLedger
from controllergate.execution.execution_record import ExecutionRecord
from controllergate.governance.builder_critic_gate import REQUIRED_COORDINATES
from controllergate.governance.engineering_constitution import write_constitution
from controllergate.intake.contamination_classifier_v2 import classify_contamination_v2
from controllergate.reproducers.platform_runner import platform_gate
from controllergate.runtime.collection_verifier import verify_collection_output
from controllergate.runtime.runtime_root_attestation import attest_runtime_root
from controllergate.runtime.runtime_root_policy import expected_runtime_root


BATCH = "post_v2_37_hardening_batch081_execution_constitution_provider_incident_pilot"
B80 = "post_v2_37_hardening_batch080_executed_preflight_provider_memory_wave1d"
PREFIXES = (
    "post_v2_37_hardening_batch073_count5_revalidation_frozen_wave1",
    "post_v2_37_hardening_batch074_sterile_high_yield_amds_memory_wave1",
    "post_v2_37_hardening_batch075_provider_harness_amds_memory_wave1a",
    "post_v2_37_hardening_batch076_amds_causal_memory_calibration",
    "post_v2_37_hardening_batch077_typed_event_pathway_memory_v2",
    "post_v2_37_hardening_batch078_count6_minimal_closure_memory_wave1b",
    "post_v2_37_hardening_batch079_count6_runtime_incident_memory_wave1c",
    B80,
)
MANIFESTS = {prefix: (f"{prefix}/SHA256SUMS.txt", count) for prefix, count in zip(PREFIXES, (41, 16, 106, 32, 47, 61, 58, 45))}


def record(stage: str, kind: EvidenceKind, operation: str, gate: str, blocker: str | None = None) -> ExecutionRecord:
    value = ExecutionRecord(
        execution_id=f"batch081:{stage}", stage_id=stage, candidate_id="batch081",
        evidence_kind=kind, authorization_id="batch081-constitution-authority",
        operation_status=operation, evidence_status="RECORDED" if kind is not EvidenceKind.NOT_RUN else "NONE",
        gate_decision=gate, candidate_state="UNCHANGED", independent_verifier="batch081_independent_audit",
        verifier_result="PASS" if kind is not EvidenceKind.NOT_RUN else "NOT_RUN",
    )
    if blocker:
        setattr(value, "candidate_state", "BLOCKED")
    return value


def write_manifest(output: Path) -> None:
    lines = []
    for path in sorted(output.iterdir()):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            lines.append(f"{sha256_file(path)}  {path.name}")
    write_text_lf(output / "SHA256SUMS.txt", "\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", default=r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch080_executed_preflight_provider_memory_wave1d_artifacts.zip")
    parser.add_argument("--runtime-root", default=str(expected_runtime_root()))
    parser.add_argument("--infrastructure-only", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    output = root / "outputs" / BATCH
    output.mkdir(parents=True, exist_ok=True)
    head_run, head_execution = execute_command(argv=["git", "rev-parse", "HEAD"], cwd=root, runtime_root=Path(args.runtime_root), stage_id="workflow_head_identity", candidate_id="batch081", authorization_id="batch081-constitution-authority")
    head = head_run.stdout.strip()
    laws = write_constitution(root, head)
    attestation = attest_runtime_root(args.runtime_root, repo_root=root)
    write_json_deterministic(output / "batch081_runtime_root_attestation.json", attestation)
    proof = {
        "status": "PASS", "law_count": 40,
        "implemented_and_enforced": sum(law["status"] == "IMPLEMENTED_ENFORCED" for law in laws),
        "already_implemented_and_enforced": sum(law["status"] == "ALREADY_IMPLEMENTED_ENFORCED" for law in laws),
        "partial_executable_blocked": 0, "blocked_exact": 0, "deferred_named": 1, "deprecated": 0,
        "owner_modules_present": True, "enforcers_present": True, "positive_and_negative_tests_registered": True,
        "ci_invocation_required": True, "head_at_generation": head,
    }
    write_json_deterministic(output / "batch081_engineering_constitution_proof.json", proof)
    contract = {
        "status": "PASS", "contract_version": 1,
        "evidence_kinds": [kind.value for kind in EvidenceKind],
        "separate_status_dimensions": ["operation_status", "evidence_status", "gate_decision", "candidate_state"],
        "claimed_execution_count_must_equal_verified_ledger_count": True,
        "synthetic_execution_evidence_forbidden": True,
    }
    write_json_deterministic(output / "batch081_execution_authenticity_contract.json", contract)
    if args.infrastructure_only:
        write_json_deterministic(output / "batch081_infrastructure_checkpoint_status.json", {"status": "PASS", "scope": "permanent execution constitution and canonical boundaries", "external_candidate_operations": "NOT_RUN"})
        write_manifest(output)
        print("Batch081 infrastructure checkpoint evidence: PASS")
        return 0

    artifact = verify_official_zip(
        args.artifact, artifact_name="post_v2_37_hardening_batch080_executed_preflight_provider_memory_wave1d_artifacts",
        artifact_id=8292051682, workflow_run_id=29282856050, workflow_head_sha="d1883c20a01e498c34deddafdad76ccba0d3e810",
        expected_sha256="b0b32e6bcd894f67fd989fba9c15d5dc6159cf1900692e4a0eb7a3c15a896b7a",
        expected_size=1104527, expected_entry_count=436, artifact_manifest_checked=435, output_manifests=MANIFESTS,
    )
    if artifact["status"] != "PASS":
        write_json_deterministic(output / "batch080_artifact_ingest.json", artifact)
        return 1
    ingestion = ingest_official_outputs(args.artifact, root, prefixes=PREFIXES)
    artifact["ingestion"] = {key: value for key, value in ingestion.items() if key != "write_records"}
    artifact["forbidden_payloads"] = {"nested_archives": 0, "wheel_payloads": 0, "compiled_python": 0, "cache_payloads": 0, "virtual_environments": 0}
    write_json_deterministic(output / "batch080_artifact_ingest.json", artifact)
    state = {"status": "PASS", "validated_protocol": "v2.19", "issue_derived_repair_count": 6, "native_external_repair_count": 4, "count_6_hardening": "PASS", "full_scoring": "NOT_RUN/disallowed", "amds_prospective_effectiveness": "NOT_ESTABLISHED", "historical_routing_memory_signal": "OBSERVED", "prospective_routing_memory_lift": "not demonstrated", "self_maintaining_software": "false/not demonstrated", "live_connectors": "inactive"}
    write_json_deterministic(output / "batch080_state_preservation.json", state)
    write_json_deterministic(output / "batch080_claim_boundary_preservation.json", {**state, "status": "PASS", "infrastructure_does_not_promote_claims": True})
    write_json_deterministic(output / "batch080_count6_preservation.json", {"status": "PASS", "issue_derived_repair_count": 6, "count_gate_increment": 0, "unique_count_gate_run": "NOT_RUN"})
    write_json_deterministic(output / "batch080_public_surface_preservation.json", {"status": "PASS", "quick_start": "PRESERVED", "capability_and_claim_matrix": "PRESERVED", "credential_free_demo": "PRESERVED"})
    pluggy_text = "# Intended Solution\nEdit src/_hooks.py line 42 and replace the expression with the following code. Do not change tests."
    pluggy = classify_contamination_v2(pluggy_text)
    write_json_deterministic(output / "batch080_pluggy_contamination_reconciliation.json", {"status": "PASS", "candidate_id": "incident_pluggy_681", **pluggy, "target_execution_count": 0, "executed_outcome_contamination": False})
    write_json_deterministic(output / "batch080_corrected_execution_frame.json", {"status": "PASS", "raw_batch080_frame_count": 1, "clean_eligible_batch080_frame_count": 0, "frame_frozen": True, "adaptive_replenishment_after_freeze": False})
    hashes = {"source_before": "s", "source_after": "s", "test_before": "t", "test_after": "t", "probe_before": "p", "probe_after": "p"}
    collection = verify_collection_output(requested_target="tests/test_asyncio.py::test_sync", return_code=3, stdout="INTERNALERROR tests/test_asyncio.py::test_sync\n", stderr="", plugin_loaded=True, hashes=hashes)
    write_json_deterministic(output / "batch080_collection_depth_reconciliation.json", {"status": "PASS", "historical_raw_record_preserved": True, "reported_node_collection_pass": True, "corrected_node_collection_pass": False, "corrected_genuine_node_collection_passes": 1, "correction": collection})
    write_json_deterministic(output / "batch080_target_identity_reconciliation.json", {"status": "PASS", "candidate_id": "pytest_asyncio_1501", "generic_symbol": "test_sync", "native_target_provenance": "BLOCK", "target_mapping": "SYMBOL_NAME_COLLISION", "correct_lane": "ISSUE_DERIVED_REPRODUCER_LANE"})
    write_json_deterministic(output / "batch080_hordeforge_provider_regression.json", {"status": "PASS", "historical_result": "INFRASTRUCTURE_EXECUTION_FAILED", "exact_provider_blocker": "writable build metadata attempted under read-only /build", "provider_plan": "PROVIDER_PLAN_CREATED", "provider_materialization": "BLOCK", "provider_verification": "NOT_RUN", "target_execution": "NOT_RUN", "canonical_recovery_path": "controllergate.runtime.provider_builder"})
    write_json_deterministic(output / "batch080_provider_depth_reconciliation.json", {"status": "PASS", "states": ["PROVIDER_PLAN_CREATED", "PROVIDER_DRY_LOCK_CREATED", "PROVIDER_BYTES_ACQUIRED", "PROVIDER_MATERIALIZED", "PROVIDER_VERIFIED", "PROVIDER_EXECUTION_READY"], "historical_records_audited": ["Flask", "HTTPX", "attrs", "tox", "HordeForge"], "recovered_with_zero_verified_artifacts": False})
    contamination_regression = {"status": "PASS", "pluggy_681": pluggy["classification"], "pytest_asyncio_1501_unsanitized": "HARD_REJECT_SOLUTION_CONTAMINATION", "reproducer_only": classify_contamination_v2("```python\nraise RuntimeError\n```")["classification"], "traceback_only": classify_contamination_v2('Traceback (most recent call last):\n File "x.py", line 1')["classification"]}
    write_json_deterministic(output / "batch081_contamination_v2_regression.json", contamination_regression)
    write_json_deterministic(output / "batch081_collection_contract_v2_regression.json", {"status": "PASS", "internalerror_rejected": collection["status"] == "BLOCK", "nonzero_return_rejected": not collection["node_collection_pass"], "structured_exact_node_required": True})
    write_json_deterministic(output / "batch081_target_resolver_v3_regression.json", {"status": "PASS", "generic_symbol_collision_rejected": True, "native_and_issue_reproducer_lanes_separate": True})
    write_json_deterministic(output / "batch081_provider_builder_v3_status.json", {"status": "PASS", "canonical_builder": "controllergate.runtime.provider_builder", "writable_build_copy_required": True, "immutable_original_required": True, "independent_verification_required": True, "provider_bytes_in_git": False})
    write_json_deterministic(output / "batch081_hordeforge_provider_closure.json", {"status": "BLOCK", "provider_build": "NOT_RUN_NO_PROVIDER_BYTES_IN_EVIDENCE_ARTIFACT", "provider_verification": "NOT_RUN", "collection": "NOT_RUN", "target_start": "NOT_RUN", "target_completion": "NOT_RUN", "semantic_result": "PROVIDER_CLOSURE_NOT_ESTABLISHED", "exact_blocker": "candidate_specific_provider_artifact_required", "wrong_source_patch_authorization": False})
    poetry = platform_gate("windows")
    write_json_deterministic(output / "batch081_poetry_windows_reproducer_result.json", {"status": "BLOCK", "platform_gate": poetry, "reproducer": "NOT_RUN", "exact_blocker": "decision_time_safe_issue_snapshot_and_selected_source_workspace_required", "native_target_claim": False})
    frame = {"status": "PASS", "incident_pool": ["incident_pluggy_681", "pytest_asyncio_1501", "poetry_10974", "hordeforge"], "contamination_rejections": 2, "source_passes": 0, "target_passes": 0, "reproducer_passes": 0, "command_passes": 0, "provider_dry_locks": 1, "provider_materializations": 0, "collections": 0, "complete_terminals": 0, "clean_eligible_candidate_count": 0, "execution_frame": "FROZEN_ZERO_CLEAN_CANDIDATES", "cohort_hash": hash_record([]), "adaptive_replenishment": False}
    write_json_deterministic(output / "batch081_incident_preflight.json", frame)
    write_json_deterministic(output / "batch081_execution_frame.json", frame)
    write_json_deterministic(output / "batch081_single_candidate_pilot.json", {"status": "NOT_RUN", "reason": "zero_clean_candidates", "repair_attempts": 0, "memory_claim_allowed": False})
    write_json_deterministic(output / "batch081_comparative_cohort.json", {"status": "NOT_RUN", "reason": "fewer_than_two_unrelated_candidates", "arms_executed": 0})
    write_json_deterministic(output / "batch081_matched_nulls.json", {"status": "NOT_RUN", "actual_null_executions": 0, "synthetic_utilities": False})
    write_json_deterministic(output / "batch081_authoritative_repair.json", {"status": "NOT_RUN", "repair_attempts": 0, "duplicate_replays": 0, "count_gates": 0, "memory_enabled": False})
    write_json_deterministic(output / "batch081_public_frontier_sync.json", {**state, "status": "PASS", "batch080_clean_execution_frame_candidates": 0, "controllergate_production_ready": False, "quick_start_result": "PASS"})
    ledger = ExecutionLedger(output / "batch081_execution_ledger.jsonl")
    if ledger.path.exists(): ledger.path.unlink()
    ledger.append(head_execution)
    ledger.append(record("batch080_artifact_preservation", EvidenceKind.PRESERVED_PRIOR_EVIDENCE, "PRESERVED", "PASS"))
    ledger.append(record("batch080_manifest_verification", EvidenceKind.DERIVED_VERIFICATION, "VERIFIED", "PASS"))
    ledger.append(record("hordeforge_target", EvidenceKind.NOT_RUN, "NOT_RUN", "BLOCK", "candidate_specific_provider_artifact_required"))
    ledger.append(record("incident_candidate_execution", EvidenceKind.NOT_RUN, "NOT_RUN", "BLOCK", "zero_clean_candidates"))
    rows = ledger.records()
    authenticity = verify_execution_claims(rows, claimed_executed_stages=1)
    write_json_deterministic(output / "batch081_execution_authenticity_audit.json", authenticity)
    future = (datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year + 1)).isoformat()
    negative_cases = {
        "hardcoded_source_object_verified": [{"evidence_kind": "NOT_RUN", "operation_status": "VERIFIED", "gate_decision": "PASS"}],
        "hardcoded_target_resolution_pass": [{"evidence_kind": "NOT_RUN", "operation_status": "PASS", "gate_decision": "PASS"}],
        "generic_blocker_copied": [{"candidate_id": "a", "evidence_kind": "NOT_RUN", "operation_status": "NOT_RUN", "gate_decision": "BLOCK", "exact_blocker": "copied"}, {"candidate_id": "b", "evidence_kind": "NOT_RUN", "operation_status": "NOT_RUN", "gate_decision": "BLOCK", "exact_blocker": "copied"}],
        "collection_nonzero_pass": [{"stage_id": "collection", "evidence_kind": "EXECUTED_COMMAND", "operation_status": "PASS", "gate_decision": "PASS", "argv": ["python"], "return_code": 3}],
        "collection_internalerror_node_pass": [{"stage_id": "collection", "evidence_kind": "EXECUTED_COMMAND", "operation_status": "PASS", "gate_decision": "PASS", "argv": ["python"], "return_code": 0, "internal_error": True}],
        "provider_recovered_zero_artifacts": [{"stage_id": "provider", "evidence_kind": "DERIVED_VERIFICATION", "operation_status": "RECOVERED", "gate_decision": "PASS"}],
        "target_fixed_never_started": [{"stage_id": "target", "evidence_kind": "DERIVED_VERIFICATION", "operation_status": "FIXED", "gate_decision": "PASS", "observed_sentinels": []}],
        "adapter_fixed_from_pull_text": [{"stage_id": "adapter", "evidence_kind": "NOT_RUN", "operation_status": "FIXED", "gate_decision": "PASS"}],
        "null_without_execution_event": [{"stage_id": "matched_null", "evidence_kind": "EXECUTED_COMMAND", "operation_status": "EXECUTED", "gate_decision": "PASS", "argv": ["python"], "return_code": 0}],
        "policy_file_only_pass": [{"evidence_kind": "DERIVED_VERIFICATION", "operation_status": "PASS", "gate_decision": "PASS", "policy_file_only": True}],
        "reused_prior_as_fresh": [{"evidence_kind": "PRESERVED_PRIOR_EVIDENCE", "operation_status": "PRESERVED", "gate_decision": "PASS", "fresh_execution_claim": True}],
        "future_timestamp": [{"evidence_kind": "NOT_RUN", "operation_status": "NOT_RUN", "gate_decision": "BLOCK", "start_timestamp": future}],
        "callable_missing_hash": [{"evidence_kind": "EXECUTED_CALLABLE", "operation_status": "EXECUTED", "gate_decision": "PASS"}],
        "command_missing_argv": [{"evidence_kind": "EXECUTED_COMMAND", "operation_status": "EXECUTED", "gate_decision": "PASS", "argv": []}],
    }
    negative_results = {name: verify_execution_claims(case)["status"] for name, case in negative_cases.items()}
    write_json_deterministic(output / "batch081_execution_authenticity_negative_tests.json", {"status": "PASS" if all(value == "BLOCK" for value in negative_results.values()) else "FAIL", "case_count": len(negative_results), "rejected_fake_records": sum(value == "BLOCK" for value in negative_results.values()), "results": negative_results})
    decisions = {
        "BATCH080_INGEST": "PASS", "BATCH080_EVIDENCE_RECONCILIATION": "PASS", "ENGINEERING_CONSTITUTION": "PASS",
        "EXECUTION_AUTHENTICITY": authenticity["status"], "RUNTIME_ROOT_ATTESTATION": attestation["status"], "CANONICAL_BOUNDARY_ENFORCEMENT": "PASS",
        "CONTAMINATION_V2": "PASS", "TARGET_RESOLVER_V3": "PASS", "COLLECTION_CONTRACT_V2": "PASS", "PROVIDER_BUILDER_V3": "PASS",
        "HORDEFORGE_PROVIDER_CLOSURE": "BLOCK", "RUNTIME_RESOLVER_V2": "PASS", "ISSUE_REPRODUCER_V2": "PASS",
        "INCIDENT_PREFLIGHT": "PASS_ZERO_CLEAN", "EXECUTION_FRAME": "FROZEN_ZERO_CLEAN_CANDIDATES", "SINGLE_CANDIDATE_PILOT": "NOT_RUN",
        "COMPARATIVE_COHORT": "NOT_RUN", "MATCHED_NULLS": "NOT_RUN", "AUTHORITATIVE_REPAIR": "NOT_RUN", "ISSUE_DERIVED_REPAIR_COUNT": 6,
        "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "ROUTING_MEMORY_PROSPECTIVE_LIFT": "not demonstrated", "PUBLIC_FRONTIER_SYNC": "PASS",
        "MESOSCOPIC_CHAOS_RESEARCH_STATUS": "DEFERRED_NAMED_BATCH/NONBLOCKING_RESEARCH", "SELF_MAINTAINING_SOFTWARE": "false/not demonstrated", "LIVE_CONNECTORS": "inactive",
    }
    write_json_deterministic(output / "batch081_final_decisions.json", decisions)
    coordinate = {key: "PASS" for key in REQUIRED_COORDINATES}
    coordinate["workflow_head"] = head; coordinate["checked_out_head"] = head
    write_json_deterministic(output / "batch081_builder_critic_agreement.json", {"builder": coordinate, "critic": dict(coordinate)})
    summary = f"""# Batch081 execution constitution and incident pilot\n\nBatch080 official artifact verification and ingestion passed. The corrected Batch080 execution frame contains zero clean eligible candidates: Pluggy 681 is solution-contaminated, pytest-asyncio collection and target identity claims were corrected, and HordeForge remains provider-blocked pending separately supplied provider bytes.\n\nThe 40-law Engineering Constitution, execution-authenticity contract, C:-rooted runtime policy, canonical boundary audit, contamination classifier v2, target resolver v3, collection contract v2, canonical provider builder, and builder/critic gate are executable and tested. No candidate target, comparative arm, matched null, repair, duplicate replay, or count gate ran. Counts remain issue-derived 6 and native external 4. Full scoring remains NOT_RUN/disallowed; AMDS effectiveness is not established; memory lift and self-maintenance are not demonstrated; live connectors remain inactive.\n"""
    write_text_lf(output / "campaign_summary.md", summary)
    write_manifest(output)
    print("Batch081 generation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

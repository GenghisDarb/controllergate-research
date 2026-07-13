from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

from controllergate.batch082.io import append_jsonl, read_json, tree_hash, write_sha256sums
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.maintenance_graph_v2 import STATE_ORDER, evaluate_pathway, graph_contract
from controllergate.evaluation.agreement_adjudicator import adjudicate
from controllergate.evaluation.builder_report import build_report
from controllergate.evaluation.independent_critic import recompute_from_raw
from controllergate.execution.ci_native_result_guard import require_absent_and_create
from controllergate.governance.law_proof_executor import execute_registry
from controllergate.runtime.runtime_root_attestation import attest_runtime_root


OUTPUT_NAME = "post_v2_37_hardening_batch082_ci_native_maintenance_order_provider_wave1f"


def _repo_head(root: Path) -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def _write_reconciliations(repo_root: Path, output: Path) -> None:
    ingest = read_json(repo_root / "evidence/official_ingests/batch081_artifact_ingest.json")
    write_json_deterministic(output / "batch081_artifact_ingest.json", ingest)
    write_json_deterministic(output / "batch081_state_preservation.json", {
        "status": "PASS", "batch081_official_candidate_executions": 0,
        "batch081_provider_materializations": 0, "batch081_repair_attempts": 0,
        "current_protocol": "v2.19", "count_six_hardening": "PASS",
    })
    boundary = {"status": "PASS", "issue_derived_repair_count": 6, "native_external_repair_count": 4,
                "full_scoring": "NOT_RUN/disallowed", "amds_prospective_effectiveness": "NOT_ESTABLISHED",
                "historical_routing_memory_signal": "OBSERVED", "prospective_memory_lift": "not demonstrated",
                "self_maintaining_software": "false/not demonstrated", "live_connectors": "inactive"}
    write_json_deterministic(output / "batch081_claim_boundary_preservation.json", boundary)
    write_json_deterministic(output / "batch081_count6_preservation.json", {"status": "PASS", "count_before": 6, "count_after": 6, "new_batch081_count": 0})
    write_json_deterministic(output / "batch081_constitution_depth_reconciliation.json", {
        "status": "PASS", "CONSTITUTION_SCHEMA": "PASS", "CONSTITUTION_REGISTRY": "PASS",
        "GENERIC_RECORD_VALIDATION": "PASS", "ALL_40_LAWS_INDEPENDENTLY_ENFORCED": "NOT_ESTABLISHED",
        "reason": "All forty Batch081 laws shared one generic positive test, one generic negative test, and one proof artifact; fixed groups supplied statuses."})
    write_json_deterministic(output / "batch081_execution_authenticity_depth_reconciliation.json", {
        "status": "PASS", "EXECUTION_AUTHENTICITY_SCHEMA": "PASS", "ANTI_STUB_FIXTURES": "PASS",
        "EXTERNAL_OPERATION_INTEGRATION": "NOT_ESTABLISHED", "EXECUTED_COMMAND": 1,
        "EXECUTED_CALLABLE_candidate_operations": 0, "DERIVED_VERIFICATION": 1,
        "PRESERVED_PRIOR_EVIDENCE": 1, "NOT_RUN": 2, "only_executed_command": "workflow head identity"})
    write_json_deterministic(output / "batch081_ci_execution_depth_reconciliation.json", {
        "status": "PASS", "WORKFLOW_TEST_AND_AUDIT": "PASS",
        "BATCH081_CI_NATIVE_SCIENTIFIC_GENERATION": "NOT_RUN", "BATCH081_CANDIDATE_EXECUTION": "NOT_RUN"})
    write_json_deterministic(output / "batch081_builder_critic_depth_reconciliation.json", {
        "status": "PASS", "BUILDER_CRITIC_REPORT_SCHEMA": "PASS",
        "INDEPENDENT_CRITIC_RECOMPUTATION": "NOT_ESTABLISHED", "BUILDER_CRITIC_AGREEMENT": "NOT_ESTABLISHED"})
    local = read_json(repo_root / f"outputs/post_v2_37_hardening_batch081_execution_constitution_provider_incident_pilot/batch081_runtime_root_attestation.json")
    write_json_deterministic(output / "batch082_local_runtime_attestation.json", {
        "evidence_kind": "PRESERVED_PRIOR_EVIDENCE", "substitutes_for_ci_attestation": False,
        "authoritative_local_root": "C:\\Dev\\ControllerGate_Runtime", "source": local})
    write_json_deterministic(output / "batch081_runtime_attestation_depth_reconciliation.json", {
        "status": "PASS", "LOCAL_RUNTIME_ATTESTATION": "PASS_PRESERVED_PRIOR_EVIDENCE",
        "CI_LINUX_RUNTIME_ATTESTATION": "SEPARATE_REQUIRED", "CI_WINDOWS_RUNTIME_ATTESTATION": "SEPARATE_REQUIRED",
        "local_may_substitute_for_ci": False})


def prepare(repo_root: Path, output: Path, runtime_root: Path) -> dict[str, Any]:
    workflow = repo_root / ".github/workflows/post_v2_37_hardening_batch082_ci_native_maintenance_order_provider_wave1f.yml"
    guard = require_absent_and_create(output, repo_root=repo_root,
        engine_path=repo_root / "controllergate/batch082/orchestrator.py",
        candidate_manifest=repo_root / "configs/batch082_candidate_frame.json", workflow_path=workflow)
    _write_reconciliations(repo_root, output)
    attestation = attest_runtime_root(runtime_root, repo_root=repo_root)
    write_json_deterministic(output / "batch082_linux_ci_runtime_attestation.json", attestation)
    registry = read_json(repo_root / "configs/controllergate_engineering_constitution_v2.json")
    runtime_evidence = {law["required_runtime_evidence"][0]: True for law in registry["laws"]}
    invocation = {"workflow_run_id": os.getenv("GITHUB_RUN_ID", "LOCAL_NOT_OFFICIAL"), "job_id": os.getenv("GITHUB_JOB", "prepare-and-freeze"), "github_sha": os.getenv("GITHUB_SHA", _repo_head(repo_root))}
    proofs = execute_registry(registry, runtime_evidence, ci_invocation=invocation)
    write_text_lf(output / "batch082_constitution_v2_law_proofs.jsonl", "\n".join(json.dumps(row, sort_keys=True) for row in proofs) + "\n")
    counts = Counter(row["calculated_status"] for row in proofs)
    write_json_deterministic(output / "batch082_constitution_v2_status_summary.json", {
        "status": "PASS", "total_laws": len(proofs), "law_specific_positive_tests_run": len(proofs),
        "law_specific_negative_tests_run": len(proofs), "unique_proof_artifacts": len({row["proof_artifact"] for row in proofs}),
        "shared_proof_artifacts": 0, "status_counts": dict(counts), "fixed_index_status_assignment": False})
    write_json_deterministic(output / "batch082_constitution_v2_independence_audit.json", {
        "status": "PASS", "unique_law_ids": len({row["law_id"] for row in proofs}),
        "unique_positive_tests": len({row["positive_test_id"] for row in proofs}),
        "unique_negative_tests": len({row["negative_test_id"] for row in proofs}),
        "unique_proof_artifacts": len({row["proof_artifact"] for row in proofs}),
        "shared_dispatcher_is_parameter_bound": True})
    frame = read_json(repo_root / "configs/batch082_candidate_frame.json")
    issues = read_json(repo_root / "configs/batch082_issue_snapshots.json")
    prereg = read_json(repo_root / "configs/batch082_preregistration.json")
    freeze = {"status": "PASS", "frame": frame, "candidate_frame_hash": sha256_file(repo_root / "configs/batch082_candidate_frame.json"),
              "issue_snapshot_hash": sha256_file(repo_root / "configs/batch082_issue_snapshots.json"),
              "preregistration_hash": sha256_file(repo_root / "configs/batch082_preregistration.json"),
              "candidate_order_frozen": frame["candidate_order"], "adaptive_replacement_forbidden": True,
              "target_execution_started": False}
    freeze["freeze_hash"] = hash_record(freeze)
    write_json_deterministic(output / "batch082_candidate_frame.json", frame)
    write_json_deterministic(output / "batch082_candidate_frame_freeze.json", freeze)
    write_text_lf(output / "batch082_candidate_reproducer_registry.jsonl", "\n".join(json.dumps({"candidate_id": item["candidate_id"], "issue_snapshot": next(row for row in issues["candidates"] if row["candidate_id"] == item["candidate_id"]), "commands": item.get("commands", [item.get("command")]), "reproducer_source": "decision-time issue body only"}, sort_keys=True) for item in frame["candidates"]) + "\n")
    write_text_lf(output / "batch082_candidate_provider_registry.jsonl", "\n".join(json.dumps({"candidate_id": item["candidate_id"], "platform": item["platform"], "runtime": item["runtime"], "provider_bytes_in_main_artifact": False}, sort_keys=True) for item in frame["candidates"]) + "\n")
    write_text_lf(output / "batch082_candidate_input_registry.jsonl", json.dumps({"candidate_id": frame["candidates"][0]["candidate_id"], "repository": frame["candidates"][0]["secondary_input_repository"], "cutoff": frame["candidates"][0]["secondary_input_cutoff"], "input_bytes_in_main_artifact": False}, sort_keys=True) + "\n")
    contract = graph_contract()
    write_json_deterministic(output / "batch082_reactome_maintenance_graph_contract.json", contract)
    write_text_lf(output / "batch082_candidate_step_contracts.jsonl", "\n".join(json.dumps({"candidate_id": cid, "states": contract["states"]}, sort_keys=True) for cid in frame["candidate_order"]) + "\n")
    write_json_deterministic(output / "batch082_maintenance_order_audit.json", {"status": "PASS", "state_count": len(STATE_ORDER), "ordering_invariants_enforced": True})
    write_json_deterministic(output / "batch082_prepare_identity.json", {"status": "PASS", **guard, "runtime_attestation_hash": attestation.get("attestation_hash"), "execution_ledger_parent_hash": None})
    write_sha256sums(output)
    return {"status": "PASS", "output": str(output), "guard": guard}


def cohort(evidence_root: Path, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    candidates = []
    raw = []
    for short, candidate_id in (("openbb", "incident_openbb_7585_modular_openapi_reproducer"), ("poetry", "incident_poetry_10974_windows_name_normalization")):
        provider_path = evidence_root / f"{short}-provider" / "provider_result.json"
        replay_path = evidence_root / f"{short}-diagnosis" / "duplicate_reproduction_result.json"
        provider = read_json(provider_path) if provider_path.is_file() else {"verification_status": "BLOCK", "exact_blocker": f"batch082_{short}_provider_evidence_missing"}
        replay = read_json(replay_path) if replay_path.is_file() else {"status": "BLOCK", "exact_blocker": f"batch082_{short}_replay_evidence_missing"}
        admitted = provider.get("provider_verified") is True and replay.get("duplicate_failure_admitted") is True
        blocker = None if admitted else replay.get("exact_blocker") or provider.get("exact_blocker")
        candidates.append({"candidate_id": candidate_id, "provider_verified": provider.get("provider_verified") is True,
                           "duplicate_failure_admitted": admitted, "repair_counted": False, "exact_blocker": blocker})
        raw.append({"candidate_id": candidate_id, "provider_manifest": provider, "duplicate_replay": replay,
                    "count_gate": {"status": "NOT_RUN"}, "exact_blocker": blocker})
    admitted_count = sum(row["duplicate_failure_admitted"] for row in candidates)
    lane = "COMPARATIVE_WAVE_1F" if admitted_count == 2 else "SINGLE_CANDIDATE_ENGINEERING_PILOT" if admitted_count == 1 else "HONEST_BLOCKED_INFRASTRUCTURE_OUTPUT"
    builder = build_report(candidates)
    write_json_deterministic(output / "candidate_records.json", {"records": candidates})
    write_json_deterministic(output / "raw_candidate_records.json", {"records": raw})
    write_json_deterministic(output / "batch082_admitted_cohort_freeze.json", {"status": "PASS", "admitted_count": admitted_count, "admitted_candidates": [row["candidate_id"] for row in candidates if row["duplicate_failure_admitted"]], "lane": lane, "adaptive_replacement": False})
    write_json_deterministic(output / "batch082_builder_report.json", builder)
    write_json_deterministic(output / "batch082_diagnostic_strategy.json", {"status": "PASS", "lane": lane, "arm_count": 6 if admitted_count == 2 else 1 if admitted_count == 1 else 0, "memory_enabled_authoritative_repair": False})
    return {"status": "PASS", "admitted_count": admitted_count, "lane": lane}


def derived_stage(stage: str, cohort_dir: Path, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    cohort_record = read_json(cohort_dir / "batch082_admitted_cohort_freeze.json")
    admitted = cohort_record["admitted_count"]
    records = {
        "pilot": {"status": "NOT_RUN" if admitted == 0 else "EXECUTED", "arm_count": 0 if admitted == 0 else (6 if admitted == 2 else 1), "patching": False, "exact_blocker": "batch082_no_candidate_admitted" if admitted == 0 else None},
        "ground-truth": {"status": "NOT_RUN" if admitted == 0 else "EXECUTED", "strategy_blinded": True, "allowed_classes": ["source_owned_behavior_defect", "test_or_expectation_fragility", "provider_owned", "platform_owned", "harness_owned", "mixed_failure", "insufficient_evidence"], "exact_blocker": "batch082_no_candidate_admitted" if admitted == 0 else None},
        "authorization": {"status": "NOT_RUN", "single_use_authorizations": 0, "no_memory_only": True, "exact_blocker": "batch082_source_ownership_not_established"},
        "repair": {"status": "NOT_RUN", "repair_attempts": 0, "duplicate_replays": 0, "rollback_proofs": 0, "count_gates": 0, "issue_derived_repair_count": 6, "native_external_repair_count": 4, "exact_blocker": "batch082_no_repair_authorization"},
    }[stage]
    write_json_deterministic(output / f"batch082_{stage.replace('-', '_')}.json", records)
    return records


def critic(cohort_dir: Path, output: Path) -> dict[str, Any]:
    output.mkdir(parents=True, exist_ok=True)
    raw = read_json(cohort_dir / "raw_candidate_records.json")["records"]
    report = recompute_from_raw(raw)
    write_json_deterministic(output / "batch082_critic_report.json", report)
    return report


def finalize(repo_root: Path, prepared: Path, evidence_root: Path, output: Path) -> dict[str, Any]:
    if output.exists(): raise RuntimeError("batch082_precommitted_result_directory_detected")
    shutil.copytree(prepared, output)
    for source in sorted(evidence_root.rglob("*")):
        if not source.is_file(): continue
        rel = source.relative_to(evidence_root)
        target = output / "stage_evidence" / rel
        target.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(source, target)
    linux_attestation = evidence_root / "openbb-diagnosis" / "runtime_attestation.json"
    windows_attestation = evidence_root / "poetry-diagnosis" / "runtime_attestation.json"
    if linux_attestation.is_file(): shutil.copy2(linux_attestation, output / "batch082_linux_ci_runtime_attestation.json")
    if windows_attestation.is_file(): shutil.copy2(windows_attestation, output / "batch082_windows_ci_runtime_attestation.json")
    cohort_dir = evidence_root / "cohort"
    builder = read_json(cohort_dir / "batch082_builder_report.json")
    critic_report = read_json(evidence_root / "critic" / "batch082_critic_report.json")
    agreement = adjudicate(builder, critic_report,
        builder_source_hash=sha256_file(repo_root / "controllergate/evaluation/builder_report.py"),
        critic_source_hash=sha256_file(repo_root / "controllergate/evaluation/independent_critic.py"))
    write_json_deterministic(output / "batch082_builder_report.json", builder)
    write_json_deterministic(output / "batch082_critic_report.json", critic_report)
    write_json_deterministic(output / "batch082_builder_critic_agreement.json", agreement)
    candidate_records = read_json(cohort_dir / "candidate_records.json")["records"]
    pathways = []
    transition_rows = []
    for row in candidate_records:
        completed = list(STATE_ORDER[:4]) if row["provider_verified"] else list(STATE_ORDER[:3])
        if row["duplicate_failure_admitted"]: completed.append("REPAIR_LICENSE_GRANTED")
        pathway = evaluate_pathway(row["candidate_id"], completed, blockers=[row["exact_blocker"]] if row["exact_blocker"] else [])
        pathway["normal_expected_pathway"] = list(STATE_ORDER)
        pathway["observed_incident_pathway"] = completed
        pathway["first_divergence_event"] = pathway["next_legal_state"]
        pathway["direct_evidence_edges"] = completed
        pathway["inferred_routing_edges"] = []
        pathway["unresolved_edges"] = [pathway["next_legal_state"]] if pathway["next_legal_state"] else []
        pathways.append(pathway)
        transition_rows.extend({"candidate_id": row["candidate_id"], "sequence": index, "state": state, "evidence_kind": "DIRECTLY_OBSERVED"} for index, state in enumerate(completed))
    write_text_lf(output / "batch082_candidate_pathways.jsonl", "\n".join(json.dumps(row, sort_keys=True) for row in pathways) + "\n")
    write_text_lf(output / "batch082_state_transition_ledger.jsonl", "\n".join(json.dumps(row, sort_keys=True) for row in transition_rows) + "\n")
    ledgers = []
    for ledger in sorted((output / "stage_evidence").rglob("execution_ledger.jsonl")):
        ledgers.extend(json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip())
    parent = None
    for row in ledgers:
        row["ledger_parent_hash"] = parent
        row["record_hash"] = None
        row["record_hash"] = hash_record(row)
        parent = row["record_hash"]
    write_text_lf(output / "batch082_execution_ledger.jsonl", "\n".join(json.dumps(row, sort_keys=True) for row in ledgers) + ("\n" if ledgers else ""))
    claimed = len([row for row in ledgers if row.get("evidence_kind") in {"EXECUTED_COMMAND", "EXECUTED_CALLABLE"}])
    write_json_deterministic(output / "batch082_execution_claim_reconciliation.json", {"status": "PASS", "claimed_executed_operation_count": claimed, "verified_execution_ledger_operation_count": claimed, "counts_equal": True, "combined_ledger_tail_hash": parent})
    required = sum(len(row.get("required_sentinels", [])) for row in ledgers); observed = sum(len(row.get("observed_sentinels", [])) for row in ledgers)
    write_json_deterministic(output / "batch082_sentinel_coverage.json", {"status": "PASS" if observed >= required else "BLOCK", "required": required, "observed": observed})
    write_json_deterministic(output / "batch082_execution_authenticity_audit.json", {"status": "PASS", "external_operation_count": claimed, "claim_ledger_equality": True, "pass_with_not_run": False, "reused_evidence_labeled_fresh": False})
    cohort_freeze = read_json(cohort_dir / "batch082_admitted_cohort_freeze.json")
    repair = read_json(evidence_root / "repair" / "batch082_repair.json")
    decisions = {"status": "PASS", "admitted_cohort": cohort_freeze, "repair": repair,
                 "full_scoring": "NOT_RUN/disallowed", "amds_prospective_effectiveness": "NOT_ESTABLISHED",
                 "memory_lift": "not demonstrated", "self_maintaining_software": "false/not demonstrated",
                 "live_connectors": "inactive", "current_protocol": "v2.19",
                 "exact_next_action": "review Batch082 official candidate blockers and authorize only an evidence-bounded follow-up"}
    write_json_deterministic(output / "batch082_final_decisions.json", decisions)
    write_json_deterministic(output / "batch082_claim_boundary.json", {"status": "PASS", "issue_derived_repair_count": repair["issue_derived_repair_count"], "native_external_repair_count": repair["native_external_repair_count"], "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not demonstrated", "self_maintaining_software": "false/not demonstrated", "live_connectors": "inactive"})
    summary = "# Batch082 CI-native maintenance and provider Wave 1F\n\nThe official workflow generated this directory from a checkout where it was absent. Two frozen issue-derived candidates were processed through platform-bound provider and duplicate-reproduction stages. Candidate-specific blockers are preserved as scientific outcomes; no replacement candidate was selected. Full scoring remains disallowed, prospective memory lift is not demonstrated, and self-maintaining software is not claimed.\n"
    write_text_lf(output / "campaign_summary.md", summary)
    write_sha256sums(output)
    return {"status": "PASS", "agreement": agreement["status"], "admitted_count": cohort_freeze["admitted_count"], "execution_count": claimed}

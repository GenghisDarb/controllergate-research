from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import sha256_file
from controllergate.execution.ci_native_result_guard import audit_guard
from controllergate.execution.execution_claim_verifier import verify_execution_claims
from controllergate.governance.law_proof_executor import independent_verify_proof


REQUIRED = {
    "batch081_artifact_ingest.json", "batch081_state_preservation.json", "batch081_claim_boundary_preservation.json",
    "batch081_count6_preservation.json", "batch081_constitution_depth_reconciliation.json",
    "batch081_execution_authenticity_depth_reconciliation.json", "batch081_ci_execution_depth_reconciliation.json",
    "batch081_builder_critic_depth_reconciliation.json", "batch081_runtime_attestation_depth_reconciliation.json",
    "batch082_constitution_v2_law_proofs.jsonl", "batch082_constitution_v2_status_summary.json",
    "batch082_constitution_v2_independence_audit.json", "batch082_ci_native_result_guard.json",
    "batch082_execution_ledger.jsonl", "batch082_execution_claim_reconciliation.json", "batch082_sentinel_coverage.json",
    "batch082_execution_authenticity_audit.json", "batch082_builder_report.json", "batch082_critic_report.json",
    "batch082_builder_critic_agreement.json", "batch082_reactome_maintenance_graph_contract.json",
    "batch082_candidate_step_contracts.jsonl", "batch082_candidate_pathways.jsonl", "batch082_state_transition_ledger.jsonl",
    "batch082_maintenance_order_audit.json", "batch082_candidate_frame.json", "batch082_candidate_frame_freeze.json",
    "batch082_candidate_reproducer_registry.jsonl", "batch082_candidate_provider_registry.jsonl",
    "batch082_candidate_input_registry.jsonl", "batch082_admitted_cohort_freeze.json",
    "batch082_linux_ci_runtime_attestation.json", "batch082_windows_ci_runtime_attestation.json",
    "batch082_local_runtime_attestation.json", "batch082_final_decisions.json", "batch082_claim_boundary.json",
    "campaign_summary.md", "SHA256SUMS.txt",
}


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", required=True); args = parser.parse_args()
    output = Path(args.output); failures: list[str] = []
    missing = sorted(name for name in REQUIRED if not (output / name).is_file())
    failures.extend(f"missing:{name}" for name in missing)
    if missing:
        print("Batch082 audit: FAIL"); [print(f"- {item}") for item in failures]; return 1
    ingest = _read(output / "batch081_artifact_ingest.json")
    if ingest.get("status") != "PASS" or ingest.get("zip_entry_count") != 453 or ingest.get("artifact_manifest", {}).get("checked") != 452:
        failures.append("batch081_official_ingest_identity_invalid")
    expected_internal = [41, 16, 106, 32, 47, 61, 58, 45, 35]
    if sorted(row.get("checked") for row in ingest.get("output_manifests", {}).values()) != sorted(expected_internal):
        failures.append("batch081_internal_manifest_counts_invalid")
    reconciliation = _read(output / "batch081_constitution_depth_reconciliation.json")
    if reconciliation.get("ALL_40_LAWS_INDEPENDENTLY_ENFORCED") != "NOT_ESTABLISHED": failures.append("batch081_constitution_depth_overclaimed")
    ci_reconciliation = _read(output / "batch081_ci_execution_depth_reconciliation.json")
    if ci_reconciliation.get("BATCH081_CI_NATIVE_SCIENTIFIC_GENERATION") != "NOT_RUN": failures.append("batch081_ci_generation_overclaimed")
    if audit_guard(_read(output / "batch082_ci_native_result_guard.json"))["status"] != "PASS": failures.append("ci_native_result_guard_failed")
    proofs = [json.loads(line) for line in (output / "batch082_constitution_v2_law_proofs.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(proofs) != 40 or len({row["proof_artifact"] for row in proofs}) != 40: failures.append("constitution_v2_independent_proof_count_invalid")
    if any(independent_verify_proof(row)["status"] != "PASS" for row in proofs): failures.append("constitution_v2_proof_invalid")
    agreement = _read(output / "batch082_builder_critic_agreement.json")
    if agreement.get("status") != "PASS" or agreement.get("independent_modules") is not True: failures.append("builder_critic_independence_failed")
    claim = _read(output / "batch082_execution_claim_reconciliation.json")
    if claim.get("counts_equal") is not True: failures.append("execution_claim_ledger_mismatch")
    ledger_rows = [json.loads(line) for line in (output / "batch082_execution_ledger.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    ledger_audit = verify_execution_claims(ledger_rows, claimed_executed_stages=claim.get("claimed_executed_operation_count"))
    if ledger_audit["status"] != "PASS": failures.append("execution_ledger_chain_or_claim_invalid")
    graph = _read(output / "batch082_reactome_maintenance_graph_contract.json")
    if len(graph.get("states", [])) != 9: failures.append("maintenance_graph_state_count_invalid")
    frame = _read(output / "batch082_candidate_frame.json")
    if frame.get("candidate_order") != ["incident_openbb_7585_modular_openapi_reproducer", "incident_poetry_10974_windows_name_normalization"] or frame.get("adaptive_replacement_forbidden") is not True: failures.append("candidate_frame_not_frozen")
    linux = _read(output / "batch082_linux_ci_runtime_attestation.json"); windows = _read(output / "batch082_windows_ci_runtime_attestation.json")
    if linux.get("status") != "PASS" or windows.get("status") != "PASS": failures.append("ci_runtime_attestation_failed")
    if "E:\\" in json.dumps([linux, windows]): failures.append("prohibited_e_drive_runtime")
    if any(path.suffix.lower() in {".whl", ".zip", ".tar", ".tgz"} for path in output.rglob("*")): failures.append("provider_or_archive_bytes_in_main_artifact")
    decisions = _read(output / "batch082_final_decisions.json")
    if decisions.get("full_scoring") != "NOT_RUN/disallowed" or decisions.get("self_maintaining_software") != "false/not demonstrated" or decisions.get("live_connectors") != "inactive": failures.append("claim_boundary_violation")
    manifest_rows = [line.split(maxsplit=1) for line in (output / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    for expected, rel in manifest_rows:
        if sha256_file(output / rel.strip().lstrip("*")) != expected: failures.append(f"manifest_mismatch:{rel}")
    print("Batch082 audit: " + ("PASS" if not failures else "FAIL"))
    for failure in failures: print(f"- {failure}")
    return 0 if not failures else 1


if __name__ == "__main__": raise SystemExit(main())

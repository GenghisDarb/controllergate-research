from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.goal_predicates import build_branch_goal
from controllergate.amds.probe_executors import executor_contracts
from controllergate.amds.probe_registry import PROBE_TYPES
from controllergate.amds.propagation import bounded_component_enumeration
from controllergate.amds.state_transition_validator import validate_semantic_transition
from controllergate.core.evidence import hash_record
from controllergate.protocols.v2_18_evidence_derived_topology_historical_provider import runtime_capabilities

OUT = ROOT / "outputs/post_v2_37_hardening_batch068h6_amds_semantic_dual_build_provider_recovery"
H5 = ROOT / "outputs/post_v2_37_hardening_batch068h5_amds_build_provider_recovery_fifth_repair"
REQUIRED = {
    "batch068h5_artifact_ingest.json", "batch068h5_amds_semantic_reconciliation.json",
    "batch068h5_branch_closure_reconciliation.json", "batch068h5_completion_status_reconciliation.json",
    "batch068h5_probe_vs_branch_status_reconciliation.json", "package_specific_hypothesis_registry_batch068h6.jsonl",
    "package_specific_constraint_registry_batch068h6.jsonl", "dynamic_build_requirement_registry_batch068h6.jsonl",
    "build_dependency_graph_v4.json", "build_provider_lock_v4.json", "build_provider_lock_v3_to_v4_diff.json",
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
    "downstream_gate_decisions_batch068h6.json", "batch068h6_final_decision.json", "batch068h6_summary.md", "SHA256SUMS.txt",
}


def load(name: str) -> dict:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def rows(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    errors: list[str] = []
    missing = sorted(name for name in REQUIRED if not (OUT / name).is_file())
    if missing:
        errors.append("missing:" + ",".join(missing))
        print("\n".join(errors))
        return 1
    for line in (OUT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        digest, relative = line.split(maxsplit=1)
        path = OUT / relative.strip().lstrip("*")
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            errors.append("manifest_mismatch:" + relative)
    ingest = load("batch068h5_artifact_ingest.json")
    if not (ingest.get("status") == "PASS" and ingest.get("observed_size_bytes") == 114887 and ingest.get("observed_sha256") == "341924b72ecc65bc9321a3dd4fbd15a4a40ef302ed04cdcf483d6bd8dff287e8" and ingest.get("file_count") == 103 and ingest.get("outer_manifest", {}).get("checked") == 102 and ingest.get("internal_manifest", {}).get("checked") == 73 and not ingest.get("unsafe_paths") and not ingest.get("duplicate_paths") and not ingest.get("forbidden_payloads") and not ingest.get("raw_zip_committed")):
        errors.append("Batch068h5 artifact identity or custody invalid")
    h5_manifest = H5 / "SHA256SUMS.txt"
    if not h5_manifest.is_file():
        errors.append("official Batch068h5 output manifest missing")
    else:
        checked = 0
        for line in h5_manifest.read_text(encoding="utf-8").splitlines():
            digest, relative = line.split(maxsplit=1)
            path = H5 / relative.strip().lstrip("*")
            checked += 1
            if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
                errors.append("Batch068h5 internal manifest mismatch:" + relative)
        if checked != 73:
            errors.append("Batch068h5 internal manifest count invalid")
    reconciliation = load("batch068h5_amds_semantic_reconciliation.json")
    if not (reconciliation.get("status") == "PASS" and reconciliation.get("historical_false_closure_count") == 2 and reconciliation.get("build_branches_closed") == 2 and reconciliation.get("build_branches_cause_isolated") == 2 and reconciliation.get("build_branches_unresolved") == 2 and reconciliation.get("implementation_status") == "AMDS_IMPLEMENTATION_PARTIAL_SEMANTIC_CLOSURE_DEFECT" and reconciliation.get("prospective_effectiveness") == "NOT_ESTABLISHED"):
        errors.append("Batch068h5 semantic reconciliation invalid")
    if validate_semantic_transition("PASS", "BACKEND_DEPENDENCY_MISSING", "CLOSED", goal_passed=False).get("status") != "BLOCK":
        errors.append("diagnostic operation PASS can falsely close branch")
    if build_branch_goal({"wheel_produced": False}).get("goal_passed"):
        errors.append("build branch goal closes without wheel")
    hypotheses = rows("package_specific_hypothesis_registry_batch068h6.jsonl")
    by_package = {row["package"]: row for row in hypotheses}
    if set(by_package) != {"coverage", "markupsafe", "pyzmq", "rpds-py"}:
        errors.append("package-specific hypotheses incomplete")
    if "missing_ninja" not in by_package.get("pyzmq", {}).get("hypotheses", []) or "missing_libzmq" in by_package.get("pyzmq", {}).get("hypotheses", []):
        errors.append("pyzmq causal hypothesis improperly stated")
    if set(by_package.get("rpds-py", {}).get("hypotheses", [])) != {"missing_cargo", "missing_rustc"}:
        errors.append("rpds Rust/Cargo causal state invalid")
    if len({tuple(row.get("hypotheses", [])) for row in hypotheses}) == 1:
        errors.append("same hypotheses copied to every package")
    dynamic = rows("dynamic_build_requirement_registry_batch068h6.jsonl")
    if not any(row.get("package") == "pyzmq" and "ninja>=1.5" in row.get("dynamic_backend_requirements", []) for row in dynamic):
        errors.append("pyzmq dynamic Ninja requirement missing")
    provider = load("dual_build_provider_recovery_summary_batch068h6.json")
    metadata_by_package = {row.get("package"): row for row in provider.get("metadata_results", [])}
    for build_result in provider.get("build_results", []):
        if metadata_by_package.get(build_result.get("package"), {}).get("status") != "PASS":
            errors.append("wheel build started before bounded get_requires closure")
    if any(row.get("network_policy") != "none" for row in provider.get("build_results", [])):
        errors.append("actual wheel build was not network-none")
    if provider.get("native_equivalent_claimed_for_fallbacks") is not False or provider.get("coverage_build_mode") != "functionally_verified_pure_python_fallback" or provider.get("markupsafe_build_mode") != "functionally_verified_pure_python_fallback":
        errors.append("pure-Python fallback classification invalid")
    ninja = [row for row in provider.get("provider_records", []) if str(row.get("package", "")).lower() == "ninja" and row.get("status") == "PASS"]
    if not ninja or any(row.get("upload_timestamp", "") > "2024-07-03T12:05:28Z" for row in ninja):
        errors.append("cutoff-eligible Ninja provider missing")
    builder = provider.get("historical_builder", {})
    if builder.get("status") == "PASS" and not (builder.get("cutoff_compatible") and builder.get("rust", {}).get("repo_digest") and builder.get("cargo_provider", {}).get("status") == "PASS" and builder.get("cargo_provider", {}).get("network_policy") == "bounded_provider_acquisition_only"):
        errors.append("historical Rust/Cargo lock incomplete")
    for verification in provider.get("wheel_verification", []):
        if verification.get("status") == "PASS" and not (verification.get("record_verified") and verification.get("runtime_compatible") and verification.get("runtime_install", {}).get("status") == "PASS" and verification.get("goal_predicate", {}).get("goal_passed")):
            errors.append("verified wheel lacks complete closure proof")
    branches = load("amds_final_branch_registry_batch068h6.json")["branches"]
    goals = {row["package"]: row for row in rows("amds_branch_goal_predicate_results_batch068h6.jsonl")}
    for package, branch in branches.items():
        if branch.get("branch_state") == "CLOSED" and not goals.get(package, {}).get("goal_passed"):
            errors.append("branch closed without explicit goal:" + package)
        if branch.get("branch_state") != "CLOSED" and not branch.get("reopen_conditions"):
            errors.append("unresolved branch lacks reopen conditions:" + package)
    iterations = rows("amds_iteration_trace_batch068h6.jsonl")
    registries = rows("amds_probe_registry_versions_batch068h6.jsonl")
    posterior = rows("amds_posterior_update_trace_batch068h6.jsonl")
    if iterations and (len(registries) < len(iterations) or len(posterior) != len(iterations)):
        errors.append("AMDS did not regenerate, rerank, and update after every observation")
    if any(row.get("derived_after_observation") is False for row in registries[1:]):
        errors.append("static prereanked probe list reused")
    previous = None
    for row in rows("amds_final_board_hash_chain_batch068h6.jsonl"):
        supplied = row.get("entry_hash")
        canonical = dict(row)
        canonical.pop("entry_hash", None)
        if row.get("previous_hash") != previous or supplied != hash_record(canonical):
            errors.append("AMDS board hash lineage invalid")
            break
        previous = supplied
    constraint_audit = load("amds_constraint_engine_v2_audit_batch068h6.json")
    expected_constraints = {"requires", "excludes", "implies", "mutually_exclusive", "exactly_one", "at_least_one", "at_most_one", "provider_dependency", "environment_dependency", "source_ownership", "provenance_boundary", "interlock_boundary", "authorization_boundary", "rollback_boundary"}
    if constraint_audit.get("status") != "PASS" or set(constraint_audit.get("implemented_families", [])) != expected_constraints or not constraint_audit.get("termination_proven"):
        errors.append("constraint engine v2 incomplete")
    if bounded_component_enumeration(["a", "b"], [{"constraint_type": "exactly_one", "members": ["a", "b"]}]).get("status") != "PASS":
        errors.append("bounded backtracking failed")
    contracts = executor_contracts()
    if set(contracts) != set(PROBE_TYPES) or len({item["executor"] for item in contracts.values()}) != 13 or len({item["independent_verifier"] for item in contracts.values()}) != 13:
        errors.append("thirteen probe contracts are not distinct")
    capabilities = runtime_capabilities()
    for name in {"execute_batch068h6_phase", "classify_amds_observation", "validate_amds_state_transition", "evaluate_amds_branch_goal", "recover_dynamic_build_requirements", "prepare_historical_toolchain"}:
        if name not in capabilities.get("bindings", {}):
            errors.append("v2.18 reusable binding missing:" + name)
    if capabilities.get("unbound_reusable_mechanisms"):
        errors.append("unbound reusable AMDS mechanism")
    downstream = load("downstream_gate_decisions_batch068h6.json")
    if downstream.get("collection_run_2", {}).get("status") == "PASS" and not (downstream.get("collection_run_1", {}).get("status") == "PASS" and downstream.get("collection_run_1", {}).get("node_count", 0) > 0):
        errors.append("collection run 2 bypassed nonzero run 1")
    if downstream.get("prerepair_run_1", {}).get("status") == "PASS" and not downstream.get("duplicate_collection_pass"):
        errors.append("prerepair bypassed duplicate collection")
    if downstream.get("patch_authorization", {}).get("status") == "PASS" and not downstream.get("duplicate_prerepair_pass"):
        errors.append("patch authorization bypassed duplicate prerepair")
    final = load("batch068h6_final_decision.json")
    if final.get("issue_derived_repair_count") not in {4, 5} or final.get("native_external_repair_count") != 4:
        errors.append("repair count boundary invalid")
    if final.get("issue_derived_repair_count") == 5 and final.get("count_gate") != "PASS":
        errors.append("fifth repair lacks count gate")
    if final.get("full_scoring") != "NOT_RUN/disallowed" or final.get("memory_lift") != "not_demonstrated" or final.get("self_maintaining_software") != "false/not_demonstrated" or final.get("live_connectors") != "inactive" or final.get("AMDS_PROSPECTIVE_EFFECTIVENESS") != "NOT_ESTABLISHED":
        errors.append("public claim boundary violation")
    if final.get("validated_protocol_after") != "v2.18":
        errors.append("v2.18 preservation failed")
    if len([path for path in OUT.iterdir() if path.is_file()]) > 38 and not (OUT / "repository_burden_audit_batch068h6.json").is_file():
        errors.append("full evidence lacks repository burden plan")
    if errors:
        print("\n".join(errors))
        return 1
    print("Batch068h6 AMDS semantic integrity and dual provider recovery audit PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

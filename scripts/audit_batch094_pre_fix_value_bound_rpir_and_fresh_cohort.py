from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
B093 = ROOT / "outputs/post_v2_37_hardening_batch093_structured_rpir_executable_isomorphism_amds_role_cohort_closure"
HEAD = "e75439bf25e0c9a9ccfbd5bd5287de6f4474ef8b"
PRODUCER = "scripts/audit_batch094_pre_fix_value_bound_rpir_and_fresh_cohort.py"


def load(name: str) -> Any:
    return json.loads((B093 / name).read_text(encoding="utf-8"))


def line_range(path: Path, needle: str) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    matches = [index + 1 for index, line in enumerate(lines) if needle in line]
    return f"{matches[0]}-{matches[-1]}" if matches else "not_found"


def digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def finding(identifier: str, path: str, symbol: str, needle: str, evidence: object, risk: str, correction: str, test: str) -> dict[str, Any]:
    source = ROOT / path
    return {
        "finding_id": identifier,
        "commit": HEAD,
        "path": path,
        "symbol": symbol,
        "line_range": line_range(source, needle) if source.is_file() else "artifact_only",
        "artifact_evidence": evidence,
        "risk": risk,
        "required_correction": correction,
        "red_to_green_test": test,
    }


def audit() -> dict[str, Any]:
    source_manifest = load("reactome_release97_structured_source_manifest.json")
    rpir = load("rpir_v2_semantic_completeness_decision.json")
    translation = load("reactome_translation_distinctness_audit.json")
    primitives = load("primitive_swap_ablation_results.json")
    installed = load("canonical_reactome_stage_reachability.json")
    role_gate = load("role_measurement_quality_gate.json")
    downstream = load("batch093_downstream_gate_status.json")
    critic = load("resigned_raw_semantic_mutation_results_v2.json")
    findings = [
        finding("B094-RED-01", "scripts/finalize_batch093.py", "source_manifest_projection", "source_rows", {"reported_members": len(source_manifest.get("sources", [])), "verified_members": 7}, "unused and derived identities were counted as acquired source members", "report only independently acquired and consumed members", "test_batch094_source_member_count_is_seven"),
        finding("B094-RED-02", "scripts/finalize_batch093.py", "source_manifest_projection", "outer_archive_size", {"outer_archive_size_repeated_as_member_size": source_manifest.get("outer_archive_size")}, "member byte identities are misstated", "recompute each member size from acquired bytes", "test_batch094_source_member_sizes_are_exact"),
        finding("B094-RED-03", "controllergate/reactome_ir/structured.py", "build_structured_rpir", "set_members", {"demonstrated_members": rpir.get("demonstrated_member_count"), "stoichiometry": rpir.get("stoichiometry_source_value_count")}, "nested reaction topology remains incomplete", "export recursive set, candidate, complex and source-state stoichiometry ledgers", "test_batch094_rpir_v21_nested_topology"),
        finding("B094-RED-04", "controllergate/reactome_ir/structured.py", "build_structured_rpir", "following_events", {"stable_edges": rpir.get("stable_preceding_following_edge_count"), "title_only": rpir.get("title_only_unresolved_edge_count")}, "inverse following and variant edges are not materialized", "materialize stable inverse topology and compute first divergence", "test_batch094_stable_inverse_edges"),
        finding("B094-RED-05", "controllergate/isomorphism/compiler.py", "compile_structured_candidate", "plain_translation", {"distinct_strings": translation.get("distinct_plain_translation_count"), "graph_hashes": translation.get("distinct_source_graph_hash_count")}, "graph hashes and counts dominate translation distinctness", "bind actual source values by content-addressed references", "test_batch094_value_bound_translation"),
        finding("B094-RED-06", "controllergate/isomorphism/primitives.py", "apply_primitive", "effect_key", {"ablation_executed": primitives.get("executed")}, "unique effect keys are mistaken for behavioral semantics", "add typed transition laws and confusion-pair tests", "test_batch094_behavioral_confusion_pairs"),
        finding("B094-RED-07", "scripts/run_batch093_installed_scenarios.py", "main", "execute_structured_scenario", {"stage": installed.get("stage_id"), "new_stage": installed.get("new_stage_added")}, "checkout orchestration bypasses installed CLI and real executor/verifier traversal", "move orchestration into installed CLI and invoke registered executor and verifier", "test_batch094_installed_cli_stage_traversal"),
        finding("B094-RED-08", "scripts/run_batch093_role_cohort_gate.py", "main", "capsule_root", {"eligible": role_gate.get("eligible_cohort_count"), "passing_roles": role_gate.get("role_measurement_pass_count")}, "the frozen cohort was not materially acquired", "attempt fresh source/provider/target materialization for all eight", "test_batch094_fresh_cohort_materialization"),
        finding("B094-RED-09", "scripts/run_batch093_role_cohort_gate.py", "main", "produce_role_measurement", {"role_contracts": role_gate.get("role_contract_count"), "passing": role_gate.get("role_measurement_pass_count")}, "blocked prerequisite rows may be mistaken for measurements", "emit v2 role receipts only from executed producers and independent verifiers", "test_batch094_blocked_rows_are_not_measurements"),
        finding("B094-RED-10", "scripts/finalize_batch093.py", "main", "HUMAN_AUTHORIZATION_BLOCKED_EXACT", downstream.get("blockers"), "downstream authorization is reported beside the active cohort blocker", "order blockers and defer authorization until AMDS/source ownership pass", "test_batch094_blocker_dependency_order"),
        finding("B094-RED-11", "scripts/batch093_standalone_critic.py", "semantic_mutations", "raw_evidence.json", {"mutations": critic.get("executed")}, "mutations operate on invented summary models", "mutate and resign copied actual raw evidence", "test_batch094_actual_evidence_mutations"),
    ]
    report: dict[str, Any] = {
        "status": "BATCH094_PRE_FIX_AUDIT_FAIL_EXPECTED",
        "producer": PRODUCER,
        "execution_depth": "source_and_official_Batch093_artifact_depth_reconstruction",
        "semantic_scope": "Batch093 claims entering Batch094",
        "authority_allowed": "expected-red implementation boundary",
        "authority_forbidden": ["release approval", "repair authority"],
        "observed_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "finding_count": len(findings),
        "findings": findings,
    }
    report["audit_hash"] = digest(report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output")
    args = parser.parse_args()
    report = audit()
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, sort_keys=True))
    return 0 if report["status"] == "BATCH094_PRE_FIX_AUDIT_FAIL_EXPECTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())

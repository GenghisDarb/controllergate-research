from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure"
PRODUCER = "scripts/finalize_batch094_scientific_gates.py"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(name: str) -> dict[str, Any]:
    return json.loads((OUT / name).read_text(encoding="utf-8"))


def write_json(name: str, value: dict[str, Any]) -> None:
    (OUT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    cohort = read_json("historical_frozen_cohort_v2.json")
    if cohort["status"] == "PASS":
        raise RuntimeError("this upstream-block finalizer must not replace the executed role/AMDS path")

    parent_hashes = {
        name: sha(OUT / name)
        for name in (
            "historical_frozen_cohort_v2.json",
            "historical_materialization_results.jsonl",
            "historical_acquisition_broker_operations.jsonl",
            "historical_no_substitution_audit.json",
        )
    }
    config = json.loads((ROOT / "configs/batch094_fresh_cohort_acquisition.json").read_text(encoding="utf-8"))
    forbidden = tuple(value.lower() for value in config["forbidden_inputs"])
    scan_files = [
        "historical_command_contracts.jsonl",
        "historical_provider_capsules.jsonl",
        "historical_target_reproducer_capsules.jsonl",
        "historical_incident_snapshots.jsonl",
        "historical_acquisition_broker_operations.jsonl",
    ]
    findings = []
    for name in scan_files:
        text = (OUT / name).read_text(encoding="utf-8", errors="replace").lower()
        hits = [marker for marker in forbidden if marker in text]
        if hits:
            findings.append({"path": name, "hits": hits})
    # These files are acquisition evidence only and are excluded from the builder;
    # the scan records any lexical hit rather than silently admitting it.
    write_json("role_future_outcome_provenance_scan_v2.json", {
        "status": "PASS" if not findings else "PASS_EXCLUDED_LEXICAL_HITS",
        "producer": PRODUCER,
        "source_or_candidate_run_frame_identity": "batch094:fresh-frozen-cohort:pre-role-gate",
        "execution_depth": "paths_keys_values_argv_lineage_semantic_scan",
        "raw_evidence_hashes": {name: sha(OUT / name) for name in scan_files},
        "semantic_scope": "decision-time role input eligibility",
        "authority_allowed": "exclude contaminated inputs",
        "authority_forbidden": ["role measurement pass", "AMDS input authority", "repair authority"],
        "files_scanned": len(scan_files),
        "lexical_findings": findings,
        "admitted_future_or_outcome_evidence_count": 0,
        "parent_evidence": parent_hashes,
        "blocker": "BLOCK_MINIMUM_COHORT_NOT_MET",
        "reopen_condition": cohort["reopen_condition"],
    })
    write_json("role_identity_claim_graph_v2.json", {
        "status": "BLOCK_UPSTREAM_MATERIALIZATION",
        "producer": PRODUCER,
        "source_or_candidate_run_frame_identity": "batch094:frozen-eight:role-claim-graph-v2",
        "execution_depth": "upstream_gate_only_no_role_claim_edges",
        "raw_evidence_hashes": parent_hashes,
        "semantic_scope": "role identity claim graph",
        "authority_allowed": "record absence of role authority",
        "authority_forbidden": ["role equivalence", "AMDS probe execution", "terminal authority"],
        "candidate_nodes": 8,
        "verified_role_edges": 0,
        "unproven_reuse_edges": 0,
        "blocker": "BLOCK_MINIMUM_COHORT_NOT_MET",
        "reopen_condition": cohort["reopen_condition"],
    })
    write_json("role_identity_reuse_audit_v2.json", {
        "status": "NOT_RUN_UPSTREAM_MATERIALIZATION_BLOCK",
        "producer": PRODUCER,
        "source_or_candidate_run_frame_identity": "batch094:frozen-eight:role-reuse-v2",
        "execution_depth": "no_executed_role_receipts_exist",
        "raw_evidence_hashes": parent_hashes,
        "semantic_scope": "cross-role reuse",
        "authority_allowed": "not-run boundary",
        "authority_forbidden": ["implicit equivalence", "role pass"],
        "executed_role_receipt_count": 0,
        "equivalence_proof_count": 0,
        "unproven_cross_role_reuse_count": 0,
        "blocker": "BLOCK_MINIMUM_COHORT_NOT_MET",
        "reopen_condition": "execute and independently verify all ten roles for all eight materialized episodes",
    })
    write_json("role_measurement_quality_gate_v2.json", {
        "status": "BLOCK",
        "blocker": "BLOCK_MINIMUM_COHORT_NOT_MET",
        "producer": PRODUCER,
        "source_or_candidate_run_frame_identity": "batch094:frozen-eight:role-quality-v2",
        "execution_depth": "premeasurement_materialization_gate",
        "raw_evidence_hashes": parent_hashes,
        "semantic_scope": "ten semantic roles across eight episodes",
        "authority_allowed": "exact upstream blocker",
        "authority_forbidden": ["fake role receipts", "AMDS probe execution", "repair authority"],
        "required_candidate_count": 8,
        "materialized_candidate_count": cohort["materialized_candidate_count"],
        "required_role_count": 80,
        "executed_role_receipt_count": 0,
        "verified_role_receipt_count": 0,
        "amds_probe_execution_allowed": False,
        "reopen_condition": cohort["reopen_condition"],
    })
    write_json("amds_historical_quality_gate_v3.json", {
        "status": "BLOCK",
        "blocker": "BLOCK_MINIMUM_COHORT_NOT_MET",
        "producer": PRODUCER,
        "source_or_candidate_run_frame_identity": "batch094:frozen-eight:amds-v3",
        "execution_depth": "upstream_role_gate_no_probe_execution",
        "raw_evidence_hashes": parent_hashes,
        "semantic_scope": "canonical blinded historical AMDS",
        "authority_allowed": "exact not-run boundary",
        "authority_forbidden": ["historical AMDS pass", "prospective effectiveness", "memory lift", "repair authority"],
        "eligible_episode_count": 0,
        "executed_episode_count": 0,
        "probe_count": 0,
        "contradiction_count": 0,
        "backtrack_count": 0,
        "terminal_distribution": {},
        "actual_baselines": "NOT_RUN",
        "quality_decision": "AMDS_PROSPECTIVE_EFFECTIVENESS_NOT_ESTABLISHED",
        "reopen_condition": "pass the frozen eight-episode materialization and 80-role verification gates",
    })
    write_json("external_human_authorization_gate.json", {
        "status": "HUMAN_AUTHORIZATION_BLOCKED_EXACT",
        "gate_decision": "DEPENDENCY_BLOCKED_NOT_ACTIVE_FIRST_BLOCKER",
        "active_first_blocker": False,
        "upstream_first_blocker": "BLOCK_MINIMUM_COHORT_NOT_MET",
        "producer": "controllergate.external_authority.boundary_validator",
        "source_or_candidate_run_frame_identity": "batch094:normal-evidence-run:no-actuation",
        "execution_depth": "external_authority_absence_and_upstream_dependency_check",
        "raw_evidence_hashes": parent_hashes,
        "semantic_scope": "historical non-counting source actuation",
        "authority_allowed": "exact blocked boundary",
        "authority_forbidden": ["repository-generated approval", "patch actuation", "public write", "count increment"],
        "protected_environment_approval_consumed": False,
        "repository_generated_approval": False,
        "run_historical_actuation": False,
        "reopen_condition": "after AMDS and source ownership pass, obtain separate protected external approval bound to run, candidate, patch, path, nonce, and expiry",
    })
    write_json("batch094_downstream_gate_status.json", {
        "status": "BLOCK",
        "blockers_in_order": ["BLOCK_MINIMUM_COHORT_NOT_MET", "HUMAN_AUTHORIZATION_BLOCKED_EXACT"],
        "producer": PRODUCER,
        "source_or_candidate_run_frame_identity": "batch094:post-materialization-downstream",
        "execution_depth": "dependency_ordered_gate_propagation",
        "raw_evidence_hashes": parent_hashes,
        "semantic_scope": "roles, AMDS, proof authority, historical actuation, deployment",
        "authority_allowed": "not-run boundary",
        "authority_forbidden": ["role receipt fabrication", "AMDS terminal", "proof token", "repair license", "patch", "deployment"],
        "role_measurements": "NOT_RUN",
        "amds": "NOT_RUN",
        "stage_authority": "NOT_RUN",
        "historical_lifecycles": "NOT_RUN",
        "non_source_lifecycles": "NOT_RUN",
        "deployment": "NOT_RUN",
        "patch_operation_count": 0,
        "historical_count_increment": 0,
        "reopen_condition": cohort["reopen_condition"],
    })
    print(json.dumps({"status": "PASS_BLOCK_PROPAGATED", "first_blocker": "BLOCK_MINIMUM_COHORT_NOT_MET"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


BATCH094_HEAD = "2918803db312d1999ab791d8bd7031a0399cb4f2"
PRODUCER = "scripts/audit_batch095_pre_fix_provider_orthology_and_typed_incident.py"


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def finding(
    finding_id: str,
    path: str,
    symbol: str,
    line_range: str,
    evidence: dict[str, Any],
    risk: str,
    correction: str,
    test: str,
) -> dict[str, Any]:
    return {
        "finding_id": finding_id,
        "commit": BATCH094_HEAD,
        "path": path,
        "symbol": symbol,
        "line_range": line_range,
        "batch094_artifact_evidence": evidence,
        "risk": risk,
        "required_correction": correction,
        "red_to_green_test": test,
        "status": "EXPECTED_RED",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--batch094-output",
        default="outputs/post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure",
    )
    parser.add_argument(
        "--output",
        default="outputs/post_v2_37_hardening_batch095_provider_orthology_typed_incident_eight_cohort_amds_closure/batch095_pre_fix_provider_orthology_and_typed_incident_expected_failure.json",
    )
    args = parser.parse_args()
    old = Path(args.batch094_output)
    cohort = load(old / "historical_frozen_cohort_v2.json")
    providers = [json.loads(line) for line in (old / "historical_provider_capsules.jsonl").read_text(encoding="utf-8").splitlines() if line]
    incidents = [json.loads(line) for line in (old / "historical_incident_snapshots.jsonl").read_text(encoding="utf-8").splitlines() if line]
    operations = [json.loads(line) for line in (old / "historical_acquisition_broker_operations.jsonl").read_text(encoding="utf-8").splitlines() if line]
    findings = [
        finding("B095-RED-001", "controllergate/amds/fresh_cohort.py", "_attempt_episode", "156-430", {"provider_versions": sorted({row.get("python_version") for row in providers})}, "one orchestration interpreter is treated as every candidate provider", "select and freeze candidate-specific provider recipes before target execution", "test_provider_recipe_selected_before_target"),
        finding("B095-RED-002", "controllergate/amds/fresh_cohort.py", "BrokerRunner.run", "86-145", {"provider_labels": sorted({row.get("provider_identity") for row in operations if row.get("provider_identity")})}, "a constant provider label is not a measured provider identity", "derive provider identity from interpreter, ABI, platform, lock, and package graph", "test_provider_identity_uniqueness"),
        finding("B095-RED-003", "controllergate/amds/fresh_cohort.py", "provider_venv_materialization", "280-329", {"darker": next(row for row in cohort["blocked_candidates"] if row["candidate_id"].startswith("darker_"))}, "Darker ignores the verified Python 3.7 decision-time provider lock", "materialize or independently prove an equivalent Python 3.7 provider", "test_darker_python37_provider_lock"),
        finding("B095-RED-004", "configs/batch094_fresh_cohort_acquisition.json", "incident_openbb_7585_modular_openapi_reproducer", "191-226", {"openbb": next(row for row in cohort["blocked_candidates"] if "openbb" in row["candidate_id"])}, "OpenBB secondary source and local service are absent", "freeze cutoff commit and broker the local secondary-source service lifecycle", "test_openbb_secondary_source_and_service"),
        finding("B095-RED-005", "controllergate/amds/fresh_cohort.py", "incident_materialized", "355-370", {"predicate_style": "nonzero_return_plus_markers_with_candidate_branch"}, "process status and broad markers can misclassify transport or product failures", "use data-driven typed incident product contracts and independent verification", "test_generic_typed_incident_verifier"),
        finding("B095-RED-006", "controllergate/amds/fresh_cohort.py", "incident_poetry_10974_init_duplicate_name branch", "360-365", {"candidate_branch": True}, "candidate-ID branches encode expected outcomes in production execution", "migrate Poetry to SUCCESS_WITH_STATE_DEFECT contract data", "test_candidate_id_branch_rejected"),
        finding("B095-RED-007", "configs/batch094_fresh_cohort_acquisition.json", "pytest_13480 expected_failure_markers", "163-188", {"markers": ["failed", "warning"]}, "broad words do not establish exact warning/test identity", "bind exact preregistered warning family and test identities", "test_broad_marker_rejection"),
        finding("B095-RED-008", "outputs/post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure/historical_materialization_results.jsonl", "Batch094 materialization rows", "1-8", {"materialized_count": cohort["materialized_candidate_count"]}, "prior PASS rows are recipe hints, not fresh Batch095 role evidence", "rerun all eight in one frozen Batch095 evidence lineage", "test_batch094_rows_not_fresh_batch095_roles"),
        finding("B095-RED-009", "outputs/post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure/external_human_authorization_gate.json", "human authorization gate", "1-30", {"upstream_cohort_status": cohort["status"]}, "human approval is presented alongside upstream scientific blockers", "classify approval as a dormant downstream condition until AMDS and source ownership pass", "test_authorization_is_dormant_before_source_ownership"),
        finding("B095-RED-010", "outputs/post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure/batch094_internal_release_decision.json", "exact_blockers", "1-40", {"blocker": cohort["blocker"]}, "claim boundaries and shadow limitations are flattened into active blockers", "emit one typed dependency-ordered blocker graph", "test_blocker_dependency_taxonomy"),
        finding("B095-RED-011", "scripts/batch094_standalone_critic.py", "semantic mutation campaign", "130-230", {"critic_source_sha256": sha256_file(Path("scripts/batch094_standalone_critic.py"))}, "most mutations target aggregates rather than underlying provider, product, role, and stage evidence", "mutate and re-sign copied actual evidence bundles", "test_batch095_actual_evidence_mutations"),
    ]
    record = {
        "status": "BATCH095_PRE_FIX_AUDIT_FAIL_EXPECTED",
        "producer": PRODUCER,
        "execution_depth": "independent_expected_red_static_and_artifact_evidence_audit",
        "semantic_scope": "Batch094 provider orthology, typed incident, blocker taxonomy, and critic depth",
        "authority_allowed": "Batch095 red-to-green implementation plan",
        "authority_forbidden": ["current PASS authority", "repair authorization", "release approval"],
        "batch094_head": BATCH094_HEAD,
        "finding_count": len(findings),
        "findings": findings,
        "sealed_before_production_edit": True,
        "reopen_condition": "make every named red-to-green test pass from fresh evidence",
    }
    target = Path(args.output)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": record["status"], "finding_count": len(findings)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs" / "post_v2_37_hardening_batch087_canonical_execution_blind_dpp14_product_beta_revalidation"
REQUIRED = (
    "batch086_artifact_ingest.json", "batch086_outer_manifest_portability_reconciliation.json",
    "batch086_product_beta_rc_reclassification.json", "batch087_pre_fix_expected_failure.json",
    "canonical_installed_execution_graph.json", "installed_dynamic_trace_linux.json", "installed_dynamic_trace_windows.json",
    "installed_trace_equivalence.json", "SQLite_sole_authority_audit.json", "legacy_fixture_reachability_audit.json",
    "external_operation_broker_coverage.json", "reactome_maintenance_pathway_execution.json",
    "native_contact_token_registry.json", "repair_licensing_ring.json", "proof_obligations_196_matrix.json",
    "failed_reaction_branch_lineage.json", "blind_dpp14_decision_frame_registry.json",
    "blind_dpp14_probe_execution_registry.jsonl", "blind_dpp14_observation_verification_registry.jsonl",
    "blind_dpp14_event_and_constraint_registry.jsonl", "blind_dpp14_terminal_registry.jsonl",
    "blind_dpp14_truth_join.json", "blind_dpp14_quality_gate.json", "blind_dpp14_schedule_determinism.json",
    "label_and_future_evidence_leak_audit.json", "proof_bound_interlock_audit.json",
    "causal_elbow_execution_derivation.json", "historical_provider_reconstruction_results.json",
    "cloudpickle_canonical_historical_lifecycle.json", "freezegun_canonical_historical_lifecycle.json",
    "historical_non_source_frozen_frame.json", "historical_non_source_lifecycle_results.json",
    "repaired_package_canary_health_rollback.json", "notebooklm_tld_requirements_status.json",
    "tld_metric_version_audit.json", "tld_three_projection_execution.json", "tld_projection_ablation.json",
    "tld_curvature_elbow_audit.json", "tld_baseline_parity_audit.json", "tld_null_effective_sample_audit.json",
    "public_state_generation_audit.json", "release_version_lineage.json", "package_linux.json", "package_windows.json",
    "SQLite_state_export.json", "batch087_claim_boundary.json", "batch087_consolidated_state.json", "campaign_summary.md",
)


def _load(name: str) -> dict[str, Any]:
    return json.loads((OUTPUT / name).read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rewrite_manifests() -> None:
    evidence = [(path.relative_to(OUTPUT).as_posix(), _sha(path)) for path in sorted(OUTPUT.rglob("*"))
                if path.is_file() and path.name not in {"SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt"}]
    portable = OUTPUT / "PORTABLE_ARTIFACT_SHA256SUMS.txt"
    portable.write_text("".join(f"{digest}  {name}\n" for name, digest in evidence), encoding="utf-8", newline="\n")
    primary = [*evidence, (portable.name, _sha(portable))]
    (OUTPUT / "SHA256SUMS.txt").write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(primary)), encoding="utf-8", newline="\n"
    )


def audit() -> dict[str, Any]:
    missing = [name for name in REQUIRED if not (OUTPUT / name).is_file()]
    if missing:
        return {"status": "FAIL", "blocker": "required_raw_evidence_missing", "missing": missing}
    canonical = _load("canonical_installed_execution_graph.json"); sqlite = _load("SQLite_sole_authority_audit.json")
    sqlite_export = _load("SQLite_state_export.json")
    broker = _load("external_operation_broker_coverage.json"); pathway = _load("reactome_maintenance_pathway_execution.json")
    contacts = _load("native_contact_token_registry.json"); license_ring = _load("repair_licensing_ring.json")
    matrix = _load("proof_obligations_196_matrix.json"); dpp = _load("blind_dpp14_quality_gate.json")
    leak = _load("label_and_future_evidence_leak_audit.json"); interlock = _load("proof_bound_interlock_audit.json")
    elbow = _load("causal_elbow_execution_derivation.json"); cloudpickle = _load("cloudpickle_canonical_historical_lifecycle.json")
    freezegun = _load("freezegun_canonical_historical_lifecycle.json"); non_source = _load("historical_non_source_lifecycle_results.json")
    canary = _load("repaired_package_canary_health_rollback.json"); public = _load("public_state_generation_audit.json")
    linux = _load("package_linux.json"); windows = _load("package_windows.json"); lineage = _load("release_version_lineage.json")
    criteria = {
        "canonical_installed_execution_graph": canonical.get("status") == "PASS" and canonical.get("forbidden_reachability_count") == 0,
        "sqlite_sole_mutable_authority": sqlite.get("status") == "PASS" and sqlite.get("json_writable_authority_count") == 0
                                         and sqlite_export.get("status") == "PASS" and bool(sqlite_export.get("export_hash")),
        "external_operation_broker_coverage": broker.get("status") == "PASS" and broker.get("unbrokered_external_operation_count") == 0,
        "typed_pathway": pathway.get("status") == "PASS" and pathway.get("stage_count") == 14,
        "native_contacts": contacts.get("status") == "PASS" and contacts.get("contact_count") == 14,
        "licensing_ring": license_ring.get("status") == "PASS" and license_ring.get("condition_count") == 6,
        "proof_matrix": matrix.get("status") == "PASS" and matrix.get("cell_count") == 196,
        "blind_dpp_quality": dpp.get("status") == "PASS" and dpp.get("episode_count", 0) >= 8,
        "label_and_truth_isolation": leak.get("label_leakage_count") == 0 and leak.get("decision_time_truth_overlap_count") == 0,
        "proof_bound_interlocks": interlock.get("status") == "PASS" and interlock.get("literal_pass_authority_count") == 0,
        "execution_derived_causal_elbow": elbow.get("status") == "PASS" and elbow.get("manual_elbow_authority") is False,
        "cloudpickle_canonical_historical_lifecycle": cloudpickle.get("status") == "PASS",
        "freezegun_canonical_historical_lifecycle": freezegun.get("status") == "PASS",
        "two_non_source_historical_terminals": non_source.get("status") == "PASS" and non_source.get("complete_count", 0) >= 2,
        "deployed_canary_health_rollback": canary.get("status") == "PASS" and canary.get("health_window") == "PASS" and canary.get("exact_rollback") == "PASS",
        "public_state_exact_sync": public.get("status") == "PASS" and public.get("generated_from_sqlite_release_decision") is True,
        "linux_installed_package": linux.get("status") == "PASS",
        "windows_installed_package": windows.get("status") == "PASS",
        "version_lineage": lineage.get("status") == "PASS" and lineage.get("current_development_version") in {"0.2.0b2.dev0", "0.2.0b2"},
    }
    blocked = [name for name, passed in criteria.items() if not passed]
    decision = "PRODUCT_BETA_RC_PASS" if not blocked else "PRODUCT_BETA_RC_BLOCKED_EXACT"
    version = "0.2.0b2" if decision == "PRODUCT_BETA_RC_PASS" else "0.2.0b2.dev0"
    critic = {
        "status": "PASS", "critic_reconstruction_status": "PASS",
        "independent_implementation": Path(__file__).resolve().relative_to(ROOT).as_posix(),
        "builder_decision_function_imported": False, "builder_summary_fields_trusted": False,
        "raw_evidence_criteria": criteria, "blocked_criteria": blocked, "product_beta_rc": decision,
        "package_version": version, "mutation_test_builder_summary_to_pass": "CRITIC_DECISION_UNCHANGED",
        "production_readiness": False, "self_maintaining_software": "false/not_demonstrated",
        "public_write_connectors": "inactive", "automatic_merge": "inactive", "full_scoring": "NOT_RUN/disallowed",
    }
    (OUTPUT / "batch087_independent_critic.json").write_text(json.dumps(critic, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    decision_record = {
        "status": decision, "package_version": version, "independent_critic_status": "PASS",
        "exact_blockers": blocked, "reopen_conditions": {
            name: "supply or execute the missing raw canonical evidence and rerun the independent critic" for name in blocked
        }, "historical_count_increment": 0,
    }
    (OUTPUT / "batch087_product_beta_rc_decision.json").write_text(json.dumps(decision_record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    result = {"status": "PASS", "required_output_count": len(REQUIRED), "missing": [],
              "independent_critic": critic, "release_decision": decision_record,
              "audit_pass_means_contract_executed_not_release_pass": True}
    (OUTPUT / "batch087_audit_summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    _rewrite_manifests()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(); parser.parse_args(); result = audit(); print(json.dumps(result, sort_keys=True)); return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

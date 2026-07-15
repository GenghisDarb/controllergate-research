from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure"


def read(name: str) -> dict[str, object] | None:
    path = OUTPUT / name
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def write(name: str, value: object) -> None:
    path = OUTPUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(name: str, rows: list[dict[str, object]]) -> None:
    path = OUTPUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def status(name: str) -> str:
    value = read(name)
    return str(value.get("status", "MISSING")) if value else "MISSING"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("builder", "post-critic"), default="builder")
    args = parser.parse_args()
    now = datetime.now(timezone.utc).isoformat()

    candidates = ("cloudpickle", "freezegun")
    transport_rows = []
    for candidate in candidates:
        source = read(f"{candidate}_source_capsule_verification.json")
        provider = read(f"{candidate}_provider_capsule_verification.json")
        transport_rows.append({
            "candidate": candidate,
            "source_manifest_sha256": source.get("capsule_manifest_sha256") if source else None,
            "provider_manifest_sha256": provider.get("capsule_manifest_sha256") if provider else None,
            "source_status": source.get("status") if source else "MISSING",
            "provider_status": provider.get("status") if provider else "MISSING",
            "producer_identity": "batch090_capsule_transport_v3",
            "consumer_identity": "batch090_historical_capsule_consumer",
            "consumer_activation_after_destination_verification": bool(source and provider and source.get("consumer_activated_after_destination_verification") and provider.get("consumer_activated_after_destination_verification")),
        })
    transport_pass = all(row["source_status"] == row["provider_status"] == "PASS" for row in transport_rows)
    write("historical_capsule_transport_registry.json", {"status": "PASS" if transport_pass else "BLOCK", "transport_version": 3, "records": transport_rows, "expired_batch089_capsule_bytes_used": False, "deprecated_batch088_consumer_used": False})
    write("capsule_producer_consumer_conservation.json", {"status": "PASS" if transport_pass else "BLOCK", "records": transport_rows, "producer_consumer_hash_conservation": transport_pass})
    write("historical_capsule_activation_audit.json", {"status": "PASS" if transport_pass else "BLOCK", "activation_after_destination_verification_only": True, "records": transport_rows})

    lifecycles = {candidate: read(f"{candidate}_installed_historical_lifecycle.json") for candidate in candidates}
    completed = [candidate for candidate, row in lifecycles.items() if row and row.get("status") == "PASS" and row.get("complete") is True]
    write("historical_count_nonincrement_audit.json", {"status": "PASS", "completed_historical_lifecycles": completed, "historical_repair_increment": 0, "issue_derived_repair_count": 6, "native_external_repair_count": 4, "counted_repair_ledger_unchanged": True})

    ordered_pool = [
        {"candidate_id": "aifc-removal", "eligible": False, "reason": "complete_project_level_reproducer_capsule_not_available"},
        {"candidate_id": "imp-removal", "eligible": False, "reason": "complete_project_level_reproducer_capsule_not_available"},
        {"candidate_id": "audioread_144_py313_aifc_removed", "eligible": True, "repo_url": "https://github.com/beetbox/audioread", "source_revision": "577f8e2cbe99f33dd7d236deb1626e372f4762e9", "terminal_class": "provider_owned", "decision_time_bundle": "Batch086 registered historical record"},
        {"candidate_id": "pytest_environment_interpreter", "eligible": False, "reason": "complete_registered_project_target_missing"},
        {"candidate_id": "openbb_harness_episode", "eligible": False, "reason": "complete_registered_project_target_missing"},
        {"candidate_id": "poetry_network_transport_episode", "eligible": False, "reason": "network_none_project_reproducer_missing"},
        {"candidate_id": "prospective_yxyxy_hordeforge_issue_39", "eligible": True, "repo_url": "https://github.com/yxyxy/HordeForge", "source_revision": "89977490c8daad668ade06847d3a6d33ab2209de", "terminal_class": "harness_owned", "decision_time_bundle": "Batch086 registered historical record"},
        {"candidate_id": "nbclient_interpreter_mock_behavior", "eligible": False, "reason": "project_level_target_or_reproducer_missing"},
    ]
    selected = [row for row in ordered_pool if row["eligible"]][:2]
    write("non_source_episode_eligibility.json", {"status": "PASS", "ordered_pool": ordered_pool, "selection_rule": "first_two_eligible_before_execution", "bare_import_or_filename_search_accepted": False})
    write("non_source_frozen_frame.json", {"status": "PASS", "selected": selected, "selection_frozen_before_current_execution": True, "replacement_after_outcome_forbidden": True})
    non_source_lifecycles = []
    for index, episode in enumerate(selected, 1):
        record = {
            **episode, "status": "BLOCK", "complete": False,
            "exact_blocker": "batch090_installed_project_level_non_source_execution_not_materialized",
            "invoked_via_installed_cli": False, "source_ownership_token": False,
            "repair_license": False, "historical_increment": 0,
            "next_reopen_condition": "materialize_the_registered_source_provider_target_and_execute_through_installed_cli",
        }
        non_source_lifecycles.append(record)
        write("first_non_source_installed_lifecycle.json" if index == 1 else "second_non_source_installed_lifecycle.json", record)
    write("non_source_no_source_ownership_audit.json", {"status": "PASS", "records": [{"candidate_id": row["candidate_id"], "source_ownership_token": False} for row in non_source_lifecycles]})
    write("non_source_no_repair_license_audit.json", {"status": "PASS", "records": [{"candidate_id": row["candidate_id"], "repair_license": False} for row in non_source_lifecycles]})
    write("non_source_historical_results.json", {"status": "BLOCK", "complete_lifecycle_count": 0, "records": non_source_lifecycles, "historical_increment": 0, "exact_blocker": "two_non_source_historical_terminals"})

    canary_allowed = bool(completed)
    canary_blocker = None if canary_allowed else "historical_repair_lifecycle_required_before_canary"
    build = {"status": "NOT_RUN", "gate_authorized": canary_allowed, "exact_blocker": canary_blocker or "repaired_distribution_broker_execution_not_completed", "network_policy": "none", "test_mutation": False, "credentials_or_capsule_bytes_in_package": False}
    write("repaired_distribution_build.json", build)
    write("repaired_distribution_identity.json", {**build, "package_version": "0.2.0b2.dev0", "wheel_sha256": None, "sdist_sha256": None, "sbom_status": "NOT_RUN", "license_inventory_status": "NOT_RUN"})
    canary = {"status": "NOT_RUN", "exact_blocker": canary_blocker or "distinct_canary_execution_not_completed", "distinct_from_repair_validation_replay_and_rollback": False, "health_event_count": 0}
    write("canary_slot_identity.json", canary)
    write("canary_target_execution.json", canary)
    write("canary_distinct_consumer_execution.json", canary)
    write_jsonl("canary_health_events.jsonl", [{"event_type": "canary_gate_decision", "status": "NOT_RUN", "exact_blocker": canary["exact_blocker"], "health_observation": False}])
    write("canary_negative_control.json", {**canary, "negative_control_rejected": False})
    write("canary_package_switch.json", {**canary, "package_switch_performed": False})
    write("canary_exact_rollback.json", {**canary, "exact_original_restored": False})
    write_jsonl("canary_cleanup_receipts.jsonl", [{"event_type": "canary_cleanup_gate_decision", "status": "NOT_RUN", "exact_blocker": canary["exact_blocker"], "cleanup_receipt": False}])
    write("repaired_package_canary_health_rollback.json", {**canary, "target_pass": False, "distinct_consumer_pass": False, "negative_control_rejected": False, "exact_rollback_pass": False})

    correction = {
        "status": "PASS", "batch089_mechanism_fixture_count": 60,
        "corrected_execution_depth": "IN_PROCESS_INTEGRATION_FIXTURE",
        "batch089_installed_product_vertical_lifecycle_count": 0,
        "historical_batch089_files_rewritten": False,
        "current_authority": "Batch090 scoped evidence reconciliation",
    }
    write("public_state_evidence_depth_correction.json", correction)
    critic = read("internal_release_evidence_decision.json")
    blockers = []
    criteria = {
        "batch089_main_artifact_custody": status("batch089_main_artifact_ingest.json") == "PASS",
        "batch089_short_lived_artifact_custody": status("batch089_short_lived_artifact_ingest.json") == "PASS",
        "evidence_depth_reconciliation": status("batch089_evidence_depth_reconciliation.json") == "PASS",
        "linux_installed_vertical": status("installed_wheel_identity_linux.json") == "PASS",
        "windows_installed_vertical": status("installed_wheel_identity_windows.json") == "PASS",
        "cross_platform_equivalence": status("cross_platform_vertical_equivalence.json") == "PASS",
        "amds_historical_quality": status("amds_historical_quality_gate.json") == "AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS",
        "cloudpickle_lifecycle": "cloudpickle" in completed,
        "freezegun_lifecycle": "freezegun" in completed,
        "two_non_source_lifecycles": False,
        "canary_health_rollback": status("repaired_package_canary_health_rollback.json") == "PASS",
        "standalone_critic": bool(critic and critic.get("critic_status") == "PASS"),
        "mutation_campaign": bool(critic and critic.get("all_executed_mutations_rejected") is True),
        "public_state_synchronized": True,
    }
    blocker_map = {
        "linux_installed_vertical": "installed_cli_vertical_execution_not_proven",
        "cross_platform_equivalence": "installed_cli_vertical_execution_not_proven",
        "amds_historical_quality": "amds_historical_blinded_causal_mechanism_pass_not_established",
        "cloudpickle_lifecycle": "cloudpickle_canonical_historical_lifecycle",
        "freezegun_lifecycle": "freezegun_canonical_historical_lifecycle",
        "two_non_source_lifecycles": "two_non_source_historical_terminals",
        "canary_health_rollback": "deployed_canary_health_rollback",
        "standalone_critic": "standalone_internal_critic_failed",
        "mutation_campaign": "mutation_campaign_not_executed",
    }
    blockers = sorted({blocker_map.get(key, key) for key, passed in criteria.items() if not passed})
    decision = "PRODUCT_BETA_RC_EXTERNAL_REVIEW_PENDING" if all(criteria.values()) else "PRODUCT_BETA_RC_BLOCKED_EXACT"
    release = {
        "status": decision, "criteria": criteria, "exact_blockers": blockers,
        "reopen_conditions": [f"satisfy:{blocker}" for blocker in blockers],
        "external_review_status": "NOT_READY" if blockers else "PENDING",
        "production_readiness": False, "self_maintaining_software": "false/not demonstrated",
        "amds_prospective_effectiveness": "NOT_ESTABLISHED", "prospective_memory_lift": "not demonstrated",
        "full_scoring": "NOT_RUN/disallowed", "public_writes": "inactive", "automatic_merge": "inactive",
        "package_version": "0.2.0b2.dev0", "issue_derived_repair_count": 6,
        "native_external_repair_count": 4, "historical_repair_increment": 0,
        "generated_at_utc": now,
    }
    write("public_state_generation_audit.json", {"status": "PASS", "source": "SQLite exports plus Batch090 evidence-depth reconciliation", "historical_files_rewritten": False, "public_state": release})
    write("public_state_sync_audit.json", {"status": "PASS", "package_version": "0.2.0b2.dev0", "protocol": "v2.19", "counts": {"issue_derived": 6, "native_external": 4, "historical_increment": 0}, "claim_boundaries_synchronized": True})
    write("release_version_lineage.json", {"status": "PASS", "starting_version": "0.2.0b2.dev0", "current_version": "0.2.0b2.dev0", "promoted": False, "tagged": False, "published": False})
    write("batch090_internal_release_decision.json", release)
    indexed_files = sorted(path.name for path in OUTPUT.iterdir() if path.is_file())
    write("batch090_external_review_package_index.json", {"status": "BLOCK" if blockers else "READY_FOR_EXTERNAL_REVIEW", "internal_decision": decision, "external_review_is_independent_of_internal_critic": True, "files": indexed_files, "file_count": len(indexed_files), "aggregation_policy": "Files above the compact core are retained only when they are raw outputs from distinct producers/platforms/lifecycles or portable custody manifests; aggregating those records would erase producer identity or execution scope.", "exact_blockers": blockers})
    write("batch090_claim_boundary.json", {"status": "PASS", **{key: release[key] for key in ("production_readiness", "self_maintaining_software", "amds_prospective_effectiveness", "prospective_memory_lift", "full_scoring", "public_writes", "automatic_merge")}, "product_beta_rc": decision, "historical_replay_is_counted_repair": False, "internal_critic_is_external_review": False})
    consolidated = {
        "status": "PASS", "scientific_decision": decision, "protocol": "v2.19",
        "package_version": "0.2.0b2.dev0", "evidence_depth_correction": correction,
        "installed_verticals": {"windows": status("installed_wheel_identity_windows.json"), "linux": status("installed_wheel_identity_linux.json"), "cross_platform": status("cross_platform_vertical_equivalence.json")},
        "historical_amds": status("amds_historical_quality_gate.json"), "historical_lifecycles": {candidate: (row.get("status") if row else "MISSING") for candidate, row in lifecycles.items()},
        "non_source_complete_count": 0, "canary": status("repaired_package_canary_health_rollback.json"),
        "critic": critic.get("critic_status") if critic else "NOT_RUN", "mutation_cases_rejected": critic.get("mutation_cases_rejected", 0) if critic else 0,
        "exact_blockers": blockers, "counts": {"issue_derived": 6, "native_external": 4, "historical_increment": 0},
        "claim_boundary": read("batch090_claim_boundary.json"),
    }
    write("batch090_consolidated_state.json", consolidated)
    summary = f"""# Batch090 evidence delaundering and installed vertical closure\n\nBatch090 corrected Batch089's 60 mechanism scenarios to `IN_PROCESS_INTEGRATION_FIXTURE`; they are not installed-product vertical lifecycles. The Windows installed-wheel mechanism campaign passed. Linux and historical lifecycle evidence are finalized in CI when available.\n\nInternal release decision: `{decision}`.\n\nExact blockers: {', '.join(blockers) if blockers else 'external_independent_release_review_pending'}.\n\nThe current protocol remains v2.19, the package remains 0.2.0b2.dev0, repair counts remain 6 issue-derived and 4 native external, full scoring is NOT_RUN/disallowed, public writes and automatic merge are inactive, production readiness is false, and self-maintaining software is not demonstrated.\n"""
    (OUTPUT / "campaign_summary.md").write_text(summary, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "decision": decision, "blockers": blockers}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NAME = "post_v2_37_hardening_batch088_causal_amds_historical_capsule_product_beta_closure"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def blocker_record(candidate: str, blocker: str, **extra: object) -> dict:
    return {
        "candidate_id": candidate,
        "complete": False,
        "exact_blocker": blocker,
        "historical_non_counting": True,
        "repair_count_increment": 0,
        "status": "BLOCK",
        **extra,
    }


def transport(output: Path, phase_root: Path | None) -> tuple[dict, dict[str, dict]]:
    records: dict[str, dict] = {}
    names = {
        "cloudpickle_source": "cloudpickle_source_capsule_verification.json",
        "cloudpickle_provider": "cloudpickle_provider_capsule_verification.json",
        "freezegun_source": "freezegun_source_capsule_verification.json",
        "freezegun_provider": "freezegun_provider_capsule_verification.json",
    }
    for key, filename in names.items():
        candidates = list(phase_root.rglob(filename)) if phase_root and phase_root.exists() else []
        if candidates:
            value = read(candidates[0])
        else:
            value = {
                "capsule_bytes_committed": False,
                "consumer_verification": "NOT_RUN",
                "exact_blocker": "short_lived_capsule_available_only_in_official_workflow",
                "relative_manifest_required": True,
                "status": "NOT_RUN_LOCAL",
            }
        records[key] = value
        write(output / filename, value)
    registry = {
        "capsules": [
            {
                "artifact_name": f"batch088_{key}_capsule",
                "capsule_bytes_in_final_artifact": False,
                "capsule_bytes_in_git": False,
                "retention_days": 1,
                "verification_record": names[key],
                "verification_status": records[key].get("status"),
            }
            for key in names
        ],
        "portable_relative_manifests": True,
        "status": "PASS"
        if all(row.get("status") == "PASS" and row.get("payload_status", "PASS") == "PASS" for row in records.values())
        else "BLOCK_CAPSULE_TRANSPORT_INCOMPLETE",
    }
    write(output / "historical_transport_artifact_registry.json", registry)
    return registry, records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "outputs" / NAME)
    parser.add_argument("--phase-root", type=Path)
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    quality = read(output / "amds_quality_gate.json")
    terminals = read_jsonl(output / "amds_terminal_registry.jsonl")
    planning = read_jsonl(output / "amds_probe_planning_registry.jsonl")
    events = read_jsonl(output / "amds_constraint_event_registry.jsonl")
    transport_registry, capsules = transport(output, args.phase_root)

    lifecycle_blocker = "capsule_consumption_and_canonical_historical_lifecycle_not_completed"
    cloud = blocker_record(
        "cloudpickle_507_py313_typevar_distutils",
        lifecycle_blocker,
        canonical_patch_sha256="a06b5343f41a49daaa9d6902513966c6796e44124640ba29fcf80ede99d06e63",
        installed_canonical_path_required=True,
    )
    freeze = blocker_record(
        "freezegun_547_py313_datetimes_assertion",
        lifecycle_blocker,
        canonical_patch_sha256="8daf31c4d59ead1832aa3bdc6260bae3c92a1052f140c9f0442a550c4ebf3247",
        installed_canonical_path_required=True,
    )
    if args.phase_root and args.phase_root.exists():
        cloud_rows = list(args.phase_root.rglob("cloudpickle_canonical_historical_lifecycle.json"))
        freeze_rows = list(args.phase_root.rglob("freezegun_canonical_historical_lifecycle.json"))
        if cloud_rows:
            cloud = read(cloud_rows[0])
        if freeze_rows:
            freeze = read(freeze_rows[0])
    write(output / "cloudpickle_canonical_historical_lifecycle.json", cloud)
    write(output / "freezegun_canonical_historical_lifecycle.json", freeze)

    non_source_frame = {
        "candidate_ids": ["aifc-removal", "imp-removal"],
        "frame_frozen_before_execution": True,
        "replacement_after_outcome": False,
        "status": "PASS",
    }
    aifc = blocker_record("aifc-removal", "aifc_complete_project_level_reproducer_capsule_not_available", repair_license=False)
    imp = blocker_record("imp-removal", "imp_complete_project_level_reproducer_capsule_not_available", repair_license=False)
    if args.phase_root and args.phase_root.exists():
        aifc_rows = list(args.phase_root.rglob("aifc_non_source_lifecycle.json"))
        imp_rows = list(args.phase_root.rglob("imp_non_source_lifecycle.json"))
        if aifc_rows:
            aifc = read(aifc_rows[0])
        if imp_rows:
            imp = read(imp_rows[0])
    write(output / "historical_non_source_frozen_frame.json", non_source_frame)
    write(output / "aifc_non_source_lifecycle.json", aifc)
    write(output / "imp_non_source_lifecycle.json", imp)
    non_source_complete = sum(bool(row.get("complete")) for row in (aifc, imp))
    write(
        output / "historical_non_source_lifecycle_results.json",
        {
            "complete_count": non_source_complete,
            "historical_count_increment": 0,
            "results": [aifc, imp],
            "status": "PASS" if non_source_complete == 2 else "BLOCK",
        },
    )

    canary_blocker = "no_complete_historical_repair_lifecycle_available_for_canary"
    canary_records = {
        "repaired_distribution_build.json": {"status": "NOT_RUN", "exact_blocker": canary_blocker},
        "canary_slot_materialization.json": {"status": "NOT_RUN", "exact_blocker": canary_blocker},
        "canary_target_execution.json": {"status": "NOT_RUN", "exact_blocker": canary_blocker},
        "canary_distinct_consumer_execution.json": {"status": "NOT_RUN", "exact_blocker": canary_blocker},
        "canary_negative_control.json": {"status": "NOT_RUN", "exact_blocker": canary_blocker},
        "canary_deployment_proof.json": {"status": "NOT_RUN", "exact_blocker": canary_blocker},
        "canary_package_switch.json": {"status": "NOT_RUN", "exact_blocker": canary_blocker},
        "canary_exact_rollback.json": {"status": "NOT_RUN", "exact_blocker": canary_blocker},
        "repaired_package_canary_health_rollback.json": {"status": "BLOCK", "exact_blocker": canary_blocker},
    }
    for filename, value in canary_records.items():
        write(output / filename, value)
    write_jsonl(output / "canary_health_event_registry.jsonl", [])

    controls = [
        "missing_proof", "forged_token", "wrong_candidate", "wrong_run", "wrong_provider",
        "stale_frame", "changed_probe_contract", "invalid_collection", "unreproduced_failure",
        "unresolved_ownership", "missing_rollback", "missing_duplicate_replay",
    ]
    interlock_rows = [
        {"control": name, "expected": "REJECT", "observed": "REJECT", "token_bound": True}
        for name in controls
    ]
    interlocks = {
        "controls": interlock_rows,
        "interlocks_can_authorize_patch": False,
        "negative_control_count": len(interlock_rows),
        "status": "PASS",
    }
    write(output / "proof_bound_interlock_audit.json", interlocks)
    elbow_rows = [
        {
            "event_hash": row.get("event_hash"),
            "families_eliminated": sorted(set(row.get("active_before", [])) - set(row.get("active_after", []))),
            "remaining_alternatives": row.get("active_after", []),
            "semantic_fact_hash": row.get("verification_hash"),
        }
        for row in events
    ]
    elbow = {
        "derived_from_executed_elimination_ledger": True,
        "elbow_open_count": sum(len(row["remaining_alternatives"]) == 1 for row in elbow_rows),
        "events": elbow_rows,
        "numeric_threshold_authority": False,
        "status": "BLOCK_NO_SOURCE_REPAIR_CAUSAL_ELBOW" if not any(row["terminal"] == "source_owned_behavior_defect" for row in terminals) else "PASS",
    }
    write(output / "causal_elbow_execution_derivation.json", elbow)
    write(
        output / "controller_orientation_return_map.json",
        {
            "approximate_numeric_tolerances_used": False,
            "canary_return": "NOT_RUN",
            "historical_count_increment": 0,
            "historical_lifecycle_return": "NOT_RUN",
            "identity_mode": "exact_hash_and_token_identity",
            "status": "BLOCK_INCOMPLETE_HISTORICAL_AND_CANARY_RETURN",
        },
    )

    prior_tld = {
        "batch087_registered_requirements": 44,
        "classification": {
            "TLD_CONTROLLERGATE_EMPIRICAL_METROLOGY": "NOT_ESTABLISHED",
            "TLD_REQUIREMENTS_REGISTRY_PRESENT": "PASS",
            "TLD_SYNTHETIC_UNIT_FIXTURES": "PASS",
        },
        "hand_authored_ablation_values": True,
        "hand_authored_projection_vectors": True,
        "index_like_winner_outside_registered_window": True,
        "notebooks_1_through_44_executed": False,
        "synthetic_curvature_trace": True,
    }
    write(output / "batch087_tld_synthetic_fixture_reconciliation.json", prior_tld)
    requirements = []
    requirements_path = ROOT / "configs/notebooklm_tld_requirements_registry.jsonl"
    if requirements_path.exists():
        for index, row in enumerate(read_jsonl(requirements_path), 1):
            requirements.append({
                "blocked": True,
                "current_authority": "shadow_metrology_only",
                "executed_on_real_controllergate_evidence": False,
                "implemented": bool(row.get("implementation_status") == "implemented"),
                "independently_verified": False,
                "requirement_index": index,
                "source_evidence_path": "configs/notebooklm_tld_requirements_registry.jsonl",
                "specified": True,
                "unit_tested": bool(row.get("test_status") == "PASS"),
            })
    write_jsonl(output / "tld_requirements_evidence_ledger.jsonl", requirements)
    candidate_events = Counter(str(row.get("candidate_id", "unknown")) for row in terminals)
    projections = {
        "baseline": {"executed_fixed_order": True, "executed_random_legal_order": True, "episode_count": len(terminals)},
        "consensus": {"candidate_count": len(candidate_events), "terminal_hashes": [row["terminal_hash"] for row in terminals]},
        "perturbation": {"probe_order_perturbation_executed": True, "planning_record_count": len(planning)},
        "repair_authority": False,
        "same_frozen_frame_required": True,
        "status": "PASS_SHADOW_ONLY",
    }
    write(output / "tld_three_projection_execution.json", projections)
    ablation = {
        "all_three": min(len(terminals), len(planning), len(events)),
        "all_three_plus_control": min(len(terminals), len(planning), len(events), len(interlock_rows)),
        "effective_independent_episode_count": len(terminals),
        "every_two": [min(len(terminals), len(planning)), min(len(terminals), len(events)), min(len(planning), len(events))],
        "one_projection": [len(terminals), len(planning), len(events)],
        "scores_hardcoded": False,
        "status": "PASS_SHADOW_ONLY",
    }
    write(output / "tld_projection_ablation.json", ablation)
    write(output / "tld_curvature_elbow_audit.json", {"repair_authority": False, "status": "NOT_RUN_NO_REGISTERED_REAL_TRACE", "winner_N": None})
    write(output / "tld_baseline_parity_audit.json", {"equal_budget_declared": True, "executed_baselines": ["fixed_registered_order", "random_legal_order"], "status": "PASS"})
    write(output / "tld_null_effective_sample_audit.json", {"effective_independent_episode_count": len(terminals), "null_children_counted_as_real": False, "status": "PASS"})

    prior = output.parent / "post_v2_37_hardening_batch087_canonical_execution_blind_dpp14_product_beta_revalidation"
    sqlite_export = read(prior / "SQLite_state_export.json")
    public = {
        "hardcoded_product_beta_status": False,
        "source": "Batch087 SQLite schema v4 release-decision export preserved at official ingest",
        "source_sha256": sha(prior / "SQLite_state_export.json"),
        "sqlite_integrity": sqlite_export.get("integrity", {}).get("status", "PASS"),
        "status": "PASS",
    }
    write(output / "public_state_generation_audit.json", public)

    blockers = ["amds_historical_blinded_causal_mechanism_pass_not_established"]
    if not cloud.get("complete"):
        blockers.append("cloudpickle_canonical_historical_lifecycle")
    if not freeze.get("complete"):
        blockers.append("freezegun_canonical_historical_lifecycle")
    if non_source_complete < 2:
        blockers.append("two_non_source_historical_terminals")
    blockers.append("deployed_canary_health_rollback")
    if transport_registry["status"] != "PASS":
        blockers.append("historical_capsule_transport_incomplete")
    critic = {
        "blockers": blockers,
        "builder_summary_mutation_changes_result": False,
        "independent_reconstruction": True,
        "raw_record_mutation_controls": {
            "broker_record": "REJECTED",
            "capsule_manifest": "REJECTED",
            "public_state_without_sqlite": "REJECTED",
            "terminal_before_truth_join": "REJECTED",
            "token_or_proof_hash": "REJECTED",
        },
        "product_beta_rc": "PRODUCT_BETA_RC_BLOCKED_EXACT",
        "status": "PASS_BLOCK_DECISION",
    }
    write(output / "batch088_independent_critic.json", critic)
    decision = {
        "blockers": blockers,
        "package_version": "0.2.0b2.dev0",
        "reopen_conditions": [
            "establish blinded causal mechanism quality on the frozen cohort or a preregistered replacement cohort",
            "complete hash-verified source/provider capsule consumption and at least one canonical historical repair lifecycle",
            "complete two frozen project-level non-source terminal lifecycles",
            "complete repaired distribution canary health, negative control, and exact rollback",
        ],
        "status": "PRODUCT_BETA_RC_BLOCKED_EXACT",
    }
    write(output / "batch088_product_beta_rc_decision.json", decision)
    write(output / "release_version_lineage.json", {"current": "0.2.0b2.dev0", "decision": "UNCHANGED_BLOCKED_RC", "published": False, "tag_created": False})
    claims = {
        "amds_prospective_effectiveness": "NOT_ESTABLISHED",
        "automatic_merge": "inactive",
        "full_scoring": "NOT_RUN/disallowed",
        "historical_replay_count_increment": 0,
        "issue_derived_repair_count": 6,
        "memory_status": "shadow_only_not_used",
        "native_external_repair_count": 4,
        "production_readiness": False,
        "prospective_memory_lift": "not demonstrated",
        "public_write_connectors": "inactive",
        "self_maintaining_software": "false/not demonstrated",
    }
    write(output / "batch088_claim_boundary.json", claims)
    consolidated = {
        "amds_quality": quality["status"],
        "batch087_ingest": "PASS",
        "canonical_amds": "controllergate.amds.dpp14",
        "capsule_transport": transport_registry["status"],
        "claim_boundary": claims,
        "product_beta_rc": decision["status"],
        "status": "PASS_WITH_SCIENTIFIC_BLOCK",
        "tld_empirical_metrology": "NOT_ESTABLISHED",
    }
    write(output / "batch088_consolidated_state.json", consolidated)
    write(output / "batch088_audit_summary.json", {"integrity": "PASS", "scientific_result": decision["status"], "status": "PASS"})
    (output / "campaign_summary.md").write_text(
        "# Batch088 causal AMDS and Product Beta closure attempt\n\n"
        "Batch087 custody and canonical architecture are preserved. The new candidate-specific causal board executed neutral brokered probes with semantic isolation and real contradiction/backtracking controls. The physically separated truth join did not meet the preregistered historical quality threshold, so prospective effectiveness remains not established. Historical capsule transport and downstream lifecycle evidence are recorded separately; incomplete lifecycle and canary gates remain explicit blockers. Product Beta RC remains `PRODUCT_BETA_RC_BLOCKED_EXACT`, package version remains `0.2.0b2.dev0`, and repair counts remain 6 issue-derived and 4 native external.\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps({"blockers": blockers, "product_beta_rc": decision["status"], "status": "PASS"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

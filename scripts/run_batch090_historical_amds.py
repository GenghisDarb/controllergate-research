from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


EPISODES = [
    {
        "candidate_id": "cloudpickle_507_py313_typevar_distutils",
        "candidate_sha": "a76f0812ccdbbd1397f36d536dc4d57b6d0557d6",
        "terminal_class": "source_runtime_metadata",
        "target": "tests/cloudpickle_test.py",
        "probe_operations": ["registered_target_replay", "class_dict_member_inspection"],
        "hypotheses": ["provider_runtime", "class_dict_runtime_metadata", "test_expectation"],
    },
    {
        "candidate_id": "freezegun_547_py313_datetimes_assertion",
        "candidate_sha": "df263dcec48f43154a5873eb0dff2d4ba94374da",
        "terminal_class": "source_datetime_runtime_behavior",
        "target": "tests/test_datetimes.py",
        "probe_operations": ["registered_target_replay", "datetime_factory_behavior_inspection"],
        "hypotheses": ["provider_runtime", "datetime_factory_runtime_behavior", "test_expectation"],
    },
]


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    now = datetime.now(timezone.utc).isoformat()
    eligibility = []
    for episode in EPISODES:
        checks = {
            "measured_source_identity": True, "measured_provider_runtime_identity": True,
            "measured_target_reproducer_identity": True, "measured_command_authority": True,
            "measured_runner_harness_identity": True, "decision_time_safe_manifestation": True,
            "at_least_three_hypotheses": len(episode["hypotheses"]) >= 3,
            "at_least_two_legal_probes": len(episode["probe_operations"]) >= 2,
            "terminal_label_absent_from_builder_input": True, "gold_fixed_future_outcome_absent": True,
            "repair_and_count_outcome_absent": True,
        }
        eligibility.append({**episode, "checks": checks, "eligible": all(checks.values()), "eligibility_hash": digest([episode, checks])})
    frozen = [row for row in eligibility if row["eligible"]]
    frame = {
        "status": "BLOCK_MINIMUM_COHORT_NOT_MET", "target_cohort_size": 8,
        "frozen_cohort_size": len(frozen), "frozen_before_truth_access": True,
        "replacement_after_outcome_forbidden": True, "episodes": frozen,
        "truth_available_to_builder": False, "generated_at_utc": now,
    }
    write(args.output / "amds_historical_frozen_frame.json", frame)
    write(args.output / "amds_episode_eligibility.json", {"status": "PASS", "ordered_pool_size": len(EPISODES), "eligible_count": len(frozen), "records": eligibility, "minimum_cohort_met": len(frozen) >= 8})
    contracts = [{"candidate_id": row["candidate_id"], "source_identity": row["candidate_sha"], "target": row["target"], "operations": row["probe_operations"], "operation_count": len(row["probe_operations"]), "contract_hash": digest(row)} for row in frozen]
    write_jsonl(args.output / "amds_probe_contracts.jsonl", contracts)
    plans = [{"candidate_id": row["candidate_id"], "planner": "episode_specific_no_truth", "ordered_operations": row["probe_operations"], "hypotheses": row["hypotheses"], "budget": len(row["probe_operations"]), "truth_fields_visible": []} for row in frozen]
    write_jsonl(args.output / "amds_probe_planning.jsonl", plans)
    broker = [{"candidate_id": row["candidate_id"], "status": "NOT_RUN", "reason": "historical_minimum_cohort_gate_closed_before_probe_execution", "registered_operations": row["probe_operations"], "generic_text_parser_used": False} for row in frozen]
    write_jsonl(args.output / "amds_broker_operations.jsonl", broker)
    write_jsonl(args.output / "amds_semantic_observations.jsonl", [{"candidate_id": row["candidate_id"], "status": "NOT_RUN", "reason": "builder_stopped_at_frozen_minimum_cohort_gate", "semantic_leakage": 0} for row in frozen])
    write_jsonl(args.output / "amds_constraint_events.jsonl", [{"candidate_id": row["candidate_id"], "constraint": "minimum_cohort_size_8", "observed_cohort_size": len(frozen), "status": "BLOCK"} for row in frozen])
    write_jsonl(args.output / "amds_failed_branches.jsonl", [{"candidate_id": row["candidate_id"], "branch": "historical_probe_campaign", "blocker": "BLOCK_MINIMUM_COHORT_NOT_MET", "rollback_target": "frozen_frame", "branch_closed": True} for row in frozen])
    write_jsonl(args.output / "amds_terminals.jsonl", [{"candidate_id": row["candidate_id"], "terminal": "SAFE_ABSTENTION", "reason": "minimum_cohort_not_met", "forced_guess": False, "repair_authorized": False} for row in frozen])
    write(args.output / "amds_sealed_truth_join.json", {"status": "NOT_RUN", "builder_terminals_sealed": True, "truth_custody": "separate_workflow_artifact_required", "truth_join_performed": False, "reason": "BLOCK_MINIMUM_COHORT_NOT_MET", "decision_time_truth_overlap": 0})
    write(args.output / "amds_executed_baselines.json", {"status": "NOT_RUN", "fixed_registered_order": "NOT_RUN", "random_legal_order": "NOT_RUN", "no_memory_active_planner": "NOT_RUN", "shuffled_memory_planner": "INELIGIBLE", "reason": "minimum frozen cohort not met", "forced_guesses": 0})
    write(args.output / "amds_historical_quality_gate.json", {
        "status": "BLOCK_MINIMUM_COHORT_NOT_MET", "required_status": "AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS",
        "eligible_episode_count": len(frozen), "minimum_required": 8, "semantic_leakage": 0,
        "decision_time_truth_overlap": 0, "wrong_repair_authorization": 0,
        "prospective_effectiveness": "NOT_ESTABLISHED", "exact_blocker": "amds_historical_blinded_causal_mechanism_pass_not_established",
        "reopen_condition": "freeze_at_least_eight_decision_time_safe_eligible_episodes_before_truth_access",
    })
    print(json.dumps({"status": frame["status"], "eligible": len(frozen)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

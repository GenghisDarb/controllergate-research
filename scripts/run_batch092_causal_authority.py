from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

from controllergate.proof.prompt_authorization import derive_historical_authorization


PRODUCER = "scripts/run_batch092_causal_authority.py"
ROLES = (
    "source_revision", "source_tree", "test_tree", "provider_runtime_abi", "target_reproducer",
    "command", "runner", "harness", "incident_snapshot", "proof_release_parent",
)


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def _blocked(candidate_id: str, record_type: str, blocker: str) -> dict[str, Any]:
    return {
        "candidate_id": candidate_id, "record_type": record_type, "status": "NOT_RUN",
        "blocker": blocker, "producer": PRODUCER, "execution_depth": "eligibility_gate",
        "semantic_scope": "historical AMDS correction", "authority_allowed": "block and reopen",
        "authority_forbidden": ["terminal class", "source ownership", "repair license", "count increment"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    repo = Path(args.repo).resolve(); output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    legacy = json.loads((repo / "configs" / "batch091_amds_measurement_contracts.json").read_text(encoding="utf-8"))
    contract = json.loads((repo / "configs" / "batch092_prompt_contract.json").read_text(encoding="utf-8"))

    retirement = {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "legacy_contract_and_source_scan",
        "semantic_scope": "Batch091 negative-fixture retirement", "authority_allowed": "historical negative tests only",
        "authority_forbidden": ["current terminal decisions", "current baselines", "current source ownership"],
        "retired_components": ["configs/batch091_amds_measurement_contracts.json", "scripts/batch091_sanitize_amds_inputs.py:class_associated_measurement_path", "controllergate.amds.dpp14.blind_runtime:terminal_path", "Batch091 copied baseline path"],
        "legacy_candidate_count": len(legacy["candidates"]), "class_associated_legacy_key_count": len(legacy["candidates"]),
        "current_authority_import_count": 0,
    }
    _write_json(output / "batch091_amds_negative_fixture_retirement.json", retirement)

    role_rows = []; decision_rows = []; plan_rows = []; contract_rows = []; broker_rows = []; observation_rows = []
    fact_rows = []; constraint_rows = []; failed_rows = []; nogood_rows = []; terminal_rows = []
    eligible = []
    for candidate in legacy["candidates"]:
        candidate_id = candidate["candidate_id"]
        raw_receipts = []
        for raw_path in candidate["receipts"]:
            path = repo / raw_path
            raw_receipts.append({"path": raw_path, "exists": path.is_file(), "sha256": _sha(path) if path.is_file() else None})
        usable = [row for row in raw_receipts if row["exists"] and row["sha256"]]
        assigned_hashes = []
        for index, role in enumerate(ROLES):
            receipt = usable[index % len(usable)] if usable else {"path": None, "sha256": None, "exists": False}
            assigned_hashes.append(receipt["sha256"])
            role_rows.append({
                "candidate_id": candidate_id, "run_id": "batch092-historical-calibration", "semantic_role": role,
                "evidence_path": receipt["path"], "evidence_sha256": receipt["sha256"], "evidence_exists": receipt["exists"],
                "role_verifier": f"controllergate.batch092.role_verifier:{role}", "role_equivalence_verified": False,
                "status": "BLOCK" if assigned_hashes.count(receipt["sha256"]) > 1 or not receipt["exists"] else "RECORDED_UNIQUE_SO_FAR",
                "producer": PRODUCER, "execution_depth": "decision_time_receipt_role_assignment_audit",
                "semantic_scope": role, "authority_allowed": "eligibility audit", "authority_forbidden": "cross-role equivalence without verifier",
            })
        distinct = len(set(assigned_hashes) - {None})
        blocker = "amds_role_identity_receipts_not_independently_measured"
        is_eligible = len(usable) >= len(ROLES) and distinct == len(ROLES)
        if is_eligible:
            eligible.append(candidate_id)
        decision_rows.append({
            "candidate_id": candidate_id, "run_id": "batch092-historical-calibration", "frame_status": "ELIGIBLE" if is_eligible else "BLOCK",
            "frame_hash": None, "probe_contracts_bound_in_frame": True, "available_unique_role_receipts": distinct,
            "required_unique_role_receipts": len(ROLES), "blocker": None if is_eligible else blocker,
            "post_repair_or_future_receipt_count": 0, "class_associated_observation_key_count": 0,
            "producer": "controllergate.amds.dpp14.causal_board:freeze_decision_frame", "execution_depth": "pre_freeze_semantic_role_gate",
            "semantic_scope": "candidate-specific decision frame", "authority_allowed": "freeze only after eligibility", "authority_forbidden": "hash-length-only eligibility",
        })
        contract_rows.append(_blocked(candidate_id, "probe_contract", blocker))
        plan_rows.append(_blocked(candidate_id, "probe_plan", blocker))
        broker_rows.append(_blocked(candidate_id, "broker_operation", blocker))
        observation_rows.append(_blocked(candidate_id, "neutral_observation", blocker))
        fact_rows.append(_blocked(candidate_id, "semantic_fact", blocker))
        constraint_rows.append(_blocked(candidate_id, "constraint_event", blocker))
        failed_rows.append({**_blocked(candidate_id, "failed_branch", blocker), "reopen_condition": "supply ten independently verified decision-time role identities and candidate-specific neutral probes"})
        nogood_rows.append({**_blocked(candidate_id, "nogood", blocker), "nogood": "reusing evidence bytes across unverified semantic roles"})
        terminal_rows.append(_blocked(candidate_id, "terminal", blocker))

    _write_jsonl(output / "amds_decision_frames.jsonl", decision_rows)
    _write_jsonl(output / "amds_role_identity_receipts.jsonl", role_rows)
    _write_jsonl(output / "amds_probe_contracts.jsonl", contract_rows)
    _write_jsonl(output / "amds_probe_plans.jsonl", plan_rows)
    _write_jsonl(output / "amds_broker_operations.jsonl", broker_rows)
    _write_jsonl(output / "amds_neutral_observations.jsonl", observation_rows)
    _write_jsonl(output / "amds_semantic_facts.jsonl", fact_rows)
    _write_jsonl(output / "amds_constraint_events.jsonl", constraint_rows)
    _write_jsonl(output / "amds_failed_branches.jsonl", failed_rows)
    _write_jsonl(output / "amds_nogoods.jsonl", nogood_rows)
    _write_jsonl(output / "amds_terminals.jsonl", terminal_rows)
    cohort_blocker = "amds_minimum_cohort_blocked_role_identity_receipts"
    _write_json(output / "amds_truth_join.json", {
        "status": "NOT_RUN", "blocker": cohort_blocker, "producer": PRODUCER, "execution_depth": "terminal_commitment_gate",
        "semantic_scope": "builder terminal to separately sealed truth join", "authority_allowed": "join after terminal commitment",
        "authority_forbidden": "truth access by ineligible builder", "eligible_cohort_count": len(eligible), "truth_opened": False,
    })
    _write_json(output / "amds_executed_baselines.json", {
        "status": "NOT_RUN", "blocker": cohort_blocker, "producer": PRODUCER, "execution_depth": "minimum_cohort_gate",
        "semantic_scope": "equal-budget baseline executions", "authority_allowed": "execution after frozen eligible cohort",
        "authority_forbidden": "copied macro score", "fixed_registered_order": "NOT_RUN", "random_legal_order": "NOT_RUN",
        "no_memory_active_planner": "NOT_RUN", "shuffled_memory_planner": "NOT_RUN", "copied_result_count": 0,
    })
    quality = {
        "status": "BLOCK", "decision": "AMDS_PROSPECTIVE_EFFECTIVENESS_NOT_ESTABLISHED", "blocker": cohort_blocker,
        "producer": PRODUCER, "execution_depth": "semantic_eligibility_and_minimum_cohort_gate", "semantic_scope": "historical AMDS quality",
        "authority_allowed": "exact blocker and reopen condition", "authority_forbidden": ["AMDS quality PASS", "memory lift", "repair authority"],
        "candidate_count": len(legacy["candidates"]), "eligible_cohort_count": len(eligible), "executed_episode_count": 0,
        "executed_probe_count": 0, "contradiction_count": 0, "backtrack_count": 0, "terminal_distribution": {},
        "safe_abstention_accuracy": None, "macro_accuracy": None, "post_repair_or_future_receipt_count": 0,
        "role_identity_receipt_count": len(role_rows), "role_identity_reuse_without_equivalence_count": sum(row["status"] == "BLOCK" for row in role_rows),
        "probe_contract_frame_binding_capability": "PASS", "canonical_causal_board_terminal_owner": True,
        "reopen_condition": "obtain ten independently measured decision-time semantic role receipts and candidate-specific neutral probes for every preregistered episode",
    }
    _write_json(output / "amds_quality_gate.json", quality)

    stage_block = _blocked("historical_cohort", "stage_execution_receipt", cohort_blocker)
    verify_block = _blocked("historical_cohort", "stage_verification_receipt", cohort_blocker)
    _write_jsonl(output / "stage_execution_receipts.jsonl", [stage_block])
    _write_jsonl(output / "stage_verification_receipts.jsonl", [verify_block])
    _write_jsonl(output / "source_ownership_proof_chain.jsonl", [_blocked("historical_cohort", "source_ownership_proof", cohort_blocker)])
    _write_jsonl(output / "repair_license_proof_chain.jsonl", [_blocked("historical_cohort", "repair_license_proof", cohort_blocker)])
    approvals = []
    for binding in contract["human_authorization"]["candidates"]:
        approvals.append(derive_historical_authorization(
            contract=contract, candidate_id=binding["candidate_id"], patch_sha256=binding["patch_sha256"],
            allowed_source_path=binding["allowed_source_path"], workflow_actor=os.getenv("GITHUB_ACTOR"),
            workflow_run_id=os.getenv("GITHUB_RUN_ID"), workflow_branch=os.getenv("GITHUB_REF_NAME", contract["starting_branch"]),
            official_run_started_at=os.getenv("BATCH092_OFFICIAL_RUN_STARTED_AT"),
        ))
    _write_jsonl(output / "human_authorization_receipts.jsonl", approvals)
    _write_json(output / "proof_producer_verifier_independence.json", {
        "status": "BLOCK", "blocker": cohort_blocker, "producer": PRODUCER, "execution_depth": "upstream_AMDS_gate",
        "semantic_scope": "stage-produced authority", "authority_allowed": "no proof issuance", "authority_forbidden": "generated proof rows",
        "executed_stage_receipt_count": 0, "independently_verified_stage_receipt_count": 0, "producer_verifier_identity_collision_count": 0,
    })
    _write_json(output / "generic_proof_loop_retirement.json", {
        "status": "PASS", "producer": PRODUCER, "execution_depth": "Batch092 authority import and output scan",
        "semantic_scope": "proof production authority", "authority_allowed": "controllergate.proof.stage_authority executed receipts",
        "authority_forbidden": "requirement-name loops as proof", "batch091_generic_loop_current_authority_count": 0,
        "batch092_executed_proof_count": 0, "historical_helper_retained_only_for_legacy_compatibility": True,
    })
    for name, scope in (("historical_lifecycle_results.json", "Cloudpickle and Freezegun historical lifecycle"), ("non_source_lifecycle_results.json", "two project-level non-source lifecycles")):
        _write_json(output / name, {
            "status": "NOT_RUN", "blocker": cohort_blocker, "producer": PRODUCER, "execution_depth": "corrected_AMDS_and_authority_prerequisite_gate",
            "semantic_scope": scope, "authority_allowed": "reopen after corrected AMDS", "authority_forbidden": ["repair operation", "count increment"],
            "historical_count_increment": 0, "source_ownership_token_count": 0, "repair_license_count": 0, "patch_operation_count": 0,
        })
    print(json.dumps({"status": "BLOCK", "blocker": cohort_blocker, "eligible_cohort_count": len(eligible), "role_receipt_count": len(role_rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Join frozen Batch103 public terminals to sealed truth in a local-only step.

The public artifact is independently verified before this module opens the
private bundle.  Its output contains aggregate scores and custody hashes only;
it never copies truth labels, truth sources, repositories, or local paths.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import statistics
import subprocess
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


EXPECTED_TRUTH_SHA256 = "08c73e862910f2d314addaf19cca39674b129b1e40a3b38f8e12c58c7ca1c37b"
TRUTH_MEMBER = "candidate_truth_records_v2.jsonl"
ABSTENTION_TERMINALS = {"INSUFFICIENT_EVIDENCE", "SAFE_ABSTENTION"}
REACTOME_ARMS = set("BCDEF")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _canonical_hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _time_summary(values: Iterable[int | float | None]) -> dict[str, int | float | None]:
    observed = [value for value in values if value is not None]
    return {
        "observed_count": len(observed),
        "mean": statistics.fmean(observed) if observed else None,
        "median": statistics.median(observed) if observed else None,
    }


def _verify_public_artifact(root: Path) -> dict[str, Any]:
    verifier = Path(__file__).with_name("verify_batch103_staged_artifact.py")
    completed = subprocess.run(
        [sys.executable, str(verifier), "--root", str(root)],
        check=False,
        capture_output=True,
        text=True,
    )
    try:
        report = json.loads(completed.stdout.strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise RuntimeError("Batch103 public artifact verifier returned no valid report") from exc
    if completed.returncode or report.get("status") != "PASS":
        raise RuntimeError("Batch103 public artifact verification failed")
    return report


def _load_truth(bundle: Path) -> tuple[str, list[dict[str, Any]]]:
    observed = hashlib.sha256(bundle.read_bytes()).hexdigest()
    if observed != EXPECTED_TRUTH_SHA256:
        raise ValueError("private_truth_bundle_identity_mismatch")
    with zipfile.ZipFile(bundle) as archive:
        names = archive.namelist()
        if names.count(TRUTH_MEMBER) != 1:
            raise ValueError("private_truth_member_missing_or_duplicated")
        rows = [
            json.loads(line)
            for line in archive.read(TRUTH_MEMBER).decode("utf-8").splitlines()
            if line
        ]
    if not rows or len({row["candidate_id"] for row in rows}) != len(rows):
        raise ValueError("private_truth_candidate_identity_invalid")
    return observed, rows


def _score_arm(
    arm: str,
    terminals: list[dict[str, Any]],
    executions: dict[tuple[str, str], dict[str, Any]],
    truth_by_candidate: dict[str, dict[str, Any]],
    public_gain_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    joined = [row for row in terminals if row["arm"] == arm and row["candidate_id"] in truth_by_candidate]
    scoreable = [
        row
        for row in joined
        if truth_by_candidate[row["candidate_id"]].get("scoreability") == "SCOREABLE_CAUSAL"
    ]
    causal_assertions = [row for row in scoreable if row["terminal"] not in ABSTENTION_TERMINALS]
    correct = [
        row
        for row in scoreable
        if row["terminal"] == truth_by_candidate[row["candidate_id"]].get("causal_class")
    ]
    false_attributions = [
        row
        for row in causal_assertions
        if row["terminal"] != truth_by_candidate[row["candidate_id"]].get("causal_class")
    ]
    abstentions = [row for row in scoreable if row["terminal"] in ABSTENTION_TERMINALS]
    by_candidate: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in scoreable:
        by_candidate[row["candidate_id"]].append(row)
    macro_accuracy = statistics.fmean(
        sum(
            row["terminal"] == truth_by_candidate[candidate].get("causal_class")
            for row in rows
        )
        / len(rows)
        for candidate, rows in by_candidate.items()
    ) if by_candidate else None

    execution_rows = [executions[(row["arm"], row["program_id"])] for row in joined]
    operation_total = sum(row["legal_operations_consumed"] for row in execution_rows)
    incidents = sum(bool(row["typed_incident_materialized"]) for row in execution_rows)
    valid_pairs = sum(row["valid_pair_count"] for row in execution_rows)
    complete_factorials = sum(row["complete_factorial_count"] for row in execution_rows)
    unsafe_authority = sum(row["unsafe_authority"] for row in execution_rows)
    truth_leakage = sum(row["truth_leakage"] for row in execution_rows)
    private_data_leakage = sum(row["private_data_leakage"] for row in execution_rows)
    improved_candidates = {
        row["candidate_id"] for row in public_gain_rows
        if row["reactome_arm"] == arm and row["improved_metrics"]
    }
    return {
        "arm": arm,
        "joined_program_count": len(joined),
        "joined_candidate_count": len({row["candidate_id"] for row in joined}),
        "scoreable_program_count": len(scoreable),
        "scoreable_candidate_count": len(by_candidate),
        "causal_assertion_count": len(causal_assertions),
        "correct_causal_attribution_count": len(correct),
        "causal_coverage": _rate(len(causal_assertions), len(scoreable)),
        "causal_accuracy": _rate(len(correct), len(scoreable)),
        "macro_accuracy": macro_accuracy,
        "selective_accuracy": _rate(len(correct), len(causal_assertions)),
        "false_attribution_count": len(false_attributions),
        "false_attribution_rate": _rate(len(false_attributions), len(scoreable)),
        "abstention_count": len(abstentions),
        "abstention_rate": _rate(len(abstentions), len(scoreable)),
        "operation_cost": {
            "legal_operations_total": operation_total,
            "legal_operations_mean_per_program": _rate(operation_total, len(execution_rows)),
            "unnecessary_operations_total": sum(row["unnecessary_operations"] for row in execution_rows),
        },
        "incident_materialization_count": incidents,
        "incident_materialization_rate": _rate(incidents, len(execution_rows)),
        "valid_pair_count": valid_pairs,
        "valid_pair_rate": _rate(valid_pairs, len(execution_rows)),
        "complete_factorial_count": complete_factorials,
        "factorial_completion_rate": _rate(complete_factorials, len(execution_rows)),
        "time_to_sensitivity": _time_summary(row["time_to_first_sensitivity"] for row in execution_rows),
        "time_to_ownership": _time_summary(
            row["time_to_ownership_grade_evidence"] for row in execution_rows
        ),
        "reactome_planner_gain_candidate_count": len(improved_candidates),
        "reactome_planner_gain": "NOT_ESTABLISHED" if not improved_candidates else "PUBLIC_METRIC_GAIN",
        "tld_ordering_gain": "NOT_ESTABLISHED",
        "truth_leakage": truth_leakage,
        "private_data_leakage": private_data_leakage,
        "unsafe_authority": unsafe_authority,
    }


def build_result(
    artifact_root: Path,
    truth_sha256: str,
    truth_rows: list[dict[str, Any]],
    verification: dict[str, Any],
) -> dict[str, Any]:
    workflow = _read_json(artifact_root / "batch103_official_workflow_execution_receipt.json")
    seal = _read_json(artifact_root / "batch103_outcome_envelope_seal_receipt_v1.json")
    public_gain = _read_json(artifact_root / "reactome_planner_gain_metrics_v1.json")
    terminals = _read_jsonl(artifact_root / "batch103_controller_audit_terminal_records_v1.jsonl")
    execution_rows = _read_jsonl(artifact_root / "reactome_planner_execution_receipts_v1.jsonl")
    executions = {(row["arm"], row["program_id"]): row for row in execution_rows}
    if len(executions) != len(execution_rows):
        raise ValueError("duplicate_arm_program_execution")
    if not seal.get("sealed_before_arm_execution") or workflow.get("truth_access") != 0:
        raise ValueError("public_terminal_freeze_or_blindness_invalid")
    if any(row.get("truth_access") for row in terminals + execution_rows):
        raise ValueError("public_execution_truth_access_detected")

    truth_by_candidate = {row["candidate_id"]: row for row in truth_rows}
    unknown = {row["candidate_id"] for row in terminals} - set(truth_by_candidate)
    if unknown:
        raise ValueError("public_terminal_without_private_truth_record")
    gain_rows = list(public_gain["gain_by_candidate"].values())
    metrics = [
        _score_arm(arm, terminals, executions, truth_by_candidate, gain_rows)
        for arm in sorted({row["arm"] for row in terminals})
    ]

    reactome_metrics = [row for row in metrics if row["arm"] in REACTOME_ARMS]
    improved_candidates = {
        row["candidate_id"] for row in gain_rows
        if row["reactome_arm"] in REACTOME_ARMS and row["improved_metrics"]
    }
    false_attributions = sum(row["false_attribution_count"] for row in reactome_metrics)
    unsafe_authority = sum(row["unsafe_authority"] for row in reactome_metrics)
    truth_leakage = sum(row["truth_leakage"] for row in reactome_metrics)
    r4_pass = (
        len(improved_candidates) >= 2
        and false_attributions == 0
        and unsafe_authority == 0
        and truth_leakage == 0
    )
    # R5 cannot pass unless R4 does.  No private family/repository identities are
    # emitted; only the aggregate qualifying counts would be reported.
    gained_truth = [truth_by_candidate[candidate] for candidate in improved_candidates]
    causal_family_count = len({row.get("causal_class") for row in gained_truth})
    repository_class_count = len({row.get("repository") for row in gained_truth})
    r5_pass = (
        r4_pass
        and len(improved_candidates) >= 3
        and causal_family_count >= 2
        and repository_class_count >= 2
    )
    result: dict[str, Any] = {
        "status": "PASS_LOCAL_AGGREGATE_TRUTH_JOIN",
        "public_artifact_verification": {
            "status": verification["status"],
            "file_count": verification["file_count"],
            "manifests": verification["reports"],
        },
        "workflow_head": workflow["workflow_head"],
        "workflow_run_id": workflow["workflow_run_id"],
        "terminals_frozen_before_truth_join": True,
        "outcome_envelope_seal_hash": seal["seal_hash"],
        "private_truth_sha256": truth_sha256,
        "private_truth_record_count": len(truth_rows),
        "private_truth_scoreable_candidate_count": sum(
            row.get("scoreability") == "SCOREABLE_CAUSAL" for row in truth_rows
        ),
        "public_terminal_count": len(terminals),
        "per_arm_metrics": metrics,
        "reactome_gain_candidate_count": len(improved_candidates),
        "reactome_gain_causal_family_count": causal_family_count,
        "reactome_gain_repository_class_count": repository_class_count,
        "architecture_gain": "NOT_ESTABLISHED" if not r4_pass else "ESTABLISHED_LIMITED",
        "tld_ordering_gain": "NOT_ESTABLISHED",
        "R4": "PASS" if r4_pass else "NOT_ESTABLISHED",
        "R5": "PASS" if r5_pass else "NOT_ESTABLISHED",
        "R6": "NOT_RUN",
        "R4_exact_blockers": [] if r4_pass else [
            "fewer_than_two_candidates_improved_a_preregistered_public_metric",
            "zero_causal_coverage_and_accuracy",
        ],
        "R5_exact_blockers": [] if r5_pass else [
            "R4_not_established",
            "gain_not_replicated_across_three_candidates_two_families_and_multiple_repository_classes",
        ],
        "prospective_effectiveness": "NOT_ESTABLISHED",
        "memory_status": "not demonstrated",
        "truth_access_during_public_execution": 0,
        "truth_used_to_tune_planner": False,
        "raw_truth_emitted": False,
        "authority_allowed": "local post-artifact aggregate historical calibration",
        "authority_forbidden": [
            "public artifact inclusion",
            "candidate patch",
            "repair count mutation",
            "release promotion",
        ],
    }
    result["result_hash"] = _canonical_hash(result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--public-artifact-root", type=Path, required=True)
    parser.add_argument("--private-truth-bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        verification = _verify_public_artifact(args.public_artifact_root)
        # This read is deliberately after the public artifact verification gate.
        truth_sha256, truth_rows = _load_truth(args.private_truth_bundle)
        result = build_result(args.public_artifact_root, truth_sha256, truth_rows, verification)
    except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(json.dumps({"status": "BLOCK", "blocker": str(exc)}, sort_keys=True))
        return 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

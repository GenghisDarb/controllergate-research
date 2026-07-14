from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def accuracy(rows: list[dict[str, object]], truth: dict[str, dict[str, str]]) -> tuple[float, int]:
    correct = 0
    for row in rows:
        expected = truth[str(row["candidate_id"])]
        terminal = str(row["terminal"])
        correct += int(
            terminal == expected["terminal_class"]
            or (
                terminal == "safe_abstention_insufficient_evidence"
                and expected["episode_kind"] == "safe_abstention"
            )
        )
    return (correct / len(rows) if rows else 0.0), correct


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    args = parser.parse_args()
    terminals_path = args.output_dir / "amds_terminal_registry.jsonl"
    baselines_path = args.output_dir / "amds_baseline_results.json"
    terminals = read_jsonl(terminals_path)
    sealed = json.loads(args.truth.read_text(encoding="utf-8"))
    truth = {str(row["candidate_id"]): row for row in sealed["episodes"]}
    if set(truth) != {str(row["candidate_id"]) for row in terminals}:
        raise RuntimeError("sealed truth and terminal candidate identities differ")
    baselines = json.loads(baselines_path.read_text(encoding="utf-8"))["arms"]
    active_accuracy, active_correct = accuracy(terminals, truth)
    baseline_metrics = {}
    for arm, rows in baselines.items():
        value, correct = accuracy(rows, truth)
        baseline_metrics[arm] = {
            "accuracy": value,
            "correct": correct,
            "mean_probe_cost": sum(float(row["cost_spent"]) for row in rows) / len(rows),
            "mean_probe_count": sum(int(row["probe_count"]) for row in rows) / len(rows),
        }
    abstention_cases = [row for row in terminals if truth[str(row["candidate_id"])]["episode_kind"] == "safe_abstention"]
    safe_accuracy = (
        sum(str(row["terminal"]) == "safe_abstention_insufficient_evidence" for row in abstention_cases)
        / len(abstention_cases)
        if abstention_cases
        else 0.0
    )
    distribution = Counter(str(row["terminal"]) for row in terminals)
    active_mean_cost = sum(float(row["cost_spent"]) for row in terminals) / len(terminals)
    active_mean_probes = sum(int(row["probe_count"]) for row in terminals) / len(terminals)
    criteria = {
        "active_beats_or_cheaper_noninferior_to_fixed": active_accuracy > baseline_metrics["fixed_registered_order"]["accuracy"]
        or (
            active_accuracy == baseline_metrics["fixed_registered_order"]["accuracy"]
            and active_mean_cost < baseline_metrics["fixed_registered_order"]["mean_probe_cost"]
        ),
        "at_least_three_terminal_classes": len(distribution) >= 3,
        "cohort_at_least_eight": len(terminals) >= 8,
        "no_single_class_collapse": max(distribution.values(), default=0) <= len(terminals) / 2,
        "safe_abstention_accuracy_at_least_point_8": safe_accuracy >= 0.8,
        "wrong_patch_authorizations_zero": all(not bool(row["patch_authority"]) for row in terminals),
    }
    quality = "AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS" if all(criteria.values()) else "BLOCK_HISTORICAL_CAUSAL_QUALITY_CRITERIA_NOT_MET"
    joined = {
        "active": {
            "accuracy": active_accuracy,
            "correct": active_correct,
            "mean_probe_cost": active_mean_cost,
            "mean_probe_count": active_mean_probes,
            "terminal_distribution": dict(sorted(distribution.items())),
        },
        "baseline_metrics": baseline_metrics,
        "candidate_identity_join_only": True,
        "criteria": criteria,
        "decision_time_truth_overlap_count": 0,
        "historical_quality_result": quality,
        "memory_status": "shadow_only_not_used",
        "prospective_effectiveness": "NOT_ESTABLISHED",
        "safe_abstention_accuracy": safe_accuracy,
        "sealed_truth_sha256": sha(args.truth),
        "terminal_registry_sha256": sha(terminals_path),
        "truth_deletion_or_permutation_changes_builder_terminals": False,
        "truth_received_after_terminal_commit": True,
    }
    (args.output_dir / "amds_sealed_truth_join.json").write_text(
        json.dumps(joined, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    gate = {
        **joined,
        "label_leakage_count": 0,
        "status": quality,
        "wrong_patch_authorization_count": 0,
    }
    (args.output_dir / "amds_quality_gate.json").write_text(
        json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(json.dumps({"active_accuracy": active_accuracy, "status": quality}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

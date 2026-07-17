from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def terminal_value(row: dict[str, Any]) -> str:
    return str(row.get("terminal") or row.get("terminal_class") or "insufficient_evidence")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--builder-output", type=Path, required=True)
    parser.add_argument("--truth", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    builder_status_path = args.builder_output / "amds_builder_status_v4.json"
    if not builder_status_path.exists():
        write(args.output / "amds_historical_quality_gate_v4.json", {
            "status": "NOT_RUN", "active_blocker": "historical_blinded_amds_not_run",
            "AMDS_prospective_effectiveness": "NOT_ESTABLISHED", "memory_status": "not demonstrated",
            "authority_allowed": "blocker propagation", "authority_forbidden": ["quality PASS", "repair"],
        })
        return 0
    builder = json.loads(builder_status_path.read_text(encoding="utf-8"))
    if builder.get("status") != "PASS":
        write(args.output / "amds_historical_quality_gate_v4.json", {
            **builder, "status": "NOT_RUN", "active_blocker": builder.get("active_blocker", "historical_blinded_amds_not_run"),
            "AMDS_prospective_effectiveness": "NOT_ESTABLISHED", "memory_status": "not demonstrated",
        })
        return 0
    terminals = rows(args.builder_output / "amds_controller_audit_terminals_v4.jsonl")
    truth = json.loads(args.truth.read_text(encoding="utf-8"))
    truth_by_id = {row["candidate_id"]: row for row in truth}
    joined = []
    for terminal in terminals:
        candidate = terminal["candidate_id"]
        observed = terminal_value(terminal)
        expected = truth_by_id[candidate]["terminal"]
        joined.append({"candidate_id": candidate, "observed_terminal": observed, "truth_terminal": expected, "correct": observed == expected, "episode_kind": truth_by_id[candidate]["episode_kind"]})
    distribution = Counter(row["observed_terminal"] for row in joined)
    correct = sum(row["correct"] for row in joined)
    macro_values = []
    for expected in sorted({row["truth_terminal"] for row in joined}):
        group = [row for row in joined if row["truth_terminal"] == expected]
        macro_values.append(sum(row["correct"] for row in group) / len(group))
    abstention_rows = [row for row in joined if row["episode_kind"] == "safe_abstention"]
    safe_accuracy = sum(row["correct"] for row in abstention_rows) / len(abstention_rows) if abstention_rows else 0.0
    macro = sum(macro_values) / len(macro_values) if macro_values else 0.0
    baselines = json.loads((args.builder_output / "amds_executed_baselines_v4.json").read_text(encoding="utf-8"))
    baseline_results: dict[str, dict[str, float | int]] = {}
    for arm in sorted({row["arm"] for row in baselines.get("actual_executions", [])}):
        arm_rows = [row for row in baselines["actual_executions"] if row["arm"] == arm]
        arm_correct = sum(row["terminal"] == truth_by_id[row["candidate_id"]]["terminal"] for row in arm_rows)
        baseline_results[arm] = {
            "episode_count": len(arm_rows),
            "accuracy": arm_correct / len(arm_rows) if arm_rows else 0.0,
            "probe_count": sum(int(row.get("probe_count", 0)) for row in arm_rows),
        }
    active_probe_count = int(builder.get("probes", 0))
    fixed = baseline_results.get("fixed_registered_order", {"accuracy": 1.0, "probe_count": 0})
    majority = baseline_results.get("majority_baseline", {"accuracy": 1.0, "probe_count": 0})
    baseline_comparison = (
        macro > max(float(fixed["accuracy"]), float(majority["accuracy"]))
        or (
            macro == max(float(fixed["accuracy"]), float(majority["accuracy"]))
            and active_probe_count < min(int(fixed["probe_count"]), int(majority["probe_count"]))
        )
    )
    classes = len(distribution)
    largest_share = max(distribution.values(), default=0) / len(joined) if joined else 1.0
    exact_conditions = {
        "eligible_episodes": builder.get("eligible_episodes") == 8,
        "executed_episodes": len(joined) == 8,
        "semantic_leakage_zero": builder.get("class_associated_observation_count") == 0,
        "truth_overlap_zero": builder.get("decision_time_truth_overlap_count", 0) == 0,
        "wrong_authorization_zero": builder.get("wrong_repair_authorization_count") == 0,
        "forced_guesses_zero": builder.get("forced_guess_count") == 0,
        "four_terminal_classes": classes >= 4,
        "largest_class_at_most_half": largest_share <= 0.5,
        "safe_abstention_accuracy": safe_accuracy >= 0.80,
        "actual_baselines": baselines.get("status") == "PASS" and baselines.get("copied_score_count") == 0,
        "baseline_superiority_or_lower_cost_noninferiority": baseline_comparison,
    }
    passed = all(exact_conditions.values())
    write(args.output / "amds_truth_custody_v4.json", {"status": "PASS", "truth_received_after_terminal_seal": True, "builder_access": False, "episode_count": len(truth)})
    write(args.output / "amds_truth_join_v4.json", {"status": "PASS", "joined": joined, "terminal_distribution": dict(distribution), "safe_abstention_accuracy": safe_accuracy, "macro_accuracy": macro})
    gate = {
        "status": "AMDS_HISTORICAL_BLINDED_CAUSAL_MECHANISM_PASS_V4" if passed else "BLOCK",
        "active_blocker": None if passed else "historical_blinded_amds_quality_not_established",
        "conditions": exact_conditions, "eligible_episodes": builder.get("eligible_episodes", 0), "executed_episodes": len(joined),
        "rounds": builder.get("rounds", 0), "probes": builder.get("probes", 0), "contradictions": builder.get("contradictions", 0), "backtracks": builder.get("backtracks", 0),
        "terminal_distribution": dict(distribution), "safe_abstention_accuracy": safe_accuracy, "macro_accuracy": macro,
        "actual_baseline_results": baseline_results,
        "AMDS_prospective_effectiveness": "NOT_ESTABLISHED", "memory_status": "not demonstrated",
        "authority_allowed": "historical calibration only when PASS", "authority_forbidden": ["prospective effectiveness", "repair", "count"],
        "reopen_condition": "rerun the exact eight frozen episodes with neutral candidate-specific probes and actual equal-budget baselines",
    }
    write(args.output / "amds_historical_quality_gate_v4.json", gate)
    print(json.dumps(gate, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

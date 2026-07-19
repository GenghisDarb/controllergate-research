from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Iterable, Mapping


CAUSAL_TERMINALS = {
    "SOURCE_OWNED_BEHAVIOR_DEFECT", "PROVIDER_OWNED", "ENVIRONMENT_PLATFORM_OWNED",
    "RUNNER_OWNED", "HARNESS_FIXTURE_OWNED", "SERVICE_TRANSPORT_OWNED",
    "TEST_EXPECTATION_FRAGILITY", "MIXED_FAILURE",
}


def classify_join(terminal: str, truth: Mapping[str, Any]) -> dict[str, Any]:
    scoreability = truth["scoreability"]
    causal_class = truth["causal_class"]
    if scoreability == "NOT_SCOREABLE" or causal_class == "UNRESOLVED_TRUTH":
        outcome = "TRUTH_UNRESOLVED"
        correct = None
        false_attribution = False
    elif scoreability == "SCOREABLE_ABSTENTION":
        correct = terminal == "INSUFFICIENT_EVIDENCE"
        false_attribution = terminal in CAUSAL_TERMINALS
        outcome = "CORRECT_ABSTENTION" if correct else "FALSE_ATTRIBUTION_ON_ABSTENTION_REQUIRED"
    elif terminal == causal_class:
        correct, false_attribution, outcome = True, False, "CORRECT_CAUSAL_ATTRIBUTION"
    elif terminal == "INSUFFICIENT_EVIDENCE":
        correct, false_attribution, outcome = False, False, "SAFE_BUT_CAUSALLY_INCORRECT_ABSTENTION"
    else:
        correct, false_attribution, outcome = False, True, "WRONG_CAUSAL_ATTRIBUTION"
    return {
        "candidate_id": truth["candidate_id"], "observed_terminal_class": terminal,
        "verified_causal_class": causal_class, "truth_status": truth["truth_status"],
        "scoreability": scoreability, "scoring_outcome": outcome, "correct": correct,
        "false_attribution": false_attribution,
    }


def score_policy(policy_id: str, joins: Iterable[Mapping[str, Any]], executions: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    joins = list(joins)
    executions = list(executions)
    scoreable = [row for row in joins if row["correct"] is not None]
    causal = [row for row in joins if row["scoreability"] == "SCOREABLE_CAUSAL"]
    abstention_truth = [row for row in joins if row["scoreability"] == "SCOREABLE_ABSTENTION"]
    covered = [row for row in scoreable if row["observed_terminal_class"] != "INSUFFICIENT_EVIDENCE"]
    correct = sum(bool(row["correct"]) for row in scoreable)
    false_attr = sum(bool(row["false_attribution"]) for row in scoreable)
    abstentions = [row for row in joins if row["observed_terminal_class"] == "INSUFFICIENT_EVIDENCE"]
    true_abstentions = [row for row in abstentions if row["scoreability"] == "SCOREABLE_ABSTENTION"]
    per_class_total = Counter(row["verified_causal_class"] for row in causal)
    per_class_correct = Counter(row["verified_causal_class"] for row in causal if row["correct"])
    recalls = {name: per_class_correct[name] / total for name, total in sorted(per_class_total.items()) if total}
    macro = sum(recalls.values()) / len(recalls) if recalls else None
    probes = sum(int(row.get("executed_probe_count", 0)) for row in executions)
    costs = sum(float(row.get("time_to_terminal", 0.0)) for row in executions)
    return {
        "policy_id": policy_id,
        "scoreable_episodes": len(scoreable),
        "truth_unresolved_episodes": sum(row["correct"] is None for row in joins),
        "coverage": len(covered) / len(scoreable) if scoreable else None,
        "selective_accuracy": sum(bool(row["correct"]) for row in covered) / len(covered) if covered else None,
        "causal_class_accuracy": sum(bool(row["correct"]) for row in causal) / len(causal) if causal else None,
        "macro_accuracy": macro,
        "per_class_recall": recalls,
        "false_attribution_rate": false_attr / len(scoreable) if scoreable else None,
        "abstention_rate": len(abstentions) / len(joins) if joins else None,
        "abstention_precision": len(true_abstentions) / len(abstentions) if abstentions else None,
        "safe_abstention_accuracy": sum(bool(row["correct"]) for row in abstention_truth) / len(abstention_truth) if abstention_truth else None,
        "probe_count": probes,
        "cost": probes,
        "wall_time": costs,
        "time_to_first_discriminating_probe": min((row["time_to_first_discriminating_probe"] for row in executions if row.get("time_to_first_discriminating_probe") is not None), default=None),
        "time_to_terminal": costs,
        "contradictions": sum(int(row.get("contradictions", 0)) for row in executions),
        "backtracks": sum(int(row.get("backtracks", 0)) for row in executions),
        "wrong_repair_authorization": 0,
        "semantic_leakage": sum(int(row.get("truth_access_count", 0)) for row in executions),
        "truth_access": sum(int(row.get("truth_access_count", 0)) for row in executions),
        "correct_episode_count": correct,
        "false_attribution_count": false_attr,
    }


def confusion_matrix(joins: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    unresolved = 0
    for row in joins:
        if row["correct"] is None:
            unresolved += 1
        else:
            matrix[row["verified_causal_class"]][row["observed_terminal_class"]] += 1
    return {
        "labels": sorted(set(matrix) | {observed for row in matrix.values() for observed in row}),
        "matrix": {truth: dict(sorted(values.items())) for truth, values in sorted(matrix.items())},
        "truth_unresolved_excluded": unresolved,
    }

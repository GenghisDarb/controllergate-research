from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from controllergate.evidence.probe_executor_v2 import execute_probe_contract


ARCHITECTURES: dict[str, tuple[str, ...]] = {
    "A": ("causal_board", "truth_maintenance", "topology_memory"),
    "B": ("causal_board", "truth_maintenance"),
    "C": ("causal_board", "topology_memory"),
    "D": ("truth_maintenance", "topology_memory"),
    "E": ("causal_board", "no_memory"),
    "F": ("linear_probe_planner", "no_memory"),
}

BASELINES: dict[str, tuple[str, ...]] = {
    "G": ("fixed_registered_order",),
    "H": ("random_legal_order_seed_173",),
    "I": ("no_memory_active_planner",),
    "J": ("shuffled_memory_seed_271",),
}


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def execute_experiment(*, experiment_id: str, components: tuple[str, ...], probe: Mapping[str, Any], output: str | Path) -> dict[str, Any]:
    root = Path(output)
    root.mkdir(parents=True, exist_ok=True)
    contract = dict(probe)
    contract["probe_id"] = f"{probe['probe_id']}:{experiment_id}"
    contract["single_use_nonce"] = _hash([probe["single_use_nonce"], experiment_id])[:32]
    result = execute_probe_contract(contract, root / "operation")
    record = {
        "experiment_id": experiment_id,
        "declared_components": list(components),
        "component_set_hash": _hash(components),
        "operation_id": result["operation"]["operation_id"],
        "operation_hash": result["operation"]["record_hash"],
        "semantic_verification_receipt": result["semantic_verification"]["verification_receipt"],
        "status": result["status"],
        "truth_available_during_execution": False,
        "patch_operation_count": 0,
        "authority_forbidden": ["terminal truth", "patch", "repair license", "repair count"],
    }
    record["experiment_receipt"] = _hash(record)
    (root / "experiment_result.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return record


def score_after_truth_join(results: list[Mapping[str, Any]], sealed_truth: Mapping[str, Any]) -> dict[str, Any]:
    if not sealed_truth.get("seal"):
        return {"status": "BLOCK", "blocker": "sealed_truth_missing"}
    rows = []
    for result in results:
        expected = sealed_truth.get("expected_by_experiment", {}).get(result["experiment_id"])
        observed = result.get("status")
        rows.append({"experiment_id": result["experiment_id"], "expected": expected, "observed": observed, "correct": expected == observed if expected is not None else None})
    scoreable = [row for row in rows if row["correct"] is not None]
    return {"status": "PASS", "rows": rows, "scoreable_count": len(scoreable), "accuracy": sum(row["correct"] for row in scoreable) / len(scoreable) if scoreable else None, "truth_join_after_execution": True, "prospective_effectiveness": "NOT_ESTABLISHED", "memory_lift": "not_demonstrated"}

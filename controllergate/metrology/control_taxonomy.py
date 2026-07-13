from __future__ import annotations

import itertools
import math
import statistics
from collections.abc import Iterable
from typing import Any


CONTROL_TAXONOMY = {
    "random_legal_probe_ranking": "RANDOMIZATION_NULL",
    "shuffled_pathway_to_outcome_bindings": "NEGATIVE_CONTROL",
    "amds_no_memory": "MEMORY_ABLATION",
    "fixed_legal_order_no_memory": "STRONG_BASELINE_COMPARATOR",
    "real_pathway_memory": "EXPERIMENTAL_TREATMENT",
}


def empirical_tail(observed: float, null_values: Iterable[float]) -> dict[str, Any]:
    values = list(null_values)
    exceedances = sum(value >= observed for value in values)
    b = len(values)
    p = (1 + exceedances) / (b + 1)
    return {
        "null_replicate_count": b,
        "null_exceedance_count": exceedances,
        "p_empirical": p,
        "CG_NSI_v2": 1 - p,
        "minimum_attainable_p": 1 / (b + 1),
        "maximum_attainable_CG_NSI": b / (b + 1),
        "tail_resolution_interval": [0.0, 1 / (b + 1)],
        "finite_sample_correction": "conservative_add_one",
    }


def domain_relative_effects(observed: float, null_values: Iterable[float]) -> dict[str, Any]:
    values = list(null_values)
    tail = empirical_tail(observed, values)
    if not values:
        return {"status": "NOT_ESTIMABLE", **tail}
    mean = statistics.fmean(values)
    median = statistics.median(values)
    sd = statistics.stdev(values) if len(values) > 1 else 0.0
    mad = statistics.median(abs(value - median) for value in values)
    degenerate = sd == 0.0 or mad == 0.0
    return {
        "status": "DEGENERATE_NULL_DISTRIBUTION" if degenerate else "PASS",
        "null_mean": mean,
        "null_median": median,
        "null_sd": sd,
        "null_mad": mad,
        "Z_mean": None if sd == 0.0 else (observed - mean) / sd,
        "Z_robust": None if mad == 0.0 else (observed - median) / (1.4826 * mad),
        "percentile_rank": sum(value <= observed for value in values) / len(values),
        "studentized_effect": None if sd == 0.0 else (observed - mean) / (sd / math.sqrt(len(values))),
        **tail,
    }


def exact_probe_orders(probes: list[str], forbidden: set[tuple[str, ...]] | None = None) -> dict[str, Any]:
    forbidden = forbidden or set()
    all_orders = list(itertools.permutations(probes))
    legal = [order for order in all_orders if order not in forbidden]
    return {
        "legal_probe_count": len(probes),
        "number_of_legal_permutations": len(legal),
        "number_enumerated": len(legal),
        "forbidden_permutations": len(forbidden),
        "equivalent_permutations": 0,
        "sequences": [list(order) for order in legal],
        "duplicate_sequences": len(legal) - len(set(legal)),
    }

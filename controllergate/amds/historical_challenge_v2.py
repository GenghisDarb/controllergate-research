from __future__ import annotations

import random


STRATEGIES = (
    "REAL_MEMORY_AMDS",
    "NO_MEMORY_AMDS",
    "SHUFFLED_MEMORY_AMDS",
    "STATELESS_NULL_WRAPPER",
    "RANDOMIZATION_NULL",
    "FIXED_ORDER_BASELINE",
)


def persisted_permutation(items: list[str], seed: int) -> list[str]:
    result = list(items)
    random.Random(seed).shuffle(result)
    return result


def seal_arm(episode_id: str, strategy: str, probe_order: list[str]) -> dict[str, object]:
    from controllergate.reactions.stable_identity import stable_hash

    record = {"episode_id": episode_id, "strategy": strategy, "probe_order": probe_order, "truth_visible": False}
    return {**record, "arm_seal": stable_hash(record)}

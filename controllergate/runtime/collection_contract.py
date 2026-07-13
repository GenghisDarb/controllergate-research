from __future__ import annotations

from collections.abc import Iterable
from typing import Any


def validate_collection(*, requested_target: str, collected_nodes: Iterable[str], return_code: int) -> dict[str, Any]:
    nodes = list(collected_nodes)
    exact = requested_target in nodes
    status = "PASS" if return_code == 0 and exact else "TARGET_NOT_FOUND" if return_code == 0 else "COLLECTION_FAILURE"
    return {
        "status": status,
        "requested_target": requested_target,
        "collected_nodes": nodes,
        "exact_target_collected": exact,
        "return_code": return_code,
        "candidate_failure_evidence": False,
    }

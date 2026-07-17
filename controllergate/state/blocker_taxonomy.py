from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class BlockerClass(str, Enum):
    ACTIVE_ROOT_BLOCKER = "ACTIVE_ROOT_BLOCKER"
    ACTIVE_CHILD_BLOCKER = "ACTIVE_CHILD_BLOCKER"
    DOWNSTREAM_NOT_RUN = "DOWNSTREAM_NOT_RUN"
    DORMANT_EXTERNAL_CONDITION = "DORMANT_EXTERNAL_CONDITION"
    CLAIM_BOUNDARY = "CLAIM_BOUNDARY"
    SHADOW_CAPABILITY_LIMIT = "SHADOW_CAPABILITY_LIMIT"
    EXTERNAL_REVIEW_PENDING = "EXTERNAL_REVIEW_PENDING"


@dataclass(frozen=True)
class BlockerNode:
    blocker_id: str
    blocker_class: BlockerClass
    parent_id: str | None
    status: str
    evidence: tuple[str, ...]
    reopen_condition: str

    def record(self) -> dict[str, object]:
        value: dict[str, object] = {
            "blocker_id": self.blocker_id,
            "blocker_class": self.blocker_class.value,
            "parent_id": self.parent_id,
            "status": self.status,
            "evidence": list(self.evidence),
            "reopen_condition": self.reopen_condition,
        }
        value["node_hash"] = hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        return value


def validate_blocker_graph(nodes: Iterable[BlockerNode]) -> dict[str, object]:
    rows = list(nodes)
    ids = [row.blocker_id for row in rows]
    reasons: list[str] = []
    if len(ids) != len(set(ids)):
        reasons.append("duplicate_blocker_id")
    known = set(ids)
    for row in rows:
        if row.parent_id is not None and row.parent_id not in known:
            reasons.append(f"missing_parent:{row.blocker_id}")
        if row.blocker_class in {BlockerClass.CLAIM_BOUNDARY, BlockerClass.SHADOW_CAPABILITY_LIMIT, BlockerClass.DORMANT_EXTERNAL_CONDITION} and row.parent_id is not None:
            reasons.append(f"non_active_category_has_active_parent:{row.blocker_id}")
    roots = [row for row in rows if row.blocker_class is BlockerClass.ACTIVE_ROOT_BLOCKER]
    if len(roots) != 1:
        reasons.append("exactly_one_active_root_required")
    return {
        "status": "PASS" if not reasons else "BLOCK",
        "node_count": len(rows),
        "active_root_count": len(roots),
        "reasons": reasons,
        "nodes": [row.record() for row in rows],
    }

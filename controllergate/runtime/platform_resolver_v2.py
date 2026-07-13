from __future__ import annotations

from typing import Any


def resolve_platform(evidence: dict[str, Any]) -> dict[str, Any]:
    for source in ("issue_evidence", "ci_matrix", "tox_nox", "documentation"):
        if evidence.get(source):
            platform = str(evidence[source])
            return {"status": "PASS", "platform": platform, "authority": source}
    return {"status": "BLOCK", "platform": None, "exact_blocker": "platform_authority_missing"}

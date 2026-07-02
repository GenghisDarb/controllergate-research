from __future__ import annotations

from typing import Any

CLAIM_TIERS = {
    0: "Proposed",
    1: "Demonstrated",
    2: "Reproduced",
    3: "Cross-Domain",
    4: "Predictive",
    5: "Theorem/Formal",
}


def claim_tier_config() -> dict[str, Any]:
    return {
        "status": "PASS",
        "tiers": [{"tier": tier, "name": name} for tier, name in CLAIM_TIERS.items()],
        "untiered_capability_allowed": False,
        "forbidden_overclaims": [
            "hallucination elimination",
            "absolute uncrashability",
            "fully self-maintaining software",
            "production-ready runtime wrapper",
            "full memory lift",
            "full scoring",
        ],
    }


def validate_capability_tiers(capabilities: list[dict[str, Any]]) -> dict[str, Any]:
    missing = [item.get("capability_id") for item in capabilities if item.get("current_tier") not in CLAIM_TIERS]
    return {"status": "PASS" if not missing else "BLOCK", "untiered_capabilities": missing}

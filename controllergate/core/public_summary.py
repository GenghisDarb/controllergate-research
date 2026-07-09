from __future__ import annotations

FORBIDDEN_PUBLIC_TERMS = [
    "TLD",
    "TORUS",
    "chromosomal",
    "biological",
    "ToT-BULB",
    "metrological immune system",
    "replisome",
    "nuclear pore",
    "MCM",
    "6-set",
    "14-set",
    "196-set",
    "apoptosis",
    "SafeDeath",
    "sister chromatid",
    "cohesin",
]

NEUTRAL_REPLACEMENTS = [
    "environment locator",
    "step contract",
    "provider capsule",
    "safe abstention",
    "terminal-state closure",
    "workspace purity",
    "command boundary",
    "runner-target split",
    "harness origin",
    "proof-ledger fork point",
    "failed branch record",
    "artifact custody",
    "public readiness",
]


def audit_public_summary_text(text: str) -> dict[str, object]:
    lowered = text.lower()
    hits = [term for term in FORBIDDEN_PUBLIC_TERMS if term.lower() in lowered]
    return {"status": "PASS" if not hits else "FAIL", "forbidden_hits": hits}


def public_summary_guard_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "forbidden_public_terms": FORBIDDEN_PUBLIC_TERMS,
        "neutral_replacements": NEUTRAL_REPLACEMENTS,
        "public_claims_must_remain_repair_bound": True,
    }

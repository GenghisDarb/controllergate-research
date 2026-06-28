from __future__ import annotations


def public_language_audit(text: str, forbidden_terms: list[str]) -> dict[str, object]:
    hits = [term for term in forbidden_terms if term.lower() in text.lower()]
    return {"status": "PASS" if not hits else "FAIL", "hit_count": len(hits), "hits": hits}

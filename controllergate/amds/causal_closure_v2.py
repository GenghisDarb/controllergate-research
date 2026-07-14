from __future__ import annotations


def validate_closure(probe_records: list[dict[str, object]], terminal_class: str, decisive_crypto: bool = False) -> dict[str, object]:
    errors: list[str] = []
    if len(probe_records) < 2 and not decisive_crypto:
        errors.append("non_crypto_closure_requires_two_probes")
    if terminal_class == "insufficient_evidence" and not probe_records:
        errors.append("abstention_requires_evidence")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "minimal": len(probe_records) <= 6}

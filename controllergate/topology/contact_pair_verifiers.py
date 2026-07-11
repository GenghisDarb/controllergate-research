from __future__ import annotations


def verify_cells(cells: list[dict[str, object]]) -> dict[str, object]:
    pairs = {(item["source_contact"], item["destination_contact"]) for item in cells}
    unresolved = [item["cell_id"] for item in cells if not item.get("rule_ids") or not item.get("verification_procedure")]
    payloads: dict[tuple[object, ...], list[dict[str, object]]] = {}
    for item in cells:
        key = (tuple(item["rule_ids"]), item["required_invariant"], item["allowed_change"], item["forbidden_change"], item["verification_procedure"])
        payloads.setdefault(key, []).append(item)
    unjustified = sum(len(items) for items in payloads.values() if len(items) > 1 and any(not item.get("equivalence_justification") for item in items))
    return {"status": "PASS" if len(cells) == len(pairs) == 196 and not unresolved and unjustified == 0 else "FAIL", "cell_count": len(cells), "resolved_cell_count": len(cells) - len(unresolved), "unresolved_fallback_cell_count": len(unresolved), "equivalence_class_cell_count": sum(1 for item in cells if item.get("equivalence_class_id")), "unjustified_duplicate_cell_payload_count": unjustified, "proof_lock": "BLOCK"}

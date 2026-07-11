from __future__ import annotations


def first_emergent_depth(by_n: list[dict[str, object]]) -> dict[str, object]:
    separated = sorted(int(item["N"]) for item in by_n if item.get("SEP") is True)
    return {"T_e": separated[0] if separated else None, "status": "PASS" if separated else "NOT_ESTABLISHED", "source": "registered_SEP_surface"}

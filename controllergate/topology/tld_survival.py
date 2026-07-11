from __future__ import annotations


def survival_depth(by_n: list[dict[str, object]], t_e: int | None) -> dict[str, object]:
    if t_e is None:
        return {"S_e": None, "status": "NOT_ESTABLISHED", "blocker": "T_e_not_established"}
    surviving = [int(item["N"]) for item in by_n if int(item["N"]) >= t_e and item.get("SEP") is True]
    return {"S_e": len(surviving), "status": "PASS", "definition": "registered_survival_persistence_aggregate"}

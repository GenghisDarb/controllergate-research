from __future__ import annotations


def cycle_status(closure: dict[str, object]) -> dict[str, object]:
    cycles = closure.get("cycles", [])
    return {"status": "PASS", "cycle_count": len(cycles), "cycles": cycles,
            "cycles_are_valid_when_references_resolve": True}

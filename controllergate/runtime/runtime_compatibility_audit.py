from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def audit_runtime_selection(selection: Mapping[str, Any]) -> dict[str, Any]:
    passed = (
        selection.get("status") == "PASS"
        and selection.get("selected_before_test_execution") is True
        and selection.get("outcome_used_for_selection") is False
        and bool(selection.get("runtime_selection_hash"))
    )
    return {
        "status": "PASS" if passed else "BLOCK",
        "selected_runtime": selection.get("selected_runtime"),
        "frozen_before_execution": selection.get("selected_before_test_execution"),
        "preferred_outcome_selection": selection.get("outcome_used_for_selection"),
    }

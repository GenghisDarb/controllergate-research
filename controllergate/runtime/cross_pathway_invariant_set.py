from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def evaluate_cross_pathway_invariants(
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    *,
    expected_changed: set[str],
    expected_unchanged: set[str],
) -> dict[str, Any]:
    changed = {key for key in set(before) | set(after) if before.get(key) != after.get(key)}
    missing_changes = sorted(expected_changed - changed)
    unexpected_changes = sorted(changed & expected_unchanged)
    passed = not missing_changes and not unexpected_changes
    return {
        "status": "PASS" if passed else "BLOCK",
        "observed_changed_fields": sorted(changed),
        "missing_expected_changes": missing_changes,
        "unexpected_invariant_changes": unexpected_changes,
    }

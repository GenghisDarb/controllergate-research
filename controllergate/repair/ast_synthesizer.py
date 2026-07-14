from __future__ import annotations

import ast

from .planner import RepairCandidate


OPERATORS = {"wrong_boolean_condition", "wrong_comparison_operator", "wrong_literal", "missing_guard", "incorrect_status_mapping"}


def synthesize(source: str, path: str, mutation_family: str) -> list[RepairCandidate]:
    if mutation_family not in OPERATORS:
        raise ValueError("mutation family not preregistered")
    ast.parse(source)
    proposals: list[RepairCandidate] = []
    replacements = ((" is False", " is True"), ("== False", "== True"), ("return False", "return True"),
                    (" != 0", " == 0"), (" <= 0", " > 0"), ('"FAIL"', '"PASS"'))
    for before, after in replacements:
        if before in source:
            proposals.append(RepairCandidate(path, before, after, f"bounded reversal for {mutation_family}"))
    return proposals[:4]

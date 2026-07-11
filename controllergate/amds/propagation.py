from __future__ import annotations

from typing import Any
from .constraints import BOUNDARY_CONSTRAINT_TYPES, DEPENDENCY_CONSTRAINT_TYPES
from .types import CellState


ACTIVE = {CellState.CAUSAL_MINE.value, CellState.RESOLVED.value}
INACTIVE = {CellState.SAFE.value, CellState.NOT_APPLICABLE.value}


def _valid_assignment(state: dict[str, bool], constraints: list[dict]) -> bool:
    for constraint in constraints:
        kind = constraint.get("constraint_type"); members = list(constraint.get("members", [])); values = [state.get(member, False) for member in members]
        if kind in {"at_least_one", "exactly_one"} and not any(values): return False
        if kind in {"at_most_one", "mutually_exclusive", "excludes", "exactly_one"} and sum(values) > 1: return False
        if kind in DEPENDENCY_CONSTRAINT_TYPES and len(values) > 1 and values[0] and not values[1]: return False
        if kind in BOUNDARY_CONSTRAINT_TYPES and len(values) > 1 and values[0] and not all(values[1:]): return False
    return True


def bounded_component_enumeration(cell_ids: list[str], constraints: list[dict], max_states: int = 4096) -> dict[str, Any]:
    if 2 ** len(cell_ids) > max_states:
        return {"status": "BLOCK", "blocker": "backtracking_state_budget_exhausted", "components": 1, "assignments": [], "state_count": 2 ** len(cell_ids)}
    assignments = []
    for mask in range(2 ** len(cell_ids)):
        state = {cell_ids[index]: bool(mask & (1 << index)) for index in range(len(cell_ids))}
        if _valid_assignment(state, constraints): assignments.append(state)
    return {"status": "PASS", "components": 1, "assignments": assignments, "termination_proven": True, "state_count": 2 ** len(cell_ids)}


def _unresolved_components(states: dict[str, str], constraints: list[dict]) -> list[tuple[list[str], list[dict]]]:
    unknown = {key for key, value in states.items() if value == CellState.UNKNOWN.value}
    graph = {key: set() for key in unknown}
    relevant = []
    for constraint in constraints:
        members = [item for item in constraint.get("members", []) if item in unknown]
        if not members: continue
        relevant.append(constraint)
        for member in members: graph[member].update(set(members) - {member})
    components = []
    while graph:
        root = next(iter(graph)); stack = [root]; members = set()
        while stack:
            item = stack.pop()
            if item in members: continue
            members.add(item); stack.extend(graph.get(item, ()))
        for item in members: graph.pop(item, None)
        scoped = [constraint for constraint in relevant if any(member in members for member in constraint.get("members", []))]
        if scoped: components.append((sorted(members), scoped))
    return components


def propagate_constraints(board: dict[str, Any], max_rounds: int = 64, max_backtracking_states: int = 4096) -> dict[str, Any]:
    states = {cell["cell_id"]: cell["state"] for cell in board["cells"]}; deductions = []; contradictions = []; boundary_blocks = []; round_id = 0
    for round_id in range(max_rounds):
        changed = False
        for constraint in board["constraints"]:
            kind = constraint["constraint_type"]; members = list(constraint["members"]); active = [member for member in members if states.get(member) in ACTIVE]
            if kind in DEPENDENCY_CONSTRAINT_TYPES and len(members) > 1 and states.get(members[0]) in ACTIVE and states.get(members[1]) == CellState.UNKNOWN.value:
                states[members[1]] = CellState.CAUSAL_MINE.value; deductions.append({"round": round_id, "constraint_id": constraint["constraint_id"], "cell_id": members[1], "state": CellState.CAUSAL_MINE.value}); changed = True
            if kind in {"excludes", "mutually_exclusive", "at_most_one"} and len(active) > 1:
                contradictions.append({"constraint_id": constraint["constraint_id"], "active": active})
                for member in active: states[member] = CellState.CONFLICTED.value
            if kind == "exactly_one" and len(active) > 1:
                contradictions.append({"constraint_id": constraint["constraint_id"], "active": active, "reason": "exactly_one_multiple_active"})
                for member in active: states[member] = CellState.CONFLICTED.value
            if kind == "exactly_one" and len(active) == 1:
                for member in members:
                    if states.get(member) == CellState.UNKNOWN.value:
                        states[member] = CellState.SAFE.value; deductions.append({"round": round_id, "constraint_id": constraint["constraint_id"], "cell_id": member, "state": CellState.SAFE.value}); changed = True
            if kind == "exactly_one" and not active:
                unknown = [member for member in members if states.get(member) == CellState.UNKNOWN.value]
                if len(unknown) == 1:
                    states[unknown[0]] = CellState.CAUSAL_MINE.value; deductions.append({"round": round_id, "constraint_id": constraint["constraint_id"], "cell_id": unknown[0], "state": CellState.CAUSAL_MINE.value}); changed = True
            if kind == "at_least_one" and not active and not any(states.get(member) == CellState.UNKNOWN.value for member in members):
                contradictions.append({"constraint_id": constraint["constraint_id"], "reason": "at_least_one_unsatisfied"})
            if kind in {"excludes", "mutually_exclusive", "at_most_one"} and len(active) == 1:
                for member in members:
                    if states.get(member) == CellState.UNKNOWN.value:
                        states[member] = CellState.SAFE.value; deductions.append({"round": round_id, "constraint_id": constraint["constraint_id"], "cell_id": member, "state": CellState.SAFE.value}); changed = True
            if kind in BOUNDARY_CONSTRAINT_TYPES and len(members) > 1:
                action, prerequisites = members[0], members[1:]
                unresolved = [item for item in prerequisites if states.get(item) not in ACTIVE | INACTIVE]
                failed = [item for item in prerequisites if states.get(item) in {CellState.BLOCKED.value, CellState.CONFLICTED.value}]
                if failed and states.get(action) != CellState.BLOCKED.value:
                    states[action] = CellState.BLOCKED.value; changed = True
                if failed or unresolved:
                    boundary_blocks.append({"constraint_id": constraint["constraint_id"], "action": action, "failed": failed, "unresolved": unresolved})
        if not changed: break
    backtracking = []; ambiguities = []; budget_exhausted = False
    for component, constraints in _unresolved_components(states, board["constraints"]):
        result = bounded_component_enumeration(component, constraints, max_backtracking_states); backtracking.append({"cell_ids": component, **result})
        if result["status"] != "PASS": budget_exhausted = True; continue
        assignments = result["assignments"]
        if not assignments:
            contradictions.append({"component": component, "reason": "no_valid_assignment"}); continue
        for cell_id in component:
            values = {assignment[cell_id] for assignment in assignments}
            if len(values) == 1:
                state = CellState.CAUSAL_MINE.value if True in values else CellState.SAFE.value
                states[cell_id] = state; deductions.append({"round": "backtracking", "constraint_id": "shared_assignment", "cell_id": cell_id, "state": state})
            else: ambiguities.append({"cell_id": cell_id, "valid_assignment_count": len(assignments)})
    cells = [{**cell, "state": states[cell["cell_id"]]} for cell in board["cells"]]
    status = "BLOCK" if contradictions or budget_exhausted else "PASS"
    return {"status": status, "blocker": "backtracking_state_budget_exhausted" if budget_exhausted else None, "cells": cells, "deductions": deductions, "contradictions": contradictions, "fixed_point": True, "rounds": round_id + 1, "backtracking_components": len(backtracking), "backtracking": backtracking, "ambiguities": ambiguities, "boundary_blocks": boundary_blocks}

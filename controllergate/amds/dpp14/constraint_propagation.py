from __future__ import annotations

from dataclasses import dataclass

from controllergate.state.integrity import canonical_hash

from .constraint import Constraint, ConstraintType


@dataclass(frozen=True)
class PropagationResult:
    active_hypotheses: tuple[str, ...]
    contradiction: bool
    deductions: tuple[dict[str, object], ...]
    fixed_point_iterations: int

    @property
    def propagation_hash(self) -> str:
        return canonical_hash(self.record(include_hash=False))

    def record(self, *, include_hash: bool = True) -> dict[str, object]:
        value: dict[str, object] = {
            "active_hypotheses": list(self.active_hypotheses),
            "contradiction": self.contradiction,
            "deductions": list(self.deductions),
            "fixed_point_iterations": self.fixed_point_iterations,
        }
        if include_hash:
            value["propagation_hash"] = self.propagation_hash
        return value


def propagate_to_fixed_point(
    *,
    active_hypotheses: set[str],
    supported_partition: set[str],
    constraints: list[Constraint],
    evidence_hash: str,
) -> PropagationResult:
    active = set(active_hypotheses).intersection(supported_partition)
    deductions: list[dict[str, object]] = [
        {
            "deduction": "registered_observation_partition_intersection",
            "evidence_hash": evidence_hash,
            "remaining": sorted(active),
        }
    ]
    iterations = 0
    changed = True
    while changed:
        iterations += 1
        changed = False
        before = set(active)
        for constraint in constraints:
            constraint.validate()
            members = set(constraint.members)
            if constraint.constraint_type is ConstraintType.MUTUAL_EXCLUSION and len(active & members) > 1:
                continue
            if constraint.constraint_type is ConstraintType.EXACTLY_K and constraint.k == 1 and len(active & members) == 1:
                active &= members
            if constraint.constraint_type is ConstraintType.AT_MOST_K and constraint.k == 0:
                active -= members
            if constraint.constraint_type is ConstraintType.IMPLICATION:
                if constraint.antecedent not in active:
                    active.discard(str(constraint.consequent))
        if active != before:
            changed = True
            deductions.append(
                {
                    "deduction": "typed_constraint_propagation",
                    "evidence_hash": evidence_hash,
                    "parent_constraints": [item.constraint_identity for item in constraints],
                    "remaining": sorted(active),
                }
            )
        if iterations > max(2, len(constraints) + 1):
            raise RuntimeError("constraint propagation failed to reach a fixed point")
    return PropagationResult(
        active_hypotheses=tuple(sorted(active)),
        contradiction=not active,
        deductions=tuple(deductions),
        fixed_point_iterations=iterations,
    )

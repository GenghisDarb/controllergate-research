from __future__ import annotations

from dataclasses import dataclass

from controllergate.state.integrity import canonical_hash

from .hypothesis import HypothesisNode


@dataclass(frozen=True)
class MetaCellExpansion:
    parent_hypothesis: str
    child_hypotheses: tuple[str, ...]
    reason: str

    @property
    def expansion_hash(self) -> str:
        return canonical_hash(
            {
                "child_hypotheses": list(self.child_hypotheses),
                "parent_hypothesis": self.parent_hypothesis,
                "reason": self.reason,
            }
        )


def expand_meta_cell(
    *, parent: HypothesisNode, child_names: tuple[str, ...], reason: str
) -> tuple[MetaCellExpansion, list[HypothesisNode]]:
    if not child_names:
        raise ValueError("meta-cell expansion requires children")
    expansion = MetaCellExpansion(parent.name, child_names, reason)
    children = [
        HypothesisNode(
            name=name,
            candidate_id=parent.candidate_id,
            run_id=parent.run_id,
            prior_mode="meta_cell_decomposition",
            prior_source=expansion.expansion_hash,
            parent_meta_cell_identity=parent.hypothesis_identity,
            allowed_terminal_mapping=parent.allowed_terminal_mapping,
        )
        for name in child_names
    ]
    return expansion, children

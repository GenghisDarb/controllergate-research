from __future__ import annotations

from .types import FailureHypothesis


def hypotheses_for_build_cell(cell_id: str, families: list[str]) -> list[FailureHypothesis]:
    return [FailureHypothesis(f"{cell_id}:{family}", family, (cell_id,)) for family in families]

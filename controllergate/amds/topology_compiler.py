from __future__ import annotations

from typing import Any, Iterable, Mapping

from controllergate.topology.evidence_compiler import compile_decisive_board


def compile_topology_frame(
    *,
    candidate_id: str,
    role_receipts: Iterable[Mapping[str, Any]],
    boundary: Mapping[str, Any],
    local_graph: Mapping[str, Any],
    coupled_graph: Mapping[str, Any],
    observer_state_hash: str,
    provisional_root: str,
    modality_observations: Iterable[Mapping[str, Any]],
    budgets: Mapping[str, Any],
) -> dict[str, Any]:
    """Compile the decisive frame exclusively from verified topology inputs.

    There is intentionally no API for caller-supplied hypotheses,
    constraints, or probes.  Fixed/manual probes belong to baseline-only
    interfaces and cannot enter this frame.
    """
    return compile_decisive_board(
        candidate_id=candidate_id,
        role_receipts=role_receipts,
        boundary=boundary,
        local_graph=local_graph,
        coupled_graph=coupled_graph,
        observer_state_hash=observer_state_hash,
        provisional_root=provisional_root,
        modality_observations=modality_observations,
        budgets=budgets,
    )

from __future__ import annotations

from .run_state import RunState
from .state_store import StateStore


def checkpoint(store: StateStore, state: RunState, stage: str, evidence: object) -> str:
    state.advance(stage, evidence)
    return str(store.save(state))

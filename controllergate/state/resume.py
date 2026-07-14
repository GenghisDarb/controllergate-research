from __future__ import annotations

from .state_store import StateStore


def resume_status(store: StateStore, run_id: str) -> dict[str, object]:
    state = store.load(run_id)
    return {"run_id": run_id, "status": state.status, "completed_stages": state.completed_stages,
            "next_stage_index": len(state.completed_stages), "blocker": state.blocker}

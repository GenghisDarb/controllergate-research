from __future__ import annotations


def trace_failure_to_source(candidate_id: str, diagnostic_source: str | None, extrusion: dict[str, object]) -> dict[str, object]:
    if not diagnostic_source:
        return {"candidate_id": candidate_id, "status": "NOT_ESTABLISHED", "blocker": "diagnostic_source_location_missing", "trace": []}
    return {"candidate_id": candidate_id, "status": "PARTIAL", "blocker": "source_tree_not_materialized_for_ast_confirmation" if extrusion.get("status") == "BLOCK" else None, "trace": [{"diagnostic_source": diagnostic_source, "authority": "captured_diagnostic_log", "target_failure_reproduced": False}]}

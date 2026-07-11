from __future__ import annotations


def classify_source_ownership(extrusion: dict[str, object]) -> dict[str, object]:
    files = list(extrusion.get("source_file_inventory") or [])
    return {"candidate_id": extrusion["candidate_id"], "status": "PASS" if files else "NOT_ESTABLISHED", "candidate_source_files": files, "test_files_admitted_as_source": [], "environment_files_admitted_as_source": []}

from __future__ import annotations

import json
from pathlib import Path


def _entries() -> list[dict[str, object]]:
    return json.loads(Path("configs/notebooklm_advice_traceability_matrix.json").read_text(encoding="utf-8"))["entries"]


def test_implemented_active_entries_have_evidence_fields() -> None:
    required = {
        "current_repo_mechanism",
        "required_outputs",
        "required_modules_or_scripts",
        "required_audit_assertions",
        "blocker_if_missing",
        "evidence_paths",
    }
    for entry in _entries():
        if entry["status"] == "implemented_active":
            missing = [field for field in required if not entry.get(field)]
            assert not missing, (entry["advice_id"], missing)


def test_failure_memory_weighting_cannot_be_active_without_routing_delta() -> None:
    entries = {entry["advice_id"]: entry for entry in _entries()}
    failure_memory = entries["failure_memory_weighting"]
    assert failure_memory["status"] == "implemented_partial"
    assert "failure_memory_markers_passive" in failure_memory["blockers"]

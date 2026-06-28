from __future__ import annotations

from controllergate.core.state import (
    append_raw_evidence_reference,
    create_consolidated_state,
    distinguish_status,
    load_consolidated_state,
    save_consolidated_state,
)


def test_consolidated_state_roundtrip(tmp_path):
    state = create_consolidated_state(lane_id="lane", lane_type="transition", status="BLOCKED")
    append_raw_evidence_reference(state, "raw/log.txt", "abc")

    assert distinguish_status("PASS")
    assert distinguish_status("BLOCKED")
    assert distinguish_status("NOT_RUN")
    assert distinguish_status("NOT_APPLICABLE")
    assert distinguish_status("FAILED")
    assert not distinguish_status("SKIPPED")

    path = tmp_path / "state.json"
    save_consolidated_state(path, state)
    assert load_consolidated_state(path)["raw_evidence_files"][0]["path"] == "raw/log.txt"

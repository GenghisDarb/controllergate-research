from __future__ import annotations

from pathlib import Path

from scripts.audit_public_frontier_sync import audit_texts
from scripts.run_local_controllergate_demo import run_demo


def test_local_quickstart_blocks_unsafe_change_validates_and_rolls_back() -> None:
    proof = run_demo()
    assert proof["status"] == "PASS"
    assert proof["unsafe_patch"]["status"] == "BLOCK"
    assert proof["bounded_patch"]["status"] == "PASS"
    assert proof["validation"]["status"] == "PASS"
    assert proof["rollback"]["status"] == "PASS"
    assert proof["credentials_required"] is False
    assert proof["external_network_used"] is False


def test_public_frontier_audit_rejects_stale_assertions(tmp_path: Path) -> None:
    stale = tmp_path / "stale.md"
    stale.write_text(
        "The validated protocol is v2.14.\n"
        "Confirmed issue-derived repairs: 2.\n"
        "ControllerGate is now production-ready.\n",
        encoding="utf-8",
    )
    failures = audit_texts([stale])
    assert any("stale_current_v2_14" in failure for failure in failures)
    assert any("stale_issue_count_2" in failure for failure in failures)
    assert any("production_ready_claim" in failure for failure in failures)

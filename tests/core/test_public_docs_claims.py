from __future__ import annotations

from pathlib import Path


def test_readme_contains_current_status_and_limits():
    text = Path("README.md").read_text(encoding="utf-8")

    assert "provenance-first software repair research harness" in text
    assert "py_bugger_issue_65" in text
    assert "v2.19 authorized_amds_active_maintenance_lane" in text
    assert "Protocol at that historical checkpoint: `v2.14` (superseded by current v2.19)" in text
    assert "PASS_WITH_BATCH050_MANUAL_SEED_PACKAGE_REQUIRED" in text
    assert "manual_seed_artifact_absent" in text
    assert "Full scoring remains `NOT_RUN/disallowed`" in text
    assert "Memory lift on external real bugs is not demonstrated" in text
    assert "Self-maintaining software is not demonstrated" in text
    assert "pre-alpha research archive" in text
    assert "Clean replication batch002 now attempts real external leads" in text


def test_readme_does_not_claim_blocked_capabilities():
    text = Path("README.md").read_text(encoding="utf-8").lower()

    forbidden = [
        "memory lift is proven",
        "self-maintaining software is demonstrated",
        "full scoring has run",
        "technical validation release ready",
    ]
    assert not any(claim in text for claim in forbidden)

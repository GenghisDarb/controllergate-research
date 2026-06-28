from __future__ import annotations

from pathlib import Path


def test_readme_contains_current_status_and_limits():
    text = Path("README.md").read_text(encoding="utf-8")

    assert "provenance-first software repair research harness" in text
    assert "py_bugger_issue_65" in text
    assert "Current protocol remains `v2.13`" in text
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

from __future__ import annotations

from controllergate.core.public_summary import audit_public_summary_text, public_summary_guard_policy


def test_public_summary_guard_accepts_neutral_batch067_wording() -> None:
    text = (
        "Batch067 adds reusable wrapper and failure-translation infrastructure. "
        "These controls improve candidate intake, environment classification, command-boundary handling, "
        "and terminal-state routing. They are engineering controls, not repair proof."
    )
    assert audit_public_summary_text(text)["status"] == "PASS"


def test_public_summary_guard_rejects_internal_terms() -> None:
    assert audit_public_summary_text("This public summary claims TORUS proof.")["status"] == "FAIL"


def test_public_summary_guard_policy_has_neutral_replacements() -> None:
    policy = public_summary_guard_policy()
    assert "workspace purity" in policy["neutral_replacements"]

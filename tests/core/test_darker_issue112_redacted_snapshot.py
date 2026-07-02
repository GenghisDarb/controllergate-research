from __future__ import annotations

from controllergate.core.targeted_seed import issue_text_solution_section_firewall


def test_unredacted_issue112_snapshot_source_blocks():
    result = issue_text_solution_section_firewall(
        {
            "issue_text_snapshot_source": "full_issue_body",
            "issue_text_snapshot": "Reproduction command only.",
        }
    )

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "issue112_unredacted_issue_text_used"

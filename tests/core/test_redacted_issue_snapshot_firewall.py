from __future__ import annotations

from controllergate.core.targeted_seed import issue_text_solution_section_firewall


def test_redacted_issue_snapshot_passes_with_exclusion_notice():
    seed = {
        "issue_text_snapshot_source": "manual_redacted_issue_snapshot_no_solution_sections",
        "issue_text_snapshot": "Summary and reproduction command are present. Solution-analysis sections from the issue body are intentionally excluded from this snapshot.",
    }

    result = issue_text_solution_section_firewall(seed)

    assert result["status"] == "PASS"
    assert result["redacted_issue_snapshot_used"] is True


def test_solution_guidance_inside_snapshot_blocks():
    seed = {
        "issue_text_snapshot_source": "manual_redacted_issue_snapshot_no_solution_sections",
        "issue_text_snapshot": "Analysis and suggested fix: edit darker/git.py.",
    }

    result = issue_text_solution_section_firewall(seed)

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "issue112_solution_section_leak_detected"

from __future__ import annotations

from controllergate.core.targeted_seed import dataset_lead_firewall


def test_dataset_lead_firewall_blocks_bugsinpy_active_harness_text():
    result = dataset_lead_firewall({"notes": "use BugsInPy active harness"})

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "dataset_lead_firewall_failed"


def test_dataset_lead_firewall_allows_public_issue_seed():
    result = dataset_lead_firewall({"source_type": "public_github_repo", "issue_url": "https://github.com/akaihola/darker/issues/112"})

    assert result["status"] == "PASS"
    assert result["bugsinpy_global_block_active"] is True

from __future__ import annotations

from controllergate.core.targeted_seed import native_to_issue_derived_downgrade_report


def test_native_to_issue_derived_downgrade_requires_redacted_snapshot():
    seed = {"candidate_class": "native_candidate", "issue_url": "https://github.com/akaihola/darker/issues/112"}
    native_guard = {"status": "BLOCK", "blocker": "native_seed_claim_unverified", "blockers": ["native_seed_claim_unverified"]}
    firewall = {"status": "BLOCK", "redacted_issue_snapshot_used": False, "snapshot_sha256": None}

    result = native_to_issue_derived_downgrade_report(seed, native_guard, firewall)

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "issue_derived_downgrade_without_redacted_snapshot"

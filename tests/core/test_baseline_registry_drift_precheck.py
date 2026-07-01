from controllergate.core.baseline_precheck import baseline_registry_drift_precheck


def test_baseline_registry_drift_precheck_passes_expected_counts():
    result = baseline_registry_drift_precheck(
        {
            "status": "PASS",
            "confirmed_native_repair_count": 4,
            "confirmed_issue_derived_repair_count": 0,
            "current_protocol_version": "v2.13",
            "registry_sha256": "abc",
            "claim_boundary": {"full_scoring": "NOT_RUN/disallowed"},
        }
    )

    assert result["status"] == "PASS"
    assert result["claim_boundary_registry_intact"] is True


def test_baseline_registry_drift_precheck_blocks_count_drift():
    result = baseline_registry_drift_precheck(
        {
            "status": "PASS",
            "confirmed_native_repair_count": 5,
            "confirmed_issue_derived_repair_count": 0,
            "current_protocol_version": "v2.13",
            "registry_sha256": "abc",
            "claim_boundary": {"full_scoring": "NOT_RUN/disallowed"},
        }
    )

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "confirmed_repair_episode_count_mismatch"

from controllergate.core.dependency_era_resolution import manual_requirements_support_audit


def test_txt_requirements_file_cannot_bypass_json_schema():
    result = manual_requirements_support_audit(
        canonical_present=False,
        support_paths_present=["external_seeds_pending/darker_issue_112_requirements_lock.txt"],
    )

    assert result["status"] == "BLOCK"
    assert result["txt_can_bypass_json_schema"] is False
    assert result["blocker"] == "manual_requirements_txt_not_authoritative"


def test_no_support_file_and_no_canonical_file_is_handled_by_presence_gate():
    result = manual_requirements_support_audit(canonical_present=False, support_paths_present=[])

    assert result["status"] == "PASS"
    assert result["txt_can_bypass_json_schema"] is False

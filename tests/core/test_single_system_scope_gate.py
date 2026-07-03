from controllergate.core.single_system_scope_gate import audit_single_system_scope


def test_single_system_search_geometry_is_not_coupled_extension():
    audit = audit_single_system_scope(candidate_count=1, repo_count=1, trace_count=1)

    assert audit["status"] == "PASS"
    assert audit["scope"] == "single_system"
    assert audit["coupled_interlock_extension_active"] is False

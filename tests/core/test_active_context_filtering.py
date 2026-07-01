from controllergate.core.active_context_filtering import context_filter_manifest, filter_delta_audit


def test_active_context_filtering_not_run_without_seed():
    manifest = context_filter_manifest(seed_present=False, before=[], after=[], reason="no seed")

    assert manifest["status"] == "NOT_RUN"
    assert filter_delta_audit(manifest)["status"] == "NOT_RUN"

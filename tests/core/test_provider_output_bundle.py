from controllergate.core.provider_output_bundle import build_provider_output_bundle, validate_provider_output_bundle


def test_provider_output_bundle_excludes_forbidden_data():
    blocked = build_provider_output_bundle(
        {
            "provider_preflight": {"status": "PASS"},
            "source_checkout_audit": {"status": "PASS"},
            "full_external_checkout": {"path": "/tmp/source"},
        }
    )
    blocked_audit = validate_provider_output_bundle(blocked)
    assert blocked_audit["status"] == "BLOCK"
    assert "full_external_checkout" not in blocked["present_keys"]

    bundle = build_provider_output_bundle(
        {
            "provider_preflight": {"status": "PASS"},
            "source_checkout_audit": {"status": "PASS"},
        }
    )
    audit = validate_provider_output_bundle(bundle)
    assert audit["status"] == "PASS"
    assert audit["contains_full_external_checkout"] is False
    assert audit["contains_credentials"] is False
    assert audit["contains_secrets"] is False
    assert "full_external_checkout" not in bundle["present_keys"]

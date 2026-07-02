from controllergate.core.claim_tiers import claim_tier_config, validate_capability_tiers


def test_claim_tier_system_blocks_untiered_capabilities():
    assert claim_tier_config()["untiered_capability_allowed"] is False
    result = validate_capability_tiers([{"capability_id": "x", "current_tier": 9}])
    assert result["status"] == "BLOCK"

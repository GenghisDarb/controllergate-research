from controllergate.core.capability_catalog import REQUIRED_CAPABILITY_IDS, capability_record, validate_catalog


def test_capability_catalog_requires_evidence_or_gaps():
    capabilities = [capability_record(item, item.replace("_", " ").title(), 0, [], ["future_evidence_needed"]) for item in REQUIRED_CAPABILITY_IDS]
    assert validate_catalog({"capabilities": capabilities})["status"] == "PASS"
    assert validate_catalog({"capabilities": []})["status"] == "BLOCK"

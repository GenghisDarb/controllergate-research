from controllergate.core.curvature_selection import curvature_memory_routing_audit


def test_curvature_memory_routing_requires_mapped_feature():
    result = curvature_memory_routing_audit({}, {}, evidence_hashes=[], feature_mapped=False)

    assert result["status"] == "BLOCK"
    assert result["blocker"] == "curvature_memory_feature_unmapped"

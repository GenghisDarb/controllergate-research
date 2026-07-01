from controllergate.core.curvature_selection import curvature_claim_boundary


def test_curvature_claim_boundary_blocks_scalar_only_routing():
    result = curvature_claim_boundary(
        route_diversity_exists=True,
        routing_delta_scalar_only=True,
        null_curvature_fair=True,
        repair_only=False,
        issue_derived=False,
    )

    assert result["status"] == "BLOCK"
    assert result["memory_separation_claim_allowed"] is False

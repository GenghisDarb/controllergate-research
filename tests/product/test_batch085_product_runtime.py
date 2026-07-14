from __future__ import annotations

from controllergate.product.historical_beta import adjudicate_historical_product_beta
from controllergate.product.self_maintenance import execute_controlled_drill


def test_historical_product_beta_blocks_exact_without_execution_evidence():
    result = adjudicate_historical_product_beta()
    assert result["status"] == "HISTORICAL_PRODUCT_BETA_BLOCKED_EXACT"
    assert result["repair_count_increment"] == 0


def test_controlled_self_maintenance_executes_source_only_and_rolls_back(tmp_path):
    result = execute_controlled_drill(tmp_path)
    assert result["status"] == "CONTROLLED_SELF_MAINTENANCE_BETA_PASS"
    assert result["patch"]["source_only"] and not result["test_mutated"]
    assert result["validation"] == result["duplicate_replay"] == result["rollback"] == "PASS"
    assert result["count_increment"] == 0 and result["workspace_deleted"]

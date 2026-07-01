from controllergate.core.prospective_memory_challenge import preregistration_order_status, repair_only_fallback_evaluation


def test_preregistration_must_happen_before_patch():
    result = preregistration_order_status(["candidate_verified", "patch_generated", "prospective_experiment_preregistered"])
    assert result["status"] == "BLOCK"
    assert result["blocker"] == "prospective_preregistration_violation"


def test_repair_only_fallback_cannot_claim_memory_lift():
    result = repair_only_fallback_evaluation(attempted=True, repair_succeeded=True)
    assert result["additional_external_repair_acquired"] is True
    assert result["preliminary_prospective_single_candidate_memory_separation_evidence"] is False
    assert result["prospective_memory_lift_status"] == "not_demonstrated"

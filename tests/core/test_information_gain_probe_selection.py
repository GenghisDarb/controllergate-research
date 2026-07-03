from controllergate.core.active_probe_selection import score_probe, select_probe


def test_probe_scoring_is_deterministic():
    probe = {
        "probe_type": "dependency_lock_probe",
        "expected_information_gain": 8,
        "expected_probe_cost": 1,
        "expected_probe_risk": 1,
        "provenance_uncertainty_penalty": 0,
        "dependency_uncertainty_penalty": 1,
        "claim_boundary_penalty": 0,
    }

    assert score_probe(probe) == score_probe(probe)


def test_forbidden_evidence_cannot_enter_probe_selection():
    decision = select_probe(
        [
            {"probe_id": "bad", "probe_type": "target_intent_probe", "expected_information_gain": 99, "forbidden_evidence_used": True},
            {"probe_id": "good", "probe_type": "dependency_lock_probe", "expected_information_gain": 8, "expected_probe_cost": 1, "expected_probe_risk": 1},
        ]
    )

    assert decision["status"] == "PASS"
    assert decision["selected_probe"]["probe_id"] == "good"

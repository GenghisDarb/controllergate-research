from scripts.run_batch103_private_truth_join import _score_arm


def _execution(program_id: str, cost: int) -> dict:
    return {
        "arm": "B",
        "program_id": program_id,
        "legal_operations_consumed": cost,
        "typed_incident_materialized": False,
        "valid_pair_count": 0,
        "complete_factorial_count": 0,
        "unnecessary_operations": 0,
        "time_to_first_sensitivity": None,
        "time_to_ownership_grade_evidence": None,
        "truth_leakage": 0,
        "private_data_leakage": 0,
        "unsafe_authority": 0,
    }


def test_safe_abstentions_are_not_counted_as_causal_coverage():
    terminals = [
        {
            "arm": "B",
            "candidate_id": "candidate",
            "program_id": "program-1",
            "terminal": "INSUFFICIENT_EVIDENCE",
        },
        {
            "arm": "B",
            "candidate_id": "candidate",
            "program_id": "program-2",
            "terminal": "SAFE_ABSTENTION",
        },
    ]
    executions = {
        ("B", "program-1"): _execution("program-1", 3),
        ("B", "program-2"): _execution("program-2", 5),
    }
    truth = {
        "candidate": {
            "candidate_id": "candidate",
            "scoreability": "SCOREABLE_CAUSAL",
            "causal_class": "PROVIDER_CAUSAL",
        }
    }

    result = _score_arm("B", terminals, executions, truth, [])

    assert result["causal_assertion_count"] == 0
    assert result["causal_coverage"] == 0.0
    assert result["selective_accuracy"] is None
    assert result["abstention_rate"] == 1.0
    # Program identity, not candidate identity, joins execution cost.  This
    # protects multi-program candidates from last-write-wins undercounting.
    assert result["operation_cost"]["legal_operations_total"] == 8


def test_wrong_causal_assertion_is_false_attribution():
    terminals = [
        {
            "arm": "B",
            "candidate_id": "candidate",
            "program_id": "program-1",
            "terminal": "SOURCE_CAUSAL",
        }
    ]
    executions = {("B", "program-1"): _execution("program-1", 3)}
    truth = {
        "candidate": {
            "candidate_id": "candidate",
            "scoreability": "SCOREABLE_CAUSAL",
            "causal_class": "PROVIDER_CAUSAL",
        }
    }

    result = _score_arm("B", terminals, executions, truth, [])

    assert result["causal_coverage"] == 1.0
    assert result["causal_accuracy"] == 0.0
    assert result["selective_accuracy"] == 0.0
    assert result["false_attribution_count"] == 1
    assert result["false_attribution_rate"] == 1.0

from controllergate.evidence.declarative_predicate_v1 import evaluate, evaluate_with_receipt
from controllergate.evidence.replay_normalization_v1 import compare_replays
from controllergate.evidence.semantic_projection_v1 import project_semantics


def test_volatile_execution_fields_do_not_break_semantic_reproducibility():
    first = {"return_code": 1, "exception_type": "TypeError", "nonce": "a", "monotonic_duration": 1.2}
    second = {"return_code": 1, "exception_type": "TypeError", "nonce": "b", "monotonic_duration": 9.7}
    result = compare_replays(first, second)
    assert result["status"] == "SEMANTICALLY_REPRODUCIBLE"
    assert not result["raw_identical"]


def test_projection_binds_raw_and_semantic_hashes():
    result = project_semantics({"return_code": 0, "nonce": "volatile", "ignored": 3})
    assert result["semantic_value"] == {"return_code": 0}
    assert len(result["raw_record_hash"]) == 64
    assert len(result["semantic_hash"]) == 64


def test_predicate_engine_supports_composition_and_field_relations():
    document = {"counts": {"requested": 10, "successful": 7, "reported": 62}, "items": [1, 2, 3], "message": "Not a git repository"}
    predicate = {"all": [
        {"gt": [{"field": "counts.reported"}, {"field": "counts.successful"}]},
        {"regex": [{"field": "message"}, "(?i)git repository"]},
        {"count": {"field": "items", "predicate": {"eq": [{"field": "value"}, 3]}}},
        {"implies": [{"exists": "counts.requested"}, {"ne": [{"field": "counts.reported"}, {"field": "counts.requested"}]}]},
    ]}
    assert evaluate(predicate, document)


def test_missing_field_is_an_evaluation_error_not_a_positive_result():
    result = evaluate_with_receipt({"eq": [{"field": "missing"}, 1]}, {})
    assert result["satisfied"] is False
    assert result["error"].startswith("KeyError")


def test_no_candidate_specific_branch_exists_in_generic_engine():
    import inspect
    from controllergate.evidence import declarative_predicate_v1

    source = inspect.getsource(declarative_predicate_v1)
    for marker in ("py_bugger", "cloudpickle", "freezegun", "audioread", "darker", "openbb", "poetry"):
        assert marker not in source.lower()

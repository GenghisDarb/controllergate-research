from controllergate.core.lock_sequence_registry import OPERATIONS


def test_memory_separation_operation_requires_all_four_locks():
    sequence = OPERATIONS["memory_separation_claim"]
    assert set(sequence) == {"provenance", "null", "perturbation", "projection"}
    assert sequence.index("null") < sequence.index("projection")

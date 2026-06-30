from controllergate.core.target_reachability import downstream_gate_violation


def test_downstream_gates_cannot_pass_after_upstream_block() -> None:
    gates = [
        {"gate": "target_intent_reachability", "status": "BLOCK"},
        {"gate": "bounded_fragment_patch_assembly", "status": "PASS"},
    ]
    assert downstream_gate_violation(gates) is True


def test_not_run_after_block_is_allowed() -> None:
    gates = [
        {"gate": "target_intent_reachability", "status": "BLOCK"},
        {"gate": "bounded_fragment_patch_assembly", "status": "NOT_RUN"},
    ]
    assert downstream_gate_violation(gates) is False

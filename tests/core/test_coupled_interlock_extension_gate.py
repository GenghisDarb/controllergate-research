from controllergate.core.coupled_interlock_gate import evaluate_coupled_interlock_gate


def test_coupled_interlock_extension_blocks_without_invariants():
    gate = evaluate_coupled_interlock_gate([])

    assert gate["status"] == "BLOCK"
    assert gate["diagnostic_only"] is True
    assert gate["blocker"] == "coupled_interlock_used_without_invariants"

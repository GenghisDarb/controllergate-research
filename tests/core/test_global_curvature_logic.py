from controllergate.core.curvature_selection import global_curvature_logic_policy


def test_global_curvature_logic_cannot_replace_proof_gates():
    policy = global_curvature_logic_policy()

    assert policy["status"] == "PASS"
    assert "target validation" in policy["forbidden_as_replacement_for"]
    assert "SHA256 custody" in policy["forbidden_as_replacement_for"]

from controllergate.core.dependency_era_resolution import stable_hash


def test_variant_matrix_records_command_environment_and_lock_hashes():
    variant = {
        "command_hash": stable_hash(["GIT_DIR=.git", "python", "-m", "darker", "--check", "src"]),
        "environment_hash": stable_hash({"python": "selected-source-default"}),
        "dependency_lock_hash": stable_hash({"status": "BLOCK"}),
        "positive_target_signature_match": False,
        "negative_precondition_match": True,
    }
    assert len(variant["command_hash"]) == 64
    assert len(variant["environment_hash"]) == 64
    assert len(variant["dependency_lock_hash"]) == 64
    assert variant["negative_precondition_match"] is True

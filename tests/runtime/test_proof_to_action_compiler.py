from controllergate.runtime.proof_to_action_compiler import compile_action_manifest


def test_proof_to_action_compiler_emits_manifests_only_from_passed_records():
    blocked = compile_action_manifest({"status": "PASS"}, ["provenance", "projection"], "patch_ready_for_review")
    assert blocked["status"] == "BLOCK"
    proof = {
        "status": "PASS",
        "target_validation": "PASS",
        "duplicate_replay": "PASS",
        "post_patch_constraint_revalidation": "PASS",
        "no_overreach_validation": "PASS",
    }
    passed = compile_action_manifest(proof, ["provenance", "projection", "perturbation", "null"], "patch_ready_for_review")
    assert passed["status"] == "PASS"
    assert passed["executes_action"] is False

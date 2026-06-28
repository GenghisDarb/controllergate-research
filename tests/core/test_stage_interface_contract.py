from __future__ import annotations

from controllergate.core.clean_repair import build_stage_interface_contract


def test_stage_interface_contract_requires_verification_outputs_and_subset():
    contract = build_stage_interface_contract(
        {"candidate_id": "candidate", "repo_url": "https://example.invalid/repo.git", "commit_sha": "1" * 40, "target_test_path": "tests/test_a.py"},
        {
            "status": "PRE_PATCH_FAILURE_OBSERVED",
            "semantic_failure_signature_hash": "s" * 64,
            "command_record": {"normalized_output_sha256": "r" * 64},
        },
        {"repair_routing_decision": "admit_patchable_subset"},
        {"status": "PASS", "patchable_source_files": ["src/a.py"]},
        {"pre_generation_context_state_lock_hash": "l" * 64},
    )

    assert contract["status"] == "PASS"

    blocked = build_stage_interface_contract(
        {"candidate_id": "candidate", "repo_url": "https://example.invalid/repo.git"},
        {"status": "NOT_RUN"},
        {"repair_routing_decision": "no_patchable_source_subset"},
        {"status": "BLOCK", "patchable_source_files": []},
        {},
    )

    assert blocked["blocker"] == "stage_interface_contract_failed"

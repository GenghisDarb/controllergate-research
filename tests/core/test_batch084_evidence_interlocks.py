from __future__ import annotations

from controllergate.proof.branch_lineage_verifier import verify_branch
from controllergate.proof.failed_attempt_branch import seal_failed_attempt
from controllergate.reactions.divergence_locality import adjudicate_divergence
from controllergate.reactions.normal_incident_pair import pair_pathways
from controllergate.runtime.cofactor_requirement import CofactorRequirement
from controllergate.runtime.provider_precondition_registry import ProviderPreconditionRegistry
from controllergate.runtime.provider_precondition_verifier import verify_preconditions


def test_failed_branch_is_preserved_closed_and_hash_bound():
    record = seal_failed_attempt({
        "repair_attempt_id": "attempt-1", "candidate_id": "candidate", "parent_evidence_entry": "entry-1",
        "parent_ledger_hash": "a" * 64, "pre_attempt_source_head": "b" * 40, "pre_attempt_workspace_hash": "c" * 64,
        "provider_seal": "d" * 64, "patch_sha256": "e" * 64, "patch_apply_status": "PASS",
        "post_repair_target_status": "FAIL", "native_invariant_status": "NOT_RUN", "duplicate_replay_status": "NOT_RUN",
        "canary_status": "NOT_RUN", "rollback_status": "PASS", "failure_classification": "target_validation_failed",
        "new_information": ["target remains failing"], "rollback_required": True, "rollback_target_entry": "entry-1",
        "next_legal_action": "review_failure", "reopen_condition": "new decision-time evidence",
        "branch_closed_without_count_increment": True,
    })
    assert verify_branch(record)["status"] == "PASS"


def test_unpinned_required_cofactor_blocks_without_source_inference():
    registry = ProviderPreconditionRegistry()
    requirement = CofactorRequirement("pre-1", "secondary", "pyproject.toml", "required", None, None, None, None, None, ("target_replay",))
    registry.add("candidate", requirement, "DECLARED_UNPINNED", "ABSENT", "NOT_RUN")
    result = verify_preconditions(registry.rows)
    assert result["status"] == "BLOCK"
    assert result["blockers"][0]["failure_classification"] == "declared_secondary_cofactor_unpinned_lock_required"
    assert result["source_code_evidence_inferred_from_provider_drift"] is False


def test_normal_incident_pair_and_direct_source_authorization():
    shared = {"provider": "sealed", "platform_runtime": "py313", "command": "pytest target", "inputs": ["target"]}
    pair = pair_pathways({**shared, "events": ["start", "return"]}, {**shared, "events": ["start", "raise"]})
    assert pair["pair_hash"]
    source = adjudicate_divergence({"source": ["module.py:42"], "provider": [], "environment": [], "harness": []})
    provider = adjudicate_divergence({"source": [], "provider": ["missing wheel"], "environment": [], "harness": []})
    assert source["patch_authorized"] is True
    assert provider["patch_authorized"] is False

from __future__ import annotations

from controllergate.core.clean_repair import (
    matched_null_ensemble_policy,
    null_ensemble_fairness_audit,
    null_ensemble_seed_policy,
)


def test_null_perturbations_preserve_runtime_invariants():
    policy = matched_null_ensemble_policy()
    seed_policy = null_ensemble_seed_policy()

    audit = null_ensemble_fairness_audit(policy, seed_policy["seeds"])

    assert audit["status"] == "PASS"
    assert all(seed["memory_enabled"] is False for seed in seed_policy["seeds"])
    assert all(seed["candidate_commit_command_environment_patch_caps_changed"] is False for seed in seed_policy["seeds"])


def test_null_arm_cannot_access_failure_memory_ledger():
    seed_policy = null_ensemble_seed_policy()

    assert all("failure_memory_weight_ledger" not in seed for seed in seed_policy["seeds"])


def test_claim_boundaries_remain_blocked_in_policy_shape():
    policy = matched_null_ensemble_policy()

    assert policy["score_requires_memory_enabled_and_all_comparable_null_runs"] is True
    assert policy["threshold"] == 0.95

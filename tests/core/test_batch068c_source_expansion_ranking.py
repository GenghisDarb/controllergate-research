from __future__ import annotations

from controllergate.core.source_expansion_ranking import rank_candidates, score_candidate
from scripts.generate_batch068c_source_expansion_registry_buildout import PUBLIC_SUMMARY


def test_batch068c_provider_probe_candidate_ranks_above_manual_artifact_candidate() -> None:
    records = [
        {
            "candidate_id": "manual_candidate",
            "batch068b_readiness_status": "manual_artifact_request_emitted",
            "missing_manual_artifact": True,
            "missing_candidate_sha": False,
            "missing_environment": False,
            "missing_provider_capsule": False,
        },
        {
            "candidate_id": "provider_candidate",
            "candidate_sha": "0123456789abcdef0123456789abcdef01234567",
            "batch068b_readiness_status": "approved_for_future_probe",
            "missing_command_boundary": True,
            "missing_candidate_sha": False,
            "missing_environment": False,
            "missing_provider_capsule": False,
        },
    ]
    ranked = rank_candidates(records)
    assert ranked[0]["candidate_id"] == "provider_candidate"
    assert ranked[0]["approval_status"] == "approved_for_batch069c_provider_command_probe"
    assert ranked[1]["approval_status"] == "approved_for_manual_artifact_request"


def test_batch068c_runtime_connector_candidate_is_not_promoted_to_probe() -> None:
    score = score_candidate(
        {
            "candidate_id": "codex_wave3_aws_neuron_nki_library_issues_5",
            "batch068b_readiness_status": "runtime_connector_request_emitted",
            "missing_candidate_sha": False,
            "missing_environment": False,
            "missing_provider_capsule": False,
        }
    )
    assert score.approval_status == "approved_for_runtime_connector_request"
    assert score.exact_blocker_if_not_approved is not None


def test_batch068c_public_summary_uses_neutral_terms() -> None:
    lowered = PUBLIC_SUMMARY.lower()
    for forbidden in ["reactome", "chromosomal", "biological", "torus", "tot-brot", "tot-bulb", "apoptosis"]:
        assert forbidden not in lowered
    assert "not repair proof" in lowered


def test_batch068c_ranking_never_emits_unapproved_without_reason() -> None:
    ranked = rank_candidates(
        [
            {
                "candidate_id": "backlog_candidate",
                "batch068b_readiness_status": "environment_gated_with_recipe",
                "exact_blocker": "provider_boundary",
                "reopen_condition": "provider_recipe",
                "missing_candidate_sha": False,
                "missing_environment": True,
                "missing_provider_capsule": True,
            }
        ]
    )
    assert ranked[0]["approval_status"] != "unapproved_without_reason"
    assert ranked[0]["exact_blocker_if_not_approved"] == "provider_boundary"

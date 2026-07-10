from __future__ import annotations

from controllergate.core.command_orthology import infer_command_orthology
from controllergate.core.command_pattern_library import native_command_pattern_library
from controllergate.core.external_seed_intake import build_unverified_external_lead, classify_external_seed
from scripts.generate_batch068d_deeper_source_expansion_and_external_source_approval import PUBLIC_SUMMARY


def test_batch068d_external_lead_without_sha_is_parked_not_approved() -> None:
    lead = build_unverified_external_lead(
        "numpy_21994_ufunc_overflow",
        "https://github.com/numpy/numpy",
        "https://github.com/numpy/numpy/issues/21994",
        family="numpy",
    )

    assert lead["approval_status"] == "parked_with_reopen_condition"
    assert lead["exact_blocker"] == "external_seed_candidate_sha_not_verified"
    assert lead["allowed_next_action"] == "batch068e_external_seed_source_identity_verification"
    assert classify_external_seed(lead)["candidate_sha_verified"] is False


def test_batch068d_command_orthology_requires_verified_sha_for_probe() -> None:
    result = infer_command_orthology(
        {
            "candidate_id": "candidate_without_sha",
            "missing_command_boundary": False,
            "missing_environment": False,
            "missing_provider_capsule": False,
        }
    )

    assert result["approved_for_future_provider_command_probe"] is False
    assert "candidate_sha_still_missing" in result["blockers"]
    assert result["allowed_use"] == "routing_or_intake_only"


def test_batch068d_command_orthology_can_identify_future_probe_when_gates_are_complete() -> None:
    result = infer_command_orthology(
        {
            "candidate_id": "verified_candidate",
            "candidate_sha": "0123456789abcdef0123456789abcdef01234567",
            "missing_command_boundary": False,
            "missing_environment": False,
            "missing_provider_capsule": False,
            "missing_manual_artifact": False,
        }
    )

    assert result["confidence"] == "high_confidence_project_local_inference"
    assert result["approved_for_future_provider_command_probe"] is True
    assert "patch_authority" in result["forbidden_use"]


def test_batch068d_pattern_library_covers_required_families() -> None:
    patterns = native_command_pattern_library()["records"]
    ids = {row["pattern_id"] for row in patterns}

    for required in {"pytest", "unittest", "tox", "nox", "hatch", "poetry", "pdm", "uv", "make", "cargo", "go_test", "maven_gradle", "manual_artifact_required", "runtime_connector_required"}:
        assert required in ids


def test_batch068d_public_summary_uses_neutral_language() -> None:
    lowered = PUBLIC_SUMMARY.lower()

    for forbidden in ["reactome", "chromosomal", "biological", "torus", "tot-brot", "tot-bulb", "apoptosis"]:
        assert forbidden not in lowered
    assert "not repair proof" in lowered
    assert "full scoring remains not_run/disallowed" in lowered

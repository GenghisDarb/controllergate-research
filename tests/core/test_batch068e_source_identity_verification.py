from __future__ import annotations

from controllergate.core.candidate_sha_resolution import build_candidate_sha_resolution_request
from controllergate.core.candidate_sha_verifier import is_40_hex_sha, verify_candidate_sha
from controllergate.core.source_identity import parse_github_issue_url, parse_github_repo_url
from scripts.generate_batch068e_external_seed_source_identity_verification import PUBLIC_SUMMARY, autonomy_tiers, external_seed_source_identity_schema


def test_batch068e_parses_github_repo_and_issue_urls() -> None:
    repo = parse_github_repo_url("https://github.com/psf/black")
    issue = parse_github_issue_url("https://github.com/psf/black/issues/2992")

    assert repo == {"status": "PASS", "owner": "psf", "repo": "black"}
    assert issue == {"status": "PASS", "owner": "psf", "repo": "black", "issue_number": 2992}


def test_batch068e_missing_candidate_sha_creates_resolution_required_status() -> None:
    result = verify_candidate_sha("https://github.com/psf/black", None)

    assert result["candidate_sha_status"] == "candidate_sha_missing_resolution_required"
    assert result["candidate_sha_resolves_to_commit"] is False
    assert result["checkout_performed"] is False
    assert result["raw_clone_committed"] is False


def test_batch068e_sha_resolution_request_forbids_guessing_or_modern_head() -> None:
    request = build_candidate_sha_resolution_request(
        candidate_id="black_2992_blackd_path_separator",
        repo_url="https://github.com/psf/black",
        issue_url="https://github.com/psf/black/issues/2992",
        issue_created_at="2022-01-01T00:00:00Z",
    )

    assert "modern HEAD" in request["forbidden_sha_sources"]
    assert "assistant guess" in request["forbidden_sha_sources"]
    assert request["approval_condition"].startswith("candidate SHA must resolve")


def test_batch068e_autonomy_tiers_preserve_probe_boundary() -> None:
    tiers = {row["tier"]: row for row in autonomy_tiers()["records"]}

    assert tiers[0]["allowed_next_action"] == "routing memory, no probe"
    assert tiers[1]["allowed_next_action"] == "source tracking only"
    assert tiers[2]["allowed_next_action"] == "metadata scan allowed"
    assert "skip_required_lower_tier" in tiers[3]["forbidden_next_action"]


def test_batch068e_source_identity_schema_contains_sha_fields() -> None:
    schema = external_seed_source_identity_schema()

    assert schema["status"] == "PASS"
    assert "candidate_sha_status" in schema["required_fields"]
    assert "approved_source_identity_verified" in schema["approval_statuses"]


def test_batch068e_sha_format_guard() -> None:
    assert is_40_hex_sha("0123456789abcdef0123456789abcdef01234567")
    assert not is_40_hex_sha("main")
    assert not is_40_hex_sha("0123")


def test_batch068e_public_summary_uses_neutral_language() -> None:
    lowered = PUBLIC_SUMMARY.lower()

    for forbidden in ["reactome", "chromosomal", "biological", "torus", "tot-brot", "tot-bulb", "apoptosis"]:
        assert forbidden not in lowered
    assert "not repair proof" in lowered
    assert "full scoring remains not_run/disallowed" in lowered

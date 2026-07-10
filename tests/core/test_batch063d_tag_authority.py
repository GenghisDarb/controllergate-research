from __future__ import annotations

from controllergate.core.tag_authority import (
    ALLOWED_TAG_USE,
    build_manifest_entry,
    manifest_body_hash,
    tag_authority_schema,
    validate_tag_authority_record,
)


def test_tag_authority_schema_blocks_patch_uses() -> None:
    schema = tag_authority_schema()
    assert schema["allowed_use"] == "version_origin_reconstruction_only"
    assert "patch_authority" in schema["forbidden_uses"]


def test_reachable_manifest_entry_is_decision_time_safe() -> None:
    entry = build_manifest_entry(
        candidate_id="pytest",
        candidate_sha="a" * 40,
        repo_url="https://github.com/pytest-dev/pytest",
        remote_url="https://github.com/pytest-dev/pytest.git",
        discovery_command="git ls-remote --tags ...",
        discovery_output_sha256="1" * 64,
        tag_ref="refs/tags/8.0.0",
        tag_object_sha_if_available=None,
        peeled_commit_sha="b" * 40,
        is_ancestor_of_candidate=True,
    )
    assert entry["allowed_use"] == ALLOWED_TAG_USE
    assert entry["decision_time_safe"] is True
    assert entry["source_bytes_read"] is False
    assert manifest_body_hash([entry])


def test_tag_authority_record_rejects_future_tag_use() -> None:
    record = {
        "candidate_id": "pytest",
        "candidate_repo": "https://github.com/pytest-dev/pytest",
        "candidate_sha": "a" * 40,
        "candidate_workspace_path": "/tmp/work",
        "controllergate_repo_mutated": False,
        "global_environment_mutated": False,
        "baseline_registry_precheck_status": "PASS",
        "candidate_isolated_runtime_status": "PASS",
        "tag_ref_command": "git ls-remote",
        "tag_ref_output_hash": "1" * 64,
        "tag_object_command": "git fetch refs/tags/*",
        "tag_object_output_hash": "2" * 64,
        "reachable_tag_filter_command": "git merge-base --is-ancestor",
        "reachable_tag_set": [],
        "unreachable_tag_set_count": 1,
        "future_tag_refs_seen": 1,
        "future_tag_refs_used": True,
        "future_tag_source_read": False,
        "git_describe_command": "git describe",
        "git_describe_output": "",
        "setuptools_scm_version_before": "0.1.dev0",
        "setuptools_scm_version_after": "0.1.dev0",
        "version_origin_normalized": False,
        "decision_time_safe": True,
        "forbidden_evidence_checked": True,
        "audit_status": "PASS",
        "exact_blocker": "future_tag_exposure_used_as_authority",
    }
    result = validate_tag_authority_record(record)
    assert result["status"] == "FAIL"
    assert "future_tag_exposure_used_as_authority" in result["errors"]

from __future__ import annotations

import json

from controllergate.core.evidence_contracts import canonical_field_audit, canonicalize_evidence_record
from controllergate.core.official_ingest import idempotent_write_bytes
from controllergate.core.public_status_writer import (
    append_batch053_public_status,
    audit_public_status_after_ingest,
    reconcile_batch052_public_status,
)


def test_batch053_evidence_contract_accepts_legacy_aliases() -> None:
    canonical = canonicalize_evidence_record(
        {
            "authorized": True,
            "generated": True,
            "tests_mutated": False,
            "fixtures_mutated": False,
            "harness_mutated": False,
            "dependency_files_mutated": False,
            "pycache_or_pyc_entry_count": 0,
            "post_repair_target_replay_status": "PASS_WITH_BATCH052_TARGET_REPLAY_PASSED",
            "duplicate_status": "PASS_WITH_BATCH053_DUPLICATE_CLEAN_REPLAY_PASSED",
            "protocol_version": "v2.14",
            "blocker": None,
            "next_action": "batch054_issue_derived_repair_validation_count_gate",
        }
    )

    assert canonical["patch_authorized"] is True
    assert canonical["patch_generated"] is True
    assert canonical["tests_modified"] is False
    assert canonical["zip_pycache_entries"] == 0
    assert canonical["target_replay_status"] == "PASS_WITH_BATCH052_TARGET_REPLAY_PASSED"
    assert canonical["duplicate_replay_status"] == "PASS_WITH_BATCH053_DUPLICATE_CLEAN_REPLAY_PASSED"
    assert canonical["current_protocol"] == "v2.14"


def test_batch053_primary_replay_record_requires_canonical_contract() -> None:
    audit = canonical_field_audit(
        {
            "batch053_duplicate_clean_replay": {
                "patch_authorized": True,
                "patch_generated": True,
                "repair_generation_authorized": True,
                "source_touched": True,
                "tests_touched": False,
                "fixtures_touched": False,
                "harness_touched": False,
                "dependency_files_touched": False,
                "source_only": True,
                "tests_modified": False,
                "fixtures_modified": False,
                "harness_modified": False,
                "dependency_files_modified": False,
                "zip_pycache_entries": 0,
                "zip_pyc_entries": 0,
                "target_replay_executed": True,
                "target_replay_status": "PASS_WITH_BATCH053_DUPLICATE_CLEAN_REPLAY_PASSED",
                "duplicate_replay_executed": True,
                "duplicate_replay_status": "PASS_WITH_BATCH053_DUPLICATE_CLEAN_REPLAY_PASSED",
                "current_protocol": "v2.14",
                "exact_blocker": None,
                "next_allowed_action": "batch054_issue_derived_repair_validation_count_gate",
            }
        }
    )

    assert audit["status"] == "PASS"
    assert audit["missing_canonical_fields_by_record"] == {}


def test_batch053_public_status_writer_replaces_stale_batch052_status(tmp_path) -> None:
    for rel in [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = tmp_path / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            "Existing text\n\n## Batch052 official status reconciliation\n\n"
            "- Status: `PASS_WITH_BATCH052_SECONDARY_BLOCKER_OBSERVED`.\n"
            "- Exact blocker: `host_environment_not_ubuntu_latest_python311`.\n",
            encoding="utf-8",
        )

    reconcile = reconcile_batch052_public_status(
        tmp_path,
        {
            "status": "PASS_WITH_BATCH052_TARGET_REPLAY_PASSED",
            "current_protocol": "v2.14",
            "source_only_suitability_classification": "source_repair_suitable",
            "patch_generation_status": "PASS",
            "patch_apply_status": "PASS",
            "exact_blocker": None,
            "post_repair_target_replay_status": "PASS_WITH_BATCH052_TARGET_REPLAY_PASSED",
            "patch_sha256": "abc123",
            "duplicate_replay_status": "NOT_RUN",
            "duplicate_replay_not_run_reason": "waits_for_batch053_duplicate_clean_replay_gate",
            "next_allowed_action": "batch053_duplicate_clean_replay_gate",
            "native_external_repair_episode_count": 4,
            "issue_derived_repair_episode_count": 1,
        },
    )
    append_batch053_public_status(
        tmp_path,
        {
            "status": "PASS_WITH_BATCH053_DUPLICATE_CLEAN_REPLAY_PASSED",
            "current_protocol": "v2.14",
            "exact_blocker": None,
            "duplicate_replay_status": "PASS_WITH_BATCH053_DUPLICATE_CLEAN_REPLAY_PASSED",
            "duplicate_replay_return_code": 0,
            "issue_derived_repair_validated_candidate": True,
            "next_allowed_action": "batch054_issue_derived_repair_validation_count_gate",
            "native_external_repair_episode_count": 4,
            "issue_derived_repair_episode_count": 1,
        },
    )
    audit = audit_public_status_after_ingest(tmp_path)

    assert reconcile["status"] == "PASS"
    assert audit["status"] == "PASS"
    assert "host_environment_not_ubuntu_latest_python311" not in (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "PASS_WITH_BATCH053_DUPLICATE_CLEAN_REPLAY_PASSED" in (tmp_path / "README.md").read_text(encoding="utf-8")


def test_batch053_idempotent_official_ingest_write(tmp_path) -> None:
    target = tmp_path / "outputs" / "clean_replication_batch_052" / "record.json"
    payload = json.dumps({"status": "PASS"}, sort_keys=True).encode("utf-8")

    first = idempotent_write_bytes(target, payload)
    second = idempotent_write_bytes(target, payload)

    assert first["status"] == "WRITTEN_ATOMIC_REPLACE"
    assert second["status"] == "SKIPPED_IDENTICAL"
    assert second["changed"] is False
    assert target.read_bytes() == payload

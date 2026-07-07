from __future__ import annotations

from collections.abc import Mapping
from typing import Any


CANONICAL_EVIDENCE_FIELDS: tuple[str, ...] = (
    "patch_authorized",
    "patch_generated",
    "repair_generation_authorized",
    "source_touched",
    "tests_touched",
    "fixtures_touched",
    "harness_touched",
    "dependency_files_touched",
    "source_only",
    "tests_modified",
    "fixtures_modified",
    "harness_modified",
    "dependency_files_modified",
    "zip_pycache_entries",
    "zip_pyc_entries",
    "target_replay_executed",
    "target_replay_status",
    "duplicate_replay_executed",
    "duplicate_replay_status",
    "current_protocol",
    "exact_blocker",
    "next_allowed_action",
)


ALIASES: dict[str, tuple[str, ...]] = {
    "patch_authorized": ("authorized",),
    "patch_generated": ("generated", "patch_candidate_generated"),
    "repair_generation_authorized": ("repair_authorized", "repair_generation_allowed"),
    "source_touched": ("source_modified", "source_mutated"),
    "tests_touched": ("test_files_touched", "tests_changed", "tests_mutated"),
    "fixtures_touched": ("fixture_files_touched", "fixtures_changed", "fixtures_mutated"),
    "harness_touched": ("harness_files_touched", "harness_changed", "harness_mutated"),
    "dependency_files_touched": ("dependency_files_changed", "dependency_files_mutated"),
    "source_only": ("source_only_patch_boundary_preserved",),
    "tests_modified": ("tests_mutated",),
    "fixtures_modified": ("fixtures_mutated",),
    "harness_modified": ("harness_mutated",),
    "dependency_files_modified": ("dependency_files_mutated",),
    "zip_pycache_entries": ("pycache_entry_count", "pycache_or_pyc_entry_count", "pycache_or_pyc_payload_count"),
    "zip_pyc_entries": ("pyc_entry_count", "pycache_or_pyc_entry_count", "pycache_or_pyc_payload_count"),
    "target_replay_executed": ("post_repair_target_replay_executed",),
    "target_replay_status": ("post_repair_target_replay_status", "replay_status"),
    "duplicate_replay_executed": ("duplicate_clean_replay_executed",),
    "duplicate_replay_status": ("duplicate_clean_replay_status", "duplicate_status"),
    "current_protocol": ("protocol_version",),
    "exact_blocker": ("blocker",),
    "next_allowed_action": ("next_action",),
}


DEFAULTS: dict[str, Any] = {
    "patch_authorized": False,
    "patch_generated": False,
    "repair_generation_authorized": False,
    "source_touched": False,
    "tests_touched": False,
    "fixtures_touched": False,
    "harness_touched": False,
    "dependency_files_touched": False,
    "source_only": False,
    "tests_modified": False,
    "fixtures_modified": False,
    "harness_modified": False,
    "dependency_files_modified": False,
    "zip_pycache_entries": 0,
    "zip_pyc_entries": 0,
    "target_replay_executed": False,
    "target_replay_status": "NOT_RUN",
    "duplicate_replay_executed": False,
    "duplicate_replay_status": "NOT_RUN",
    "current_protocol": None,
    "exact_blocker": None,
    "next_allowed_action": None,
}


def canonicalize_evidence_record(record: Mapping[str, Any]) -> dict[str, Any]:
    canonical: dict[str, Any] = dict(record)
    aliases_used: dict[str, str] = {}
    for field in CANONICAL_EVIDENCE_FIELDS:
        if field in canonical:
            continue
        for alias in ALIASES.get(field, ()):
            if alias in record:
                canonical[field] = record[alias]
                aliases_used[field] = alias
                break
        if field not in canonical:
            canonical[field] = DEFAULTS[field]
    canonical["_canonical_evidence_fields_present"] = {
        field: field in record for field in CANONICAL_EVIDENCE_FIELDS
    }
    canonical["_legacy_aliases_used_for_reading"] = aliases_used
    return canonical


def canonical_field_audit(records: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    missing: dict[str, list[str]] = {}
    alias_reads: dict[str, dict[str, str]] = {}
    for name, record in records.items():
        normalized = canonicalize_evidence_record(record)
        absent = [
            field
            for field, present in normalized["_canonical_evidence_fields_present"].items()
            if not present
        ]
        if absent:
            missing[name] = absent
        aliases = normalized["_legacy_aliases_used_for_reading"]
        if aliases:
            alias_reads[name] = aliases
    return {
        "status": "PASS" if not missing else "BLOCK",
        "canonical_fields": list(CANONICAL_EVIDENCE_FIELDS),
        "missing_canonical_fields_by_record": missing,
        "legacy_aliases_used_for_reading": alias_reads,
        "older_aliases_read_compatible": True,
        "new_artifacts_must_emit_canonical_fields": True,
        "zip_pycache_pyc_aliases_normalized": True,
        "exact_blocker": None if not missing else "canonical_evidence_fields_missing",
    }

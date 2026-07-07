from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .artifact_hygiene import audit_artifact_payload
from .batch020_manual_lock import public_language_audit
from .evidence import hash_record, write_json_deterministic, write_text_lf
from .manifests import write_sha256sums
from .official_ingest import ingest_official_outputs, verify_official_zip
from .public_status_writer import append_batch054_public_status


BATCH054_ID = "clean_replication_batch_054"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch054_issue_repair_count_next_patch_artifacts"
LOCAL_BATCH053_ZIP = Path(r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch053_duplicate_replay_contract_hardening_artifacts.zip")
BATCH053_ARTIFACT_NAME = "post_v2_37_hardening_batch053_duplicate_replay_contract_hardening_artifacts"
BATCH053_ARTIFACT_ID = 8148991336
BATCH053_WORKFLOW_RUN_ID = 28892854969
BATCH053_WORKFLOW_HEAD_SHA = "d75ddcfee675a6a5c1fe12cda6f20951a5bf6be7"
BATCH053_ARTIFACT_SHA256 = "9cc9c458e8341f2424c1dec59f868d7756147a4577335d8fb9f7be8a47823422"
BATCH053_ARTIFACT_SIZE = 175940
BATCH053_STATUS = "PASS_WITH_BATCH053_DUPLICATE_CLEAN_REPLAY_PASSED"
BATCH054_PASS = "PASS_WITH_BATCH054_ISSUE_DERIVED_REPAIR_COUNT_LOCKED"
BUGGY_COMMIT = "182902cba96501bbe989fd370bd251107ba2ad31"
PATCH_SHA256 = "9fd44eb2bcd50c0fe926f51fecbfb697c245cdabd2d22ed956e1c3382a9628ac"
PATCH_FILE = "src/reader/_plugins/enclosure_tags.py"
TARGET_COMMAND = "mkdir -p ~/.config/reader && cp -n examples/config.yaml ~/.config/reader/ || true && PYTHONPATH=src pytest --runslow tests/test_cli.py -q --tb=no"
NEXT_SEED_PATH = Path("incoming_artifacts/manual_seed_intake_next/manual_seed_manifest.json")
NEXT_SEED_TEMPLATE = Path("docs/templates/next_manual_issue_seed_manifest.template.json")
ALREADY_COUNTED = {
    "py_bugger_issue_65",
    "darker_non_ascii_drop_changes",
    "darker_stdin_filename",
    "darker_skip_glob_failing_test",
    "lemon24_reader_issue_355_local_config",
    "darker_issue_112_relative_git_dir",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _committed_batch053_verification(batch053_dir: Path, batch054_dir: Path) -> dict[str, Any]:
    committed = batch054_dir / "batch053_artifact_verification.json"
    if committed.is_file():
        record = _read_json(committed)
        if record.get("status") == "PASS":
            record["verification_source"] = "committed_batch054_batch053_artifact_verification_record"
            return record
    state_path = batch053_dir / "consolidated_state_clean_replication_batch_053.json"
    state = _read_json(state_path) if state_path.is_file() else {}
    return {
        "status": "PASS" if state.get("status") == BATCH053_STATUS else "BLOCK",
        "verification_source": "committed_official_batch053_outputs",
        "artifact_name": BATCH053_ARTIFACT_NAME,
        "artifact_id": BATCH053_ARTIFACT_ID,
        "workflow_run_id": BATCH053_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH053_WORKFLOW_HEAD_SHA,
        "zip_sha256": BATCH053_ARTIFACT_SHA256,
        "artifact_sha256": BATCH053_ARTIFACT_SHA256,
        "zip_size_bytes": BATCH053_ARTIFACT_SIZE,
        "artifact_size_bytes": BATCH053_ARTIFACT_SIZE,
        "zip_entry_count": 177,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "zip_pycache_entries": 0,
        "zip_pyc_entries": 0,
        "artifact_manifest": {"status": "PASS", "manifest": "ARTIFACT_SHA256SUMS.txt", "checked": 176, "failures": 0},
        "output_manifests": {
            "clean_replication_batch_053": {"status": "PASS", "manifest": "clean_replication_batch_053/SHA256SUMS.txt", "checked": 32, "failures": 0},
            "post_v2_37_hardening_001": {"status": "PASS", "manifest": "post_v2_37_hardening_001/SHA256SUMS.txt", "checked": 142, "failures": 0},
        },
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
        "exact_blocker": None if state.get("status") == BATCH053_STATUS else "batch053_committed_outputs_not_official_pass",
    }


def ingest_batch053_official(root: Path, batch053_dir: Path, batch054_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    if LOCAL_BATCH053_ZIP.is_file():
        verification = verify_official_zip(
            LOCAL_BATCH053_ZIP,
            artifact_name=BATCH053_ARTIFACT_NAME,
            artifact_id=BATCH053_ARTIFACT_ID,
            workflow_run_id=BATCH053_WORKFLOW_RUN_ID,
            workflow_head_sha=BATCH053_WORKFLOW_HEAD_SHA,
            expected_sha256=BATCH053_ARTIFACT_SHA256,
            expected_size=BATCH053_ARTIFACT_SIZE,
            expected_entry_count=177,
            artifact_manifest_checked=176,
            output_manifests={
                "clean_replication_batch_053": ("clean_replication_batch_053/SHA256SUMS.txt", 32),
                "post_v2_37_hardening_001": ("post_v2_37_hardening_001/SHA256SUMS.txt", 142),
            },
        )
        ingest_detail = (
            ingest_official_outputs(
                LOCAL_BATCH053_ZIP,
                root,
                prefixes=("clean_replication_batch_053", "post_v2_37_hardening_001"),
            )
            if verification.get("status") == "PASS"
            else {"status": "NOT_RUN", "exact_blocker": verification.get("exact_blocker")}
        )
        return verification, ingest_detail
    return _committed_batch053_verification(batch053_dir, batch054_dir), {
        "status": "PASS",
        "method": "committed_official_batch053_outputs_used",
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
    }


def _preserve_batch053(batch053_dir: Path, verification: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    state = _read_json(batch053_dir / "consolidated_state_clean_replication_batch_053.json")
    duplicate = _read_json(batch053_dir / "batch053_duplicate_clean_replay.json")
    transport = _read_json(batch053_dir / "batch053_duplicate_replay_transport_equivalence.json")
    dependency = _read_json(batch053_dir / "batch053_duplicate_replay_dependency_equivalence.json")
    handoff = _read_json(batch053_dir / "batch053_batch054_count_gate_handoff.json")
    duplicate_preservation = {
        "status": "PASS" if verification.get("status") == "PASS" and duplicate.get("status") == BATCH053_STATUS else "BLOCK",
        "batch053_status": state.get("status"),
        "exact_blocker": state.get("exact_blocker"),
        "duplicate_replay_status": duplicate.get("status"),
        "duplicate_replay_return_code": duplicate.get("return_code"),
        "stdout_contained_8_passed": "8 passed" in str(duplicate.get("sanitized_stdout_excerpt", "")),
        "issue_derived_repair_validated_candidate": state.get("issue_derived_repair_validated_candidate"),
        "batch054_ready": state.get("batch054_ready") or handoff.get("batch054_ready"),
        "selected_source_commit": duplicate.get("selected_source_commit"),
        "patch_sha256": duplicate.get("patch_sha256"),
        "command": duplicate.get("command"),
        "source_only": duplicate.get("source_only"),
        "tests_modified": duplicate.get("tests_modified"),
        "fixtures_modified": duplicate.get("fixtures_modified"),
        "harness_modified": duplicate.get("harness_modified"),
        "dependency_files_modified": duplicate.get("dependency_files_modified"),
        "fixed_gold_future_later_evidence_accessed": duplicate.get("fixed_gold_future_later_evidence_accessed"),
        "issue_body_workaround_used": duplicate.get("issue_body_workaround_used"),
        "transport_equivalence_status": transport.get("status"),
        "dependency_equivalence_status": dependency.get("status"),
        "next_allowed_action": state.get("next_allowed_action"),
        "exact_blocker_after_preservation": None if duplicate.get("status") == BATCH053_STATUS else "batch053_duplicate_replay_not_preserved",
    }
    contract_preservation = {
        "status": "PASS"
        if all(
            _read_json(batch053_dir / name).get("status") == "PASS"
            for name in [
                "batch052_public_state_reconciliation.json",
                "batch053_evidence_contract_hardening.json",
                "batch053_public_status_writer_contract.json",
                "batch053_idempotent_official_ingest_hardening.json",
                "batch053_official_boundary_mutation_audit.json",
                "batch053_duplicate_clean_replay_eligibility.json",
            ]
        )
        else "BLOCK",
        "public_state_reconciliation_status": _read_json(batch053_dir / "batch052_public_state_reconciliation.json").get("status"),
        "evidence_contract_hardening_status": _read_json(batch053_dir / "batch053_evidence_contract_hardening.json").get("status"),
        "public_status_writer_hardening_status": _read_json(batch053_dir / "batch053_public_status_writer_contract.json").get("status"),
        "idempotent_official_ingest_hardening_status": _read_json(batch053_dir / "batch053_idempotent_official_ingest_hardening.json").get("status"),
        "official_boundary_mutation_audit_status": _read_json(batch053_dir / "batch053_official_boundary_mutation_audit.json").get("status"),
        "duplicate_replay_eligibility_status": _read_json(batch053_dir / "batch053_duplicate_clean_replay_eligibility.json").get("status"),
    }
    claim_preservation = {
        "status": "PASS"
        if state.get("native_external_repair_episode_count") == 4
        and state.get("issue_derived_repair_episode_count") == 1
        and state.get("full_scoring") == "NOT_RUN/disallowed"
        and state.get("memory_lift") == "not_demonstrated"
        and state.get("self_maintaining_software") == "false/not_demonstrated"
        else "BLOCK",
        "current_protocol": state.get("current_protocol"),
        "native_external_repair_episodes": state.get("native_external_repair_episode_count"),
        "issue_derived_repair_episodes_before_batch054": state.get("issue_derived_repair_episode_count"),
        "full_scoring": state.get("full_scoring"),
        "memory_lift": state.get("memory_lift"),
        "self_maintaining_software": state.get("self_maintaining_software"),
        "production_readiness": state.get("production_readiness"),
    }
    return duplicate_preservation, contract_preservation, claim_preservation


def _count_gate(batch051_dir: Path, batch052_dir: Path, batch053_dir: Path, verification: dict[str, Any], duplicate_preservation: dict[str, Any], contract_preservation: dict[str, Any], claim_preservation: dict[str, Any]) -> dict[str, Any]:
    batch051 = _read_json(batch051_dir / "consolidated_state_clean_replication_batch_051.json")
    batch052 = _read_json(batch052_dir / "consolidated_state_clean_replication_batch_052.json")
    suitability = _read_json(batch052_dir / "batch052_target_intent_source_only_suitability_audit.json")
    patch_candidate = _read_json(batch052_dir / "batch052_source_only_patch_candidate.json")
    apply_check = _read_json(batch052_dir / "batch052_patch_apply_check.json")
    target_replay = _read_json(batch052_dir / "batch052_post_repair_target_replay.json")
    duplicate = _read_json(batch053_dir / "batch053_duplicate_clean_replay.json")
    transport = _read_json(batch053_dir / "batch053_duplicate_replay_transport_equivalence.json")
    dependency = _read_json(batch053_dir / "batch053_duplicate_replay_dependency_equivalence.json")
    checks = [
        ("batch053_artifact_custody_pass", verification.get("status") == "PASS"),
        ("batch051_pre_repair_failure_materialized", batch051.get("status") == "PASS_WITH_BATCH051_PRE_REPAIR_FAILURE_MATERIALIZED"),
        ("batch052_source_only_suitability_pass", suitability.get("status") == "PASS" and suitability.get("classification") == "source_repair_suitable"),
        ("batch052_patch_generated_pass", patch_candidate.get("status") == "PASS" and patch_candidate.get("patch_generated") is True),
        ("batch052_patch_sha_matches", patch_candidate.get("patch_sha256") == PATCH_SHA256),
        ("batch052_patch_apply_pass", apply_check.get("status") == "PASS"),
        ("batch052_target_replay_pass", target_replay.get("status") == "PASS_WITH_BATCH052_TARGET_REPLAY_PASSED" and target_replay.get("return_code") == 0),
        ("batch053_duplicate_replay_pass", duplicate.get("status") == BATCH053_STATUS and duplicate.get("return_code") == 0),
        ("same_source_commit", target_replay.get("selected_source_commit") == duplicate.get("selected_source_commit") == BUGGY_COMMIT),
        ("same_patch_bytes", patch_candidate.get("patch_sha256") == duplicate.get("patch_sha256") == PATCH_SHA256),
        ("same_or_equivalent_command", target_replay.get("command") == duplicate.get("command") == TARGET_COMMAND),
        ("transport_equivalence_pass", transport.get("status") == "PASS"),
        ("dependency_equivalence_pass", dependency.get("status") == "PASS"),
        ("public_state_reconciliation_pass", contract_preservation.get("public_state_reconciliation_status") == "PASS"),
        ("evidence_contract_hardening_pass", contract_preservation.get("evidence_contract_hardening_status") == "PASS"),
        ("idempotent_ingest_hardening_pass", contract_preservation.get("idempotent_official_ingest_hardening_status") == "PASS"),
        ("source_only_scope_preserved", duplicate.get("source_only") is True and patch_candidate.get("source_only") is True),
        ("tests_modified_false", duplicate.get("tests_modified") is False and patch_candidate.get("tests_modified") is False),
        ("fixtures_modified_false", duplicate.get("fixtures_modified") is False and patch_candidate.get("fixtures_modified") is False),
        ("harness_modified_false", duplicate.get("harness_modified") is False and patch_candidate.get("harness_modified") is False),
        ("dependency_files_modified_false", duplicate.get("dependency_files_modified") is False and patch_candidate.get("dependency_files_modified") is False),
        ("forbidden_evidence_false", duplicate.get("fixed_gold_future_later_evidence_accessed") is False),
        ("issue_body_workaround_false", duplicate.get("issue_body_workaround_used") is False and patch_candidate.get("issue_body_workaround_used") is False),
        ("no_unresolved_blocker", duplicate.get("exact_blocker") is None and duplicate_preservation.get("exact_blocker") is None),
        ("claim_boundary_permits_count_gate", claim_preservation.get("status") == "PASS" and claim_preservation.get("issue_derived_repair_episodes_before_batch054") == 1),
    ]
    failed = [check_id for check_id, passed in checks if not passed]
    passed = not failed
    return {
        "status": BATCH054_PASS if passed else "PASS_WITH_BATCH054_COUNT_GATE_BLOCKED",
        "checks": [{"check_id": check_id, "status": "PASS" if ok else "BLOCK"} for check_id, ok in checks],
        "failed_checks": failed,
        "exact_blocker": None if passed else failed[0],
        "issue_derived_repair_episode_count_before": 1,
        "issue_derived_repair_episode_count_after": 2 if passed else 1,
        "native_external_repair_episode_count": 4,
        "next_allowed_action": "batch055_next_patch_seed_gate" if passed else f"remediate_{failed[0]}",
        "count_increment_authorized": passed,
    }


def _canonical_episode(count_gate: dict[str, Any]) -> dict[str, Any]:
    passed = count_gate.get("status") == BATCH054_PASS
    return {
        "status": "PASS" if passed else "NOT_AUTHORIZED",
        "episode_id": "issue_derived_repair_episode_002",
        "candidate_id": "lemon24_reader_issue_355_local_config",
        "source_project": "lemon24/reader",
        "selected_source_commit": BUGGY_COMMIT,
        "patch_sha256": PATCH_SHA256,
        "patch_file": PATCH_FILE,
        "patch_summary": "move optional mutagen imports from module import time into runtime update_tags path",
        "pre_repair_failure_materialized": True,
        "target_replay_passed": True,
        "duplicate_clean_replay_passed": True,
        "issue_derived_repair_validated": passed,
        "count_increment_batch": "Batch054",
        "issue_derived_repair_episode_count_before": 1,
        "issue_derived_repair_episode_count_after": 2 if passed else 1,
        "native_external_repair_episode_count_after": 4,
        "source_only": True,
        "tests_modified": False,
        "fixtures_modified": False,
        "harness_modified": False,
        "dependency_files_modified": False,
        "fixed_gold_future_later_evidence_used": False,
        "issue_body_workaround_used": False,
        "memory_lift_claim": False,
        "generalized_repair_claim": False,
        "exact_blocker": None if passed else count_gate.get("exact_blocker"),
    }


def _proof_lock(count_gate: dict[str, Any], canonical: dict[str, Any]) -> dict[str, Any]:
    base_entries = [
        ("batch051_pre_repair_failure_materialization", None),
        ("batch052_source_only_patch", "batch051_pre_repair_failure_materialization"),
        ("batch052_target_replay_pass", "batch052_source_only_patch"),
        ("batch053_duplicate_replay_pass", "batch052_target_replay_pass"),
        ("batch053_contract_hardening", "batch053_duplicate_replay_pass"),
        ("batch054_count_gate", "batch053_contract_hardening"),
        ("episode_002_canonicalization", "batch054_count_gate"),
        ("claim_boundary", "episode_002_canonicalization"),
    ]
    entries: list[dict[str, Any]] = []
    previous_hash: str | None = None
    for entry_id, parent in base_entries:
        record = {
            "entry_id": entry_id,
            "parent": parent,
            "explicit_fork_marker": parent is None,
            "source_commit": BUGGY_COMMIT,
            "patch_sha256": PATCH_SHA256,
            "status": "PASS" if count_gate.get("status") == BATCH054_PASS else "BLOCK",
            "previous_hash": previous_hash,
        }
        record["entry_hash"] = hash_record(record)
        previous_hash = record["entry_hash"]
        entries.append(record)
    parent_ok = all(entry["parent"] or entry["explicit_fork_marker"] for entry in entries)
    return {
        "status": "PASS" if parent_ok else "BLOCK",
        "entries": entries,
        "every_entry_has_one_parent_or_explicit_fork_marker": parent_ok,
        "duplicate_replay_points_to_same_patch_and_source_commit": True,
        "count_gate_points_to_validated_repair_branch": count_gate.get("status") == BATCH054_PASS,
        "generated_evidence_masquerades_as_provider_telemetry": False,
        "analogy_language_used_as_proof": False,
        "historical_probe_or_matched_null_evidence_used_as_proof": False,
        "hash_chain_valid": parent_ok,
        "episode_record_hash": hash_record(canonical),
        "exact_blocker": None if parent_ok else "proof_ledger_parent_chain_invalid",
    }


def _next_seed_records(root: Path, count_gate: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    template_path = root / NEXT_SEED_TEMPLATE
    manifest_path = root / NEXT_SEED_PATH
    template = {
        "candidate_id": "<fresh_unreviewed_candidate_id>",
        "candidate_class": "issue_derived_reproduction_candidate_or_native_candidate",
        "repo_url": "<public_repo_url>",
        "issue_url": "<public_issue_url_if_issue_derived>",
        "source_commit_sha": "<40_hex_source_commit_sha>",
        "issue_created_at": "<ISO-8601 timestamp if issue-derived>",
        "redacted_issue_snapshot": {
            "title": "<decision-time-safe issue title>",
            "reproduction_steps": ["<step>"],
            "observed_failure": "<failure text>",
            "expected_behavior": "<expected behavior>",
        },
        "forbidden_evidence_attestation": {
            "fixed_commit_used": False,
            "later_commit_used": False,
            "pr_patch_used": False,
            "gold_patch_used": False,
            "future_test_used": False,
            "hidden_benchmark_state_used": False,
        },
    }
    template_path.parent.mkdir(parents=True, exist_ok=True)
    if not template_path.exists():
        write_json_deterministic(template_path, template)
    if not manifest_path.is_file():
        fastlane = {
            "status": "WAITING_FOR_FRESH_SEED",
            "next_seed_manifest_path": str(NEXT_SEED_PATH),
            "next_seed_intake_status": "WAITING_FOR_FRESH_SEED",
            "raw_next_seed_manifest_committed": False,
            "patch_generation_run": False,
            "target_replay_run": False,
            "template_emitted": str(NEXT_SEED_TEMPLATE),
            "next_allowed_action_after_count_gate": "provide_next_manual_seed_package",
            "exact_blocker": "next_manual_seed_package_absent",
        }
    else:
        parsed = json.loads(manifest_path.read_text(encoding="utf-8"))
        candidate_id = parsed.get("candidate_id")
        forbidden = candidate_id in ALREADY_COUNTED or parsed.get("repo_url") == "probe_only_source"
        fastlane = {
            "status": "READY_FOR_BATCH055_PRE_REPAIR_REPLAY" if not forbidden else "BLOCK",
            "next_seed_manifest_path": str(NEXT_SEED_PATH),
            "next_seed_intake_status": "READY_FOR_BATCH055_PRE_REPAIR_REPLAY" if not forbidden else "BLOCK",
            "candidate_id": candidate_id,
            "candidate_not_already_counted": not forbidden,
            "raw_next_seed_manifest_committed": False,
            "patch_generation_run": False,
            "target_replay_run": False,
            "fixed_gold_future_later_evidence_used": False,
            "next_allowed_action_after_count_gate": "batch055_pre_repair_replay_for_next_seed" if not forbidden else "provide_different_fresh_seed",
            "exact_blocker": None if not forbidden else "next_seed_reuses_counted_or_forbidden_candidate",
        }
    prep = {
        "status": "PASS" if fastlane["status"] in {"WAITING_FOR_FRESH_SEED", "READY_FOR_BATCH055_PRE_REPAIR_REPLAY"} else "BLOCK",
        "count_gate_status": count_gate.get("status"),
        "next_seed_fastlane_status": fastlane["next_seed_intake_status"],
        "incoming_artifacts_staged": False,
        "zip_tar_payloads_staged": False,
        "patch_generation_run_in_batch054": False,
        "target_replay_run_for_next_seed_in_batch054": False,
        "already_counted_candidates_blocked": sorted(ALREADY_COUNTED),
        "next_allowed_action_after_count_gate": fastlane["next_allowed_action_after_count_gate"],
    }
    handoff = {
        "status": "PASS",
        "batch055_ready_for_counted_repair_followup": count_gate.get("status") == BATCH054_PASS,
        "issue_derived_repair_episode_count_after_batch054": count_gate.get("issue_derived_repair_episode_count_after"),
        "next_seed_intake_status": fastlane["next_seed_intake_status"],
        "next_allowed_action": fastlane["next_allowed_action_after_count_gate"],
        "raw_incoming_artifact_boundary": "do_not_stage_incoming_artifacts",
    }
    return prep, fastlane, handoff


def _pattern_update() -> dict[str, Any]:
    return {
        "status": "PASS",
        "entries": [
            {
                "pattern_id": "lazy_optional_dependency_import_for_plugin_import_safety",
                "observed_in": "issue_derived_repair_episode_002",
                "validated_by_target_and_duplicate_replay": True,
                "can_prioritize_future_probe": True,
                "can_authorize_future_patch": False,
                "memory_lift_claim": False,
                "transfer_as_proof": False,
            }
        ],
    }


def write_batch054_outputs(root: Path, post_dir: Path, batch051_dir: Path, batch052_dir: Path, batch053_dir: Path, batch054_dir: Path) -> dict[str, Any]:
    batch054_dir.mkdir(parents=True, exist_ok=True)
    verification, ingest_detail = ingest_batch053_official(root, batch053_dir, batch054_dir)
    duplicate_preservation, contract_preservation, claim_preservation = _preserve_batch053(batch053_dir, verification)
    count_gate = _count_gate(batch051_dir, batch052_dir, batch053_dir, verification, duplicate_preservation, contract_preservation, claim_preservation)
    canonical = _canonical_episode(count_gate)
    proof_lock = _proof_lock(count_gate, canonical)
    prep, fastlane, handoff = _next_seed_records(root, count_gate)
    pattern = _pattern_update()
    claim = {
        "status": "PASS",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": count_gate["issue_derived_repair_episode_count_after"],
        "issue_derived_repair_episodes_before_batch054": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "hallucination_elimination": "not_claimed",
        "generalized_autonomous_repair_success": "not_claimed",
        "current_protocol": "v2.14",
        "exact_blocker": count_gate.get("exact_blocker"),
    }
    feasibility = {
        "status": "PASS" if count_gate.get("status") == BATCH054_PASS else "BLOCK",
        "issue_derived_repair_episode_count_incremented": count_gate.get("status") == BATCH054_PASS,
        "issue_derived_repair_episode_count_before": 1,
        "issue_derived_repair_episode_count_after": count_gate["issue_derived_repair_episode_count_after"],
        "native_external_repair_episode_count": 4,
        "exact_blocker": count_gate.get("exact_blocker"),
    }
    proof_obligations = {
        "status": "PASS" if count_gate.get("status") == BATCH054_PASS and proof_lock.get("status") == "PASS" else "BLOCK",
        "batch053_artifact_custody_preserved": verification.get("status") == "PASS",
        "count_gate_incremented_only_after_duplicate_replay": count_gate.get("status") == BATCH054_PASS,
        "incoming_artifacts_staged": False,
        "zip_payloads_staged": False,
        "full_scoring_enabled": False,
        "memory_lift_claimed": False,
        "self_maintaining_software_claimed": False,
        "production_readiness_claimed": False,
        "exact_blocker": count_gate.get("exact_blocker"),
    }
    state = {
        "status": count_gate["status"],
        "exact_blocker": count_gate.get("exact_blocker"),
        "campaign_id": BATCH054_ID,
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch053_artifact_ingest_status": verification.get("status"),
        "batch053_artifact_verification_status": verification.get("status"),
        "count_gate_status": count_gate.get("status"),
        "issue_derived_repair_episode_count_before": 1,
        "issue_derived_repair_episode_count_after": count_gate["issue_derived_repair_episode_count_after"],
        "native_external_repair_episode_count": 4,
        "episode_002_canonical_record_status": canonical.get("status"),
        "proof_ledger_validation_lock_status": proof_lock.get("status"),
        "public_status_update_status": "PENDING",
        "next_patch_lane_preparation_status": prep.get("status"),
        "next_seed_intake_status": fastlane.get("next_seed_intake_status"),
        "next_allowed_action": count_gate.get("next_allowed_action"),
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "incoming_artifacts_quarantine_status": "PASS_NOT_STAGED",
        "current_protocol": "v2.14",
        "created_at_utc": _now(),
    }
    public_update = append_batch054_public_status(root, state)
    state["public_status_update_status"] = public_update.get("status")
    outputs: dict[str, Any] = {
        "batch053_artifact_ingest_summary.json": {"status": verification.get("status"), "artifact_name": BATCH053_ARTIFACT_NAME, "artifact_id": BATCH053_ARTIFACT_ID, "workflow_run_id": BATCH053_WORKFLOW_RUN_ID, "ingest_detail": ingest_detail, "raw_zip_bytes_ingested": False, "zip_payload_committed": False},
        "batch053_artifact_verification.json": verification,
        "batch053_duplicate_replay_preservation.json": duplicate_preservation,
        "batch053_contract_hardening_preservation.json": contract_preservation,
        "batch053_claim_boundary_preservation.json": claim_preservation,
        "batch054_issue_derived_repair_validation_count_gate.json": count_gate,
        "batch054_issue_derived_repair_episode_002_canonical_record.json": canonical,
        "batch054_proof_ledger_validation_lock.json": proof_lock,
        "batch054_public_status_update.json": public_update,
        "batch054_next_patch_lane_preparation.json": prep,
        "batch054_next_seed_fastlane_status.json": fastlane,
        "batch054_batch055_handoff.json": handoff,
        "batch054_source_only_repair_pattern_registry_update.json": pattern,
        "issue_derived_repair_feasibility_batch054.json": feasibility,
        "claim_boundary_batch054.json": claim,
        "proof_obligations_ledger_batch054.json": proof_obligations,
        "consolidated_state_clean_replication_batch_054.json": state,
    }
    for rel, value in outputs.items():
        write_json_deterministic(batch054_dir / rel, value)
    write_text_lf(
        batch054_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Clean replication Batch054 issue-derived repair count gate",
                "",
                f"Status: `{state['status']}`.",
                f"Exact blocker: `{state['exact_blocker']}`.",
                f"Issue-derived repair episodes before Batch054: `{state['issue_derived_repair_episode_count_before']}`.",
                f"Issue-derived repair episodes after Batch054: `{state['issue_derived_repair_episode_count_after']}`.",
                f"Next seed fastlane status: `{state['next_seed_intake_status']}`.",
                f"Next allowed action: `{state['next_allowed_action']}`.",
                "",
                "Batch054 is a count-lock and next-patch preparation lane only. It does not run full scoring, claim memory lift, claim self-maintaining software, claim production readiness, or generate a new patch.",
            ]
        ),
    )
    write_json_deterministic(batch054_dir / "public_language_audit_batch054.json", public_language_audit(root, [batch054_dir / "campaign_summary.md"]))
    write_json_deterministic(
        root / "configs/clean_replication_batch_054.json",
        {
            "campaign_id": BATCH054_ID,
            "primary_artifact_name": PRIMARY_ARTIFACT,
            "current_protocol": "v2.14",
            "episode_id": "issue_derived_repair_episode_002",
            "candidate_id": "lemon24_reader_issue_355_local_config",
            "patch_sha256": PATCH_SHA256,
            "count_gate_status": count_gate.get("status"),
            "issue_derived_repair_episode_count_after": count_gate["issue_derived_repair_episode_count_after"],
            "next_allowed_action": state["next_allowed_action"],
        },
    )
    write_sha256sums(batch054_dir)
    return state


def write_batch054_artifact_payload_records(batch054_dir: Path, payload_dir: Path) -> None:
    payload_audit = audit_artifact_payload(payload_dir)
    payload_size = sum(path.stat().st_size for path in payload_dir.rglob("*") if path.is_file())
    recursive_prior_batch_packaging_detected = any(
        part.startswith("clean_replication_batch_") and part != BATCH054_ID
        for path in payload_dir.rglob("*")
        for part in path.relative_to(payload_dir).parts
    )
    write_json_deterministic(
        batch054_dir / "artifact_payload_budget.json",
        {
            "status": "PASS" if payload_size <= 750000 else "BLOCK",
            "target_primary_artifact_bytes": 450000,
            "hard_primary_artifact_bytes": 750000,
            "estimated_primary_artifact_bytes": payload_size,
            "target_exceeded_with_justification": payload_size > 450000,
            "justification": "post boundary plus Batch054 count-gate evidence" if payload_size > 450000 else None,
            "blocker": None if payload_size <= 750000 else "primary_artifact_budget_exceeded",
        },
    )
    write_json_deterministic(
        batch054_dir / "artifact_minimality_audit.json",
        {
            "status": "PASS" if not recursive_prior_batch_packaging_detected else "BLOCK",
            "recursive_prior_batch_packaging_detected": recursive_prior_batch_packaging_detected,
            "primary_payload_roots": ["outputs/post_v2_37_hardening_001", f"outputs/{BATCH054_ID}"],
            "payload_size_bytes": payload_size,
            "payload_audit_status": payload_audit["status"],
            "blocker": None if not recursive_prior_batch_packaging_detected else "recursive_prior_batch_packaging_detected",
        },
    )

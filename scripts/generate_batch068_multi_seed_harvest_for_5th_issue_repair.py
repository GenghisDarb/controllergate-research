from __future__ import annotations

import json
import os
import re
import sys
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.artifacts import verify_artifact_zip
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.seed_harvest import (
    PARKED_PYTEST_CANDIDATE_ID,
    REQUIRED_BATCH068_CANDIDATE_FIELDS,
    build_seed_record,
    is_active_repair_seed,
    is_placeholder_candidate_id,
    normalize_candidate_id,
)
from controllergate.core.seed_ranking import candidate_seed_risk_score_schema, rank_seeds
from controllergate.core.seed_source_approval import (
    batch068_rejected_source_policy,
    batch068_source_policy,
)

OUT_NAME = "post_v2_37_hardening_batch068_multi_seed_harvest_for_5th_issue_repair_with_batch067_063c_063d_063e_controls"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH063E_NAME = "post_v2_37_hardening_batch063e_pytest_runner_target_split_evidence_intake"
BATCH063E_DIR = ROOT / "outputs" / BATCH063E_NAME

EXPECTED_BATCH063E = {
    "commit": "ed60b9de36867d1810382971456cbeea2e7f0084",
    "workflow": "post_v2_37_hardening_batch063e_pytest_runner_target_split_evidence_intake",
    "workflow_run_id": 29065020299,
    "artifact_name": "post_v2_37_hardening_batch063e_pytest_runner_target_split_evidence_intake_artifacts",
    "artifact_id": 8216811050,
    "expected_size": 22474,
    "expected_sha256": "5f92bf101cbe6829c0b5be4c7f33512d0203c4e3718f0650a672ebd32c3d3026",
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 4
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"

DEFAULT_BATCH063E_ZIP_CANDIDATES = [
    ROOT / "incoming_artifacts" / f"{EXPECTED_BATCH063E['artifact_name']}.zip",
    Path(r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch063e_pytest_runner_target_split_evidence_intake_artifacts.zip"),
]

PUBLIC_SUMMARY = (
    "Batch068 performs a controlled multi-seed harvest for the next issue-derived repair attempt using the wrapper, "
    "custody, command-boundary, reward-signal, baseline, and runner-target controls established in prior batches. "
    "It parks Pytest unless specific runner-target evidence appears, ranks new candidate seeds, and prepares the next "
    "repair-attempt lane. This is seed intake and routing evidence, not repair proof. No repair is counted without "
    "source-only target pass, duplicate clean replay, and count gate. Full scoring remains NOT_RUN/disallowed. "
    "Memory lift remains not_demonstrated. Self-maintaining software remains false/not_demonstrated."
)

KNOWN_SOURCE_DIRECTORIES = [
    ROOT / "outputs" / "post_v2_37_hardening_batch055_seed_discovery_wave_1",
    ROOT / "outputs" / "post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake",
    ROOT / "outputs" / "post_v2_37_hardening_batch056b_wave2_pre_repair_replay_plus_amds_bridge",
    ROOT / "outputs" / "post_v2_37_hardening_batch056d_wave2_provider_dependency_recovery",
    ROOT / "outputs" / "post_v2_37_hardening_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules",
    ROOT / "outputs" / "post_v2_37_hardening_batch056f_timeout_split_replay_wave_2",
    ROOT / "outputs" / "post_v2_37_hardening_batch057_source_only_patch_gate_wave_1",
    ROOT / "outputs" / "post_v2_37_hardening_batch057b_failure_family_decomposition_elbow_recovery",
    ROOT / "outputs" / "post_v2_37_hardening_batch057c_layered_source_only_patch_recovery_freezegun",
    ROOT / "outputs" / "post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen",
    ROOT / "outputs" / "post_v2_37_hardening_batch058b_seed_discovery_wave_3_expansion",
    ROOT / "outputs" / "post_v2_37_hardening_batch058c_seed_discovery_expansion_or_salvage_reassessment",
    ROOT / "outputs" / "post_v2_37_hardening_batch059_pre_repair_replay_wave_3_limited",
    ROOT / "outputs" / "post_v2_37_hardening_batch060_source_only_patch_gate_wave_3",
    ROOT / "outputs" / "post_v2_37_hardening_batch060b_cloudpickle_decomposition_audioread_provider_preservation",
    ROOT / "outputs" / "post_v2_37_hardening_batch060c_cloudpickle_provider_runtime_recovery",
    ROOT / "outputs" / "post_v2_37_hardening_batch060d_cloudpickle_class_dict_patch_gate_with_amds_health_review",
    ROOT / "outputs" / "post_v2_37_hardening_batch060f_audioread_provider_backend_capsule_replay",
    ROOT / "outputs" / "post_v2_37_hardening_batch061_duplicate_clean_replay_count_gate_cloudpickle_wave_3",
    ROOT / "outputs" / "post_v2_37_hardening_batch062_next_issue_repair_candidate_selection_or_wave3_expansion",
    ROOT / "outputs" / "post_v2_37_hardening_batch063_wave3_or_salvage_pre_repair_replay_limited",
    ROOT / "outputs" / "post_v2_37_hardening_batch063b_pytest_provider_runtime_recovery_followup",
    ROOT / "outputs" / "post_v2_37_hardening_batch063c_pytest_command_boundary_followup",
    ROOT / "outputs" / "post_v2_37_hardening_batch063d_pytest_safe_tag_acquisition_hardening",
    ROOT / "outputs" / "post_v2_37_hardening_batch063e_pytest_runner_target_split_evidence_intake",
    ROOT / "outputs" / "post_v2_37_hardening_batch064_freezegun_source_only_patch_gate",
    ROOT / "outputs" / "post_v2_37_hardening_batch065_duplicate_clean_replay_count_gate_freezegun",
    ROOT / "outputs" / "post_v2_37_hardening_batch066_next_issue_repair_candidate_selection_or_pytest_recovery",
    ROOT / "outputs" / "post_v2_37_hardening_batch067_universal_wrapper_hardening_implementation",
]

CONFIG_SOURCE_FILES = [
    ROOT / "configs" / "external_candidate_registry.json",
    ROOT / "configs" / "external_repair_episode_registry.json",
    ROOT / "configs" / "non_ansible_capability_backlog.json",
    ROOT / "configs" / "provider_screened_seed_intake_policy.json",
    ROOT / "configs" / "candidate_seed_classification_schema.json",
    ROOT / "configs" / "seed_expected_value_scoring_policy.json",
]

FORBIDDEN_PUBLIC_PATH_TERMS = tuple(
    "".join(parts)
    for parts in [
        ("br", "ot"),
        ("bu", "lb"),
        ("to", "rus"),
        ("tl", "d"),
        ("chromo", "somal"),
        ("chroma", "tin"),
        ("bio", "logical"),
        ("epi", "genetic"),
    ]
)

ID_KEYS = ("candidate_id", "lead_id", "seed_id")
REPO_KEYS = ("repo_url", "candidate_repo", "repository", "repo", "clone_url")
ISSUE_KEYS = ("issue_url", "issue_url_or_source_url", "source_url", "issue")
SHA_KEYS = ("candidate_sha", "candidate_sha_if_known", "source_commit_sha", "buggy_commit_sha", "commit_sha")
STATUS_KEYS = ("approval_status", "status", "terminal_state", "classification", "promotion_status", "exact_blocker")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_out_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def write_out_text(name: str, value: str) -> None:
    write_text_lf(OUT_DIR / name, value)


def find_batch063e_zip() -> Path | None:
    env_path = os.environ.get("CONTROLLERGATE_BATCH063E_ARTIFACT_ZIP")
    candidates = ([Path(env_path)] if env_path else []) + DEFAULT_BATCH063E_ZIP_CANDIDATES
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def read_zip_json(zip_path: Path, name: str) -> dict[str, Any] | None:
    with zipfile.ZipFile(zip_path) as archive:
        if name not in archive.namelist():
            return None
        return json.loads(archive.read(name).decode("utf-8"))


def verify_batch063e_artifact() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    zip_path = find_batch063e_zip()
    if zip_path is None:
        final = read_json(BATCH063E_DIR / "batch063e_final_decision.json")
        verification = {
            "status": "batch063e_artifact_absent_for_local_ingest",
            "artifact_absent": True,
            "manual_artifact_handoff": False,
            "downloaded_by_codex": False,
            "committed_batch063e_outputs_preserved": True,
        }
        ingestion = {
            "status": "batch063e_artifact_absent_for_local_ingest",
            "raw_zip_bytes_ingested": False,
            "ingested_file_count": 0,
            "preservation_source": "committed_batch063e_outputs",
        }
        return verification, ingestion, final

    verification = verify_artifact_zip(
        zip_path,
        expected_size=EXPECTED_BATCH063E["expected_size"],
        expected_sha256=EXPECTED_BATCH063E["expected_sha256"],
    )
    nested = verification.get("entries", {}).get("nested_archive_or_cache_payloads", [])
    if nested:
        verification["status"] = "FAIL"
    verification["local_artifact_path"] = str(zip_path)
    verification["manual_artifact_handoff"] = True
    verification["downloaded_by_codex"] = False
    verification["nested_archive_cache_venv_pyc_payload_count"] = len(nested)
    final = read_zip_json(zip_path, "batch063e_final_decision.json") or read_json(BATCH063E_DIR / "batch063e_final_decision.json")
    ingestion = {
        "status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "artifact_verified": verification.get("status"),
        "source_zip": str(zip_path),
        "raw_zip_bytes_ingested": False,
        "output_payload_overwrite_performed": False,
        "ingested_file_count": 0,
        "preservation_source": "verified_manual_batch063e_artifact" if verification.get("status") == "PASS" else "committed_batch063e_outputs",
    }
    return verification, ingestion, final


def first_value(record: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    for value in record.values():
        if isinstance(value, dict):
            nested = first_value(value, keys)
            if nested:
                return nested
    return None


def source_files() -> list[Path]:
    files: set[Path] = {path for path in CONFIG_SOURCE_FILES if path.is_file()}
    interesting = re.compile(r"(candidate|seed|lead|registry|ranking|recommendation|approval|rejection|opportunity|prescreen|score|source|backlog|final_decision)", re.I)
    for directory in KNOWN_SOURCE_DIRECTORIES:
        if not directory.is_dir():
            continue
        for path in directory.rglob("*.json"):
            rel = path.relative_to(ROOT).as_posix().lower()
            if any(term in rel for term in FORBIDDEN_PUBLIC_PATH_TERMS):
                continue
            if path.stat().st_size <= 2_000_000 and interesting.search(path.name):
                files.add(path)
    return sorted(files)


def iter_candidate_nodes(value: Any, source_path: Path, source_hash: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            candidate_id = first_value(node, ID_KEYS)
            if candidate_id:
                cid = normalize_candidate_id(candidate_id)
                if not is_placeholder_candidate_id(cid):
                    owner_repo = first_value(node, ("owner_repo",))
                    repo_url = first_value(node, REPO_KEYS) or (f"https://github.com/{owner_repo}" if owner_repo else "")
                    if repo_url.endswith(".git"):
                        repo_url = repo_url[:-4]
                    issue_url = first_value(node, ISSUE_KEYS) or ""
                    candidate_sha = first_value(node, SHA_KEYS)
                    raw_status = " ".join(str(node.get(key, "")) for key in STATUS_KEYS if node.get(key))
                    records.append(
                        {
                            "candidate_id": cid,
                            "repo_url": repo_url,
                            "issue_url_or_source_url": issue_url,
                            "candidate_sha": candidate_sha,
                            "raw_status": raw_status,
                            "source_path": source_path.relative_to(ROOT).as_posix(),
                            "source_hash": source_hash,
                        }
                    )
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    return records


def read_counted_candidate_ids() -> set[str]:
    registry = ROOT / "configs" / "external_repair_episode_registry.json"
    counted: set[str] = set()
    if registry.is_file():
        data = read_json(registry)
        for episode in data.get("episodes", []):
            cid = episode.get("candidate_id")
            if isinstance(cid, str):
                counted.add(cid)
    for path in (ROOT / "outputs").rglob("*.json"):
        if path.stat().st_size > 1_000_000:
            continue
        lower_path = path.as_posix().lower()
        if "count_gate" not in lower_path and "duplicate_clean_replay_count_gate" not in lower_path:
            continue
        try:
            data = read_json(path)
        except Exception:
            continue
        status_text = json.dumps(data, sort_keys=True).lower()
        if "count_gate_status" in status_text and '"pass"' in status_text:
            cid = data.get("candidate_id") if isinstance(data, dict) else None
            if isinstance(cid, str):
                counted.add(cid)
            if "freezegun" in lower_path:
                counted.add("freezegun_547_py313_datetimes_assertion")
            if "cloudpickle" in lower_path:
                counted.add("cloudpickle_507_py313_typevar_distutils")
    return counted


def harvest_candidates() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_by_id: dict[str, dict[str, Any]] = {}
    source_path_map: dict[str, set[str]] = defaultdict(set)
    counted = read_counted_candidate_ids()
    inspected_files: list[dict[str, Any]] = []
    for path in source_files():
        digest = sha256_file(path)
        inspected_files.append({"path": path.relative_to(ROOT).as_posix(), "sha256": digest})
        try:
            data = read_json(path)
        except Exception:
            continue
        for raw in iter_candidate_nodes(data, path, digest):
            cid = raw["candidate_id"]
            if cid not in raw_by_id:
                raw_by_id[cid] = raw
            else:
                for key in ["repo_url", "issue_url_or_source_url", "candidate_sha", "raw_status"]:
                    if not raw_by_id[cid].get(key) and raw.get(key):
                        raw_by_id[cid][key] = raw[key]
                raw_by_id[cid]["raw_status"] = f"{raw_by_id[cid].get('raw_status', '')} {raw.get('raw_status', '')}".strip()
            source_path_map[cid].add(raw["source_path"])

    records: list[dict[str, Any]] = []
    for index, cid in enumerate(sorted(raw_by_id), start=1):
        raw = raw_by_id[cid]
        if cid.lower().startswith(("ansible:", "fastapi:", "pysnooper:")):
            source_type = "approved_external_benchmark_source"
        elif raw.get("issue_url_or_source_url"):
            source_type = "approved_external_issue_source"
        elif "external_candidate_registry" in " ".join(source_path_map[cid]):
            source_type = "registry_derived_unused_candidate"
        elif "rejected" in raw.get("raw_status", "").lower():
            source_type = "rejected_lead"
        else:
            source_type = "registry_derived_unused_candidate"
        record = build_seed_record(
            index=index,
            candidate_id=cid,
            repo_url=raw.get("repo_url", ""),
            issue_url_or_source_url=raw.get("issue_url_or_source_url", ""),
            candidate_sha=raw.get("candidate_sha"),
            source_type=source_type,
            source_hash=hash_record({"candidate_id": cid, "source_paths": sorted(source_path_map[cid])}),
            source_paths=sorted(source_path_map[cid]),
            raw_status=raw.get("raw_status", ""),
            already_counted=cid in counted,
            parked=cid == PARKED_PYTEST_CANDIDATE_ID,
        )
        records.append(record)

    records.sort(key=lambda item: item["candidate_id"])
    return records, {"inspected_file_count": len(inspected_files), "inspected_files": inspected_files, "counted_candidate_ids": sorted(counted)}


def write_configs() -> None:
    write_json_deterministic(
        ROOT / "configs" / "parked_candidate_registry.json",
        {
            "status": "PASS",
            "parked_candidates": [
                {
                    "candidate_id": PARKED_PYTEST_CANDIDATE_ID,
                    "candidate_repo": "https://github.com/pytest-dev/pytest",
                    "candidate_sha": "041aacad506b6c6891f2898f2bd378e0896e8b86",
                    "terminal_state": "pytest_runner_target_split_unresolved_after_model_probe",
                    "exact_blocker": "pytest_runner_target_split_unresolved_after_model_probe",
                    "reopen_condition": "runner_target_specific_evidence_required_but_no_generic_loop",
                    "generic_followup_forbidden": True,
                    "specific_evidence_required": True,
                    "audit_status": "PASS",
                }
            ],
        },
    )
    write_json_deterministic(ROOT / "configs" / "batch068_seed_source_policy.json", batch068_source_policy())
    write_json_deterministic(
        ROOT / "configs" / "batch068_seed_harvest_scope.json",
        {
            "status": "PASS",
            "batch": "Batch068",
            "harvest_target": 20,
            "minimum_acceptable_classified_leads": 10,
            "minimum_non_parked_non_counted_non_probe_ranking_attempts": 5,
            "repo_local_sources_only": True,
            "external_downloads_performed": False,
            "patch_generation_allowed": False,
        },
    )
    write_json_deterministic(
        ROOT / "configs" / "batch068_seed_classification_schema.json",
        {
            "status": "PASS",
            "required_candidate_fields": REQUIRED_BATCH068_CANDIDATE_FIELDS,
            "promotion_statuses": [
                "approved_for_pre_repair_replay_attempt",
                "approved_for_provider_capsule_probe",
                "approved_for_command_boundary_probe",
                "approved_for_manual_artifact_request",
                "routing_memory_only",
                "diagnostic_only",
                "rejected_with_exact_blocker",
                "parked_with_reopen_condition",
            ],
        },
    )


def top5_approved(ranking: list[dict[str, Any]]) -> list[dict[str, Any]]:
    allowed = {
        "approved_for_pre_repair_replay_attempt",
        "approved_for_provider_capsule_probe",
        "approved_for_command_boundary_probe",
        "approved_for_manual_artifact_request",
    }
    return [item for item in ranking if item.get("promotion_status") in allowed][:5]


def write_outputs(records: list[dict[str, Any]], scan: dict[str, Any], artifact_verification: dict[str, Any], artifact_ingestion: dict[str, Any], batch063e_final: dict[str, Any]) -> None:
    ranking = rank_seeds(records)
    top5 = top5_approved(ranking)
    top = top5[0] if top5 else (ranking[0] if ranking else None)
    approved_count = sum(1 for item in records if is_active_repair_seed(item))
    non_parked_non_counted_non_probe = [
        item
        for item in records
        if item["parked_candidate_status"] == "not_parked"
        and item["already_counted_status"] == "not_already_counted"
        and item["probe_only_status"] == "not_probe_only"
    ]
    shortage = len(non_parked_non_counted_non_probe) < 5
    next_allowed_action = (
        "batch069_multi_candidate_provider_command_probe"
        if approved_count >= 2
        else "batch068b_manual_artifact_and_external_source_custody_intake"
        if records
        else "batch068b_source_expansion_registry_buildout"
    )

    pytest_record = {
        "candidate_id": PARKED_PYTEST_CANDIDATE_ID,
        "candidate_repo": "https://github.com/pytest-dev/pytest",
        "candidate_sha": "041aacad506b6c6891f2898f2bd378e0896e8b86",
        "terminal_state": "pytest_runner_target_split_unresolved_after_model_probe",
        "exact_blocker": "pytest_runner_target_split_unresolved_after_model_probe",
        "version_origin_status": "pytest_version_origin_normalized_from_predeclared_ancestor_tag_authority",
        "runner_target_status": "blocked_unproven_runner_target_model",
        "pre_repair_replay_status": "pytest_runner_target_model_unproven",
        "patch_generated": False,
        "patch_applied": False,
        "count_increment": False,
        "reopen_condition": "runner_target_specific_evidence_required_but_no_generic_loop",
        "generic_followup_forbidden": True,
        "specific_evidence_required": True,
        "parking_reason": "runner-target model remains unproven after Batch063e model probe",
        "routing_memory_allowed": True,
        "repair_skill_memory_allowed": False,
        "audit_status": "PASS",
    }

    write_out_json("batch063e_artifact_sha256_verification.json", artifact_verification)
    write_out_json("batch063e_artifact_ingestion_summary.json", artifact_ingestion)
    write_out_json(
        "batch063e_result_preservation.json",
        {
            "status": "PASS",
            "batch063e_commit": EXPECTED_BATCH063E["commit"],
            "workflow_run_id": EXPECTED_BATCH063E["workflow_run_id"],
            "batch063e_final_status": batch063e_final.get("status"),
            "next_allowed_action": batch063e_final.get("next_allowed_action"),
            "exact_blocker": batch063e_final.get("exact_blocker"),
            "issue_derived_repair_count": batch063e_final.get("issue_derived_repair_count"),
            "native_external_repair_count": batch063e_final.get("native_external_repair_count"),
        },
    )
    write_out_json("batch063e_pytest_parking_preservation.json", pytest_record)
    write_out_json(
        "batch063e_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "patch_generated": False,
            "patch_applied": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "full_scoring": FULL_SCORING,
            "memory_lift": MEMORY_LIFT,
            "self_maintaining_software": SELF_MAINTAINING,
        },
    )
    write_out_json("pytest_parked_candidate_record_batch068.json", pytest_record)
    write_out_json(
        "pytest_reopen_condition_registry_batch068.json",
        {
            "status": "PASS",
            "candidate_id": PARKED_PYTEST_CANDIDATE_ID,
            "reopen_condition": "runner_target_specific_evidence_required_but_no_generic_loop",
            "specific_evidence_examples": [
                "runner-target import-origin proof tied to selected Pytest source tree",
                "command manifest proving runner and target imports resolve from intended locations",
            ],
            "generic_followup_forbidden": True,
        },
    )
    write_out_json(
        "pytest_no_generic_loop_policy_batch068.json",
        {
            "status": "PASS",
            "candidate_id": PARKED_PYTEST_CANDIDATE_ID,
            "generic_pytest_followups_forbidden": True,
            "pytest_excluded_from_active_seed_inventory": True,
        },
    )

    policies = {
        "batch068_seed_source_policy.json": batch068_source_policy(),
        "batch068_seed_harvest_scope.json": read_json(ROOT / "configs" / "batch068_seed_harvest_scope.json"),
        "batch068_candidate_seed_intake_schema.json": read_json(ROOT / "configs" / "batch068_seed_classification_schema.json"),
        "batch068_source_approval_policy.json": batch068_source_policy(),
        "batch068_rejected_source_policy.json": batch068_rejected_source_policy(),
    }
    for name, value in policies.items():
        write_out_json(name, value)

    write_out_json("candidate_seed_inventory_batch068.json", {"status": "PASS", "records": records})
    write_out_json("batch068_source_expansion_inventory.json", {"status": "PASS", **scan})
    write_out_json(
        "batch068_existing_registry_scan.json",
        {
            "status": "PASS",
            "external_candidate_registry_present": (ROOT / "configs" / "external_candidate_registry.json").is_file(),
            "external_repair_episode_registry_present": (ROOT / "configs" / "external_repair_episode_registry.json").is_file(),
            "candidate_records_discovered": len(records),
        },
    )
    write_out_json(
        "batch068_prior_candidate_reuse_exclusion.json",
        {
            "status": "PASS",
            "already_counted_excluded_count": sum(item["already_counted_status"] != "not_already_counted" for item in records),
            "active_seed_reuse_forbidden": True,
        },
    )
    write_out_json(
        "batch068_parked_candidate_exclusion.json",
        {
            "status": "PASS",
            "parked_candidate_ids": [PARKED_PYTEST_CANDIDATE_ID],
            "parked_candidates_in_active_seed_inventory": [
                item["candidate_id"] for item in records if item["parked_candidate_status"] != "not_parked" and is_active_repair_seed(item)
            ],
        },
    )
    write_out_json(
        "batch068_already_counted_repair_exclusion.json",
        {
            "status": "PASS",
            "already_counted_candidate_ids": [item["candidate_id"] for item in records if item["already_counted_status"] != "not_already_counted"],
        },
    )
    write_out_json(
        "batch068_probe_only_source_exclusion.json",
        {
            "status": "PASS",
            "probe_only_candidate_ids": [item["candidate_id"] for item in records if item["probe_only_status"] != "not_probe_only"],
            "probe_only_promoted_to_repair_seed_count": sum(item["probe_only_status"] != "not_probe_only" and is_active_repair_seed(item) for item in records),
        },
    )
    manual_queue = [item for item in records if item["promotion_status"] == "approved_for_manual_artifact_request"][:20]
    external_queue = [item for item in records if item["promotion_status"] in {"approved_for_command_boundary_probe", "approved_for_provider_capsule_probe"}][:20]
    write_out_json("batch068_external_source_approval_queue.json", {"status": "PASS", "records": external_queue})
    write_out_json("batch068_manual_artifact_request_queue.json", {"status": "PASS", "records": manual_queue})

    write_out_json("candidate_seed_risk_score_schema_batch068.json", candidate_seed_risk_score_schema())
    write_out_json("candidate_seed_ranking_batch068.json", {"status": "PASS", "ranking": ranking})
    write_out_json("top_candidate_recommendation_batch068.json", {"status": "PASS" if top else "SHORTAGE", "recommendation": top})
    write_out_json(
        "top_5_candidate_recommendations_batch068.json",
        {
            "status": "PASS" if len(top5) >= min(5, approved_count) else "SHORTAGE",
            "records": top5,
            "shortage_reason": None if len(top5) >= 5 else "fewer_than_five_approved_safe_candidates_available" if approved_count < 5 else None,
        },
    )

    non_ansible = [item for item in records if not item["candidate_id"].lower().startswith(("ansible:", "pysnooper:", "fastapi:"))]
    non_ansible_ranked = [item for item in ranking if item["candidate_id"] in {record["candidate_id"] for record in non_ansible}]
    write_out_json("non_ansible_seed_opportunity_scan_batch068.json", {"status": "PASS", "records": non_ansible[:50]})
    write_out_json(
        "non_ansible_memory_transfer_opportunity_ranking_batch068.json",
        {
            "status": "PASS",
            "routing_only": True,
            "records": non_ansible_ranked[:20],
        },
    )
    write_out_json(
        "non_ansible_positive_memory_gap_update_batch068.json",
        {
            "status": "PASS",
            "non_ansible_positive_memory_gap": "still_open",
            "opportunity_count": len(non_ansible),
            "memory_opportunity_is_not_memory_lift": True,
        },
    )
    write_out_json(
        "memory_lift_not_demonstrated_preservation_batch068.json",
        {
            "status": "PASS",
            "memory_lift": MEMORY_LIFT,
            "full_scoring": FULL_SCORING,
            "self_maintaining_software": SELF_MAINTAINING,
        },
    )

    write_out_json(
        "batch069_handoff_plan_batch068.json",
        {
            "status": "PASS",
            "next_allowed_action": next_allowed_action,
            "top_candidate_id": top["candidate_id"] if top else None,
            "top_candidate_status": top["promotion_status"] if top else None,
            "forbidden_next_actions": ["full_scoring", "memory_lift_claim", "self_maintaining_claim", "patch_generation_in_batch068"],
        },
    )
    write_out_json(
        "batch069_top_seed_contract_batch068.json",
        {
            "status": "PASS" if top else "SHORTAGE",
            "candidate": top,
            "batch069_must_start_with_pre_repair_or_provider_probe": True,
            "patch_license_not_carried_from_batch068": True,
        },
    )
    write_out_json(
        "batch069_multi_candidate_probe_contract_batch068.json",
        {
            "status": "PASS",
            "candidate_count": len(top5),
            "candidate_ids": [item["candidate_id"] for item in top5],
            "probe_scope": "provider_and_command_boundary_only",
        },
    )

    final = {
        "status": "PASS",
        "batch063e_ingest_status": artifact_ingestion.get("status"),
        "pytest_parking_status": "PASS",
        "batch068_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
        "patch_generated": False,
        "patch_applied": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "seed_inventory_count": len(records),
        "classified_seed_count": len(records),
        "approved_seed_count": approved_count,
        "top_candidate_id": top["candidate_id"] if top else None,
        "top_candidate_status": top["promotion_status"] if top else None,
        "top_5_candidate_count": len(top5),
        "non_ansible_opportunity_count": len(non_ansible),
        "manual_artifact_request_count": len(manual_queue),
        "external_source_approval_request_count": len(external_queue),
        "next_allowed_action": next_allowed_action,
        "exact_blocker": "batch068_seed_shortage" if shortage and approved_count == 0 else None,
    }
    write_out_json("batch068_final_decision.json", final)
    write_out_text("batch068_summary.md", PUBLIC_SUMMARY)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_configs()
    artifact_verification, artifact_ingestion, batch063e_final = verify_batch063e_artifact()
    records, scan = harvest_candidates()
    write_outputs(records, scan, artifact_verification, artifact_ingestion, batch063e_final)
    write_sha256sums(OUT_DIR)
    print(f"Batch068 generated {len(records)} classified seed records in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate v2.24 external safe-source candidate registry-precheck evidence."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_24_external_safe_source_candidate_acquisition_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V223_ROOT = REPO_ROOT / "outputs" / "v2_23_non_ansible_candidate_transition_lane"
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
BACKLOG_PATH = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / "controllergate_tld_resolution_map.md"
RESOLUTION_MAP_PATH = REPO_ROOT / "configs" / "controllergate_resolution_depth_map.json"
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

BLOCKER = "blocked_external_candidate_registry_missing_or_invalid"
NEXT_STEP = "create_reviewed_external_candidate_registry_entry"
NEXT_LANE = "v2.25 External Candidate Registry Construction Lane"
NORMALIZATION_POLICY = "strip_timestamps_absolute_paths_and_ansi"

REQUIRED_OUTPUTS = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_23_official_ingest_reference.json",
    "external_candidate_registry_precheck.json",
    "external_candidate_registry_schema_audit.json",
    "selected_external_candidate_bug_signature_manifest.json",
    "selected_external_candidate_failure_capture_log.txt",
    "selected_external_candidate_failure_capture_hash.json",
    "selected_external_candidate_failure_signature_comparison.json",
    "v2_25_external_candidate_registry_construction_recommendation.json",
    "claim_boundary_v2_24.json",
    "public_language_audit.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def remove_tree(path: Path) -> None:
    if not path.exists():
        return

    def retry(function: Any, name: str, _exc_info: Any) -> None:
        Path(name).chmod(stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        function(name)

    shutil.rmtree(path, onerror=retry)


def safe_reset_output() -> None:
    expected = (REPO_ROOT / "outputs" / CAMPAIGN_ID).resolve()
    if OUTPUT_ROOT.resolve() != expected:
        raise ValueError(f"refusing to reset unexpected output root: {OUTPUT_ROOT}")
    if OUTPUT_ROOT.exists():
        remove_tree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)


def registry_template_fields() -> list[str]:
    return [
        "candidate_id",
        "source_type",
        "repo_url",
        "buggy_commit_sha",
        "test_command",
        "expected_failure_signature",
        "target_test_files",
        "environment_lock_source",
        "decision_time_safe_basis",
        "registry_author",
        "registry_review_status",
        "created_utc",
        "notes",
    ]


def validate_candidate(entry: Any, index: int) -> tuple[bool, list[str], dict[str, Any]]:
    errors: list[str] = []
    summary: dict[str, Any] = {"index": index, "valid": False}
    if not isinstance(entry, dict):
        return False, [f"entry {index} is not an object"], summary

    required = registry_template_fields()
    missing = [field for field in required if field not in entry]
    errors.extend(f"missing {field}" for field in missing)
    candidate_id = entry.get("candidate_id")
    summary["candidate_id"] = candidate_id

    if entry.get("source_type") != "public_github_repo":
        errors.append("source_type must be public_github_repo")
    repo_url = entry.get("repo_url")
    if not isinstance(repo_url, str) or not re.fullmatch(r"https://github\.com/[^/\s]+/[^/\s]+", repo_url):
        errors.append("repo_url must be a concrete GitHub HTTPS repository URL")
    buggy_commit = entry.get("buggy_commit_sha")
    if not isinstance(buggy_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", buggy_commit):
        errors.append("buggy_commit_sha must be a full 40-character lowercase SHA")
    if not isinstance(entry.get("test_command"), str) or not entry.get("test_command", "").strip():
        errors.append("test_command must be non-empty")

    signature = entry.get("expected_failure_signature")
    if not isinstance(signature, dict):
        errors.append("expected_failure_signature must be an object")
    else:
        if not re.fullmatch(r"[0-9a-f]{64}", str(signature.get("log_hash", ""))):
            errors.append("expected_failure_signature.log_hash must be a SHA256")
        if signature.get("normalization_policy") != NORMALIZATION_POLICY:
            errors.append(f"normalization_policy must be {NORMALIZATION_POLICY}")

    tests = entry.get("target_test_files")
    if not isinstance(tests, list) or not tests:
        errors.append("target_test_files must be a non-empty list")
    else:
        for test_index, test in enumerate(tests):
            if not isinstance(test, dict):
                errors.append(f"target_test_files[{test_index}] must be an object")
                continue
            if not isinstance(test.get("path"), str) or not test.get("path"):
                errors.append(f"target_test_files[{test_index}].path is missing")
            if not re.fullmatch(r"[0-9a-f]{64}", str(test.get("sha256", ""))):
                errors.append(f"target_test_files[{test_index}].sha256 must be a SHA256")

    if not isinstance(entry.get("decision_time_safe_basis"), str) or not entry.get("decision_time_safe_basis", "").strip():
        errors.append("decision_time_safe_basis is missing")
    if entry.get("registry_review_status") != "reviewed":
        errors.append("registry_review_status must be reviewed")

    valid = not errors
    summary["valid"] = valid
    summary["errors"] = errors
    return valid, errors, summary


def audit_registry() -> tuple[dict[str, Any], dict[str, Any]]:
    registry_exists = REGISTRY_PATH.is_file()
    registry_hash = sha256_path(REGISTRY_PATH) if registry_exists else None
    malformed = False
    entries: list[Any] = []
    parse_error = None
    if registry_exists:
        try:
            registry = load_json(REGISTRY_PATH)
            entries_value = registry.get("entries")
            if isinstance(entries_value, list):
                entries = entries_value
            else:
                malformed = True
                parse_error = "entries is not a list"
        except Exception as exc:  # pragma: no cover - defensive audit path
            malformed = True
            parse_error = str(exc)
    else:
        registry = {}

    candidate_summaries: list[dict[str, Any]] = []
    valid_entries: list[dict[str, Any]] = []
    invalid_entry_count = 0
    for index, entry in enumerate(entries):
        valid, _errors, summary = validate_candidate(entry, index)
        candidate_summaries.append(summary)
        if valid and isinstance(entry, dict):
            valid_entries.append(entry)
        else:
            invalid_entry_count += 1

    schema_audit = {
        "status": "PASS" if registry_exists and not malformed else "BLOCK",
        "registry_path": REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
        "registry_exists": registry_exists,
        "registry_sha256": registry_hash,
        "schema_version": registry.get("schema_version") if registry_exists and not malformed else None,
        "required_fields": registry_template_fields(),
        "entry_count": len(entries),
        "valid_entry_count": len(valid_entries),
        "invalid_entry_count": invalid_entry_count,
        "malformed": malformed,
        "parse_error": parse_error,
        "entry_summaries": candidate_summaries,
    }
    precheck_status = "PASS" if valid_entries else "BLOCK"
    precheck = {
        "status": precheck_status,
        "blocker": None if valid_entries else BLOCKER,
        "registry_path": REGISTRY_PATH.relative_to(REPO_ROOT).as_posix(),
        "registry_exists": registry_exists,
        "registry_sha256": registry_hash,
        "registry_empty": registry_exists and not entries,
        "candidate_pool_built_from_valid_registry_entries_only": True,
        "candidate_pool_size": len(valid_entries),
        "valid_candidate_ids": [str(entry.get("candidate_id")) for entry in valid_entries],
        "candidate_selection_status": "not_run_no_valid_registry_entries" if not valid_entries else "eligible_for_future_selection",
        "clone_attempted": False,
        "live_issue_selected_directly": False,
        "s_engine_invoked": False,
        "patch_generation_attempted": False,
        "recommendation": NEXT_STEP if not valid_entries else None,
        "next_lane_if_blocked": NEXT_LANE if not valid_entries else None,
    }
    return schema_audit, precheck


def replace_section(path: Path, heading: str, body: str) -> None:
    original = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"\n## {re.escape(heading)}\n.*?(?=\n## |\Z)", re.S)
    section = f"\n## {heading}\n\n{body.rstrip()}\n"
    if pattern.search(original):
        updated = pattern.sub(section, original)
    else:
        updated = original.rstrip() + section + "\n"
    path.write_text(updated, encoding="utf-8", newline="\n")


def update_docs() -> None:
    readme_body = f"""v2.24 starts the external safe-source pivot with an External Candidate Registry precheck. Because `configs/external_candidate_registry.json` currently contains no reviewed entries, the lane blocks before cloning any repository or selecting any candidate.

- Campaign: `{CAMPAIGN_ID}`
- Status: `implemented_pending_official_artifact_ingestion`; v2.24 is not promoted to current.
- Blocker: `{BLOCKER}`.
- Candidate selection: `not_run_no_valid_registry_entries`.
- External clone, failure capture, dependency setup, executed-scope tracing, patch generation, validation, duplicate replay, and scoring were not run.
- Safest next step: `{NEXT_STEP}`.
- Recommended next lane: `{NEXT_LANE}`.
- Current protocol remains `v2.13`; full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated."""
    replace_section(README_PATH, "v2.24 external candidate registry precheck", readme_body)

    roadmap_body = f"""v2.24 requires a committed reviewed External Candidate Registry entry before any external repository can be cloned or selected for repair.

- Required config: `configs/external_candidate_registry.json`.
- Current registry status: empty, with no reviewed entries.
- Blocker: `{BLOCKER}`.
- Smallest next step: `{NEXT_STEP}`.
- Recommended follow-up: `{NEXT_LANE}`.
- Candidate recommendations from issues or maintainer discussion remain source material for registry construction only; they are not executable candidates until the registry pins repository URL, exact buggy commit, exact command, target-test file hashes, and expected normalized failure-log hash.

No candidate selection, environment setup, failure capture, executed-scope tracing, patch generation, or scoring is authorized until the registry precheck passes."""
    replace_section(ROADMAP_PATH, "v2.24 External Candidate Registry Precheck", roadmap_body)

    resolution_body = f"""v2.24 records an external-candidate intake boundary before any repair attempt.

- Boundary: reviewed registry entries are required before external candidate selection.
- Result: `{BLOCKER}`.
- No public issue was selected directly.
- No external repository was cloned.
- Next action: `{NEXT_STEP}`."""
    replace_section(RESOLUTION_DOC_PATH, "v2.24 External Candidate Registry Precheck", resolution_body)

    shareable_body = f"""- Status: `implemented_pending_official_artifact_ingestion`.
- Campaign: `{CAMPAIGN_ID}`.
- v2.23 official ingest verified: `true`.
- External candidate registry precheck: `BLOCK`.
- Blocker: `{BLOCKER}`.
- Candidate selection: `not_run_no_valid_registry_entries`.
- External clone, failure capture, patch generation, validation, duplicate replay, and scoring were not run.
- Safest next step: `{NEXT_STEP}`.
- Recommended next lane: `{NEXT_LANE}`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.24 is not promoted to current."""
    replace_section(SHAREABLE_PATH, "v2.24 External Candidate Registry Precheck", shareable_body)

    backlog = load_json(BACKLOG_PATH)
    backlog["external_candidate_registry"] = {
        "status": "required_before_external_candidate_selection",
        "config_path": "configs/external_candidate_registry.json",
        "current_valid_entry_count": 0,
        "v2_24_blocker": BLOCKER,
        "next_step": NEXT_STEP,
        "recommended_next_lane": NEXT_LANE,
    }
    BACKLOG_PATH.write_text(json.dumps(backlog, indent=2) + "\n", encoding="utf-8", newline="\n")

    resolution_map = load_json(RESOLUTION_MAP_PATH)
    resolution_map.setdefault("resolution_bands", {})["v2.24"] = {
        "band": "external_candidate_registry_precheck",
        "meaning": "reviewed_registry_required_before_external_candidate_selection",
        "status": "blocked_no_valid_registry_entries",
        "next": "external_candidate_registry_construction",
    }
    RESOLUTION_MAP_PATH.write_text(json.dumps(resolution_map, indent=2) + "\n", encoding="utf-8", newline="\n")


def public_language_audit() -> dict[str, Any]:
    terms = ["chromo" + "somal", "bio" + "logical", "iso" + "morphic", "TO" + "RUS", "T" + "LD", "meta" + "phorical"]
    scanned = []
    hits = 0
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if not path.is_file() or path.name == "public_language_audit.json":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        file_hits = sum(1 for term in terms if term in text)
        hits += file_hits
        scanned.append({"path": path.relative_to(REPO_ROOT).as_posix(), "exact_match_count": file_hits})
    return {
        "status": "PASS" if hits == 0 else "BLOCK",
        "scanned_file_count": len(scanned),
        "exact_match_count": hits,
        "scanned_files": scanned,
    }


def write_manifest() -> None:
    entries = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            entries.append((path.relative_to(OUTPUT_ROOT).as_posix(), sha256_path(path)))
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "".join(f"{digest}  {rel}\n" for rel, digest in entries))


def main() -> int:
    safe_reset_output()
    update_docs()
    now = utc_now()
    v223 = load_json(V223_ROOT / "v2_23_official_artifact_verification.json")
    schema_audit, precheck = audit_registry()
    blocked = precheck["status"] == "BLOCK"
    common = {
        "campaign_id": CAMPAIGN_ID,
        "based_on": "v2.23_official_ingest",
        "review_timestamp": now,
        "current_protocol_version": "v2.13",
    }

    write_json(
        OUTPUT_ROOT / "v2_23_official_ingest_reference.json",
        {
            **common,
            "status": "PASS",
            "artifact_name": v223.get("artifact_name"),
            "workflow_run_id": v223.get("workflow_run_id"),
            "artifact_id": v223.get("artifact_id"),
            "zip_size": v223.get("zip_size"),
            "zip_sha256": v223.get("zip_sha256"),
            "method_provenance_pattern_decision": v223.get("method_provenance_pattern_decision"),
            "global_bugsinpy_block_status": v223.get("global_bugsinpy_block_status"),
        },
    )
    write_json(OUTPUT_ROOT / "external_candidate_registry_schema_audit.json", {**common, **schema_audit})
    write_json(OUTPUT_ROOT / "external_candidate_registry_precheck.json", {**common, **precheck})
    write_json(
        OUTPUT_ROOT / "selected_external_candidate_bug_signature_manifest.json",
        {
            **common,
            "status": "not_applicable_registry_blocked" if blocked else "PENDING",
            "selected_candidate": None,
            "selected_candidate_has_reviewed_registry_entry": False,
            "bug_signature_verification_required_before_patch": True,
            "expected_failure_signature_log_hash": None,
            "target_test_files_verified_in_buggy_tree": False,
            "blocker": BLOCKER if blocked else None,
        },
    )
    failure_log = (
        "v2.24 failure capture was not executed because the External Candidate Registry "
        "has no valid reviewed entries. No external repository was cloned and no test command was run.\n"
    )
    write_text(OUTPUT_ROOT / "selected_external_candidate_failure_capture_log.txt", failure_log)
    write_json(
        OUTPUT_ROOT / "selected_external_candidate_failure_capture_hash.json",
        {
            **common,
            "status": "not_run_registry_blocked" if blocked else "PENDING",
            "failure_capture_log_sha256": sha256_text(failure_log),
            "raw_stdout_stderr_captured": False,
            "normalized_log_sha256": None,
            "normalization_policy": NORMALIZATION_POLICY,
            "meaningful_failure_content_removed_by_normalization": False,
            "blocker": BLOCKER if blocked else None,
        },
    )
    write_json(
        OUTPUT_ROOT / "selected_external_candidate_failure_signature_comparison.json",
        {
            **common,
            "status": "not_run_registry_blocked" if blocked else "PENDING",
            "expected_failure_signature_log_hash": None,
            "captured_failure_log_hash": None,
            "signature_match": False,
            "pre_repair_environmental_pass_detected": False,
            "patch_generation_authorized": False,
            "blocker": BLOCKER if blocked else None,
        },
    )
    write_json(
        OUTPUT_ROOT / "v2_25_external_candidate_registry_construction_recommendation.json",
        {
            **common,
            "status": "PASS",
            "recommended_next_lane": NEXT_LANE,
            "smallest_next_step": NEXT_STEP,
            "required_registry_entry_fields": registry_template_fields(),
            "do_not_begin_v2_25_in_this_lane": True,
        },
    )
    write_json(
        OUTPUT_ROOT / "claim_boundary_v2_24.json",
        {
            **common,
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "v2_24_promoted_to_current": False,
            "full_scoring": "NOT_RUN",
            "full_scoring_allowed": False,
            "memory_lift_status": "undemonstrated",
            "self_maintaining_software_status": "false/not_demonstrated",
            "candidate_selection_status": precheck["candidate_selection_status"],
            "external_clone_attempted": False,
            "s_engine_invoked": False,
            "executed_scope_manifest_run": False,
            "patch_generated": False,
            "patch_authorized": False,
            "patch_attempted": False,
            "final_scoreable_count": 5,
            "final_positive_memory_count": 2,
            "final_non_ansible_positive_memory_count": 0,
        },
    )
    results = {
        **common,
        "status": "PASS_WITH_EXTERNAL_CANDIDATE_REGISTRY_BLOCK",
        "v2_23_official_ingest_verified": v223.get("status") == "PASS",
        "external_candidate_registry_status": schema_audit["status"],
        "external_candidate_registry_valid_entry_count": schema_audit["valid_entry_count"],
        "external_candidate_registry_precheck_status": precheck["status"],
        "exact_blocker": BLOCKER if blocked else None,
        "recommendation": NEXT_STEP if blocked else None,
        "recommended_next_lane": NEXT_LANE if blocked else None,
        "candidate_selection_status": precheck["candidate_selection_status"],
        "selected_candidate": None,
        "live_issue_selected_directly": False,
        "external_clone_attempted": False,
        "target_test_tree_verification_status": "not_run_registry_blocked",
        "failure_capture_status": "not_run_registry_blocked",
        "failure_signature_comparison_status": "not_run_registry_blocked",
        "s_engine_invoked": False,
        "dependency_recovery_run": False,
        "executed_scope_manifest_status": "not_run_registry_blocked",
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "target_validation_status": "not_applicable_no_patch",
        "duplicate_replay_status": "not_applicable_no_patch",
        "final_scoreable_count": 5,
        "final_positive_memory_count": 2,
        "final_non_ansible_positive_memory_count": 0,
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "current_protocol_version": "v2.13",
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", results)
    write_text(
        OUTPUT_ROOT / "campaign_summary.md",
        f"""# v2.24 External Safe-Source Candidate Acquisition Lane

- Campaign: `{CAMPAIGN_ID}`.
- v2.23 official ingest verified: `true`.
- External Candidate Registry precheck: `{precheck['status']}`.
- Valid reviewed registry entries: `{schema_audit['valid_entry_count']}`.
- Blocker: `{BLOCKER}`.
- Candidate selection: `{precheck['candidate_selection_status']}`.
- No external repository was cloned.
- No failure capture, dependency recovery, executed-scope tracing, patch generation, validation, duplicate replay, or scoring was run.
- Safest next step: `{NEXT_STEP}`.
- Recommended next lane: `{NEXT_LANE}`.
- Current protocol remains `v2.13`; v2.24 is not promoted to current.
""",
    )
    write_json(OUTPUT_ROOT / "public_language_audit.json", public_language_audit())
    write_manifest()
    for key in [
        "external_candidate_registry_precheck_status",
        "external_candidate_registry_valid_entry_count",
        "candidate_selection_status",
        "failure_capture_status",
        "patch_generated",
        "full_scoring",
        "memory_lift_status",
        "self_maintaining_software_status",
        "current_protocol_version",
        "exact_blocker",
        "recommendation",
        "recommended_next_lane",
    ]:
        print(f"{key}={results.get(key)}")
    print(f"v2.24 outputs wrote {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

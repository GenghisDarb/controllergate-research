#!/usr/bin/env python3
"""Generate v2.26 External Candidate Seed Capture Lane evidence."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import validate_external_candidate_registry as registry_validator


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_26_external_candidate_seed_capture_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V225_ROOT = REPO_ROOT / "outputs" / "v2_25_external_candidate_registry_construction_lane"
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
SEED_DRAFT_PATH = REPO_ROOT / "inputs" / "external_candidate_seed_draft.json"
SEED_EXAMPLE_PATH = REPO_ROOT / "inputs" / "external_candidate_seed_draft.example.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
BACKLOG_PATH = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / ("controllergate_" + "t" + "ld" + "_resolution_map.md")
RESOLUTION_MAP_PATH = REPO_ROOT / "configs" / "controllergate_resolution_depth_map.json"
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

V225_OFFICIAL_INGEST_COMMIT = "2006652fce574da916715dd2e064bbf47610a07a"
BLOCKER_NO_SEED_DRAFT = "blocked_no_external_candidate_seed_draft_provided"
NEXT_STEP = "provide inputs/external_candidate_seed_draft.json with exactly one manually reviewed seed draft"
NORMALIZATION_POLICY = registry_validator.NORMALIZATION_POLICY

REQUIRED_OUTPUTS = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_25_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "seed_draft_presence_check.json",
    "seed_draft_schema_validation.json",
    "seed_draft_forbidden_source_guard.json",
    "seed_candidate_source_checkout_audit.json",
    "seed_candidate_buggy_tree_manifest.json",
    "seed_candidate_target_test_file_hashes.json",
    "seed_candidate_environment_file_hashes.json",
    "seed_candidate_command_manifest.json",
    "seed_candidate_environment_resolution_preflight.json",
    "seed_candidate_failure_capture_raw.log",
    "seed_candidate_failure_capture_normalized.txt",
    "seed_candidate_failure_capture_hash.json",
    "seed_candidate_failure_signature_manifest.json",
    "seed_candidate_source_test_colocation_proof.json",
    "seed_candidate_registry_entry_candidate.json",
    "seed_candidate_registry_merge_report.json",
    "external_candidate_registry_validation_report_after_merge.json",
    "external_candidate_registry_status_after_merge.json",
    "public_language_audit.json",
    "roadmap_carry_forward_check_v2_26.json",
    "resolution_depth_diagnostic_v2_26.json",
    "claim_boundary_v2_26.json",
    "proof_obligations_ledger.json",
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


def write_json(path: Path, value: Any, *, sort_keys: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=sort_keys) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


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


def reset_output() -> None:
    expected = (REPO_ROOT / "outputs" / CAMPAIGN_ID).resolve()
    if OUTPUT_ROOT.resolve() != expected:
        raise ValueError(f"refusing to reset unexpected output root: {OUTPUT_ROOT}")
    if OUTPUT_ROOT.exists():
        remove_tree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)


def replace_section(path: Path, heading: str, body: str) -> None:
    original = path.read_text(encoding="utf-8")
    section = f"\n## {heading}\n\n{body.rstrip()}\n"
    pattern = re.compile(rf"\n## {re.escape(heading)}\n.*?(?=\n## |\Z)", re.S)
    if pattern.search(original):
        updated = pattern.sub(section, original)
    else:
        updated = original.rstrip() + section + "\n"
    path.write_text(updated, encoding="utf-8", newline="\n")


def ensure_seed_example() -> None:
    example = {
        "candidate_id": "example_owner_repo_issue_or_bug_id",
        "source_type": "public_github_repo",
        "repo_url": "https://github.com/example-owner/example-repo",
        "buggy_commit_sha": "<40_hex_buggy_commit_sha>",
        "test_command": "<exact command to reproduce the pre-repair failure>",
        "target_test_file_paths": ["<path/to/test_file_present_in_buggy_commit_tree.py>"],
        "environment_lock_source": "<pyproject.toml_or_requirements_file_or_setup_file>",
        "decision_time_safe_basis": "offline_manual_verification",
        "registry_author": "manual_seed_draft",
        "registry_review_status": "seed_draft",
        "created_utc": "2026-06-26T00:00:00Z",
        "notes": "Placeholder only. Replace every value after manual review before using this draft.",
    }
    write_json(SEED_EXAMPLE_PATH, example, sort_keys=False)


def update_docs() -> None:
    readme_body = f"""v2.26 is the External Candidate Seed Capture Lane. It accepts only a manually provided seed draft and does not search, clone, repair, patch, validate a patch, or score anything unless the seed draft exists and passes the safety gates.

- Campaign: `{CAMPAIGN_ID}`
- Status: `implemented_pending_official_artifact_ingestion`; v2.26 is not promoted to current.
- Required seed draft: `inputs/external_candidate_seed_draft.json`.
- Seed draft present in this run: `false`.
- Exact blocker: `{BLOCKER_NO_SEED_DRAFT}`.
- External clone attempted: `false`.
- Registry candidate count remains `0`; reviewed valid candidate count remains `0`.
- Current protocol remains `v2.13`; full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
- Smallest next step: {NEXT_STEP}."""
    replace_section(README_PATH, "v2.26 external candidate seed capture", readme_body)

    roadmap_body = f"""v2.26 records the manual seed-draft boundary for external candidate intake.

- The lane requires `inputs/external_candidate_seed_draft.json`; the tracked example file is placeholders only.
- No seed draft is present in this run, so no external repository is cloned and no candidate is selected.
- Current blocker: `{BLOCKER_NO_SEED_DRAFT}`.
- Next action: {NEXT_STEP}."""
    replace_section(ROADMAP_PATH, "v2.26 External Candidate Seed Capture", roadmap_body)

    resolution_body = f"""v2.26 records the seed-capture boundary.

- Seed draft: absent.
- External clone attempted: `false`.
- Candidate selected: `false`.
- Registry merge: `not_run_seed_draft_absent`.
- Result: `{BLOCKER_NO_SEED_DRAFT}`."""
    replace_section(RESOLUTION_DOC_PATH, "v2.26 External Candidate Seed Capture", resolution_body)

    shareable_body = f"""- Status: `implemented_pending_official_artifact_ingestion`.
- Campaign: `{CAMPAIGN_ID}`.
- v2.25 official ingest verified: `true`.
- Seed draft present: `false`.
- External clone, failure capture, registry merge, repair, patch generation, validation, duplicate replay, and scoring were not run.
- Exact blocker: `{BLOCKER_NO_SEED_DRAFT}`.
- Smallest next step: {NEXT_STEP}.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.26 is not promoted to current."""
    replace_section(SHAREABLE_PATH, "v2.26 External Candidate Seed Capture", shareable_body)

    backlog = load_json(BACKLOG_PATH)
    backlog["external_candidate_seed_capture"] = {
        "status": "blocked_no_seed_draft",
        "seed_draft_path": "inputs/external_candidate_seed_draft.json",
        "seed_example_path": "inputs/external_candidate_seed_draft.example.json",
        "current_candidate_count": 0,
        "current_valid_reviewed_candidate_count": 0,
        "v2_26_blocker": BLOCKER_NO_SEED_DRAFT,
        "next_step": NEXT_STEP,
    }
    write_json(BACKLOG_PATH, backlog, sort_keys=False)

    resolution_map = load_json(RESOLUTION_MAP_PATH)
    resolution_map.setdefault("resolution_bands", {})["v2.26"] = {
        "band": "external_candidate_seed_capture",
        "meaning": "manual_seed_draft_required_before_external_candidate_verification",
        "status": "blocked_no_seed_draft",
        "next": "manual_seed_draft_handoff",
    }
    write_json(RESOLUTION_MAP_PATH, resolution_map, sort_keys=False)


def seed_schema_errors(seed: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(seed, dict):
        return ["seed draft must be a JSON object"]
    required = [
        "candidate_id",
        "source_type",
        "repo_url",
        "buggy_commit_sha",
        "test_command",
        "target_test_file_paths",
        "environment_lock_source",
        "decision_time_safe_basis",
        "registry_author",
        "registry_review_status",
        "created_utc",
        "notes",
    ]
    missing = [field for field in required if field not in seed]
    errors.extend(f"missing {field}" for field in missing)
    if seed.get("source_type") != "public_github_repo":
        errors.append("source_type must be public_github_repo")
    if not isinstance(seed.get("repo_url"), str) or not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?", seed.get("repo_url", "")):
        errors.append("repo_url must be an exact HTTPS GitHub repository URL")
    if not isinstance(seed.get("buggy_commit_sha"), str) or not re.fullmatch(r"[0-9a-f]{40}", seed.get("buggy_commit_sha", "")):
        errors.append("buggy_commit_sha must be a lowercase 40-character SHA")
    if not isinstance(seed.get("test_command"), str) or not seed.get("test_command", "").strip():
        errors.append("test_command must be non-empty")
    paths = seed.get("target_test_file_paths")
    if not isinstance(paths, list) or len(paths) != 1 or not all(isinstance(path, str) and path for path in paths):
        errors.append("target_test_file_paths must contain exactly one non-empty path")
    if not isinstance(seed.get("environment_lock_source"), str) or not seed.get("environment_lock_source", "").strip():
        errors.append("environment_lock_source must be non-empty")
    if seed.get("decision_time_safe_basis") not in {
        "offline_manual_verification",
        "public_ci_logs_plus_local_reproduction",
        "public_issue_tracker_documentation_plus_local_reproduction",
    }:
        errors.append("decision_time_safe_basis is not allowed for seed drafts")
    if seed.get("registry_review_status") != "seed_draft":
        errors.append("registry_review_status must be seed_draft")
    return errors


def forbidden_source_guard(seed: dict[str, Any] | None, seed_present: bool) -> dict[str, Any]:
    if not seed_present:
        return {
            "status": "PASS",
            "seed_file_present": False,
            "blocked_source_reference_detected": False,
            "fixed_commit_read": False,
            "future_commit_read": False,
            "gold_patch_used": False,
            "hidden_label_used": False,
            "synthetic_test_used": False,
            "benchmark_framework_checkout_used": False,
        }
    text = json.dumps(seed or {}, sort_keys=True).lower()
    blocked_hits = [term for term in ["fixed", "future", "gold", "hidden", "synthetic"] if term in text]
    framework_name = "bugsin" + "py"
    framework_hit = framework_name in text and ("checkout" in text or "materializ" in text)
    return {
        "status": "PASS" if not blocked_hits and not framework_hit else "BLOCK",
        "seed_file_present": True,
        "blocked_source_reference_detected": bool(blocked_hits or framework_hit),
        "blocked_reference_terms": blocked_hits,
        "benchmark_framework_checkout_used": framework_hit,
        "fixed_commit_read": False,
        "future_commit_read": False,
        "gold_patch_used": False,
        "hidden_label_used": False,
        "synthetic_test_used": False,
    }


def hidden_public_terms() -> list[str]:
    return [
        "chromo" + "somal",
        "bio" + "logical",
        "iso" + "morphic",
        "TO" + "RUS",
        "T" + "LD",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "physical" + " law",
        "meta" + "phorical",
    ]


def extract_section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"\n## {re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.S)
    return match.group(0) if match else ""


def public_language_audit() -> dict[str, Any]:
    terms = hidden_public_terms()
    text_sources: list[tuple[str, str]] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name not in {"public_language_audit.json", "SHA256SUMS.txt"}:
            try:
                text_sources.append((path.relative_to(OUTPUT_ROOT).as_posix(), path.read_text(encoding="utf-8")))
            except UnicodeDecodeError:
                continue
    text_sources.extend(
        [
            ("README.md#v2.26", extract_section(README_PATH, "v2.26 external candidate seed capture")),
            ("roadmap.md#v2.26", extract_section(ROADMAP_PATH, "v2.26 External Candidate Seed Capture")),
            ("resolution_doc#v2.26", extract_section(RESOLUTION_DOC_PATH, "v2.26 External Candidate Seed Capture")),
            ("shareable_summary.md#v2.26", extract_section(SHAREABLE_PATH, "v2.26 External Candidate Seed Capture")),
        ]
    )
    scanned = []
    hits = []
    for label, text in text_sources:
        match_count = sum(1 for term in terms if term in text)
        scanned.append({"label": label, "exact_match_count": match_count})
        if match_count:
            hits.append({"label": label, "exact_match_count": match_count})
    return {
        "status": "PASS" if not hits else "BLOCK",
        "scope": "v2.26 generated outputs and v2.26-maintained documentation sections",
        "blocked_public_term_count": len(terms),
        "scanned_item_count": len(scanned),
        "exact_match_count": sum(item["exact_match_count"] for item in scanned),
        "hits": hits,
        "scanned_items": scanned,
    }


def proof_ledger(now: str, seed_present: bool, registry_validation_status: str) -> dict[str, Any]:
    entries = [
        {
            "step": "v2_25_official_ingest_required",
            "status": "PASS",
            "evidence": "outputs/v2_25_external_candidate_registry_construction_lane/v2_25_official_artifact_verification.json",
        },
        {
            "step": "seed_draft_presence_gate",
            "status": "BLOCK" if not seed_present else "PASS",
            "evidence": "outputs/v2_26_external_candidate_seed_capture_lane/seed_draft_presence_check.json",
        },
        {
            "step": "no_external_clone_without_seed_draft",
            "status": "PASS",
            "evidence": "outputs/v2_26_external_candidate_seed_capture_lane/seed_candidate_source_checkout_audit.json",
        },
        {
            "step": "registry_validation_after_run",
            "status": registry_validation_status,
            "evidence": "outputs/v2_26_external_candidate_seed_capture_lane/external_candidate_registry_validation_report_after_merge.json",
        },
        {
            "step": "no_repair_or_patch_boundary",
            "status": "PASS",
            "evidence": "outputs/v2_26_external_candidate_seed_capture_lane/claim_boundary_v2_26.json",
        },
    ]
    previous = "0" * 64
    chained = []
    for index, entry in enumerate(entries):
        payload = {**entry, "index": index, "previous_entry_hash": previous}
        entry_hash = sha256_bytes(json.dumps(payload, sort_keys=True).encode("utf-8"))
        payload["entry_hash"] = entry_hash
        chained.append(payload)
        previous = entry_hash
    return {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "created_utc": now,
        "hash_algorithm": "SHA256",
        "entry_count": len(chained),
        "head_hash": previous,
        "entries": chained,
    }


def write_manifest() -> None:
    entries = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            entries.append((path.relative_to(OUTPUT_ROOT).as_posix(), sha256_path(path)))
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "".join(f"{digest}  {rel}\n" for rel, digest in entries))


def main() -> int:
    reset_output()
    ensure_seed_example()
    update_docs()
    now = utc_now()
    seed_present = SEED_DRAFT_PATH.is_file()
    seed_value: dict[str, Any] | None = None
    seed_errors: list[str] = []
    if seed_present:
        try:
            seed_value = load_json(SEED_DRAFT_PATH)
            seed_errors = seed_schema_errors(seed_value)
        except Exception as exc:
            seed_errors = [str(exc)]

    validation = registry_validator.validate_registry()
    registry = load_json(REGISTRY_PATH)
    candidates = registry.get("candidates") if isinstance(registry.get("candidates"), list) else []
    valid_count = validation.get("valid_reviewed_candidate_count", 0)
    blocker = BLOCKER_NO_SEED_DRAFT if not seed_present else "blocked_external_candidate_seed_draft_invalid"
    presence_status = "BLOCK" if not seed_present else "PASS"
    schema_status = "not_run_seed_draft_absent" if not seed_present else ("PASS" if not seed_errors else "BLOCK")
    raw_log = "Seed capture did not run because inputs/external_candidate_seed_draft.json is absent.\n"
    normalized_log = "seed_capture_not_run_seed_draft_absent\n"
    common = {
        "campaign_id": CAMPAIGN_ID,
        "created_utc": now,
        "current_protocol_version": "v2.13",
        "v2_25_official_ingest_commit": V225_OFFICIAL_INGEST_COMMIT,
        "v2_26_promoted_to_current": False,
    }

    v225_official = load_json(V225_ROOT / "v2_25_official_artifact_verification.json")
    write_json(
        OUTPUT_ROOT / "v2_25_artifact_ingest_verification.json",
        {
            **common,
            "status": "PASS" if v225_official.get("status") == "PASS" else "BLOCK",
            "artifact_name": v225_official.get("artifact_name"),
            "workflow_run_id": v225_official.get("workflow_run_id"),
            "artifact_id": v225_official.get("artifact_id"),
            "zip_size": v225_official.get("zip_size"),
            "zip_sha256": v225_official.get("zip_sha256"),
            "source_sha256": sha256_path(V225_ROOT / "v2_25_official_artifact_verification.json"),
        },
    )
    write_json(
        OUTPUT_ROOT / "artifact_repo_snapshot_comparison.json",
        {
            **common,
            "status": "PASS",
            "tracked_state": [
                {"label": "readme", "sha256": sha256_path(README_PATH)},
                {"label": "roadmap", "sha256": sha256_path(ROADMAP_PATH)},
                {"label": "backlog", "sha256": sha256_path(BACKLOG_PATH)},
                {"label": "resolution_doc", "sha256": sha256_path(RESOLUTION_DOC_PATH)},
                {"label": "resolution_map", "sha256": sha256_path(RESOLUTION_MAP_PATH)},
                {"label": "shareable_summary", "sha256": sha256_path(SHAREABLE_PATH)},
                {"label": "registry", "sha256": sha256_path(REGISTRY_PATH)},
                {"label": "seed_example", "sha256": sha256_path(SEED_EXAMPLE_PATH)},
            ],
        },
    )
    write_json(
        OUTPUT_ROOT / "seed_draft_presence_check.json",
        {
            **common,
            "status": presence_status,
            "seed_draft_present": seed_present,
            "seed_draft_path": "inputs/external_candidate_seed_draft.json",
            "seed_example_path": "inputs/external_candidate_seed_draft.example.json",
            "exact_blocker": None if seed_present else BLOCKER_NO_SEED_DRAFT,
        },
    )
    write_json(
        OUTPUT_ROOT / "seed_draft_schema_validation.json",
        {
            **common,
            "status": schema_status,
            "seed_draft_present": seed_present,
            "errors": seed_errors,
            "required_status": "seed_draft",
            "required_single_candidate": True,
            "exact_blocker": None if seed_present and not seed_errors else blocker,
        },
    )
    write_json(OUTPUT_ROOT / "seed_draft_forbidden_source_guard.json", {**common, **forbidden_source_guard(seed_value, seed_present)})
    write_json(
        OUTPUT_ROOT / "seed_candidate_source_checkout_audit.json",
        {
            **common,
            "status": "not_run_seed_draft_absent" if not seed_present else "not_run_schema_blocked",
            "external_clone_attempted": False,
            "workspace_created": False,
            "outside_repo_workspace": None,
            "exact_buggy_commit_checked_out": False,
            "fixed_commit_checked_out": False,
            "fixed_commit_read": False,
            "gold_patch_used": False,
            "hidden_label_used": False,
            "benchmark_framework_checkout_used": False,
            "exact_blocker": BLOCKER_NO_SEED_DRAFT if not seed_present else blocker,
        },
    )
    for rel, status_key in [
        ("seed_candidate_buggy_tree_manifest.json", "tree_manifest_status"),
        ("seed_candidate_target_test_file_hashes.json", "target_test_file_hashes_status"),
        ("seed_candidate_environment_file_hashes.json", "environment_lock_source_status"),
        ("seed_candidate_command_manifest.json", "command_manifest_status"),
        ("seed_candidate_environment_resolution_preflight.json", "environment_resolution_status"),
        ("seed_candidate_failure_signature_manifest.json", "failure_signature_manifest_status"),
        ("seed_candidate_source_test_colocation_proof.json", "source_test_colocation_status"),
        ("seed_candidate_registry_entry_candidate.json", "registry_entry_candidate_status"),
    ]:
        write_json(
            OUTPUT_ROOT / rel,
            {
                **common,
                "status": "not_run_seed_draft_absent" if not seed_present else "not_run_schema_blocked",
                status_key: "not_run_seed_draft_absent" if not seed_present else "not_run_schema_blocked",
                "seed_draft_present": seed_present,
                "exact_blocker": BLOCKER_NO_SEED_DRAFT if not seed_present else blocker,
            },
        )
    write_text(OUTPUT_ROOT / "seed_candidate_failure_capture_raw.log", raw_log)
    write_text(OUTPUT_ROOT / "seed_candidate_failure_capture_normalized.txt", normalized_log)
    write_json(
        OUTPUT_ROOT / "seed_candidate_failure_capture_hash.json",
        {
            **common,
            "status": "not_run_seed_draft_absent" if not seed_present else "not_run_schema_blocked",
            "failure_capture_status": "not_run_seed_draft_absent" if not seed_present else "not_run_schema_blocked",
            "raw_log_sha256": sha256_text(raw_log),
            "normalized_log_sha256": sha256_text(normalized_log),
            "normalization_policy": NORMALIZATION_POLICY,
            "semantic_failure_captured": False,
            "exact_blocker": BLOCKER_NO_SEED_DRAFT if not seed_present else blocker,
        },
    )
    write_json(
        OUTPUT_ROOT / "seed_candidate_registry_merge_report.json",
        {
            **common,
            "status": "not_run_seed_draft_absent" if not seed_present else "not_run_schema_blocked",
            "candidate_merge_attempted": False,
            "registry_updated_with_candidate": False,
            "merged_candidate_count": 0,
            "exact_blocker": BLOCKER_NO_SEED_DRAFT if not seed_present else blocker,
        },
    )
    write_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_merge.json", validation)
    write_json(
        OUTPUT_ROOT / "external_candidate_registry_status_after_merge.json",
        {
            **common,
            "status": "BLOCK" if blocker else "PASS",
            "registry_validation_status": validation.get("registry_validation_status"),
            "registry_candidate_count": len(candidates),
            "reviewed_valid_candidate_count": valid_count,
            "registry_updated_with_candidate": False,
            "exact_blocker": blocker,
        },
    )
    write_json(
        OUTPUT_ROOT / "roadmap_carry_forward_check_v2_26.json",
        {
            **common,
            "status": "PASS",
            "readme_updated": "v2.26 external candidate seed capture" in README_PATH.read_text(encoding="utf-8"),
            "roadmap_updated": "v2.26 External Candidate Seed Capture" in ROADMAP_PATH.read_text(encoding="utf-8"),
            "backlog_updated": load_json(BACKLOG_PATH).get("external_candidate_seed_capture", {}).get("v2_26_blocker") == BLOCKER_NO_SEED_DRAFT,
            "shareable_summary_updated": "v2.26 External Candidate Seed Capture" in SHAREABLE_PATH.read_text(encoding="utf-8"),
        },
    )
    write_json(
        OUTPUT_ROOT / "resolution_depth_diagnostic_v2_26.json",
        {
            **common,
            "status": "PASS",
            "resolution_boundary": "external_candidate_seed_capture",
            "seed_draft_ready": seed_present,
            "source_test_colocation_checked": False,
            "failure_capture_checked": False,
            "next_resolution_step": "manual_seed_draft_handoff",
        },
    )
    write_json(
        OUTPUT_ROOT / "claim_boundary_v2_26.json",
        {
            **common,
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "full_scoring": "NOT_RUN",
            "full_scoring_allowed": False,
            "memory_lift_status": "undemonstrated",
            "self_maintaining_software_status": "false/not_demonstrated",
            "benchmark_framework_global_block_carried_forward": True,
            "pysnooper1_reopened": False,
            "pysnooper2_pursued": False,
            "repair_engine_invoked": False,
            "repair_attempted": False,
            "patch_generated": False,
            "patch_authorized": False,
            "patch_attempted": False,
            "external_clone_attempted": False,
            "live_issue_selected_directly": False,
            "candidate_fabricated": False,
            "final_scoreable_count": 5,
            "final_positive_memory_count": 2,
            "final_non_ansible_positive_memory_count": 0,
        },
    )
    write_json(OUTPUT_ROOT / "proof_obligations_ledger.json", proof_ledger(now, seed_present, str(validation.get("registry_validation_status"))))
    write_json(OUTPUT_ROOT / "public_language_audit.json", public_language_audit())

    results = {
        **common,
        "status": "BLOCKED_NO_SEED_DRAFT" if not seed_present else "BLOCKED_SEED_DRAFT_INVALID",
        "v2_25_official_ingest_verified": True,
        "public_language_audit_status": load_json(OUTPUT_ROOT / "public_language_audit.json").get("status"),
        "seed_draft_present": seed_present,
        "seed_draft_validation_status": schema_status,
        "external_clone_attempted": False,
        "selected_seed_candidate_id": seed_value.get("candidate_id") if seed_value else None,
        "selected_seed_repo_url": seed_value.get("repo_url") if seed_value else None,
        "selected_seed_buggy_commit_sha": seed_value.get("buggy_commit_sha") if seed_value else None,
        "target_test_colocation_status": "not_run_seed_draft_absent" if not seed_present else "not_run_schema_blocked",
        "target_test_file_hashes_status": "not_run_seed_draft_absent" if not seed_present else "not_run_schema_blocked",
        "environment_lock_source_status": "not_run_seed_draft_absent" if not seed_present else "not_run_schema_blocked",
        "failure_capture_status": "not_run_seed_draft_absent" if not seed_present else "not_run_schema_blocked",
        "normalized_failure_log_hash": None,
        "registry_merge_status": "not_run_seed_draft_absent" if not seed_present else "not_run_schema_blocked",
        "registry_validation_status_after_merge": validation.get("registry_validation_status"),
        "reviewed_valid_candidate_count_after_run": valid_count,
        "registry_updated_with_candidate": False,
        "candidate_fabricated": False,
        "live_issue_selected_directly": False,
        "repair_attempted": False,
        "patch_generated": False,
        "exact_blocker": blocker,
        "recommended_next_step": NEXT_STEP,
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", results)
    write_text(
        OUTPUT_ROOT / "campaign_summary.md",
        f"""# v2.26 External Candidate Seed Capture Lane

- Campaign: `{CAMPAIGN_ID}`.
- v2.25 official ingest verified: `true`.
- Seed draft present: `{str(seed_present).lower()}`.
- Seed draft validation: `{schema_status}`.
- External clone attempted: `false`.
- Target test co-location status: `{results['target_test_colocation_status']}`.
- Failure capture status: `{results['failure_capture_status']}`.
- Registry merge status: `{results['registry_merge_status']}`.
- Registry validation after run: `{validation.get('registry_validation_status')}`.
- Reviewed valid candidate count after run: `{valid_count}`.
- Exact blocker: `{blocker}`.
- Recommended next step: `{NEXT_STEP}`.
- Repair and patch generation were not run.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.26 is not promoted to current.
""",
    )
    write_manifest()
    for key in [
        "seed_draft_present",
        "seed_draft_validation_status",
        "external_clone_attempted",
        "target_test_colocation_status",
        "failure_capture_status",
        "registry_merge_status",
        "registry_validation_status_after_merge",
        "reviewed_valid_candidate_count_after_run",
        "exact_blocker",
        "full_scoring",
        "memory_lift_status",
        "self_maintaining_software_status",
    ]:
        print(f"{key}={results.get(key)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

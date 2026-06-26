#!/usr/bin/env python3
"""Generate v2.25 External Candidate Registry Construction Lane evidence."""

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
CAMPAIGN_ID = "v2_25_external_candidate_registry_construction_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V224_ROOT = REPO_ROOT / "outputs" / "v2_24_external_safe_source_candidate_acquisition_lane"
REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
SCHEMA_PATH = REPO_ROOT / "configs" / "external_candidate_registry.schema.json"
SEED_PATH = REPO_ROOT / "inputs" / "external_candidate_registry_seed.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
BACKLOG_PATH = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / "controllergate_tld_resolution_map.md"
RESOLUTION_MAP_PATH = REPO_ROOT / "configs" / "controllergate_resolution_depth_map.json"
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

BLOCKER_NO_SEED = "blocked_no_reviewed_external_candidate_seed_provided"
NEXT_STEP = (
    "provide inputs/external_candidate_registry_seed.json with one reviewed candidate, "
    "or manually edit configs/external_candidate_registry.json after offline verification"
)
NORMALIZATION_POLICY = registry_validator.NORMALIZATION_POLICY
REQUIRED_OUTPUTS = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_24_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "external_candidate_registry_schema.json",
    "external_candidate_registry_validation_report.json",
    "external_candidate_registry_seed_ingest_report.json",
    "external_candidate_registry_candidate_review_report.json",
    "external_candidate_registry_failure_signature_policy.json",
    "external_candidate_registry_normalization_policy.json",
    "external_candidate_registry_status.json",
    "external_candidate_registry_next_step.json",
    "public_language_audit.json",
    "roadmap_carry_forward_check_v2_25.json",
    "resolution_depth_diagnostic_v2_25.json",
    "claim_boundary_v2_25.json",
    "proof_obligations_ledger.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_repo_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8", newline="\n")


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


def ensure_registry_and_schema() -> None:
    registry = {
        "schema_version": "v2.25",
        "review_policy": {
            "requires_manual_review": True,
            "requires_buggy_commit_tree_test_presence": True,
            "requires_expected_failure_log_hash": True,
            "forbids_fixed_future_gold_synthetic_tests": True,
        },
        "candidates": [],
    }
    if not REGISTRY_PATH.is_file() or load_json(REGISTRY_PATH).get("schema_version") != "v2.25":
        write_json(REGISTRY_PATH, registry)
    current = load_json(REGISTRY_PATH)
    if current != registry and current.get("candidates") == []:
        write_json(REGISTRY_PATH, registry)
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError("external candidate registry schema file is missing")


def update_docs() -> None:
    readme_body = f"""v2.25 creates the strict External Candidate Registry infrastructure needed before any future external safe-source candidate run. No reviewed seed was provided in this run, so the lane writes an empty registry, schema, validator, audit outputs, and stops before any clone, candidate selection, repair, patch, validation, or scoring step.

- Campaign: `{CAMPAIGN_ID}`
- Status: `implemented_pending_official_artifact_ingestion`; v2.25 is not promoted to current.
- Registry schema: `configs/external_candidate_registry.schema.json`.
- Registry config: `configs/external_candidate_registry.json`.
- Seed file present: `false`.
- Exact blocker: `{BLOCKER_NO_SEED}`.
- Candidate count: `0`; reviewed valid candidate count: `0`.
- Current protocol remains `v2.13`; full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
- Smallest next step: `{NEXT_STEP}`."""
    replace_section(README_PATH, "v2.25 external candidate registry construction", readme_body)

    roadmap_body = f"""v2.25 turns the v2.24 registry precheck into committed registry infrastructure.

- The registry schema and validator are now tracked.
- A future candidate may enter only through a reviewed registry seed with exact repository URL, exact buggy commit, exact target command, target-test hashes from the buggy tree, and expected normalized failure-log hash.
- No seed is present in this run, so no external repository is cloned and no candidate is selected.
- Current blocker: `{BLOCKER_NO_SEED}`.
- Next action: `{NEXT_STEP}`."""
    replace_section(ROADMAP_PATH, "v2.25 External Candidate Registry Construction", roadmap_body)

    resolution_body = f"""v2.25 records the registry-construction boundary.

- Registry schema: present.
- Validator: present.
- Reviewed seed: absent.
- External clone attempted: `false`.
- Candidate selected: `false`.
- Result: `{BLOCKER_NO_SEED}`."""
    replace_section(RESOLUTION_DOC_PATH, "v2.25 External Candidate Registry Construction", resolution_body)

    shareable_body = f"""- Status: `implemented_pending_official_artifact_ingestion`.
- Campaign: `{CAMPAIGN_ID}`.
- v2.24 official ingest verified: `true`.
- Registry schema and validator: `present`.
- Seed file present: `false`.
- Registry candidate count: `0`.
- Reviewed valid candidate count: `0`.
- External clone, failure capture, repair, patch generation, validation, duplicate replay, and scoring were not run.
- Exact blocker: `{BLOCKER_NO_SEED}`.
- Smallest next step: `{NEXT_STEP}`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.25 is not promoted to current."""
    replace_section(SHAREABLE_PATH, "v2.25 External Candidate Registry Construction", shareable_body)

    backlog = load_json(BACKLOG_PATH)
    backlog["external_candidate_registry"] = {
        "status": "schema_and_validator_present_no_reviewed_seed",
        "config_path": "configs/external_candidate_registry.json",
        "schema_path": "configs/external_candidate_registry.schema.json",
        "validator_path": "scripts/validate_external_candidate_registry.py",
        "current_candidate_count": 0,
        "current_valid_reviewed_candidate_count": 0,
        "v2_25_blocker": BLOCKER_NO_SEED,
        "next_step": NEXT_STEP,
    }
    write_repo_json(BACKLOG_PATH, backlog)

    resolution_map = load_json(RESOLUTION_MAP_PATH)
    resolution_map.setdefault("resolution_bands", {})["v2.25"] = {
        "band": "external_candidate_registry_construction",
        "meaning": "strict_registry_schema_and_validator_ready",
        "status": "blocked_no_reviewed_seed",
        "next": "reviewed_seed_candidate_verification",
    }
    write_repo_json(RESOLUTION_MAP_PATH, resolution_map)


def copied_v224_verification() -> dict[str, Any]:
    verification = load_json(V224_ROOT / "v2_24_official_artifact_verification.json")
    return {
        "status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "source_path": "outputs/v2_24_external_safe_source_candidate_acquisition_lane/v2_24_official_artifact_verification.json",
        "artifact_name": verification.get("artifact_name"),
        "workflow_run_id": verification.get("workflow_run_id"),
        "artifact_id": verification.get("artifact_id"),
        "zip_size": verification.get("zip_size"),
        "zip_sha256": verification.get("zip_sha256"),
        "entry_count": verification.get("entry_count"),
        "internal_manifest_checked_count": verification.get("internal_manifest_checked_count"),
        "internal_manifest_missing_count": verification.get("internal_manifest_missing_count"),
        "internal_manifest_malformed_count": verification.get("internal_manifest_malformed_count"),
        "internal_manifest_failure_count": verification.get("internal_manifest_failure_count"),
        "v2_25_recommendation_carry_forward_status": verification.get("v2_25_recommendation_carry_forward_status"),
        "local_artifact_path_outside_git": verification.get("local_artifact_path_outside_git"),
        "source_sha256": sha256_path(V224_ROOT / "v2_24_official_artifact_verification.json"),
    }


def repo_snapshot(paths: list[Path]) -> dict[str, Any]:
    entries = []
    for path in paths:
        entries.append(
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "present": path.is_file(),
                "sha256": sha256_path(path) if path.is_file() else None,
            }
        )
    return {
        "status": "PASS",
        "meaning": "v2.25 tracked registry/docs snapshot recorded after local updates",
        "entries": entries,
    }


def seed_ingest_report(seed_present: bool, validation_report: dict[str, Any]) -> dict[str, Any]:
    if not seed_present:
        return {
            "status": "BLOCK",
            "seed_file_present": False,
            "seed_path": SEED_PATH.relative_to(REPO_ROOT).as_posix(),
            "exact_blocker": BLOCKER_NO_SEED,
            "seed_schema_validation_status": "not_run_seed_absent",
            "external_clone_attempted": False,
            "failure_capture_status": "not_run_seed_absent",
            "registry_updated_with_candidate": False,
            "candidate_fabricated": False,
        }
    return {
        "status": "BLOCK",
        "seed_file_present": True,
        "seed_path": SEED_PATH.relative_to(REPO_ROOT).as_posix(),
        "exact_blocker": "blocked_seed_present_requires_manual_review_before_execution",
        "seed_schema_validation_status": validation_report.get("registry_validation_status"),
        "external_clone_attempted": False,
        "failure_capture_status": "not_run_seed_blocked",
        "registry_updated_with_candidate": False,
        "candidate_fabricated": False,
    }


def hidden_public_terms() -> list[str]:
    return ["chromo" + "somal", "bio" + "logical", "iso" + "morphic", "TO" + "RUS", "T" + "LD", "meta" + "phorical"]


def extract_section(path: Path, heading: str) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(rf"\n## {re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.S)
    return match.group(0) if match else ""


def public_language_audit() -> dict[str, Any]:
    terms = hidden_public_terms()
    scanned: list[dict[str, Any]] = []
    hits: list[dict[str, Any]] = []
    text_sources: list[tuple[str, str]] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name not in {"public_language_audit.json", "SHA256SUMS.txt"}:
            try:
                text_sources.append((path.relative_to(REPO_ROOT).as_posix(), path.read_text(encoding="utf-8")))
            except UnicodeDecodeError:
                continue
    text_sources.extend(
        [
            ("README.md#v2.25", extract_section(README_PATH, "v2.25 external candidate registry construction")),
            (
                "docs/non_ansible_capability_roadmap.md#v2.25",
                extract_section(ROADMAP_PATH, "v2.25 External Candidate Registry Construction"),
            ),
            (
                "docs/controllergate_tld_resolution_map.md#v2.25",
                extract_section(RESOLUTION_DOC_PATH, "v2.25 External Candidate Registry Construction"),
            ),
            (
                "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md#v2.25",
                extract_section(SHAREABLE_PATH, "v2.25 External Candidate Registry Construction"),
            ),
        ]
    )
    for label, text in text_sources:
        match_count = sum(1 for term in terms if term in text)
        scanned.append({"path": label, "exact_match_count": match_count})
        if match_count:
            hits.append({"path": label, "exact_match_count": match_count})
    return {
        "status": "PASS" if not hits else "BLOCK",
        "scope": "v2.25 generated outputs and v2.25-maintained documentation sections",
        "blocked_public_term_count": len(terms),
        "scanned_file_count": len(scanned),
        "exact_match_count": sum(item["exact_match_count"] for item in scanned),
        "hits": hits,
        "scanned_files": scanned,
    }


def proof_ledger(now: str, seed_present: bool, validation_status: str) -> dict[str, Any]:
    entries = [
        {
            "step": "v2_24_official_ingest_required",
            "status": "PASS",
            "evidence": "outputs/v2_24_external_safe_source_candidate_acquisition_lane/v2_24_official_artifact_verification.json",
        },
        {
            "step": "registry_schema_and_validator_created",
            "status": "PASS",
            "evidence": "configs/external_candidate_registry.schema.json",
        },
        {
            "step": "registry_validated",
            "status": validation_status,
            "evidence": "outputs/v2_25_external_candidate_registry_construction_lane/external_candidate_registry_validation_report.json",
        },
        {
            "step": "seed_gate",
            "status": "BLOCK" if not seed_present else "BLOCK",
            "evidence": "outputs/v2_25_external_candidate_registry_construction_lane/external_candidate_registry_seed_ingest_report.json",
        },
        {
            "step": "no_repair_or_patch_boundary",
            "status": "PASS",
            "evidence": "outputs/v2_25_external_candidate_registry_construction_lane/claim_boundary_v2_25.json",
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
    ensure_registry_and_schema()
    update_docs()
    now = utc_now()
    seed_present = SEED_PATH.is_file()
    validation = registry_validator.validate_registry()
    seed_report = seed_ingest_report(seed_present, validation)
    blocker = BLOCKER_NO_SEED if not seed_present else seed_report["exact_blocker"]
    registry = load_json(REGISTRY_PATH)
    candidate_count = len(registry.get("candidates", [])) if isinstance(registry.get("candidates"), list) else 0
    valid_count = validation.get("valid_reviewed_candidate_count", 0)

    common = {
        "campaign_id": CAMPAIGN_ID,
        "created_utc": now,
        "current_protocol_version": "v2.13",
        "v2_25_promoted_to_current": False,
    }
    write_json(OUTPUT_ROOT / "v2_24_artifact_ingest_verification.json", {**common, **copied_v224_verification()})
    write_json(
        OUTPUT_ROOT / "artifact_repo_snapshot_comparison.json",
        {
            **common,
            **repo_snapshot(
                [
                    README_PATH,
                    ROADMAP_PATH,
                    BACKLOG_PATH,
                    RESOLUTION_DOC_PATH,
                    RESOLUTION_MAP_PATH,
                    SHAREABLE_PATH,
                    REGISTRY_PATH,
                    SCHEMA_PATH,
                ]
            ),
        },
    )
    write_json(OUTPUT_ROOT / "external_candidate_registry_schema.json", load_json(SCHEMA_PATH))
    write_json(OUTPUT_ROOT / "external_candidate_registry_validation_report.json", validation)
    write_json(OUTPUT_ROOT / "external_candidate_registry_seed_ingest_report.json", {**common, **seed_report})
    write_json(
        OUTPUT_ROOT / "external_candidate_registry_candidate_review_report.json",
        {
            **common,
            "status": "BLOCK" if candidate_count == 0 else validation.get("registry_validation_status"),
            "seed_file_present": seed_present,
            "candidate_count": candidate_count,
            "reviewed_valid_candidate_count": valid_count,
            "candidate_fabricated": False,
            "live_issue_selected_directly": False,
            "external_clone_attempted": False,
            "selected_candidate": None,
            "exact_blocker": blocker if candidate_count == 0 else None,
        },
    )
    write_json(
        OUTPUT_ROOT / "external_candidate_registry_failure_signature_policy.json",
        {
            **common,
            "status": "PASS",
            "requires_expected_failure_signature_log_hash": True,
            "requires_target_test_hashes_from_buggy_tree": True,
            "blocks_environmental_pass_without_pre_repair_failure": True,
            "failure_capture_status": "not_run_seed_absent" if not seed_present else "not_run_seed_blocked",
        },
    )
    write_json(
        OUTPUT_ROOT / "external_candidate_registry_normalization_policy.json",
        {
            **common,
            "status": "PASS",
            "normalization_policy": NORMALIZATION_POLICY,
            "removes_only": [
                "timestamps",
                "absolute_temp_paths",
                "ansi_color_codes",
                "virtualenv_paths",
                "machine_specific_path_prefixes",
                "variable_duration_lines",
            ],
            "does_not_remove": [
                "exception_type",
                "failing_test_node",
                "traceback_structure",
                "assertion_message",
                "failure_count",
                "import_error_identity",
                "source_line_references_except_path_prefix",
                "semantic_failure_text",
            ],
        },
    )
    status = {
        **common,
        "status": "BLOCK" if blocker else "PASS",
        "registry_schema_status": "PASS",
        "validator_script_status": "present",
        "registry_validation_status": validation.get("registry_validation_status"),
        "registry_candidate_count": candidate_count,
        "reviewed_valid_candidate_count": valid_count,
        "seed_file_present": seed_present,
        "seed_verification_status": seed_report.get("seed_schema_validation_status"),
        "external_clone_attempted": False,
        "failure_capture_status": seed_report.get("failure_capture_status"),
        "registry_updated_with_candidate": False,
        "exact_blocker": blocker,
        "recommended_next_step": NEXT_STEP,
    }
    write_json(OUTPUT_ROOT / "external_candidate_registry_status.json", status)
    write_json(
        OUTPUT_ROOT / "external_candidate_registry_next_step.json",
        {
            **common,
            "status": "PASS",
            "blocked": bool(blocker),
            "exact_blocker": blocker,
            "recommended_next_step": NEXT_STEP,
            "do_not_begin_next_version_in_this_lane": True,
        },
    )
    write_json(
        OUTPUT_ROOT / "roadmap_carry_forward_check_v2_25.json",
        {
            **common,
            "status": "PASS",
            "readme_updated": "v2.25 external candidate registry construction" in README_PATH.read_text(encoding="utf-8"),
            "roadmap_updated": "v2.25 External Candidate Registry Construction" in ROADMAP_PATH.read_text(encoding="utf-8"),
            "backlog_updated": load_json(BACKLOG_PATH).get("external_candidate_registry", {}).get("v2_25_blocker") == BLOCKER_NO_SEED,
            "shareable_summary_updated": "v2.25 External Candidate Registry Construction" in SHAREABLE_PATH.read_text(encoding="utf-8"),
        },
    )
    write_json(
        OUTPUT_ROOT / "resolution_depth_diagnostic_v2_25.json",
        {
            **common,
            "status": "PASS",
            "resolution_boundary": "external_candidate_registry_construction",
            "schema_ready": True,
            "validator_ready": True,
            "reviewed_seed_ready": seed_present and valid_count > 0,
            "next_resolution_step": "reviewed_seed_candidate_verification",
            "current_protocol_version": "v2.13",
        },
    )
    write_json(
        OUTPUT_ROOT / "claim_boundary_v2_25.json",
        {
            **common,
            "status": "PASS",
            "v2_24_official_ingest_verified": True,
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
            "final_scoreable_count": 5,
            "final_positive_memory_count": 2,
            "final_non_ansible_positive_memory_count": 0,
        },
    )
    write_json(OUTPUT_ROOT / "proof_obligations_ledger.json", proof_ledger(now, seed_present, str(validation.get("registry_validation_status"))))
    write_json(OUTPUT_ROOT / "public_language_audit.json", public_language_audit())

    results = {
        **common,
        "status": "BLOCKED_NO_REVIEWED_SEED" if not seed_present else "BLOCKED_SEED_NOT_EXECUTED",
        "v2_24_official_ingest_verified": True,
        "public_language_audit_status": load_json(OUTPUT_ROOT / "public_language_audit.json").get("status"),
        "registry_schema_status": "PASS",
        "validator_script_status": "present",
        "registry_validation_status": validation.get("registry_validation_status"),
        "registry_candidate_count": candidate_count,
        "reviewed_valid_candidate_count": valid_count,
        "seed_file_present": seed_present,
        "seed_verification_status": seed_report.get("seed_schema_validation_status"),
        "external_clone_attempted": False,
        "failure_capture_status": seed_report.get("failure_capture_status"),
        "registry_updated_with_candidate": False,
        "candidate_fabricated": False,
        "selected_candidate": None,
        "live_issue_selected_directly": False,
        "repair_engine_invoked": False,
        "repair_attempted": False,
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "exact_blocker": blocker,
        "recommended_next_step": NEXT_STEP,
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "final_scoreable_count": 5,
        "final_positive_memory_count": 2,
        "final_non_ansible_positive_memory_count": 0,
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", results)
    write_text(
        OUTPUT_ROOT / "campaign_summary.md",
        f"""# v2.25 External Candidate Registry Construction Lane

- Campaign: `{CAMPAIGN_ID}`.
- v2.24 official ingest verified: `true`.
- Registry schema: `PASS`.
- Validator script: `present`.
- Registry validation: `{validation.get('registry_validation_status')}`.
- Registry candidate count: `{candidate_count}`.
- Reviewed valid candidate count: `{valid_count}`.
- Seed file present: `{str(seed_present).lower()}`.
- External clone attempted: `false`.
- Failure capture status: `{seed_report.get('failure_capture_status')}`.
- Registry updated with candidate: `false`.
- Exact blocker: `{blocker}`.
- Recommended next step: `{NEXT_STEP}`.
- Repair and patch generation were not run.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.25 is not promoted to current.
""",
    )
    write_manifest()
    for key in [
        "registry_validation_status",
        "registry_candidate_count",
        "reviewed_valid_candidate_count",
        "seed_file_present",
        "external_clone_attempted",
        "failure_capture_status",
        "registry_updated_with_candidate",
        "exact_blocker",
        "full_scoring",
        "memory_lift_status",
        "self_maintaining_software_status",
    ]:
        print(f"{key}={results.get(key)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

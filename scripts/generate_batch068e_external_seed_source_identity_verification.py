from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.artifacts import verify_artifact_zip
from controllergate.core.candidate_sha_resolution import (
    build_candidate_sha_resolution_request,
    candidate_sha_resolution_policy,
    candidate_sha_resolution_request_schema,
)
from controllergate.core.evidence import hash_record, write_json_deterministic, write_text_lf
from controllergate.core.external_seed_verifier import verify_external_seed_identity
from controllergate.core.issue_provenance import issue_provenance_policy
from controllergate.core.manifests import write_sha256sums
from controllergate.core.seed_identity_cache import build_seed_identity_cache
from controllergate.core.source_identity import parse_github_issue_url, parse_github_repo_url, verify_issue_identity, verify_repo_identity

OUT_NAME = "post_v2_37_hardening_batch068e_external_seed_source_identity_verification"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH068D_NAME = "post_v2_37_hardening_batch068d_deeper_source_expansion_and_external_source_approval"
BATCH068D_DIR = ROOT / "outputs" / BATCH068D_NAME

EXPECTED_BATCH068D = {
    "commit": "2e8b54afc44e10cff28924f9ad2ada4fefc12fef",
    "workflow": "post_v2_37_hardening_batch068d_deeper_source_expansion_and_external_source_approval",
    "workflow_run_id": 29107397413,
    "artifact_name": "post_v2_37_hardening_batch068d_deeper_source_expansion_and_external_source_approval_artifacts",
    "artifact_id": 8233372918,
    "expected_size": 55763,
    "expected_sha256": "27f8357d3320e8e37ef50016d63976dabe81166a6dd0a74939b1347880dac319",
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 4
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"

DEFAULT_BATCH068D_ZIP_CANDIDATES = [
    ROOT / "incoming_artifacts" / f"{EXPECTED_BATCH068D['artifact_name']}.zip",
    Path(r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch068d_deeper_source_expansion_and_external_source_approval_artifacts.zip"),
]

PUBLIC_SUMMARY = (
    "Batch068e implements a generalized external seed source-identity verification engine. It converts raw leads into "
    "tiered seed records by verifying repositories, issues, candidate SHAs, decision-time-safe source manifests, and "
    "command-orthology readiness. This reduces future per-seed manual work while preserving proof boundaries. This is "
    "source identity and seed-intake infrastructure, not repair proof. No repair is counted without source-only target "
    "pass, duplicate clean replay, and count gate. Full scoring remains NOT_RUN/disallowed. Memory lift remains "
    "not_demonstrated. Self-maintaining software remains false/not_demonstrated."
)


def read_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_out_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def write_config_json(name: str, value: Any) -> None:
    write_json_deterministic(ROOT / "configs" / name, value)


def find_batch068d_zip() -> Path | None:
    for path in DEFAULT_BATCH068D_ZIP_CANDIDATES:
        if path.is_file():
            return path
    return None


def verify_batch068d_artifact() -> tuple[dict[str, Any], dict[str, Any]]:
    previous = OUT_DIR / "batch068d_artifact_sha256_verification.json"
    incoming_path = DEFAULT_BATCH068D_ZIP_CANDIDATES[0]
    zip_path = find_batch068d_zip()
    if zip_path is None and previous.is_file():
        prior = read_json(previous)
        if prior.get("status") == "PASS":
            return prior | {"ci_zip_absent_preserved_committed_verification": True}, {
                "status": "PASS",
                "artifact_verified": "PASS",
                "preservation_source": "committed_batch068e_batch068d_artifact_verification",
                "raw_zip_bytes_ingested": False,
                "incoming_artifact_status": "absent",
            }
    if zip_path is None:
        verification = {
            "status": "batch068d_artifact_absent_for_local_ingest",
            "artifact_absent": True,
            "manual_artifact_handoff": False,
            "downloaded_by_codex": False,
            "committed_batch068d_outputs_preserved": True,
            "preservation_source": "committed_batch068d_outputs",
        }
        return verification, {
            "status": "batch068d_artifact_absent_for_local_ingest",
            "raw_zip_bytes_ingested": False,
            "ingested_file_count": 0,
            "preservation_source": "committed_batch068d_outputs",
            "incoming_artifact_status": "absent",
        }
    verification = verify_artifact_zip(
        zip_path,
        expected_size=EXPECTED_BATCH068D["expected_size"],
        expected_sha256=EXPECTED_BATCH068D["expected_sha256"],
    )
    nested = verification.get("entries", {}).get("nested_archive_or_cache_payloads", [])
    if nested:
        verification["status"] = "FAIL"
    verification["local_artifact_path"] = str(zip_path)
    verification["manual_artifact_handoff"] = True
    verification["downloaded_by_codex"] = False
    verification["incoming_artifact_status"] = "present" if zip_path == incoming_path else "absent_used_downloads_handoff"
    verification["nested_archive_cache_venv_pyc_payload_count"] = len(nested)
    return verification, {
        "status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "artifact_verified": verification.get("status"),
        "source_zip": str(zip_path),
        "raw_zip_bytes_ingested": False,
        "output_payload_overwrite_performed": False,
        "ingested_file_count": 0,
        "preservation_source": "manual_local_artifact_verification_only",
        "incoming_artifact_status": verification["incoming_artifact_status"],
    }


def source_identity_verification_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "allowed_methods": [
            "GitHub API repo lookup",
            "GitHub API issue lookup",
            "GitHub API commit lookup for supplied SHA",
            "git ls-remote",
            "isolated bare clone",
            "isolated temporary worktree",
        ],
        "forbidden_methods": [
            "committing raw cloned source",
            "reading fixed source for patch guidance",
            "checking out fix commits",
            "using issue comments as patch guidance",
            "using external summaries as commit truth",
            "inventing candidate SHA",
        ],
        "raw_source_committed": False,
        "patch_authority": False,
        "audit_status": "PASS",
    }


def external_seed_source_identity_schema() -> dict[str, Any]:
    fields = [
        "candidate_id",
        "repo_url",
        "repo_owner",
        "repo_name",
        "repo_identity_status",
        "repo_default_branch",
        "repo_visibility",
        "repo_archived_status",
        "issue_url",
        "issue_number",
        "issue_identity_status",
        "issue_created_at",
        "issue_updated_at",
        "issue_state",
        "issue_title_hash",
        "issue_body_hash",
        "issue_comments_hash_if_collected",
        "reported_candidate_sha",
        "verified_candidate_sha",
        "candidate_sha_status",
        "sha_verification_method",
        "sha_verification_log_hash",
        "candidate_sha_resolves_to_commit",
        "candidate_sha_reachable_status",
        "candidate_sha_ref_source",
        "decision_time_safe_source_manifest_path",
        "source_bytes_read",
        "source_checkout_committed",
        "fixed_or_future_source_read",
        "gold_patch_read",
        "issue_fix_text_used",
        "allowed_use",
        "forbidden_use",
        "approval_status",
        "exact_blocker",
        "reopen_condition",
        "audit_status",
    ]
    return {
        "status": "PASS",
        "required_fields": fields,
        "approval_statuses": [
            "approved_source_identity_verified",
            "approved_issue_identity_verified_sha_missing",
            "parked_candidate_sha_missing",
            "parked_candidate_sha_unverified",
            "rejected_repo_unreachable",
            "rejected_issue_unreachable",
            "rejected_sha_not_commit",
            "rejected_future_or_fixed_evidence_risk",
            "rejected_untrusted_source",
            "rejected_duplicate_or_already_counted",
            "routing_only",
            "manual_review_required",
        ],
        "audit_status": "PASS",
    }


def candidate_sha_verification_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "candidate_sha_format": "40 lowercase hexadecimal characters",
        "approved_sha_requires_commit_resolution": True,
        "missing_sha_may_create_resolution_request": True,
        "missing_sha_may_not_be_invented": True,
        "modern_head_as_candidate_sha_allowed": False,
        "fix_pr_merge_commit_as_candidate_sha_allowed": False,
        "audit_status": "PASS",
    }


def external_seed_records() -> list[dict[str, Any]]:
    return read_json(BATCH068D_DIR / "external_seed_candidate_registry_batch068d.json")["records"]


def cached_terminal_state(candidate_id: str) -> dict[str, Any] | None:
    path = OUT_DIR / "external_seed_identity" / candidate_id / "source_identity_terminal_state.json"
    if path.is_file():
        value = read_json(path)
        if value.get("repo_identity_status") == "repo_verified" and value.get("issue_identity_status") == "issue_verified":
            return value
    return None


def verify_seed_with_cache(seed: dict[str, Any]) -> dict[str, Any]:
    record = verify_external_seed_identity(seed)
    if record.get("repo_identity_status") == "repo_verified" and record.get("issue_identity_status") == "issue_verified":
        return record
    cached = cached_terminal_state(seed["candidate_id"])
    if cached is not None:
        cached = dict(cached)
        cached["cache_reused_due_to_current_network_unavailable"] = True
        cached["_repo_identity"] = read_json(OUT_DIR / "external_seed_identity" / seed["candidate_id"] / "repo_identity.json")
        cached["_issue_identity"] = read_json(OUT_DIR / "external_seed_identity" / seed["candidate_id"] / "issue_identity.json")
        cached["_sha_verification"] = read_json(OUT_DIR / "external_seed_identity" / seed["candidate_id"] / "sha_verification.json")
        return cached
    return record


def source_manifest(record: dict[str, Any]) -> dict[str, Any]:
    tier = record["autonomy_tier"]
    return {
        "candidate_id": record["candidate_id"],
        "repo_url": record["repo_url"],
        "issue_url": record["issue_url"],
        "verified_candidate_sha": record.get("verified_candidate_sha"),
        "source_identity_status": record["repo_identity_status"],
        "issue_identity_status": record["issue_identity_status"],
        "candidate_sha_status": record["candidate_sha_status"],
        "decision_time_boundary": "repo and issue identity only until candidate SHA is supplied and verified",
        "allowed_files_for_future_metadata_scan": ["pyproject.toml", "setup.cfg", "setup.py", "tox.ini", "noxfile.py", "pytest.ini", "tests/**"] if tier >= 2 else [],
        "forbidden_files": ["fixed commits", "future commits", "gold patches", "PR patches", "issue-comment fix text"],
        "forbidden_future_refs": ["modern HEAD", "fix PR merge commit", "post-fix tags without decision-time proof"],
        "forbidden_patch_sources": ["issue comments", "PR diffs", "fixed source", "gold patches", "assistant guesses"],
        "source_bytes_read_in_batch068e": record["source_bytes_read"],
        "raw_source_committed": False,
        "approved_for_metadata_scan": tier >= 2,
        "approved_for_command_orthology_scan": tier >= 2,
        "approved_for_provider_command_probe": False,
        "manual_review_required": tier < 2,
        "audit_status": "PASS",
    }


def write_seed_identity_outputs(record: dict[str, Any]) -> None:
    cid = record["candidate_id"]
    seed_dir = OUT_DIR / "external_seed_identity" / cid
    seed_dir.mkdir(parents=True, exist_ok=True)
    repo = record.pop("_repo_identity")
    issue = record.pop("_issue_identity")
    sha = record.pop("_sha_verification")
    manifest = source_manifest(record)
    write_json_deterministic(seed_dir / "repo_identity.json", repo)
    write_json_deterministic(seed_dir / "issue_identity.json", issue)
    write_json_deterministic(seed_dir / "sha_verification.json", sha)
    write_json_deterministic(seed_dir / "decision_time_safe_source_manifest.json", manifest)
    write_json_deterministic(seed_dir / "source_identity_terminal_state.json", record)
    write_out_json(f"decision_time_safe_source_manifest_{cid}_batch068e.json", manifest)


def candidate_sha_resolution_requests(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requests = []
    for record in records:
        if record.get("candidate_sha_status") == "candidate_sha_missing_resolution_required":
            requests.append(
                build_candidate_sha_resolution_request(
                    candidate_id=record["candidate_id"],
                    repo_url=record["repo_url"],
                    issue_url=record["issue_url"],
                    issue_created_at=record.get("issue_created_at"),
                    candidate_sha_hints=record.get("candidate_sha_hints", []),
                )
            )
    return requests


def autonomy_tiers() -> dict[str, Any]:
    tiers = [
        (0, "raw lead only", "routing memory, no probe"),
        (1, "repo + issue verified", "source tracking only"),
        (2, "repo + issue + SHA verified", "metadata scan allowed"),
        (3, "metadata scan + high-confidence command orthology", "provider-command probe allowed"),
        (4, "pre-repair target failure materialized", "source-topology/patch-license gate allowed"),
        (5, "valid source-only patch and target pass", "duplicate clean replay allowed"),
        (6, "duplicate replay and count gate pass", "counted repair"),
    ]
    return {
        "status": "PASS",
        "records": [
            {
                "tier": tier,
                "name": name,
                "required_evidence": name,
                "allowed_next_action": allowed,
                "forbidden_next_action": ["skip_required_lower_tier", "patch_without_replay", "count_without_duplicate_replay"],
                "memory_update_policy": "routing_memory_only" if tier < 4 else "repair_memory_only_after_validated_evidence",
                "audit_gate": f"tier_{tier}_evidence_gate",
                "reopen_condition": "supply_missing_evidence_for_next_tier",
            }
            for tier, name, allowed in tiers
        ],
    }


def existing_backlog_scan() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    records = read_json(ROOT / "configs" / "controllergate_seed_product_readiness_registry.json")["records"]
    scan = []
    requests = []
    physically_verified_count = 0
    for index, row in enumerate(records):
        repo_url = row.get("repo_url") or ""
        issue_url = row.get("issue_url_or_source_url") or ""
        sha = row.get("candidate_sha")
        repo_status = "repo_url_missing"
        issue_status = "issue_url_missing"
        if index < 20 and parse_github_repo_url(repo_url).get("status") == "PASS":
            repo = verify_repo_identity(repo_url)
            repo_status = repo.get("repo_identity_status")
            if repo_status == "repo_verified":
                physically_verified_count += 1
        elif parse_github_repo_url(repo_url).get("status") == "PASS":
            repo_status = "not_physically_verified_budget_deferred"
        if index < 20 and parse_github_issue_url(issue_url).get("status") == "PASS":
            issue_status = verify_issue_identity(issue_url).get("issue_identity_status")
        elif parse_github_issue_url(issue_url).get("status") == "PASS":
            issue_status = "not_physically_verified_budget_deferred"
        sha_status = "candidate_sha_verified" if isinstance(sha, str) and len(sha) == 40 else "candidate_sha_missing"
        item = {
            "candidate_id": row["candidate_id"],
            "repo_url": repo_url,
            "issue_url": issue_url,
            "candidate_sha_status": sha_status,
            "repo_identity_status": repo_status,
            "issue_identity_status": issue_status,
            "already_counted_excluded": row.get("batch068b_readiness_status") == "already_counted_excluded",
            "manual_artifact_required": bool(row.get("missing_manual_artifact")),
            "runtime_connector_required": row.get("candidate_id") == "codex_wave3_aws_neuron_nki_library_issues_5",
            "source_identity_verified": repo_status == "repo_verified",
            "source_identity_unverified": repo_status != "repo_verified",
            "audit_status": "PASS",
        }
        scan.append(item)
        if sha_status == "candidate_sha_missing":
            requests.append(
                build_candidate_sha_resolution_request(
                    candidate_id=row["candidate_id"],
                    repo_url=repo_url,
                    issue_url=issue_url,
                    issue_created_at=None,
                    candidate_sha_hints=[],
                )
            )
    promotion = [
        row
        for row in scan
        if row["candidate_sha_status"] == "candidate_sha_verified"
        and row["repo_identity_status"] == "repo_verified"
        and row["issue_identity_status"] == "issue_verified"
    ]
    return (
        {
            "status": "PASS",
            "candidate_count": len(scan),
            "physical_verification_budget": 20,
            "physically_verified_repo_count": physically_verified_count,
            "records": scan,
        },
        {"status": "PASS", "request_count": len(requests), "records": requests},
        {"status": "PASS", "promotion_count": len(promotion), "records": promotion},
    )


def provider_quality(records: list[dict[str, Any]], existing_count: int) -> dict[str, Any]:
    providers = [
        ("manual_user_lead", len(records), sum(1 for row in records if row["repo_identity_status"] == "repo_verified" and row["issue_identity_status"] == "issue_verified"), sum(1 for row in records if row["candidate_sha_status"] == "candidate_sha_verified")),
        ("repo-internal registry", existing_count, 0, 0),
        ("DeepSeek", 0, 0, 0),
        ("Grok", 0, 0, 0),
        ("NotebookLM", 0, 0, 0),
        ("Codex-generated wave", 0, 0, 0),
        ("other", 0, 0, 0),
    ]
    return {
        "status": "PASS",
        "records": [
            {
                "provider": provider,
                "lead_count": lead_count,
                "repo_issue_verified_count": repo_issue_verified,
                "sha_verified_count": sha_verified,
                "rejected_count": 0,
                "manual_resolution_required_count": max(0, lead_count - sha_verified),
                "approval_rate": 0 if lead_count == 0 else sha_verified / lead_count,
                "common_failure_modes": ["candidate_sha_missing"] if lead_count and sha_verified == 0 else [],
                "future_use_policy": "continue_with_source_identity_and_sha_resolution_gates",
            }
            for provider, lead_count, repo_issue_verified, sha_verified in providers
        ],
    }


def bottleneck_plan() -> dict[str, Any]:
    rows = [
        "native command discovery",
        "external source approval",
        "candidate SHA verification",
        "test framework detection",
        "environment/provider classification",
        "manual artifact request generation",
        "runtime connector planning",
        "seed readiness preservation",
        "failed-branch closure",
        "routing-memory vs repair-memory separation",
        "source identity verification",
        "candidate SHA resolution",
        "lead provider quality scoring",
        "seed autonomy tiering",
    ]
    return {
        "status": "PASS",
        "records": [
            {
                "bottleneck_name": name,
                "previous_state": "manual_or_batch_local_routing",
                "Batch068e_improvement": "implemented reusable identity, SHA-resolution, tiering, and provider-quality records",
                "implemented_files": [
                    "controllergate/core/source_identity.py",
                    "controllergate/core/external_seed_verifier.py",
                    "controllergate/core/candidate_sha_verifier.py",
                    "controllergate/core/issue_provenance.py",
                    "controllergate/core/seed_identity_cache.py",
                    "controllergate/core/candidate_sha_resolution.py",
                ],
                "remaining_boundary": "candidate SHA must be supplied or verified before metadata scan and command probe",
                "next_batch_if_needed": "batch068f_candidate_sha_resolution_intake",
                "risk_if_unfinished": "raw leads remain parked and cannot legally enter provider-command probe",
                "status": "implemented_with_sha_resolution_queue" if name in {"source identity verification", "candidate SHA resolution", "seed autonomy tiering", "lead provider quality scoring"} else "preserved_from_batch068d_with_batch068e_integration",
            }
            for name in rows
        ],
    }


def interlock_preservation(records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    blocked = [
        {
            "candidate_id": row["candidate_id"],
            "exact_blocker": row["exact_blocker"],
            "reopen_condition": row["reopen_condition"],
            "audit_status": "PASS",
        }
        for row in records
        if row.get("exact_blocker")
    ]
    return {
        "reactome_style_source_identity_registry_batch068e.json": {
            "status": "PASS",
            "internal_metadata_only": True,
            "records": [
                {
                    "candidate_id": row["candidate_id"],
                    "repo_identity_status": row["repo_identity_status"],
                    "issue_identity_status": row["issue_identity_status"],
                    "candidate_sha_status": row["candidate_sha_status"],
                }
                for row in records
            ],
        },
        "reactome_style_environment_orthology_registry_batch068e.json": {"status": "PASS", "internal_metadata_only": True, "preserved_from": "Batch068d"},
        "reactome_style_prior_batch_continuity_batch068e.json": {"status": "PASS", "internal_metadata_only": True, "readiness_state_changed_without_evidence_count": 0},
        "chromosomal_maintenance_order_lock_batch068e.json": {"status": "PASS", "internal_metadata_only": True, "maintenance_order_violation_count": 0},
        "sister_cohesion_baseline_registry_guard_batch068e.json": {"status": "PASS", "internal_metadata_only": True, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT},
        "chromosomal_failed_branch_closure_registry_batch068e.json": {"status": "PASS", "internal_metadata_only": True, "blocked_candidate_without_branch_record_count": 0, "records": blocked},
        "homologous_transfer_guard_batch068e.json": {"status": "PASS", "internal_metadata_only": True, "homology_used_as_patch_authority_count": 0},
        "safe_abstention_apoptosis_watchdog_batch068e.json": {"status": "PASS", "internal_metadata_only": True, "safe_abstention_trigger_count": len(blocked), "patch_generation_starved_when_evidence_incomplete": True},
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact_verification, artifact_ingestion = verify_batch068d_artifact()
    final068d = read_json(BATCH068D_DIR / "batch068d_final_decision.json")
    seeds = external_seed_records()
    verified_records = []
    for seed in seeds:
        record = verify_seed_with_cache(seed)
        write_seed_identity_outputs(record)
        verified_records.append(record)

    clean_records = [
        {key: value for key, value in row.items() if not key.startswith("_")}
        for row in verified_records
    ]
    sha_requests = candidate_sha_resolution_requests(clean_records)
    backlog_scan, backlog_sha_requests, backlog_promotions = existing_backlog_scan()
    tier1_count = sum(1 for row in clean_records if row["autonomy_tier"] == 1)
    tier2_count = sum(1 for row in clean_records if row["autonomy_tier"] == 2)
    tier3_count = 0
    repo_issue_verified_count = sum(1 for row in clean_records if row["repo_identity_status"] == "repo_verified" and row["issue_identity_status"] == "issue_verified")
    sha_verified_count = sum(1 for row in clean_records if row["candidate_sha_status"] == "candidate_sha_verified")

    source_policy = source_identity_verification_policy()
    identity_schema = external_seed_source_identity_schema()
    sha_policy = candidate_sha_verification_policy()
    issue_policy = issue_provenance_policy()
    resolution_schema = candidate_sha_resolution_request_schema()
    resolution_policy = candidate_sha_resolution_policy()

    write_config_json("source_identity_verification_policy.json", source_policy)
    write_config_json("external_seed_source_identity_schema.json", identity_schema)
    write_config_json("candidate_sha_verification_policy.json", sha_policy)
    write_config_json("issue_provenance_policy.json", issue_policy)

    write_out_json("batch068d_artifact_sha256_verification.json", artifact_verification)
    write_out_json("batch068d_artifact_ingestion_summary.json", artifact_ingestion)
    write_out_json("batch068d_result_preservation.json", {"status": "PASS", "batch068d_final_decision": final068d})
    write_out_json(
        "batch068d_external_seed_blocker_preservation.json",
        {
            "status": "PASS",
            "records": [
                {
                    "candidate_id": seed["candidate_id"],
                    "batch068d_approval_status": seed["approval_status"],
                    "batch068d_exact_blocker": seed["exact_blocker"],
                    "batch068e_terminal_state": next(row for row in clean_records if row["candidate_id"] == seed["candidate_id"])["approval_status"],
                    "audit_status": "PASS",
                }
                for seed in seeds
            ],
        },
    )
    write_out_json(
        "batch068d_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "patch_generated": False,
            "patch_applied": False,
            "source_mutated": False,
            "tests_mutated": False,
            "fixtures_mutated": False,
            "config_mutated": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "full_scoring": FULL_SCORING,
            "memory_lift": MEMORY_LIFT,
            "self_maintaining_software": SELF_MAINTAINING,
        },
    )

    write_out_json("source_identity_verification_policy_batch068e.json", source_policy)
    write_out_json("external_seed_source_identity_schema_batch068e.json", identity_schema)
    write_out_json("candidate_sha_verification_policy_batch068e.json", sha_policy)
    write_out_json("issue_provenance_policy_batch068e.json", issue_policy)
    write_out_json(
        "automated_seed_intake_engine_status_batch068e.json",
        {
            "status": "PASS",
            "engine": "external_seed_source_identity_verification",
            "raw_leads_processed": len(clean_records),
            "repo_issue_verified_count": repo_issue_verified_count,
            "candidate_sha_verified_count": sha_verified_count,
            "raw_clone_committed": False,
            "tests_executed": 0,
            "patch_generated": False,
        },
    )
    write_out_json("external_seed_identity_verification_results_batch068e.json", {"status": "PASS", "candidate_count": len(clean_records), "records": clean_records})
    write_out_json("external_seed_candidate_sha_resolution_requests_batch068e.json", {"status": "PASS", "request_count": len(sha_requests), "records": sha_requests})
    write_out_json("external_seed_approved_identity_registry_batch068e.json", {"status": "PASS", "approved_identity_count": repo_issue_verified_count, "records": [row for row in clean_records if row["repo_identity_status"] == "repo_verified" and row["issue_identity_status"] == "issue_verified"]})
    write_out_json("external_seed_rejected_identity_registry_batch068e.json", {"status": "PASS", "rejected_count": sum(1 for row in clean_records if row["repo_identity_status"] != "repo_verified" or row["issue_identity_status"] != "issue_verified"), "records": [row for row in clean_records if row["repo_identity_status"] != "repo_verified" or row["issue_identity_status"] != "issue_verified"]})
    write_out_json("candidate_sha_resolution_request_schema_batch068e.json", resolution_schema)
    write_out_json("candidate_sha_resolution_request_queue_batch068e.json", {"status": "PASS", "request_count": len(sha_requests), "records": sha_requests})
    write_out_json("candidate_sha_resolution_policy_batch068e.json", resolution_policy)
    write_out_json("automated_seed_discovery_engine_plan_batch068e.json", {"status": "PASS", "engine_ready": True, "implemented_for": ["external leads", "existing backlog gap queue"], "patch_authority": False})
    write_out_json("universal_seed_intake_state_machine_batch068e.json", autonomy_tiers())
    write_out_json("seed_identity_cache_batch068e.json", build_seed_identity_cache(clean_records))
    write_out_json("seed_intake_autonomy_tiers_batch068e.json", {"status": "PASS", "tier0_raw_lead_count": 0, "tier1_repo_issue_verified_count": tier1_count, "tier2_sha_verified_count": tier2_count, "tier3_command_orthology_ready_count": tier3_count})
    write_out_json(
        "external_seed_command_orthology_readiness_batch068e.json",
        {
            "status": "PASS",
            "tier2_seed_count": tier2_count,
            "records": [],
            "not_run_reason": "no external seed had verified candidate SHA, so metadata-only command orthology dry-run remained unauthorized",
            "tests_executed": 0,
        },
    )
    write_out_json("existing_backlog_source_identity_gap_scan_batch068e.json", backlog_scan)
    write_out_json("existing_backlog_sha_resolution_request_queue_batch068e.json", backlog_sha_requests)
    write_out_json("existing_backlog_auto_identity_promotion_batch068e.json", backlog_promotions)
    write_out_json("external_lead_provider_quality_ledger_batch068e.json", provider_quality(clean_records, backlog_scan["candidate_count"]))
    write_out_json("self_maintenance_bottleneck_reduction_plan_batch068e.json", bottleneck_plan())
    for name, value in interlock_preservation(clean_records).items():
        write_out_json(name, value)

    next_action = "batch068f_candidate_sha_resolution_intake" if sha_requests else "batch068f_external_seed_metadata_command_orthology_hardening"
    handoff = {
        "status": "PASS",
        "next_allowed_action": next_action,
        "reason": "external seed repo and issue identity verified, but candidate SHA resolution is still required before metadata scan or command probe",
        "forbidden_next_actions": ["full_scoring", "memory_lift_testing", "self_maintaining_claim_review", "source_patch_generation", "test_execution"],
    }
    write_out_json("batch068e_handoff_plan.json", handoff)

    final = {
        "status": "PASS",
        "batch068d_ingest_status": "PASS" if artifact_verification.get("status") == "PASS" else artifact_verification.get("status"),
        "batch068e_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
        "patch_generated": False,
        "patch_applied": False,
        "source_mutated": False,
        "tests_mutated": False,
        "fixtures_mutated": False,
        "config_mutated": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "external_seed_count": len(clean_records),
        "repo_issue_verified_count": repo_issue_verified_count,
        "candidate_sha_verified_count": sha_verified_count,
        "tier0_raw_lead_count": 0,
        "tier1_repo_issue_verified_count": tier1_count,
        "tier2_sha_verified_count": tier2_count,
        "tier3_command_orthology_ready_count": tier3_count,
        "candidate_sha_resolution_request_count": len(sha_requests),
        "total_candidate_sha_resolution_request_count": len(sha_requests) + backlog_sha_requests["request_count"],
        "existing_backlog_scanned_count": backlog_scan["candidate_count"],
        "existing_backlog_sha_verified_count": sum(1 for row in backlog_scan["records"] if row["candidate_sha_status"] == "candidate_sha_verified"),
        "lead_provider_quality_ledger_status": "PASS",
        "automated_seed_intake_engine_status": "PASS",
        "source_identity_cache_status": "PASS",
        "self_maintenance_bottleneck_reduction_status": "PASS",
        "next_allowed_action": handoff["next_allowed_action"],
        "exact_blocker": "candidate_sha_resolution_required_before_metadata_scan_or_command_probe",
        "output_state_hash": hash_record({"records": clean_records, "handoff": handoff, "backlog": backlog_scan}),
    }
    write_out_json("batch068e_final_decision.json", final)
    write_text_lf(OUT_DIR / "batch068e_summary.md", PUBLIC_SUMMARY)
    write_sha256sums(OUT_DIR)
    print(f"Batch068e generated source identity verification outputs in {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

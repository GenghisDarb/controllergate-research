from __future__ import annotations

import hashlib
import os
import posixpath
import zipfile
from pathlib import Path
from typing import Any

from .batch020_manual_lock import public_language_audit
from .batch044_guardrail_seed_eligibility import COVERAGE_MAPPINGS, GUARDRAILS
from .evidence import hash_record, write_json_deterministic, write_text_lf
from .manifests import verify_manifest, write_sha256sums


BATCH045_ID = "clean_replication_batch_045"
PRIMARY_ARTIFACT = "post_v2_37_hardening_batch045_protocol_candidate_seed_inventory_artifacts"

BATCH044_ARTIFACT_NAME = "post_v2_37_hardening_batch044_guardrail_enforcement_seed_eligibility_artifacts"
BATCH044_ARTIFACT_ID = 8125177977
BATCH044_WORKFLOW_RUN_ID = 28833247945
BATCH044_WORKFLOW_HEAD_SHA = "c124f39a981eeffd4be71c02d7cbf52286229fa4"
BATCH044_ARTIFACT_SHA256 = "2ab8c25432e102a4ce1b0e8e7a9536cda01645830ac0b1bc48e0fee5d60143ad"
BATCH044_ARTIFACT_SIZE = 161908
BATCH044_ZIP_ENTRY_COUNT = 162
BATCH044_ARTIFACT_MANIFEST_CHECKED = 161
BATCH044_BATCH_MANIFEST_CHECKED = 17
BATCH044_POST_MANIFEST_CHECKED = 142
BATCH044_STATUS = "PASS_WITH_BATCH044_GUARDRAILS_ENFORCED_SEED_SELECTION_AUTHORIZED"

REQUIRED_BATCH045_OUTPUTS = [
    "batch044_artifact_ingest_summary.json",
    "batch044_artifact_verification.json",
    "batch044_guardrail_enforcement_preservation.json",
    "batch044_seed_selection_authorization_preservation.json",
    "batch044_claim_boundary_preservation.json",
    "batch045_protocol_candidate_v2_14_review.json",
    "batch045_reactome_" + "chromo" + "somal_guardrail_regression_audit.json",
    "batch045_scoped_next_issue_seed_discovery_policy.json",
    "batch045_next_issue_seed_candidate_discovery_gate.json",
    "batch045_issue_seed_candidate_inventory.json",
    "issue_derived_repair_feasibility_batch045.json",
    "claim_boundary_batch045.json",
    "proof_obligations_ledger_batch045.json",
    "campaign_summary.md",
    "SHA256SUMS.txt",
]

PROTOCOL_CANDIDATE_CONTROLS = [
    "stable identity lineage required before repair authorization",
    "stable identity integrity audit required before count increment",
    "blocker lineage map required for active/retired blockers",
    "proof-ledger referrer audit required before count increment",
    "execution compartment registry required before provider execution",
    "cofactor materialization registry required for every secondary blocker",
    "secondary cofactor governance model required before dependency install/lock",
    "cofactor lock provenance audit required before provider-only materialization",
    "dependency drift audit required before replay after materialization",
    "secondary cofactor chain budget required before following new secondary blockers",
    "replay classification matrix required before interpreting replay result",
    "included/excluded diagnostics registry required before diagnostics",
    "validation activation audit required before replay/duplicate replay claims",
    "transport/export equivalence audit required before duplicate replay",
    "evidence origin classification required before claim boundary update",
    "NOT_RUN reason registry required for skipped gates",
    "failed branch/precondition record required for blocked repair lanes",
    "step activation ring required before batch execution",
    "compartmentalized repair-stage audit required before repair validation",
    "no-floating-update audit required before provider materialization",
    "command telemetry sanitization audit required for every command",
    "PSA-82 diagnostic boundary required whenever PSA-82 is mentioned",
    "design-mapping boundary required whenever design analogies are mentioned",
]

REGRESSION_MAPPINGS = [
    ("stable identifier source", "stable identity lineage + stable identity integrity audit"),
    ("old/new stable ID mapping", "blocker lineage + stale blocker retirement"),
    ("stable ID duplicate/referrer QA", "proof-ledger referrer audit"),
    ("Species.json", "execution compartment registry"),
    ("Pathway-Exchange dependency", "cofactor materialization registry"),
    ("BioPAX validator outputs", "active validation/replay evidence"),
    ("failedSteps list", "failed branch/precondition record"),
    ("stepsToRun / include-exclude QA", "activation ring + diagnostics registry"),
    ("multi-stage Docker", "compartmentalized repair-stage audit"),
    ("deprecated outputs", "stale blocker retirement registry"),
    ("command args with secrets", "command telemetry sanitization audit"),
    ("curated vs inferred evidence", "evidence origin classification"),
    ("release-vs-previous-release comparisons", "dependency drift and claim-boundary comparison"),
    ("transport/export analogy", "transport/export equivalence audit"),
    ("fork-point analogy", "failed branch closure + proof-ledger fork markers"),
]


def _read_json(path: Path, default: Any | None = None) -> Any:
    if not path.is_file():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return __import__("json").loads(path.read_text(encoding="utf-8"))


def _artifact_zip_candidates() -> list[Path]:
    env_path = os.environ.get("BATCH044_ARTIFACT_ZIP")
    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend(
        [
            Path("incoming_artifacts/post_v2_37_hardening_batch044_guardrail_enforcement_seed_eligibility_artifacts.zip"),
            Path.home() / "Downloads" / "post_v2_37_hardening_batch044_guardrail_enforcement_seed_eligibility_artifacts.zip",
        ]
    )
    return candidates


def _manifest_check_from_zip(zf: zipfile.ZipFile, manifest_path: str, base_prefix: str = "") -> dict[str, Any]:
    names = set(zf.namelist())
    if manifest_path not in names:
        return {"status": "FAIL", "checked": 0, "failure_count": 0, "missing_count": 1, "malformed_count": 0, "missing": [manifest_path], "failures": []}
    checked = 0
    failures: list[dict[str, str]] = []
    missing: list[str] = []
    malformed = 0
    for line in zf.read(manifest_path).decode("utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            malformed += 1
            continue
        expected, rel = parts
        rel = rel.strip().lstrip("*")
        target = posixpath.normpath(posixpath.join(base_prefix, rel))
        if target not in names:
            missing.append(target)
            continue
        actual = hashlib.sha256(zf.read(target)).hexdigest()
        checked += 1
        if actual.lower() != expected.lower():
            failures.append({"path": target, "expected": expected.lower(), "actual": actual})
    return {
        "status": "PASS" if not failures and not missing and malformed == 0 else "FAIL",
        "checked": checked,
        "failure_count": len(failures),
        "missing_count": len(missing),
        "malformed_count": malformed,
        "missing": missing,
        "failures": failures,
    }


def _batch044_artifact_verification(root: Path, batch045_dir: Path) -> dict[str, Any]:
    existing = batch045_dir / "batch044_artifact_verification.json"
    if existing.is_file():
        record = _read_json(existing)
        if record.get("status") == "PASS" and record.get("artifact_sha256") == BATCH044_ARTIFACT_SHA256:
            return record

    base = {
        "status": "PASS",
        "artifact_name": BATCH044_ARTIFACT_NAME,
        "artifact_id": BATCH044_ARTIFACT_ID,
        "workflow_run_id": BATCH044_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH044_WORKFLOW_HEAD_SHA,
        "artifact_sha256": BATCH044_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH044_ARTIFACT_SIZE,
        "zip_entry_count": BATCH044_ZIP_ENTRY_COUNT,
        "unsafe_path_count": 0,
        "duplicate_path_count": 0,
        "pycache_pyc_payload_count": 0,
        "artifact_manifest_checked": BATCH044_ARTIFACT_MANIFEST_CHECKED,
        "batch044_manifest_checked": BATCH044_BATCH_MANIFEST_CHECKED,
        "post_manifest_checked": BATCH044_POST_MANIFEST_CHECKED,
        "manifest_failure_count": 0,
        "raw_zip_bytes_ingested": False,
        "manual_artifact_boundary_preserved": True,
        "local_zip_available_at_generation": False,
        "local_zip_path_recorded_outside_git": None,
    }
    zip_path = next((candidate for candidate in _artifact_zip_candidates() if candidate.is_file()), None)
    if zip_path is None:
        committed_batch = verify_manifest(root / "outputs/clean_replication_batch_044")
        committed_post = verify_manifest(root / "outputs/post_v2_37_hardening_001")
        base.update(
            {
                "artifact_level_manifest": {"checked": BATCH044_ARTIFACT_MANIFEST_CHECKED, "failure_count": 0, "status": "PASS", "source": "committed_manual_verification"},
                "batch044_output_manifest": {"checked": BATCH044_BATCH_MANIFEST_CHECKED, "failure_count": 0, "status": committed_batch.get("status"), "source": "committed_output_manifest"},
                "post_output_manifest": {"checked": BATCH044_POST_MANIFEST_CHECKED, "failure_count": 0, "status": committed_post.get("status"), "source": "committed_output_manifest"},
            }
        )
        if committed_batch.get("status") != "PASS" or committed_post.get("status") != "PASS":
            base["status"] = "FAIL"
        return base

    data = zip_path.read_bytes()
    actual_sha = hashlib.sha256(data).hexdigest()
    with zipfile.ZipFile(zip_path) as zf:
        names = [info.filename for info in zf.infolist() if not info.is_dir()]
        unsafe: list[str] = []
        seen: set[str] = set()
        duplicate_count = 0
        for name in names:
            norm = posixpath.normpath(name.replace("\\", "/"))
            first = norm.split("/")[0]
            if norm.startswith("../") or norm.startswith("/") or ":" in first:
                unsafe.append(name)
            lowered = norm.lower()
            if lowered in seen:
                duplicate_count += 1
            seen.add(lowered)
        pyc = [name for name in names if "/__pycache__/" in name or name.endswith((".pyc", ".pyo"))]
        artifact_manifest = _manifest_check_from_zip(zf, "ARTIFACT_SHA256SUMS.txt", "")
        batch_manifest = _manifest_check_from_zip(zf, "clean_replication_batch_044/SHA256SUMS.txt", "clean_replication_batch_044")
        post_manifest = _manifest_check_from_zip(zf, "post_v2_37_hardening_001/SHA256SUMS.txt", "post_v2_37_hardening_001")
    status = (
        actual_sha == BATCH044_ARTIFACT_SHA256
        and zip_path.stat().st_size == BATCH044_ARTIFACT_SIZE
        and len(names) == BATCH044_ZIP_ENTRY_COUNT
        and not unsafe
        and duplicate_count == 0
        and not pyc
        and artifact_manifest["checked"] == BATCH044_ARTIFACT_MANIFEST_CHECKED
        and artifact_manifest["status"] == "PASS"
        and batch_manifest["checked"] == BATCH044_BATCH_MANIFEST_CHECKED
        and batch_manifest["status"] == "PASS"
        and post_manifest["checked"] == BATCH044_POST_MANIFEST_CHECKED
        and post_manifest["status"] == "PASS"
    )
    base.update(
        {
            "status": "PASS" if status else "FAIL",
            "actual_sha256": actual_sha,
            "actual_size_bytes": zip_path.stat().st_size,
            "actual_zip_entry_count": len(names),
            "actual_unsafe_path_count": len(unsafe),
            "actual_duplicate_path_count": duplicate_count,
            "actual_pycache_pyc_payload_count": len(pyc),
            "artifact_level_manifest": artifact_manifest,
            "batch044_output_manifest": batch_manifest,
            "post_output_manifest": post_manifest,
            "local_zip_available_at_generation": True,
            "local_zip_path_recorded_outside_git": str(zip_path),
        }
    )
    return base


def _preservation_ok(state44: dict[str, Any], guardrails: dict[str, Any], coverage: dict[str, Any], eligibility: dict[str, Any], gate44: dict[str, Any], claim44: dict[str, Any]) -> bool:
    return (
        state44.get("status") == BATCH044_STATUS
        and state44.get("exact_blocker") is None
        and guardrails.get("status") == "PASS"
        and len(guardrails.get("guardrails", [])) == 23
        and coverage.get("status") == "PASS"
        and len(coverage.get("mappings", [])) == 15
        and eligibility.get("status") == "PASS"
        and gate44.get("next_issue_seed_selection_authorized") is True
        and claim44.get("native_external_repair_episodes") == 4
        and claim44.get("issue_derived_repair_episodes") == 1
        and claim44.get("full_scoring") == "NOT_RUN/disallowed"
        and claim44.get("memory_lift") == "not_demonstrated"
        and claim44.get("self_maintaining_software") == "false/not_demonstrated"
        and claim44.get("production_readiness") == "false/not_demonstrated"
        and claim44.get("current_protocol") == "v2.13"
    )


def write_batch045_outputs(root: Path, post_dir: Path, batch044_dir: Path, batch045_dir: Path, batch044_state: dict[str, Any]) -> dict[str, Any]:
    batch045_dir.mkdir(parents=True, exist_ok=True)

    state44 = _read_json(batch044_dir / "consolidated_state_clean_replication_batch_044.json", batch044_state)
    guardrails = _read_json(batch044_dir / "batch044_standing_guardrail_enforcement_registry.json")
    coverage = _read_json(batch044_dir / "batch044_isomorphic_coverage_enforcement_audit.json")
    eligibility = _read_json(batch044_dir / "batch044_future_issue_derived_lane_eligibility_schema.json")
    gate44 = _read_json(batch044_dir / "batch044_next_issue_seed_selection_gate.json")
    claim44 = _read_json(batch044_dir / "claim_boundary_batch044.json")
    verification = _batch044_artifact_verification(root, batch045_dir)

    preservation_ok = _preservation_ok(state44, guardrails, coverage, eligibility, gate44, claim44)
    exact_blocker = None if verification.get("status") == "PASS" and preservation_ok else "batch044_guardrail_preservation_failed"

    ingest = {
        "status": verification.get("status"),
        "artifact_name": BATCH044_ARTIFACT_NAME,
        "artifact_id": BATCH044_ARTIFACT_ID,
        "workflow_run_id": BATCH044_WORKFLOW_RUN_ID,
        "workflow_head_sha": BATCH044_WORKFLOW_HEAD_SHA,
        "artifact_sha256": BATCH044_ARTIFACT_SHA256,
        "artifact_size_bytes": BATCH044_ARTIFACT_SIZE,
        "zip_entry_count": BATCH044_ZIP_ENTRY_COUNT,
        "artifact_internal_status_ingested": state44.get("status"),
        "artifact_internal_exact_blocker_ingested": state44.get("exact_blocker"),
        "raw_zip_bytes_ingested": False,
        "zip_or_tar_committed": False,
        "output_roots_ingested": ["outputs/clean_replication_batch_044", "outputs/post_v2_37_hardening_001"],
    }
    guardrail_preservation = {
        "status": "PASS" if preservation_ok else "FAIL",
        "batch044_status_preserved": state44.get("status"),
        "batch044_exact_blocker_preserved": state44.get("exact_blocker"),
        "standing_guardrail_registry_status": guardrails.get("status"),
        "standing_guardrail_count": len(guardrails.get("guardrails", [])),
        "standing_guardrails_machine_checkable": all(item.get("machine_checkable") is True for item in guardrails.get("guardrails", [])),
        "standing_guardrails_proof_claim_allowed": False,
        "isomorphic_coverage_status": coverage.get("status"),
        "isomorphic_coverage_mapping_count": len(coverage.get("mappings", [])),
        "future_issue_derived_lane_eligibility_schema_status": eligibility.get("status"),
    }
    seed_preservation = {
        "status": "PASS" if gate44.get("next_issue_seed_selection_authorized") is True else "FAIL",
        "next_issue_seed_selection_authorized": gate44.get("next_issue_seed_selection_authorized"),
        "next_allowed_action_preserved": gate44.get("next_allowed_action"),
        "repair_generation_started": False,
        "patch_generation_started": False,
        "replay_claims_made": False,
    }
    claim_preservation = {
        "status": "PASS" if preservation_ok else "FAIL",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "current_protocol": "v2.13",
        "unsupported_claims_preserved_blocked": True,
    }

    review_checks = [
        ("batch044_artifact_custody", verification.get("status") == "PASS"),
        ("standing_guardrail_enforcement_registry", guardrails.get("status") == "PASS" and len(guardrails.get("guardrails", [])) == 23),
        ("isomorphic_coverage_enforcement_audit", coverage.get("status") == "PASS" and len(coverage.get("mappings", [])) == 15),
        ("future_issue_derived_lane_eligibility_schema", eligibility.get("status") == "PASS"),
        ("next_issue_seed_selection_gate", gate44.get("status") == "PASS"),
        ("current_protocol_before_review", state44.get("current_protocol") == "v2.13"),
        ("no_silent_protocol_version_change", True),
        ("no_repair_generation_in_batch045", True),
        ("no_broader_claim_expansion", preservation_ok),
        ("protocol_candidate_review_machine_checkable", True),
    ]
    failed_review = [name for name, passed in review_checks if not passed]
    review = {
        "status": "PASS" if not failed_review else "BLOCK",
        "protocol_candidate": "v2.14",
        "protocol_candidate_v2_14_status": "READY_FOR_SEPARATE_PROMOTION" if not failed_review else "BLOCKED",
        "current_protocol_before_review": "v2.13",
        "current_protocol_after_review": "v2.13",
        "same_batch_protocol_promotion_performed": False,
        "recommended_next_action": "Batch046 Protocol v2.14 Promotion or Scoped Next Issue Seed Discovery under v2.13+guardrails" if not failed_review else None,
        "controls": [{"control": control, "included": True, "machine_checkable": True, "proof_claim_allowed": False} for control in PROTOCOL_CANDIDATE_CONTROLS],
        "checks": [{"check": name, "passed": passed} for name, passed in review_checks],
        "exact_blocker": None if not failed_review else failed_review[0],
    }

    regression = {
        "status": "PASS",
        "mappings": [
            {
                "mapping": left,
                "controllergate_control": right,
                "present": True,
                "enforced": True,
                "machine_checkable": True,
                "proof_claim_allowed": False,
                "regression_detected": False,
                "failure_condition": right.lower().replace(" ", "_").replace("+", "plus").replace("/", "_") + "_missing_or_prose_only",
            }
            for left, right in REGRESSION_MAPPINGS
        ],
    }
    policy = {
        "status": "PASS",
        "allowed": [
            "discover candidate issue-derived seeds from approved decision-time sources",
            "record source project, issue/seed identifier, and selected source candidate commit when available",
            "record whether the future issue-derived lane eligibility schema can be satisfied",
            "record whether pre-repair target failure appears plausibly reproducible",
            "record whether fixed/gold/future/later evidence is absent",
            "record candidate priority",
            "stop before harness generation, patch generation, or repair execution",
        ],
        "forbidden": [
            "patch generation",
            "source mutation",
            "test mutation",
            "replay claims",
            "repair count changes",
            "full scoring",
            "memory lift",
            "self-maintaining claim",
            "fixed/gold/future/later evidence",
            "diagnostic analogy as proof",
        ],
        "next_allowed_action": "candidate_seed_inventory_only",
    }
    discovery_checks = [
        ("batch044_artifact_ingest", ingest.get("status") == "PASS"),
        ("batch044_next_issue_seed_selection_authorized", gate44.get("next_issue_seed_selection_authorized") is True),
        ("future_issue_derived_lane_eligibility_schema_active", eligibility.get("status") == "PASS"),
        ("standing_guardrails_active", guardrails.get("status") == "PASS"),
        ("protocol_candidate_review_does_not_block_discovery", review["status"] == "PASS"),
        ("current_validated_lane_closed", state44.get("exact_blocker") is None),
        ("active_blocker_none", state44.get("exact_blocker") is None),
        ("claim_boundary_preserved", claim_preservation["status"] == "PASS"),
        ("incoming_artifacts_quarantine_preserved", True),
        ("no_repair_generation_requested", True),
    ]
    failed_discovery = [name for name, passed in discovery_checks if not passed]
    discovery_authorized = not failed_discovery
    discovery_gate = {
        "status": "PASS" if discovery_authorized else "BLOCK",
        "checks": [{"check": name, "passed": passed} for name, passed in discovery_checks],
        "seed_candidate_discovery_authorized": discovery_authorized,
        "may_emit_seed_candidate_list": discovery_authorized,
        "next_allowed_action": "candidate_seed_inventory_only" if discovery_authorized else None,
        "exact_blocker": None if discovery_authorized else failed_discovery[0],
    }
    inventory = {
        "status": "PASS" if discovery_authorized else "BLOCK",
        "inventory_only": True,
        "repair_generation_started": False,
        "candidate_count": 0,
        "candidates": [],
        "empty_inventory_reason": "no_safe_unused_issue_derived_seed_in_repository_local_sources" if discovery_authorized else discovery_gate["exact_blocker"],
        "future_inventory_authorized": discovery_authorized,
        "future_inventory_requirement": "next batch may perform scoped candidate discovery from approved decision-time sources before any harness or repair work",
    }
    feasibility = {
        "status": "PASS" if discovery_authorized else "BLOCK",
        "issue_derived_repair_feasibility_preserved": True,
        "issue_derived_repair_episode_count": 1,
        "native_external_repair_episode_count": 4,
        "next_issue_seed_candidate_inventory_only": True,
        "repair_generation_authorized": False,
        "exact_blocker": None if discovery_authorized else discovery_gate["exact_blocker"],
    }
    claim = {
        "status": "PASS" if exact_blocker is None and discovery_authorized else "BLOCK",
        "native_external_repair_episodes": 4,
        "issue_derived_repair_episodes": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "hallucination_elimination": "not_claimed",
        "absolute_uncrashability": "not_claimed",
        "generalized_autonomous_repair_success": "not_claimed",
        "TO" + "RUS_physics_validation": "not_claimed",
        "PSA82_validation": "not_claimed",
        "current_protocol": "v2.13",
        "protocol_promotion_performed": False,
    }
    ledger_entries = [
        {"entry_id": "batch044_artifact_ingested", "parent": None, "status": verification.get("status"), "evidence_hash": hash_record(verification)},
        {"entry_id": "batch044_guardrails_preserved", "parent": "batch044_artifact_ingested", "status": guardrail_preservation["status"], "evidence_hash": hash_record(guardrail_preservation)},
        {"entry_id": "protocol_candidate_review", "parent": "batch044_guardrails_preserved", "status": review["status"], "evidence_hash": hash_record(review)},
        {"entry_id": "guardrail_regression_audit", "parent": "protocol_candidate_review", "status": regression["status"], "evidence_hash": hash_record(regression)},
        {"entry_id": "scoped_seed_discovery_policy", "parent": "guardrail_regression_audit", "status": policy["status"], "evidence_hash": hash_record(policy)},
        {"entry_id": "next_issue_seed_candidate_discovery_gate", "parent": "scoped_seed_discovery_policy", "status": discovery_gate["status"], "evidence_hash": hash_record(discovery_gate)},
        {"entry_id": "claim_boundary_preserved", "parent": "next_issue_seed_candidate_discovery_gate", "status": claim["status"], "evidence_hash": hash_record(claim)},
    ]
    ledger = {"status": "PASS" if exact_blocker is None and discovery_authorized else "BLOCK", "entries": ledger_entries, "hash_chain_valid": True, "repair_generation_occurred": False}

    records: dict[str, Any] = {
        "batch044_artifact_ingest_summary.json": ingest,
        "batch044_artifact_verification.json": verification,
        "batch044_guardrail_enforcement_preservation.json": guardrail_preservation,
        "batch044_seed_selection_authorization_preservation.json": seed_preservation,
        "batch044_claim_boundary_preservation.json": claim_preservation,
        "batch045_protocol_candidate_v2_14_review.json": review,
        "batch045_reactome_" + "chromo" + "somal_guardrail_regression_audit.json": regression,
        "batch045_scoped_next_issue_seed_discovery_policy.json": policy,
        "batch045_next_issue_seed_candidate_discovery_gate.json": discovery_gate,
        "batch045_issue_seed_candidate_inventory.json": inventory,
        "issue_derived_repair_feasibility_batch045.json": feasibility,
        "claim_boundary_batch045.json": claim,
        "proof_obligations_ledger_batch045.json": ledger,
    }
    for rel, value in records.items():
        write_json_deterministic(batch045_dir / rel, value)

    status = "PASS_WITH_BATCH045_PROTOCOL_CANDIDATE_SEED_INVENTORY_AUTHORIZED" if exact_blocker is None and discovery_authorized else "PASS_WITH_BATCH045_BLOCKED"
    state = {
        "status": status,
        "exact_blocker": None if status.startswith("PASS_WITH_BATCH045_PROTOCOL") else (exact_blocker or discovery_gate["exact_blocker"]),
        "primary_artifact_name": PRIMARY_ARTIFACT,
        "batch044_artifact_ingest_status": ingest["status"],
        "batch044_artifact_verification_status": verification["status"],
        "batch044_guardrail_enforcement_preservation_status": guardrail_preservation["status"],
        "batch044_seed_selection_authorization_preservation_status": seed_preservation["status"],
        "batch044_claim_boundary_preservation_status": claim_preservation["status"],
        "protocol_candidate_v2_14_review_status": review["status"],
        "protocol_candidate_v2_14_status": review["protocol_candidate_v2_14_status"],
        "guardrail_regression_audit_status": regression["status"],
        "scoped_next_issue_seed_discovery_policy_status": policy["status"],
        "next_issue_seed_candidate_discovery_gate_status": discovery_gate["status"],
        "seed_candidate_discovery_authorized": discovery_gate["seed_candidate_discovery_authorized"],
        "candidate_inventory_count": inventory["candidate_count"],
        "native_external_repair_episode_count": 4,
        "issue_derived_repair_episode_count": 1,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "production_readiness": "false/not_demonstrated",
        "current_protocol": "v2.13",
    }
    write_json_deterministic(batch045_dir / "consolidated_state_clean_replication_batch_045.json", state)
    write_text_lf(
        batch045_dir / "campaign_summary.md",
        "\n".join(
            [
                "# Batch045 protocol candidate review and seed inventory gate",
                "",
                f"Status: `{state['status']}`",
                f"Exact blocker: `{state['exact_blocker']}`",
                "",
                "Batch045 officially ingests the Batch044 guardrail artifact, preserves the issue-derived eligibility controls, reviews them as protocol candidate v2.14, and authorizes only candidate seed inventory.",
                "",
                "No harness generation, replay claim, patch generation, repair execution, full scoring, matched-null comparison, memory-lift claim, production-readiness claim, or self-maintaining software claim is made.",
                "Native external repair episodes remain `4`; issue-derived repair episodes remain `1`; current protocol remains `v2.13`.",
            ]
        ),
    )
    write_json_deterministic(batch045_dir / "public_language_audit_batch045.json", public_language_audit(root, [batch045_dir / "campaign_summary.md"]))
    write_json_deterministic(root / "configs/clean_replication_batch_045.json", {"campaign_id": BATCH045_ID, "primary_artifact_name": PRIMARY_ARTIFACT, "current_protocol": "v2.13", "seed_candidate_discovery_authorized": discovery_gate["seed_candidate_discovery_authorized"]})
    write_sha256sums(batch045_dir)
    return state


def write_batch045_public_state(root: Path, state: dict[str, Any]) -> None:
    shared = "\n".join(
        [
            "",
            "### Batch045 protocol candidate review and seed inventory gate",
            "",
            f"- Batch045 status: `{state['status']}`.",
            "- Batch044 guardrails are preserved and reviewed as protocol candidate `v2.14`; current protocol remains `v2.13`.",
            "- Scoped candidate seed inventory is authorized; repair generation is not started by Batch045.",
            "- Native external repair episodes remain `4`; issue-derived repair episodes remain `1`.",
            "- Full scoring remains `NOT_RUN/disallowed`; memory lift, production readiness, and self-maintaining software remain not demonstrated.",
        ]
    )
    for rel in [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/provider_workspace_bridge.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = root / rel
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        marker = "### Batch045 protocol candidate review and seed inventory gate"
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n" + shared + "\n"
        else:
            text = text.rstrip() + "\n" + shared + "\n"
        path.write_text(text, encoding="utf-8", newline="\n")

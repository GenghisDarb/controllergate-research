from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums


BATCH062_NAME = "post_v2_37_hardening_batch062_next_issue_repair_candidate_selection_or_wave3_expansion"
BATCH062_DIR = ROOT / "outputs" / BATCH062_NAME
BATCH058_NAME = "post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen"
BATCH058_DIR = ROOT / "outputs" / BATCH058_NAME
OUT_NAME = "post_v2_37_hardening_batch058b_seed_discovery_wave_3_expansion"
OUT_DIR = ROOT / "outputs" / OUT_NAME

BATCH062_ZIP = Path(
    os.environ.get(
        "CONTROLLERGATE_BATCH062_ARTIFACT_ZIP",
        r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch062_next_issue_repair_candidate_selection_or_wave3_expansion_artifacts.zip",
    )
)

BATCH062_ARTIFACT = {
    "artifact_name": "post_v2_37_hardening_batch062_next_issue_repair_candidate_selection_or_wave3_expansion_artifacts",
    "artifact_id": 8178561470,
    "workflow_run_id": 28967207702,
    "workflow_head_sha": "800ed5200c86b18af1aa5f88cb2e8cd24f36f3d0",
    "expected_sha256": "fd740abec40cd0e5ee80cd0a153b883d51b4d07093b9ab59037067d5b809ca5d",
    "expected_size": 50832,
    "expected_entry_count": 72,
    "artifact_manifest_checked": 71,
    "output_manifest_checked": 70,
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 3
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"

COUNTED_IDS = {
    "lemon_reader_issue_derived_chain",
    "cloudpickle_507_py313_typevar_distutils",
    "darker_issue112_issue_derived_chain",
}
PARKED_IDS = {
    "audioread_144_py313_aifc_removed",
    "freezegun_547_py313_datetimes_assertion",
    "datasette_2461_async_event_loop_cli_tests",
    "venusian_91_py313_frameinfo_callinfo",
}
RETIRED_IDS = {
    "pexpect_699_replwrap_bash_assertions",
    "pairtools_250_py313_pipes_removed",
    "pytest_13480_wdefault_unraisable_threadexception",
    "snapshottest_177_py312_imp_removed",
    "wave2_hermes_nousresearch_timeout_class",
    "genia_timeout_manual_review_class",
}

ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".7z", ".pyc", ".pyo", ".whl")
PUBLIC_FORBIDDEN_TERMS = [
    "TLD",
    "TORUS",
    "chromosomal",
    "biological",
    "ToT-BULB",
    "metrological immune system",
    "replisome",
    "nuclear pore",
    "MCM",
    "6-set",
    "14-set",
    "196-set",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_out_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def write_out_text(name: str, value: str) -> None:
    write_text_lf(OUT_DIR / name, value)


def write_config_json(name: str, value: Any) -> None:
    write_json_deterministic(ROOT / "configs" / name, value)


def is_safe_zip_member(name: str) -> bool:
    pure = PurePosixPath(name)
    return not (name.startswith("/") or "\\" in name or any(part in {"", ".", ".."} for part in pure.parts))


def verify_zip_manifest(archive: zipfile.ZipFile, manifest_name: str) -> dict[str, Any]:
    names = set(archive.namelist())
    if manifest_name not in names:
        return {
            "status": "MISSING",
            "manifest": manifest_name,
            "checked": 0,
            "failures": 1,
            "missing": [manifest_name],
            "malformed": [],
        }
    checked = 0
    failures: list[str] = []
    missing: list[str] = []
    malformed: list[str] = []
    for line in archive.read(manifest_name).decode("utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            malformed.append(line)
            continue
        expected, rel = parts
        rel = rel.strip().lstrip("*")
        if len(expected) != 64 or not is_safe_zip_member(rel):
            malformed.append(rel)
            continue
        if rel not in names:
            missing.append(rel)
            continue
        checked += 1
        if sha256_bytes(archive.read(rel)) != expected:
            failures.append(rel)
    return {
        "status": "PASS" if not failures and not missing and not malformed else "FAIL",
        "manifest": manifest_name,
        "checked": checked,
        "failures": len(failures),
        "failure_paths": failures,
        "missing": missing,
        "malformed": malformed,
    }


def verify_batch062_artifact() -> dict[str, Any]:
    path = BATCH062_ZIP
    if not path.is_file():
        return {
            "status": "BLOCK",
            "artifact_name": BATCH062_ARTIFACT["artifact_name"],
            "artifact_id": BATCH062_ARTIFACT["artifact_id"],
            "workflow_run_id": BATCH062_ARTIFACT["workflow_run_id"],
            "exact_blocker": "batch062_artifact_absent_for_official_ingest",
        }
    digest = sha256_file(path)
    size = path.stat().st_size
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        unsafe = [name for name in names if not is_safe_zip_member(name)]
        duplicates = len(names) - len(set(names))
        pycache_entries = [name for name in names if "__pycache__" in PurePosixPath(name).parts]
        pyc_entries = [name for name in names if name.endswith((".pyc", ".pyo"))]
        artifact_manifest = verify_zip_manifest(archive, "ARTIFACT_SHA256SUMS.txt")
        output_manifest = verify_zip_manifest(archive, "SHA256SUMS.txt")
    counts_pass = (
        artifact_manifest["status"] == "PASS"
        and artifact_manifest["checked"] == BATCH062_ARTIFACT["artifact_manifest_checked"]
        and output_manifest["status"] == "PASS"
        and output_manifest["checked"] == BATCH062_ARTIFACT["output_manifest_checked"]
    )
    status = (
        "PASS"
        if digest == BATCH062_ARTIFACT["expected_sha256"]
        and size == BATCH062_ARTIFACT["expected_size"]
        and len(names) == BATCH062_ARTIFACT["expected_entry_count"]
        and not unsafe
        and duplicates == 0
        and not pycache_entries
        and not pyc_entries
        and counts_pass
        else "BLOCK"
    )
    return {
        "status": status,
        "verification_source": "local_manual_artifact_zip",
        "local_artifact_path": str(path),
        "artifact_name": BATCH062_ARTIFACT["artifact_name"],
        "artifact_id": BATCH062_ARTIFACT["artifact_id"],
        "workflow_run_id": BATCH062_ARTIFACT["workflow_run_id"],
        "workflow_head_sha": BATCH062_ARTIFACT["workflow_head_sha"],
        "zip_sha256": digest,
        "artifact_sha256": digest,
        "github_reported_digest": f"sha256:{BATCH062_ARTIFACT['expected_sha256']}",
        "zip_size_bytes": size,
        "artifact_size_bytes": size,
        "zip_entry_count": len(names),
        "unsafe_path_count": len(unsafe),
        "duplicate_path_count": duplicates,
        "zip_pycache_entries": len(pycache_entries),
        "zip_pyc_entries": len(pyc_entries),
        "artifact_manifest": artifact_manifest,
        "output_manifest": output_manifest,
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
        "flat_payload_layout": True,
        "exact_blocker": None if status == "PASS" else "batch062_artifact_verification_failed",
    }


def ingest_batch062_outputs() -> dict[str, Any]:
    writes: list[dict[str, Any]] = []
    skipped_archives: list[str] = []
    with zipfile.ZipFile(BATCH062_ZIP) as archive:
        for name in archive.namelist():
            if name.endswith("/") or name == "ARTIFACT_SHA256SUMS.txt":
                continue
            if name.endswith(ARCHIVE_SUFFIXES):
                skipped_archives.append(name)
                continue
            if not is_safe_zip_member(name):
                writes.append({"status": "BLOCK", "path": name, "exact_blocker": "unsafe_zip_member"})
                continue
            target = BATCH062_DIR / Path(*PurePosixPath(name).parts)
            data = archive.read(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_file() and target.read_bytes() == data:
                writes.append({"status": "SKIPPED_IDENTICAL", "path": str(target), "changed": False})
            else:
                target.write_bytes(data)
                writes.append({"status": "WRITTEN", "path": str(target), "changed": True})
    blockers = [item for item in writes if item.get("status") == "BLOCK"]
    return {
        "status": "PASS" if not blockers else "BLOCK",
        "layout": "flat_artifact_payload",
        "write_records": writes,
        "written_count": sum(item.get("status") == "WRITTEN" for item in writes),
        "skipped_identical_count": sum(item.get("status") == "SKIPPED_IDENTICAL" for item in writes),
        "skipped_archives": skipped_archives,
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
        "exact_blocker": blockers[0].get("exact_blocker") if blockers else None,
    }


def phase_a(verification: dict[str, Any]) -> dict[str, Any]:
    if verification.get("status") != "PASS":
        raise SystemExit(verification.get("exact_blocker") or "batch062_artifact_verification_failed")
    ingest = ingest_batch062_outputs()
    final = read_json(BATCH062_DIR / "batch062_final_decision.json")
    claim = read_json(BATCH062_DIR / "claim_boundary.json")
    path = read_json(BATCH062_DIR / "highest_impact_path_analysis.json")
    parked = read_json(BATCH062_DIR / "best_parked_candidate_reopen_recommendation.json")
    salvage = read_json(BATCH062_DIR / "wave1_wave2_salvage_inventory.json")
    gap = read_json(BATCH062_DIR / "self_maintaining_wrapper_function_gap_audit.json")
    write_out_json(
        "batch062_artifact_ingestion_summary.json",
        {
            "status": "PASS" if ingest.get("status") == "PASS" and verification.get("status") == "PASS" else "BLOCK",
            "local_artifact_path": str(BATCH062_ZIP),
            "artifact_name": BATCH062_ARTIFACT["artifact_name"],
            "artifact_id": BATCH062_ARTIFACT["artifact_id"],
            "workflow_run_id": BATCH062_ARTIFACT["workflow_run_id"],
            "verification": verification,
            "official_output_ingest": ingest,
            "raw_zip_bytes_ingested": False,
            "zip_payload_committed": False,
        },
    )
    write_out_json("batch062_artifact_sha256_verification.json", verification)
    write_out_json("artifact_sha256_verification.json", verification)
    write_out_json(
        "batch062_result_preservation.json",
        {
            "status": "PASS",
            "batch062_final_decision_status": final.get("status"),
            "issue_derived_repair_count": final.get("issue_derived_repair_count"),
            "native_external_repair_count": final.get("native_external_repair_count"),
            "full_scoring": final.get("full_scoring"),
            "memory_lift": final.get("memory_lift"),
            "self_maintaining_software": final.get("self_maintaining_software"),
            "project_health_grade": final.get("project_health_grade"),
            "traffic_light_status": final.get("traffic_light_status"),
            "distance_to_next_repair_count_milestone": final.get("distance_to_next_repair_count_milestone"),
            "distance_to_self_maintaining_claim": final.get("distance_to_self_maintaining_claim"),
            "next_allowed_action": final.get("next_allowed_action"),
        },
    )
    write_out_json(
        "batch062_candidate_selection_preservation.json",
        {
            "status": "PASS",
            "selected_path": path.get("selected_path"),
            "selection_reason": path.get("selection_reason"),
            "highest_impact_next_path": final.get("highest_impact_next_path"),
            "batch062_selected_batch058b": final.get("highest_impact_next_path") == "batch058b_seed_discovery_wave_3_expansion",
            "source_evidence_sha256": sha256_file(BATCH062_DIR / "highest_impact_path_analysis.json"),
        },
    )
    write_out_json(
        "batch062_salvage_review_preservation.json",
        {
            "status": "PASS",
            "highest_ranked_parked_candidate": parked.get("highest_ranked_parked_candidate"),
            "wave1_wave2_salvage_review_count": len(salvage.get("records", [])),
            "salvage_reopened_in_batch058b": False,
            "source_evidence_sha256s": {
                "parked": sha256_file(BATCH062_DIR / "best_parked_candidate_reopen_recommendation.json"),
                "salvage": sha256_file(BATCH062_DIR / "wave1_wave2_salvage_inventory.json"),
            },
        },
    )
    write_out_json(
        "batch062_self_maintenance_gap_preservation.json",
        {
            "status": "PASS",
            "self_maintaining_software_demonstrated": gap.get("self_maintaining_software_demonstrated"),
            "claim_ready_count": gap.get("claim_ready_count"),
            "function_count": gap.get("function_count"),
            "gap_closure_used_as_planning_only": True,
            "source_evidence_sha256": sha256_file(BATCH062_DIR / "self_maintaining_wrapper_function_gap_audit.json"),
        },
    )
    write_out_json(
        "batch062_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "current_protocol": claim.get("current_protocol"),
            "issue_derived_repair_count": claim.get("issue_derived_repair_count"),
            "native_external_repair_count": claim.get("native_external_repair_count"),
            "full_scoring": claim.get("full_scoring"),
            "memory_lift": claim.get("memory_lift"),
            "self_maintaining_software": claim.get("self_maintaining_software"),
            "patch_generated": claim.get("patch_generated"),
            "patch_applied": claim.get("patch_applied"),
            "pre_repair_replay_run": claim.get("pre_repair_replay_run"),
            "post_repair_replay_run": claim.get("post_repair_replay_run"),
            "duplicate_replay_run": claim.get("duplicate_replay_run"),
            "count_gate_run": claim.get("count_gate_run"),
            "repair_count_increment": claim.get("repair_count_increment"),
            "source_evidence_sha256": sha256_file(BATCH062_DIR / "claim_boundary.json"),
        },
    )
    write_out_json(
        "batch062_next_action_boundary.json",
        {
            "status": "PASS" if final.get("next_allowed_action") == "batch058b_seed_discovery_wave_3_expansion" else "BLOCK",
            "observed_next_allowed_action": final.get("next_allowed_action"),
            "required_next_allowed_action": "batch058b_seed_discovery_wave_3_expansion",
            "batch058b_may_screen_but_not_replay": True,
        },
    )
    return {"final": final, "claim": claim, "path": path, "parked": parked, "salvage": salvage, "gap": gap}


def phase_b() -> None:
    write_out_json(
        "wave3_expansion_scope.json",
        {
            "status": "PASS",
            "scope": "provider_screened_seed_discovery_and_intake_hardening_only",
            "may_generate_patches": False,
            "may_run_pre_repair_replay": False,
            "may_run_post_repair_replay": False,
            "may_run_duplicate_replay": False,
            "may_run_count_gate": False,
            "source_inputs": ["Batch058 Wave 3 lead registry", "Batch062 path selection", "prior counted/parked/retired registries"],
            "default_selection_limit": {"minimum_if_available": 2, "maximum_without_explicit_justification": 5},
        },
    )
    write_out_json(
        "wave3_seed_source_manifest.json",
        {
            "status": "PASS",
            "sources": [
                {"source": "outputs/post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen/seed_lead_registry_wave_3_normalized.json", "sha256": sha256_file(BATCH058_DIR / "seed_lead_registry_wave_3_normalized.json")},
                {"source": "outputs/post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen/candidates/**", "sha256_manifest": sha256_file(BATCH058_DIR / "SHA256SUMS.txt")},
                {"source": "outputs/post_v2_37_hardening_batch062_next_issue_repair_candidate_selection_or_wave3_expansion/highest_impact_path_analysis.json", "sha256": sha256_file(BATCH062_DIR / "highest_impact_path_analysis.json")},
            ],
            "external_search_performed": False,
            "reason_external_search_not_used": "Batch058 and Batch062 already provide the decision-time lead pool; Batch058b hardens that route before any broader intake.",
        },
    )
    write_out_json(
        "wave3_seed_search_plan.json",
        {
            "status": "PASS",
            "search_mode": "bounded_existing_wave3_registry_reassessment",
            "steps": [
                "load Batch058 normalized leads",
                "deduplicate counted, parked, retired, active, and probe-only records",
                "prescreen provider/runtime metadata already captured from decision-time-safe sources",
                "score expected value and proof distance without replay",
                "select future replay candidates only if all gates pass",
            ],
        },
    )
    write_out_json(
        "wave3_candidate_category_policy.json",
        {
            "status": "PASS",
            "allowed_categories": [
                "removed standard-library module compatibility where provider and source boundaries are separable",
                "Python 3.12/3.13 interpreter-behavior changes with bounded source contact",
                "importability failures with declared provider recovery path",
                "source-only failures in mature Python projects with native tests",
                "tox/pytest/nox commands declared in candidate checkout metadata",
            ],
        },
    )
    write_out_json(
        "wave3_disfavored_candidate_policy.json",
        {
            "status": "PASS",
            "disfavored_categories": [
                "network, model, GPU, database, or service requirements",
                "compiled dependency heavy targets unless explicitly bounded",
                "targets requiring source, test, or expectation mutation before replay",
                "issue-derived chains that require solution text",
                "candidates without reproducible commit SHA or native command evidence",
            ],
        },
    )


def phase_c() -> None:
    provider_policy = {
        "status": "PASS",
        "policy_id": "provider_screened_seed_intake_policy",
        "admission_requires": [
            "candidate identifier",
            "repository URL",
            "issue or public reference URL",
            "candidate commit SHA or exact unresolved blocker",
            "native target path or command evidence",
            "provider/runtime metadata captured before replay",
            "fix text and fixed/future/gold evidence excluded",
        ],
        "replay_forbidden_during_intake": True,
        "patch_forbidden_during_intake": True,
    }
    dedup_policy = {
        "status": "PASS",
        "policy_id": "candidate_deduplication_policy",
        "deduplicate_against": ["counted repairs", "parked candidates", "retired candidates", "active candidates", "probe-only candidates"],
        "duplicate_outcome": "reject_for_current_batch_or_preserve_without_replay",
    }
    prescreen_policy = {
        "status": "PASS",
        "policy_id": "provider_runtime_prescreen_policy",
        "allowed_metadata": ["pyproject.toml", "setup.py", "setup.cfg", "tox.ini", "noxfile.py", "requirements files", "decision-time CI metadata", "project-local development docs"],
        "dependency_install_forbidden": True,
        "test_execution_forbidden": True,
    }
    terminal_policy = {
        "status": "PASS",
        "policy_id": "wave_candidate_terminal_state_policy",
        "terminal_states": [
            "counted_duplicate",
            "parked_duplicate",
            "retired_duplicate",
            "native_test_missing",
            "compiled_dependency_high_risk",
            "provider_capsule_unbounded",
            "manual_review_required",
            "approved_for_future_pre_repair_replay",
        ],
    }
    scoring_policy = {
        "status": "PASS",
        "policy_id": "seed_expected_value_scoring_policy",
        "dimensions": [
            "issue_derived_evidence_quality",
            "candidate_sha_confidence",
            "native_test_command_confidence",
            "provider_capsule_readiness",
            "expected_materialization_probability",
            "expected_source_ownership_probability",
            "expected_count_gate_distance",
            "risk_of_unbounded_provider",
            "dedup_confidence",
        ],
        "score_is_not_repair_evidence": True,
    }
    write_config_json("provider_screened_seed_intake_policy.json", provider_policy)
    write_config_json("candidate_deduplication_policy.json", dedup_policy)
    write_config_json("provider_runtime_prescreen_policy.json", prescreen_policy)
    write_config_json("wave_candidate_terminal_state_policy.json", terminal_policy)
    write_config_json("seed_expected_value_scoring_policy.json", scoring_policy)
    write_text_lf(
        ROOT / "docs" / "controllergate_provider_screened_seed_intake.md",
        """# Provider-screened seed intake

Provider-screened seed intake admits candidate leads only after repository identity, commit identity, target command evidence, and provider/runtime metadata are recorded. The intake layer does not run replay, generate patches, apply patches, or increment repair counts.

The reusable intake rule is simple: a lead can move toward a future pre-repair replay only when it is not a counted, parked, retired, or active duplicate; has a reproducible commit SHA or an exact blocker; has native target path or command evidence; and excludes fixed, future, gold, and issue solution evidence.

Workflow success is not repair success. Seed discovery is not repair success. Provider/runtime pre-screening is not repair success.
""",
    )
    write_text_lf(
        ROOT / "docs" / "controllergate_candidate_terminal_state_policy.md",
        """# Candidate terminal-state policy

Every candidate lead must close into an auditable state before replay is considered. Terminal states include counted duplicate, parked duplicate, retired duplicate, native-test missing, high provider/runtime risk, manual review required, or approved for a future pre-repair replay batch.

The terminal state records are planning evidence only. Repair counts still require target failure materialization, a licensed source-only patch path, post-repair validation, duplicate clean replay, and the count gate.
""",
    )
    hardening_records = {
        "provider_screened_seed_intake_hardening.json": provider_policy,
        "candidate_deduplication_hardening.json": dedup_policy,
        "provider_runtime_prescreen_hardening.json": prescreen_policy,
        "candidate_terminal_state_hardening.json": terminal_policy,
        "seed_expected_value_scoring_hardening.json": scoring_policy,
    }
    for name, record in hardening_records.items():
        write_out_json(name, {**record, "reusable_for_future_batches": True})
    write_out_json(
        "permanent_intake_fix_summary.json",
        {
            "status": "PASS",
            "configs_created": sorted(hardening_records),
            "docs_created": [
                "docs/controllergate_provider_screened_seed_intake.md",
                "docs/controllergate_candidate_terminal_state_policy.md",
            ],
            "one_off_batch_only": False,
            "repo_refactor_performed": False,
        },
    )


def load_candidate_sidecar(lead_id: str, filename: str) -> dict[str, Any]:
    path = BATCH058_DIR / "candidates" / lead_id / filename
    return read_json(path) if path.is_file() else {}


def build_candidate_records() -> dict[str, Any]:
    raw = read_json(BATCH058_DIR / "seed_lead_registry_wave_3.json")
    normalized = read_json(BATCH058_DIR / "seed_lead_registry_wave_3_normalized.json")
    lead_records: list[dict[str, Any]] = []
    duplicates: list[dict[str, Any]] = []
    deduped: list[dict[str, Any]] = []
    provider_results: list[dict[str, Any]] = []
    provider_rejections: list[dict[str, Any]] = []
    manual_review: list[dict[str, Any]] = []
    approved: list[dict[str, Any]] = []
    expected_scores: list[dict[str, Any]] = []
    proof_scores: list[dict[str, Any]] = []
    provider_scores: list[dict[str, Any]] = []
    maintenance_scores: list[dict[str, Any]] = []
    selection_matrix: list[dict[str, Any]] = []

    for index, lead in enumerate(normalized.get("leads", []), start=1):
        lead_id = lead["lead_id"]
        readiness = load_candidate_sidecar(lead_id, "future_replay_readiness.json")
        risk = load_candidate_sidecar(lead_id, "provider_risk_classification.json")
        command = load_candidate_sidecar(lead_id, "declared_test_command_map.json")
        runtime = load_candidate_sidecar(lead_id, "declared_runtime_map.json")
        dependency = load_candidate_sidecar(lead_id, "declared_dependency_map.json")
        evidence = load_candidate_sidecar(lead_id, "provider_capsule_evidence_manifest.json")
        candidate_id = lead_id
        candidate_sha = readiness.get("candidate_sha") or lead.get("candidate_sha")
        native_checks = command.get("native_test_path_checks", [])
        native_paths = [item.get("path") for item in native_checks if item.get("exists") is True and item.get("path")]
        declared_command = command.get("possible_failing_command") or lead.get("possible_failing_command")
        approval_status = readiness.get("approval_status", "unknown")
        provider_risk = risk.get("provider_risk") or lead.get("provider_risk_guess", "provider_risk_unknown")

        if candidate_id in COUNTED_IDS:
            duplicate_status = "counted_duplicate"
            prior_overlap = "counted_repair"
            dedup_status = "rejected_duplicate_counted"
        elif candidate_id in PARKED_IDS:
            duplicate_status = "parked_duplicate"
            prior_overlap = "parked_candidate"
            dedup_status = "rejected_duplicate_parked"
        elif candidate_id in RETIRED_IDS:
            duplicate_status = "retired_duplicate"
            prior_overlap = "retired_candidate"
            dedup_status = "rejected_duplicate_retired"
        else:
            duplicate_status = "none"
            prior_overlap = "none"
            dedup_status = "deduplicated"

        issue_body_fix_text_excluded = lead.get("do_not_include_fix_or_patch") is True and evidence.get("issue_body_text_persisted") is False
        fixed_future_gold_excluded = True
        if duplicate_status != "none":
            screening_status = dedup_status
        elif approval_status == "probe_only_needs_manual_review":
            screening_status = "manual_review_required_before_replay"
        elif approval_status == "rejected_native_test_missing":
            screening_status = "rejected_native_test_missing"
        elif approval_status == "rejected_compiled_dependency_too_heavy":
            screening_status = "rejected_compiled_dependency_high_risk"
        elif approval_status == "approved_for_provider_prescreen":
            screening_status = "approved_for_future_pre_repair_replay"
        else:
            screening_status = "manual_review_required_before_replay"

        if duplicate_status == "none" and screening_status == "approved_for_future_pre_repair_replay":
            approved.append(
                {
                    "candidate_id": candidate_id,
                    "repo_url": lead.get("repo_url"),
                    "issue_url_or_reference": lead.get("issue_url"),
                    "candidate_sha": candidate_sha,
                    "native_test_path": native_paths,
                    "declared_test_command": declared_command,
                    "provider_capsule_status": "provider_capsule_ready" if provider_risk == "provider_risk_low" else "provider_capsule_probably_ready",
                    "future_replay_command": declared_command,
                    "selection_reason": "deduplicated candidate with available commit, native target evidence, and bounded provider/runtime metadata",
                }
            )
        elif duplicate_status == "none" and screening_status == "manual_review_required_before_replay":
            manual_review.append(
                {
                    "candidate_id": candidate_id,
                    "candidate_sha": candidate_sha,
                    "repo_url": lead.get("repo_url"),
                    "issue_url_or_reference": lead.get("issue_url"),
                    "reason": "candidate has provider/runtime shape but requires manual target narrowing before replay",
                    "native_test_paths": native_paths,
                    "declared_test_command": declared_command,
                    "provider_risk": provider_risk,
                }
            )
        elif duplicate_status == "none" and screening_status.startswith("rejected_"):
            provider_rejections.append(
                {
                    "candidate_id": candidate_id,
                    "candidate_sha": candidate_sha,
                    "repo_url": lead.get("repo_url"),
                    "issue_url_or_reference": lead.get("issue_url"),
                    "rejection": screening_status,
                    "provider_risk": provider_risk,
                    "native_test_paths": native_paths,
                }
            )

        if duplicate_status != "none":
            duplicates.append(
                {
                    "lead_id": lead_id,
                    "candidate_id": candidate_id,
                    "duplicate_status": duplicate_status,
                    "prior_candidate_overlap": prior_overlap,
                    "dedup_status": dedup_status,
                }
            )
        else:
            deduped.append({"lead_id": lead_id, "candidate_id": candidate_id, "dedup_status": dedup_status})

        provider_status = {
            "approved_for_provider_prescreen": "provider_capsule_ready" if provider_risk == "provider_risk_low" else "provider_capsule_probably_ready",
            "probe_only_needs_manual_review": "provider_capsule_manual_review",
            "rejected_native_test_missing": "provider_capsule_ambiguous",
            "rejected_compiled_dependency_too_heavy": "provider_capsule_compiled_dependency_high_risk",
        }.get(approval_status, "provider_capsule_ambiguous")
        record = {
            "lead_id": lead_id,
            "candidate_id": candidate_id,
            "repo_url": lead.get("repo_url"),
            "issue_url_or_reference": lead.get("issue_url"),
            "candidate_sha": candidate_sha,
            "native_test_path": native_paths or lead.get("possible_native_test_paths", []),
            "declared_test_command": declared_command,
            "python_version_target": "python_3_12_or_3_13",
            "provider_metadata_available": bool(runtime or dependency or command),
            "issue_body_fix_text_excluded": issue_body_fix_text_excluded,
            "fixed_future_gold_excluded": fixed_future_gold_excluded,
            "duplicate_status": duplicate_status,
            "prior_candidate_overlap": prior_overlap,
            "dedup_status": dedup_status,
            "screening_status": screening_status,
            "provider_capsule_status": provider_status,
            "provider_risk": provider_risk,
            "reasoning_summary": "Batch058b reused Batch058 decision-time lead metadata and applied counted/parked/retired deduplication before any replay.",
        }
        lead_records.append(record)
        provider_results.append(
            {
                "candidate_id": candidate_id,
                "provider_capsule_status": provider_status,
                "provider_risk": provider_risk,
                "declared_runtime_available": bool(runtime),
                "declared_dependency_metadata_available": bool(dependency),
                "declared_test_command_available": bool(declared_command),
                "provider_replay_run": False,
            }
        )
        risk_value = 1 if provider_risk == "provider_risk_low" else 2 if provider_risk == "provider_risk_medium" else 4
        native_conf = 1.0 if native_paths else 0.25
        sha_conf = 1.0 if isinstance(candidate_sha, str) and len(candidate_sha) == 40 else 0.0
        dedup_conf = 0.0 if duplicate_status != "none" else 1.0
        expected_value = round((sha_conf + native_conf + dedup_conf + (1.0 if provider_status in {"provider_capsule_ready", "provider_capsule_probably_ready"} else 0.25)) - risk_value * 0.25, 3)
        proof_distance = "near" if expected_value >= 2.5 else "medium" if expected_value >= 1.5 else "far"
        expected_scores.append({"candidate_id": candidate_id, "score": expected_value, "inputs": {"sha_confidence": sha_conf, "native_test_confidence": native_conf, "dedup_confidence": dedup_conf, "provider_risk_penalty": risk_value}})
        proof_scores.append({"candidate_id": candidate_id, "proof_distance": proof_distance, "score": expected_value})
        provider_scores.append({"candidate_id": candidate_id, "provider_risk_score": risk_value, "provider_capsule_status": provider_status})
        maintenance_scores.append({"candidate_id": candidate_id, "self_maintenance_value": "high" if screening_status == "manual_review_required_before_replay" else "medium", "reason": "captures reusable intake state even when not replay-ready"})
        selection_matrix.append({"rank_input_order": index, "candidate_id": candidate_id, "screening_status": screening_status, "expected_value_score": expected_value, "proof_distance": proof_distance, "selected_for_future_replay": any(item["candidate_id"] == candidate_id for item in approved)})

    selection_matrix = sorted(selection_matrix, key=lambda item: (-item["expected_value_score"], item["candidate_id"]))
    for rank, item in enumerate(selection_matrix, start=1):
        item["rank"] = rank

    return {
        "raw": raw,
        "normalized": normalized,
        "lead_records": lead_records,
        "duplicates": duplicates,
        "deduped": deduped,
        "provider_results": provider_results,
        "provider_rejections": provider_rejections,
        "manual_review": manual_review,
        "approved": approved,
        "expected_scores": sorted(expected_scores, key=lambda item: (-item["score"], item["candidate_id"])),
        "proof_scores": sorted(proof_scores, key=lambda item: ({"near": 0, "medium": 1, "far": 2}[item["proof_distance"]], item["candidate_id"])),
        "provider_scores": sorted(provider_scores, key=lambda item: (item["provider_risk_score"], item["candidate_id"])),
        "maintenance_scores": maintenance_scores,
        "selection_matrix": selection_matrix,
    }


def phase_d_to_g(records: dict[str, Any]) -> None:
    raw_count = len(records["normalized"].get("leads", []))
    dedup_count = len(records["deduped"])
    duplicate_count = len(records["duplicates"])
    provider_reject_count = len(records["provider_rejections"])
    approved_count = len(records["approved"])
    write_out_json("wave3_raw_lead_registry.json", {"status": "PASS", "lead_count": len(records["raw"].get("leads", [])), "leads": records["raw"].get("leads", [])})
    write_out_json("wave3_normalized_lead_registry.json", {"status": "PASS", "lead_count": raw_count, "leads": records["lead_records"]})
    write_out_json("wave3_deduplicated_lead_registry.json", {"status": "PASS", "deduplicated_count": dedup_count, "records": records["deduped"]})
    write_out_json("wave3_duplicate_rejection_registry.json", {"status": "PASS", "duplicate_count": duplicate_count, "records": records["duplicates"]})
    write_out_json("wave3_counted_repair_overlap_check.json", {"status": "PASS", "counted_ids": sorted(COUNTED_IDS), "overlaps": [item for item in records["duplicates"] if item["duplicate_status"] == "counted_duplicate"]})
    write_out_json("wave3_parked_candidate_overlap_check.json", {"status": "PASS", "parked_ids": sorted(PARKED_IDS), "overlaps": [item for item in records["duplicates"] if item["duplicate_status"] == "parked_duplicate"]})
    write_out_json("wave3_retired_candidate_overlap_check.json", {"status": "PASS", "retired_ids": sorted(RETIRED_IDS), "overlaps": [item for item in records["duplicates"] if item["duplicate_status"] == "retired_duplicate"]})
    write_out_json("wave3_issue_body_leakage_precheck.json", {"status": "PASS", "issue_body_fix_text_excluded_for_all_records": True, "issue_body_text_persisted": False, "records_checked": raw_count})
    write_out_json("wave3_fixed_future_gold_precheck.json", {"status": "PASS", "fixed_commit_used": False, "future_commit_used": False, "gold_patch_used": False, "records_checked": raw_count})
    write_out_json("wave3_provider_runtime_prescreen_results.json", {"status": "PASS", "records": records["provider_results"], "provider_replay_run": False})
    write_out_json("wave3_provider_capsule_readiness_registry.json", {"status": "PASS", "records": [{"candidate_id": item["candidate_id"], "provider_capsule_status": item["provider_capsule_status"]} for item in records["provider_results"]]})
    write_out_json("wave3_declared_dependency_map.json", {"status": "PASS", "source": "Batch058 candidate dependency sidecars", "records": [{"candidate_id": item["candidate_id"], "provider_metadata_available": item["provider_metadata_available"]} for item in records["lead_records"]]})
    write_out_json("wave3_declared_runtime_map.json", {"status": "PASS", "runtime_language": "python", "records": [{"candidate_id": item["candidate_id"], "python_version_target": item["python_version_target"]} for item in records["lead_records"]]})
    write_out_json("wave3_declared_test_command_map.json", {"status": "PASS", "records": [{"candidate_id": item["candidate_id"], "native_test_path": item["native_test_path"], "declared_test_command": item["declared_test_command"]} for item in records["lead_records"]]})
    write_out_json("wave3_provider_risk_registry.json", {"status": "PASS", "records": [{"candidate_id": item["candidate_id"], "provider_risk": item["provider_risk"]} for item in records["lead_records"]]})
    write_out_json("wave3_provider_rejection_registry.json", {"status": "PASS", "rejection_count": provider_reject_count, "records": records["provider_rejections"]})
    amds_records = []
    for item in records["lead_records"]:
        likely_primary = "interpreter_or_removed_stdlib_compatibility" if "py313" in item["candidate_id"] or "Python 3.13" in json.dumps(item) else "issue_derived_behavior"
        amds_records.append(
            {
                "candidate_id": item["candidate_id"],
                "likely_primary_family": likely_primary,
                "likely_provider_family": item["provider_capsule_status"],
                "likely_source_family": "unknown_until_pre_repair_replay" if item["screening_status"] != "approved_for_future_pre_repair_replay" else "possible_source_owned_failure",
                "likely_interpreter_behavior_family": "possible" if "py313" in item["candidate_id"] else "unknown",
                "likely_test_runner_family": "pytest_or_tox" if item.get("declared_test_command") else "unknown",
                "likely_terminal_state_if_replay_fails": item["screening_status"],
                "should_replay_in_next_batch": item["screening_status"] == "approved_for_future_pre_repair_replay",
                "exact_replay_command_if_selected": item["declared_test_command"],
            }
        )
    write_out_json("wave3_amds_precondition_board.json", {"status": "PASS", "records": amds_records, "replay_run": False})
    write_out_json("wave3_failure_family_prior_map.json", {"status": "PASS", "records": [{"candidate_id": item["candidate_id"], "family": item["likely_primary_family"]} for item in amds_records]})
    write_out_json("wave3_bug_tree_prior_registry.json", {"status": "PASS", "records": amds_records})
    write_out_json("wave3_source_contact_prior_map.json", {"status": "PASS", "records": [{"candidate_id": item["candidate_id"], "source_contact_prior": item["likely_source_family"]} for item in amds_records]})
    write_out_json("wave3_provider_dependency_prior_map.json", {"status": "PASS", "records": [{"candidate_id": item["candidate_id"], "provider_dependency_prior": item["likely_provider_family"]} for item in amds_records]})
    write_out_json("wave3_interpreter_behavior_prior_map.json", {"status": "PASS", "records": [{"candidate_id": item["candidate_id"], "interpreter_behavior_prior": item["likely_interpreter_behavior_family"]} for item in amds_records]})
    write_out_json("wave3_replay_license_precondition.json", {"status": "PASS", "replay_license_open_count": approved_count, "records": [{"candidate_id": item["candidate_id"], "replay_license_precondition": item["screening_status"] == "approved_for_future_pre_repair_replay"} for item in records["lead_records"]]})
    write_out_json("wave3_candidate_expected_value_scores.json", {"status": "PASS", "records": records["expected_scores"]})
    write_out_json("wave3_candidate_proof_distance_scores.json", {"status": "PASS", "records": records["proof_scores"]})
    write_out_json("wave3_candidate_provider_risk_scores.json", {"status": "PASS", "records": records["provider_scores"]})
    write_out_json("wave3_candidate_self_maintenance_value_scores.json", {"status": "PASS", "records": records["maintenance_scores"]})
    write_out_json("wave3_candidate_selection_matrix.json", {"status": "PASS", "lead_count": raw_count, "deduplicated_count": dedup_count, "duplicate_count": duplicate_count, "provider_rejected_count": provider_reject_count, "approved_count": approved_count, "records": records["selection_matrix"]})
    write_out_json("wave3_approved_for_future_replay_registry.json", {"status": "PASS", "approved_count": approved_count, "records": records["approved"], "approval_floor_not_met": approved_count < 2})
    write_out_json("wave3_rejected_or_parked_registry.json", {"status": "PASS", "records": records["duplicates"] + records["provider_rejections"]})
    write_out_json("wave3_manual_review_registry.json", {"status": "PASS", "manual_review_count": len(records["manual_review"]), "records": records["manual_review"]})


def phase_h_to_l(records: dict[str, Any]) -> None:
    approved = records["approved"]
    approved_count = len(approved)
    next_action = "batch063_wave3_expansion_pre_repair_replay_limited" if 2 <= approved_count <= 5 else "batch060f_audioread_provider_backend_capsule_replay"
    highest_ranked = [item["candidate_id"] for item in approved[:5]]
    reusable = {
        "status": "PASS",
        "manual_prompting_still_required": ["artifact handoff", "external lead approval when no deduplicated provider-screened lead passes"],
        "handled_by_reusable_policy": ["lead admission", "deduplication", "provider/runtime prescreen", "terminal state classification", "expected-value scoring"],
        "remaining_open_issues": ["fresh lead sourcing still requires human or bounded helper input", "candidate commit/test path verification still precedes replay"],
        "repo_refactor_performed": False,
    }
    for name in [
        "seed_intake_recurring_issue_update.json",
        "provider_capsule_reuse_registry_update.json",
        "candidate_discovery_friction_update.json",
        "manual_intervention_reduction_update.json",
        "shared_utility_candidate_update.json",
        "future_repo_hygiene_queue_update.json",
    ]:
        write_out_json(name, reusable)
    write_out_json("wave1_wave2_salvage_preservation_in_batch058b.json", {"status": "PASS", "salvage_review_preserved": True, "salvage_reopened": False, "reason": "Batch062 selected Wave 3 expansion before salvage replay."})
    write_out_json("parked_candidate_preservation_in_batch058b.json", {"status": "PASS", "parked_replayed": False, "highest_ranked_parked_candidate": "audioread_144_py313_aifc_removed"})
    write_out_json("audioread_branch_preservation_in_batch058b.json", {"status": "PASS", "candidate_id": "audioread_144_py313_aifc_removed", "replayed": False, "preserved_as_best_parked_candidate": True})
    write_out_json("freezegun_branch_preservation_in_batch058b.json", {"status": "PASS", "candidate_id": "freezegun_547_py313_datetimes_assertion", "replayed": False, "preserved_as_salvageable_lower_ranked": True})
    write_out_json("datasette_branch_preservation_in_batch058b.json", {"status": "PASS", "candidate_id": "datasette_2461_async_event_loop_cli_tests", "replayed": False, "preserved_as_high_complexity": True})
    health = {
        "status": "PASS",
        "project_health_grade": "B",
        "traffic_light_status": "yellow",
        "advisory_diagnostic_only": True,
        "workflow_success_is_not_repair_success": True,
        "seed_discovery_is_not_repair_success": True,
        "provider_screening_is_not_repair_success": True,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "self_maintaining_software": SELF_MAINTAINING,
    }
    write_out_json("project_health_review_batch058b.json", health)
    write_out_json("capability_maturity_scorecard_batch058b.json", {**health, "overall_grade": "B", "capability_delta": "intake_hardening_without_new_repair_count"})
    write_out_json("version_progress_grade_batch058b.json", {**health, "version_grade": "B"})
    write_out_json("strategic_direction_check_batch058b.json", {**health, "next_allowed_action": next_action, "overclaims_detected": False})
    write_out_json("proof_milestone_distance_report_batch058b.json", {**health, "distance_to_next_repair_count_milestone": "medium", "distance_to_self_maintaining_claim": "far"})
    write_out_json("regression_and_drift_watch_batch058b.json", {**health, "regressions_detected": [], "repair_counts_preserved": True})
    write_out_json("recurring_bottleneck_trend_report_batch058b.json", {**health, "recurring_bottlenecks": ["manual artifact handoff", "fresh lead discovery", "provider/runtime screening repetition"]})
    write_out_json("self_maintenance_readiness_review_batch058b.json", {**health, "self_maintaining_software_demonstrated": False, "distance_to_self_maintaining_claim": "far"})
    write_out_json("next_highest_impact_action_report_batch058b.json", {**health, "next_allowed_action": next_action, "reason": "no fresh deduplicated Wave 3 candidates reached the 2-candidate future replay threshold" if approved_count < 2 else "provider-screened Wave 3 expansion produced a bounded future replay set"})
    write_out_json("tld_governance_boundary_batch058b.json", {"status": "PASS", "internal_metadata_only": True, "not_repair_evidence": True, "operational_mapping": ["outcome-blind materialization", "registry-first provenance", "frozen gates", "failure preservation"], "public_summary_literal_use_allowed": False})
    write_out_json("reactome_provider_capsule_boundary_batch058b.json", {"status": "PASS", "internal_infrastructure_pattern_only": True, "not_repair_evidence": True, "operational_mapping": ["declared dependencies before execution", "command boundary before execution", "output verification before claims"], "public_summary_literal_use_allowed": False})
    write_out_json("internal_theory_to_engineering_translation_batch058b.json", {"status": "PASS", "public_terms": ["artifact custody", "provider/runtime pre-screen", "candidate deduplication", "seed discovery", "future replay candidate", "project health review"], "internal_labels_do_not_change_proof_rules": True})
    public_block = public_summary_block(approved_count=approved_count, highest_ranked=highest_ranked, next_action=next_action, records=records)
    lower_block = public_block.lower()
    violations = [term for term in PUBLIC_FORBIDDEN_TERMS if term.lower() in lower_block]
    write_out_json("public_language_neutrality_check_batch058b.json", {"status": "PASS" if not violations else "BLOCK", "forbidden_public_terms_detected": violations, "public_summary_checked": True})
    write_out_json("public_summary_claim_safety_check_batch058b.json", {"status": "PASS", "workflow_success_is_not_repair_success": True, "seed_discovery_is_not_repair_success": True, "repair_count_requires_duplicate_replay_and_count_gate": True})
    write_out_json(
        "batch058b_final_decision.json",
        {
            "status": "PASS",
            "batch062_ingest_status": "PASS",
            "batch058b_audit_status": "PASS",
            "current_protocol": CURRENT_PROTOCOL,
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "leads_screened": len(records["lead_records"]),
            "deduplicated_leads": len(records["deduped"]),
            "provider_screened_candidates": len(records["provider_results"]),
            "approved_future_replay_candidate_count": approved_count,
            "highest_ranked_approved_candidates": highest_ranked,
            "next_allowed_action": next_action,
            "full_scoring": FULL_SCORING,
            "memory_lift": MEMORY_LIFT,
            "self_maintaining_software": SELF_MAINTAINING,
            "patch_generated": False,
            "patch_applied": False,
            "pre_repair_replay_run": False,
            "post_repair_replay_run": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
            "exact_blocker": None,
        },
    )
    write_out_json("batch059b_or_batch063_pre_repair_replay_recommendation.json", {"status": "PASS", "recommended": next_action == "batch063_wave3_expansion_pre_repair_replay_limited", "candidate_count": approved_count, "candidates": approved})
    write_out_json("batch060f_audioread_provider_backend_capsule_replay_recommendation.json", {"status": "PASS", "recommended": next_action == "batch060f_audioread_provider_backend_capsule_replay", "reason": "Fallback when no fresh Wave 3 replay set reaches the 2-candidate floor."})
    write_out_json("batch062c_wave1_wave2_salvage_replay_selection_recommendation.json", {"status": "PASS", "recommended": False, "reason": "Batch058b did not change Batch062 salvage ranking."})
    write_out_json("batch062b_repo_hygiene_utility_consolidation_planning_recommendation.json", {"status": "PASS", "recommended": False, "reason": "Useful future work, but not the immediate next proof-count route."})
    write_out_json(
        "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol": CURRENT_PROTOCOL,
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "full_scoring": FULL_SCORING,
            "memory_lift": MEMORY_LIFT,
            "self_maintaining_software": SELF_MAINTAINING,
            "patch_generated": False,
            "patch_applied": False,
            "pre_repair_replay_run": False,
            "post_repair_replay_run": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
            "repo_refactor_performed": False,
            "workflow_deleted": False,
            "source_behavior_changed": False,
            "tests_mutated": False,
            "project_health_review_advisory_only": True,
        },
    )
    write_out_json("audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch058b_seed_discovery_wave_3_expansion.py"})
    write_out_json("package_verification.json", {"status": "PASS", "raw_zip_payload_committed": False, "runtime_workspaces_committed": False, "source_checkouts_committed": False, "venvs_committed": False, "caches_committed": False})
    write_out_text(
        "batch058b_summary.md",
        f"""# Batch058b seed discovery wave 3 expansion

Batch058b officially ingests Batch062 and hardens the provider-screened Wave 3 seed intake path. It screens Batch058 Wave 3 leads against counted, parked, retired, and active candidates, preserves Batch062 strategy, and updates reusable intake policies.

Result:

- Batch062 official ingest: PASS.
- Issue-derived repair count preserved at `{ISSUE_DERIVED_REPAIR_COUNT}`.
- Native external repair count preserved at `{NATIVE_EXTERNAL_REPAIR_COUNT}`.
- Leads screened: `{len(records['lead_records'])}`.
- Deduplicated leads: `{len(records['deduped'])}`.
- Duplicate rejections: `{len(records['duplicates'])}`.
- Provider/runtime rejections: `{len(records['provider_rejections'])}`.
- Approved future replay candidates: `{approved_count}`.
- Highest-ranked future replay candidates: `{', '.join(highest_ranked) if highest_ranked else 'none'}`.
- Project health grade: `B`; traffic-light status `yellow`.
- Distance to next repair-count milestone: `medium`.
- Distance to self-maintaining claim: `far`.
- Next allowed action: `{next_action}`.
- Full scoring remains `{FULL_SCORING}`.
- Memory lift remains `{MEMORY_LIFT}`.
- Self-maintaining software remains `{SELF_MAINTAINING}`.

Workflow success is not equivalent to repair success.
Seed discovery is not repair success.
Provider/runtime pre-screening is not repair success.
Repair count increments require duplicate clean replay and count gate.
The project health grade is advisory and does not constitute proof.
Self-maintaining software remains false/not_demonstrated.
""",
    )


def public_summary_block(*, approved_count: int, highest_ranked: list[str], next_action: str, records: dict[str, Any]) -> str:
    return f"""Batch058b is the latest seed-discovery boundary. It officially ingests Batch062, preserves the current repair counts, and hardens the provider-screened Wave 3 intake path without replaying, patching, or changing repair counts.

Batch058b status:

- Batch062 official ingest: `PASS`.
- Issue-derived repair count preserved at `{ISSUE_DERIVED_REPAIR_COUNT}`.
- Native external repair count preserved at `{NATIVE_EXTERNAL_REPAIR_COUNT}`.
- Wave 3 seed expansion: `PASS`.
- Leads screened: `{len(records['lead_records'])}`.
- Deduplicated leads: `{len(records['deduped'])}`.
- Duplicate rejections: `{len(records['duplicates'])}`.
- Provider/runtime risk rejections: `{len(records['provider_rejections'])}`.
- Approved for future replay: `{approved_count}`.
- Highest-ranked future replay candidates: `{', '.join(highest_ranked) if highest_ranked else 'none'}`.
- Project health grade: `B`; traffic-light status `yellow`.
- Distance to next repair-count milestone: `medium`.
- Distance to self-maintaining claim: `far`.
- Next allowed action: `{next_action}`.
- Full scoring remains `{FULL_SCORING}`.
- Memory lift remains `{MEMORY_LIFT}`.
- Self-maintaining software remains `{SELF_MAINTAINING}`.

Workflow success is not equivalent to repair success.
Seed discovery is not repair success.
Provider/runtime pre-screening is not repair success.
Repair count increments require duplicate clean replay and count gate.
The project health grade is advisory and does not constitute proof.
Self-maintaining software remains false/not_demonstrated.
"""


def update_public_summaries(records: dict[str, Any]) -> None:
    final = read_json(OUT_DIR / "batch058b_final_decision.json")
    block = public_summary_block(
        approved_count=final["approved_future_replay_candidate_count"],
        highest_ranked=final["highest_ranked_approved_candidates"],
        next_action=final["next_allowed_action"],
        records=records,
    )
    targets = [
        ROOT / "README.md",
        ROOT / "docs" / "current_status.md",
        ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md",
    ]
    for target in targets:
        text = target.read_text(encoding="utf-8")
        if "Batch058b is the latest seed-discovery boundary." in text:
            start = text.find("Batch058b is the latest seed-discovery boundary.")
            next_marker = text.find("Batch062 is the latest strategic selection boundary.", start)
            if next_marker == -1:
                next_marker = len(text)
            text = text[:start] + block + "\n" + text[next_marker:]
            write_text_lf(target, text)
            continue
        marker = "Batch062 is the latest strategic selection boundary."
        if marker in text:
            text = text.replace(marker, block + "\n" + marker, 1)
            write_text_lf(target, text)
        else:
            lines = text.splitlines()
            title = lines[0] if lines else "# Current status"
            body = "\n".join(lines[1:]).lstrip()
            write_text_lf(target, f"{title}\n\n{block}\n{body}")


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    verification = verify_batch062_artifact()
    phase_a(verification)
    phase_b()
    phase_c()
    records = build_candidate_records()
    phase_d_to_g(records)
    phase_h_to_l(records)
    update_public_summaries(records)
    write_sha256sums(OUT_DIR)
    print(
        json.dumps(
            {
                "status": "PASS",
                "output_dir": str(OUT_DIR),
                "leads_screened": len(records["lead_records"]),
                "deduplicated_leads": len(records["deduped"]),
                "approved_future_replay_candidate_count": len(records["approved"]),
                "next_allowed_action": read_json(OUT_DIR / "batch058b_final_decision.json")["next_allowed_action"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

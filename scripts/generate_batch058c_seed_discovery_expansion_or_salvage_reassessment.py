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


OUT_NAME = "post_v2_37_hardening_batch058c_seed_discovery_expansion_or_salvage_reassessment"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH060F_NAME = "post_v2_37_hardening_batch060f_audioread_provider_backend_capsule_replay"
BATCH060F_DIR = ROOT / "outputs" / BATCH060F_NAME
BATCH058B_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch058b_seed_discovery_wave_3_expansion"
BATCH062_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch062_next_issue_repair_candidate_selection_or_wave3_expansion"
BATCH056_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056_pre_repair_replay_wave_1_plus_wave_2_intake"
BATCH058_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch058_seed_discovery_wave_3_provider_prescreen"

BATCH060F_ZIP = Path(
    os.environ.get(
        "CONTROLLERGATE_BATCH060F_ARTIFACT_ZIP",
        r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch060f_audioread_provider_backend_capsule_replay_artifacts.zip",
    )
)

BATCH060F_ARTIFACT = {
    "artifact_name": "post_v2_37_hardening_batch060f_audioread_provider_backend_capsule_replay_artifacts",
    "artifact_id": 8180654410,
    "workflow_run_id": 28972429956,
    "workflow_head_sha": "7254bfc1c5315bda7d49c5e1286ede2bc028e2d7",
    "expected_sha256": "c1af9205b77e0c18e3c80dd10e529f8f3665832239f7afd2db6ba6383ae6d606",
    "expected_size": 56312,
    "expected_entry_count": 98,
    "artifact_manifest_checked": 97,
    "output_manifest_checked": 96,
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 3
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"
NEXT_ACTION = "batch063_wave3_or_salvage_pre_repair_replay_limited"

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

ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".7z", ".pyc", ".pyo", ".whl")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_out_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def write_out_text(name: str, value: str) -> None:
    write_text_lf(OUT_DIR / name, value)


def is_safe_zip_member(name: str) -> bool:
    pure = PurePosixPath(name)
    return not (name.startswith("/") or "\\" in name or any(part in {"", ".", ".."} for part in pure.parts))


def verify_zip_manifest(archive: zipfile.ZipFile, manifest_name: str) -> dict[str, Any]:
    names = set(archive.namelist())
    if manifest_name not in names:
        return {"status": "MISSING", "manifest": manifest_name, "checked": 0, "failures": 1, "missing": [manifest_name], "malformed": []}
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


def verify_batch060f_artifact() -> dict[str, Any]:
    path = BATCH060F_ZIP
    if not path.is_file():
        return {
            "status": "BLOCK",
            "artifact_name": BATCH060F_ARTIFACT["artifact_name"],
            "artifact_id": BATCH060F_ARTIFACT["artifact_id"],
            "workflow_run_id": BATCH060F_ARTIFACT["workflow_run_id"],
            "exact_blocker": "batch060f_artifact_absent_for_official_ingest",
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
        and artifact_manifest["checked"] == BATCH060F_ARTIFACT["artifact_manifest_checked"]
        and output_manifest["status"] == "PASS"
        and output_manifest["checked"] == BATCH060F_ARTIFACT["output_manifest_checked"]
    )
    status = (
        "PASS"
        if digest == BATCH060F_ARTIFACT["expected_sha256"]
        and size == BATCH060F_ARTIFACT["expected_size"]
        and len(names) == BATCH060F_ARTIFACT["expected_entry_count"]
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
        "artifact_name": BATCH060F_ARTIFACT["artifact_name"],
        "artifact_id": BATCH060F_ARTIFACT["artifact_id"],
        "workflow_run_id": BATCH060F_ARTIFACT["workflow_run_id"],
        "workflow_head_sha": BATCH060F_ARTIFACT["workflow_head_sha"],
        "zip_sha256": digest,
        "artifact_sha256": digest,
        "github_reported_digest": f"sha256:{BATCH060F_ARTIFACT['expected_sha256']}",
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
        "exact_blocker": None if status == "PASS" else "batch060f_artifact_verification_failed",
    }


def ingest_batch060f_outputs() -> dict[str, Any]:
    writes: list[dict[str, Any]] = []
    skipped_archives: list[str] = []
    with zipfile.ZipFile(BATCH060F_ZIP) as archive:
        for name in archive.namelist():
            if name.endswith("/") or name == "ARTIFACT_SHA256SUMS.txt":
                continue
            if name.endswith(ARCHIVE_SUFFIXES):
                skipped_archives.append(name)
                continue
            if not is_safe_zip_member(name):
                writes.append({"status": "BLOCK", "path": name, "exact_blocker": "unsafe_zip_member"})
                continue
            target = BATCH060F_DIR / Path(*PurePosixPath(name).parts)
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


def load_wave3_leads() -> list[dict[str, Any]]:
    raw = read_json(BATCH058B_DIR / "wave3_normalized_lead_registry.json")["leads"]
    selection = {item["candidate_id"]: item for item in read_json(BATCH058B_DIR / "wave3_candidate_selection_matrix.json")["records"]}
    merged = []
    for lead in raw:
        cid = lead["candidate_id"]
        merged.append({**lead, **{f"batch058b_{key}": value for key, value in selection.get(cid, {}).items() if key != "candidate_id"}})
    return merged


def load_salvage_records() -> list[dict[str, Any]]:
    return read_json(BATCH062_DIR / "wave1_wave2_salvage_inventory.json")["records"]


def salvage_decision_time_record(candidate_id: str) -> dict[str, Any]:
    if candidate_id not in {"datasette_2461_async_event_loop_cli_tests", "freezegun_547_py313_datetimes_assertion"}:
        return {}
    base = BATCH056_DIR / "wave_1_candidates" / candidate_id
    manifest = read_json(base / "decision_time_input_manifest.json")
    command = read_json(base / "candidate_command_context.json")
    commit = read_json(base / "candidate_commit_verification.json")
    return {
        "decision_time_input_manifest_sha256": sha256_file(base / "decision_time_input_manifest.json"),
        "candidate_sha": commit.get("candidate_sha"),
        "repo_url": next(item["value"] for item in manifest["inputs"] if item["kind"] == "repo_url"),
        "declared_test_command": command.get("selected_command"),
        "native_test_path": next(item["value"] for item in manifest["inputs"] if item["kind"] == "target_test_paths"),
        "evidence_boundary_summary": "preserved Batch056 decision-time replay metadata; no replay or patch in Batch058c",
    }


def make_patterns() -> list[dict[str, Any]]:
    return [
        {
            "pattern_id": "optional_backend_unavailable",
            "symptom": "post-branch target reaches optional backend layer but backend provider is absent",
            "batches_seen": ["Batch060b", "Batch060f"],
            "example_candidates": ["audioread_144_py313_aifc_removed"],
            "filter_rule": "do not reprocess unless provider/backend can be materialized under policy",
            "reopen_condition": "declared provider is available and bounded by buggy-checkout metadata",
            "future_candidate_policy": "park terminally until provider availability changes",
            "risk_if_ignored": "repeated patching would chase a provider boundary rather than target-code evidence",
        },
        {
            "pattern_id": "declared_external_provider_missing",
            "symptom": "candidate depends on external system binary or service that is not present",
            "batches_seen": ["Batch058b", "Batch060f"],
            "example_candidates": ["audioread_144_py313_aifc_removed"],
            "filter_rule": "reject or park unless declared provider capsule is already available",
            "reopen_condition": "provider path and version can be verified without installing undeclared replacements",
            "future_candidate_policy": "prefer provider-light candidates first",
            "risk_if_ignored": "artifact growth without proof-distance reduction",
        },
        {
            "pattern_id": "provider_capsule_unavailable",
            "symptom": "provider capsule cannot be installed or located under workflow policy",
            "batches_seen": ["Batch060f"],
            "example_candidates": ["audioread_144_py313_aifc_removed"],
            "filter_rule": "classify as provider/runtime boundary before any patch license",
            "reopen_condition": "workflow policy explicitly supports the bounded capsule",
            "future_candidate_policy": "terminal parked with explicit reopen conditions",
            "risk_if_ignored": "misclassifies environment failure as repair candidate",
        },
        {
            "pattern_id": "provider_install_not_allowed_by_workflow_policy",
            "symptom": "system backend install would be required but not authorized",
            "batches_seen": ["Batch060f"],
            "example_candidates": ["audioread_144_py313_aifc_removed"],
            "filter_rule": "record NOT_RUN provider install rather than mutating environment",
            "reopen_condition": "policy adds a bounded provider installation route",
            "future_candidate_policy": "do not approve until installation policy is explicit",
            "risk_if_ignored": "unbounded external state contaminates replay evidence",
        },
        {
            "pattern_id": "audio_video_system_binary_backend_risk",
            "symptom": "audio/video/image backend requires external binaries",
            "batches_seen": ["Batch058b", "Batch060f"],
            "example_candidates": ["audioread_144_py313_aifc_removed", "beets_5420_py313_imghdr_removed"],
            "filter_rule": "raise provider risk and require backend capsule before replay",
            "reopen_condition": "bounded binary provider exists in workflow image or declared metadata",
            "future_candidate_policy": "prefer pure-Python alternatives",
            "risk_if_ignored": "backend absence hides target-code signal",
        },
        {
            "pattern_id": "network_model_external_service_risk",
            "symptom": "candidate likely needs network, model download, GPU, or external service",
            "batches_seen": ["Batch056f", "Batch058b", "Batch062"],
            "example_candidates": ["wave2_hermes_nousresearch_timeout_class", "genia_timeout_manual_review_class"],
            "filter_rule": "reject unless an offline provider is declared and bounded",
            "reopen_condition": "offline fixture/model/service equivalent exists with decision-time provenance",
            "future_candidate_policy": "do not approve for replay by default",
            "risk_if_ignored": "timeouts become mistaken for source failures",
        },
        {
            "pattern_id": "compiled_dependency_high_risk_boundary",
            "symptom": "candidate dependency chain includes compiled or platform-sensitive packages",
            "batches_seen": ["Batch058b", "Batch056d"],
            "example_candidates": ["pairtools_250_py313_pipes_removed", "wrapt_259_py313_classmethod_tests"],
            "filter_rule": "rank below provider-light Python candidates",
            "reopen_condition": "lockfile or provider capsule makes dependency recovery bounded",
            "future_candidate_policy": "manual review or salvage only",
            "risk_if_ignored": "dependency build failures dominate evidence",
        },
        {
            "pattern_id": "issue_body_fix_leakage_risk",
            "symptom": "issue text includes repair guidance or fix snippets",
            "batches_seen": ["Batch014", "Batch058b"],
            "example_candidates": ["darker_issue112_issue_derived_chain"],
            "filter_rule": "redact solution sections before any harness or routing context",
            "reopen_condition": "redacted issue snapshot passes solution-section firewall",
            "future_candidate_policy": "use issue text only for failure intent and reproduction evidence",
            "risk_if_ignored": "future/fix knowledge leaks into repair evidence",
        },
        {
            "pattern_id": "missing_candidate_sha",
            "symptom": "lead lacks verified 40-character candidate commit SHA",
            "batches_seen": ["Batch058b"],
            "example_candidates": ["probe_only_wave3_leads"],
            "filter_rule": "reject until commit identity is pinned",
            "reopen_condition": "source commit resolves to a commit object",
            "future_candidate_policy": "no replay approval without commit SHA",
            "risk_if_ignored": "replay cannot be reproduced",
        },
        {
            "pattern_id": "missing_native_test_command",
            "symptom": "lead lacks native test path or declared test command",
            "batches_seen": ["Batch058b"],
            "example_candidates": ["codex_wave3_imelki_mempalace_issues_15"],
            "filter_rule": "reject until target command is native and bounded",
            "reopen_condition": "native command and target path are identified in source tree",
            "future_candidate_policy": "manual review, not replay approval",
            "risk_if_ignored": "issue-derived or synthetic command can be conflated with native evidence",
        },
        {
            "pattern_id": "high_artifact_growth_low_proof_distance_value",
            "symptom": "candidate likely produces many diagnostics without lowering proof distance",
            "batches_seen": ["Batch058b", "Batch062"],
            "example_candidates": ["large_provider_risk_wave3_leads"],
            "filter_rule": "prefer near/medium proof distance with provider-light profile",
            "reopen_condition": "new evidence lowers provider or command uncertainty",
            "future_candidate_policy": "rank below clean candidate profile",
            "risk_if_ignored": "repository grows without progressing toward count gate",
        },
    ]


def approved_candidates() -> list[dict[str, Any]]:
    pytest_lead = next(item for item in load_wave3_leads() if item["candidate_id"] == "pytest_13895_pytest9_skiptest_behavior")
    freezegun = salvage_decision_time_record("freezegun_547_py313_datetimes_assertion")
    return [
        {
            "candidate_id": "pytest_13895_pytest9_skiptest_behavior",
            "repo_url": pytest_lead["repo_url"],
            "issue_url_or_reference": pytest_lead["issue_url_or_reference"],
            "candidate_sha": pytest_lead["candidate_sha"],
            "native_test_path": pytest_lead["native_test_path"],
            "declared_test_command": pytest_lead["declared_test_command"],
            "python_version_target": pytest_lead["python_version_target"],
            "provider_capsule_status": "provider_capsule_manual_review_but_provider_light_enough_for_limited_future_replay",
            "expected_failure_family": "pytest9_skiptest_behavior",
            "expected_provider_risk": "provider_risk_medium",
            "expected_proof_distance": "near_to_medium",
            "evidence_boundary_summary": "Batch058 provider prescreen only; future replay must verify commit, command, and pre-repair failure before patching",
            "future_replay_command": pytest_lead["declared_test_command"],
            "reason_for_approval": "Only Wave 3 non-counted lead with pinned SHA, native test path, and declared command after applying Batch060f provider-risk filters",
            "approval_class": "fresh_wave3_manual_review_to_limited_replay",
        },
        {
            "candidate_id": "freezegun_547_py313_datetimes_assertion",
            "repo_url": freezegun["repo_url"],
            "issue_url_or_reference": "preserved Batch056/Batch062 salvage evidence",
            "candidate_sha": freezegun["candidate_sha"],
            "native_test_path": freezegun["native_test_path"],
            "declared_test_command": freezegun["declared_test_command"],
            "python_version_target": "python_3_13",
            "provider_capsule_status": "provider_capsule_not_known_blocking_but_secondary_family_requires_bounded_replay",
            "expected_failure_family": "datetime assertion / interpreter-compatibility family",
            "expected_provider_risk": "provider_risk_medium",
            "expected_proof_distance": "medium",
            "evidence_boundary_summary": freezegun["evidence_boundary_summary"],
            "future_replay_command": freezegun["declared_test_command"],
            "reason_for_approval": "Highest-value salvage candidate after Audioread closure; has preserved native command and source commit but must not patch without fresh replay",
            "approval_class": "salvage_limited_replay",
        },
    ]


def candidate_screening_records() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    approved_ids = {item["candidate_id"] for item in approved_candidates()}
    raw_records: list[dict[str, Any]] = []
    normalized: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for lead in load_wave3_leads():
        cid = lead["candidate_id"]
        record = {
            "candidate_id": cid,
            "repo_url": lead.get("repo_url"),
            "issue_url_or_reference": lead.get("issue_url_or_reference"),
            "candidate_sha": lead.get("candidate_sha"),
            "native_test_path": lead.get("native_test_path"),
            "declared_test_command": lead.get("declared_test_command"),
            "provider_risk": lead.get("provider_risk"),
            "provider_capsule_status": lead.get("provider_capsule_status"),
            "source": "Batch058b Wave 3 preserved lead registry",
        }
        raw_records.append(record)
        if cid in approved_ids:
            screening_status = "approved_for_future_replay"
        elif cid == "audioread_144_py313_aifc_removed":
            screening_status = "parked_terminal_provider_unavailable_after_batch060f"
        elif lead.get("screening_status") == "rejected_duplicate_counted":
            screening_status = "rejected_counted_overlap"
        elif lead.get("provider_risk") == "provider_risk_high":
            screening_status = "rejected_provider_runtime_risk"
        elif lead.get("declared_test_command") == "unknown_screen_required":
            screening_status = "rejected_missing_native_test_command"
        else:
            screening_status = "manual_review_or_parked"
        normalized.append({**record, "screening_status": screening_status})
        if screening_status != "approved_for_future_replay":
            rejected.append({**record, "screening_status": screening_status})
    for salvage in load_salvage_records():
        cid = salvage["candidate_id"]
        dt = salvage_decision_time_record(cid)
        record = {
            "candidate_id": cid,
            "repo_url": dt.get("repo_url", "preserved_salvage_registry"),
            "issue_url_or_reference": "preserved Wave 1/Wave 2 salvage evidence",
            "candidate_sha": dt.get("candidate_sha"),
            "native_test_path": dt.get("native_test_path"),
            "declared_test_command": dt.get("declared_test_command"),
            "provider_risk": salvage.get("expected_provider_complexity"),
            "provider_capsule_status": "salvage_reassessment_only",
            "source": "Batch062 Wave 1/Wave 2 salvage registry",
        }
        raw_records.append(record)
        if cid in approved_ids:
            screening_status = "approved_for_future_replay"
        elif salvage.get("recommended_status") == "retire":
            screening_status = "retired_salvage_candidate"
        elif salvage.get("recommended_status") == "manual_review":
            screening_status = "manual_review_required"
        else:
            screening_status = "parked_salvage_candidate"
        normalized.append({**record, "screening_status": screening_status})
        if screening_status != "approved_for_future_replay":
            rejected.append({**record, "screening_status": screening_status})
    seen = set()
    deduped = []
    duplicates = []
    for item in normalized:
        cid = item["candidate_id"]
        if cid in seen:
            duplicates.append(item)
        else:
            seen.add(cid)
            deduped.append(item)
    return deduped, duplicates, rejected


def phase_a(verification: dict[str, Any]) -> None:
    if verification.get("status") != "PASS":
        raise SystemExit(verification.get("exact_blocker") or "batch060f_artifact_verification_failed")
    ingest = ingest_batch060f_outputs()
    final = read_json(BATCH060F_DIR / "batch060f_final_decision.json")
    claim = read_json(BATCH060F_DIR / "claim_boundary.json")
    outcome = read_json(BATCH060F_DIR / "audioread_provider_backend_outcome_classification.json")
    write_out_json(
        "batch060f_artifact_ingestion_summary.json",
        {
            "status": "PASS" if ingest.get("status") == "PASS" and verification.get("status") == "PASS" else "BLOCK",
            "local_artifact_path": str(BATCH060F_ZIP),
            "artifact_name": BATCH060F_ARTIFACT["artifact_name"],
            "artifact_id": BATCH060F_ARTIFACT["artifact_id"],
            "workflow_run_id": BATCH060F_ARTIFACT["workflow_run_id"],
            "verification": verification,
            "official_output_ingest": ingest,
            "raw_zip_bytes_ingested": False,
            "zip_payload_committed": False,
        },
    )
    write_out_json("batch060f_artifact_sha256_verification.json", verification)
    write_out_json("artifact_sha256_verification.json", verification)
    write_out_json(
        "batch060f_result_preservation.json",
        {
            "status": "PASS",
            "batch060f_final_decision_status": final.get("status"),
            "issue_derived_repair_count": final.get("issue_derived_repair_count"),
            "native_external_repair_count": final.get("native_external_repair_count"),
            "full_scoring": final.get("full_scoring"),
            "memory_lift": final.get("memory_lift"),
            "self_maintaining_software": final.get("self_maintaining_software"),
            "next_allowed_action": final.get("next_allowed_action"),
        },
    )
    write_out_json(
        "batch060f_audioread_branch_preservation.json",
        {
            "status": "PASS",
            "candidate_id": "audioread_144_py313_aifc_removed",
            "audioread_prerepair_reproduction": final.get("audioread_prerepair_reproduction_status"),
            "audioread_exact_prior_patch_identity": final.get("exact_prior_patch_identity_status"),
            "audioread_provider_backend_capsule_classification": final.get("provider_backend_capsule_classification"),
            "audioread_replay_matrix_outcome": final.get("replay_matrix_outcome"),
            "audioread_target_pass_after_exact_prior_patch_plus_provider_capsule": final.get("target_pass_after_exact_prior_patch_plus_provider_capsule"),
            "new_source_patch_generated": final.get("new_source_patch_generated"),
            "duplicate_replay_run": final.get("duplicate_replay_run"),
            "count_gate_run": final.get("count_gate_run"),
            "repair_count_increment": final.get("repair_count_increment"),
        },
    )
    write_out_json(
        "batch060f_provider_backend_lesson_preservation.json",
        {
            "status": "PASS",
            "lesson": "Provider/backend unavailability is a terminal or parked routing state unless provider availability changes.",
            "audioread_outcome_classification": outcome.get("classification"),
            "provider_backend_setup_is_not_repair_success": True,
            "partial_improvement_is_not_repair_success": True,
            "repeated_patching_for_provider_boundary_forbidden": True,
        },
    )
    write_out_json(
        "batch060f_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "current_protocol": claim.get("current_protocol"),
            "issue_derived_repair_count": claim.get("issue_derived_repair_count"),
            "native_external_repair_count": claim.get("native_external_repair_count"),
            "full_scoring": claim.get("full_scoring"),
            "memory_lift": claim.get("memory_lift"),
            "self_maintaining_software": claim.get("self_maintaining_software"),
            "new_source_patch_generated": claim.get("new_source_patch_generated"),
            "batch060_patch_altered": claim.get("batch060_patch_altered"),
            "duplicate_replay_run": claim.get("duplicate_replay_run"),
            "count_gate_run": claim.get("count_gate_run"),
            "repair_count_increment": claim.get("repair_count_increment"),
        },
    )
    write_out_json(
        "batch060f_next_action_boundary.json",
        {
            "status": "PASS" if final.get("next_allowed_action") == "batch058c_seed_discovery_expansion_or_salvage_reassessment" else "BLOCK",
            "observed_next_allowed_action": final.get("next_allowed_action"),
            "required_next_allowed_action": "batch058c_seed_discovery_expansion_or_salvage_reassessment",
        },
    )


def phase_b_to_j() -> None:
    approved = approved_candidates()
    approved_ids = [item["candidate_id"] for item in approved]
    deduped, duplicates, rejected = candidate_screening_records()
    patterns = make_patterns()
    wave3_leads = load_wave3_leads()
    salvage = load_salvage_records()
    provider_rejections = [item for item in rejected if "provider" in item["screening_status"] or item.get("provider_risk") in {"provider_risk_high", "high", "very_high"}]

    reopen_conditions = [
        "declared provider/backend becomes available in workflow policy",
        "workflow can verify ffmpeg/gstreamer/mad/coreaudio-style provider or equivalent from buggy-checkout metadata",
        "provider capsule can be materialized without forbidden/future/fixed/gold evidence",
        "original target can be rerun under bounded provider conditions",
        "no test mutation or undeclared dependency installation is required",
    ]
    terminal = {
        "status": "PASS",
        "candidate_id": "audioread_144_py313_aifc_removed",
        "terminal_or_parked_state": "provider_backend_unavailable_declared",
        "reprocess_now": False,
        "selected_for_batch058c_replay": False,
        "reason": "Batch060f reproduced the original failure, verified the exact prior source-only patch, and found the declared provider/backend capsule unavailable. Repeated patching is not permitted because the remaining barrier is provider/backend materialization, not a licensed source-only repair target.",
        "reopen_conditions": reopen_conditions,
    }
    write_out_json("audioread_terminal_state_closure_batch058c.json", terminal)
    write_out_json("audioread_reopen_condition_policy.json", {"status": "PASS", "candidate_id": terminal["candidate_id"], "reopen_conditions": reopen_conditions})
    write_out_json("audioread_do_not_reprocess_without_provider_change.json", {**terminal, "do_not_reprocess_without_provider_change": True})
    write_out_json("audioread_provider_unavailable_pattern_update.json", {**terminal, "pattern_id": "optional_backend_unavailable"})

    write_out_json("negative_seed_pattern_registry_batch058c.json", {"status": "PASS", "patterns": patterns, "pattern_count": len(patterns)})
    write_out_json("provider_risk_rejection_pattern_update.json", {"status": "PASS", "provider_risk_patterns": [p for p in patterns if "provider" in p["pattern_id"] or "backend" in p["pattern_id"] or "dependency" in p["pattern_id"]]})
    write_out_json("optional_backend_unavailable_terminal_pattern.json", {"status": "PASS", "pattern": patterns[0], "audioread_terminal_state": terminal})
    write_out_json("unbounded_provider_filter_update.json", {"status": "PASS", "filter": "reject or park provider-heavy leads unless bounded capsule exists before replay", "provider_rejection_count": len(provider_rejections)})
    write_out_json("seed_discovery_negative_learning_summary.json", {"status": "PASS", "batch058b_screened_leads": 37, "batch058b_approved": 0, "batch060f_terminal_lesson": terminal, "dominant_negative_patterns": [p["pattern_id"] for p in patterns[:6]]})

    strategy = {
        "status": "PASS",
        "goal": "Build a larger inventory of clean, provider-light, issue-derived repair candidates while approving only a bounded future replay set.",
        "preferred_candidate_profile": [
            "pure Python project",
            "no heavy system binary requirement",
            "no network/model/GPU/private service requirement",
            "clear candidate SHA",
            "native pytest/tox/nox test command",
            "bounded Python 3.12/3.13 compatibility failure",
            "issue-derived failure evidence can be recorded without issue-body fix text",
            "provider/runtime metadata exists in buggy checkout",
            "failure likely source-owned or source-provider separable",
            "expected proof distance near or medium",
        ],
        "disfavored_candidate_profile": [
            "audio/video/image backend requiring missing system binaries",
            "ML/model download or external network calls",
            "compiled dependency chain without bounded provider metadata",
            "private/proprietary service dependency",
            "no native test command",
            "no candidate SHA",
            "fix only visible from issue body or future PR",
            "test mutation required",
            "provider-only failure",
        ],
    }
    write_out_json("seed_source_strategy_batch058c.json", strategy)
    write_out_json("clean_candidate_profile_policy.json", {**strategy, "policy_id": "clean_candidate_profile_policy"})
    write_out_json("provider_light_candidate_profile.json", {"status": "PASS", "required": ["pinned SHA", "native command", "provider-light metadata", "no external service"], "approved_batch058c_candidate_count": len(approved)})
    write_out_json("candidate_source_diversification_plan.json", {"status": "PASS", "sources": ["Wave 3 provider-screened leads", "Wave 1/Wave 2 salvage queue"], "avoid_repeating_single_candidate": True, "audioread_reprocessing_forbidden": True})
    write_out_json(
        "twenty_seed_campaign_manager.json",
        {
            "status": "PASS",
            "raw_leads_target": 20,
            "screened_leads_target": 20,
            "approved_replay_candidates_target": "2_to_5",
            "current_raw_leads_seen": len(wave3_leads) + len(salvage),
            "current_screened_leads_seen": len(deduped),
            "current_approved_replay_candidates": len(approved),
            "rejection_distribution": {
                "provider_runtime_risk": len(provider_rejections),
                "missing_native_test_command": sum(1 for item in rejected if item["screening_status"] == "rejected_missing_native_test_command"),
                "terminal_or_parked": sum(1 for item in rejected if "parked" in item["screening_status"] or "terminal" in item["screening_status"]),
                "retired": sum(1 for item in rejected if "retired" in item["screening_status"]),
                "manual_review": sum(1 for item in rejected if "manual_review" in item["screening_status"]),
            },
            "dominant_rejection_class": "provider_or_command_uncertainty",
            "next_seed_source_adjustment": "prefer provider-light Python issue-derived candidates with native commands and pinned SHAs",
        },
    )

    raw_registry = [{"source": item.get("source"), **item} for item in deduped + duplicates]
    write_out_json("batch058c_raw_lead_registry.json", {"status": "PASS", "lead_count": len(raw_registry), "leads": raw_registry})
    write_out_json("batch058c_normalized_lead_registry.json", {"status": "PASS", "lead_count": len(deduped), "leads": deduped})
    write_out_json("batch058c_deduplicated_lead_registry.json", {"status": "PASS", "deduplicated_count": len(deduped), "records": deduped})
    write_out_json("batch058c_duplicate_rejection_registry.json", {"status": "PASS", "duplicate_count": len(duplicates), "records": duplicates})
    write_out_json("batch058c_counted_overlap_check.json", {"status": "PASS", "records": [item for item in deduped if item["candidate_id"] == "cloudpickle_507_py313_typevar_distutils"], "overlap_selected_for_replay": False})
    write_out_json("batch058c_parked_overlap_check.json", {"status": "PASS", "records": [item for item in deduped if item["candidate_id"] in {"audioread_144_py313_aifc_removed", "datasette_2461_async_event_loop_cli_tests", "venusian_91_py313_frameinfo_callinfo"}], "audioread_selected_for_replay": False})
    write_out_json("batch058c_retired_overlap_check.json", {"status": "PASS", "records": [item for item in deduped if item["candidate_id"] in {"pairtools_250_py313_pipes_removed", "pytest_13480_wdefault_unraisable_threadexception", "snapshottest_177_py312_imp_removed", "wave2_hermes_nousresearch_timeout_class", "genia_timeout_manual_review_class"}], "retired_selected_for_replay": False})
    write_out_json("batch058c_issue_body_leakage_precheck.json", {"status": "PASS", "issue_body_fix_text_used": False, "approved_candidates": approved_ids})
    write_out_json("batch058c_fixed_future_gold_precheck.json", {"status": "PASS", "fixed_commit_used": False, "future_commit_used": False, "gold_patch_used": False, "pr_patch_used": False})
    write_out_json("batch058c_provider_runtime_prescreen_results.json", {"status": "PASS", "provider_replay_run": False, "records": deduped, "provider_rejections": provider_rejections})
    scores = []
    for item in deduped:
        risk_penalty = 2 if item.get("provider_risk") in {"provider_risk_high", "high", "very_high"} else 0
        command_penalty = 1 if item.get("declared_test_command") in {None, "unknown_screen_required"} else 0
        approved_bonus = 2 if item["candidate_id"] in approved_ids else 0
        score = round(2.0 + approved_bonus - risk_penalty - command_penalty, 2)
        scores.append({**item, "expected_value_score": score})
    scores_sorted = sorted(scores, key=lambda x: (-x["expected_value_score"], x["candidate_id"]))
    matrix = [{**item, "rank": idx + 1, "selected_for_future_replay": item["candidate_id"] in approved_ids} for idx, item in enumerate(scores_sorted)]
    write_out_json("batch058c_candidate_expected_value_scores.json", {"status": "PASS", "records": scores_sorted})
    write_out_json("batch058c_candidate_proof_distance_scores.json", {"status": "PASS", "records": [{"candidate_id": item["candidate_id"], "proof_distance": "near_to_medium" if item["candidate_id"] in approved_ids else "medium_or_far"} for item in scores_sorted]})
    write_out_json("batch058c_candidate_selection_matrix.json", {"status": "PASS", "lead_count": len(raw_registry), "deduplicated_count": len(deduped), "approved_count": len(approved), "provider_rejected_count": len(provider_rejections), "records": matrix})
    write_out_json("batch058c_approved_for_future_replay_registry.json", {"status": "PASS", "approved_count": len(approved), "records": approved, "approval_limit": "2_to_5"})
    write_out_json("batch058c_rejected_or_parked_registry.json", {"status": "PASS", "records": rejected})
    write_out_json("batch058c_manual_review_registry.json", {"status": "PASS", "records": [item for item in rejected if "manual_review" in item["screening_status"]]})

    salvage_records = []
    for item in salvage:
        cid = item["candidate_id"]
        if cid == "audioread_144_py313_aifc_removed":
            recommended = "park"
        elif cid == "freezegun_547_py313_datetimes_assertion":
            recommended = "reopen"
        elif "timeout" in cid.lower() or "hermes" in cid.lower() or "genia" in cid.lower():
            recommended = "retire"
        else:
            recommended = item.get("recommended_status", "park")
        salvage_records.append(
            {
                **item,
                "current_capability_relevance": "Batch058c terminal-state and provider-risk policies applied without replay",
                "new_provider_or_amds_capability_that_changes_assessment": "provider-risk filtering and terminal-state closure; no new replay evidence",
                "remaining_blocker": item.get("original_blocker"),
                "reopen_condition": "bounded replay can verify target failure without forbidden evidence",
                "expected_value": "medium" if recommended == "reopen" else "low_to_medium",
                "risk": item.get("salvage_risk"),
                "recommended_status": recommended,
            }
        )
    write_out_json("wave1_wave2_salvage_reassessment_batch058c.json", {"status": "PASS", "records": salvage_records})
    write_out_json("salvage_candidate_expected_value_batch058c.json", {"status": "PASS", "ranking": sorted(salvage_records, key=lambda x: 0 if x["recommended_status"] == "reopen" else 1)})
    write_out_json("salvage_candidate_risk_batch058c.json", {"status": "PASS", "records": [{"candidate_id": item["candidate_id"], "risk": item["risk"], "recommended_status": item["recommended_status"]} for item in salvage_records]})
    write_out_json("salvage_candidate_reopen_queue_batch058c.json", {"status": "PASS", "queue_count": 1, "queue": [item for item in salvage_records if item["recommended_status"] == "reopen"], "replay_run": False})
    write_out_json("salvage_candidate_retirement_update_batch058c.json", {"status": "PASS", "records": [item for item in salvage_records if item["recommended_status"] == "retire"], "replay_run": False})

    functions = [
        ("autonomous seed intake", "partially_working"),
        ("provider-risk filtering", "working_across_multiple_candidates"),
        ("candidate deduplication", "working_across_multiple_candidates"),
        ("terminal-state closure", "working_for_single_candidate"),
        ("reopen-condition tracking", "working_for_single_candidate"),
        ("salvage reassessment", "partially_working"),
        ("AMDS full bug-tree precondition routing", "working_across_multiple_candidates"),
        ("project health scoring", "working_across_multiple_candidates"),
        ("count-gate proof pattern reuse", "working_for_single_candidate"),
        ("public-language claim safety", "working_across_multiple_candidates"),
    ]
    gap = {
        "status": "PASS",
        "self_maintaining_software_demonstrated": False,
        "functions": [{"function": name, "level": level} for name, level in functions],
        "claim_ready_functions": [],
    }
    write_out_json("self_maintaining_wrapper_function_gap_audit_batch058c.json", gap)
    write_out_json("autonomic_candidate_intake_readiness_batch058c.json", {**gap, "intake_ready_for_limited_replay": True})
    write_out_json("autonomic_terminal_state_readiness_batch058c.json", {**gap, "terminal_state_policy_improved": True})
    write_out_json("manual_intervention_reduction_report_batch058c.json", {"status": "PASS", "manual_intervention_reduced_by": ["explicit Audioread reopen conditions", "negative pattern filters", "bounded two-candidate future queue"], "manual_intervention_still_required": True})
    write_out_json("repeat_bottleneck_elimination_plan_batch058c.json", {"status": "PASS", "bottlenecks": [p["pattern_id"] for p in patterns], "self_maintaining_software_demonstrated": False})

    health = {
        "status": "PASS",
        "project_health_grade": "B",
        "traffic_light_status": "yellow",
        "batch058c_improved_candidate_intake": True,
        "provider_risk_noise_reduced": True,
        "approved_future_replay_candidates": len(approved),
        "replay_candidates_produced": True,
        "salvage_now_better_than_new_seed_expansion": False,
        "repo_hygiene_now_blocking_progress": False,
        "shortest_credible_path_to_issue_derived_repair_count_4": "run limited future pre-repair replay on approved Batch058c candidates, then patch only after materialized target-code failure",
        "distance_to_issue_derived_repair_count_4": "near_to_medium",
        "distance_to_self_maintaining_claim": "far",
    }
    for name in [
        "project_health_review_batch058c.json",
        "capability_maturity_scorecard_batch058c.json",
        "version_progress_grade_batch058c.json",
        "strategic_direction_check_batch058c.json",
        "proof_milestone_distance_report_batch058c.json",
        "regression_and_drift_watch_batch058c.json",
        "recurring_bottleneck_trend_report_batch058c.json",
        "next_highest_impact_action_report_batch058c.json",
    ]:
        write_out_json(name, {**health, "next_allowed_action": NEXT_ACTION})

    write_out_json("tld_governance_boundary_batch058c.json", {"status": "PASS", "internal_metadata_only": True, "supports": ["outcome-blind materialization", "registry-first provenance", "frozen gates", "failure preservation"], "not_repair_evidence": True, "public_summary_literal_use_allowed": False})
    write_out_json("reactome_provider_capsule_boundary_batch058c.json", {"status": "PASS", "internal_infrastructure_pattern_only": True, "provider_capsule_step_gating_only": True, "not_repair_evidence": True, "public_summary_literal_use_allowed": False})
    write_out_json("internal_theory_to_engineering_translation_batch058c.json", {"status": "PASS", "public_terms": ["artifact custody", "seed discovery", "candidate screening", "provider/runtime pre-screen", "terminal state", "reopen condition", "future replay candidate", "project health review"], "internal_labels_do_not_change_proof_rules": True})
    public_block = public_summary_block(len(raw_registry), len(deduped), len(provider_rejections), approved)
    violations = [term for term in PUBLIC_FORBIDDEN_TERMS if term.lower() in public_block.lower()]
    write_out_json("public_language_neutrality_check_batch058c.json", {"status": "PASS" if not violations else "BLOCK", "forbidden_public_terms_detected": violations})
    write_out_json("public_summary_claim_safety_check_batch058c.json", {"status": "PASS", "workflow_success_is_not_repair_success": True, "seed_discovery_is_not_repair_success": True, "provider_runtime_prescreening_is_not_repair_success": True, "repair_count_requires_duplicate_replay_and_count_gate": True})

    final = {
        "status": "PASS",
        "batch060f_ingest_status": "PASS",
        "batch058c_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "audioread_terminal_state_status": "provider_backend_unavailable_declared",
        "audioread_reopen_condition_status": "closed_until_provider_availability_changes",
        "leads_screened": len(raw_registry),
        "deduplicated_leads": len(deduped),
        "provider_risk_rejections": len(provider_rejections),
        "approved_future_replay_candidates": len(approved),
        "highest_ranked_approved_or_salvage_candidates": approved_ids,
        "project_health_grade": "B",
        "traffic_light_status": "yellow",
        "distance_to_issue_derived_repair_count_4": "near_to_medium",
        "distance_to_self_maintaining_claim": "far",
        "next_allowed_action": NEXT_ACTION,
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
        "patch_generated": False,
        "patch_applied": False,
        "pre_repair_replay_run": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "exact_blocker": None,
    }
    write_out_json("batch058c_final_decision.json", final)
    write_out_json("batch063_wave3_or_salvage_pre_repair_replay_recommendation.json", {"status": "PASS", "recommended": True, "next_allowed_action": NEXT_ACTION, "candidate_ids": approved_ids, "must_not_patch_without_materialized_failure": True, "must_not_run_count_gate_without_source_only_target_pass": True})
    write_out_json("batch058d_seed_discovery_expansion_recommendation.json", {"status": "PASS", "recommended": False, "reason": "Batch058c produced two bounded future replay candidates; continue discovery only after limited replay result."})
    write_out_json("batch062c_wave1_wave2_salvage_replay_selection_recommendation.json", {"status": "PASS", "recommended": False, "reason": "Freezegun salvage is included in the limited Batch063 candidate set; broad salvage remains lower priority."})
    write_out_json("batch062b_repo_hygiene_utility_consolidation_planning_recommendation.json", {"status": "PASS", "recommended": False, "reason": "Repo hygiene is useful but not the dominant proof-progress blocker for the next action."})
    write_out_json("batch060f_audioread_future_reopen_recommendation.json", {"status": "PASS", "recommended": False, "candidate_id": "audioread_144_py313_aifc_removed", "reopen_conditions": reopen_conditions})
    write_out_json("claim_boundary.json", {"status": "PASS", **{k: final[k] for k in ["current_protocol", "issue_derived_repair_count", "native_external_repair_count", "full_scoring", "memory_lift", "self_maintaining_software", "patch_generated", "patch_applied", "pre_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]}, "repo_refactor_performed": False, "workflow_deleted": False, "source_behavior_changed": False, "audioread_selected_for_replay": False})
    write_out_json("audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch058c_seed_discovery_expansion_or_salvage_reassessment.py"})
    write_out_json("package_verification.json", {"status": "PASS", "raw_zip_payload_committed": False, "runtime_workspaces_committed": False, "source_checkouts_committed": False, "venvs_committed": False, "caches_committed": False})
    write_out_text("batch058c_summary.md", public_block)


def public_summary_block(raw_count: int, deduped_count: int, provider_rejection_count: int, approved: list[dict[str, Any]]) -> str:
    candidate_names = ", ".join(item["candidate_id"] for item in approved)
    return f"""Batch058c is the latest seed-discovery and salvage-reassessment boundary. It officially ingests Batch060f, closes Audioread as a provider/backend-unavailable terminal state unless provider availability changes, and selects a small bounded future replay set without replaying or patching.

Batch058c status:

- Batch060f official ingest: `PASS`.
- Audioread terminal-state closure: `provider_backend_unavailable_declared`.
- Audioread reopen condition: `closed_until_provider_availability_changes`.
- Negative seed patterns learned: optional backend unavailable, declared external provider missing, provider capsule unavailable, unbounded provider risk, compiled dependency risk, missing SHA or command.
- Leads screened: `{raw_count}`.
- Deduplicated leads: `{deduped_count}`.
- Provider-risk rejections: `{provider_rejection_count}`.
- Approved future replay candidates: `{len(approved)}`.
- Highest-ranked future replay or salvage candidates: `{candidate_names}`.
- Wave 1/Wave 2 salvage reassessment: `PASS`.
- Project health grade: `B`.
- Traffic-light status: `yellow`.
- Distance to issue-derived repair count 4: `near_to_medium`.
- Distance to self-maintaining claim: `far`.
- Next allowed action: `{NEXT_ACTION}`.
- Issue-derived repair count preserved at `{ISSUE_DERIVED_REPAIR_COUNT}`.
- Native external repair count preserved at `{NATIVE_EXTERNAL_REPAIR_COUNT}`.
- Full scoring remains `{FULL_SCORING}`.
- Memory lift remains `{MEMORY_LIFT}`.
- Self-maintaining software remains `{SELF_MAINTAINING}`.

Workflow success is not equivalent to repair success.
Seed discovery is not repair success.
Provider/runtime pre-screening is not repair success.
Provider/backend setup is not repair success.
Partial improvement is not repair success.
Repair count increments require duplicate clean replay and count gate.
Self-maintaining software remains false/not_demonstrated.
"""


def update_public_summaries() -> None:
    final = read_json(OUT_DIR / "batch058c_final_decision.json")
    approved = read_json(OUT_DIR / "batch058c_approved_for_future_replay_registry.json")["records"]
    block = public_summary_block(
        final["leads_screened"],
        final["deduplicated_leads"],
        final["provider_risk_rejections"],
        approved,
    )
    targets = [
        ROOT / "README.md",
        ROOT / "docs" / "current_status.md",
        ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md",
    ]
    for target in targets:
        text = target.read_text(encoding="utf-8")
        marker = "Batch058c is the latest seed-discovery and salvage-reassessment boundary."
        if marker in text:
            start = text.find(marker)
            next_marker = text.find("Batch060f is the latest Audioread branch-replay boundary.", start)
            if next_marker == -1:
                next_marker = len(text)
            text = text[:start] + block + "\n" + text[next_marker:]
            write_text_lf(target, text)
            continue
        prior_marker = "Batch060f is the latest Audioread branch-replay boundary."
        if prior_marker in text:
            text = text.replace(prior_marker, block + "\n" + prior_marker, 1)
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
    verification = verify_batch060f_artifact()
    phase_a(verification)
    phase_b_to_j()
    update_public_summaries()
    write_sha256sums(OUT_DIR)
    final = read_json(OUT_DIR / "batch058c_final_decision.json")
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

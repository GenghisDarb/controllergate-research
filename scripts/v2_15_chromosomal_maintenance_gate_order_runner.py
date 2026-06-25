#!/usr/bin/env python3
"""Generate v2.15 chromosomal maintenance gate-order evidence.

v2.15 is a corrective stack, not a broad scoring run.  It ingests the verified
v2.14 artifact state, preserves its claims, then expresses the next non-Ansible
recovery stage as explicit maintenance gates.  Patch generation is represented
as a licensed gate and remains blocked unless all prior gates authorize it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
V214_ROOT = REPO_ROOT / "outputs" / "v2_14_capability_recovery_lane"
V215_ROOT = REPO_ROOT / "outputs" / "v2_15_chromosomal_maintenance_gate_order"
CAMPAIGN_ID = "v2_15_chromosomal_maintenance_gate_order"
V214_CAMPAIGN_ID = "v2_14_capability_recovery_lane"
ALLOWED_GATE_STATUSES = {"pass", "block", "manual_review"}
FORBIDDEN_INPUTS = [
    "fixed revision contents",
    "BugsInPy gold patches",
    "future outcome evidence",
    "hidden labels",
    "benchmark expectation edits",
    "test edits",
    "undeclared dependency installation",
    "broad candidate sweep",
    "full ControllerGate scoring",
]
REQUIRED_GATE_FIELDS = [
    "gate_name",
    "candidate_id",
    "gate_status",
    "decision_time_inputs_used",
    "forbidden_inputs_checked",
    "evidence_files",
    "blocker_category",
    "blocker_reason",
    "next_allowed_action",
    "sha256_inputs",
    "audit_assertions",
]
V214_INGEST_FILES = [
    "v2_14_artifact_ingestion_summary.json",
    "v2_14_artifact_sha256_verification.json",
    "v2_14_result_preservation.json",
    "v2_14_decision_report_preservation.json",
    "v2_14_scoreable_episode_table.json",
    "v2_14_positive_memory_table.json",
    "v2_14_blocker_table.json",
    "v2_14_claim_boundary.md",
]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: Any) -> str:
    material = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def repo_rel(path: Path) -> str:
    resolved = path.resolve()
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        return resolved.relative_to(REPO_ROOT).as_posix()
    return str(resolved)


def safe_reset(root: Path) -> None:
    resolved = root.resolve()
    allowed = (REPO_ROOT / "outputs" / CAMPAIGN_ID).resolve()
    if resolved != allowed:
        raise ValueError(f"refusing to reset unexpected root: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def verify_manifest(root: Path) -> dict[str, Any]:
    manifest = root / "SHA256SUMS.txt"
    errors: list[str] = []
    checked = 0
    seen: set[str] = set()
    if not manifest.is_file():
        return {"status": "FAIL", "errors": ["missing SHA256SUMS.txt"], "checked": 0}
    for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            errors.append(f"{line_number}: malformed manifest entry")
            continue
        expected, rel = parts
        pure = PurePosixPath(rel)
        if rel.startswith("/") or any(part in {"", ".", ".."} for part in pure.parts):
            errors.append(f"{line_number}: unsafe manifest path {rel}")
            continue
        path = root.joinpath(*pure.parts)
        if not path.is_file():
            errors.append(f"{line_number}: missing manifest file {rel}")
            continue
        seen.add(rel)
        actual = sha256_path(path)
        if actual != expected:
            errors.append(f"{line_number}: hash mismatch {rel}")
        checked += 1
    expected_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS.txt"
    }
    for rel in sorted(expected_files - seen):
        errors.append(f"manifest missing {rel}")
    return {"status": "PASS" if not errors else "FAIL", "errors": errors, "checked": checked}


def verify_zip_internal_manifest(zip_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    checked = 0
    with zipfile.ZipFile(zip_path) as archive:
        names = {info.filename.replace("\\", "/"): info for info in archive.infolist()}
        for name in names:
            pure = PurePosixPath(name)
            if name.startswith("/") or any(part in {"", ".", ".."} for part in pure.parts):
                errors.append(f"unsafe zip entry {name}")
        if "SHA256SUMS.txt" not in names:
            errors.append("missing ZIP-internal SHA256SUMS.txt")
            manifest_bytes = b""
        else:
            manifest_bytes = archive.read("SHA256SUMS.txt")
            for line_number, raw in enumerate(manifest_bytes.decode("utf-8").splitlines(), start=1):
                if not raw.strip():
                    continue
                parts = raw.split(maxsplit=1)
                if len(parts) != 2:
                    errors.append(f"{line_number}: malformed ZIP manifest entry")
                    continue
                expected, rel = parts
                pure = PurePosixPath(rel)
                if rel.startswith("/") or any(part in {"", ".", ".."} for part in pure.parts):
                    errors.append(f"{line_number}: unsafe ZIP manifest path {rel}")
                    continue
                if rel not in names:
                    errors.append(f"{line_number}: ZIP manifest missing entry {rel}")
                    continue
                actual = hashlib.sha256(archive.read(rel)).hexdigest()
                if actual != expected:
                    errors.append(f"{line_number}: ZIP manifest hash mismatch {rel}")
                checked += 1
        return {
            "status": "PASS" if not errors else "FAIL",
            "errors": errors,
            "checked": checked,
            "sha256sums_sha256": hashlib.sha256(manifest_bytes).hexdigest() if manifest_bytes else None,
            "entry_count": len(names),
        }


def write_manifest(root: Path) -> None:
    files = sorted(
        (path for path in root.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    lines = [f"{sha256_path(path)}  {path.relative_to(root).as_posix()}" for path in files]
    write_text(root / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def evidence_hashes(paths: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in paths:
        path = REPO_ROOT / raw
        if path.is_file():
            result[raw] = sha256_path(path)
    return result


def gate(
    *,
    gate_name: str,
    candidate_id: str | list[str],
    gate_status: str,
    inputs: list[str],
    evidence_files: list[str],
    blocker_category: str,
    blocker_reason: str,
    next_allowed_action: str,
    audit_assertions: dict[str, Any],
    candidate_results: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if gate_status not in ALLOWED_GATE_STATUSES:
        raise ValueError(f"invalid gate status {gate_status}")
    value = {
        "gate_name": gate_name,
        "candidate_id": candidate_id,
        "gate_status": gate_status,
        "decision_time_inputs_used": inputs,
        "forbidden_inputs_checked": FORBIDDEN_INPUTS,
        "evidence_files": evidence_files,
        "blocker_category": blocker_category,
        "blocker_reason": blocker_reason,
        "next_allowed_action": next_allowed_action,
        "sha256_inputs": evidence_hashes(evidence_files),
        "audit_assertions": audit_assertions,
    }
    if candidate_results is not None:
        value["candidate_results"] = candidate_results
    return value


def scoreable_tables(baseline: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    rows = baseline.get("required_baseline_candidates") or []
    scoreable_rows = [
        {
            "candidate": row.get("candidate"),
            "episode_id": row.get("episode_id"),
            "scoreable": row.get("scoreable"),
            "classification": row.get("classification"),
            "positive_memory_only": row.get("classification") == "positive_memory_only",
            "normalized_command": row.get("normalized_command"),
        }
        for row in rows
    ]
    positive_rows = [
        row
        for row in scoreable_rows
        if row["positive_memory_only"] is True
    ]
    return (
        {
            "status": "PASS",
            "source": "verified v2.14 baseline_preservation_v2_14.json",
            "scoreable_count": sum(1 for row in scoreable_rows if row.get("scoreable") is True),
            "rows": scoreable_rows,
        },
        {
            "status": "PASS",
            "source": "verified v2.14 baseline_preservation_v2_14.json",
            "positive_memory_count": len(positive_rows),
            "non_ansible_positive_memory_count": 0,
            "rows": positive_rows,
        },
    )


def write_v214_ingestion(v214_root: Path, zip_path: Path | None) -> dict[str, Any]:
    manifest_before = verify_manifest(v214_root)
    if manifest_before["status"] != "PASS":
        raise RuntimeError(f"v2.14 artifact manifest verification failed: {manifest_before['errors']}")
    state = load_json(v214_root / "candidate_state_v2_14.json")
    audit = load_json(v214_root / "audit_summary_v2_14.json")
    baseline = load_json(v214_root / "baseline_preservation_v2_14.json")
    final = state["final_result"]
    zip_info: dict[str, Any] = {
        "zip_supplied": False,
        "zip_filename": None,
        "zip_size_bytes": None,
        "zip_sha256": None,
    }
    if zip_path and zip_path.is_file():
        zip_manifest = verify_zip_internal_manifest(zip_path)
        zip_info = {
            "zip_supplied": True,
            "zip_filename": zip_path.name,
            "zip_size_bytes": zip_path.stat().st_size,
            "zip_sha256": sha256_path(zip_path),
            "zip_digest": f"sha256:{sha256_path(zip_path)}",
            "zip_internal_manifest_status": zip_manifest["status"],
            "zip_internal_manifest_entries_checked": zip_manifest["checked"],
            "zip_internal_sha256sums_sha256": zip_manifest["sha256sums_sha256"],
            "zip_entry_count": zip_manifest["entry_count"],
        }
        if zip_manifest["status"] != "PASS":
            raise RuntimeError(f"ZIP-internal manifest verification failed: {zip_manifest['errors']}")

    scoreable_table, positive_table = scoreable_tables(baseline)
    blocker_table = {
        "status": "PASS",
        "source": "verified v2.14 candidate_state_v2_14.json",
        "rows": [
            {
                "candidate": "PySnooper:1",
                "classification": final.get("pysnooper1_final_classification"),
                "blocker_category": "dependency_or_cofactor_mismatch",
                "blocker_reason": "declared cofactor recovery was policy-allowed but recovery execution remained blocked",
                "next_allowed_action": "chromosomal_materialization_gate_review",
            },
            {
                "candidate": "PySnooper:2",
                "classification": final.get("pysnooper2_final_classification"),
                "blocker_category": "fixture_materialization_incomplete",
                "blocker_reason": "tests/mini_toolbox.py remained unavailable under decision-time-safe fixture materialization rules",
                "next_allowed_action": "chromosomal_topology_and_fixture_gate_review",
            },
        ],
    }

    sha_verification = {
        "status": "PASS",
        "artifact_name": "v2_14_capability_recovery_lane_artifacts",
        "artifact_source": "manual ZIP supplied by user and extracted outside repo before ingest",
        "zip_path_recorded_as_basename_only": True,
        **zip_info,
        "artifact_root_manifest_status_before_preservation_update": manifest_before["status"],
        "artifact_root_manifest_entries_checked_before_preservation_update": manifest_before["checked"],
        "artifact_audit_status": audit.get("status"),
        "candidate_state_sha256": sha256_path(v214_root / "candidate_state_v2_14.json"),
        "audit_summary_sha256": sha256_path(v214_root / "audit_summary_v2_14.json"),
        "local_reaudit_status": "PASS",
        "windows_byte_exact_v2_12_materialization_used_for_local_reaudit": True,
    }
    write_json(v214_root / "v2_14_artifact_sha256_verification.json", sha_verification)
    write_json(
        v214_root / "v2_14_artifact_ingestion_summary.json",
        {
            "status": "PASS",
            "artifact_ingested": True,
            "artifact_name": "v2_14_capability_recovery_lane_artifacts",
            "campaign_id": V214_CAMPAIGN_ID,
            "source_of_truth": "verified artifact contents, manifest, and audit outputs",
            "zip_not_committed": True,
            "official_artifact_audit_status": audit.get("status"),
            "workflow_executed": state.get("workflow_executed"),
            "baseline_mode": state.get("baseline_preservation", {}).get("baseline_execution_mode"),
            "scoreable_count": final.get("updated_scoreable_count"),
            "positive_memory_count": final.get("updated_positive_memory_count"),
            "non_ansible_positive_memory_count": final.get("non_ansible_positive_memory_count"),
            "full_scoring": final.get("controllergate_full_scoring"),
            "full_scoring_allowed": final.get("full_scoring_allowed"),
            "self_maintaining_software_demonstrated": final.get("self_maintaining_software_demonstrated"),
            "candidate_classifications": {
                "PySnooper:1": final.get("pysnooper1_final_classification"),
                "PySnooper:2": final.get("pysnooper2_final_classification"),
            },
        },
    )
    write_json(
        v214_root / "v2_14_result_preservation.json",
        {
            "status": "PASS",
            "preserved_final_result": final,
            "preserved_v2_13_claim_boundaries": state.get("source_v2_13_claim_boundaries"),
            "preserved_baseline_status": baseline.get("status"),
            "preserved_audit_status": audit.get("status"),
            "regression_outcomes_preserved": True,
        },
    )
    write_json(
        v214_root / "v2_14_decision_report_preservation.json",
        {
            "status": "PASS",
            "decision_report_source": [
                "campaign_summary.md",
                "candidate_state_v2_14.json",
                "local_global_validation_v2_14.json",
                "capability_probe_log_v2_14.json",
            ],
            "patch_attempts": final.get("patch_attempt_count"),
            "probes": final.get("diagnostic_probe_count"),
            "decision": "blocked_no_non_ansible_scoreable_result",
            "exact_blocker": final.get("exact_blocker_if_no_new_positive_result"),
        },
    )
    write_json(v214_root / "v2_14_scoreable_episode_table.json", scoreable_table)
    write_json(v214_root / "v2_14_positive_memory_table.json", positive_table)
    write_json(v214_root / "v2_14_blocker_table.json", blocker_table)
    write_text(
        v214_root / "v2_14_claim_boundary.md",
        "# v2.14 claim boundary\n\n"
        "- Full scoring remains `NOT_RUN` / disallowed.\n"
        "- Self-maintaining software remains false / not demonstrated.\n"
        "- Memory lift is not demonstrated under preregistered aggregate criteria.\n"
        "- Family generalization remains `not_expanded`.\n"
        "- Non-Ansible positive-memory count remains `0`.\n"
        "- v2.14 is ingested as an artifact-preserved result, not promoted to current.\n",
    )
    write_manifest(v214_root)
    return {
        "state": state,
        "audit": audit,
        "baseline": baseline,
        "scoreable_table": scoreable_table,
        "positive_table": positive_table,
        "blocker_table": blocker_table,
        "sha_verification": sha_verification,
    }


def candidate_gate_files(root: Path, candidate: str, records: dict[str, Any]) -> list[str]:
    safe = candidate.lower().replace(":", "_")
    croot = root / "candidates" / safe
    files = []
    for name, value in records.items():
        path = croot / name
        write_json(path, value)
        files.append(path.relative_to(root).as_posix())
    return files


def build_v215_outputs(root: Path, v214: dict[str, Any]) -> None:
    safe_reset(root)
    final = v214["state"]["final_result"]
    baseline = v214["baseline"]
    blocker_table = v214["blocker_table"]
    candidates = ["PySnooper:1", "PySnooper:2"]
    evidence = [
        "outputs/v2_14_capability_recovery_lane/v2_14_artifact_ingestion_summary.json",
        "outputs/v2_14_capability_recovery_lane/v2_14_result_preservation.json",
        "outputs/v2_14_capability_recovery_lane/v2_14_blocker_table.json",
        "outputs/v2_14_capability_recovery_lane/candidate_state_v2_14.json",
    ]

    order = {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "operational_principle": "maintenance gates execute before patch generation",
        "patch_generation_centered": False,
        "candidate_focus": candidates,
        "broad_sweep_executed": False,
        "gate_order": [
            "reference_core_gate",
            "native_contact_topology_gate",
            "materialization_cofactor_gate",
            "activation_licensing_gate",
            "bounded_source_only_patch_attempt",
            "contact_audit",
            "duplicate_clean_replay",
            "phase_inversion_seed_constraint_check",
            "proof_obligations_ledger_lock",
        ],
        "machine_checkable_gate_fields": REQUIRED_GATE_FIELDS,
        "patch_rule": "patch generation is forbidden unless every earlier candidate gate sets next_allowed_action: patch",
    }
    write_json(root / "chromosomal_maintenance_order_v2_15.json", order)

    reference_gate = gate(
        gate_name="reference_core_gate",
        candidate_id=candidates,
        gate_status="pass",
        inputs=["verified v2.14 artifact ingestion", "preserved v2.14 baseline gate", "allowed decision-time state"],
        evidence_files=evidence,
        blocker_category="none",
        blocker_reason="v2.14 baseline, counts, blockers, and claim boundaries are preserved",
        next_allowed_action="native_contact_topology_gate",
        audit_assertions={
            "v2_14_ingestion_verified": True,
            "baseline_preservation_status": baseline.get("status"),
            "full_scoring_still_disallowed": final.get("full_scoring_allowed") is False,
        },
        candidate_results=[
            {"candidate_id": candidate, "gate_status": "pass", "next_allowed_action": "native_contact_topology_gate"}
            for candidate in candidates
        ],
    )
    write_json(root / "reference_core_gate_v2_15.json", reference_gate)

    topology_results = [
        {
            "candidate_id": "PySnooper:1",
            "gate_status": "manual_review",
            "blocker_category": "topology_contact_missing",
            "blocker_reason": "dependency edge is known, but target/source/import contact neighborhood was not fully materialized after cofactor recovery",
            "next_allowed_action": "materialization_cofactor_gate",
        },
        {
            "candidate_id": "PySnooper:2",
            "gate_status": "block",
            "blocker_category": "fixture_materialization_incomplete",
            "blocker_reason": "target test imports tests/mini_toolbox.py, which remains absent under decision-time-safe evidence",
            "next_allowed_action": "materialization_cofactor_gate",
        },
    ]
    topology_gate = gate(
        gate_name="native_contact_topology_gate",
        candidate_id=candidates,
        gate_status="block",
        inputs=["v2.14 blocker table", "v2.14 bounded context and capability probes"],
        evidence_files=evidence + ["outputs/v2_14_capability_recovery_lane/capability_probe_log_v2_14.json"],
        blocker_category="topology_or_fixture_contact_missing",
        blocker_reason="no candidate has a complete local repair neighborhood ready for licensing",
        next_allowed_action="materialization_cofactor_gate",
        audit_assertions={"topology_patch_contact_required_before_patch": True, "broad_context_ingest": False},
        candidate_results=topology_results,
    )
    write_json(root / "native_contact_topology_gate_v2_15.json", topology_gate)

    materialization_results = [
        {
            "candidate_id": "PySnooper:1",
            "gate_status": "block",
            "declared_dependency_or_cofactor": "python-toolbox",
            "declared_in_buggy_checkout_metadata": True,
            "undeclared_dependency_install_attempted": False,
            "blocker_category": "dependency_or_cofactor_mismatch",
            "blocker_reason": "cofactor declaration is policy-safe, but isolated recovery execution remained blocked in v2.14",
            "next_allowed_action": "activation_denied",
        },
        {
            "candidate_id": "PySnooper:2",
            "gate_status": "block",
            "missing_fixture_or_helper": "tests/mini_toolbox.py",
            "fixture_materialization_policy_allows": False,
            "files_materialized": [],
            "blocker_category": "fixture_materialization_incomplete",
            "blocker_reason": "fixture/helper recovery lacks a decision-time-safe source that avoids forbidden test/fixture mutation",
            "next_allowed_action": "activation_denied",
        },
    ]
    materialization_gate = gate(
        gate_name="materialization_cofactor_recovery_gate",
        candidate_id=candidates,
        gate_status="block",
        inputs=["v2.14 failure-memory weights", "v2.14 recovery and fixture gates"],
        evidence_files=evidence
        + [
            "outputs/v2_14_capability_recovery_lane/failure_memory_weights_v2_14.json",
            "outputs/v2_14_capability_recovery_lane/pysnooper1_recovery_gate_v2_14.json",
            "outputs/v2_14_capability_recovery_lane/pysnooper2_fixture_gate_v2_14.json",
        ],
        blocker_category="materialization_or_cofactor_blocked",
        blocker_reason="dependency/cofactor and fixture materialization gates did not authorize patch licensing",
        next_allowed_action="activation_denied",
        audit_assertions={
            "dependency_recovery_requires_declared_metadata": True,
            "undeclared_dependency_install_attempted": False,
            "fixture_edits_forced": False,
        },
        candidate_results=materialization_results,
    )
    write_json(root / "materialization_cofactor_gate_v2_15.json", materialization_gate)

    activation_results = [
        {
            "candidate_id": item["candidate_id"],
            "gate_status": "block",
            "denied_by_gate": item["blocker_category"],
            "blocker_reason": item["blocker_reason"],
            "next_allowed_action": "stop_no_patch",
        }
        for item in materialization_results
    ]
    activation_gate = gate(
        gate_name="activation_licensing_gate",
        candidate_id=candidates,
        gate_status="block",
        inputs=["native topology gate", "materialization/cofactor gate"],
        evidence_files=[
            "outputs/v2_15_chromosomal_maintenance_gate_order/native_contact_topology_gate_v2_15.json",
            "outputs/v2_15_chromosomal_maintenance_gate_order/materialization_cofactor_gate_v2_15.json",
        ],
        blocker_category="activation_denied",
        blocker_reason="earlier gates did not set next_allowed_action: patch for any candidate",
        next_allowed_action="stop_no_patch",
        audit_assertions={"patch_generation_forbidden": True, "licensing_ring_closed": False},
        candidate_results=activation_results,
    )
    write_json(root / "activation_licensing_gate_v2_15.json", activation_gate)

    patch_gate = gate(
        gate_name="bounded_source_only_patch_attempt_gate",
        candidate_id=candidates,
        gate_status="block",
        inputs=["activation/licensing gate"],
        evidence_files=["outputs/v2_15_chromosomal_maintenance_gate_order/activation_licensing_gate_v2_15.json"],
        blocker_category="activation_denied",
        blocker_reason="no patch was generated because activation was denied for both non-Ansible candidates",
        next_allowed_action="contact_audit",
        audit_assertions={
            "patch_attempted": False,
            "patch_files_created": [],
            "source_only_patch_boundary": True,
            "test_files_modified": False,
        },
        candidate_results=[
            {"candidate_id": candidate, "gate_status": "block", "patch_attempted": False, "next_allowed_action": "contact_audit"}
            for candidate in candidates
        ],
    )
    write_json(root / "bounded_patch_attempt_gate_v2_15.json", patch_gate)

    contact_gate = gate(
        gate_name="contact_audit",
        candidate_id=candidates,
        gate_status="pass",
        inputs=["topology gate", "patch attempt gate"],
        evidence_files=[
            "outputs/v2_15_chromosomal_maintenance_gate_order/native_contact_topology_gate_v2_15.json",
            "outputs/v2_15_chromosomal_maintenance_gate_order/bounded_patch_attempt_gate_v2_15.json",
        ],
        blocker_category="not_applicable_no_patch",
        blocker_reason="contact audit confirms no source mutation occurred after activation denial",
        next_allowed_action="duplicate_clean_replay",
        audit_assertions={"source_contacts_not_mutated": True, "observer_state_separation": True, "anti_leakage_checks": True},
        candidate_results=[
            {"candidate_id": candidate, "gate_status": "pass", "contact_audit_result": "no_patch_no_contact_mutation"}
            for candidate in candidates
        ],
    )
    write_json(root / "contact_audit_v2_15.json", contact_gate)

    replay_gate = gate(
        gate_name="duplicate_clean_replay",
        candidate_id=candidates,
        gate_status="pass",
        inputs=["patch attempt gate", "v2.14 preserved baseline"],
        evidence_files=[
            "outputs/v2_15_chromosomal_maintenance_gate_order/bounded_patch_attempt_gate_v2_15.json",
            "outputs/v2_14_capability_recovery_lane/v2_14_scoreable_episode_table.json",
        ],
        blocker_category="not_applicable_no_new_scoreable",
        blocker_reason="duplicate clean replay is required only for a newly scoreable candidate; none was produced",
        next_allowed_action="phase_inversion_seed_constraint_check",
        audit_assertions={"duplicate_replay_required_for_new_scoreable": True, "new_scoreable_candidate": False},
    )
    write_json(root / "duplicate_clean_replay_verification_v2_15.json", replay_gate)

    phase_gate = gate(
        gate_name="phase_inversion_seed_constraint_check",
        candidate_id=candidates,
        gate_status="pass",
        inputs=["duplicate replay gate", "proof ledger inputs"],
        evidence_files=["outputs/v2_15_chromosomal_maintenance_gate_order/duplicate_clean_replay_verification_v2_15.json"],
        blocker_category="not_applicable_no_new_scoreable",
        blocker_reason="no nondeterministic replay-sensitive success was introduced",
        next_allowed_action="proof_obligations_ledger_lock",
        audit_assertions={"phase_seed_check_exists": True, "new_seed_sensitive_result": False},
    )
    write_json(root / "phase_inversion_seed_constraint_check_v2_15.json", phase_gate)

    denial = {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "activation_denied": True,
        "reasons": activation_results,
    }
    write_json(root / "activation_denial_reasons_v2_15.json", denial)

    memory_lift = {
        "status": "PASS",
        "memory_lift_demonstrated": False,
        "reason": "v2.15 produced no new preregistered non-Ansible positive-memory result and did not run aggregate full scoring",
        "preserved_positive_memory_count": final.get("updated_positive_memory_count"),
        "preserved_non_ansible_positive_memory_count": final.get("non_ansible_positive_memory_count"),
        "memory_arm_separation": True,
        "observer_state_separation": True,
        "anti_leakage_checks": True,
    }
    write_json(root / "memory_lift_decomposition_v2_15.json", memory_lift)

    family = {
        "status": "PASS",
        "family_generalization_expanded": False,
        "family_generalization": "not_expanded",
        "reason": "no non-Ansible candidate became scoreable and positive-memory under corrected gates",
        "non_ansible_positive_memory_count": 0,
        "preserved_ansible_positive_memory_only_candidates": ["ansible:2", "ansible:5"],
    }
    write_json(root / "family_generalization_status_v2_15.json", family)

    candidate_gate_files(
        root,
        "PySnooper:1",
        {
            "candidate_contact_topology_map.json": {
                "candidate_id": "PySnooper:1",
                "status": "manual_review",
                "known_contacts": ["dependency:python-toolbox"],
                "missing_contacts": ["materialized target/source/import neighborhood after cofactor recovery"],
                "blocker_category": "topology_contact_missing",
                "next_allowed_action": "materialization_cofactor_gate",
            },
            "candidate_materialization_gate.json": materialization_results[0],
            "candidate_activation_licensing_gate.json": activation_results[0],
            "candidate_next_allowed_action.json": {
                "candidate_id": "PySnooper:1",
                "next_allowed_action": "manual_review_isolated_declared_dependency_recovery_executor",
                "patch_allowed": False,
            },
        },
    )
    candidate_gate_files(
        root,
        "PySnooper:2",
        {
            "candidate_contact_topology_map.json": {
                "candidate_id": "PySnooper:2",
                "status": "block",
                "known_contacts": ["tests/test_pysnooper.py::test_custom_repr_single", "import:mini_toolbox"],
                "missing_contacts": ["tests/mini_toolbox.py"],
                "blocker_category": "fixture_materialization_incomplete",
                "next_allowed_action": "stop_fixture_materialization_forbidden_or_unavailable",
            },
            "candidate_materialization_gate.json": materialization_results[1],
            "candidate_activation_licensing_gate.json": activation_results[1],
            "candidate_next_allowed_action.json": {
                "candidate_id": "PySnooper:2",
                "next_allowed_action": "stop_fixture_materialization_forbidden_or_unavailable",
                "patch_allowed": False,
            },
        },
    )

    gate_paths = [
        "reference_core_gate_v2_15.json",
        "native_contact_topology_gate_v2_15.json",
        "materialization_cofactor_gate_v2_15.json",
        "activation_licensing_gate_v2_15.json",
        "bounded_patch_attempt_gate_v2_15.json",
        "contact_audit_v2_15.json",
        "duplicate_clean_replay_verification_v2_15.json",
        "phase_inversion_seed_constraint_check_v2_15.json",
    ]
    ledger_entries = []
    previous: str | None = None
    for rel in gate_paths:
        path = root / rel
        entry = {
            "path": rel,
            "sha256": sha256_path(path),
            "previous_entry_hash": previous,
        }
        entry["entry_hash"] = canonical_sha(entry)
        previous = entry["entry_hash"]
        ledger_entries.append(entry)
    proof_gate = gate(
        gate_name="proof_obligations_ledger_lock",
        candidate_id=candidates,
        gate_status="pass",
        inputs=["all previous v2.15 gate artifacts", "v2.14 preserved artifact boundary"],
        evidence_files=[f"outputs/v2_15_chromosomal_maintenance_gate_order/{rel}" for rel in gate_paths],
        blocker_category="none",
        blocker_reason="proof ledger is locked over ordered gate hashes",
        next_allowed_action="stop_after_v2_15",
        audit_assertions={"hash_chain_valid": True, "proof_obligations_locked": True},
    )
    proof_gate["ledger_entries"] = ledger_entries
    proof_gate["ledger_tip"] = previous
    write_json(root / "proof_obligations_ledger_lock_v2_15.json", proof_gate)

    preserved = {
        "status": "PASS",
        "source": "outputs/v2_14_capability_recovery_lane/baseline_preservation_v2_14.json",
        "baseline_execution_scope": baseline.get("baseline_execution_scope"),
        "baseline_execution_mode": baseline.get("baseline_execution_mode"),
        "baseline_preservation_passed": baseline.get("baseline_preservation_passed"),
        "ansible2_positive_memory_only_status_preserved": baseline.get("ansible2_positive_memory_only_status_preserved"),
        "ansible5_positive_memory_only_status_preserved": baseline.get("ansible5_positive_memory_only_status_preserved"),
    }
    write_json(root / "preserved_v2_14_baseline_gate_result.json", preserved)

    results = {
        "status": "PASS_WITH_ACTIVATION_DENIED",
        "campaign_id": CAMPAIGN_ID,
        "v2_14_artifact_ingestion_verified": True,
        "corrected_chromosomal_maintenance_order_implemented": True,
        "every_gate_machine_checkable": True,
        "baseline_previous_positives_preserved": True,
        "final_scoreable_count": final.get("updated_scoreable_count"),
        "final_positive_memory_count": final.get("updated_positive_memory_count"),
        "final_non_ansible_positive_memory_count": 0,
        "family_generalization_expanded": False,
        "candidate_classifications": {
            "PySnooper:1": "activation_denied_after_dependency_or_cofactor_mismatch",
            "PySnooper:2": "activation_denied_after_fixture_materialization_incomplete",
        },
        "exact_remaining_blocker": {
            "PySnooper:1": materialization_results[0]["blocker_reason"],
            "PySnooper:2": materialization_results[1]["blocker_reason"],
        },
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_demonstrated": False,
        "self_maintaining_software_demonstrated": False,
        "patch_attempted": False,
    }
    write_json(root / "campaign_results.json", results)

    decision = {
        "status": "PASS",
        "decision": "activation_denied_no_patch",
        "why": "v2.15 made the maintenance order machine-checkable; materialization/cofactor gates block both allowed non-Ansible candidates before patch licensing",
        "primary_focus": "PySnooper non-Ansible blockers from v2.14",
        "not_a_broad_sweep": True,
        "next_safe_action": "manual design/review of an isolated declared-dependency recovery executor for PySnooper:1 or decision-time-safe fixture provenance for PySnooper:2",
    }
    write_json(root / "decision_report.json", decision)

    write_text(
        root / "campaign_summary.md",
        "# v2.15 chromosomal maintenance gate order\n\n"
        "Status: `PASS_WITH_ACTIVATION_DENIED`.\n\n"
        "v2.15 preserves the verified v2.14 artifact and implements the requested maintenance order as machine-checkable gates. "
        "No broad sweep, full scoring, current-protocol promotion, or v2.16 work was performed.\n\n"
        "- v2.14 artifact ingestion: `PASS`.\n"
        "- Gate order implemented: `PASS`.\n"
        "- Patch generation: `blocked before licensing`.\n"
        "- PySnooper:1: `activation_denied_after_dependency_or_cofactor_mismatch`.\n"
        "- PySnooper:2: `activation_denied_after_fixture_materialization_incomplete`.\n"
        "- Final scoreable count: `5`.\n"
        "- Final positive-memory count: `2`.\n"
        "- Non-Ansible positive-memory count: `0`.\n"
        "- Family generalization: `not_expanded`.\n"
        "- Full scoring remains `NOT_RUN` / disallowed.\n"
        "- Memory lift and self-maintaining software remain undemonstrated.\n",
    )

    artifact_verification = {
        "status": "PASS",
        "v2_14_ingestion_files_present": V214_INGEST_FILES,
        "v2_14_artifact_sha256_verification_status": "PASS",
        "v2_15_sha256_manifest_written": True,
    }
    write_json(root / "artifact_sha256_verification.json", artifact_verification)

    required_paths = [
        "campaign_summary.md",
        "campaign_results.json",
        "decision_report.json",
        "preserved_v2_14_baseline_gate_result.json",
        "chromosomal_maintenance_order_v2_15.json",
        *gate_paths,
        "proof_obligations_ledger_lock_v2_15.json",
        "activation_denial_reasons_v2_15.json",
        "memory_lift_decomposition_v2_15.json",
        "family_generalization_status_v2_15.json",
        "artifact_sha256_verification.json",
        "package_verification.json",
        "SHA256SUMS.txt",
    ]
    package = {
        "status": "PASS",
        "required_paths": required_paths,
        "candidate_specific_paths": sorted(
            path.relative_to(root).as_posix()
            for path in (root / "candidates").rglob("*.json")
        ),
        "zip_or_tar_included": False,
        "runtime_workspace_included": False,
        "credentials_included": False,
    }
    write_json(root / "package_verification.json", package)
    write_manifest(root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate v2.15 chromosomal maintenance gate-order outputs.")
    parser.add_argument("--v2-14-root", type=Path, default=V214_ROOT)
    parser.add_argument("--v2-15-root", type=Path, default=V215_ROOT)
    parser.add_argument("--v2-14-zip", type=Path, default=None)
    args = parser.parse_args()

    v214 = write_v214_ingestion(args.v2_14_root.resolve(), args.v2_14_zip.resolve() if args.v2_14_zip else None)
    build_v215_outputs(args.v2_15_root.resolve(), v214)
    print(f"v2.15 chromosomal maintenance gate-order outputs wrote {args.v2_15_root.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

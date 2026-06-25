#!/usr/bin/env python3
"""Audit v2.15 chromosomal maintenance gate-order evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
V214_ROOT = REPO_ROOT / "outputs" / "v2_14_capability_recovery_lane"
DEFAULT_ROOT = REPO_ROOT / "outputs" / "v2_15_chromosomal_maintenance_gate_order"
CAMPAIGN_ID = "v2_15_chromosomal_maintenance_gate_order"
ALLOWED_GATE_STATUSES = {"pass", "block", "manual_review"}
GATE_FIELDS = [
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
REQUIRED_V214_INGEST = [
    "v2_14_artifact_ingestion_summary.json",
    "v2_14_artifact_sha256_verification.json",
    "v2_14_result_preservation.json",
    "v2_14_decision_report_preservation.json",
    "v2_14_scoreable_episode_table.json",
    "v2_14_positive_memory_table.json",
    "v2_14_blocker_table.json",
    "v2_14_claim_boundary.md",
]
REQUIRED_V215 = [
    "campaign_summary.md",
    "campaign_results.json",
    "decision_report.json",
    "preserved_v2_14_baseline_gate_result.json",
    "chromosomal_maintenance_order_v2_15.json",
    "reference_core_gate_v2_15.json",
    "native_contact_topology_gate_v2_15.json",
    "materialization_cofactor_gate_v2_15.json",
    "activation_licensing_gate_v2_15.json",
    "bounded_patch_attempt_gate_v2_15.json",
    "contact_audit_v2_15.json",
    "duplicate_clean_replay_verification_v2_15.json",
    "phase_inversion_seed_constraint_check_v2_15.json",
    "proof_obligations_ledger_lock_v2_15.json",
    "activation_denial_reasons_v2_15.json",
    "memory_lift_decomposition_v2_15.json",
    "family_generalization_status_v2_15.json",
    "artifact_sha256_verification.json",
    "package_verification.json",
    "SHA256SUMS.txt",
]
GATE_FILES = [
    "reference_core_gate_v2_15.json",
    "native_contact_topology_gate_v2_15.json",
    "materialization_cofactor_gate_v2_15.json",
    "activation_licensing_gate_v2_15.json",
    "bounded_patch_attempt_gate_v2_15.json",
    "contact_audit_v2_15.json",
    "duplicate_clean_replay_verification_v2_15.json",
    "phase_inversion_seed_constraint_check_v2_15.json",
    "proof_obligations_ledger_lock_v2_15.json",
]
FORBIDDEN_DECISION_INPUT_PATTERNS = [
    "fixed revision",
    "gold patch",
    "future outcome",
    "hidden label",
]


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: Any) -> str:
    material = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def load_json(path: Path, errors: list[str]) -> dict[str, Any]:
    if not path.is_file():
        errors.append(f"missing JSON: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid JSON {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"expected JSON object: {path}")
        return {}
    return value


def verify_manifest(root: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    manifest = root / "SHA256SUMS.txt"
    if not manifest.is_file():
        return [f"missing manifest: {manifest}"], 0
    seen: set[str] = set()
    checked = 0
    for line_number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            errors.append(f"{manifest}:{line_number}: malformed entry")
            continue
        expected, rel = parts
        pure = PurePosixPath(rel)
        if rel.startswith("/") or any(part in {"", ".", ".."} for part in pure.parts):
            errors.append(f"{manifest}:{line_number}: unsafe path {rel}")
            continue
        seen.add(rel)
        path = root.joinpath(*pure.parts)
        if not path.is_file():
            errors.append(f"{manifest}:{line_number}: missing file {rel}")
            continue
        if sha256_path(path) != expected:
            errors.append(f"{manifest}:{line_number}: hash mismatch {rel}")
        checked += 1
    expected_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS.txt"
    }
    for rel in sorted(expected_files - seen):
        errors.append(f"manifest missing {rel}")
    for rel in sorted(seen - expected_files):
        errors.append(f"manifest contains extra {rel}")
    return errors, checked


def resolve_repo_rel(raw: str) -> Path | None:
    pure = PurePosixPath(raw)
    if raw.startswith("/") or any(part in {"", ".", ".."} for part in pure.parts):
        return None
    path = REPO_ROOT.joinpath(*pure.parts)
    return path if path.is_file() else None


def audit_v214_ingestion(errors: list[str]) -> dict[str, Any]:
    for rel in REQUIRED_V214_INGEST:
        if not (V214_ROOT / rel).is_file():
            errors.append(f"missing v2.14 ingestion output: {rel}")
    sha = load_json(V214_ROOT / "v2_14_artifact_sha256_verification.json", errors)
    ingest = load_json(V214_ROOT / "v2_14_artifact_ingestion_summary.json", errors)
    result = load_json(V214_ROOT / "v2_14_result_preservation.json", errors)
    scoreable = load_json(V214_ROOT / "v2_14_scoreable_episode_table.json", errors)
    positive = load_json(V214_ROOT / "v2_14_positive_memory_table.json", errors)
    blocker = load_json(V214_ROOT / "v2_14_blocker_table.json", errors)
    manifest_status = sha.get("zip_internal_manifest_status") or sha.get("artifact_root_manifest_status_before_preservation_update")
    if sha.get("status") != "PASS" or manifest_status != "PASS":
        errors.append("v2.14 artifact SHA/manifest verification is not clean")
    if ingest.get("status") != "PASS" or ingest.get("artifact_ingested") is not True:
        errors.append("v2.14 artifact ingestion summary is not PASS")
    if result.get("status") != "PASS":
        errors.append("v2.14 result preservation is not PASS")
    final = result.get("preserved_final_result") or {}
    if final.get("controllergate_full_scoring") != "NOT_RUN" or final.get("full_scoring_allowed") is not False:
        errors.append("v2.14 full scoring boundary changed")
    if final.get("self_maintaining_software_demonstrated") is not False:
        errors.append("v2.14 self-maintaining boundary changed")
    if final.get("updated_scoreable_count") != 5 or final.get("updated_positive_memory_count") != 2:
        errors.append("v2.14 scoreable/positive counts not preserved")
    if final.get("non_ansible_positive_memory_count") != 0:
        errors.append("v2.14 non-Ansible positive-memory count changed")
    if scoreable.get("scoreable_count") != 5:
        errors.append("v2.14 scoreable table count mismatch")
    if positive.get("positive_memory_count") != 2 or positive.get("non_ansible_positive_memory_count") != 0:
        errors.append("v2.14 positive-memory table mismatch")
    rows = blocker.get("rows") or []
    classifications = {row.get("candidate"): row.get("classification") for row in rows if isinstance(row, dict)}
    if classifications.get("PySnooper:1") != "pysnooper1_dependency_recovery_execution_blocked":
        errors.append("v2.14 PySnooper:1 classification not preserved")
    if classifications.get("PySnooper:2") != "pysnooper2_fixture_materialization_forbidden_or_unavailable":
        errors.append("v2.14 PySnooper:2 classification not preserved")
    return final


def audit_gate_file(root: Path, rel: str, errors: list[str]) -> dict[str, Any]:
    gate = load_json(root / rel, errors)
    for field in GATE_FIELDS:
        if field not in gate:
            errors.append(f"{rel} missing gate field {field}")
    if gate.get("gate_status") not in ALLOWED_GATE_STATUSES:
        errors.append(f"{rel} has invalid gate_status {gate.get('gate_status')!r}")
    if not gate.get("candidate_id"):
        errors.append(f"{rel} missing candidate_id value")
    if not isinstance(gate.get("decision_time_inputs_used"), list):
        errors.append(f"{rel} decision_time_inputs_used must be a list")
    else:
        lowered = " ".join(str(item).lower() for item in gate.get("decision_time_inputs_used") or [])
        for pattern in FORBIDDEN_DECISION_INPUT_PATTERNS:
            if pattern in lowered:
                errors.append(f"{rel} decision-time inputs contain forbidden pattern {pattern!r}")
    if not isinstance(gate.get("audit_assertions"), dict):
        errors.append(f"{rel} audit_assertions must be an object")
    for evidence, expected in (gate.get("sha256_inputs") or {}).items():
        path = resolve_repo_rel(evidence)
        if path is None:
            errors.append(f"{rel} evidence path cannot be resolved: {evidence}")
        elif sha256_path(path) != expected:
            errors.append(f"{rel} evidence hash mismatch: {evidence}")
    return gate


def audit_gates(root: Path, errors: list[str]) -> None:
    gates = {rel: audit_gate_file(root, rel, errors) for rel in GATE_FILES}
    order = load_json(root / "chromosomal_maintenance_order_v2_15.json", errors)
    expected_order = [
        "reference_core_gate",
        "native_contact_topology_gate",
        "materialization_cofactor_gate",
        "activation_licensing_gate",
        "bounded_source_only_patch_attempt",
        "contact_audit",
        "duplicate_clean_replay",
        "phase_inversion_seed_constraint_check",
        "proof_obligations_ledger_lock",
    ]
    if order.get("gate_order") != expected_order or order.get("patch_generation_centered") is not False:
        errors.append("chromosomal maintenance order is missing or decorative")

    activation = gates["activation_licensing_gate_v2_15.json"]
    patch = gates["bounded_patch_attempt_gate_v2_15.json"]
    materialization = gates["materialization_cofactor_gate_v2_15.json"]
    if activation.get("gate_status") != "block" or activation.get("blocker_category") != "activation_denied":
        errors.append("activation/licensing gate did not deny patch as expected")
    if patch.get("audit_assertions", {}).get("patch_attempted") is not False:
        errors.append("bounded patch gate unexpectedly attempted a patch")
    if patch.get("next_allowed_action") == "patch":
        errors.append("patch gate cannot set next_allowed_action: patch after activation denial")
    if any(path.suffix == ".diff" for path in root.rglob("*")):
        errors.append("unexpected patch diff generated in v2.15")

    results = materialization.get("candidate_results") or []
    py1 = next((row for row in results if row.get("candidate_id") == "PySnooper:1"), {})
    py2 = next((row for row in results if row.get("candidate_id") == "PySnooper:2"), {})
    if py1.get("declared_in_buggy_checkout_metadata") is not True:
        errors.append("PySnooper:1 dependency recovery lacks declared metadata evidence")
    if py1.get("undeclared_dependency_install_attempted") is not False:
        errors.append("PySnooper:1 attempted undeclared dependency install")
    if py2.get("fixture_materialization_policy_allows") is not False or py2.get("files_materialized") != []:
        errors.append("PySnooper:2 fixture materialization was not blocked cleanly")

    proof = gates["proof_obligations_ledger_lock_v2_15.json"]
    previous = None
    for index, entry in enumerate(proof.get("ledger_entries") or []):
        expected = {
            "path": entry.get("path"),
            "sha256": entry.get("sha256"),
            "previous_entry_hash": previous,
        }
        if entry.get("previous_entry_hash") != previous:
            errors.append(f"proof ledger entry {index} previous hash mismatch")
        if canonical_sha(expected) != entry.get("entry_hash"):
            errors.append(f"proof ledger entry {index} hash mismatch")
        target = root / str(entry.get("path"))
        if not target.is_file() or sha256_path(target) != entry.get("sha256"):
            errors.append(f"proof ledger entry {index} target hash mismatch")
        previous = entry.get("entry_hash")
    if proof.get("ledger_tip") != previous or proof.get("audit_assertions", {}).get("proof_obligations_locked") is not True:
        errors.append("proof obligations ledger lock is invalid")


def audit_candidate_specific(root: Path, errors: list[str]) -> None:
    for safe, candidate in [("pysnooper_1", "PySnooper:1"), ("pysnooper_2", "PySnooper:2")]:
        croot = root / "candidates" / safe
        for rel in [
            "candidate_contact_topology_map.json",
            "candidate_materialization_gate.json",
            "candidate_activation_licensing_gate.json",
            "candidate_next_allowed_action.json",
        ]:
            path = croot / rel
            if not path.is_file():
                errors.append(f"missing candidate artifact for {candidate}: {rel}")
        next_action = load_json(croot / "candidate_next_allowed_action.json", errors)
        if next_action.get("candidate_id") != candidate or next_action.get("patch_allowed") is not False:
            errors.append(f"{candidate} next-action artifact unexpectedly allows patching")
    if any((root / "candidates").rglob("candidate_failed_patch_forensics.json")):
        errors.append("failed-patch forensics exists despite no patch attempt")


def audit_claims(root: Path, final: dict[str, Any], errors: list[str]) -> None:
    results = load_json(root / "campaign_results.json", errors)
    memory = load_json(root / "memory_lift_decomposition_v2_15.json", errors)
    family = load_json(root / "family_generalization_status_v2_15.json", errors)
    preserved = load_json(root / "preserved_v2_14_baseline_gate_result.json", errors)
    if results.get("final_scoreable_count") != 5 or results.get("final_positive_memory_count") != 2:
        errors.append("v2.15 final counts do not preserve v2.14")
    if results.get("final_non_ansible_positive_memory_count") != 0:
        errors.append("v2.15 unexpectedly expands non-Ansible positive-memory count")
    if results.get("family_generalization_expanded") is not False or family.get("family_generalization_expanded") is not False:
        errors.append("family generalization expanded without a non-Ansible positive-memory result")
    if results.get("full_scoring") != "NOT_RUN" or results.get("full_scoring_allowed") is not False:
        errors.append("full scoring boundary changed")
    if memory.get("memory_lift_demonstrated") is not False:
        errors.append("memory lift was claimed without preregistered aggregate gates")
    if results.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software was claimed")
    if preserved.get("baseline_preservation_passed") is not True:
        errors.append("preserved v2.14 baseline gate did not pass")
    if final.get("updated_scoreable_count") != results.get("final_scoreable_count"):
        errors.append("v2.14/v2.15 scoreable preservation mismatch")


def audit_tatmapper_quarantine(errors: list[str]) -> None:
    summary = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
    if not summary.is_file():
        errors.append("TatMapper shareable summary missing")
        return
    text = summary.read_text(encoding="utf-8", errors="replace")
    if "0 of 11 TatMapper episodes are deterministic-replay-ready" not in text:
        errors.append("TatMapper quarantine marker changed or missing")
    if "scoring must not be expanded" not in text:
        errors.append("TatMapper scoring quarantine language missing")


def audit_package(root: Path, errors: list[str]) -> None:
    for rel in REQUIRED_V215:
        if not (root / rel).is_file():
            errors.append(f"missing required v2.15 artifact: {rel}")
    for path in root.rglob("*"):
        lowered = path.as_posix().lower()
        if path.suffix.lower() in {".zip", ".tar"} or any(token in lowered for token in [".venv", "/venv/", "__pycache__", "_runtime"]):
            errors.append(f"forbidden packaged path: {path.relative_to(root).as_posix()}")
    package = load_json(root / "package_verification.json", errors)
    if package.get("status") != "PASS" or package.get("zip_or_tar_included") is not False:
        errors.append("package verification did not pass cleanly")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit v2.15 chromosomal maintenance gate-order outputs.")
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.artifact_root.resolve()
    errors: list[str] = []

    audit_package(root, errors)
    manifest_errors, checked = verify_manifest(root)
    errors.extend(manifest_errors)
    final = audit_v214_ingestion(errors)
    audit_gates(root, errors)
    audit_candidate_specific(root, errors)
    audit_claims(root, final, errors)
    audit_tatmapper_quarantine(errors)

    status = "PASS" if not errors else "FAIL"
    print(f"v2.15 chromosomal maintenance gate-order audit {status} ({checked} manifest entries)")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

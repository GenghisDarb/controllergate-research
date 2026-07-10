#!/usr/bin/env python3
"""Independent audit for the v2.14 capability recovery lane."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "outputs" / "v2_14_capability_recovery_lane"
CAMPAIGN_ID = "v2_14_capability_recovery_lane"
REQUIRED_FILES = [
    "campaign_summary.md",
    "candidate_state_v2_14.json",
    "failure_memory_weights_v2_14.json",
    "local_global_validation_v2_14.json",
    "capability_probe_log_v2_14.json",
    "audit_summary_v2_14.json",
    "SHA256SUMS.txt",
    "baseline_preservation_v2_14.json",
    "pysnooper1_recovery_gate_v2_14.json",
    "pysnooper2_fixture_gate_v2_14.json",
]
BASELINE_IDS = ["youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"]
ALLOWED_CANDIDATES = ["PySnooper:1", "PySnooper:2"]
ALLOWED_WEIGHT_ORIGINS = {
    "v2.13 classifier",
    "v2.13 context extraction",
    "v2.13 logs",
    "current probe output",
    "current validation output",
}
STATE_FIELDS = [
    "agent_state_id",
    "observation_id",
    "parent_agent_state_id",
    "last_stable_state_id",
    "state_status",
    "rollback_to_state_id",
    "pre_state_hash",
    "post_state_hash",
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
        errors.append(f"missing JSON file: {path}")
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


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_manifest(root: Path) -> None:
    files = sorted(
        (path for path in root.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    lines = [f"{sha256_path(path)}  {path.relative_to(root).as_posix()}" for path in files]
    with (root / "SHA256SUMS.txt").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(lines) + "\n")


def verify_manifest(root: Path) -> tuple[list[str], int]:
    errors: list[str] = []
    manifest = root / "SHA256SUMS.txt"
    if not manifest.exists():
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
        if rel in seen:
            errors.append(f"{manifest}:{line_number}: duplicate entry {rel}")
            continue
        seen.add(rel)
        path = root.joinpath(*pure.parts)
        if not path.is_file():
            errors.append(f"{manifest}:{line_number}: missing file {rel}")
            continue
        checked += 1
        actual = sha256_path(path)
        if actual != expected:
            errors.append(f"{manifest}:{line_number}: hash mismatch for {rel}")
    expected_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.name != "SHA256SUMS.txt"
    }
    for rel in sorted(expected_files - seen):
        errors.append(f"manifest missing artifact entry {rel}")
    for rel in sorted(seen - expected_files):
        errors.append(f"manifest contains unexpected artifact entry {rel}")
    return errors, checked


def resolve_evidence_path(root: Path, raw: str) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw)
    if candidate.is_absolute():
        return candidate if candidate.exists() else None
    pure = PurePosixPath(raw)
    if any(part in {"", ".", ".."} for part in pure.parts):
        return None
    artifact_candidate = root.joinpath(*pure.parts)
    if artifact_candidate.exists():
        return artifact_candidate
    repo_candidate = REPO_ROOT.joinpath(*pure.parts)
    if repo_candidate.exists():
        return repo_candidate
    return None


def state_material(entry: dict[str, Any]) -> dict[str, Any]:
    hashes = entry.get("sha256") or {}
    return {
        "agent_state_id": entry.get("agent_state_id"),
        "observation_id": entry.get("observation_id"),
        "parent_agent_state_id": entry.get("parent_agent_state_id"),
        "last_stable_state_id": entry.get("last_stable_state_id"),
        "state_status": entry.get("state_status"),
        "rollback_to_state_id": entry.get("rollback_to_state_id"),
        "action": entry.get("action"),
        "candidate": entry.get("candidate"),
        "evidence_files": entry.get("evidence_files") or [],
        "input_hashes": hashes.get("input_hashes") or {},
        "output_hashes": hashes.get("output_hashes") or {},
        "result": entry.get("result"),
        "next_allowed_action": entry.get("next_allowed_action"),
    }


def audit_ledger(root: Path, state: dict[str, Any], errors: list[str]) -> None:
    entries = state.get("proof_ledger")
    if not isinstance(entries, list) or not entries:
        errors.append("proof ledger missing or empty")
        return
    current_hash = canonical_sha({"campaign_id": CAMPAIGN_ID, "state": "initial"})
    previous_entry_hash: str | None = None
    previous_state_id: str | None = None
    last_stable_state_id = "state_000_initial"
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"ledger entry {index} is not an object")
            continue
        if entry.get("entry_index") != index or entry.get("sequence_index") != index:
            errors.append(f"ledger entry {index} has wrong sequence index")
        if entry.get("pre_state_hash") != current_hash:
            errors.append(f"ledger entry {index} pre_state_hash does not match previous state")
        if entry.get("parent_agent_state_id") != previous_state_id:
            errors.append(f"ledger entry {index} parent state mismatch")
        state_status = entry.get("state_status")
        expected_last_stable = entry.get("agent_state_id") if state_status == "stable" else last_stable_state_id
        if entry.get("last_stable_state_id") != expected_last_stable:
            errors.append(f"ledger entry {index} last stable state mismatch")
        if entry.get("post_state_hash") != canonical_sha(state_material(entry)):
            errors.append(f"ledger entry {index} post_state_hash mismatch")
        hashes = entry.get("sha256") or {}
        if hashes.get("previous_entry_hash") != previous_entry_hash:
            errors.append(f"ledger entry {index} previous entry hash mismatch")
        material = dict(entry)
        material.pop("entry_hash", None)
        material_hashes = dict(material.get("sha256") or {})
        stored_hash = material_hashes.get("entry_hash")
        material_hashes["entry_hash"] = None
        material["sha256"] = material_hashes
        if stored_hash != canonical_sha(material) or entry.get("entry_hash") != stored_hash:
            errors.append(f"ledger entry {index} entry hash mismatch")
        for key, expected in (hashes.get("input_hashes") or {}).items():
            path = resolve_evidence_path(root, key) or resolve_evidence_path(REPO_ROOT, key)
            if path is not None and path.is_file() and sha256_path(path) != expected:
                errors.append(f"ledger entry {index} input hash mismatch for {key}")
        for key, expected in (hashes.get("output_hashes") or {}).items():
            path = resolve_evidence_path(root, key) or resolve_evidence_path(REPO_ROOT, key)
            if path is not None and path.is_file() and sha256_path(path) != expected:
                errors.append(f"ledger entry {index} output hash mismatch for {key}")
        current_hash = entry.get("post_state_hash")
        previous_entry_hash = stored_hash
        previous_state_id = entry.get("agent_state_id")
        if state_status == "stable":
            last_stable_state_id = str(entry.get("agent_state_id"))


def section_has_state_fields(name: str, value: dict[str, Any], errors: list[str]) -> None:
    for field in STATE_FIELDS:
        if field not in value:
            errors.append(f"{name} missing state custody field {field}")


def audit_baseline(state: dict[str, Any], baseline: dict[str, Any], errors: list[str]) -> None:
    state_baseline = state.get("baseline_preservation") or {}
    section_has_state_fields("baseline_preservation", state_baseline, errors)
    if state_baseline.get("baseline_execution_scope") != BASELINE_IDS:
        errors.append("baseline scope is not exactly the required five candidates")
    if state_baseline.get("broad_candidate_sweep_executed") is not False:
        errors.append("baseline recorded a broad candidate sweep")
    if state_baseline.get("baseline_preservation_passed") is not True or state_baseline.get("status") != "PASS":
        errors.append("baseline preservation did not PASS")
    if state_baseline.get("ansible2_positive_memory_only_status_preserved") is not True:
        errors.append("ansible:2 positive_memory_only status not preserved")
    if state_baseline.get("ansible5_positive_memory_only_status_preserved") is not True:
        errors.append("ansible:5 positive_memory_only status not preserved")
    if baseline.get("baseline_execution_scope") != BASELINE_IDS or baseline.get("status") != "PASS":
        errors.append("baseline_preservation_v2_14.json does not record PASS for exact five candidates")


def audit_weights(root: Path, weights: dict[str, Any], errors: list[str]) -> None:
    if weights.get("campaign_id") != CAMPAIGN_ID:
        errors.append("failure-memory weights have wrong campaign id")
    if weights.get("hard_safety_gates_override_allowed") is not False or weights.get("ranking_only") is not True:
        errors.append("failure-memory weights must be ranking-only and never override hard gates")
    records = weights.get("source_evidence")
    if not isinstance(records, list) or not records:
        errors.append("failure-memory weights missing source evidence")
    else:
        for record in records:
            if not isinstance(record, dict):
                errors.append("failure-memory source evidence entry is not an object")
                continue
            path = resolve_evidence_path(root, str(record.get("path") or ""))
            if path is None or not path.is_file():
                errors.append(f"failure-memory source evidence missing: {record.get('path')}")
                continue
            if record.get("sha256") != sha256_path(path):
                errors.append(f"failure-memory source evidence hash mismatch: {record.get('path')}")
            if record.get("decision_time_safe") is not True:
                errors.append(f"failure-memory source evidence not decision-time safe: {record.get('path')}")
    candidates = weights.get("candidates")
    if not isinstance(candidates, list) or [item.get("candidate") for item in candidates if isinstance(item, dict)] != ALLOWED_CANDIDATES:
        errors.append("failure-memory candidates must be exactly PySnooper:1 then PySnooper:2")
        return
    for item in candidates:
        if item.get("decision_time_safe") is not True:
            errors.append(f"{item.get('candidate')} weight is not marked decision-time safe")
        if item.get("evidence_origin") not in ALLOWED_WEIGHT_ORIGINS:
            errors.append(f"{item.get('candidate')} has unsupported evidence origin")
        suspects = (
            item.get("suspect_files") or []
        ) + (item.get("suspect_symbols") or []) + (item.get("suspect_dependency_edges") or []) + (
            item.get("suspect_fixture_helper_references") or []
        )
        if not suspects:
            errors.append(f"{item.get('candidate')} weight has no suspect ranking entries")


def audit_probes(root: Path, probes: dict[str, Any], errors: list[str]) -> None:
    if probes.get("max_total_probes") != 4:
        errors.append("probe budget must be 4")
    if probes.get("total_probe_count") != 2 or len(probes.get("probes") or []) != 2:
        errors.append("v2.14 expected exactly two bounded probes")
        return
    if probes.get("source_mutating_probes") != 0 or probes.get("test_mutating_probes") != 0:
        errors.append("mutating probes were recorded")
    for probe in probes.get("probes") or []:
        if probe.get("predeclared_before_execution") is not True:
            errors.append(f"{probe.get('probe_id')} was not predeclared")
        if probe.get("mutates_source_or_tests") is not False:
            errors.append(f"{probe.get('probe_id')} mutates source or tests")
        if probe.get("candidate") not in ALLOWED_CANDIDATES:
            errors.append(f"{probe.get('probe_id')} has out-of-scope candidate")
        for field in ["command", "reason", "expected_uncertainty_reduced", "decision_time_inputs"]:
            if not probe.get(field):
                errors.append(f"{probe.get('probe_id')} missing {field}")
        path = resolve_evidence_path(root, str(probe.get("result_log_path") or ""))
        if path is None or not path.is_file():
            errors.append(f"{probe.get('probe_id')} missing result log")
        elif probe.get("result_log_sha256") != sha256_path(path):
            errors.append(f"{probe.get('probe_id')} result log hash mismatch")


def audit_local_global(validation: dict[str, Any], errors: list[str]) -> None:
    if validation.get("scoreable_requires_local_and_global_pass") is not True:
        errors.append("local/global validation does not require both gates")
    baseline = validation.get("baseline_preservation") or {}
    if baseline.get("status") != "PASS" or baseline.get("required_candidates") != BASELINE_IDS:
        errors.append("local/global validation baseline preservation failed")
    candidates = validation.get("candidates") or {}
    if list(candidates.keys()) != ALLOWED_CANDIDATES:
        errors.append("local/global validation candidate scope changed")
        return
    for candidate, expected_classification in [
        ("PySnooper:1", "pysnooper1_dependency_recovery_execution_blocked"),
        ("PySnooper:2", "pysnooper2_fixture_materialization_forbidden_or_unavailable"),
    ]:
        section = candidates.get(candidate) or {}
        if section.get("final_classification") != expected_classification:
            errors.append(f"{candidate} validation classification mismatch")
        if section.get("scoreable") is not False or section.get("positive_memory_only") is not False:
            errors.append(f"{candidate} unexpectedly marked scoreable/positive-memory")
        global_checks = section.get("global_constraints_checks") or {}
        for key in [
            "no_test_edits",
            "no_benchmark_expectation_edits",
            "no_unauthorized_fixture_edits",
            "no_fixed_gold_future_evidence",
            "decision_time_outcome_separation",
            "memory_no_memory_separation",
            "no_full_scoring_claim",
            "no_self_maintaining_claim",
        ]:
            if global_checks.get(key) is not True:
                errors.append(f"{candidate} global constraint {key} did not pass")
    aggregate = validation.get("aggregate") or {}
    if aggregate.get("any_scoreable_non_ansible_result") is not False:
        errors.append("aggregate unexpectedly reports a scoreable non-Ansible result")
    if aggregate.get("patch_attempts") != 0:
        errors.append("aggregate patch attempt count must be zero")
    if aggregate.get("full_scoring") != "NOT_RUN" or aggregate.get("full_scoring_allowed") is not False:
        errors.append("full scoring boundary changed")
    if aggregate.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining claim boundary changed")


def audit_candidate_state(state: dict[str, Any], errors: list[str]) -> None:
    if state.get("campaign_id") != CAMPAIGN_ID or state.get("version") != "v2.14":
        errors.append("candidate state identity mismatch")
    if state.get("current_protocol_promoted") is not False or state.get("official_artifact_ingested") is not False:
        errors.append("v2.14 must not be promoted or officially ingested in this implementation step")
    scope = state.get("scope") or {}
    if scope.get("allowed_candidates") != ALLOWED_CANDIDATES or scope.get("candidate_order") != ALLOWED_CANDIDATES:
        errors.append("candidate scope/order is not exactly PySnooper:1 then PySnooper:2")
    if scope.get("broad_sweep_executed") is not False or scope.get("full_scoring_executed") is not False:
        errors.append("broad sweep or full scoring was executed")
    if scope.get("max_total_probes") != 4 or scope.get("max_total_patch_attempts") != 2:
        errors.append("scope limits changed")

    boundaries = state.get("source_v2_13_claim_boundaries") or {}
    expected_boundaries = {
        "v2_13_audit_status": "PASS",
        "v2_13_pysnooper1_policy_classification": "dependency_recovery_allowed_by_policy_not_executed_in_minimal_lane",
        "v2_13_pysnooper2_final_blocker": "blocked_fixture_materialization_incomplete",
        "v2_13_scoreable_count": 5,
        "v2_13_positive_memory_count": 2,
        "v2_13_non_ansible_positive_memory_count": 0,
        "v2_13_full_scoring": "NOT_RUN",
        "v2_13_full_scoring_allowed": False,
        "v2_13_self_maintaining_software_demonstrated": False,
        "v2_13_claims_changed_by_v2_14": False,
    }
    for key, expected in expected_boundaries.items():
        if boundaries.get(key) != expected:
            errors.append(f"v2.13 claim boundary changed: {key}")

    section_has_state_fields("failure_memory_weighting", state.get("failure_memory_weighting") or {}, errors)
    section_has_state_fields("local_global_validation", state.get("local_global_validation") or {}, errors)
    final = state.get("final_result") or {}
    section_has_state_fields("final_result", final, errors)
    if final.get("status") != "PASS_WITH_BOUNDED_BLOCKERS":
        errors.append("final v2.14 status mismatch")
    if final.get("pysnooper1_final_classification") != "pysnooper1_dependency_recovery_execution_blocked":
        errors.append("PySnooper:1 final classification mismatch")
    if final.get("pysnooper2_final_classification") != "pysnooper2_fixture_materialization_forbidden_or_unavailable":
        errors.append("PySnooper:2 final classification mismatch")
    if final.get("any_scoreable_non_ansible_result") is not False:
        errors.append("unexpected non-Ansible scoreable result")
    if final.get("positive_memory_only") is not False or final.get("non_ansible_positive_memory_count") != 0:
        errors.append("unexpected non-Ansible positive-memory result")
    if final.get("updated_scoreable_count") != 5 or final.get("updated_positive_memory_count") != 2:
        errors.append("scoreable/positive-memory counts changed")
    if final.get("diagnostic_probe_count") != 2 or final.get("patch_attempt_count") != 0:
        errors.append("probe or patch-attempt count mismatch")
    if final.get("controllergate_full_scoring") != "NOT_RUN" or final.get("full_scoring_allowed") is not False:
        errors.append("full scoring boundary changed")
    if final.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software boundary changed")
    if final.get("family_generalization") != "not_expanded":
        errors.append("family generalization boundary changed")
    if final.get("fixed_gold_future_evidence_used") is not False or final.get("decision_time_outcome_overlap_count") != 0:
        errors.append("evidence firewall was violated")

    candidates = state.get("candidates") or {}
    if list(candidates.keys()) != ALLOWED_CANDIDATES:
        errors.append("candidate state candidate set changed")
        return
    py1 = candidates.get("PySnooper:1") or {}
    py1_gate = py1.get("dependency_recovery") or {}
    section_has_state_fields("PySnooper:1 dependency_recovery", py1_gate, errors)
    if py1.get("patch_attempt_count") != 0 or py1.get("patch_authorized") is not False:
        errors.append("PySnooper:1 patch was unexpectedly authorized or attempted")
    if py1_gate.get("policy_reverified") is not True or py1_gate.get("recovery_policy_allowed") is not True:
        errors.append("PySnooper:1 dependency declaration was not reverified as policy-allowed")
    if py1_gate.get("recovery_execution_attempted") is not False or py1_gate.get("recovery_executed") is not False:
        errors.append("PySnooper:1 recovery execution should be blocked, not attempted")
    if py1_gate.get("undeclared_dependencies_installed") is not False:
        errors.append("PySnooper:1 installed undeclared dependencies")
    if py1_gate.get("classification") != "pysnooper1_dependency_recovery_execution_blocked":
        errors.append("PySnooper:1 gate classification mismatch")

    py2 = candidates.get("PySnooper:2") or {}
    py2_gate = py2.get("fixture_materialization") or {}
    section_has_state_fields("PySnooper:2 fixture_materialization", py2_gate, errors)
    if py2.get("patch_attempt_count") != 0 or py2.get("patch_authorized") is not False:
        errors.append("PySnooper:2 patch was unexpectedly authorized or attempted")
    if py2_gate.get("missing_fixture_or_helper") != ["tests/mini_toolbox.py"]:
        errors.append("PySnooper:2 missing fixture/helper mismatch")
    if py2_gate.get("fixture_materialization_policy_allows") is not False:
        errors.append("PySnooper:2 fixture materialization should remain forbidden/unavailable")
    if py2_gate.get("files_materialized") != []:
        errors.append("PySnooper:2 materialized fixture files")
    if py2_gate.get("classification") != "pysnooper2_fixture_materialization_forbidden_or_unavailable":
        errors.append("PySnooper:2 gate classification mismatch")

    patch_attempts = state.get("patch_attempts") or {}
    if patch_attempts.get("total_patch_attempts") != 0:
        errors.append("patch attempts must be zero")
    if patch_attempts.get("attempts_by_candidate") != {"PySnooper:1": 0, "PySnooper:2": 0}:
        errors.append("patch attempts by candidate mismatch")
    if patch_attempts.get("failed_patches_rolled_back") is not True:
        errors.append("failed patches are not recorded as rolled back")
    if patch_attempts.get("source_only_rule_enforced") is not True:
        errors.append("source-only rule was not enforced")


def audit_filesystem(root: Path, errors: list[str]) -> None:
    for rel in REQUIRED_FILES:
        if not (root / rel).is_file():
            errors.append(f"missing required v2.14 artifact file: {rel}")
    for rel in ["pysnooper1_revised_patch.diff", "pysnooper2_revised_patch.diff"]:
        if (root / rel).exists():
            errors.append(f"unexpected revised patch file with zero attempts: {rel}")
    forbidden_names = {".venv", "venv", "__pycache__"}
    for path in root.rglob("*"):
        if path.name in forbidden_names or path.suffix.lower() in {".zip", ".tar"}:
            errors.append(f"forbidden packaged output under artifact root: {path.relative_to(root).as_posix()}")
    current_config = (REPO_ROOT / "configs" / "controllergate_current.yaml").read_text(encoding="utf-8")
    if "protocol_version: v2.13" not in current_config:
        batch048_decision = REPO_ROOT / "outputs" / "clean_replication_batch_048" / "batch048_protocol_v2_14_promotion_decision.json"
        batch068h_decision = REPO_ROOT / "outputs" / "post_v2_37_hardening_batch068h_semantic_pathway_secure_provider_probe" / "static_planning_protocol_promotion_decision_batch068h.json"
        batch068h1_decision = REPO_ROOT / "outputs" / "post_v2_37_hardening_batch068h1_universal_interlock_elbow_harness_decomposition" / "v2_16_promotion_decision_batch068h1.json"
        batch068h2_decision = REPO_ROOT / "outputs" / "post_v2_37_hardening_batch068h2_tld_brot_bulb_topology_runtime_historical_capsule_recovery" / "v2_17_topology_promotion_decision.json"
        if "protocol_version: v2.17" in current_config and batch068h_decision.is_file() and batch068h1_decision.is_file() and batch068h2_decision.is_file():
            v215 = load_json(batch068h_decision, errors)
            v216 = load_json(batch068h1_decision, errors)
            v217 = load_json(batch068h2_decision, errors)
            if v215.get("status") != "PASS" or v215.get("protocol_before") != "v2.14" or v215.get("protocol_after") != "v2.15": errors.append("v2.14 to v2.15 promotion lineage invalid")
            if v216.get("status") != "PASS" or v216.get("protocol_before") != "v2.15" or v216.get("protocol_after") != "v2.16": errors.append("v2.15 to v2.16 promotion lineage invalid")
            if v217.get("status") != "PASS" or v217.get("protocol_before") != "v2.16" or v217.get("protocol_after") != "v2.17": errors.append("v2.16 to v2.17 promotion lineage invalid")
            return
        if "protocol_version: v2.16" in current_config and batch068h_decision.is_file() and batch068h1_decision.is_file():
            v215 = load_json(batch068h_decision, errors)
            v216 = load_json(batch068h1_decision, errors)
            if v215.get("status") != "PASS" or v215.get("protocol_before") != "v2.14" or v215.get("protocol_after") != "v2.15":
                errors.append("v2.14 to v2.15 promotion lineage invalid")
            criteria = v216.get("criteria") or {}
            if v216.get("status") != "PASS" or v216.get("protocol_before") != "v2.15" or v216.get("protocol_after") != "v2.16":
                errors.append("v2.15 to v2.16 promotion lineage invalid")
            if not criteria or not all(value is True for value in criteria.values()):
                errors.append("Batch068h1 v2.16 promotion criteria are incomplete")
            return
        if "protocol_version: v2.15" in current_config and batch068h_decision.is_file():
            decision = load_json(batch068h_decision, errors)
            criteria = decision.get("criteria") or {}
            if decision.get("status") != "PASS" or decision.get("protocol_before") != "v2.14" or decision.get("protocol_after") != "v2.15":
                errors.append("configs/controllergate_current.yaml changed without valid Batch068h v2.15 promotion")
            if not criteria or not all(value is True for value in criteria.values()):
                errors.append("Batch068h v2.15 promotion criteria are incomplete")
            return
        if "protocol_version: v2.14" not in current_config or not batch048_decision.is_file():
            errors.append("configs/controllergate_current.yaml no longer points to v2.13")
            return
        decision = load_json(batch048_decision, errors)
        if decision.get("protocol_v2_14_promotion_status") != "PROMOTED":
            errors.append("configs/controllergate_current.yaml changed without Batch048 v2.14 promotion")
        if decision.get("current_protocol_before_decision") != "v2.13" or decision.get("current_protocol_after_decision") != "v2.14":
            errors.append("Batch048 v2.14 promotion decision has invalid protocol transition")
        for field in ["repair_counts_changed", "repair_generation_authorized", "full_scoring_enabled", "memory_lift_claimed", "self_maintaining_software_claimed"]:
            if decision.get(field) is not False:
                errors.append(f"Batch048 v2.14 promotion over-allowed {field}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the v2.14 capability recovery lane artifact.")
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    root = args.artifact_root.resolve()
    errors: list[str] = []

    audit_filesystem(root, errors)
    manifest_errors, checked_manifest_entries = verify_manifest(root)
    errors.extend(manifest_errors)

    state = load_json(root / "candidate_state_v2_14.json", errors)
    weights = load_json(root / "failure_memory_weights_v2_14.json", errors)
    validation = load_json(root / "local_global_validation_v2_14.json", errors)
    probes = load_json(root / "capability_probe_log_v2_14.json", errors)
    baseline = load_json(root / "baseline_preservation_v2_14.json", errors)
    py1_gate = load_json(root / "pysnooper1_recovery_gate_v2_14.json", errors)
    py2_gate = load_json(root / "pysnooper2_fixture_gate_v2_14.json", errors)

    if state:
        audit_candidate_state(state, errors)
        audit_baseline(state, baseline, errors)
        audit_ledger(root, state, errors)
    if weights:
        audit_weights(root, weights, errors)
    if probes:
        audit_probes(root, probes, errors)
    if validation:
        audit_local_global(validation, errors)
    if py1_gate and py1_gate.get("classification") != "pysnooper1_dependency_recovery_execution_blocked":
        errors.append("standalone PySnooper:1 recovery gate classification mismatch")
    if py2_gate and py2_gate.get("classification") != "pysnooper2_fixture_materialization_forbidden_or_unavailable":
        errors.append("standalone PySnooper:2 fixture gate classification mismatch")

    status = "PASS" if not errors else "FAIL"
    summary = {
        "status": status,
        "campaign_id": CAMPAIGN_ID,
        "required_files_checked": REQUIRED_FILES,
        "manifest_entries_checked": checked_manifest_entries,
        "baseline_preservation_status": baseline.get("status"),
        "ansible2_preservation_status": baseline.get("ansible2_positive_memory_only_status_preserved"),
        "ansible5_preservation_status": baseline.get("ansible5_positive_memory_only_status_preserved"),
        "candidate_scope_status": "PASS" if not errors else "CHECK_ERRORS",
        "probe_count": probes.get("total_probe_count"),
        "patch_attempt_count": (state.get("patch_attempts") or {}).get("total_patch_attempts"),
        "pysnooper1_final_classification": (state.get("final_result") or {}).get("pysnooper1_final_classification"),
        "pysnooper2_final_classification": (state.get("final_result") or {}).get("pysnooper2_final_classification"),
        "full_scoring": (state.get("final_result") or {}).get("controllergate_full_scoring"),
        "full_scoring_allowed": (state.get("final_result") or {}).get("full_scoring_allowed"),
        "self_maintaining_software_demonstrated": (state.get("final_result") or {}).get(
            "self_maintaining_software_demonstrated"
        ),
        "proof_ledger_hash_chain_status": "PASS" if not [e for e in errors if "ledger" in e] else "FAIL",
        "agent_state_lineage_status": "PASS" if not [e for e in errors if "state" in e] else "FAIL",
        "decision_time_outcome_separation_status": "PASS"
        if (state.get("final_result") or {}).get("decision_time_outcome_overlap_count") == 0
        else "FAIL",
        "errors": errors,
    }

    if not errors and state:
        state["audit_summary"] = {
            "status": "PASS",
            "audit_script": "scripts/audit_v2_14_capability_recovery_lane.py",
            "audit_summary_path": "audit_summary_v2_14.json",
        }
        write_json(root / "candidate_state_v2_14.json", state)
        summary["candidate_state_sha256_after_audit"] = sha256_path(root / "candidate_state_v2_14.json")
        write_json(root / "audit_summary_v2_14.json", summary)
        write_manifest(root)
    else:
        write_json(root / "audit_summary_v2_14.json", summary)

    print(f"v2.14 capability recovery audit {status}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

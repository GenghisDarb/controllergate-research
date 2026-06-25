#!/usr/bin/env python3
"""Audit v2.17 PySnooper:1 runtime-workspace materialization evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / "outputs" / "v2_17_pysnooper1_runtime_workspace_materialization"
CAMPAIGN_ID = "v2_17_pysnooper1_runtime_workspace_materialization"
EXPECTED_CURRENT_PROTOCOL = "v2.13"
EXPECTED_HEAD = "e21a31162f4c54be693d8ca8260e42393b39abd3"
REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "workspace_materialization_audit.json",
    "workspace_provenance.json",
    "buggy_checkout_identity.json",
    "pre_repair_replay_gate_summary.json",
    "dependency_recovery_execution_summary.json",
    "isolated_execution_log.txt",
    "patch_candidate_safety_check.json",
    "proof_obligations_ledger.json",
    "claim_boundary_v2_17.json",
    "SHA256SUMS.txt",
]
OPTIONAL_PATCH_FILES = [
    "memory_enabled_source_only_repair_patch.diff",
    "target_validation_log.txt",
    "duplicate_replay_summary.json",
]
WORKSPACE_CLASSIFICATIONS = {
    "workspace_materialized_decision_time_safe",
    "workspace_found_decision_time_safe",
    "blocked_no_decision_time_safe_workspace_source",
    "blocked_workspace_provenance_incomplete",
    "blocked_forbidden_workspace_source",
}
REGRESSION_COMMANDS = [
    ["scripts/audit_v2_16.py"],
    ["scripts/audit_v2_15_chromosomal_maintenance_gate_order.py"],
    ["scripts/audit_v2_14_capability_recovery_lane.py"],
    ["scripts/audit_v2_13_minimal_forensic_context_lane.py"],
    ["scripts/audit_v2_12_dependency_cofactor_recovery.py"],
    ["scripts/controllergate_audit.py", "--protocol", "current"],
    ["scripts/controllergate_run.py", "--protocol", "current", "--dry-run"],
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
        errors.append(f"expected object in {path}")
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
            errors.append(f"SHA256SUMS.txt:{line_number}: malformed entry")
            continue
        expected, rel = parts
        pure = PurePosixPath(rel)
        if rel.startswith("/") or any(part in {"", ".", ".."} for part in pure.parts):
            errors.append(f"SHA256SUMS.txt:{line_number}: unsafe path {rel}")
            continue
        path = root.joinpath(*pure.parts)
        seen.add(rel)
        if not path.is_file():
            errors.append(f"SHA256SUMS.txt:{line_number}: missing file {rel}")
            continue
        if sha256_path(path) != expected:
            errors.append(f"SHA256SUMS.txt:{line_number}: hash mismatch {rel}")
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


def is_outside_repo(path_text: str | None) -> bool:
    if not path_text:
        return False
    path = Path(path_text)
    try:
        resolved = path.resolve()
    except OSError:
        resolved = path.absolute()
    repo = REPO_ROOT.resolve()
    return resolved != repo and repo not in resolved.parents


def audit_workspace(workspace: dict[str, Any], provenance: dict[str, Any], identity: dict[str, Any], errors: list[str]) -> None:
    classification = workspace.get("final_workspace_classification")
    if classification not in WORKSPACE_CLASSIFICATIONS:
        errors.append(f"invalid workspace classification: {classification}")
    if workspace.get("candidate") != "PySnooper:1" or provenance.get("candidate") != "PySnooper:1":
        errors.append("workspace/provenance candidate must be PySnooper:1")
    if workspace.get("fixed_gold_future_evidence_accessed") is not False:
        errors.append("workspace audit accessed fixed/gold/future evidence")
    if workspace.get("tests_fixtures_expectations_mutated") is not False:
        errors.append("workspace materialization mutated tests/fixtures/expectations")
    metadata = workspace.get("metadata_authorizing_workspace_creation") or {}
    required_metadata = [
        "outputs/v2_13_minimal_forensic_context_lane/raw_logs/pysnooper1_policy_recheck_v2_13.json",
        "outputs/v2_13_minimal_forensic_context_lane/raw_logs/pysnooper1_checkout_identity.json",
        "outputs/v2_16_pysnooper1_isolated_recovery_executor/dependency_recovery_audit.json",
    ]
    for rel in required_metadata:
        path = REPO_ROOT / rel
        if metadata.get(rel) != sha256_path(path):
            errors.append(f"workspace metadata hash mismatch or missing: {rel}")
    if identity.get("expected_buggy_head_sha") != EXPECTED_HEAD:
        errors.append("buggy checkout expected HEAD changed")
    if (identity.get("v2_13_recorded_identity") or {}).get("head_sha") != EXPECTED_HEAD:
        errors.append("v2.13 recorded PySnooper:1 HEAD changed")
    if classification in {"workspace_materialized_decision_time_safe", "workspace_found_decision_time_safe"}:
        if provenance.get("decision_time_safe") is not True or provenance.get("provenance_complete") is not True:
            errors.append("decision-time-safe workspace classification lacks complete provenance")
        if workspace.get("workspace_path_outside_live_repo_worktree") is not True or not is_outside_repo(workspace.get("workspace_path")):
            errors.append("decision-time-safe workspace path is not outside live repo")
    else:
        if workspace.get("workspace_found_or_materialized") is not False:
            errors.append("blocked workspace classification cannot claim found/materialized workspace")
        if provenance.get("decision_time_safe") is not False or provenance.get("provenance_complete") is not False:
            errors.append("blocked workspace provenance must remain incomplete and not decision-time-safe")
    if provenance.get("fixed_revision_accessed") is not False or provenance.get("gold_patch_accessed") is not False:
        errors.append("provenance accessed fixed/gold evidence")
    if provenance.get("future_outcome_evidence_accessed") is not False:
        errors.append("provenance accessed future outcome evidence")


def audit_dependency_and_replay(dep: dict[str, Any], replay: dict[str, Any], patch: dict[str, Any], errors: list[str]) -> None:
    if dep.get("declared_dependencies_to_install") != ["python-toolbox"]:
        errors.append("dependency recovery must install only declared python-toolbox")
    if dep.get("undeclared_dependencies_installed") is not False:
        errors.append("undeclared dependency install recorded")
    if dep.get("source_tests_fixtures_expectations_mutated") is not False:
        errors.append("dependency recovery mutated source/tests/fixtures/expectations")
    if dep.get("global_environment_mutated") is not False:
        errors.append("dependency recovery mutated global environment")
    if dep.get("fixed_gold_future_evidence_accessed") is not False:
        errors.append("dependency recovery accessed fixed/gold/future evidence")
    if patch.get("patch_authorized") is True:
        if replay.get("pre_repair_replay_reproduced_target_failure") is not True:
            errors.append("patch authorized without reproduced pre-repair target failure")
        if dep.get("status") != "PASS":
            errors.append("patch authorized without dependency recovery pass")
    if replay.get("patch_authorization") == "allowed" and patch.get("patch_authorized") is not True:
        errors.append("replay and patch authorization fields disagree")


def parse_diff_paths(diff_text: str) -> set[str]:
    paths: set[str] = set()
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            for raw in parts[2:4]:
                if raw.startswith(("a/", "b/")):
                    paths.add(raw[2:])
        elif line.startswith(("--- ", "+++ ")):
            raw = line[4:].strip()
            if raw != "/dev/null" and raw.startswith(("a/", "b/")):
                paths.add(raw[2:])
    return paths


def audit_patch(root: Path, patch: dict[str, Any], results: dict[str, Any], errors: list[str]) -> None:
    if patch.get("patch_attempt_count", 0) > 1:
        errors.append("patch attempt count exceeds 1")
    if patch.get("tests_modified") is not False or patch.get("fixtures_modified") is not False:
        errors.append("patch modified tests or fixtures")
    if patch.get("expectations_modified") is not False or patch.get("benchmark_expectations_modified") is not False:
        errors.append("patch modified benchmark expectations")
    if patch.get("harness_files_modified") is not False:
        errors.append("patch modified harness files")
    patch_file = root / "memory_enabled_source_only_repair_patch.diff"
    if patch.get("patch_generated") is False:
        for rel in OPTIONAL_PATCH_FILES:
            if (root / rel).exists():
                errors.append(f"optional patch output exists despite patch_generated=false: {rel}")
        if patch.get("patch_authorized") is not False or patch.get("patch_attempted") is not False:
            errors.append("patch false state must keep authorized/attempted false")
        if results.get("pysnooper1_scoreable") is not False:
            errors.append("scoreable cannot be true when no patch exists")
        return
    if not patch_file.is_file():
        errors.append("patch_generated=true but patch diff is missing")
        return
    text = patch_file.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        errors.append("generated patch is empty")
    touched = parse_diff_paths(text)
    allowed = set(patch.get("allowed_pysnooper_source_paths") or [])
    forbidden = [item for item in touched if item not in allowed or item.startswith(("tests/", "test/", "harness/", "benchmarks/"))]
    if forbidden:
        errors.append(f"patch touches forbidden paths: {forbidden}")
    if patch.get("patch_sha256") != sha256_path(patch_file):
        errors.append("patch SHA256 mismatch")
    if results.get("pysnooper1_scoreable") is True and results.get("duplicate_replay_status") != "PASS":
        errors.append("scoreable=true requires duplicate clean replay PASS")


def audit_ledger(root: Path, ledger: dict[str, Any], errors: list[str]) -> None:
    previous = None
    for index, entry in enumerate(ledger.get("ledger_entries") or []):
        rel = str(entry.get("path"))
        path = root / rel
        if not path.is_file():
            errors.append(f"ledger entry {index} missing path {rel}")
            continue
        material = {
            "path": rel,
            "sha256": entry.get("sha256"),
            "previous_entry_hash": previous,
        }
        if entry.get("previous_entry_hash") != previous:
            errors.append(f"ledger entry {index} previous hash mismatch")
        if entry.get("sha256") != sha256_path(path):
            errors.append(f"ledger entry {index} target hash mismatch")
        if entry.get("entry_hash") != canonical_sha(material):
            errors.append(f"ledger entry {index} entry hash mismatch")
        previous = entry.get("entry_hash")
    if ledger.get("ledger_tip") != previous:
        errors.append("ledger tip mismatch")


def audit_claims(results: dict[str, Any], claims: dict[str, Any], errors: list[str]) -> None:
    if results.get("candidate_scope") != ["PySnooper:1"] or claims.get("candidate_scope") != ["PySnooper:1"]:
        errors.append("v2.17 scope must be PySnooper:1 only")
    if results.get("pysnooper2_pursued") is not False or claims.get("pysnooper2_pursued") is not False:
        errors.append("PySnooper:2 was pursued")
    if results.get("current_protocol_version") != EXPECTED_CURRENT_PROTOCOL or claims.get("current_protocol_version") != EXPECTED_CURRENT_PROTOCOL:
        errors.append("current protocol boundary changed")
    if claims.get("v2_17_promoted_to_current") is not False:
        errors.append("v2.17 was promoted to current")
    if results.get("full_scoring") != "NOT_RUN" or results.get("full_scoring_allowed") is not False:
        errors.append("full scoring boundary changed")
    if claims.get("full_scoring") != "NOT_RUN" or claims.get("full_scoring_allowed") is not False:
        errors.append("claim full scoring boundary changed")
    if results.get("final_scoreable_count") != 5 or results.get("final_positive_memory_count") != 2:
        errors.append("baseline/positive memory counts changed")
    if results.get("final_non_ansible_positive_memory_count") != 0:
        errors.append("non-Ansible positive-memory count changed")
    if results.get("self_maintaining_software_status") != "false/not_demonstrated":
        errors.append("self-maintaining software was claimed")
    if results.get("memory_lift_status") != "undemonstrated":
        errors.append("memory lift was claimed")


def run_regression_audits(errors: list[str]) -> dict[str, str]:
    statuses: dict[str, str] = {}
    for command in REGRESSION_COMMANDS:
        label = " ".join(command)
        completed = subprocess.run(
            [sys.executable, *command],
            cwd=str(REPO_ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        statuses[label] = "PASS" if completed.returncode == 0 else "FAIL"
        if completed.returncode != 0:
            errors.append(f"regression audit failed: {label}\n{completed.stdout[-1000:]}\n{completed.stderr[-1000:]}")
    return statuses


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit v2.17 PySnooper:1 runtime-workspace materialization outputs.")
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--run-regression-audits", action="store_true")
    args = parser.parse_args()

    root = args.artifact_root.resolve()
    errors: list[str] = []
    for rel in REQUIRED_FILES:
        path = root / rel
        if not path.is_file():
            errors.append(f"missing required output: {rel}")
        elif path.stat().st_size == 0:
            errors.append(f"empty required output: {rel}")
    for path in root.rglob("*"):
        rel = path.relative_to(root).as_posix()
        rel_parts = [part.lower() for part in PurePosixPath(rel).parts]
        if path.suffix.lower() in {".zip", ".tar"} or any(part in {".venv", "venv", "__pycache__"} for part in rel_parts):
            errors.append(f"forbidden packaged path: {rel}")
        if any(part.endswith("_runtime") or part.endswith("_workspace") for part in rel_parts):
            errors.append(f"forbidden packaged runtime/workspace path: {rel}")

    manifest_errors, checked = verify_manifest(root)
    errors.extend(manifest_errors)

    results = load_json(root / "campaign_results.json", errors)
    workspace = load_json(root / "workspace_materialization_audit.json", errors)
    provenance = load_json(root / "workspace_provenance.json", errors)
    identity = load_json(root / "buggy_checkout_identity.json", errors)
    replay = load_json(root / "pre_repair_replay_gate_summary.json", errors)
    dep = load_json(root / "dependency_recovery_execution_summary.json", errors)
    patch = load_json(root / "patch_candidate_safety_check.json", errors)
    ledger = load_json(root / "proof_obligations_ledger.json", errors)
    claims = load_json(root / "claim_boundary_v2_17.json", errors)

    if workspace and provenance and identity:
        audit_workspace(workspace, provenance, identity, errors)
    if dep and replay and patch:
        audit_dependency_and_replay(dep, replay, patch, errors)
    if patch and results:
        audit_patch(root, patch, results, errors)
    if ledger:
        audit_ledger(root, ledger, errors)
    if results and claims:
        audit_claims(results, claims, errors)
    regression_statuses = run_regression_audits(errors) if args.run_regression_audits else {}

    status = "PASS" if not errors else "FAIL"
    print(f"v2.17 PySnooper:1 runtime workspace materialization audit {status} ({checked} manifest entries)")
    if regression_statuses:
        for label, value in regression_statuses.items():
            print(f"regression_audit {label}: {value}")
    if results:
        for key in [
            "workspace_materialization_classification",
            "workspace_provenance_status",
            "pre_repair_replay_status",
            "dependency_recovery_execution_status",
            "patch_generated",
            "patch_authorized",
            "patch_attempted",
            "pysnooper1_scoreable",
            "pysnooper1_positive_memory_only",
        ]:
            print(f"{key}={results.get(key)}")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

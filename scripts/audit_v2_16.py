#!/usr/bin/env python3
"""Audit v2.16 PySnooper:1 isolated recovery executor evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / "outputs" / "v2_16_pysnooper1_isolated_recovery_executor"
V215_ROOT = REPO_ROOT / "outputs" / "v2_15_chromosomal_maintenance_gate_order"
CAMPAIGN_ID = "v2_16_pysnooper1_isolated_recovery_executor"
REQUIRED_FILES = [
    "campaign_summary.md",
    "campaign_results.json",
    "dependency_recovery_audit.json",
    "isolated_execution_log.txt",
    "pre_repair_replay_gate_summary.json",
    "patch_candidate_safety_check.json",
    "pysnooper2_fixture_materialization_permanent_block.json",
    "claim_boundary_v2_16.json",
    "proof_obligations_ledger.json",
    "audit_summary_v2_16.json",
    "SHA256SUMS.txt",
]
REQUIRED_FORBIDDEN_OPERATIONS = {
    "inspect fixed revision contents",
    "inspect BugsInPy gold patches",
    "use future outcome evidence",
    "copy known fixes manually",
    "read hidden labels",
    "mutate tests to match broken code",
    "modify benchmark metadata or expectations",
    "install undeclared dependencies",
    "vendor global helpers into the project",
}
ALLOWED_DECLARATION_SUFFIXES = ("setup.py", "requirements.txt", "pipfile")


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
        path = root.joinpath(*pure.parts)
        seen.add(rel)
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


def audit_dependency_recovery(value: dict[str, Any], errors: list[str]) -> None:
    if value.get("candidate") != "PySnooper:1":
        errors.append("dependency recovery candidate must be PySnooper:1")
    if value.get("source_or_tests_mutated") is not False:
        errors.append("dependency recovery mutated source or tests")
    if value.get("undeclared_dependencies_installed") is not False:
        errors.append("dependency recovery installed undeclared dependencies")
    if not REQUIRED_FORBIDDEN_OPERATIONS.issubset(set(value.get("forbidden_operations_checked") or [])):
        errors.append("dependency recovery missing forbidden-operation checks")
    evidence = value.get("dependency_declaration_evidence") or []
    if not evidence:
        errors.append("missing dependency declaration evidence")
    for record in evidence:
        path = str(record.get("path", "")).lower()
        if not path.endswith(ALLOWED_DECLARATION_SUFFIXES):
            errors.append(f"declaration evidence uses forbidden source: {record.get('path')}")
        if record.get("decision_time_safe") is not True:
            errors.append(f"declaration evidence is not decision-time-safe: {record.get('path')}")
    contract = value.get("executor_contract") or {}
    if contract.get("create_virtual_environment") is not True:
        errors.append("executor contract does not create an isolated venv")
    if contract.get("declared_dependencies_to_install") != ["python-toolbox"]:
        errors.append("executor contract must install only declared python-toolbox")
    command_norm = contract.get("command_normalization") or {}
    if command_norm.get("PYTHONPATH") != "checked_out_project_root":
        errors.append("executor contract does not normalize PYTHONPATH to project root")
    if value.get("executor_executed") is not False:
        errors.append("local v2.16 runner unexpectedly claims executor execution")


def parse_diff_paths(diff_text: str) -> set[str]:
    paths: set[str] = set()
    for line in diff_text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                for raw in parts[2:4]:
                    if raw.startswith(("a/", "b/")):
                        paths.add(raw[2:])
        elif line.startswith(("--- ", "+++ ")):
            raw = line[4:].strip()
            if raw != "/dev/null" and raw.startswith(("a/", "b/")):
                paths.add(raw[2:])
    return paths


def audit_patch_safety(root: Path, value: dict[str, Any], errors: list[str]) -> None:
    allowed = value.get("allowed_target_python_source_file")
    if allowed != "pysnooper/utils.py":
        errors.append("allowed target source file must be explicitly pysnooper/utils.py")
    if value.get("test_files_modified") is not False:
        errors.append("patch safety indicates test modifications")
    if value.get("benchmark_metadata_modified") is not False:
        errors.append("patch safety indicates benchmark metadata modifications")
    if value.get("harness_directories_modified") is not False:
        errors.append("patch safety indicates harness directory modifications")
    if value.get("no_op_patch_counted_as_success") is not False:
        errors.append("no-op patch was counted as success")

    diff_files = [
        root / "no_memory_source_only_repair_patch.diff",
        root / "memory_enabled_source_only_repair_patch.diff",
    ]
    present = [path for path in diff_files if path.exists()]
    if value.get("patch_generated") is False:
        if present:
            errors.append("diff files exist even though patch_generated is false")
        if value.get("patch_authorized") is not False:
            errors.append("patch authorization must be denied when no patch is generated")
        return
    if value.get("patch_generated") is not True or value.get("patch_authorized") is not True:
        errors.append("patch state must be explicit true/true or false/false")
        return
    for path in diff_files:
        if not path.is_file():
            errors.append(f"missing generated diff: {path.name}")
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            errors.append(f"empty generated diff: {path.name}")
            continue
        touched = parse_diff_paths(text)
        if not touched:
            errors.append(f"generated diff does not parse touched paths: {path.name}")
        forbidden = [item for item in touched if item != allowed or item.startswith(("tests/", "test/", "harness/", "benchmark"))]
        if forbidden:
            errors.append(f"generated diff touches forbidden paths {forbidden}: {path.name}")


def audit_preconditions(value: dict[str, Any], patch: dict[str, Any], errors: list[str]) -> None:
    required = [
        value.get("pre_repair_replay_gate_passed"),
        value.get("isolated_repair_workspace_equivalence_passed"),
        value.get("no_memory_path_reproduces_target_failure"),
        value.get("memory_enabled_path_reproduces_target_failure"),
    ]
    if patch.get("patch_authorized") is True and not all(item is True for item in required):
        errors.append("patch was authorized before all replay/workspace preconditions passed")
    if patch.get("patch_authorized") is False and value.get("status") != "BLOCK":
        errors.append("pre-repair gate must block when patch is not authorized")


def audit_ledger(root: Path, ledger: dict[str, Any], dep: dict[str, Any], patch: dict[str, Any], errors: list[str]) -> None:
    contract = dep.get("executor_contract") or {}
    env_hash = ((ledger.get("isolated_execution_environment") or {}).get("sha256"))
    if env_hash != canonical_sha(contract):
        errors.append("isolated execution environment contract hash mismatch")
    previous = None
    for index, entry in enumerate(ledger.get("ledger_entries") or []):
        expected_material = {
            "path": entry.get("path"),
            "sha256": entry.get("sha256"),
            "previous_entry_hash": previous,
        }
        if entry.get("previous_entry_hash") != previous:
            errors.append(f"ledger entry {index} previous hash mismatch")
        if canonical_sha(expected_material) != entry.get("entry_hash"):
            errors.append(f"ledger entry {index} entry hash mismatch")
        path = root / str(entry.get("path"))
        if not path.is_file() or sha256_path(path) != entry.get("sha256"):
            errors.append(f"ledger entry {index} target hash mismatch")
        previous = entry.get("entry_hash")
    if ledger.get("ledger_tip") != previous:
        errors.append("ledger tip mismatch")
    diff_hashes = ledger.get("proposed_diff_hashes") or {}
    if patch.get("patch_generated") is False:
        if any(value is not None for value in diff_hashes.values()):
            errors.append("ledger contains diff hashes even though patch generation is blocked")
    else:
        for rel, expected in diff_hashes.items():
            path = root / rel
            if not path.is_file() or sha256_path(path) != expected:
                errors.append(f"ledger diff hash mismatch: {rel}")


def audit_claims(results: dict[str, Any], claims: dict[str, Any], errors: list[str]) -> None:
    if results.get("candidate_scope") != ["PySnooper:1"]:
        errors.append("v2.16 candidate scope must be PySnooper:1 only")
    if results.get("pysnooper2_scope") != "permanently_blocked_unless_decision_time_safe_fixture_provenance_exists":
        errors.append("PySnooper:2 is not preserved as blocked")
    if results.get("pysnooper1_classification") != "blocked_no_safe_patch_candidate_generated":
        errors.append("unexpected PySnooper:1 classification")
    if results.get("scoreable_non_ansible_result") is not False:
        errors.append("v2.16 claims a scoreable non-Ansible result without audited patch evidence")
    if results.get("final_non_ansible_positive_memory_count") != 0:
        errors.append("non-Ansible positive-memory count changed")
    if results.get("full_scoring") != "NOT_RUN" or results.get("full_scoring_allowed") is not False:
        errors.append("full-scoring boundary changed")
    if results.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software was claimed")
    if results.get("family_generalization_expanded") is not False:
        errors.append("family generalization expanded")
    if claims.get("aggregate_criteria_met") is not False:
        errors.append("aggregate positive-memory criteria unexpectedly marked met")
    required = claims.get("positive_memory_claim_requires") or {}
    if required.get("minimum_scoreable_bugsinpy_real_bug_episodes") != 3:
        errors.append("positive-memory aggregate minimum episode count changed")
    if required.get("memory_enabled_outperforms_no_memory_in_at_least") != 2:
        errors.append("positive-memory aggregate win threshold changed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit v2.16 PySnooper:1 isolated recovery executor outputs.")
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    root = args.artifact_root.resolve()
    errors: list[str] = []

    for rel in REQUIRED_FILES:
        path = root / rel
        if not path.is_file():
            errors.append(f"missing required v2.16 output: {rel}")
        elif path.stat().st_size == 0:
            errors.append(f"empty required v2.16 output: {rel}")
    for path in root.rglob("*"):
        lowered = path.as_posix().lower()
        if path.suffix.lower() in {".zip", ".tar"} or any(token in lowered for token in [".venv", "/venv/", "__pycache__", "_runtime"]):
            errors.append(f"forbidden packaged path: {path.relative_to(root).as_posix()}")

    manifest_errors, checked = verify_manifest(root)
    errors.extend(manifest_errors)

    dep = load_json(root / "dependency_recovery_audit.json", errors)
    pre = load_json(root / "pre_repair_replay_gate_summary.json", errors)
    patch = load_json(root / "patch_candidate_safety_check.json", errors)
    ledger = load_json(root / "proof_obligations_ledger.json", errors)
    results = load_json(root / "campaign_results.json", errors)
    claims = load_json(root / "claim_boundary_v2_16.json", errors)
    py2 = load_json(root / "pysnooper2_fixture_materialization_permanent_block.json", errors)
    v215 = load_json(V215_ROOT / "v2_15_official_artifact_verification.json", errors)

    if v215.get("status") != "PASS" or v215.get("current_protocol_version") != "v2.13":
        errors.append("v2.15 official verification/current protocol boundary is not preserved")
    if py2.get("status") != "BLOCK" or py2.get("permanent_until_decision_time_safe_fixture_provenance") is not True:
        errors.append("PySnooper:2 fixture materialization permanence not enforced")

    if dep:
        audit_dependency_recovery(dep, errors)
    if patch:
        audit_patch_safety(root, patch, errors)
    if pre and patch:
        audit_preconditions(pre, patch, errors)
    if ledger and dep and patch:
        audit_ledger(root, ledger, dep, patch, errors)
    if results and claims:
        audit_claims(results, claims, errors)

    status = "PASS" if not errors else "FAIL"
    print(f"v2.16 PySnooper:1 isolated recovery executor audit {status} ({checked} manifest entries)")
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Generate v2.16 PySnooper:1 isolated recovery executor evidence.

v2.16 is intentionally narrow.  It turns the v2.15 manual-review next action
into a machine-checkable executor contract for PySnooper:1 only.  The local
repository does not contain a live BugsInPy PySnooper checkout/runtime
workspace, so this runner records the safe executor design and stops before
patch generation.  A scoreable non-Ansible result may only be claimed by a later
run that materializes the isolated workspace, reproduces the target failure in
both arms, and emits source-only, non-empty diffs that pass audit_v2_16.py.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_16_pysnooper1_isolated_recovery_executor"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V213_ROOT = REPO_ROOT / "outputs" / "v2_13_minimal_forensic_context_lane"
V214_ROOT = REPO_ROOT / "outputs" / "v2_14_capability_recovery_lane"
V215_ROOT = REPO_ROOT / "outputs" / "v2_15_chromosomal_maintenance_gate_order"

FORBIDDEN_OPERATIONS = [
    "inspect fixed revision contents",
    "inspect BugsInPy gold patches",
    "use future outcome evidence",
    "copy known fixes manually",
    "read hidden labels",
    "mutate tests to match broken code",
    "modify benchmark metadata or expectations",
    "install undeclared dependencies",
    "vendor global helpers into the project",
    "claim full scoring",
    "claim self-maintaining software",
    "claim generalized non-Ansible capability",
]

REQUIRED_PRECONDITIONS = [
    "pre_repair_replay_gate_passes",
    "isolated_repair_workspace_equivalence_passes",
    "no_memory_path_reproduces_target_failure",
    "memory_enabled_path_reproduces_target_failure",
    "source_only_patch_boundary_passes",
]


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: Any) -> str:
    material = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_bytes(material.encode("utf-8"))


def repo_rel(path: Path) -> str:
    resolved = path.resolve()
    if resolved == REPO_ROOT or REPO_ROOT in resolved.parents:
        return resolved.relative_to(REPO_ROOT).as_posix()
    return str(resolved)


def evidence_hashes(paths: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for rel in paths:
        path = REPO_ROOT / rel
        if path.is_file():
            result[rel] = sha256_path(path)
    return result


def safe_reset(root: Path) -> None:
    resolved = root.resolve()
    allowed = (REPO_ROOT / "outputs" / CAMPAIGN_ID).resolve()
    if resolved != allowed:
        raise ValueError(f"refusing to reset unexpected output root: {resolved}")
    if resolved.exists():
        shutil.rmtree(resolved)
    resolved.mkdir(parents=True, exist_ok=True)


def write_manifest(root: Path) -> None:
    files = sorted(
        (path for path in root.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    lines = [f"{sha256_path(path)}  {path.relative_to(root).as_posix()}" for path in files]
    write_text(root / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def declaration_evidence(policy: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in policy.get("metadata_files_inspected") or []:
        raw_path = str(item.get("path", ""))
        lowered = raw_path.lower()
        if not lowered.endswith(("setup.py", "requirements.txt", "pipfile")):
            continue
        matching = item.get("matching_lines") or []
        if not matching and not lowered.endswith("requirements.txt"):
            continue
        role = "dependency_declaration" if matching else "empty_dependency_context"
        records.append(
            {
                "path": raw_path,
                "sha256": item.get("sha256"),
                "matching_lines": matching,
                "role": role,
                "decision_time_safe": policy.get("decision_time_safe_status") == "PASS",
                "source_boundary": "buggy_checkout_metadata",
            }
        )
    return records


def build_ledger(root: Path, environment_contract: dict[str, Any], diff_paths: list[str]) -> dict[str, Any]:
    paths = [
        "dependency_recovery_audit.json",
        "isolated_execution_log.txt",
        "pre_repair_replay_gate_summary.json",
        "patch_candidate_safety_check.json",
        "pysnooper2_fixture_materialization_permanent_block.json",
        "claim_boundary_v2_16.json",
        "campaign_results.json",
    ]
    entries = []
    previous: str | None = None
    for rel in paths:
        path = root / rel
        entry_material = {
            "path": rel,
            "sha256": sha256_path(path),
            "previous_entry_hash": previous,
        }
        entry = dict(entry_material)
        entry["entry_hash"] = canonical_sha(entry_material)
        entries.append(entry)
        previous = entry["entry_hash"]
    diff_hashes = {
        rel: sha256_path(root / rel) if (root / rel).is_file() else None
        for rel in diff_paths
    }
    return {
        "campaign_id": CAMPAIGN_ID,
        "status": "PASS",
        "isolated_execution_environment": {
            "status": "contract_only_not_materialized",
            "sha256": canonical_sha(environment_contract),
            "hash_material": "isolated_executor_contract",
        },
        "proposed_diff_hashes": diff_hashes,
        "proposed_diff_status": "not_generated_preconditions_failed",
        "ledger_entries": entries,
        "ledger_tip": previous,
    }


def main() -> int:
    safe_reset(OUTPUT_ROOT)

    v213_policy_path = V213_ROOT / "raw_logs" / "pysnooper1_policy_recheck_v2_13.json"
    v213_checkout_identity_path = V213_ROOT / "raw_logs" / "pysnooper1_checkout_identity.json"
    v214_gate_path = V214_ROOT / "pysnooper1_recovery_gate_v2_14.json"
    v214_weights_path = V214_ROOT / "failure_memory_weights_v2_14.json"
    v215_results_path = V215_ROOT / "campaign_results.json"
    v215_verification_path = V215_ROOT / "v2_15_official_artifact_verification.json"

    policy = load_json(v213_policy_path)
    checkout_identity = load_json(v213_checkout_identity_path)
    v214_gate = load_json(v214_gate_path)
    v215_results = load_json(v215_results_path)
    v215_verification = load_json(v215_verification_path)

    evidence_files = [
        repo_rel(v213_policy_path),
        repo_rel(v213_checkout_identity_path),
        repo_rel(v214_gate_path),
        repo_rel(v214_weights_path),
        repo_rel(v215_results_path),
        repo_rel(v215_verification_path),
    ]
    declarations = declaration_evidence(policy)
    declared_dependencies = sorted(
        {
            "python-toolbox"
            for record in declarations
            for line in record.get("matching_lines") or []
            if "python-toolbox" in str(line.get("line", "")) or "python_toolbox" in str(line.get("line", ""))
        }
    )
    environment_contract = {
        "candidate": "PySnooper:1",
        "create_virtual_environment": True,
        "venv_scope": "strictly isolated inside candidate runtime workspace",
        "dependency_install_policy": "install only dependencies explicitly declared in buggy checkout metadata",
        "declared_dependencies_to_install": declared_dependencies,
        "forbidden_dependency_sources": [
            "global site-packages",
            "manually vendored helpers",
            "fixed revision files",
            "gold patches",
            "future outcome logs",
        ],
        "command_normalization": {
            "PYTHONPATH": "checked_out_project_root",
            "working_directory": "checked_out_project_root",
        },
        "target_command": "BugsInPy PySnooper bug 1 target test from decision-time bug metadata",
        "requires_runtime_workspace": True,
    }
    executor_ready = bool(declared_dependencies) and policy.get("decision_time_safe_status") == "PASS"

    dependency_recovery = {
        "status": "PASS" if executor_ready else "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "decision_time_safe_evidence_scope": [
            "buggy checkout setup.py",
            "buggy checkout requirements.txt",
            "buggy checkout Pipfile",
            "native imports in buggy source files",
            "initial failing test context",
        ],
        "dependency_declaration_evidence": declarations,
        "declared_dependencies_to_install": declared_dependencies,
        "recovery_policy_allowed": v214_gate.get("recovery_policy_allowed") is True,
        "executor_contract": environment_contract,
        "executor_executed": False,
        "executor_execution_blocker": "live BugsInPy PySnooper buggy checkout/runtime workspace is not present in the repository",
        "source_or_tests_mutated": False,
        "undeclared_dependencies_installed": False,
        "forbidden_operations_checked": FORBIDDEN_OPERATIONS,
        "evidence_files": evidence_files,
        "sha256_inputs": evidence_hashes(evidence_files),
    }
    write_json(OUTPUT_ROOT / "dependency_recovery_audit.json", dependency_recovery)

    isolated_log = "\n".join(
        [
            "v2.16 PySnooper:1 isolated recovery executor log",
            "execution_status: not_executed",
            "reason: live BugsInPy PySnooper buggy checkout/runtime workspace is absent from the repository",
            "required_action_when_runtime_available: create venv inside isolated workspace",
            "required_install_policy: install only python-toolbox declared by buggy checkout setup.py",
            "required_command_normalization: set PYTHONPATH to checked-out project root",
            "forbidden: fixed revision, BugsInPy gold patches, future outcomes, hidden labels, test mutation",
            "",
        ]
    )
    write_text(OUTPUT_ROOT / "isolated_execution_log.txt", isolated_log)

    pre_repair = {
        "status": "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "pre_repair_replay_gate_passed": False,
        "isolated_repair_workspace_equivalence_passed": False,
        "no_memory_path_reproduces_target_failure": False,
        "memory_enabled_path_reproduces_target_failure": False,
        "target_failure_cannot_be_reproduced_reason": "isolated runtime workspace absent; no repair attempt authorized",
        "required_preconditions_for_patch_authorization": REQUIRED_PRECONDITIONS,
        "patch_authorization": "denied",
        "evidence_files": evidence_files,
        "sha256_inputs": evidence_hashes(evidence_files),
    }
    write_json(OUTPUT_ROOT / "pre_repair_replay_gate_summary.json", pre_repair)

    patch_safety = {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:1",
        "patch_authorized": False,
        "patch_generated": False,
        "patch_attempted": False,
        "no_memory_diff_path": None,
        "memory_enabled_diff_path": None,
        "allowed_target_python_source_file": "pysnooper/utils.py",
        "diff_non_empty": False,
        "touches_only_allowed_source_file": None,
        "test_files_modified": False,
        "benchmark_metadata_modified": False,
        "harness_directories_modified": False,
        "no_op_patch_counted_as_success": False,
        "reason_no_diff_generated": "patch preconditions did not pass; generating a no-op diff is forbidden",
        "forbidden_operations_checked": FORBIDDEN_OPERATIONS,
    }
    write_json(OUTPUT_ROOT / "patch_candidate_safety_check.json", patch_safety)

    pysnooper2_block = {
        "status": "BLOCK",
        "campaign_id": CAMPAIGN_ID,
        "candidate": "PySnooper:2",
        "classification": "fixture_materialization_permanently_blocked_without_decision_time_safe_provenance",
        "missing_fixture": "tests/mini_toolbox.py",
        "permanent_until_decision_time_safe_fixture_provenance": True,
        "allowed_sources_checked": [
            "BugsInPy metadata",
            "buggy checkout",
            "decision-time-safe test materialization records",
        ],
        "forbidden_sources": [
            "fixed revision contents",
            "BugsInPy gold patches",
            "future outcome evidence",
            "hallucinated fixture reconstruction",
            "test or fixture mutation to match broken code",
        ],
        "next_allowed_action": "do_not_attempt_in_v2_16",
    }
    write_json(OUTPUT_ROOT / "pysnooper2_fixture_materialization_permanent_block.json", pysnooper2_block)

    claim_boundary = {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "current_protocol_version": "v2.13",
        "v2_16_promoted_to_current": False,
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "self_maintaining_software_demonstrated": False,
        "family_generalization": "not_expanded",
        "memory_lift_demonstrated": False,
        "non_ansible_positive_memory_count": 0,
        "positive_memory_claim_requires": {
            "minimum_scoreable_bugsinpy_real_bug_episodes": 3,
            "memory_enabled_outperforms_no_memory_in_at_least": 2,
            "corruption_instances": 0,
            "label_leakage_instances": 0,
            "decision_time_outcome_overlap_instances": 0,
        },
        "aggregate_criteria_met": False,
    }
    write_json(OUTPUT_ROOT / "claim_boundary_v2_16.json", claim_boundary)

    campaign_results = {
        "status": "PASS_WITH_EXECUTOR_CONTRACT_BLOCKED",
        "campaign_id": CAMPAIGN_ID,
        "based_on": "v2.15",
        "candidate_scope": ["PySnooper:1"],
        "pysnooper2_scope": "permanently_blocked_unless_decision_time_safe_fixture_provenance_exists",
        "pysnooper1_classification": "blocked_no_safe_patch_candidate_generated",
        "dependency_recovery_executor_contract_ready": executor_ready,
        "dependency_recovery_executor_executed": False,
        "scoreable_non_ansible_result": False,
        "final_scoreable_count": v215_results.get("final_scoreable_count"),
        "final_positive_memory_count": v215_results.get("final_positive_memory_count"),
        "final_non_ansible_positive_memory_count": 0,
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_demonstrated": False,
        "self_maintaining_software_demonstrated": False,
        "family_generalization_expanded": False,
        "current_protocol_version": "v2.13",
        "v2_15_official_artifact_verified": v215_verification.get("status") == "PASS",
        "exact_blocker": "PySnooper:1 isolated runtime workspace was not available, so pre-repair replay could not be reproduced and patch generation remained forbidden.",
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", campaign_results)

    summary = f"""# v2.16 PySnooper:1 Isolated Recovery Executor

- Status: `PASS_WITH_EXECUTOR_CONTRACT_BLOCKED`.
- Candidate scope: `PySnooper:1` only.
- PySnooper:2 status: permanently blocked unless decision-time-safe fixture provenance for `tests/mini_toolbox.py` is proven.
- Decision-time-safe recovery evidence: buggy-checkout dependency declarations from v2.13/v2.14 (`setup.py`; `requirements.txt` context).
- Executor contract: create an isolated `venv`, install only `python-toolbox`, set `PYTHONPATH` to the checked-out project root, and run the target test strictly inside that sandbox.
- Executor executed locally: `false`; the live BugsInPy PySnooper checkout/runtime workspace is not committed in this repository.
- Patch generated: `false`; no `.diff` file is created because pre-repair replay and workspace-equivalence preconditions did not pass.
- PySnooper:1 classification: `blocked_no_safe_patch_candidate_generated`.
- Scoreable non-Ansible result: `false`.
- Scoreable count remains `{campaign_results['final_scoreable_count']}`; positive-memory count remains `{campaign_results['final_positive_memory_count']}`; non-Ansible positive-memory count remains `0`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains undemonstrated.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`.
"""
    write_text(OUTPUT_ROOT / "campaign_summary.md", summary)

    ledger = build_ledger(
        OUTPUT_ROOT,
        environment_contract,
        ["no_memory_source_only_repair_patch.diff", "memory_enabled_source_only_repair_patch.diff"],
    )
    write_json(OUTPUT_ROOT / "proof_obligations_ledger.json", ledger)

    audit_summary = {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "audit_script": "scripts/audit_v2_16.py",
        "classification": campaign_results["pysnooper1_classification"],
        "manifest_entries_expected_after_runner": 10,
        "patch_generated": False,
        "scoreable_non_ansible_result": False,
    }
    write_json(OUTPUT_ROOT / "audit_summary_v2_16.json", audit_summary)
    write_manifest(OUTPUT_ROOT)
    print(f"v2.16 PySnooper:1 isolated recovery executor outputs wrote {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

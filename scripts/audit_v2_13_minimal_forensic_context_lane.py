#!/usr/bin/env python3
"""Independent audit for the v2.13 minimal forensic context lane."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = REPO_ROOT / "outputs" / "v2_13_minimal_forensic_context_lane"
V212_EPISODE = REPO_ROOT / "outputs" / "v2_12_dependency_cofactor_recovery" / "episode_034"
REQUIRED_FILES = [
    "campaign_summary.md",
    "candidate_state_v2_13.json",
    "pysnooper2_patch_failure_classification.json",
    "pysnooper2_candidate_context.json",
    "audit_summary_v2_13.json",
    "SHA256SUMS.txt",
]
BASELINE_IDS = ["youtube-dl:1", "black:4", "fastapi:1", "ansible:2", "ansible:5"]
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
    if not path.exists():
        errors.append(f"missing JSON file: {path}")
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        errors.append(f"invalid JSON {path}: {exc}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"expected JSON object: {path}")
        return {}
    return value


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
        if not path.exists():
            errors.append(f"{manifest}:{line_number}: missing {rel}")
            continue
        checked += 1
        if sha256_path(path) != expected:
            errors.append(f"{manifest}:{line_number}: hash mismatch {rel}")
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


def parse_diff_independent(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="strict")
    old_path: str | None = None
    touched: set[str] = set()
    added: list[str] = []
    removed: list[str] = []
    hunks = 0
    unsafe = False
    malformed = False

    def normalize(raw: str) -> str | None:
        nonlocal unsafe
        value = raw.strip().split("\t", 1)[0].replace("\\", "/")
        if value == "/dev/null":
            return None
        if value.startswith(("a/", "b/")):
            value = value[2:]
        parts = PurePosixPath(value).parts
        if not value or value.startswith("/") or re.match(r"^[A-Za-z]:", value) or any(part in {"", ".", ".."} for part in parts):
            unsafe = True
        return "/".join(parts)

    for line in text.splitlines():
        if line.startswith("--- "):
            old_path = normalize(line[4:])
        elif line.startswith("+++ "):
            new_path = normalize(line[4:])
            if old_path is None and new_path is None:
                malformed = True
            elif new_path or old_path:
                touched.add(new_path or old_path or "")
            old_path = None
        elif line.startswith("@@"):
            hunks += 1
        elif line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])

    def semantic(lines: list[str]) -> list[str]:
        result = []
        for line in lines:
            code = line.strip().split("#", 1)[0]
            token = re.sub(r"\s+", "", code)
            if token:
                result.append(token)
        return sorted(result)

    return {
        "touched_files": sorted(touched),
        "hunk_count": hunks,
        "nonempty": bool(text.strip() and hunks and touched),
        "semantic": semantic(added) != semantic(removed) and bool(semantic(added) or semantic(removed)),
        "unsafe": unsafe,
        "malformed": malformed,
    }


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


def audit_actual(root: Path, state: dict[str, Any], classification: dict[str, Any], context: dict[str, Any], errors: list[str]) -> None:
    if state.get("campaign_id") != "v2_13_minimal_forensic_context_lane" or state.get("based_on_v2_12") is not True:
        errors.append("candidate state has the wrong campaign identity or base version")
    for section_name in [
        "baseline_preservation",
        "pysnooper1_policy_recheck",
        "pysnooper2_context_extraction",
        "pysnooper2_failed_patch_analysis",
        "pysnooper2_revised_patch_attempt",
        "final_result",
    ]:
        section = state.get(section_name) or {}
        for field in STATE_FIELDS:
            if field not in section:
                errors.append(f"{section_name} missing state-custody field {field}")

    baseline = state.get("baseline_preservation") or {}
    if baseline.get("baseline_execution_scope") != BASELINE_IDS:
        errors.append("baseline execution scope must be exactly the five required candidates in order")
    if baseline.get("broad_candidate_sweep_executed") is not False:
        errors.append("v2.13 baseline must not execute a broad candidate sweep")
    if baseline.get("exact_v2_12_scoring_harness_reused") is not True:
        errors.append("baseline must reuse the exact v2.12 scoring harness semantics")
    if baseline.get("baseline_preservation_passed") is not True or baseline.get("status") != "PASS":
        errors.append("v2.12 baseline preservation did not PASS")
    if baseline.get("ansible2_positive_memory_only_status_preserved") is not True:
        errors.append("ansible:2 positive_memory_only was not preserved")
    if baseline.get("ansible5_positive_memory_only_status_preserved") is not True:
        errors.append("ansible:5 positive_memory_only was not preserved")
    records = baseline.get("required_baseline_candidates") or []
    if [record.get("candidate") for record in records] != BASELINE_IDS:
        errors.append("baseline result records are missing or reordered")
    if any(record.get("scoreable") is not True for record in records):
        errors.append("one or more required baseline candidates ceased to be scoreable")
    for rel in baseline.get("evidence_files") or []:
        if not (root / rel).is_file():
            errors.append(f"missing baseline execution evidence: {rel}")
    for record in records:
        episode_id = str(record.get("episode_id") or "unknown")
        candidate_slug = str(record.get("candidate") or "unknown").replace(":", "_")
        evidence_dir = root / "raw_logs" / "baseline" / f"{episode_id}_{candidate_slug}"
        limited = load_json(evidence_dir / "limited_scoring_result.json", errors)
        if limited.get("scoreable") is not True or limited.get("classification") != record.get("classification"):
            errors.append(f"baseline limited-scoring evidence disagrees for {record.get('candidate')}")
        for name in ["no_memory_post_repair_log_raw.txt", "memory_enabled_post_repair_log_raw.txt"]:
            path = evidence_dir / name
            if not path.exists() or path.stat().st_size == 0:
                errors.append(f"missing baseline raw validation log: {path}")

    py1 = state.get("pysnooper1_policy_recheck") or {}
    if py1.get("status") != "PASS" or py1.get("decision_time_safe_status") != "PASS":
        errors.append("PySnooper:1 policy recheck did not PASS")
    if py1.get("installation_performed") is not False:
        errors.append("PySnooper:1 policy recheck must not install python_toolbox")
    metadata = py1.get("metadata_files_inspected") or []
    declared_from_actual_lines = any(record.get("matching_lines") for record in metadata if isinstance(record, dict))
    if bool(py1.get("python_toolbox_declared")) != declared_from_actual_lines:
        errors.append("PySnooper:1 declaration result does not match inspected metadata lines")
    expected_py1 = (
        "dependency_recovery_allowed_by_policy_not_executed_in_minimal_lane"
        if declared_from_actual_lines
        else "dependency_recovery_forbidden_by_policy"
    )
    if py1.get("classification") != expected_py1:
        errors.append("PySnooper:1 final policy classification does not match direct metadata evidence")

    if classification.get("status") != "PASS":
        errors.append("deterministic failed-patch classifier did not PASS")
    patch_path = V212_EPISODE / "memory_enabled_source_only_repair_patch.diff"
    parsed = parse_diff_independent(patch_path)
    if parsed["touched_files"] != ["pysnooper/variables.py"]:
        errors.append("independent diff parser found an unexpected v2.12 patch surface")
    if not parsed["nonempty"] or not parsed["semantic"]:
        errors.append("independent diff parser found an empty or degenerate patch")
    if parsed["unsafe"] or parsed["malformed"]:
        errors.append("independent diff parser found unsafe or malformed patch structure")
    if classification.get("touched_files") != parsed["touched_files"]:
        errors.append("classifier touched-files result disagrees with independent diff parsing")
    for field, expected in [
        ("patch_nonempty", True),
        ("patch_semantic_delta_detected", True),
        ("degenerate_flatline_detected", False),
        ("source_only_patch", True),
        ("tests_modified", False),
        ("benchmark_expectations_modified", False),
        ("generated_fixtures_modified", False),
    ]:
        if classification.get(field) is not expected:
            errors.append(f"classifier field {field} must be {expected}")
    if classification.get("deterministic_classification") != "fixture_materialization_incomplete":
        errors.append("v2.12 failed patch must classify as fixture_materialization_incomplete")
    if classification.get("source_only_repair_actionable") is not False:
        errors.append("fixture-materialization blocker must not authorize a source-only revision")

    if context.get("status") != "PASS" or context.get("candidate") != "PySnooper:2":
        errors.append("bounded PySnooper:2 context extraction did not PASS")
    budget = context.get("context_budget") or {}
    if int(budget.get("selected_file_count", 999)) > 20 or int(budget.get("selected_symbol_count", 999)) > 80:
        errors.append("bounded context extraction exceeded its file or symbol budget")
    if int(budget.get("max_probe_commands", 999)) != 2:
        errors.append("context must preserve the two-probe maximum")
    missing_helpers = context.get("missing_fixture_or_test_helpers_referenced") or []
    if "tests/mini_toolbox.py" not in missing_helpers:
        errors.append("context must directly establish missing tests/mini_toolbox.py")
    identity = context.get("buggy_checkout_identity") or {}
    if identity.get("head_sha") != "e21a31162f4c54be693d8ca8260e42393b39abd3":
        errors.append("PySnooper:2 buggy checkout identity does not match the v2.12 source provenance")
    if identity.get("status_porcelain") not in {"", None}:
        errors.append("context collector observed source/test drift in the buggy checkout")

    direct_outputs = {
        "pysnooper2_patch_failure_classification.json": classification,
        "pysnooper2_candidate_context.json": context,
    }
    for rel, _data in direct_outputs.items():
        path = root / rel
        section_name = "pysnooper2_failed_patch_analysis" if "classification" in rel else "pysnooper2_context_extraction"
        section = state.get(section_name) or {}
        if section.get("direct_output") != rel or section.get("sha256") != sha256_path(path):
            errors.append(f"direct deterministic output custody mismatch for {rel}")

    ledger = state.get("proof_ledger") or []
    if not ledger or ledger[0].get("action") != "baseline_preservation":
        errors.append("baseline preservation must be the first proof-ledger event")
    previous_hash = None
    previous_state = None
    previous_post = canonical_sha({"campaign_id": "v2_13_minimal_forensic_context_lane", "state": "initial"})
    rejected_states: set[str] = set()
    action_index: dict[str, int] = {}
    for index, entry in enumerate(ledger):
        action_index[str(entry.get("action"))] = index
        if entry.get("entry_index") != index or entry.get("sequence_index") != index:
            errors.append(f"ledger sequence mismatch at index {index}")
        if entry.get("parent_agent_state_id") != previous_state:
            errors.append(f"ledger parent-state mismatch at index {index}")
        if entry.get("pre_state_hash") != previous_post:
            errors.append(f"ledger pre-state hash mismatch at index {index}")
        expected_post = canonical_sha(state_material(entry))
        if entry.get("post_state_hash") != expected_post:
            errors.append(f"ledger post-state hash mismatch at index {index}")
        hashes = entry.get("sha256") or {}
        if hashes.get("previous_entry_hash") != previous_hash:
            errors.append(f"ledger previous-entry hash mismatch at index {index}")
        material = json.loads(json.dumps(entry))
        material.pop("entry_hash", None)
        material.setdefault("sha256", {})["entry_hash"] = None
        expected_entry_hash = canonical_sha(material)
        if entry.get("entry_hash") != expected_entry_hash or hashes.get("entry_hash") != expected_entry_hash:
            errors.append(f"ledger entry hash mismatch at index {index}")
        if entry.get("state_status") not in {"stable", "speculative", "rejected", "rolled_back"}:
            errors.append(f"invalid state status at ledger index {index}")
        if entry.get("parent_agent_state_id") in rejected_states:
            errors.append(f"rejected state reused as parent at ledger index {index}")
        if entry.get("state_status") == "rejected":
            rejected_states.add(str(entry.get("agent_state_id")))
        if entry.get("state_status") == "rolled_back" and not entry.get("rollback_to_state_id"):
            errors.append(f"rollback state missing rollback_to_state_id at index {index}")
        for rel, expected in (hashes.get("output_hashes") or {}).items():
            candidate_path = root / rel
            if candidate_path.exists() and sha256_path(candidate_path) != expected:
                errors.append(f"ledger output hash no longer matches {rel}")
        previous_hash = expected_entry_hash
        previous_state = entry.get("agent_state_id")
        previous_post = entry.get("post_state_hash")

    if action_index.get("failed_patch_analysis", 999) >= action_index.get("patch_authorization", -1):
        errors.append("classifier did not run before patch authorization")
    if action_index.get("context_extraction", 999) >= action_index.get("patch_authorization", -1):
        errors.append("context extractor did not run before patch authorization")
    probes = state.get("pysnooper2_minimal_probes") or []
    if len(probes) > 2:
        errors.append("diagnostic probe count exceeds two")
    for probe in probes:
        if probe.get("predeclared_before_run") is not True or probe.get("mutates_source_or_tests") is not False:
            errors.append("every probe must be predeclared and non-mutating")
    patch_attempt = state.get("pysnooper2_revised_patch_attempt") or {}
    if int(patch_attempt.get("attempt_count", 0)) > 1:
        errors.append("revised patch attempt count exceeds one")
    if patch_attempt.get("authorized") is not False or patch_attempt.get("attempted") is not False:
        errors.append("fixture-materialization blocker must stop without authorizing or attempting a patch")
    if (root / "pysnooper2_revised_patch.diff").exists():
        errors.append("unexpected revised patch exists despite blocked authorization")

    final = state.get("final_result") or {}
    expected_final_state = ledger[-1].get("agent_state_id") if ledger else None
    if final.get("final_agent_state_id") != expected_final_state:
        errors.append("final classification is not linked to the final valid state")
    if final.get("pysnooper2_classification") != "blocked_fixture_materialization_incomplete":
        errors.append("final PySnooper:2 classification does not match deterministic evidence")
    if final.get("pysnooper2_scoreable") is not False or final.get("pysnooper2_positive_memory_only") is not False:
        errors.append("blocked PySnooper:2 must remain non-scoreable and non-positive")
    if final.get("diagnostic_probe_count") != len(probes):
        errors.append("final diagnostic probe count is inconsistent")
    if final.get("decision_time_outcome_overlap_count") != 0 or final.get("corruption_count") != 0:
        errors.append("decision-time overlap and corruption counts must remain zero")
    if final.get("controllergate_full_scoring") != "NOT_RUN" or final.get("full_scoring_allowed") is not False:
        errors.append("full ControllerGate scoring must remain NOT_RUN/disallowed")
    if final.get("self_maintaining_software_demonstrated") is not False:
        errors.append("self-maintaining software must not be claimed")
    if final.get("fixed_gold_future_evidence_used") is not False:
        errors.append("fixed/gold/future evidence firewall was violated")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--allow-pending", action="store_true")
    args = parser.parse_args()
    root = args.artifact_root.resolve()
    errors: list[str] = []
    for name in REQUIRED_FILES:
        path = root / name
        if not path.exists():
            errors.append(f"missing required v2.13 artifact: {path}")
        elif path.stat().st_size == 0:
            errors.append(f"empty required v2.13 artifact: {path}")
    state = load_json(root / "candidate_state_v2_13.json", errors)
    classification = load_json(root / "pysnooper2_patch_failure_classification.json", errors)
    context = load_json(root / "pysnooper2_candidate_context.json", errors)
    manifest_errors, checked = verify_manifest(root)
    errors.extend(manifest_errors)

    pending = state.get("workflow_executed") is False
    if pending:
        if not args.allow_pending:
            errors.append("pending v2.13 checkpoint requires --allow-pending")
        final = state.get("final_result") or {}
        if final.get("controllergate_full_scoring") != "NOT_RUN" or final.get("full_scoring_allowed") is not False:
            errors.append("pending checkpoint must keep full scoring NOT_RUN/disallowed")
        if final.get("self_maintaining_software_demonstrated") is not False:
            errors.append("pending checkpoint must not claim self-maintaining software")
    else:
        audit_actual(root, state, classification, context, errors)

    if errors:
        print("v2.13 minimal forensic context lane audit FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    if pending:
        print(f"v2.13 minimal forensic context lane pending audit PASS ({checked} manifest entries)")
        return 0

    state["audit_summary"] = {
        "status": "PASS",
        "report": "audit_summary_v2_13.json",
        "completed_after_runner": True,
    }
    write_json(root / "candidate_state_v2_13.json", state)
    summary = {
        "status": "PASS",
        "workflow_executed": True,
        "baseline_preservation_status": "PASS",
        "ansible2_preservation_status": "PASS",
        "ansible5_preservation_status": "PASS",
        "proof_ledger_hash_chain_status": "PASS",
        "agent_state_lineage_status": "PASS",
        "decision_time_outcome_separation_status": "PASS",
        "direct_deterministic_output_custody_status": "PASS",
        "diagnostic_probe_count": len(state.get("pysnooper2_minimal_probes") or []),
        "revised_patch_attempt_count": int((state.get("pysnooper2_revised_patch_attempt") or {}).get("attempt_count", 0)),
        "pysnooper2_final_classification": (state.get("final_result") or {}).get("pysnooper2_classification"),
        "controllergate_full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "self_maintaining_software_demonstrated": False,
    }
    write_json(root / "audit_summary_v2_13.json", summary)
    files = sorted(
        (path for path in root.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    (root / "SHA256SUMS.txt").write_text(
        "\n".join(f"{sha256_path(path)}  {path.relative_to(root).as_posix()}" for path in files) + "\n",
        encoding="utf-8",
    )
    final_manifest_errors, final_checked = verify_manifest(root)
    if final_manifest_errors:
        print("v2.13 minimal forensic context lane audit FAIL after manifest regeneration")
        for error in final_manifest_errors:
            print(f"- {error}")
        return 1
    print(f"v2.13 minimal forensic context lane audit PASS ({final_checked} manifest entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

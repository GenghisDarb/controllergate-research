from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


MUTATIONS: tuple[tuple[str, tuple[str, ...], Any, str], ...] = (
    ("M01", ("capsules", "cloudpickle_hidden_files"), 57, "CAPSULE_CLOUDPICKLE_HIDDEN_CONSERVATION"),
    ("M02", ("capsules", "freezegun_hidden_files"), 38, "CAPSULE_FREEZEGUN_HIDDEN_CONSERVATION"),
    ("M03", ("capsules", "transport_residue_count"), 1, "CAPSULE_RUNTIME_RESIDUE_PROHIBITED"),
    ("M04", ("amds", "builder_terminal_label_count"), 1, "AMDS_BUILDER_TRUTH_BLIND"),
    ("M05", ("amds", "literal_true_measurement_count"), 1, "AMDS_MEASUREMENTS_EXECUTED"),
    ("M06", ("authority", "source_token_minted_after_probe"), False, "SOURCE_TOKEN_REQUIRES_EXECUTED_PROBE"),
    ("M07", ("authority", "direct_source_contact"), False, "SOURCE_OWNERSHIP_REQUIRES_DIRECT_CONTACT"),
    ("M08", ("authority", "causal_alternatives_remaining"), 2, "CAUSAL_ELBOW_CATEGORICAL"),
    ("M09", ("authority", "candidate_bound_human_approval"), False, "LICENSE_REQUIRES_CANDIDATE_BOUND_APPROVAL"),
    ("M10", ("authority", "repair_license_use_count"), 2, "REPAIR_LICENSE_SINGLE_USE"),
    ("M11", ("amds", "source_terminal_committed_before_truth_join"), False, "SOURCE_TERMINAL_PRECEDES_TRUTH_JOIN"),
    ("M12", ("authority", "non_source_source_token_count"), 1, "NON_SOURCE_HAS_NO_SOURCE_AUTHORITY"),
    ("M13", ("lifecycles", "fresh_replay_workspace_independent"), False, "FRESH_REPLAY_WORKSPACE_INDEPENDENT"),
    ("M14", ("lifecycles", "diagnosis_provider_reused_for_replay"), True, "REPLAY_PROVIDER_INDEPENDENT"),
    ("M15", ("authority", "observed_patch_sha256"), "0" * 64, "PATCH_BYTES_MATCH_APPROVAL"),
    ("M16", ("distribution_canary", "health_event_classes"), ["registered_target", "registered_target", "distribution_integrity"], "CANARY_THREE_DISTINCT_HEALTH_EVENTS"),
    ("M17", ("distribution_canary", "negative_canary_rejected"), False, "NEGATIVE_CANARY_MUST_REJECT"),
    ("M18", ("distribution_canary", "rollback_restored_hash"), "f" * 64, "ROLLBACK_EXACT_PACKAGE_IDENTITY"),
    ("M19", ("release", "historical_increment"), 1, "HISTORICAL_NON_COUNTING_BOUNDARY"),
    ("M20", ("release", "public_status"), "PRODUCT_BETA_PASS", "PUBLIC_EXTERNAL_REVIEW_BOUNDARY"),
    ("M21", ("release", "critic_finding_count"), 0, "CRITIC_FINDING_CONSERVATION"),
    ("M22", ("release", "execution_receipt_candidate_bound"), False, "EXECUTION_RECEIPT_CONTEXT_BOUND"),
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _set(value: dict[str, Any], path: tuple[str, ...], replacement: Any) -> None:
    current: dict[str, Any] = value
    for part in path[:-1]:
        current = current[part]
    current[path[-1]] = replacement


def run_mutation_campaign(*, critic: Path, evidence: dict[str, Any], runtime: Path) -> dict[str, Any]:
    shutil = __import__("shutil")
    shutil.rmtree(runtime, ignore_errors=True)
    runtime.mkdir(parents=True)
    critic_hash = _sha(critic)
    seal_results = []
    semantic_results = []
    registry = []
    for mutation_id, path, replacement, expected_rule in MUTATIONS:
        case = runtime / mutation_id
        case.mkdir()
        bundle = case / "evidence.json"
        manifest = case / "manifest.json"
        output = case / "result.json"
        bundle.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        manifest_value = {"evidence_sha256": _sha(bundle), "critic_source_sha256": critic_hash, "criteria": "batch091-frozen-v1"}
        manifest.write_text(json.dumps(manifest_value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        mutated = copy.deepcopy(evidence); _set(mutated, path, replacement)
        bundle.write_text(json.dumps(mutated, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        seal = subprocess.run([sys.executable, str(critic), "--manifest", str(manifest), "--bundle", str(bundle), "--output", str(output)], capture_output=True, text=True, check=False)
        seal_result = json.loads(output.read_text(encoding="utf-8"))
        seal_results.append({"mutation_id": mutation_id, "executed": True, "rejected": seal.returncode == 2 and seal_result["custody_status"] == "FAIL", "rejection_class": "custody"})
        manifest_value["evidence_sha256"] = _sha(bundle)
        manifest.write_text(json.dumps(manifest_value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        semantic = subprocess.run([sys.executable, str(critic), "--manifest", str(manifest), "--bundle", str(bundle), "--output", str(output)], capture_output=True, text=True, check=False)
        semantic_result = json.loads(output.read_text(encoding="utf-8"))
        rules = [row["rule"] for row in semantic_result.get("findings", []) if isinstance(row, dict)]
        accepted_rejection = semantic.returncode == 3 and semantic_result["custody_status"] == "PASS" and expected_rule in rules
        finding = next((row for row in semantic_result.get("findings", []) if isinstance(row, dict) and row.get("rule") == expected_rule), {})
        row = {"mutation_id": mutation_id, "mutated_invariant": ".".join(path), "custody_status": semantic_result["custody_status"],
               "semantic_status": semantic_result["semantic_status"], "exact_critic_rule": expected_rule,
               "exact_blocker": finding.get("exact_blocker"), "expected_reopen_condition": finding.get("expected_reopen_condition"),
               "executed": True, "rejected_for_semantic_reason": accepted_rejection}
        semantic_results.append(row); registry.append({**row, "replacement_sha256": hashlib.sha256(json.dumps(replacement, sort_keys=True).encode()).hexdigest()})
    return {"seal_results": seal_results, "semantic_results": semantic_results, "registry": registry,
            "seal_pass": all(row["rejected"] for row in seal_results),
            "semantic_pass": all(row["rejected_for_semantic_reason"] for row in semantic_results)}

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


FORBIDDEN_KEYS = {
    "gold_patch",
    "post_repair_result",
    "post_validation_result",
    "future_revision",
    "source_owned_label",
}

SEMANTIC_MUTATION_FINDINGS = {
    "combined_scientific_responsibilities", "sealed_truth_available_before_terminal", "architecture_arm_not_executed",
    "baseline_not_executed", "critic_imports_product", "partial_tree_mutation", "main_artifact_retention_short",
    "control_not_executed", "openbb_placeholder_control", "generic_source_control", "openbb_ancestry_absent",
    "openbb_cutoff_unverified", "openbb_loopback_absent", "openbb_port_missing", "openbb_product_not_executed",
    "copied_post_manifest", "source_vault_not_reverified", "broker_record_rehashed", "local_wheel_network_enabled",
    "local_project_network_enabled", "candidate_id_parser_dispatch", "exact_node_unverified", "audioread_text_only",
    "pytest_warning_identity_missing", "poetry_name_too_broad", "boundary_summary_only", "summary_hash_verifier",
    "brot_label_receipt", "ownership_parent_reuse", "product_hash_only", "projection_side_missing",
    "modality_parent_presence", "uniform_target_probe", "probe_relation_not_executed", "generic_partition_rule",
    "execute_probe_cli_missing", "dpp14_stage_name_only", "dpp14_same_runtime_verifier", "diagnose_skips_probes",
    "diagnose_skips_experiments", "truth_join_not_separated", "source_ownership_not_stage_produced", "shallow_final_package",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def json_rows(path: Path) -> list[Any]:
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [json.loads(path.read_text(encoding="utf-8"))]


def scan_tree(root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        relative = path.relative_to(root).as_posix()
        if path.suffix not in {".json", ".jsonl"}:
            continue
        try:
            rows = json_rows(path)
        except Exception as error:
            findings.append({"finding": "RAW_EVIDENCE_PARSE_FAILURE", "path": relative, "detail": str(error)})
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            leaked = sorted(FORBIDDEN_KEYS.intersection(row))
            if leaked:
                findings.append({"finding": "FORBIDDEN_DECISION_TIME_FIELD", "path": relative, "row": index, "fields": leaked})
            if row.get("producer_execution_receipt") and row.get("verifier_execution_receipt") == row.get("producer_execution_receipt"):
                findings.append({"finding": "PRODUCER_VERIFIER_COLLAPSE", "path": relative, "row": index})
            if row.get("verifier_execution_receipt", "").startswith("graph:"):
                findings.append({"finding": "GRAPH_HASH_USED_AS_VERIFIER", "path": relative, "row": index})
            if row.get("terminal_transfer_allowed") is True:
                findings.append({"finding": "PROJECTION_TERMINAL_TRANSFER", "path": relative, "row": index})
            if row.get("patch_operation_count", 0) or row.get("historical_count_increment", 0):
                findings.append({"finding": "ORDINARY_RUN_ACTUATION_OR_COUNT", "path": relative, "row": index})
            if row.get("caller_supplied_decisive_input_count", 0):
                findings.append({"finding": "CALLER_SUPPLIED_DECISIVE_INPUT", "path": relative, "row": index})
            if row.get("configured_expected_value_injection_count", 0):
                findings.append({"finding": "CONFIGURED_VALUE_INJECTION", "path": relative, "row": index})
            if row.get("marker_only_verifier_count", 0):
                findings.append({"finding": "MARKER_ONLY_AUTHORITY", "path": relative, "row": index})
            mutation = row.get("semantic_mutation_kind")
            if mutation:
                findings.append({"finding": "RE_SIGNED_RAW_SEMANTIC_MUTATION", "path": relative, "row": index, "mutation": mutation, "registered": mutation in SEMANTIC_MUTATION_FINDINGS})
            if row.get("complete_copied_raw_evidence_tree_mutation") is False:
                findings.append({"finding": "INCOMPLETE_RAW_TREE_MUTATION", "path": relative, "row": index})
            if row.get("network_policy") not in {None, "none", "bounded_loopback_only", "bounded_acquisition"}:
                findings.append({"finding": "UNREGISTERED_NETWORK_POLICY", "path": relative, "row": index})
            if row.get("terminal_writer") and not str(row.get("terminal_writer")).endswith("ControllerAudit"):
                findings.append({"finding": "NON_CONTROLLER_AUDIT_TERMINAL_WRITER", "path": relative, "row": index})
            if row.get("legal_probe_exhaustion_receipt", {}).get("status") == "BLOCK" and row.get("terminal") in {"INSUFFICIENT_EVIDENCE", "safe_abstention_insufficient_evidence"}:
                findings.append({"finding": "UNEARNED_INSUFFICIENT_EVIDENCE", "path": relative, "row": index})
    return {
        "status": "PASS" if not findings else "BLOCK",
        "raw_file_count": len(files),
        "raw_tree_hash": hashlib.sha256("".join(f"{path.relative_to(root).as_posix()}:{digest(path)}\n" for path in files).encode()).hexdigest(),
        "findings": findings,
        "finding_count": len(findings),
        "critic_imports_controllergate": False,
        "reconstructed_domains": ["materialization", "incident products", "controls", "source/test integrity", "boundary cells", "BROT edges", "projection pairs", "modalities", "probe partitions", "causal facts", "branches", "terminals", "baselines", "source ownership", "public state"],
        "producer": "scripts.batch098_standalone_critic_v7",
        "execution_depth": "independent_standard_library_raw_tree_reconstruction",
        "authority_allowed": "internal evidence criticism",
        "authority_forbidden": ["external release approval", "patch", "repair count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-evidence", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = scan_tree(Path(args.raw_evidence))
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "finding_count": result["finding_count"]}, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Mapping

from controllergate.execution.execution_broker import execute_external_operation


FORBIDDEN_OUTPUT_KEYS = {"terminal_class", "source_owned", "repair_patch", "future_outcome", "diagnosis"}


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def execute_probe_contract(contract: Mapping[str, Any], output: str | Path) -> dict[str, Any]:
    required = {
        "probe_id", "candidate_id", "run_id", "exact_argv", "cwd_compartment",
        "single_use_nonce", "semantic_verifier_id", "predicted_neutral_partitions",
        "structured_result_schema", "probe_kind", "source_cell_or_edge_or_region",
    }
    missing = sorted(required - contract.keys())
    if missing:
        raise ValueError(f"probe contract fields missing: {','.join(missing)}")
    provider_python = str(contract.get("provider_python_executable") or sys.executable)
    argv = [provider_python if value == "{python}" else str(value) for value in contract["exact_argv"]]
    if not argv:
        raise ValueError("probe requires exact executable argv")
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=True)
    installed_import_root = Path(__file__).resolve().parents[2]
    cwd = Path(str(contract.get("cwd", installed_import_root))).resolve()
    if not cwd.is_dir():
        cwd = root
    attestation = {"status": "PASS", "attestation_hash": _hash([provider_python, contract.get("provider_identity_receipt"), sys.platform])}
    completed, operation = execute_external_operation(
        operation_type="diagnostic_probe", argv=argv, cwd=cwd, runtime_root=root,
        stage_id=str(contract["probe_id"]), candidate_id=str(contract["candidate_id"]),
        authorization_id=f"evidence-only:{_hash(contract)}", runtime_attestation=attestation,
        platform=sys.platform, runtime=str(contract.get("provider_exact_version") or sys.version), network_policy="none",
        env=dict(contract.get("environment_delta", {})), timeout=int(contract.get("timeout_seconds", 60)),
        run_id=str(contract["run_id"]), nonce=str(contract["single_use_nonce"]),
    )
    raw = completed.stdout.strip()
    try:
        structured = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        structured = {"unparsed_stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest()}
    leakage = sorted(FORBIDDEN_OUTPUT_KEYS.intersection(structured))
    schema = contract["structured_result_schema"]
    required_keys = set(schema.get("required", ()))
    status = "PASS" if completed.returncode == 0 and not leakage and required_keys.issubset(structured) else "BLOCK"
    verification = {
        "status": status,
        "semantic_verifier_id": contract["semantic_verifier_id"],
        "operation_id": operation["operation_id"],
        "operation_record_hash": operation["record_hash"],
        "probe_id": contract["probe_id"],
        "probe_kind": contract["probe_kind"],
        "subject": contract["source_cell_or_edge_or_region"],
        "structured_product_hash": _hash(structured),
        "required_keys": sorted(required_keys),
        "forbidden_output_keys_observed": leakage,
        "partition_rule": contract.get("partition_rule"),
        "partition_reconstructible": bool(contract.get("partition_rule")) and len(contract["predicted_neutral_partitions"]) >= 2,
        "authority_allowed": "verified causal fact proposal only",
        "authority_forbidden": ["terminal", "patch", "repair license", "repair count"],
    }
    verification["verification_receipt"] = f"probe-verifier:{_hash([operation['record_hash'], structured, verification])}"
    result = {"status": status, "operation": operation, "structured_product": structured, "semantic_verification": verification}
    (root / "probe_execution.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return result

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Mapping


ROLE_NAMES = (
    "source_revision",
    "source_tree",
    "test_tree",
    "provider_runtime_abi",
    "target_reproducer",
    "command",
    "runner",
    "harness",
    "incident_snapshot",
    "proof_release_parent",
)


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _require_hash(value: object, label: str) -> str:
    text = str(value or "")
    if len(text.removeprefix("sha256:")) != 64:
        raise ValueError(f"{label} is not content addressed")
    return text


def produce_source_revision(e: Mapping[str, Any]) -> dict[str, Any]:
    return {"value": e["source_commit"], "parents": [_require_hash(e["contract_hash"], "contract_hash")]}


def produce_source_tree(e: Mapping[str, Any]) -> dict[str, Any]:
    return {"value": _require_hash(e["source_manifest_hash_after"], "source tree"), "parents": [_require_hash(e["source_manifest_hash_before"], "source parent")]}


def produce_test_tree(e: Mapping[str, Any]) -> dict[str, Any]:
    return {"value": _require_hash(e["test_manifest_hash_after"], "test tree"), "parents": [_require_hash(e["test_manifest_hash_before"], "test parent")]}


def produce_provider_runtime_abi(e: Mapping[str, Any]) -> dict[str, Any]:
    observation = e["neutral_observation"]
    return {"value": observation["provider_identity"], "parents": [_require_hash(observation["producer_installed_code_hash"], "installed producer")]}


def produce_target_reproducer(e: Mapping[str, Any]) -> dict[str, Any]:
    observation = e["neutral_observation"]
    return {"value": observation["probe_id"], "parents": [_require_hash(observation["stdout_sha256"], "stdout")]}


def produce_command(e: Mapping[str, Any]) -> dict[str, Any]:
    observation = e["neutral_observation"]
    return {"value": observation["argv"], "parents": [_require_hash(observation["parent_broker_record"], "broker parent")]}


def produce_runner(e: Mapping[str, Any]) -> dict[str, Any]:
    observation = e["neutral_observation"]
    return {"value": observation["runner_identity"], "parents": [_require_hash(observation["producer_installed_code_hash"], "installed producer")]}


def produce_harness(e: Mapping[str, Any]) -> dict[str, Any]:
    observation = e["neutral_observation"]
    return {"value": observation["harness_identity"], "parents": [_require_hash(observation["stderr_sha256"], "stderr")]}


def produce_incident_snapshot(e: Mapping[str, Any]) -> dict[str, Any]:
    incident = e["typed_incident"]
    if incident.get("status") != "PASS":
        raise ValueError("incident role requires an independently verified incident")
    return {"value": incident["typed_incident_materialized"], "parents": list(incident["structured_product_parents"])}


def produce_proof_release_parent(e: Mapping[str, Any]) -> dict[str, Any]:
    return {"value": e["frame_id"], "parents": [_require_hash(e["contract_hash"], "contract parent")]}


PRODUCERS: Mapping[str, Callable[[Mapping[str, Any]], dict[str, Any]]] = {
    "source_revision": produce_source_revision,
    "source_tree": produce_source_tree,
    "test_tree": produce_test_tree,
    "provider_runtime_abi": produce_provider_runtime_abi,
    "target_reproducer": produce_target_reproducer,
    "command": produce_command,
    "runner": produce_runner,
    "harness": produce_harness,
    "incident_snapshot": produce_incident_snapshot,
    "proof_release_parent": produce_proof_release_parent,
}


@dataclass(frozen=True)
class RoleReceipt:
    receipt_id: str
    candidate_id: str
    run_id: str
    frame_id: str
    role: str
    observed_value: Any
    raw_evidence_parents: tuple[str, ...]
    producer: str
    verifier: str
    verification_receipt: str
    status: str

    def record(self) -> dict[str, Any]:
        return dict(self.__dict__)


def produce_roles(evidence: Mapping[str, Any]) -> list[dict[str, Any]]:
    produced: list[dict[str, Any]] = []
    for role in ROLE_NAMES:
        result = PRODUCERS[role](evidence)
        producer_id = f"controllergate.evidence.roles_v2.produce_{role}"
        receipt_id = f"role-producer:{_hash([evidence['candidate_id'], evidence['run_id'], evidence['frame_id'], role, result])}"
        producer_row = {
            "receipt_id": receipt_id,
            "candidate_id": evidence["candidate_id"],
            "run_id": evidence["run_id"],
            "frame_id": evidence["frame_id"],
            "role": role,
            "observed_value": result["value"],
            "raw_evidence_parents": result["parents"],
            "producer": producer_id,
            "authority_allowed": "role-specific measurement",
            "authority_forbidden": ["terminal class", "repair authority"],
        }
        produced.append(producer_row)
    return produced


def verify_role_receipts(produced: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    verified: list[dict[str, Any]] = []
    for producer_row in produced:
        role = str(producer_row["role"])
        receipt_id = str(producer_row["receipt_id"])
        verifier_payload = {
            "receipt_id": receipt_id,
            "role": role,
            "value_hash": _hash(producer_row["observed_value"]),
            "parent_hash": _hash(producer_row["raw_evidence_parents"]),
        }
        verifier_receipt = f"role-verifier:{_hash(verifier_payload)}"
        verified.append(
            {
                "verification_receipt": verifier_receipt,
                "producer_receipt": receipt_id,
                "candidate_id": producer_row["candidate_id"],
                "run_id": producer_row["run_id"],
                "frame_id": producer_row["frame_id"],
                "role": role,
                "verifier": "controllergate.evidence.roles_v2.verify_role_receipt",
                "producer_verifier_distinct": producer_row["producer"] != "controllergate.evidence.roles_v2.verify_role_receipt",
                "status": "PASS" if producer_row["raw_evidence_parents"] else "BLOCK",
                "authority_allowed": "role-receipt integrity only",
                "authority_forbidden": ["semantic role equivalence", "terminal class", "repair authority"],
            }
        )
    return verified


def execute_and_verify_roles(evidence: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Compatibility coordinator; official workflow isolates these executors."""
    produced = produce_roles(evidence)
    return produced, verify_role_receipts(produced)


def role_quality_gate(produced: list[Mapping[str, Any]], verified: list[Mapping[str, Any]], candidate_count: int) -> dict[str, Any]:
    expected = candidate_count * len(ROLE_NAMES)
    producer_ids = {row["receipt_id"] for row in produced}
    verifier_parents = {row["producer_receipt"] for row in verified if row.get("status") == "PASS"}
    pass_count = len(producer_ids.intersection(verifier_parents))
    cross_role_reuse: list[str] = []
    by_parent: dict[str, set[str]] = {}
    for row in produced:
        for parent in row["raw_evidence_parents"]:
            by_parent.setdefault(parent, set()).add(str(row["role"]))
    for parent, roles in by_parent.items():
        if len(roles) > 1:
            cross_role_reuse.append(parent)
    return {
        "status": "PASS" if len(produced) == len(verified) == pass_count == expected and not cross_role_reuse else "BLOCK",
        "expected_receipts": expected,
        "producer_receipt_count": len(produced),
        "verifier_receipt_count": len(verified),
        "verified_pass_count": pass_count,
        "unproven_cross_role_reuse": cross_role_reuse,
        "authority_allowed": "AMDS eligibility only",
        "authority_forbidden": ["terminal class", "repair authority"],
    }

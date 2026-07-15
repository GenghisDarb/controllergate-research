from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Callable


def identity(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class Compartment:
    compartment_id: str
    compartment_type: str
    accepted_schemas: frozenset[str]
    confidentiality: str


@dataclass
class CompartmentTransport:
    compartments: dict[str, Compartment]
    receipts: list[dict[str, Any]] = field(default_factory=list)

    def translocate(self, source: str, destination: str, payload: dict[str, Any], schema: str, *, hidden_files: tuple[str, ...] = ()) -> dict[str, Any]:
        if source not in self.compartments or destination not in self.compartments:
            return {"status": "BLOCK", "blocker": "compartment_identity_unknown"}
        if schema not in self.compartments[destination].accepted_schemas:
            return {"status": "BLOCK", "blocker": "destination_schema_rejected"}
        if hidden_files:
            return {"status": "BLOCK", "blocker": "hidden_file_transport_forbidden", "files": list(hidden_files)}
        record = {"status": "PASS", "source": source, "destination": destination, "payload_hash": identity(payload), "conserved": True, "schema": schema}
        record["receipt_hash"] = identity(record); self.receipts.append(record); return record


@dataclass(frozen=True)
class ScaffoldComponent:
    component_id: str
    component_hash: str
    dependencies: tuple[str, ...]
    replaceable: bool


class ScaffoldController:
    def __init__(self, components: list[ScaffoldComponent]) -> None:
        self.components = {item.component_id: item for item in components}

    def integrity(self) -> dict[str, Any]:
        missing = [(item.component_id, dependency) for item in self.components.values() for dependency in item.dependencies if dependency not in self.components]
        return {"status": "PASS" if not missing else "BLOCK", "missing_dependencies": missing, "scaffold_hash": identity([item.__dict__ for item in self.components.values()])}

    def remodel(self, component_id: str, replacement: ScaffoldComponent, *, rollback_hash: str | None) -> dict[str, Any]:
        current = self.components[component_id]
        if not current.replaceable or not rollback_hash:
            return {"status": "BLOCK", "blocker": "scaffold_remodeling_not_reversible"}
        self.components[component_id] = replacement
        return {"status": "PASS", "prior_hash": current.component_hash, "new_hash": replacement.component_hash, "rollback_hash": rollback_hash}


class ReactionTerminal(str, Enum):
    PASS = "PASS"
    BLOCK = "BLOCK"
    FAIL = "FAIL"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass(frozen=True)
class ReactionContract:
    reaction_id: str
    input_schema: frozenset[str]
    output_schema: frozenset[str]
    preconditions: tuple[str, ...]
    verifier: str
    rollback: str


class ReactionExecutor:
    def execute(self, contract: ReactionContract, inputs: dict[str, Any], preconditions: dict[str, bool], operation: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
        if set(inputs) != contract.input_schema:
            return {"status": ReactionTerminal.BLOCK.value, "blocker": "reaction_input_schema_mismatch"}
        missing = [name for name in contract.preconditions if not preconditions.get(name)]
        if missing:
            return {"status": ReactionTerminal.BLOCK.value, "blocker": "reaction_precondition_missing", "missing": missing}
        try:
            output = operation(inputs)
        except Exception as exc:
            return {"status": ReactionTerminal.ROLLED_BACK.value, "blocker": type(exc).__name__, "rollback": contract.rollback}
        if set(output) != contract.output_schema:
            return {"status": ReactionTerminal.FAIL.value, "blocker": "reaction_output_schema_mismatch"}
        return {"status": ReactionTerminal.PASS.value, "output": output, "output_hash": identity(output), "verifier": contract.verifier}


class HypothesisState(str, Enum):
    CANDIDATE = "CANDIDATE"
    SUPPORTED_INFERRED = "SUPPORTED_INFERRED"
    DEMONSTRATED_DIRECT = "DEMONSTRATED_DIRECT"
    REJECTED = "REJECTED"


def promote_hypothesis(current: HypothesisState, *, direct_support_hash: str | None, inferred_support: bool) -> HypothesisState:
    if direct_support_hash:
        return HypothesisState.DEMONSTRATED_DIRECT
    if inferred_support and current is HypothesisState.CANDIDATE:
        return HypothesisState.SUPPORTED_INFERRED
    return current


@dataclass(frozen=True)
class Contact:
    path: str
    symbol: str
    basis: str
    patchable: bool


def bounded_contact_search(candidates: list[Contact], *, maximum_contacts: int, allowed_bases: set[str]) -> dict[str, Any]:
    admitted = [item for item in candidates if item.basis in allowed_bases][:maximum_contacts]
    return {"status": "PASS", "contacts": [item.__dict__ for item in admitted], "excluded_count": len(candidates) - len(admitted), "budget": maximum_contacts, "contact_hash": identity([item.__dict__ for item in admitted])}


@dataclass(frozen=True)
class EnvironmentTranslation:
    source_runtime: str
    destination_runtime: str
    command_mapping: tuple[str, ...]
    evidence_hash: str

    def authorize(self, reproduced_at_destination: bool) -> dict[str, Any]:
        return {"status": "PASS" if reproduced_at_destination else "BLOCK", "translation_hash": identity(self.__dict__), "source_authority": False, "destination_reproduced": reproduced_at_destination}

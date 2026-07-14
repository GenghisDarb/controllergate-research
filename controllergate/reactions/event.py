from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from .catalyst import Catalyst
from .entity import Entity
from .failed_reaction import FailedReaction
from .output_token import OutputToken
from .regulation import Regulator
from .stable_identity import stable_hash


ALLOWED_OUTCOMES = {"REACTION_COMPLETED", "BLOCKED_REQUIRED_INPUT_ABSENT", "BLOCKED_CATALYST_INACTIVE",
                    "BLOCKED_POSITIVE_REGULATOR_ABSENT", "BLOCKED_NEGATIVE_REGULATOR_PRESENT",
                    "FAILED_REACTION_OUTPUT_ABSENT", "FAILED_REACTION_OUTPUT_INVALID", "NOT_RUN"}


@dataclass
class ReactionResult:
    event_record: dict[str, Any]
    output_token: OutputToken | None = None
    failure: dict[str, Any] | None = None


@dataclass
class ReactionEvent:
    event_id: str
    schema_version: int
    candidate_id: str
    event_type: str
    source_compartment: str
    destination_compartment: str
    required_input_ids: list[str]
    ordinary_input_ids: list[str]
    input_multiplicities: dict[str, int]
    catalyst: Catalyst
    positive_regulators: list[Regulator]
    negative_regulators: list[Regulator]
    normal_reference_event: str
    incident_variant_event: str
    expected_outputs: list[str]
    forbidden_outputs: list[str]
    author: str
    independent_reviewer: str
    revision_parent: str | None = None
    direct_evidence: list[str] = field(default_factory=list)
    inferred_evidence: list[str] = field(default_factory=list)

    def execute(self, entities: list[Entity], context: dict[str, Any], *, parent_token_hash: str | None = None,
                verifier: Callable[[dict[str, Any]], bool] | None = None) -> ReactionResult:
        started = datetime.now(timezone.utc).isoformat()
        by_id: dict[str, list[Entity]] = {}
        for entity in entities:
            by_id.setdefault(entity.entity_id, []).append(entity)
        missing = [item for item in self.required_input_ids
                   if len(by_id.get(item, [])) < self.input_multiplicities.get(item, 1)]
        verified_compartments = set(context.get("verified_compartments", []))
        compartments_verified = {
            "source": self.source_compartment in verified_compartments,
            "destination": self.destination_compartment in verified_compartments,
        }
        outcome = "REACTION_COMPLETED"
        if missing:
            outcome = "BLOCKED_REQUIRED_INPUT_ABSENT"
        elif not all(compartments_verified.values()):
            outcome = "FAILED_REACTION_OUTPUT_INVALID"
        elif self.catalyst.active_units < 1:
            outcome = "BLOCKED_CATALYST_INACTIVE"
        elif any(not regulator.allows(context) for regulator in self.positive_regulators):
            outcome = "BLOCKED_POSITIVE_REGULATOR_ABSENT"
        elif any(not regulator.allows(context) for regulator in self.negative_regulators):
            outcome = "BLOCKED_NEGATIVE_REGULATOR_PRESENT"
        operation: dict[str, Any] = {}
        if outcome == "REACTION_COMPLETED":
            operation = self.catalyst.execute(context)
            outputs = operation.get("outputs", {})
            if not operation.get("execution_record_id") or not operation.get("observed_sentinels"):
                outcome = "FAILED_REACTION_OUTPUT_INVALID"
            elif any(name not in outputs for name in self.expected_outputs):
                outcome = "FAILED_REACTION_OUTPUT_ABSENT"
            elif any(name in outputs for name in self.forbidden_outputs):
                outcome = "FAILED_REACTION_OUTPUT_INVALID"
            elif verifier is not None and not verifier(operation):
                outcome = "FAILED_REACTION_OUTPUT_INVALID"
        completed = datetime.now(timezone.utc).isoformat()
        base = {"stable_event_id": self.event_id, "schema_version": self.schema_version,
                "candidate_id": self.candidate_id, "event_type": self.event_type,
                "source_compartment": self.source_compartment, "destination_compartment": self.destination_compartment,
                "required_input_entities": self.required_input_ids, "ordinary_input_entities": self.ordinary_input_ids,
                "input_multiplicities": self.input_multiplicities, "catalyst_identity": self.catalyst.catalyst_id,
                "active_catalyst_units": self.catalyst.active_units,
                "positive_regulators": [r.regulator_id for r in self.positive_regulators],
                "negative_regulators": [r.regulator_id for r in self.negative_regulators],
                "normal_reference_event": self.normal_reference_event, "incident_variant_event": self.incident_variant_event,
                "compartment_verification": compartments_verified,
                "expected_outputs": self.expected_outputs, "forbidden_outputs": self.forbidden_outputs,
                "direct_evidence": self.direct_evidence, "inferred_evidence": self.inferred_evidence,
                "author": self.author, "independent_reviewer": self.independent_reviewer,
                "revision_parent": self.revision_parent, "created_timestamp": started,
                "completed_timestamp": completed, "outcome": outcome, "operation": operation}
        base["state_hash"] = stable_hash(base)
        if outcome != "REACTION_COMPLETED":
            failure = FailedReaction(self.event_id, self.candidate_id, outcome,
                                     f"{self.source_compartment}->{self.destination_compartment}",
                                     {e.entity_id: e.entity_hash for e in entities}, self.catalyst.catalyst_id,
                                     [r.regulator_id for r in self.positive_regulators + self.negative_regulators],
                                     stable_hash({"outcome": outcome, "operation": operation, "missing": missing}),
                                     "restore source and compartment identities", "supply the exact missing evidence",
                                     ",".join(missing) if missing else "new verifier-approved operation evidence").record()
            return ReactionResult(base, failure=failure)
        output_identities = {key: stable_hash(value) for key, value in operation["outputs"].items()}
        token = OutputToken(f"token:{self.event_id}", self.event_id, self.candidate_id,
                            output_identities, self.independent_reviewer, parent_token_hash)
        base["output_token_hash"] = token.token_hash
        return ReactionResult(base, output_token=token)

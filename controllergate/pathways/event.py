from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from .compartment import require_compartment
from .entity import Entity
from .regulation import Regulator
from .stable_identity import stable_identity, state_hash

DEFAULT_TIMESTAMP = "1970-01-01T00:00:00Z"


@dataclass(frozen=True)
class Event:
    event_type: str
    schema_type: str
    compartment: str
    input_entities: tuple[Entity, ...] = ()
    required_input_entities: tuple[Entity, ...] = ()
    catalyst_or_executor: Entity | None = None
    positive_regulators: tuple[Regulator, ...] = ()
    negative_regulators: tuple[Regulator, ...] = ()
    output_entities: tuple[Entity, ...] = ()
    expected_output: Any = None
    observed_output: Any = None
    normal_reference_event: str | None = None
    incident_variant_event: str | None = None
    knowledge_status: Literal["DIRECTLY_OBSERVED", "STRUCTURALLY_PROJECTED", "INFERRED_FROM_PATHWAY"] = "DIRECTLY_OBSERVED"
    inferred_from_links: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()
    author_record: str = "controllergate"
    reviewer_record: str = "independent_audit"
    revision_record: str = "initial"
    created_timestamp: str = DEFAULT_TIMESTAMP
    modified_timestamp: str = DEFAULT_TIMESTAMP
    event_version: int = 1

    @property
    def event_id(self) -> str:
        return stable_identity("event", {
            "event_type": self.event_type,
            "schema_type": self.schema_type,
            "compartment": require_compartment(self.compartment),
            "required_inputs": [item.entity_id for item in self.required_input_entities],
            "executor": self.catalyst_or_executor.entity_id if self.catalyst_or_executor else None,
            "outputs": [item.entity_id for item in self.output_entities],
            "normal": self.normal_reference_event,
            "incident": self.incident_variant_event,
        }, version=self.event_version)

    def to_record(self) -> dict[str, Any]:
        record = {
            "event_id": self.event_id,
            "event_version": self.event_version,
            "event_type": self.event_type,
            "schema_type": self.schema_type,
            "compartment": require_compartment(self.compartment),
            "input_entities": [item.to_record() for item in self.input_entities],
            "required_input_entities": [item.to_record() for item in self.required_input_entities],
            "catalyst_or_executor": self.catalyst_or_executor.to_record() if self.catalyst_or_executor else None,
            "positive_regulators": [item.to_record() for item in self.positive_regulators],
            "negative_regulators": [item.to_record() for item in self.negative_regulators],
            "output_entities": [item.to_record() for item in self.output_entities],
            "expected_output": self.expected_output,
            "observed_output": self.observed_output,
            "normal_reference_event": self.normal_reference_event,
            "incident_variant_event": self.incident_variant_event,
            "knowledge_status": self.knowledge_status,
            "inferred_from_links": list(self.inferred_from_links),
            "evidence_references": list(self.evidence_references),
            "author_record": self.author_record,
            "reviewer_record": self.reviewer_record,
            "revision_record": self.revision_record,
            "created_timestamp": self.created_timestamp,
            "modified_timestamp": self.modified_timestamp,
        }
        record["state_hash"] = state_hash(record)
        return record

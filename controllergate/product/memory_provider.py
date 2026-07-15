from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Protocol


class MemoryResultType(str, Enum):
    VERBATIM_SOURCE_RECORD = "VERBATIM_SOURCE_RECORD"
    TEMPORAL_RELATION = "TEMPORAL_RELATION"
    SEMANTIC_HIT = "SEMANTIC_HIT"
    LEXICAL_HIT = "LEXICAL_HIT"
    EXPLICIT_TUNNEL = "EXPLICIT_TUNNEL"


class MemoryProvider(Protocol):
    def health(self) -> dict[str, Any]: ...
    def write_proposal(self, namespace: str, record: dict[str, Any]) -> dict[str, Any]: ...
    def write(self, namespace: str, proposal: dict[str, Any], authorization: str) -> dict[str, Any]: ...
    def recall(self, namespace: str, query: str) -> list[dict[str, Any]]: ...
    def invalidate(self, namespace: str, record_hash: str, authorization: str) -> dict[str, Any]: ...
    def timeline(self, namespace: str) -> list[dict[str, Any]]: ...
    def namespaces(self) -> list[str]: ...
    def shutdown(self) -> dict[str, Any]: ...


@dataclass
class DisabledMemoryProvider:
    reason: str = "optional_provider_disabled_by_default"

    def health(self) -> dict[str, Any]: return {"status": "UNAVAILABLE", "reason": self.reason, "canonical_engine_available": True}
    def write_proposal(self, namespace: str, record: dict[str, Any]) -> dict[str, Any]: return {"status": "REJECTED", "reason": self.reason, "authority": "NONE"}
    def write(self, namespace: str, proposal: dict[str, Any], authorization: str) -> dict[str, Any]: return {"status": "REJECTED", "reason": self.reason}
    def recall(self, namespace: str, query: str) -> list[dict[str, Any]]: return []
    def invalidate(self, namespace: str, record_hash: str, authorization: str) -> dict[str, Any]: return {"status": "REJECTED", "reason": self.reason}
    def timeline(self, namespace: str) -> list[dict[str, Any]]: return []
    def namespaces(self) -> list[str]: return []
    def shutdown(self) -> dict[str, Any]: return {"status": "STOPPED", "state_changed": False}


@dataclass
class InMemoryAdvisoryProvider:
    records: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    active: bool = True

    def health(self) -> dict[str, Any]: return {"status": "PASS" if self.active else "STOPPED", "authority": "ADVISORY_ONLY"}
    def write_proposal(self, namespace: str, record: dict[str, Any]) -> dict[str, Any]:
        text = json.dumps(record, sort_keys=True).lower()
        if any(marker in text for marker in ("ignore previous", "system prompt", "authorize patch", "repair_license")):
            return {"status": "REJECTED", "reason": "prompt_injection_or_authority_escalation"}
        proposal = {"namespace": namespace, "record": record, "proposal_hash": sha256((namespace + text).encode()).hexdigest(), "authority": "ADVISORY_ONLY"}
        return {"status": "PROPOSED", "proposal": proposal}
    def write(self, namespace: str, proposal: dict[str, Any], authorization: str) -> dict[str, Any]:
        if not authorization or proposal.get("namespace") != namespace:
            return {"status": "REJECTED", "reason": "memory_write_authorization_or_namespace_invalid"}
        value = {**proposal, "record_hash": sha256(json.dumps(proposal, sort_keys=True).encode()).hexdigest(), "result_type": MemoryResultType.VERBATIM_SOURCE_RECORD.value, "direct_evidence": False}
        self.records.setdefault(namespace, []).append(value); return {"status": "STORED", "record_hash": value["record_hash"]}
    def recall(self, namespace: str, query: str) -> list[dict[str, Any]]:
        return [{**record, "result_type": MemoryResultType.LEXICAL_HIT.value, "direct_evidence": False} for record in self.records.get(namespace, []) if query.lower() in json.dumps(record).lower()]
    def invalidate(self, namespace: str, record_hash: str, authorization: str) -> dict[str, Any]:
        if not authorization: return {"status": "REJECTED"}
        before = len(self.records.get(namespace, [])); self.records[namespace] = [row for row in self.records.get(namespace, []) if row["record_hash"] != record_hash]
        return {"status": "INVALIDATED" if len(self.records[namespace]) < before else "NOT_FOUND"}
    def timeline(self, namespace: str) -> list[dict[str, Any]]: return list(self.records.get(namespace, []))
    def namespaces(self) -> list[str]: return sorted(self.records)
    def shutdown(self) -> dict[str, Any]: self.active = False; return {"status": "STOPPED", "state_changed": True}

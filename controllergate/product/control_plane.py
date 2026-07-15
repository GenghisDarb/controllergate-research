from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable

from controllergate.reactions.stable_identity import stable_hash


@dataclass(frozen=True)
class BoundEnvelope:
    envelope_id: str
    candidate_id: str
    run_id: str
    frame_hash: str
    payload_hash: str
    schema: str
    source_compartment: str
    destination_compartment: str
    authority: str = "NONE"

    @property
    def envelope_hash(self) -> str:
        return stable_hash(asdict(self))


def normalize_input_bundle(bundle: dict[str, Any], envelope: BoundEnvelope) -> list[dict[str, Any]]:
    if stable_hash(bundle) != envelope.payload_hash:
        raise ValueError("input bundle hash does not match its bound envelope")
    units = []
    for key, value in sorted(bundle.items()):
        unit = {"unit_id": f"{envelope.envelope_id}:{key}", "key": key, "value_type": type(value).__name__,
                "value_hash": stable_hash(value), "envelope_hash": envelope.envelope_hash,
                "operational_authority": False}
        unit["unit_hash"] = stable_hash(unit); units.append(unit)
    return units


class PlanState(str, Enum):
    GENERATED_UNTRUSTED = "GENERATED_UNTRUSTED"
    NORMALIZED = "NORMALIZED"
    SEMANTICALLY_VALIDATED = "SEMANTICALLY_VALIDATED"
    AUTHORIZED = "AUTHORIZED"
    ACTIVE = "ACTIVE"
    TERMINATED = "TERMINATED"
    REJECTED = "REJECTED"


@dataclass
class ExecutionPlan:
    plan_id: str
    provenance_hash: str
    steps: tuple[dict[str, Any], ...]
    state: PlanState = PlanState.GENERATED_UNTRUSTED
    authorization_hash: str | None = None

    @property
    def plan_hash(self) -> str:
        return stable_hash({"plan_id": self.plan_id, "provenance": self.provenance_hash,
                            "steps": self.steps, "state": self.state.value, "authorization": self.authorization_hash})


class PlanMaturationService:
    def normalize(self, plan: ExecutionPlan) -> ExecutionPlan:
        if plan.state is not PlanState.GENERATED_UNTRUSTED:
            raise ValueError("only generated plans can enter normalization")
        if not plan.steps or any("operation" not in step for step in plan.steps):
            plan.state = PlanState.REJECTED
        else:
            plan.state = PlanState.NORMALIZED
        return plan

    def validate(self, plan: ExecutionPlan, validator: Callable[[dict[str, Any]], bool]) -> ExecutionPlan:
        if plan.state is not PlanState.NORMALIZED or not all(validator(step) for step in plan.steps):
            plan.state = PlanState.REJECTED
        else:
            plan.state = PlanState.SEMANTICALLY_VALIDATED
        return plan

    def authorize(self, plan: ExecutionPlan, authorization_hash: str) -> ExecutionPlan:
        if plan.state is not PlanState.SEMANTICALLY_VALIDATED or not authorization_hash:
            raise ValueError("unvalidated plan cannot be authorized")
        plan.authorization_hash = authorization_hash; plan.state = PlanState.AUTHORIZED; return plan

    def activate(self, plan: ExecutionPlan) -> ExecutionPlan:
        if plan.state is not PlanState.AUTHORIZED:
            raise ValueError("raw or unlicensed plan execution prohibited")
        plan.state = PlanState.ACTIVE; return plan


@dataclass(frozen=True)
class SensorContract:
    sensor_id: str
    input_schema: str
    calibration_hash: str
    transducer: str
    verifier: str
    minimum: float
    maximum: float


class SensorPlane:
    def observe(self, contract: SensorContract, raw_value: float, *, calibration_hash: str) -> dict[str, Any]:
        errors = []
        if calibration_hash != contract.calibration_hash:
            errors.append("sensor_calibration_mismatch")
        if not contract.minimum <= raw_value <= contract.maximum:
            errors.append("sensor_saturation")
        fact = {"sensor_id": contract.sensor_id, "raw_value": raw_value, "normalized_code": round(raw_value, 6),
                "transducer": contract.transducer, "verifier": contract.verifier}
        fact["fact_hash"] = stable_hash(fact)
        return {"status": "DIRECT_VERIFIED" if not errors else "REJECTED_UNUSABLE", "errors": errors, "fact": fact}


@dataclass(frozen=True)
class SignalRoute:
    route_id: str
    receptor: str
    effector: str
    maximum_depth: int
    maximum_fanout: int
    ttl: int
    inhibitor: str | None = None


class SignalRouter:
    def __init__(self, routes: list[SignalRoute]) -> None:
        self.routes = {route.route_id: route for route in routes}

    def route(self, route_id: str, signal: dict[str, Any], *, receptor: str, depth: int = 0,
              fanout: int = 1, inhibitors: set[str] | None = None) -> dict[str, Any]:
        route = self.routes[route_id]; inhibitors = inhibitors or set()
        errors = []
        if receptor != route.receptor: errors.append("wrong_receptor")
        if depth > route.maximum_depth: errors.append("signal_depth_exceeded")
        if fanout > route.maximum_fanout: errors.append("signal_fanout_exceeded")
        if signal.get("ttl", route.ttl) <= 0: errors.append("signal_expired")
        if route.inhibitor and route.inhibitor in inhibitors: errors.append("signal_inhibited")
        return {"status": "DELIVERED" if not errors else "BLOCK", "errors": errors,
                "route_id": route_id, "signal_hash": stable_hash(signal), "effect_authority": not errors}


class TransportService:
    def __init__(self) -> None:
        self.delivered: set[str] = set(); self.acknowledged: set[str] = set(); self.dead_letters: list[dict[str, Any]] = []

    def deliver(self, envelope: BoundEnvelope, *, destination: str, destination_verified: bool) -> dict[str, Any]:
        errors = []
        if destination != envelope.destination_compartment: errors.append("wrong_destination")
        if not destination_verified: errors.append("destination_unverified")
        if envelope.envelope_hash in self.delivered: errors.append("duplicate_delivery")
        if errors:
            record = {"envelope_hash": envelope.envelope_hash, "errors": errors}; self.dead_letters.append(record)
            return {"status": "DEAD_LETTER", **record, "activation": False}
        self.delivered.add(envelope.envelope_hash)
        return {"status": "DESTINATION_VERIFIED", "envelope_hash": envelope.envelope_hash, "activation": False}

    def activate(self, envelope: BoundEnvelope, receipt: dict[str, Any]) -> dict[str, Any]:
        if receipt.get("status") != "DESTINATION_VERIFIED":
            raise ValueError("payload cannot activate before destination verification")
        return {"status": "ACTIVATED", "envelope_hash": envelope.envelope_hash}

    def acknowledge(self, envelope_hash: str) -> None:
        if envelope_hash not in self.delivered: raise ValueError("cannot acknowledge undelivered payload")
        self.acknowledged.add(envelope_hash)


class OperationalMode(str, Enum):
    NORMAL = "NORMAL"
    DEGRADED = "DEGRADED"
    QUIESCENT = "QUIESCENT"
    EMERGENCY = "EMERGENCY"


@dataclass
class HomeostasisController:
    enter_threshold: float
    exit_threshold: float
    mode: OperationalMode = OperationalMode.NORMAL
    transitions: list[dict[str, Any]] = field(default_factory=list)

    def observe(self, stress: float) -> OperationalMode:
        previous = self.mode
        if stress >= self.enter_threshold: self.mode = OperationalMode.DEGRADED
        elif self.mode is OperationalMode.DEGRADED and stress <= self.exit_threshold: self.mode = OperationalMode.NORMAL
        if self.mode != previous:
            self.transitions.append({"from": previous.value, "to": self.mode.value, "stress": stress})
        return self.mode


PROTECTED_RETENTION_CLASSES = {"active_evidence", "historical_evidence", "sealed_truth", "proof_record", "release_decision", "operator_data"}


class CleanupController:
    def select(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        selected = [row for row in records if row.get("retention_class") not in PROTECTED_RETENTION_CLASSES and not row.get("active_reference")]
        protected = [row for row in records if row not in selected]
        return {"selected": selected, "protected": protected, "status": "PASS"}

    def execute(self, selection: dict[str, Any]) -> list[dict[str, Any]]:
        return [{"entity_id": row["entity_id"], "action": "REMOVED_WITH_RECEIPT", "source_hash": row["hash"],
                 "receipt_hash": stable_hash(row)} for row in selection["selected"]]


class TerminationController:
    def terminate(self, *, plan_id: str, evidence_sealed: bool, leases_active: int,
                  transaction_ambiguous: bool, patch_half_applied: bool, public_state_consistent: bool) -> dict[str, Any]:
        errors = []
        if not evidence_sealed: errors.append("evidence_not_sealed")
        if leases_active: errors.append("active_lease_remains")
        if transaction_ambiguous: errors.append("ambiguous_transaction")
        if patch_half_applied: errors.append("half_applied_patch")
        if not public_state_consistent: errors.append("public_state_inconsistent")
        return {"status": "TERMINATED" if not errors else "BLOCK", "errors": errors, "plan_id": plan_id}


class AdvisoryMemoryGateway:
    FORBIDDEN_AUTHORITY = {"causal_terminal", "source_ownership", "repair_license", "repair_count", "deployment", "release", "public_write"}

    def __init__(self) -> None:
        self.namespaces: dict[str, list[dict[str, Any]]] = {}

    def write_proposal(self, namespace: str, record: dict[str, Any]) -> dict[str, Any]:
        if any(key in record for key in self.FORBIDDEN_AUTHORITY):
            return {"status": "REJECTED", "reason": "memory_authority_escalation"}
        if any(marker in str(record).lower() for marker in ("ignore previous", "system prompt", "authorize patch")):
            return {"status": "REJECTED", "reason": "prompt_injection"}
        value = {**record, "record_hash": stable_hash(record), "authority": "ADVISORY_ONLY"}
        self.namespaces.setdefault(namespace, []).append(value)
        return {"status": "STORED_ADVISORY", "record": value}

    def recall(self, namespace: str) -> list[dict[str, Any]]:
        return list(self.namespaces.get(namespace, ()))

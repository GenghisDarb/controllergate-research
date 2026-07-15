from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


SLOT_STATES = (
    "MATERIALIZED", "INSTALLED", "INACTIVE_VERIFIED", "ACTIVE", "HEALTHY", "UNHEALTHY",
    "ROLLBACK_READY", "ROLLED_BACK", "RETIRED", "CLEANED",
)


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _tree_hash(root: Path) -> str:
    rows = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rows.append([path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()])
    return _hash(rows)


@dataclass
class BrokerBackedSlotManager:
    runtime_root: Path
    deployment_id: str
    operations: list[dict[str, Any]] = field(default_factory=list)
    transitions: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.root = self.runtime_root / "deployment-slots" / self.deployment_id
        self.slots = self.root / "slots"
        self.active_pointer = self.root / "active-slot.json"
        self.slots.mkdir(parents=True, exist_ok=True)

    def _record(self, operation_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        parent = self.operations[-1]["record_hash"] if self.operations else "0" * 64
        record = {"adapter": "controllergate.deployment.slot_manager.BrokerBackedSlotManager", "operation_type": operation_type, "deployment_id": self.deployment_id, "ledger_parent_hash": parent, **payload}
        record["record_hash"] = _hash(record)
        self.operations.append(record)
        return record

    def materialize(self, *, slot_id: str, package_source: Path, package_hash: str, source_hash: str,
                    provider_identity: str, interpreter_identity: str, parent_slot: str | None,
                    rollback_slot: str | None, health_contract: dict[str, Any]) -> dict[str, Any]:
        target = self.slots / slot_id
        if target.exists():
            raise ValueError("slot already exists")
        shutil.copytree(package_source, target)
        observed = _tree_hash(target)
        manifest = {
            "slot_id": slot_id, "slot_path": str(target.resolve()), "package_hash": package_hash,
            "source_hash": source_hash, "provider_identity": provider_identity, "interpreter_identity": interpreter_identity,
            "tree_hash": observed, "health_contract": health_contract, "parent_slot": parent_slot,
            "rollback_slot": rollback_slot, "state": "INACTIVE_VERIFIED",
        }
        (target / "slot-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        self._record("canary_installation", {"slot_id": slot_id, "slot_tree_hash": observed, "state": "INACTIVE_VERIFIED"})
        return manifest

    def active(self) -> dict[str, Any] | None:
        return json.loads(self.active_pointer.read_text(encoding="utf-8")) if self.active_pointer.is_file() else None

    def switch(self, slot_id: str, *, authorization_id: str) -> dict[str, Any]:
        target = self.slots / slot_id
        if not (target / "slot-manifest.json").is_file():
            raise ValueError("materialized verified slot required")
        previous = self.active()
        generation = 1 if previous is None else int(previous["generation"]) + 1
        pointer = {"slot_id": slot_id, "slot_path": str(target.resolve()), "generation": generation, "authorization_id": authorization_id}
        temporary = self.active_pointer.with_suffix(f".tmp-{os.getpid()}")
        temporary.write_text(json.dumps(pointer, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        os.replace(temporary, self.active_pointer)
        transition = {"from_slot": previous["slot_id"] if previous else None, "to_slot": slot_id, "generation": generation, "state": "ACTIVE", "atomic_mechanism": "os.replace_pointer_file", "authorization_id": authorization_id}
        transition["transition_hash"] = _hash(transition)
        self.transitions.append(transition)
        self._record("local_actuation", transition)
        return transition

    def prove_active_content(self, relative_path: str) -> dict[str, Any]:
        pointer = self.active()
        if pointer is None:
            raise ValueError("no active slot")
        path = Path(pointer["slot_path"]) / relative_path
        if not path.is_file():
            raise ValueError("active slot consumer target missing")
        proof = {"slot_id": pointer["slot_id"], "generation": pointer["generation"], "resolved_path": str(path.resolve()), "content_sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "active_pointer_sha256": hashlib.sha256(self.active_pointer.read_bytes()).hexdigest()}
        proof["proof_hash"] = _hash(proof)
        self._record("canary_execution", proof)
        return proof

    def health(self, *, event_id: str, relative_path: str, expected_sha256: str) -> dict[str, Any]:
        proof = self.prove_active_content(relative_path)
        event = {"event_id": event_id, "slot_id": proof["slot_id"], "generation": proof["generation"], "status": "PASS" if proof["content_sha256"] == expected_sha256 else "FAIL", "proof_hash": proof["proof_hash"]}
        event["event_hash"] = _hash(event)
        self._record("health_observation", event)
        return event

    def rollback(self, original_slot: str, *, authorization_id: str) -> dict[str, Any]:
        transition = self.switch(original_slot, authorization_id=authorization_id)
        transition = {**transition, "state": "ROLLED_BACK"}
        self._record("rollback", transition)
        return transition

    def cleanup(self, slot_id: str) -> dict[str, Any]:
        active = self.active()
        if active and active["slot_id"] == slot_id:
            raise ValueError("active slot cannot be cleaned")
        target = (self.slots / slot_id).resolve()
        if self.slots.resolve() not in target.parents:
            raise ValueError("slot cleanup escaped deployment root")
        existed = target.exists()
        if existed:
            shutil.rmtree(target)
        receipt = {"slot_id": slot_id, "state": "CLEANED", "existed": existed, "path": str(target)}
        receipt["receipt_hash"] = _hash(receipt)
        self._record("cleanup", receipt)
        return receipt

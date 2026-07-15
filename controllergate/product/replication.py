from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from typing import Any


def _hash(value: Any) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass(frozen=True)
class FrozenOrigin:
    origin_id: str
    source_hash: str
    epoch: int
    license_hash: str


@dataclass
class ReplicationCoordinator:
    fired: set[tuple[str, int]] = field(default_factory=set)
    checkpoints: dict[str, dict[str, Any]] = field(default_factory=dict)

    def freeze(self, source: bytes, epoch: int, license_hash: str) -> FrozenOrigin:
        if epoch < 0 or not license_hash:
            raise ValueError("replication_origin_contract_invalid")
        source_hash = sha256(source).hexdigest()
        return FrozenOrigin(_hash({"source": source_hash, "epoch": epoch}), source_hash, epoch, license_hash)

    def replicate(self, origin: FrozenOrigin, source: bytes, destinations: tuple[str, ...], *, segment_size: int = 64) -> dict[str, Any]:
        key = (origin.origin_id, origin.epoch)
        if key in self.fired:
            return {"status": "BLOCK", "blocker": "duplicate_origin_firing", "origin_id": origin.origin_id}
        if sha256(source).hexdigest() != origin.source_hash:
            return {"status": "BLOCK", "blocker": "source_mutation_during_replication", "origin_id": origin.origin_id}
        if len(set(destinations)) != len(destinations) or not destinations:
            return {"status": "BLOCK", "blocker": "replication_destination_identity_invalid"}
        self.fired.add(key)
        segments = [source[index:index + segment_size] for index in range(0, len(source), segment_size)] or [b""]
        segment_hashes = [sha256(segment).hexdigest() for segment in segments]
        receipt = {"status": "PASS", "origin_id": origin.origin_id, "source_hash": origin.source_hash, "segment_hashes": segment_hashes, "destinations": {d: origin.source_hash for d in destinations}, "post_replication_lock": True}
        self.checkpoints[origin.origin_id] = receipt
        return receipt

    def stall(self, origin_id: str, completed_segments: int) -> dict[str, Any]:
        checkpoint = {"status": "STALLED", "origin_id": origin_id, "completed_segments": completed_segments, "checkpoint_hash": _hash({"origin": origin_id, "completed": completed_segments})}
        self.checkpoints[origin_id] = checkpoint
        return checkpoint

    def resume(self, origin_id: str, checkpoint_hash: str) -> dict[str, Any]:
        checkpoint = self.checkpoints.get(origin_id)
        if not checkpoint or checkpoint.get("checkpoint_hash") != checkpoint_hash:
            return {"status": "BLOCK", "blocker": "replication_checkpoint_invalid"}
        return {"status": "RESUMED", "origin_id": origin_id, "from_checkpoint": checkpoint_hash}

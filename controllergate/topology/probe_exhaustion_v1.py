from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping


BLOCKED_CLASSES = {
    "BLOCKED_PRECONDITION", "BLOCKED_AUTHORITY", "BLOCKED_RESOURCE", "BLOCKED_RISK", "BLOCKED_NETWORK",
    "BLOCKED_NO_SEMANTIC_VERIFIER", "BLOCKED_REDUNDANT", "BLOCKED_NOGOOD", "BLOCKED_TRUTH_OR_FUTURE_LEAKAGE",
}
ACCOUNTED_CLASSES = BLOCKED_CLASSES | {"EXECUTED"}


def _hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(frozen=True)
class LegalProbeExhaustionReceipt:
    candidate_id: str
    run_id: str
    frame_hash: str
    unresolved_cell_ids: tuple[str, ...]
    unresolved_region_ids: tuple[str, ...]
    probe_inventory: tuple[Mapping[str, Any], ...]
    budget_used: Mapping[str, int]
    budget_remaining: Mapping[str, int]
    why_remaining_budget_cannot_execute_a_legal_discriminating_probe: str
    legal_probe_space_fully_accounted: bool
    redundancy_complete: bool
    nogood_complete: bool
    receipt_id: str

    def record(self) -> dict[str, Any]:
        return asdict(self)


def produce_exhaustion_receipt(
    *, candidate_id: str, run_id: str, frame_hash: str, unresolved_cell_ids: Iterable[str], unresolved_region_ids: Iterable[str],
    probe_inventory: Iterable[Mapping[str, Any]], budget_used: Mapping[str, int], budget_remaining: Mapping[str, int],
    why_remaining_budget_cannot_execute_a_legal_discriminating_probe: str, enumeration_complete: bool,
    redundancy_complete: bool, nogood_complete: bool,
) -> LegalProbeExhaustionReceipt:
    cells = tuple(sorted(set(unresolved_cell_ids))); regions = tuple(sorted(set(unresolved_region_ids))); probes = tuple(dict(row) for row in probe_inventory)
    if not enumeration_complete or not (cells or regions):
        raise ValueError("empty probe list is not legal-probe exhaustion without complete unresolved-board enumeration")
    for probe in probes:
        if probe.get("classification") not in ACCOUNTED_CLASSES or not probe.get("evidence_reason"):
            raise ValueError("every legal probe requires an allowed classification and exact evidence-derived reason")
        if probe.get("classification") == "EXECUTED" and probe.get("admissible_unspent"):
            raise ValueError("executed probe cannot be unspent")
    remaining = [row for row in probes if row.get("admissible_unspent") and row.get("discriminates_at_least_two")]
    if remaining:
        raise ValueError("admissible discriminating probe remains")
    if not why_remaining_budget_cannot_execute_a_legal_discriminating_probe:
        raise ValueError("remaining budget disposition is required")
    if not redundancy_complete or not nogood_complete:
        raise ValueError("redundancy and nogood accounting must be complete")
    payload = [candidate_id, run_id, frame_hash, cells, regions, probes, budget_used, budget_remaining]
    return LegalProbeExhaustionReceipt(candidate_id, run_id, frame_hash, cells, regions, probes, dict(budget_used), dict(budget_remaining), why_remaining_budget_cannot_execute_a_legal_discriminating_probe, True, True, True, f"probe-exhaustion:{_hash(payload)}")


def verify_exhaustion_receipt(receipt: LegalProbeExhaustionReceipt, frozen_frame: Mapping[str, Any]) -> dict[str, Any]:
    frame_probes = {row["probe_id"] for row in frozen_frame.get("probes", [])}
    inventoried = {str(row["probe_id"]) for row in receipt.probe_inventory}
    omitted = sorted(frame_probes.difference(inventoried))
    remaining = [row["probe_id"] for row in receipt.probe_inventory if row.get("admissible_unspent") and row.get("discriminates_at_least_two")]
    status = "PASS" if receipt.frame_hash == frozen_frame.get("frame_hash") and not omitted and not remaining and receipt.legal_probe_space_fully_accounted else "BLOCK"
    return {"status": status, "receipt_id": receipt.receipt_id, "silently_omitted_legal_probes": omitted, "remaining_discriminating_probes": remaining, "independent_verifier": "controllergate.topology.probe_exhaustion_v1.verify_exhaustion_receipt", "earned_insufficient_evidence": status == "PASS"}

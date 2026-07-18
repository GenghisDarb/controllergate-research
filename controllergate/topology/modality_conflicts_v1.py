from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Iterable, Mapping


MODALITIES = ("STRUCTURAL", "TEMPORAL", "EXECUTION_BOUNDARY", "PROVENANCE_ANOMALY", "PRODUCT_CLAIM")


def identity(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


@dataclass(frozen=True)
class ModalityProposal:
    candidate_id: str
    modality: str
    subject_cell_id: str
    state_proposal: str
    raw_observation_parents: tuple[str, ...]
    producer_receipt: str
    verifier_receipt: str
    known_blind_spots: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.modality not in MODALITIES: raise ValueError("unknown modality")
        if not self.raw_observation_parents or not self.producer_receipt or not self.verifier_receipt: raise ValueError("modality requires executed evidence")
        if self.producer_receipt == self.verifier_receipt: raise ValueError("modality producer/verifier collapse")


def reconcile_modalities(proposals: Iterable[ModalityProposal], legal_probe_ids: Iterable[str]) -> dict[str, Any]:
    rows = list(proposals); grouped: dict[str, list[ModalityProposal]] = {}
    for row in rows: grouped.setdefault(row.subject_cell_id, []).append(row)
    conflicts = []
    for subject, values in grouped.items():
        states = sorted(set(row.state_proposal for row in values))
        if len(states) > 1:
            probes = list(legal_probe_ids)
            conflicts.append({"conflict_cell_id": f"modality-conflict:{identity([subject, states, [row.raw_observation_parents for row in values]])}", "subject_cell_id": subject, "proposals": [row.__dict__ for row in values], "state": "UNRESOLVED", "discrepancy_probe_id": probes[0] if probes else None, "safe_abstention_required": not probes})
    return {"status": "PASS", "observation_count": len(rows), "verifier_count": len(rows), "conflict_count": len(conflicts), "conflicts": conflicts, "uncalibrated_averaging_count": 0, "majority_vote_resolution_count": 0}

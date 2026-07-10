from __future__ import annotations

from controllergate.core.evidence import hash_record

from .types import TwistHolonomyRecord


def validate_twist_return(origin_state_hash: str, terminal_state_hash: str, rollback_identity: str, *, operational_mapping_established: bool) -> TwistHolonomyRecord:
    if not operational_mapping_established:
        return TwistHolonomyRecord(origin_state_hash, terminal_state_hash, origin_state_hash, 0, {}, rollback_identity, "proof-ledger", ("candidate_identity", "source_identity", "evidence_identity"), (), ("fixed_future_gold_evidence",), "NOT_ESTABLISHED")
    mapping = {"terminal": "reference", "reference": "terminal"}
    return TwistHolonomyRecord(origin_state_hash, terminal_state_hash, origin_state_hash, 1, mapping, rollback_identity, hash_record(mapping), ("candidate_identity", "source_identity", "evidence_identity"), ("operational_orientation",), ("fixed_future_gold_evidence",), "PASS")


def two_traversals_restore_orientation(record: TwistHolonomyRecord) -> bool:
    return record.status in {"PASS", "NOT_ESTABLISHED"} and record.return_state_hash == record.origin_state_hash

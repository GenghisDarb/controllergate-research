from __future__ import annotations

from controllergate.core.evidence import hash_record

from .null_models import parent_specific_nulls
from .types import ContactLedger14, TldLadderRecord, TldMetricRecord, TldNullRecord


def build_ladder(ledger: ContactLedger14, seed: int = 0) -> TldLadderRecord:
    omega = tuple(item.evidence_status for item in ledger.contacts)
    return TldLadderRecord(f"ladder:{ledger.candidate_id}", ledger.candidate_id, "observed", None, omega, "canonical_fourteen_contact_order", False, True, seed, ledger.ledger_hash, 14, 1, "outcome-blind retrospective shadow ladder")


def run_shadow_assay(ledgers: tuple[ContactLedger14, ...]) -> tuple[tuple[TldLadderRecord, ...], tuple[TldNullRecord, ...], tuple[TldMetricRecord, ...]]:
    parents = tuple(build_ladder(item, index) for index, item in enumerate(ledgers))
    nulls = tuple(child for parent in parents for child in parent_specific_nulls(parent))
    metrics = tuple(TldMetricRecord(parent.ladder_id, "NOT_ESTABLISHED", "NOT_ESTABLISHED", "NOT_ESTABLISHED", "NOT_ESTABLISHED", "NOT_ESTABLISHED", "NOT_ESTABLISHED") for parent in parents)
    return parents, nulls, metrics

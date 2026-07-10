from __future__ import annotations

from .contact_ledger import CONTACT_ROLES
from .types import ProofMatrix196, ProofObligationCell


def build_proof_matrix(*, post_action: bool = False) -> ProofMatrix196:
    cells = tuple(
        ProofObligationCell(
            source_id, target_id, "candidate_source_evidence_identity_preserved", "verified_source_only_delta_after_authorization",
            "test_fixture_harness_or_evidence_identity_mutation", "contact_ledger_pre_state", "contact_ledger_post_state",
            "independent_hash_and_interlock_verification", "NOT_RUN" if not post_action else "BLOCK",
            "post_action_evidence_not_available", "authorized_action_then_duplicate_clean_replay",
        )
        for source_id, _ in CONTACT_ROLES for target_id, _ in CONTACT_ROLES
    )
    return ProofMatrix196(cells, "PLANNED" if not post_action else "BLOCK")

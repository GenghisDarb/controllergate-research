from __future__ import annotations

from controllergate.core.evidence import hash_record
from .contact_ledger import CONTACT_ROLES
from .contact_pair_rules import derive_rule


def resolve_all_contact_pairs(pre_state_hashes: dict[str, str]) -> list[dict[str, object]]:
    cells = []
    for source_id, source_role in CONTACT_ROLES:
        for destination_id, destination_role in CONTACT_ROLES:
            rule = derive_rule(source_role, destination_role)
            cell = {"cell_id": f"{source_id}__{destination_id}", "source_contact": source_id, "source_role": source_role, "destination_contact": destination_id, "destination_role": destination_role, **rule, "why_relation_matters": f"ordered proof custody for {source_role} and {destination_role}", "pre_state_evidence": pre_state_hashes.get(source_id, "NOT_ESTABLISHED"), "required_post_state_evidence": f"future_post_state:{destination_id}", "current_status": "PLANNED", "blocker": "post_action_evidence_not_available", "reopen_condition": "authorized_action_then_post_action_contact_audit"}
            cell["cell_hash"] = hash_record(cell); cells.append(cell)
    return cells

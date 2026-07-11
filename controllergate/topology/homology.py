from __future__ import annotations

from itertools import combinations
from typing import Any

from controllergate.core.evidence import hash_record


def structural_signature(candidate_id: str, contacts: list[dict[str, Any]], graph: dict[str, Any], ast_record: dict[str, Any]) -> dict[str, Any]:
    signature = {"candidate_id": candidate_id, "contact_states": {item["canonical_role"]: item["evidence_status"] for item in contacts}, "provider_boundary": next(item["blocker"] for item in contacts if item["canonical_role"] == "provider_and_cofactor"), "target_origin": next(item["evidence_status"] for item in contacts if item["canonical_role"] == "target_import_origin"), "semantic_edge_classes": sorted({item["edge_class"] for item in graph["edges"] if item["edge_class"] != "canonical_sequence"}), "ast_status": ast_record["status"], "outcome_inputs": False, "tier_label_inputs": False}
    signature["signature_hash"] = hash_record(signature); return signature


def evaluate_all_pairs(signatures: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for left, right in combinations(signatures, 2):
        exact = [key for key in ["provider_boundary", "target_origin", "ast_status"] if left[key] == right[key] and left[key] not in {None, "NOT_ESTABLISHED", "BLOCK"}]
        compatible = sorted(set(left["semantic_edge_classes"]) & set(right["semantic_edge_classes"]))
        conflicts = ["candidate_source_identity"]
        if exact and compatible:
            classification = "partial_homology"; verified = False; reason = "source_identity_conflict_blocks_transfer"
        else:
            classification = "insufficient_evidence"; verified = False; reason = "role_specific_cross_candidate_evidence_insufficient"
        row = {"source_candidate": left["candidate_id"], "target_candidate": right["candidate_id"], "classification": classification, "exact_invariants": exact, "compatible_orthology": compatible, "conflicting_homology": conflicts, "superficial_similarity_only": False, "verified_homology": verified, "transfer_allowed": False, "negative_transfer_risk": "blocked", "reason": reason, "candidate_adjacency_used": False}
        row["record_hash"] = hash_record(row); rows.append(row)
    return rows

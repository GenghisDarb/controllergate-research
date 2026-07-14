from __future__ import annotations

from controllergate.reactions.stable_identity import stable_hash


def ledger_entry(candidate_id: str, comparison: dict[str, object]) -> dict[str, object]:
    value = {"candidate_id": candidate_id, "structural_hints": comparison.get("shared_motifs", []),
             "used_for_probe_ranking_only": True, "patch_text_present": False}
    value["entry_hash"] = stable_hash(value)
    return value

from __future__ import annotations

PENALTY_CODES = {
    "PRECONDITION_UNRESOLVED",
    "TARGET_INTENT_NOT_REACHED",
    "NO_PATCH_GENERATED",
    "PATCH_SAFETY_FAILED",
    "TARGET_VALIDATION_FAILED",
}

SUCCESS_CODES = {
    "TARGET_VALIDATION_PASSED",
    "DUPLICATE_REPLAY_PASSED",
    "REPAIR_SUCCESS",
}


def weight_class_for_code(code: str) -> str:
    if code in PENALTY_CODES:
        return "downrank"
    if code in SUCCESS_CODES:
        return "uprank"
    return "neutral"


def build_status_code_weight_map(records: list[dict[str, object]], legal_source_paths: list[str]) -> dict[str, object]:
    legal = set(legal_source_paths)
    weights = []
    unmapped = []
    excluded = []
    for record in records:
        code = str(record.get("status_code"))
        path = record.get("source_path")
        uses_patch_detail = record.get("uses_patch_bytes_or_rationale") is True
        if uses_patch_detail:
            excluded.append({**record, "exclusion_reason": "patch_detail_quarantine"})
            continue
        if not path or path not in legal:
            unmapped.append({**record, "unmapped_reason": "no_legal_source_context_feature"})
            continue
        weight_class = weight_class_for_code(code)
        weight = -1 if weight_class == "downrank" else 1 if weight_class == "uprank" else 0
        weights.append(
            {
                "status_code": code,
                "source_path": path,
                "function_or_class": record.get("function_or_class"),
                "weight_class": weight_class,
                "weight": weight,
                "evidence_path": record.get("evidence_path"),
                "evidence_sha256": record.get("evidence_sha256"),
                "reason": record.get("reason"),
                "decision_time_safe": record.get("decision_time_safe") is True,
            }
        )
    return {
        "status": "PASS",
        "weights": weights,
        "unmapped_records": unmapped,
        "excluded_records": excluded,
        "no_relevant_memory_features_available": not weights,
    }


def weights_are_evidence_linked(weight_map: dict[str, object]) -> bool:
    return all(
        isinstance(item, dict)
        and bool(item.get("status_code"))
        and bool(item.get("source_path"))
        and bool(item.get("evidence_path"))
        and bool(item.get("evidence_sha256"))
        and bool(item.get("reason"))
        for item in weight_map.get("weights", [])
    )

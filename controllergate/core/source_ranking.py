from __future__ import annotations

import hashlib
import json


def stable_hash(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def baseline_source_ranking(source_paths: list[str]) -> list[dict[str, object]]:
    return [
        {
            "rank": index + 1,
            "source_path": path,
            "function_or_class": None,
            "base_score": 0,
            "memory_weight": 0,
            "final_score": 0,
            "reason_codes": ["baseline_patchable_source_subset"],
        }
        for index, path in enumerate(source_paths)
    ]


def apply_status_weights(baseline: list[dict[str, object]], weight_map: dict[str, object]) -> list[dict[str, object]]:
    weight_by_path: dict[str, int] = {}
    reasons_by_path: dict[str, list[str]] = {}
    for item in weight_map.get("weights", []):
        if not isinstance(item, dict):
            continue
        path = str(item.get("source_path"))
        weight_by_path[path] = weight_by_path.get(path, 0) + int(item.get("weight", 0))
        reasons_by_path.setdefault(path, []).append(str(item.get("status_code")))
    weighted = []
    for row in baseline:
        path = str(row.get("source_path"))
        memory_weight = weight_by_path.get(path, 0)
        weighted.append(
            {
                **row,
                "memory_weight": memory_weight,
                "final_score": int(row.get("base_score", 0)) + memory_weight,
                "reason_codes": list(row.get("reason_codes", [])) + reasons_by_path.get(path, []),
            }
        )
    return sorted(weighted, key=lambda item: (-int(item["final_score"]), str(item["source_path"])))


def apply_high_pass_filter(weighted: list[dict[str, object]], *, minimum_legal_sources: int = 1) -> dict[str, object]:
    legal = [item for item in weighted if item.get("source_path")]
    if len(legal) < minimum_legal_sources:
        return {"status": "BLOCK", "blocker": "high_pass_filter_no_legal_source_remaining", "admitted": [], "masked": []}
    return {
        "status": "PASS",
        "blocker": None,
        "admitted": legal,
        "masked": [],
        "rule": "do_not_mask_the_only_legal_patchable_source",
    }


def select_two_candidate_routes(weighted: list[dict[str, object]]) -> dict[str, object]:
    primary = weighted[0] if weighted else None
    secondary = None
    if primary:
        for item in weighted[1:]:
            if item.get("source_path") != primary.get("source_path") or item.get("function_or_class") != primary.get("function_or_class"):
                secondary = item
                break
    return {
        "status": "PASS" if primary else "BLOCK",
        "primary_route": primary,
        "secondary_route": secondary,
        "secondary_available": secondary is not None,
    }


def strict_minimum_delta(
    *,
    before: list[dict[str, object]],
    after: list[dict[str, object]],
    context_before: list[str],
    context_after: list[str],
    generation_before: dict[str, object],
    generation_after: dict[str, object],
) -> dict[str, object]:
    before_top = before[0] if before else {}
    after_top = after[0] if after else {}
    reason_codes = []
    if before_top.get("source_path") != after_top.get("source_path"):
        reason_codes.append("top_ranked_source_file_changed")
    if before_top.get("function_or_class") != after_top.get("function_or_class"):
        reason_codes.append("top_ranked_function_or_class_changed")
    if context_before != context_after:
        reason_codes.append("context_selection_changed")
    if generation_before != generation_after:
        reason_codes.append("generation_strategy_changed")
    detected = bool(reason_codes)
    return {
        "status": "PASS",
        "routing_delta_detected": detected,
        "routing_delta_reason_codes": reason_codes,
        "source_ranking_before_hash": stable_hash(before),
        "source_ranking_after_hash": stable_hash(after),
        "context_before_hash": stable_hash(context_before),
        "context_after_hash": stable_hash(context_after),
        "generation_strategy_before_hash": stable_hash(generation_before),
        "generation_strategy_after_hash": stable_hash(generation_after),
        "blocker": None if detected else "active_memory_routing_delta_not_established",
    }

from __future__ import annotations


def retrieve_structural(
    rows: list[dict[str, object]], query: dict[str, object], *, holdout_family: str, excluded_proof_groups: set[str], limit: int = 3
) -> dict[str, object]:
    eligible = [row for row in rows if row["repository_family"] != holdout_family and row["proof_group"] not in excluded_proof_groups]
    query_features = query.get("features", {})
    scored = []
    for row in eligible:
        features = row.get("features", {})
        overlap = sorted(key for key in query_features if query_features[key] == features.get(key))
        scored.append((len(overlap), str(row.get("signature")), row, overlap))
    selected = sorted(scored, reverse=True)[:limit]
    return {
        "holdout_family": holdout_family,
        "excluded_repositories": [holdout_family],
        "excluded_proof_groups": sorted(excluded_proof_groups),
        "retrieved_structural_records": [row for _, _, row, _ in selected],
        "similarity_components": [overlap for _, _, _, overlap in selected],
    }

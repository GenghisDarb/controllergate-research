"""Role-aware semantic projections for externally executed evidence."""

from __future__ import annotations

from typing import Any, Iterable

from .replay_normalization_v1 import canonical_hash, normalize_replay


DEFAULT_SCIENTIFIC_FIELDS = (
    "return_code",
    "exception_type",
    "failed_node_count",
    "semantic_observation",
    "observed_sentinels",
    "source_tree_hash_before",
    "source_tree_hash_after",
    "test_tree_hash_before",
    "test_tree_hash_after",
    "provider_identity",
    "runtime_attestation_hash",
    "candidate_state",
)


def project_semantics(record: dict[str, Any], fields: Iterable[str] = DEFAULT_SCIENTIFIC_FIELDS) -> dict[str, Any]:
    """Project declared scientific fields and bind the result to raw bytes."""

    selected = {field: record[field] for field in fields if field in record}
    normalized = normalize_replay(selected)
    return {
        "schema": "controllergate-semantic-projection-v1",
        "raw_record_hash": canonical_hash(record),
        "projected_fields": sorted(selected),
        "semantic_value": normalized,
        "semantic_hash": canonical_hash(normalized),
        "producer": "controllergate.evidence.semantic_projection_v1.project_semantics",
        "execution_depth": "deterministic projection of raw record",
        "semantic_scope": "declared outcome fields",
        "authority_allowed": "predicate evaluation and replay comparison",
        "authority_forbidden": ["raw evidence replacement", "causal ownership", "patch", "repair count"],
    }

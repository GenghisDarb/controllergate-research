from __future__ import annotations

from typing import Any


def verify_collection_contract(*, requested_target: str, return_code: int, collected_nodes: list[str], plugin_loaded: bool, structured_json_present: bool, internal_error: bool, source_hash_before: str, source_hash_after: str, test_hash_before: str, test_hash_after: str, probe_hash_before: str, probe_hash_after: str) -> dict[str, Any]:
    exact = requested_target in collected_nodes
    immutable = source_hash_before == source_hash_after and test_hash_before == test_hash_after and probe_hash_before == probe_hash_after
    passed = return_code == 0 and plugin_loaded and structured_json_present and bool(collected_nodes) and exact and not internal_error and immutable
    return {
        "status": "PASS" if passed else "BLOCK", "return_code": return_code,
        "plugin_loaded": plugin_loaded, "structured_json_present": structured_json_present,
        "collected_node_count": len(collected_nodes), "exact_target_collected": exact,
        "internal_error": internal_error, "trees_immutable": immutable,
        "node_collection_pass": passed,
    }

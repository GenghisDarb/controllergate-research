from __future__ import annotations

from typing import Any

from .collection_contract_v2 import verify_collection_contract
from .collection_result_parser import parse_collection_result


def verify_collection_output(*, requested_target: str, return_code: int, stdout: str, stderr: str, plugin_loaded: bool, hashes: dict[str, str]) -> dict[str, Any]:
    parsed = parse_collection_result(stdout, stderr)
    return verify_collection_contract(requested_target=requested_target, return_code=return_code, collected_nodes=parsed["nodes"], plugin_loaded=plugin_loaded, structured_json_present=parsed["structured_json_present"], internal_error=parsed["internal_error"], source_hash_before=hashes["source_before"], source_hash_after=hashes["source_after"], test_hash_before=hashes["test_before"], test_hash_after=hashes["test_after"], probe_hash_before=hashes["probe_before"], probe_hash_after=hashes["probe_after"])

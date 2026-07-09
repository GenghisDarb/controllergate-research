from __future__ import annotations

REQUIRED_SOURCE_TOPOLOGY_FIELDS = [
    "source_file_inventory",
    "target_module_import_graph",
    "candidate_symbol_map",
    "function_class_ownership_map",
    "call_contact_graph",
    "AST_parse_status",
    "patch_locality_region",
    "symbol_references_touched",
    "risk_of_broad_semantic_alteration",
    "forbidden_path_check",
    "source_contact_to_failure_trace",
]


def validate_source_topology_map(topology: dict[str, object]) -> dict[str, object]:
    missing = [field for field in REQUIRED_SOURCE_TOPOLOGY_FIELDS if field not in topology]
    tests_only = topology.get("source_contact_to_failure_trace") == "tests_only"
    return {
        "status": "PASS" if not missing and not tests_only else "FAIL",
        "missing": missing,
        "tests_only": tests_only,
        "blocker": None if not missing and not tests_only else "patch_license_closed_source_topology_incomplete",
    }


def source_topology_patch_gate_policy() -> dict[str, object]:
    return {
        "status": "PASS",
        "future_patch_gate_law": True,
        "required_fields": REQUIRED_SOURCE_TOPOLOGY_FIELDS,
        "tests_only_topology_blocks_patch_generation": True,
    }

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import write_json_deterministic
from controllergate.core.maintenance_graph_v2 import graph_contract
from controllergate.governance.constitution_v2 import ALLOWED_STATUSES, build_registry


def main() -> int:
    write_json_deterministic(ROOT / "configs/controllergate_engineering_constitution_v2.json", build_registry())
    write_json_deterministic(ROOT / "configs/controllergate_law_proof_schema_v2.json", {
        "schema_version": 2,
        "required_fields": ["law_id", "law_definition_hash", "owner_module", "enforcement_callable", "owner_import_result", "enforcer_execution_result", "positive_test_id", "positive_test_execution", "negative_test_id", "negative_test_execution", "required_evidence_verification", "ci_invocation_record", "proof_artifact", "proof_hash", "independent_verifier_result", "calculated_status", "exact_blocker"],
        "allowed_statuses": sorted(ALLOWED_STATUSES),
        "fixed_index_status_assignment_forbidden": True,
    })
    write_json_deterministic(ROOT / "configs/controllergate_maintenance_graph_v2.json", graph_contract())
    write_json_deterministic(ROOT / "configs/batch082_candidate_frame.json", {
        "frame_version": 1,
        "adaptive_replacement_forbidden": True,
        "candidate_order": ["incident_openbb_7585_modular_openapi_reproducer", "incident_poetry_10974_windows_name_normalization"],
        "candidates": [
            {
                "candidate_id": "incident_openbb_7585_modular_openapi_reproducer",
                "repository": "https://github.com/OpenBB-finance/OpenBB.git",
                "issue_url": "https://github.com/OpenBB-finance/OpenBB/issues/7585",
                "source_sha": "1c74893140292944e71ff5cdd9536edf12f05483",
                "platform": "linux", "runtime": "python3.11", "lane": "ISSUE_DERIVED_REPRODUCER_LANE",
                "secondary_input_repository": "https://github.com/EodHistoricalData/EODHD-openapi.git",
                "secondary_input_cutoff": "2026-07-13T18:15:59Z",
                "commands": ["openbb --generate-spec --server http://localhost:8000 --openapi-path /openapi.yaml --output eodhd.spec", "openbb --generate-extension --spec eodhd.spec --provider-name eodhd --output ./openbb-eodhd"],
                "external_network_during_reproduction": False,
            },
            {
                "candidate_id": "incident_poetry_10974_windows_name_normalization",
                "repository": "https://github.com/python-poetry/poetry.git",
                "issue_url": "https://github.com/python-poetry/poetry/issues/10974",
                "source_tag": "2.4.1", "resolved_tag_sha": "811a12dae0fe81f199e3f1b88b8b8be9eed543c2",
                "cutoff_comparison_sha": "f46702336862f30050d5c641d5ed6f7568ded793",
                "platform": "windows", "runtime": "python3.13", "lane": "ISSUE_DERIVED_REPRODUCER_LANE",
                "command": "poetry init -n", "working_directory_basename": "my project with spaces",
                "expected_project_name": "my-project-with-spaces",
            },
        ],
    })
    write_json_deterministic(ROOT / "configs/batch082_preregistration.json", {
        "version": 1, "candidate_count": 2, "candidate_replacement_after_execution": False,
        "comparative_arms": ["AMDS_ACTIVE_REAL_MEMORY", "AMDS_ACTIVE_NO_MEMORY", "AMDS_ACTIVE_SHUFFLED_MEMORY", "FIXED_ORDER_REAL_MEMORY", "FIXED_ORDER_NO_MEMORY", "FIXED_ORDER_SHUFFLED_MEMORY"],
        "null_orders_per_candidate_minimum": 19,
        "single_candidate_fallback": "SINGLE_CANDIDATE_ENGINEERING_PILOT_NO_MEMORY",
        "zero_candidate_outcome": "HONEST_BLOCKED_INFRASTRUCTURE_OUTPUT",
        "maximum_authoritative_repairs": 2,
        "authoritative_repair_memory": "NO_MEMORY",
        "full_scoring": "NOT_RUN/disallowed",
    })
    print(json.dumps({"status": "PASS", "law_count": 40, "candidate_count": 2}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


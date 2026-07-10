from __future__ import annotations

from typing import Any


def agnostic_provenance_lock_scaffold() -> dict[str, Any]:
    return {
        "status": "scaffolded_with_config_and_audit",
        "activation_state": "not_run_precondition_blocked",
        "purpose": "Define future non-Git provenance records without enabling live runtime repair.",
        "supported_future_evidence_kinds": [
            "binary_hash",
            "memory_snapshot_hash",
            "crash_dump_hash",
            "process_state_hash",
            "event_stream_hash",
            "operator_policy_hash",
        ],
        "active_collection_enabled": False,
        "live_device_access_enabled": False,
        "patch_authority": False,
        "forbidden_until_activation": [
            "live_device_hook",
            "memory_dump_collection",
            "runtime_hot_swap",
            "live_patch_application",
        ],
        "audit_status": "PASS",
    }

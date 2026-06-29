from __future__ import annotations

from controllergate.core.clean_repair import active_failure_memory_weighting, memory_disabled_exclusion_audit


def test_arm_a_memory_must_alter_routing_to_count_active():
    selection = {
        "ranked_patchable_sources": [
            {
                "file_path": "src/darker/config.py",
                "function_or_class": ["validate_stdin_src"],
                "score": 1,
                "reason_codes": [],
            }
        ]
    }
    result = active_failure_memory_weighting(selection, {"records": [{"status_code": "PINNED_EDGE"}]})

    assert result["failure_memory_markers_passive"] is False
    assert result["changed_generation_strategy"] is True


def test_arm_b_memory_exclusion_blocks_memory_sources():
    result = memory_disabled_exclusion_audit()

    assert result["status"] == "PASS"
    assert result["memory_ledger_opened"] is False
    assert result["successful_patch_bytes_opened"] is False
    assert result["memory_weighted_routing_applied"] is False

from controllergate.core.failure_memory import build_status_code_inventory
from controllergate.core.status_code_weighting import build_status_code_weight_map


def test_status_codes_must_map_to_evidence_before_changing_weights():
    inventory = build_status_code_inventory([
        {
            "status_code": "NO_PATCH_GENERATED",
            "candidate_id": "c1",
            "source_path": "src/pkg/mod.py",
            "evidence_path": "outputs/x.json",
            "evidence_sha256": "abc",
            "decision_time_safe": True,
            "reason": "prior no-patch blocker",
        }
    ])
    weight_map = build_status_code_weight_map(inventory["records"], ["src/pkg/mod.py"])
    assert weight_map["weights"][0]["weight_class"] == "downrank"
    assert weight_map["weights"][0]["evidence_sha256"] == "abc"


def test_unmapped_status_codes_cannot_change_routing():
    inventory = build_status_code_inventory([
        {
            "status_code": "PRECONDITION_UNRESOLVED",
            "candidate_id": "c1",
            "source_path": None,
            "evidence_path": "outputs/x.json",
            "evidence_sha256": "abc",
            "decision_time_safe": True,
            "reason": "environment blocker",
        }
    ])
    weight_map = build_status_code_weight_map(inventory["records"], ["src/pkg/mod.py"])
    assert weight_map["weights"] == []
    assert weight_map["no_relevant_memory_features_available"] is True


def test_patch_bytes_cannot_be_used_as_memory():
    inventory = build_status_code_inventory([
        {
            "status_code": "REPAIR_SUCCESS",
            "candidate_id": "c1",
            "source_path": "src/pkg/mod.py",
            "evidence_path": "outputs/patch.diff",
            "evidence_sha256": "abc",
            "decision_time_safe": True,
            "uses_patch_bytes_or_rationale": True,
            "reason": "patch detail excluded",
        }
    ])
    weight_map = build_status_code_weight_map(inventory["records"], ["src/pkg/mod.py"])
    assert weight_map["weights"] == []
    assert weight_map["excluded_records"][0]["exclusion_reason"] == "patch_detail_quarantine"

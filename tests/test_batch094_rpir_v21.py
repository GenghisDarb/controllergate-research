from __future__ import annotations

from controllergate.reactome_ir.nested import _content_reference
from controllergate.reactome_ir.schema import RPIR_V2_1_VERSION, field_value, rpir_v2_1_schema


def test_rpir_v21_is_one_way_value_bound_extension() -> None:
    schema = rpir_v2_1_schema()
    assert schema["$id"] == RPIR_V2_1_VERSION
    assert schema["migration"] == {"from": "controllergate-rpir-v2", "direction": "one_way", "idempotent": True}
    assert "stable_event_edges" in schema["required"]
    assert "normal_variant_graph" in schema["required"]
    assert "nested_membership_closure" in schema["required"]


def test_content_addressed_binding_does_not_duplicate_ledger_rows() -> None:
    row = {"edge_hash": "a" * 64, "parent": {"database_id": 1}, "member": {"database_id": 2}}
    assert _content_reference("entity_set_members", row) == "a" * 64


def test_absence_state_cannot_assert_a_value() -> None:
    try:
        field_value([1], state="SOURCE_NOT_EXPOSED_BY_FORMAT", source="test")
    except ValueError:
        pass
    else:
        raise AssertionError("absence state accepted an asserted value")

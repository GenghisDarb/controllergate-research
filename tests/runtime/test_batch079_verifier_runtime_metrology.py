from __future__ import annotations

from controllergate.metrology.control_taxonomy import CONTROL_TAXONOMY, domain_relative_effects, empirical_tail, exact_probe_orders
from controllergate.runtime.admission_failure_classifier import classify_capsule_failure
from controllergate.runtime.collection_contract import validate_collection
from controllergate.runtime.native_working_directory_adapter import build_native_working_directory_adapter
from controllergate.runtime.python_runtime_resolver import resolve_python_runtime
from controllergate.runtime.semantic_change_verifier import verify_html_title_only_change
from controllergate.runtime.unified_diff_contract import parse_unified_diff


PATCH = """diff --git a/cognicore/studio.py b/cognicore/studio.py
--- a/cognicore/studio.py
+++ b/cognicore/studio.py
@@ -1 +1 @@
-<title>Old</title>
+<title>New</title>
"""


def test_unified_diff_counts_headers_not_at_markers():
    parsed = parse_unified_diff(PATCH)
    assert parsed["status"] == "PASS" and parsed["hunk_count"] == 1


def test_unified_diff_multiple_and_malformed_hunks():
    two = PATCH + "@@ -3 +3 @@\n-a\n+b\n"
    assert parse_unified_diff(two)["hunk_count"] == 2
    assert parse_unified_diff(PATCH.replace("@@ -1 +1 @@", "@@ broken @@"))["status"] == "BLOCK"


def test_title_only_semantic_witness_and_negative_controls():
    before = "@app.get('/api/x')\n<html><head><title>Old</title><style>x{}</style></head><script>x()</script></html>"
    after = before.replace("<title>Old</title>", "<title>New</title>")
    assert verify_html_title_only_change(before=before, after=after, patch_text=PATCH, expected_file="cognicore/studio.py")["status"] == "PASS"
    assert verify_html_title_only_change(before=before, after=after + "<script>y()</script>", patch_text=PATCH, expected_file="cognicore/studio.py")["status"] == "BLOCK"


def test_failure_contract_separates_collection_timeout_and_candidate_failure():
    assert classify_capsule_failure({"stage": "collection", "return_code": 4, "target_nodes": [], "bounded_output_tail": "not found"})["candidate_failure_admissible"] is False
    assert classify_capsule_failure({"stage": "test_execution", "return_code": 124, "timeout_state": True, "target_nodes": ["x"], "bounded_output_tail": "assert"})["classification"] == "RESOURCE_TIMEOUT_REPRODUCED"
    assert classify_capsule_failure({"stage": "test_execution", "return_code": 1, "target_nodes": ["x"], "bounded_output_tail": "AssertionError"})["classification"] == "CANDIDATE_FAILURE_REPRODUCED"


def test_collection_contract_requires_exact_node():
    assert validate_collection(requested_target="a.py::test_a", collected_nodes=["a.py::test_a"], return_code=0)["status"] == "PASS"
    assert validate_collection(requested_target="a.py::test_a", collected_nodes=[], return_code=0)["candidate_failure_evidence"] is False


def test_runtime_resolver_freezes_before_outcome():
    result = resolve_python_runtime({"requires_python": ">=3.8,<3.12", "declared_versions": ["3.9", "3.10"]})
    assert result["selected_runtime"] == "3.10"
    assert result["selected_before_test_execution"] is True
    assert result["outcome_used_for_selection"] is False


def test_native_working_directory_adapter_separates_scratch(tmp_path):
    source = tmp_path / "source"; scratch = tmp_path / "scratch"; source.mkdir(); scratch.mkdir()
    result = build_native_working_directory_adapter(source_root=source, scratch_root=scratch, target="tests/test_x.py::test_x")
    assert result["status"] == "PASS"
    assert result["command_working_directory"] != result["runtime_scratch"]
    assert result["candidate_source_read_only"] and result["candidate_tests_read_only"]


def test_control_taxonomy_does_not_conflate_baseline_and_null():
    assert CONTROL_TAXONOMY["random_legal_probe_ranking"] == "RANDOMIZATION_NULL"
    assert CONTROL_TAXONOMY["fixed_legal_order_no_memory"] == "STRONG_BASELINE_COMPARATOR"
    assert CONTROL_TAXONOMY["amds_no_memory"] == "MEMORY_ABLATION"


def test_empirical_tail_uses_add_one_resolution():
    result = empirical_tail(1.0, [0.1] * 19)
    assert result["p_empirical"] == 0.05
    assert result["CG_NSI_v2"] == 0.95
    assert result["minimum_attainable_p"] == 0.05


def test_exact_null_orders_are_unique():
    result = exact_probe_orders(["a", "b", "c"])
    assert result["number_enumerated"] == 6 and result["duplicate_sequences"] == 0


def test_degenerate_null_fails_closed_without_infinite_z():
    result = domain_relative_effects(1.0, [0.5] * 19)
    assert result["status"] == "DEGENERATE_NULL_DISTRIBUTION"
    assert result["Z_mean"] is None and result["Z_robust"] is None

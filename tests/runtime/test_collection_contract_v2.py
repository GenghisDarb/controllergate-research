from controllergate.runtime.collection_result_parser import parse_collection_result
from controllergate.runtime.collection_verifier import verify_collection_output


H = {"source_before": "s", "source_after": "s", "test_before": "t", "test_after": "t", "probe_before": "p", "probe_after": "p"}


def test_structured_exact_node_passes():
    out = 'CONTROLLERGATE_COLLECTION_JSON={"nodes":["tests/test_x.py::test_x"]}'
    assert verify_collection_output(requested_target="tests/test_x.py::test_x", return_code=0, stdout=out, stderr="", plugin_loaded=True, hashes=H)["status"] == "PASS"


def test_internalerror_with_colons_rejected():
    out = 'INTERNALERROR tests/test_x.py::test_x\nCONTROLLERGATE_COLLECTION_JSON={"nodes":[]}'
    result = verify_collection_output(requested_target="tests/test_x.py::test_x", return_code=3, stdout=out, stderr="", plugin_loaded=True, hashes=H)
    assert result["status"] == "BLOCK"
    assert not result["node_collection_pass"]


def test_plain_colon_line_not_a_node():
    assert parse_collection_result("INTERNALERROR file.py::thing", "")["nodes"] == []

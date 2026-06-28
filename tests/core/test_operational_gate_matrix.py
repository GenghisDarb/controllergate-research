from __future__ import annotations

import json
from pathlib import Path


REQUIRED_GATES = {
    "Artifact Byte Custody",
    "Workspace Transport Integrity",
    "External Candidate Registry",
    "Semantic Failure Signature",
    "Structural Navigation Map",
    "Active Probe Router",
    "Candidate Admission Decision Map",
    "Execution Environment Normalization",
    "Public Claim Boundary Audit",
    "v3.0 Readiness Gate",
}


def test_operational_gate_matrix_contains_required_neutral_gates():
    matrix = json.loads(Path("configs/operational_gate_matrix.json").read_text(encoding="utf-8"))
    names = {item["neutral_gate_name"] for item in matrix["gates"]}

    assert len(matrix["gates"]) >= 26
    assert REQUIRED_GATES <= names
    assert matrix["terminology_policy"] == "neutral_engineering_terms_only"
    assert "native_repair_evidence" in matrix["evidence_classes"]
    assert "issue_derived_repair_evidence" in matrix["evidence_classes"]

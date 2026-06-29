from __future__ import annotations

import json
from pathlib import Path


PUBLIC_DOCS = [
    Path("README.md"),
    Path("docs/current_status.md"),
    Path("docs/capability_inventory.md"),
    Path("docs/public_release_readiness.md"),
    Path("docs/technical_validation_gap_report.md"),
    Path("docs/operational_gate_matrix.md"),
]


def test_operational_gate_matrix_cross_references_traceability_entries() -> None:
    matrix = json.loads(Path("configs/notebooklm_advice_traceability_matrix.json").read_text(encoding="utf-8"))
    operational = json.loads(Path("configs/operational_gate_matrix.json").read_text(encoding="utf-8"))
    gate_names = {gate["neutral_gate_name"] for gate in operational["gates"]}
    for entry in matrix["entries"]:
        if entry["status"] not in {"deferred_with_blocker", "rejected_with_reason"}:
            assert entry["operational_gate_name"] in gate_names, entry["advice_id"]
    crosscheck = json.loads(Path("outputs/clean_replication_batch_005/operational_gate_matrix_crosscheck.json").read_text(encoding="utf-8"))
    assert crosscheck["status"] == "PASS"


def test_public_docs_status_matches_traceability_matrix_and_uses_neutral_terms() -> None:
    blocked_terms = [
        "chromo" + "somal",
        "TO" + "RUS",
        "TL" + "D",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "Klein " + "twist",
        "OS" + "QN",
        "N" + "\u2248",
        "meta" + "phorical",
    ]
    for path in PUBLIC_DOCS:
        text = path.read_text(encoding="utf-8")
        assert "Current operational gate status" in text
        for term in blocked_terms:
            assert term not in text

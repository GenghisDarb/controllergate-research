from __future__ import annotations

from pathlib import Path

from controllergate.core.maintenance_transition_guard import guard_transition
from controllergate.protocols.v2_18_evidence_derived_topology_historical_provider import runtime_capabilities
from controllergate.topology.contact_pair_obligation_resolver import resolve_all_contact_pairs
from controllergate.topology.contact_pair_verifiers import verify_cells
from controllergate.topology.contact_resolvers import resolve_all_contacts
from controllergate.topology.homology import evaluate_all_pairs
from controllergate.topology.tld_clean_track import evaluate_parent


def test_contact_resolution_never_passes_synthetic_labels(tmp_path: Path) -> None:
    state = tmp_path / "state.json"
    state.write_text("{}", encoding="utf-8")
    records = resolve_all_contacts({"semantic_transitions": []}, state, {})
    assert len(records) == 14
    assert all(item["gate_decision"] == "BLOCK" for item in records)
    assert all(not item["generic_template_derived"] for item in records)


def test_all_pairs_are_evaluated_without_adjacency() -> None:
    signatures = [{"candidate_id": f"c{i}", "provider_boundary": "x", "target_origin": "PARTIAL", "ast_status": "BLOCK", "semantic_edge_classes": [], "signature_hash": str(i)} for i in range(25)]
    rows = evaluate_all_pairs(signatures)
    assert len(rows) == 300
    assert not any(row["candidate_adjacency_used"] for row in rows)
    assert not any(row["transfer_allowed"] for row in rows)


def test_semantic_proof_matrix_has_196_resolved_cells() -> None:
    hashes = {f"CG-C14-{index:02d}": f"hash-{index}" for index in range(1, 15)}
    result = verify_cells(resolve_all_contact_pairs(hashes))
    assert result["status"] == "PASS"
    assert result["resolved_cell_count"] == 196
    assert result["unresolved_fallback_cell_count"] == 0


def test_tld_argmin_is_canonical_and_elbow_is_not_established() -> None:
    parent = {"ladder_id": "l", "candidate_id": "c", "is_null": False, "eligible": True, "provenance_complete": True, "omega_numeric": list(range(40))}
    result = evaluate_parent(parent, [6, 7, 8, 9], 10)
    assert result["winner_N_argmin"]["status"] == "PASS"
    assert result["winner_N_elbow"]["status"] == "NOT_ESTABLISHED"
    assert result["noncanonical_elbow_diagnostic"]["canonical"] is False


def test_out_of_order_maintenance_transition_blocks_without_command() -> None:
    result = guard_transition("bounded_action", set(), "0" * 64, {"status": "PASS", "allowed_phase": "bounded_action", "invokes_command": True}, {"candidate_id": "c"}, {"safety": "PASS"})
    assert result.status == "BLOCK"
    assert result.command_invoked is False
    assert result.canonical_state_mutated is False


def test_v218_runtime_bindings_are_callable_and_complete() -> None:
    capabilities = runtime_capabilities()
    assert capabilities["status"] == "PASS"
    assert capabilities["unbound_reusable_mechanisms"] == []
    assert len(capabilities["bindings"]) >= 18

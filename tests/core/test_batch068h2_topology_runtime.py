from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path

import pytest

from controllergate.topology import TopologyService
from controllergate.topology.activation_ring import LICENSE_GATES
from controllergate.topology.contact_ledger import CONTACT_ROLES, validate_contact_ledger
from controllergate.topology.null_models import parent_specific_nulls
from controllergate.topology.tld_metrology import build_ladder
from controllergate.topology.twist_return import two_traversals_restore_orientation

ROOT = Path(__file__).resolve().parents[2]


def states(established: bool = True):
    return {role: {"evidence_inputs": [role], "evidence_hashes": [f"{index:064x}"], "evidence_status": "ESTABLISHED" if established else "PARTIAL", "verifier_result": "PASS" if established else "PARTIAL"} for index, (_, role) in enumerate(CONTACT_ROLES, 1)}


def ledger():
    return TopologyService.build_contact_ledger("candidate", states())


def test_canonical_terminology_and_errata_are_locked():
    law = json.loads((ROOT / "configs/tld_brot_bulb_canonical_law_v1.json").read_text(encoding="utf-8"))
    assert "one local candidate" in law["definitions"]["TORUS-BROT"]
    assert "two-dimensional" in law["definitions"]["ToT-BROT"]
    assert "three/four-dimensional" in law["definitions"]["ToT-BULB"]
    assert "interchangeably" in (ROOT / "docs/internal/TLD_BROT_BULB_ERRATA.md").read_text(encoding="utf-8")


def test_reference_core_has_five_roles():
    core = TopologyService.build_reference_core({"source": "evidence"})
    assert len(core) == 5
    assert len({item.role_id for item in core}) == 5


def test_contact_ledger_enforces_exact_fourteen_unique_verified_contacts():
    item = ledger()
    assert len(item.contacts) == 14
    with pytest.raises(ValueError, match="exactly_fourteen"):
        validate_contact_ledger(item.contacts[:-1])
    with pytest.raises(ValueError, match="duplicate"):
        validate_contact_ledger(item.contacts[:-1] + (replace(item.contacts[-1], contact_id=item.contacts[0].contact_id),))
    with pytest.raises(ValueError, match="empty_or_unverified"):
        validate_contact_ledger((replace(item.contacts[0], evidence_inputs=()),) + item.contacts[1:])


def test_six_set_is_conjunctive_and_cannot_create_topology():
    facts = {"identity_and_custody_complete": True, "materialization_and_environment_bounded": True, "command_harness_and_oracle_integrity": True, "intervention_scope_and_rollback_bounded": True, "replay_and_proof_path_reachable": True}
    result = TopologyService.evaluate_activation_ring(ledger(), facts)
    assert len(result.gates) == len(LICENSE_GATES) == 6
    assert result.status == "PASS" and result.patch_authority is False
    partial = TopologyService.evaluate_activation_ring(TopologyService.build_contact_ledger("candidate", states(False)), facts)
    assert partial.status == "BLOCK"
    facts["materialization_and_environment_bounded"] = False
    assert TopologyService.evaluate_activation_ring(ledger(), facts).status == "BLOCK"


def test_proof_matrix_is_complete_and_planned_not_passed():
    matrix = TopologyService.build_proof_matrix()
    assert len(matrix.cells) == 196
    assert len({(item.source_contact, item.destination_contact) for item in matrix.cells}) == 196
    assert matrix.status == "PLANNED"


def test_local_brot_has_bounded_collapse_and_recovery_regions():
    partial = states(); partial["provider_and_cofactor"]["evidence_status"] = "PARTIAL"; partial["provider_and_cofactor"]["verifier_result"] = "PARTIAL"
    graph = TopologyService.build_local_brot(TopologyService.build_contact_ledger("candidate", partial))
    regions = {item.region for item in graph.nodes}
    assert {"bounded_region", "collapse_region", "recovery_region"} <= regions
    assert any(item.edge_class == "reopens" for item in graph.edges)


def test_coupling_requires_typed_evidence_and_blocks_similarity_only_transfer():
    left = TopologyService.build_local_brot(ledger())
    right = replace(left, candidate_id="candidate-2")
    graph = TopologyService.build_coupled_tot_brot((left, right), {(left.candidate_id, right.candidate_id): {"matched_dimensions": ["generic_python"], "typed_evidence": False}})
    assert len(graph.edges) == 1
    assert graph.edges[0].transfer_allowed is False
    assert graph.edges[0].negative_transfer_risk == "blocked"


def test_targeted_volume_separates_global_and_candidate_masks_and_rejects_blind_selection():
    local = TopologyService.build_local_brot(ledger())
    coupled = TopologyService.build_coupled_tot_brot((local,))
    with pytest.raises(ValueError, match="candidate_identity"):
        TopologyService.build_tot_bulb_volume("candidate", ledger(), coupled, {"host": "ok"}, {}, ("package_epoch",))
    with pytest.raises(ValueError, match="basin"):
        TopologyService.build_tot_bulb_volume("candidate", ledger(), coupled, {"host": "ok"}, {"candidate_identity_established": True}, ())
    volume = TopologyService.build_tot_bulb_volume("candidate", ledger(), coupled, {"host": "ok"}, {"candidate_identity_established": True}, ("package_epoch",))
    assert volume.global_mask != volume.candidate_mask and volume.basins[0].selected_by_evidence


def test_twist_return_preserves_identity_and_round_trip_class():
    record = TopologyService.validate_twist_return("a" * 64, "b" * 64, "rollback", operational_mapping_established=True)
    assert record.status == "PASS"
    assert record.return_state_hash == record.origin_state_hash
    assert two_traversals_restore_orientation(record)


def test_tld_ladder_omega_and_parent_specific_nulls_are_separate_from_outcomes():
    parent = build_ladder(ledger())
    nulls = parent_specific_nulls(parent)
    assert parent.contact_topology_size == 14 and len(parent.omega) == 14
    assert len(nulls) == 21
    assert sum(item.null_family.startswith("single_contact_ablation") for item in nulls) == 14
    assert len({item.seed for item in nulls}) == 21
    assert all(item.parent_ladder_id == parent.ladder_id for item in nulls)


def test_tld_symbols_are_not_conflated():
    symbols = json.loads((ROOT / "configs/tld_brot_bulb_canonical_law_v1.json").read_text(encoding="utf-8"))["symbols"]
    assert len(set(symbols.values())) == len(symbols)
    assert symbols["omega"].endswith("only")

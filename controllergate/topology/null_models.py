from __future__ import annotations

from controllergate.core.evidence import hash_record

from .types import TldLadderRecord, TldNullRecord


def parent_specific_nulls(parent: TldLadderRecord) -> tuple[TldNullRecord, ...]:
    base = dict(ladder_id="", candidate_id=parent.candidate_id, kind="null", parent_ladder_id=parent.ladder_id,
                omega=parent.omega, adjacency_topology=parent.adjacency_topology, is_null=True, eligible=True,
                source_evidence_hash=parent.source_evidence_hash, contact_topology_size=14, tld_recursion_depth_N=parent.tld_recursion_depth_N)
    records: list[TldNullRecord] = []
    families = ["fourteen_role_permutation", "redundant_fifteenth_contact", "cross_candidate_evidence_swap", "order_mutation", "contact_state_jitter", "linear_versus_cyclic_adjacency", "provider_environment_coupling_permutation"]
    families.extend(f"single_contact_ablation_{index:02d}" for index in range(1, 15))
    for index, family in enumerate(families):
        omega = tuple(reversed(parent.omega)) if family == "fourteen_role_permutation" else parent.omega
        if family.startswith("single_contact_ablation_"):
            removed = int(family.rsplit("_", 1)[1]) - 1
            omega = tuple(value for idx, value in enumerate(parent.omega) if idx != removed)
        if family == "redundant_fifteenth_contact":
            omega = parent.omega + (parent.omega[-1],)
        records.append(TldNullRecord(**{**base, "ladder_id": f"{parent.ladder_id}:null:{family}", "omega": omega, "seed": int(hash_record({"parent": parent.ladder_id, "family": family})[:8], 16), "notes": "deterministic parent-specific shadow control"}, null_family=family))
    return tuple(records)

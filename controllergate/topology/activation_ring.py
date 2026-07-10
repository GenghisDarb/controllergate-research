from __future__ import annotations

from .types import ActivationLicense6, ContactLedger14

LICENSE_GATES = (
    "CG-LIC-01 identity_and_custody_complete",
    "CG-LIC-02 fourteen_contact_topology_legible",
    "CG-LIC-03 materialization_and_environment_bounded",
    "CG-LIC-04 command_harness_and_oracle_integrity",
    "CG-LIC-05 intervention_scope_and_rollback_bounded",
    "CG-LIC-06 replay_and_proof_path_reachable",
)


def evaluate_activation_ring(ledger: ContactLedger14, facts: dict[str, bool]) -> ActivationLicense6:
    topology_legible = len(ledger.contacts) == 14 and all(
        item.evidence_inputs and item.evidence_hashes and item.gate_decision == "PASS"
        for item in ledger.contacts
    )
    required = (
        bool(facts.get("identity_and_custody_complete")), topology_legible,
        bool(facts.get("materialization_and_environment_bounded")), bool(facts.get("command_harness_and_oracle_integrity")),
        bool(facts.get("intervention_scope_and_rollback_bounded")), bool(facts.get("replay_and_proof_path_reachable")),
    )
    gates = tuple({"gate_id": label.split()[0], "role": label.split(maxsplit=1)[1], "status": "PASS" if passed else "BLOCK", "conjunctive": True} for label, passed in zip(LICENSE_GATES, required))
    return ActivationLicense6(gates, "PASS" if all(required) else "BLOCK", False)

from __future__ import annotations

from controllergate.reactions.stable_identity import stable_hash


STATES = (
    "REFERENCE_CORE_PRESERVED", "CONTACT_TOPOLOGY_LEGIBLE", "WORKSPACE_ACCESSIBLE",
    "PROVIDER_EXECUTION_READY", "FAILURE_REPRODUCED", "SOURCE_OWNERSHIP_ESTABLISHED",
    "REPAIR_LICENSE_GRANTED", "BOUNDED_SYNTHESIS_COMPLETED", "VALIDATION_PASSED",
    "DUPLICATE_REPLAY_AND_ROLLBACK_PASSED", "CANARY_DEPLOYMENT",
    "HEALTH_MONITORING", "COMMIT_OR_ROLLBACK", "PROOF_AND_MAINTENANCE_MEMORY_UPDATE",
)


def graph_contract() -> dict[str, object]:
    rows=[]
    for index,state in enumerate(STATES):
        row={"reaction_id":f"CG-RXN-{index+1:03d}","state":state,
             "required_verified_output_token":None if index==0 else f"CG-RXN-{index:03d}",
             "next_state":STATES[index+1] if index+1<len(STATES) else None,
             "failure_mints_output":False,"real_execution_required":True}
        row["state_hash"]=stable_hash(row);rows.append(row)
    return {"version":3,"state_count":len(rows),"states":rows,"public_state_names_neutral":True}

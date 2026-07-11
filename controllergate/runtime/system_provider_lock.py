from __future__ import annotations

from controllergate.core.evidence import hash_record


def build_system_provider_lock(inventory: dict, build_cells: list[dict]) -> dict:
    required=sorted({item for cell in build_cells for item in cell.get("system_provider_hypotheses",[])})
    tools=inventory.get("tools",{}); value={"status":"PASS" if inventory.get("status")=="PASS" else "BLOCK","classification":"current_build_only","inventory_status":inventory.get("status"),"required_provider_hypotheses":required,"available_tools":tools,"missing_tools":sorted(name for name,path in tools.items() if not path),"observed_exact":False,"cutoff_compatible":False,"network_preparation_authorized":False}
    value["lock_hash"]=hash_record(value); return value

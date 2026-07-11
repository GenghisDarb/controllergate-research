from __future__ import annotations


def evaluate_stop(*, unresolved_branches: int, legal_probes: int, budget_remaining: int, interlock_pass: bool, contradictions: int = 0, manual_review: bool = False) -> dict:
    if manual_review: return {"stop":True,"reason":"manual review required","legal_probe_count":legal_probes}
    if contradictions: return {"stop":True,"reason":"contradiction unresolved","legal_probe_count":legal_probes}
    if not interlock_pass: return {"stop":True,"reason":"interlock blocked","legal_probe_count":legal_probes}
    if unresolved_branches==0: return {"stop":True,"reason":"all known branches closed","legal_probe_count":legal_probes}
    if budget_remaining<=0: return {"stop":True,"reason":"probe budget exhausted","legal_probe_count":legal_probes}
    if legal_probes==0: return {"stop":True,"reason":"no legal probes","legal_probe_count":0}
    return {"stop":False,"reason":"continue","legal_probe_count":legal_probes}

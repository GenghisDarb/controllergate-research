from .state import DPP14State


def detect_contradiction_and_backtrack(state: DPP14State) -> DPP14State:
    by_subject: dict[str, set] = {}
    for fact in state.certain_facts:
        by_subject.setdefault(str(fact.get("subject")), set()).add(str(fact.get("value")))
    state.contradictions = [{"subject": subject, "values": sorted(values)} for subject, values in by_subject.items() if len(values) > 1]
    if state.contradictions:
        state.hypotheses = ["insufficient_evidence"]
    state.trace.append({"transition": "DetectContradictionAndBacktrack", "status": "PASS", "backtracked": bool(state.contradictions)})
    return state

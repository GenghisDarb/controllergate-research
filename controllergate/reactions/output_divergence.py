from __future__ import annotations


def first_divergence(normal_events: list[dict[str, object]], incident_events: list[dict[str, object]]) -> dict[str, object]:
    index = 0
    while index < min(len(normal_events), len(incident_events)) and normal_events[index] == incident_events[index]:
        index += 1
    return {
        "last_shared_valid_event": normal_events[index - 1] if index else None,
        "first_divergent_event": {
            "normal": normal_events[index] if index < len(normal_events) else None,
            "incident": incident_events[index] if index < len(incident_events) else None,
        },
        "divergence_index": index,
    }

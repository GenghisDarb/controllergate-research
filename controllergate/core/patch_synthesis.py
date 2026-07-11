from __future__ import annotations

from pathlib import Path
import re


def synthesize_ordering_patch(source_path: Path, symbol: str) -> dict:
    """Synthesize a bounded ordering-key repair after a diagnosed ordering failure."""
    text = source_path.read_text(encoding="utf-8")
    if symbol != "sort_routes" or "class SortableRoute:" not in text or "return sorted(routes, key=lambda r: SortableRoute" not in text:
        return {"status": "BLOCK", "blocker": "no_registered_bounded_semantic_transform"}
    pattern = re.compile(r"\n    class SortableRoute:.*?\n    return sorted\(routes, key=lambda r: SortableRoute\(key\(r\) if key else r\)\)\n", re.S)
    replacement = '''
    def specificity(path: str):
        components = [component for component in path.strip("/").split("/") if component]
        ranked = tuple(
            (1, "") if component.startswith("{") and component.endswith("}") else (0, component)
            for component in components
        )
        return ranked + ((2, ""),)

    return sorted(routes, key=lambda route: specificity(key(route) if key else route))
'''
    updated, count = pattern.subn("\n" + replacement, text, count=1)
    if count != 1: return {"status": "BLOCK", "blocker": "bounded_transform_precondition_mismatch"}
    source_path.write_text(updated, encoding="utf-8", newline="\n")
    return {"status": "PASS", "operation": "replace_nontransitive_partial_comparator_with_total_specificity_key", "semantic_objective": "order static route components before parameters and longer common-prefix routes before shorter routes"}

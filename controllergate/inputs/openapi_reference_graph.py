from __future__ import annotations

from collections import defaultdict


def strongly_connected_components(graph: dict[str, list[str]]) -> list[list[str]]:
    index = 0; stack: list[str] = []; on_stack: set[str] = set(); indices: dict[str, int] = {}; low: dict[str, int] = {}; result: list[list[str]] = []
    def visit(node: str) -> None:
        nonlocal index
        indices[node] = low[node] = index; index += 1; stack.append(node); on_stack.add(node)
        for edge in graph.get(node, []):
            if edge not in indices: visit(edge); low[node] = min(low[node], low[edge])
            elif edge in on_stack: low[node] = min(low[node], indices[edge])
        if low[node] == indices[node]:
            component: list[str] = []
            while True:
                item = stack.pop(); on_stack.remove(item); component.append(item)
                if item == node: break
            result.append(sorted(component))
    for node in sorted(graph):
        if node not in indices: visit(node)
    return result

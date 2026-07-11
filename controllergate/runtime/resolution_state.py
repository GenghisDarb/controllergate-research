from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResolutionState:
    requirements: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    selected: dict[str, dict[str, Any]] = field(default_factory=dict)
    metadata: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)
    unresolved: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    backtracking: list[dict[str, Any]] = field(default_factory=list)
    cycles: list[dict[str, Any]] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)

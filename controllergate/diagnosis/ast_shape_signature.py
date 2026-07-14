from __future__ import annotations

import ast
from collections import Counter


def ast_shape_signature(source: str) -> dict[str, int]:
    tree = ast.parse(source)
    return dict(sorted(Counter(type(node).__name__ for node in ast.walk(tree)).items()))

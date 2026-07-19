"""Generic declarative predicate evaluator for candidate outcome contracts."""

from __future__ import annotations

import re
from typing import Any


class PredicateError(ValueError):
    """Raised when a predicate is malformed rather than scientifically false."""


def resolve(document: Any, path: str) -> Any:
    current = document
    if path in ("", "$"):
        return current
    for part in path.removeprefix("$.").split("."):
        if isinstance(current, list) and part.isdigit():
            current = current[int(part)]
        elif isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise KeyError(path)
    return current


def _operand(spec: Any, document: Any) -> Any:
    if isinstance(spec, dict) and set(spec) == {"field"}:
        return resolve(document, spec["field"])
    return spec


def evaluate(predicate: dict[str, Any], document: Any) -> bool:
    """Evaluate a composable, candidate-neutral predicate."""

    if not isinstance(predicate, dict) or len(predicate) != 1:
        raise PredicateError("predicate must contain exactly one operator")
    op, argument = next(iter(predicate.items()))
    if op == "all":
        return all(evaluate(item, document) for item in argument)
    if op == "any":
        return any(evaluate(item, document) for item in argument)
    if op == "not":
        return not evaluate(argument, document)
    if op in {"exists", "missing"}:
        try:
            resolve(document, str(argument))
            found = True
        except (KeyError, IndexError, TypeError):
            found = False
        return found if op == "exists" else not found
    if op == "implies":
        if not isinstance(argument, list) or len(argument) != 2:
            raise PredicateError("implies requires [antecedent, consequent]")
        return (not evaluate(argument[0], document)) or evaluate(argument[1], document)
    if op == "count":
        values = resolve(document, argument["field"])
        if not isinstance(values, (list, tuple, dict, set)):
            raise PredicateError("count field is not countable")
        return evaluate(argument["predicate"], {"value": len(values)})
    if op == "derived_relation":
        left = _operand(argument["left"], document)
        right = _operand(argument["right"], document)
        relation = argument["relation"]
        return _compare(relation, left, right)
    if op in {"eq", "ne", "gt", "ge", "lt", "le", "contains", "in", "regex"}:
        if not isinstance(argument, list) or len(argument) != 2:
            raise PredicateError(f"{op} requires two operands")
        left = _operand(argument[0], document)
        right = _operand(argument[1], document)
        return _compare(op, left, right)
    raise PredicateError(f"unsupported predicate operator: {op}")


def _compare(op: str, left: Any, right: Any) -> bool:
    if op == "eq":
        return left == right
    if op == "ne":
        return left != right
    if op == "gt":
        return left > right
    if op == "ge":
        return left >= right
    if op == "lt":
        return left < right
    if op == "le":
        return left <= right
    if op == "contains":
        return right in left
    if op == "in":
        return left in right
    if op == "regex":
        return re.search(str(right), str(left)) is not None
    if op == "difference":
        return left != right
    if op == "same":
        return left == right
    raise PredicateError(f"unsupported relation: {op}")


def evaluate_with_receipt(predicate: dict[str, Any], document: Any) -> dict[str, Any]:
    try:
        result = evaluate(predicate, document)
        error = None
    except (KeyError, IndexError, TypeError, PredicateError) as exc:
        result = False
        error = f"{type(exc).__name__}: {exc}"
    return {
        "satisfied": result,
        "error": error,
        "predicate": predicate,
        "producer": "controllergate.evidence.declarative_predicate_v1.evaluate_with_receipt",
        "execution_depth": "declarative evaluation",
        "semantic_scope": "candidate-configured outcome semantics",
        "authority_allowed": "outcome classification",
        "authority_forbidden": ["causal ownership without matched evidence", "patch", "repair count"],
    }

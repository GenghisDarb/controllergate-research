#!/usr/bin/env python3
"""Validate the v1.7-alpha episode ledger without external dependencies."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "episode.schema.json"
LEDGER_PATH = ROOT / "traces" / "normalized" / "episodes.jsonl"


def _type_matches(value: Any, expected: Any) -> bool:
    if isinstance(expected, list):
        return any(_type_matches(value, item) for item in expected)
    if expected == "null":
        return value is None
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    return True


def _validate_array_items(path: str, value: list[Any], spec: dict[str, Any], errors: list[str]) -> None:
    item_spec = spec.get("items")
    if not item_spec:
        return
    item_type = item_spec.get("type")
    for idx, item in enumerate(value):
        if item_type and not _type_matches(item, item_type):
            errors.append(f"{path}[{idx}] expected {item_type}, got {type(item).__name__}")


def validate_episode(obj: dict[str, Any], schema: dict[str, Any], line_no: int) -> list[str]:
    errors: list[str] = []
    required = schema.get("required", [])
    properties = schema.get("properties", {})

    for field in required:
        if field not in obj:
            errors.append(f"line {line_no}: missing required field '{field}'")

    if schema.get("additionalProperties") is False:
        allowed = set(properties)
        for field in obj:
            if field not in allowed:
                errors.append(f"line {line_no}: unexpected field '{field}'")

    for field, value in obj.items():
        spec = properties.get(field)
        if not spec:
            continue
        expected_type = spec.get("type")
        if expected_type and not _type_matches(value, expected_type):
            errors.append(
                f"line {line_no}: field '{field}' expected {expected_type}, got {type(value).__name__}"
            )
            continue
        enum = spec.get("enum")
        if enum is not None and value not in enum:
            errors.append(f"line {line_no}: field '{field}' value '{value}' not in {enum}")
        pattern = spec.get("pattern")
        if pattern and isinstance(value, str) and not re.match(pattern, value):
            errors.append(f"line {line_no}: field '{field}' does not match {pattern}")
        if isinstance(value, list):
            _validate_array_items(f"line {line_no}: field '{field}'", value, spec, errors)

    return errors


def load_ledger(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    episodes: list[dict[str, Any]] = []
    errors: list[str] = []
    if not path.exists():
        return episodes, [f"ledger not found: {path}"]

    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            errors.append(f"line {line_no}: blank JSONL lines are not allowed")
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError as exc:
            errors.append(f"line {line_no}: invalid JSON: {exc.msg}")
            continue
        if not isinstance(item, dict):
            errors.append(f"line {line_no}: episode must be a JSON object")
            continue
        episodes.append(item)
    return episodes, errors


def main() -> int:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    episodes, errors = load_ledger(LEDGER_PATH)

    for idx, episode in enumerate(episodes, start=1):
        errors.extend(validate_episode(episode, schema, idx))

    if errors:
        print("ledger validation: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("ledger validation: PASS")
    print(f"episodes: {len(episodes)}")
    if not episodes:
        print("status: empty scaffold; real episodes required before scoring")
    return 0


if __name__ == "__main__":
    sys.exit(main())

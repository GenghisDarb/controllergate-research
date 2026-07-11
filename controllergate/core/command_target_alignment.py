from __future__ import annotations

from controllergate.core.evidence import hash_record


def narrow_to_target(argv: list[str], target: str) -> dict:
    base = list(argv); transformed = []
    for token in base:
        if token == "{posargs}": transformed.append(target)
        elif token == "tests" or token.startswith("tests/") or token.startswith("tests\\"):
            if not any(item.startswith("tests") for item in transformed): transformed.append(target)
        else: transformed.append(token)
    if target not in transformed: transformed.append(target)
    record = {"declared_base_command": base, "transformation": "bounded_native_target_narrowing", "exact_target": target, "transformed_command": transformed, "forbidden_flags_added": False}
    record["transformation_hash"] = hash_record(record)
    return record

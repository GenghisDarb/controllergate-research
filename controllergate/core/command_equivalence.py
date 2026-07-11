from __future__ import annotations

from typing import Sequence


WRAPPERS = {"poetry", "uv"}


def split_wrapper(argv: Sequence[str]) -> tuple[list[str], list[str]]:
    tokens = list(argv)
    if len(tokens) >= 2 and tokens[0] in WRAPPERS and tokens[1] == "run": return tokens[:2], tokens[2:]
    return [], tokens


def canonical_pytest_command(argv: Sequence[str]) -> dict:
    wrapper, inner = split_wrapper(argv); tokens = list(inner)
    if tokens[:3] in (["python", "-m", "pytest"], ["python3", "-m", "pytest"]): tokens = ["pytest", *tokens[3:]]
    elif tokens and tokens[0] == "py.test": tokens[0] = "pytest"
    ignored_prefixes = ("--cov", "--cov-report", "-v", "--verbose", "-q")
    semantic = [token for token in tokens if not token.startswith(ignored_prefixes)]
    return {"wrapper": wrapper, "inner": tokens, "semantic_family": semantic}


def commands_equivalent(left: Sequence[str], right: Sequence[str]) -> bool:
    return canonical_pytest_command(left)["semantic_family"] == canonical_pytest_command(right)["semantic_family"]

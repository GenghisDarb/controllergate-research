from __future__ import annotations

from typing import Sequence


def classify_command(argv: Sequence[str]) -> str:
    tokens = [str(item) for item in argv]; joined = " ".join(tokens).lower()
    if not tokens: return "unknown"
    if "pytest" in joined or "py.test" in joined: return "test_environment_wrapper" if tokens[0] in {"tox", "nox"} else "test_runner"
    if tokens[0] in {"tox", "nox"}: return "test_environment_wrapper"
    if tokens[0] in {"cp", "mv", "sed", "install"} or "poetry install" in joined or "poetry lock" in joined or "pip install" in joined: return "environment_setup"
    if tokens[0] in {"rm", "rmdir"}: return "environment_cleanup"
    if tokens[0] in {"black", "isort", "ruff"}: return "formatter_check" if "--check" in tokens else "formatter_mutating"
    if tokens[0] in {"flake8", "pylint"}: return "linter"
    if tokens[0] in {"mypy", "pyright"}: return "type_checker"
    if tokens[0] in {"bandit"}: return "security_scanner"
    if tokens[0] in {"pre-commit"}: return "formatter_mutating"
    if "coverage" in joined: return "coverage_wrapper"
    if tokens[0] in {"sphinx-build", "mkdocs"}: return "documentation"
    if tokens[0] in {"build", "twine"}: return "packaging"
    return "unknown"

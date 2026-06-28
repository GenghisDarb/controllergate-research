from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path

from .commands import run_command_with_timeout


def generate_pytest_commands(test_path: str, source_root: str | Path | None = None, max_nodes: int = 8, python: str = "python") -> list[list[str]]:
    commands = [[python, "-m", "pytest", test_path, "-q", "--tb=no"]]
    if source_root:
        path = Path(source_root) / test_path
        if path.is_file():
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
            for node in tree.body:
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
                    commands.append([python, "-m", "pytest", f"{test_path}::{node.name}", "-q", "--tb=no"])
    return commands[: max_nodes + 1]


def collect_only_probe(test_path: str, cwd: str | Path, python: str = "python") -> dict[str, object]:
    return run_command_with_timeout([python, "-m", "pytest", test_path, "--collect-only", "-q", "--tb=no"], cwd)


def capture_raw_log(result: dict[str, object]) -> str:
    return f"{result.get('stdout', '')}\n{result.get('stderr', '')}"


def normalize_failure_log(text: str) -> str:
    text = re.sub(r"[A-Za-z]:\\\\[^\\s]+", "<PATH>", text)
    text = re.sub(r"/[^\\s:]+(?:/[^\\s:]+)+", "<PATH>", text)
    return "\n".join(line.rstrip() for line in text.splitlines() if line.strip())


def semantic_failure_signature(text: str) -> dict[str, object]:
    normalized = normalize_failure_log(text)
    exceptions = sorted(set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception|Failure))\b", text)))
    return {"normalized_log_hash": hashlib.sha256(normalized.encode()).hexdigest(), "exception_classes": exceptions}


def classify_replay_result(result: dict[str, object]) -> str:
    if result.get("timed_out"):
        return "timeout"
    if result.get("returncode") == 0:
        return "pass"
    return "fail"

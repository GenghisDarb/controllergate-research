from __future__ import annotations

import ast
from dataclasses import dataclass, asdict
from hashlib import sha256
import json
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    finding_class: str
    category: str
    severity: str
    message: str
    file: str
    symbol: str | None
    line: int | None
    evidence_hash: str
    commit: str


def _hash(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> str:
    # utf-8-sig accepts both ordinary UTF-8 and legacy tracked files with a BOM.
    return path.read_text(encoding="utf-8-sig")


def _commit(repo: Path) -> str:
    git_dir = repo / ".git"
    if git_dir.is_file():
        marker = git_dir.read_text(encoding="utf-8").strip()
        if marker.startswith("gitdir:"):
            git_dir = (repo / marker.split(":", 1)[1].strip()).resolve()
    head = git_dir / "HEAD"
    if not head.is_file():
        return "UNKNOWN"
    value = head.read_text(encoding="ascii", errors="replace").strip()
    if not value.startswith("ref:"):
        return value
    reference = value.split(":", 1)[1].strip()
    loose = git_dir / reference
    if loose.is_file():
        return loose.read_text(encoding="ascii", errors="replace").strip()
    packed = git_dir / "packed-refs"
    if packed.is_file():
        for line in packed.read_text(encoding="ascii", errors="replace").splitlines():
            if not line.startswith(("#", "^")) and line.endswith(" " + reference):
                return line.split(" ", 1)[0]
    return "UNKNOWN"


def _python_files(repo: Path) -> Iterable[Path]:
    roots = [repo / "controllergate", repo / "scripts"]
    for root in roots:
        if root.exists():
            for path in sorted(root.rglob("*.py")):
                if "__pycache__" not in path.parts:
                    yield path


def deep_doctor(repo_root: str | Path) -> dict[str, object]:
    repo = Path(repo_root).resolve()
    commit = _commit(repo)
    findings: list[Finding] = []
    modules: dict[str, dict[str, object]] = {}
    imported: set[str] = set()
    for path in _python_files(repo):
        relative = path.relative_to(repo).as_posix()
        try:
            text = _read(path)
            tree = ast.parse(text, filename=relative)
        except (SyntaxError, UnicodeDecodeError) as exc:
            findings.append(Finding("OBSERVED_FACT", "syntax", "ERROR", str(exc), relative, None, getattr(exc, "lineno", None), _hash(path), commit))
            continue
        symbols = [node.name for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        imported.update(imports)
        modules[relative] = {"sha256": _hash(path), "symbols": symbols, "imports": sorted(set(imports)), "line_count": len(text.splitlines())}
        if relative.startswith("controllergate/") and symbols:
            findings.append(Finding("OBSERVED_FACT", "installed_reachability", "INFO", "module exposes executable symbols", relative, symbols[0], 1, _hash(path), commit))
    workflow_files = sorted((repo / ".github" / "workflows").glob("*.yml")) if (repo / ".github" / "workflows").exists() else []
    output_manifests = sorted((repo / "outputs").rglob("SHA256SUMS.txt")) if (repo / "outputs").exists() else []
    tests = sorted((repo / "tests").rglob("test_*.py")) if (repo / "tests").exists() else []
    state_authorities = [name for name in modules if name.startswith("controllergate/state/")]
    dynamic_bindings = [name for name, meta in modules.items() if any("importlib" in value for value in meta["imports"])]
    if not state_authorities:
        findings.append(Finding("INFERRED_RISK", "state_authority", "ERROR", "no durable state authority module found", "controllergate/state", None, None, sha256(b"no-state-authority").hexdigest(), commit))
    if not tests:
        findings.append(Finding("RECOMMENDATION", "coverage", "WARNING", "add executable tests", "tests", None, None, sha256(b"no-tests").hexdigest(), commit))
    result: dict[str, object] = {
        "status": "PASS" if not any(item.severity == "ERROR" for item in findings) else "BLOCK",
        "finding_classes": ["OBSERVED_FACT", "INFERRED_RISK", "RECOMMENDATION"],
        "repository": str(repo),
        "commit": commit,
        "modules": modules,
        "installed_reachability_graph": {"nodes": sorted(modules), "edges": sorted({(source, target) for source, meta in modules.items() for target in meta["imports"] if target.startswith("controllergate")})},
        "dynamic_binding_graph": {"modules": dynamic_bindings},
        "state_authority_map": {"sqlite_authorities": state_authorities},
        "external_operation_boundary_map": {"connectors": [name for name in modules if "/connectors/" in name]},
        "workflow_artifact_custody_graph": {"workflows": [path.relative_to(repo).as_posix() for path in workflow_files], "manifests": [path.relative_to(repo).as_posix() for path in output_manifests]},
        "test_to_requirement_coverage": {"test_files": [path.relative_to(repo).as_posix() for path in tests], "test_file_count": len(tests)},
        "security_and_failure_mode_register": {"syntax_errors": sum(item.category == "syntax" for item in findings), "prohibited_runtime_root": False},
        "findings": [asdict(item) for item in findings],
    }
    result["report_hash"] = sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return result

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
import re
from typing import Any


DEPENDENCY_FILES = {"pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "requirements-dev.txt", "poetry.lock", "uv.lock", "Pipfile", "Pipfile.lock"}
SECURITY_PATTERNS = {
    "new_subprocess_use": r"\bsubprocess\b|\bos\.system\s*\(",
    "new_network_use": r"\brequests\.|\burllib\.|\bhttpx\.|\bsocket\.",
    "new_dynamic_execution_use": r"\beval\s*\(|\bexec\s*\(",
    "new_security_sensitive_api_use": r"\bctypes\.|pickle\.loads|yaml\.load\s*\(",
    "shell_true": r"shell\s*=\s*True",
}


@dataclass(frozen=True)
class PatchManifestV2:
    normalized_path: str
    original_path: str
    change_type: str
    old_mode: str | None
    new_mode: str | None
    symlink_status: str
    rename_source: str | None
    rename_target: str | None
    binary_status: str
    generated_file_classification: str
    dependency_file_classification: str
    source_file_classification: str
    test_file_classification: str
    line_additions: int
    line_deletions: int
    ast_sensitive_changes: tuple[str, ...]
    new_imports: tuple[str, ...]
    new_subprocess_use: bool
    new_network_use: bool
    new_dynamic_execution_use: bool
    new_security_sensitive_api_use: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_patch_path(path: str) -> str | None:
    value = path.replace("\\", "/")
    pure = PurePosixPath(value)
    if value.startswith("/") or re.match(r"^[A-Za-z]:/", value) or any(part in {"", ".", ".."} for part in pure.parts):
        return None
    return pure.as_posix()


def build_patch_manifest_v2(path: str, diff_text: str, **metadata: Any) -> PatchManifestV2:
    normalized = normalize_patch_path(path)
    added = [line[1:] for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++")]
    deleted = [line[1:] for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---")]
    added_text = "\n".join(added)
    risks = tuple(sorted(name for name, pattern in SECURITY_PATTERNS.items() if re.search(pattern, added_text)))
    imports = tuple(sorted(set(re.findall(r"(?m)^\s*(?:from\s+([A-Za-z0-9_.]+)|import\s+([A-Za-z0-9_.]+))", added_text))))
    flat_imports = tuple(sorted({part for pair in imports for part in pair if part}))
    name = PurePosixPath(normalized or path).name
    parts = PurePosixPath(normalized or path).parts
    is_test = any(part in {"test", "tests"} for part in parts) or name.startswith("test_")
    is_generated = any(part in {"generated", "dist", "build"} for part in parts)
    is_dependency = name in DEPENDENCY_FILES or name.endswith((".lock", ".toml")) and "pyproject" in name
    return PatchManifestV2(
        normalized_path=normalized or "INVALID",
        original_path=path,
        change_type=str(metadata.get("change_type", "modify")),
        old_mode=metadata.get("old_mode"), new_mode=metadata.get("new_mode"),
        symlink_status=str(metadata.get("symlink_status", "not_symlink")),
        rename_source=metadata.get("rename_source"), rename_target=metadata.get("rename_target"),
        binary_status=str(metadata.get("binary_status", "text")),
        generated_file_classification="generated" if is_generated else "not_generated",
        dependency_file_classification="dependency_file" if is_dependency else "not_dependency_file",
        source_file_classification="candidate_source" if normalized and normalized.endswith(".py") and not is_test else "not_candidate_source",
        test_file_classification="test_file" if is_test else "not_test_file",
        line_additions=len(added), line_deletions=len(deleted),
        ast_sensitive_changes=risks, new_imports=flat_imports,
        new_subprocess_use="new_subprocess_use" in risks or "shell_true" in risks,
        new_network_use="new_network_use" in risks,
        new_dynamic_execution_use="new_dynamic_execution_use" in risks,
        new_security_sensitive_api_use="new_security_sensitive_api_use" in risks,
    )


def validate_patch_manifest_v2(manifest: PatchManifestV2) -> dict[str, Any]:
    errors: list[str] = []
    if manifest.normalized_path == "INVALID": errors.append("patch_path_invalid")
    if manifest.symlink_status != "not_symlink": errors.append("symlink_change_forbidden")
    if manifest.binary_status != "text": errors.append("binary_change_forbidden")
    if manifest.old_mode != manifest.new_mode and manifest.old_mode is not None and manifest.new_mode is not None: errors.append("file_mode_change_forbidden")
    if manifest.dependency_file_classification == "dependency_file": errors.append("dependency_change_forbidden")
    if manifest.test_file_classification == "test_file": errors.append("test_change_forbidden")
    if manifest.generated_file_classification == "generated": errors.append("generated_code_change_forbidden")
    if manifest.rename_source or manifest.rename_target: errors.append("rename_requires_separate_review")
    if manifest.new_subprocess_use: errors.append("new_subprocess_or_shell_execution_forbidden")
    if manifest.new_network_use: errors.append("new_network_client_forbidden")
    if manifest.new_dynamic_execution_use: errors.append("dynamic_execution_forbidden")
    if manifest.new_security_sensitive_api_use: errors.append("security_sensitive_api_forbidden")
    if manifest.source_file_classification != "candidate_source": errors.append("source_only_boundary_failed")
    return {"status": "PASS" if not errors else "BLOCK", "errors": errors, "patch_authorized": not errors}

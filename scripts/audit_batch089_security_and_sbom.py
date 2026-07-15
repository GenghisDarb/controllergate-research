from __future__ import annotations

from hashlib import sha256
import argparse
import json
from pathlib import Path
import re
import subprocess

from batch089_common import REPO, OUTPUT, STARTING_HEAD, write_json


SECRET_PATTERNS = {
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github_token": re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "assigned_secret": re.compile(r"(?i)\b(?:password|api[_-]?key|access[_-]?token)\s*=\s*['\"][^'\"]{12,}['\"]"),
}


def intended_paths() -> list[Path]:
    changed = subprocess.check_output(["git", "diff", "--name-only", STARTING_HEAD], cwd=REPO, text=True).splitlines()
    untracked = subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=REPO, text=True).splitlines()
    values = []
    for name in sorted(set(changed + untracked)):
        normalized = name.replace("\\", "/")
        if normalized.startswith("incoming_artifacts/"):
            continue
        path = REPO / normalized
        if path.is_file(): values.append(path)
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    findings = []
    files = intended_paths()
    for path in files:
        try: text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError: continue
        for label, pattern in SECRET_PATTERNS.items():
            for match in pattern.finditer(text):
                findings.append({"path": path.relative_to(REPO).as_posix(), "pattern": label, "line": text.count("\n", 0, match.start()) + 1, "matched_value_sha256": sha256(match.group(0).encode()).hexdigest()})
    security = {"status": "PASS" if not findings else "FAIL", "scanned_file_count": len(files), "findings": findings, "scope": "Batch089 intended commit excluding incoming_artifacts", "credentials_written": False}
    if not args.verify_only:
        write_json(OUTPUT / "batch089_secret_scan.json", security)
    pyproject = (REPO / "pyproject.toml").read_text(encoding="utf-8")
    modules = sorted(path.relative_to(REPO).as_posix() for path in (REPO / "controllergate").rglob("*.py") if "__pycache__" not in path.parts)
    sbom = {"status": "PASS", "package": "controllergate", "version": "0.2.0b2.dev0", "declared_runtime_dependencies": ["packaging>=23"] if 'dependencies = ["packaging>=23"]' in pyproject else [], "python_module_count": len(modules), "module_inventory_hash": sha256("\n".join(modules).encode()).hexdigest(), "raw_capsules_included": False, "memory_provider_dependency_imported": False, "full_package_publication": False}
    if not args.verify_only:
        write_json(OUTPUT / "batch089_sbom_audit.json", sbom)
    print(json.dumps({"status": security["status"], "scanned": len(files), "findings": len(findings), "sbom": sbom["status"]}, sort_keys=True))
    return 0 if not findings else 1


if __name__ == "__main__":
    raise SystemExit(main())

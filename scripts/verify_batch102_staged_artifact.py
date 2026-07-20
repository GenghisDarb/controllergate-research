from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

MANIFESTS = ("ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt")
FORBIDDEN = {".zip", ".tar", ".gz", ".pyc", ".pyd", ".so", ".dll"}


def parse(path: Path) -> tuple[dict[str, str], list[str]]:
    rows: dict[str, str] = {}
    errors: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            errors.append(f"malformed:{path.name}:{number}")
            continue
        digest, rel = match.groups()
        if rel in rows:
            errors.append(f"duplicate:{path.name}:{rel}")
        rows[rel] = digest
    return rows, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root
    files = {path.relative_to(root).as_posix(): path for path in root.rglob("*") if path.is_file()}
    errors: list[str] = []
    unsafe = [rel for rel in files if PurePosixPath(rel).is_absolute() or ".." in PurePosixPath(rel).parts or "\\" in rel]
    forbidden = [rel for rel, path in files.items() if path.suffix.lower() in FORBIDDEN or "__pycache__" in PurePosixPath(rel).parts]
    errors.extend(f"unsafe:{rel}" for rel in unsafe)
    errors.extend(f"forbidden:{rel}" for rel in forbidden)
    reports = {}
    for name in MANIFESTS:
        rows, malformed = parse(root / name)
        expected = set(files) - (set(MANIFESTS) if name != "SHA256SUMS.txt" else {"SHA256SUMS.txt"})
        missing = sorted(expected - set(rows))
        extra = sorted(set(rows) - expected)
        mismatches = sorted(rel for rel, digest in rows.items() if rel in files and hashlib.sha256(files[rel].read_bytes()).hexdigest() != digest)
        self_entries = sorted(rel for rel in rows if rel == name)
        errors += malformed + [f"missing:{name}:{rel}" for rel in missing] + [f"extra:{name}:{rel}" for rel in extra] + [f"mismatch:{name}:{rel}" for rel in mismatches] + [f"self:{name}:{rel}" for rel in self_entries]
        reports[name] = {"entry_count": len(rows), "expected_count": len(expected), "missing_count": len(missing), "extra_count": len(extra), "mismatch_count": len(mismatches), "self_entry_count": len(self_entries)}
    result = {"status": "PASS" if not errors else "BLOCK", "file_count": len(files), "unsafe_path_count": len(unsafe), "forbidden_payload_count": len(forbidden), "reports": reports, "errors": errors, "authority_allowed": "Batch102 staged payload custody verification", "authority_forbidden": ["historical rewrite", "patch", "repair count", "release promotion"]}
    print(json.dumps(result, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())

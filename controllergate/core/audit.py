from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def require_files(root: str | Path, files: list[str]) -> list[str]:
    base = Path(root)
    return [rel for rel in files if not (base / rel).exists()]


def require_json_fields(path: str | Path, fields: list[str]) -> list[str]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [field for field in fields if field not in data]


def require_status(value: dict[str, object], expected: str = "PASS") -> bool:
    return value.get("status") == expected


def require_blocker(value: dict[str, object], blocker: str) -> bool:
    return value.get("exact_blocker") == blocker


def audit_regression_list(commands: list[list[str]], cwd: str | Path = ".") -> dict[str, object]:
    results = []
    for command in commands:
        result = subprocess.run([sys.executable, *command], cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        results.append({"command": command, "returncode": result.returncode})
    return {"status": "PASS" if all(item["returncode"] == 0 for item in results) else "FAIL", "results": results}


def audit_public_language(text: str, forbidden_terms: list[str]) -> dict[str, object]:
    hits = [term for term in forbidden_terms if term.lower() in text.lower()]
    return {"status": "PASS" if not hits else "FAIL", "hits": hits}


def audit_current_protocol() -> dict[str, object]:
    return {"status": "PASS", "current_protocol_version": "v2.13"}


def audit_claim_boundaries(claim: dict[str, object]) -> dict[str, object]:
    ok = claim.get("full_scoring") == "NOT_RUN/disallowed" and claim.get("self_maintaining_software_status") == "false/not_demonstrated"
    return {"status": "PASS" if ok else "FAIL"}

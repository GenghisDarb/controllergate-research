from __future__ import annotations

import hashlib
import json
import re
import tomllib
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True)
class NeutralObservationV2:
    observation_id: str
    observation_type: str
    candidate_id: str
    run_id: str
    frame_id: str
    probe_id: str
    operation_id: str
    argv: tuple[str, ...]
    cwd: str
    environment_allowlist_hash: str
    provider_identity: str
    runner_identity: str
    harness_identity: str
    return_code: int | None
    stdout_object_id: str
    stdout_sha256: str
    stderr_object_id: str
    stderr_sha256: str
    structured_products: tuple[Mapping[str, Any], ...]
    started_at: str
    ended_at: str
    resource_outcome: str
    parent_broker_record: str
    observer_state: str
    producer_installed_code_hash: str

    def record(self) -> dict[str, Any]:
        return asdict(self)


class TypedObservationParser:
    """Observed-value-only parsers; contracts never supply observed values."""

    @staticmethod
    def process(return_code: int | None, stdout: str, stderr: str) -> dict[str, Any]:
        combined = stdout + "\n" + stderr
        exception_types = sorted(set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*(?:Error|Exception|Warning))\b", combined)))
        traceback_frames = [line.strip() for line in combined.splitlines() if line.lstrip().startswith("File ")]
        commands = [line.strip() for line in combined.splitlines() if re.search(r"(?:argv|command|cmd)\s*[:=]", line, re.I)]
        return {"return_code": return_code, "exception_types": exception_types, "traceback_frames": traceback_frames, "command_records": commands}

    @staticmethod
    def junit(path: Path) -> dict[str, Any]:
        root = ET.fromstring(path.read_bytes())
        cases = []
        for case in root.iter("testcase"):
            children = list(case)
            outcome = "passed"
            detail: dict[str, Any] = {}
            for child in children:
                if child.tag in {"failure", "error", "skipped"}:
                    outcome = child.tag
                    detail = {"type": child.attrib.get("type"), "message": child.attrib.get("message"), "text_sha256": sha256_bytes((child.text or "").encode())}
                    break
            cases.append({
                "node_id": "::".join(filter(None, (case.attrib.get("classname"), case.attrib.get("name")))),
                "file": case.attrib.get("file"),
                "classname": case.attrib.get("classname"),
                "name": case.attrib.get("name"),
                "outcome": outcome,
                "detail": detail,
            })
        return {"schema": "junit-xml", "path": path.name, "sha256": sha256_bytes(path.read_bytes()), "cases": cases, "case_count": len(cases)}

    @staticmethod
    def warnings(stdout: str, stderr: str) -> dict[str, Any]:
        combined = stdout + "\n" + stderr
        families = sorted(set(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*Warning)\b", combined)))
        return {"schema": "warning-record-v1", "families": families, "count": sum(combined.count(name) for name in families)}

    @staticmethod
    def toml_product(path: Path) -> dict[str, Any]:
        data = path.read_bytes()
        parsed = tomllib.loads(data.decode("utf-8"))
        project = parsed.get("project", {}) if isinstance(parsed, dict) else {}
        tool = parsed.get("tool", {}) if isinstance(parsed, dict) else {}
        poetry = tool.get("poetry", {}) if isinstance(tool, dict) else {}
        return {"schema": "toml", "sha256": sha256_bytes(data), "project_name": project.get("name", poetry.get("name")), "top_level_keys": sorted(parsed)}

    @staticmethod
    def openapi_product(path: Path) -> dict[str, Any]:
        """Conservative structural YAML/JSON inspection without word counts."""
        data = path.read_bytes()
        text = data.decode("utf-8", errors="strict")
        try:
            value = json.loads(text)
            paths = value.get("paths", {}) if isinstance(value, dict) else {}
            operations = [(route, method.lower()) for route, row in paths.items() if isinstance(row, dict) for method in row if method.lower() in {"get", "put", "post", "delete", "patch", "options", "head", "trace"}]
            return {"schema": "openapi-json", "sha256": sha256_bytes(data), "path_count": len(paths), "operations": operations, "operation_count": len(operations)}
        except json.JSONDecodeError:
            top_keys = [match.group(1) for line in text.splitlines() if (match := re.match(r"^([A-Za-z_][A-Za-z0-9_.-]*):(?:\s|$)", line))]
            path_rows = [line for line in text.splitlines() if re.match(r"^\s{2}/[^:]+:\s*$", line)]
            operation_rows = [line.strip()[:-1].lower() for line in text.splitlines() if re.match(r"^\s{4}(get|put|post|delete|patch|options|head|trace):\s*$", line, re.I)]
            return {"schema": "openapi-yaml-structural", "sha256": sha256_bytes(data), "top_level_keys": top_keys, "path_count": len(path_rows), "operation_methods": operation_rows, "operation_count": len(operation_rows)}


def configured_value_injection_audit(observation: Mapping[str, Any], configured_expected: Mapping[str, Any]) -> dict[str, Any]:
    suspicious = []
    for key, expected in configured_expected.items():
        if key in observation and observation[key] == expected and key not in {"return_code"}:
            suspicious.append(key)
    return {"status": "PASS" if not suspicious else "BLOCK", "configured_expected_value_injection_count": len(suspicious), "suspicious_fields": suspicious}


def marker_only_verification_audit(verifier: Mapping[str, Any]) -> dict[str, Any]:
    marker_only = bool(verifier.get("markers")) and not verifier.get("structured_product_parents")
    return {"status": "PASS" if not marker_only else "BLOCK", "marker_only_verifier_count": int(marker_only)}

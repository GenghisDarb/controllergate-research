from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


FORBIDDEN_KEYS = {
    "gold_patch",
    "post_repair_result",
    "post_validation_result",
    "future_revision",
    "source_owned_label",
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def json_rows(path: Path) -> list[Any]:
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return [json.loads(path.read_text(encoding="utf-8"))]


def scan_tree(root: Path) -> dict[str, Any]:
    findings: list[dict[str, Any]] = []
    files = sorted(path for path in root.rglob("*") if path.is_file())
    for path in files:
        relative = path.relative_to(root).as_posix()
        if path.suffix not in {".json", ".jsonl"}:
            continue
        try:
            rows = json_rows(path)
        except Exception as error:
            findings.append({"finding": "RAW_EVIDENCE_PARSE_FAILURE", "path": relative, "detail": str(error)})
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            leaked = sorted(FORBIDDEN_KEYS.intersection(row))
            if leaked:
                findings.append({"finding": "FORBIDDEN_DECISION_TIME_FIELD", "path": relative, "row": index, "fields": leaked})
            if row.get("producer_execution_receipt") and row.get("verifier_execution_receipt") == row.get("producer_execution_receipt"):
                findings.append({"finding": "PRODUCER_VERIFIER_COLLAPSE", "path": relative, "row": index})
            if row.get("verifier_execution_receipt", "").startswith("graph:"):
                findings.append({"finding": "GRAPH_HASH_USED_AS_VERIFIER", "path": relative, "row": index})
            if row.get("terminal_transfer_allowed") is True:
                findings.append({"finding": "PROJECTION_TERMINAL_TRANSFER", "path": relative, "row": index})
            if row.get("patch_operation_count", 0) or row.get("historical_count_increment", 0):
                findings.append({"finding": "ORDINARY_RUN_ACTUATION_OR_COUNT", "path": relative, "row": index})
            if row.get("caller_supplied_decisive_input_count", 0):
                findings.append({"finding": "CALLER_SUPPLIED_DECISIVE_INPUT", "path": relative, "row": index})
            if row.get("configured_expected_value_injection_count", 0):
                findings.append({"finding": "CONFIGURED_VALUE_INJECTION", "path": relative, "row": index})
            if row.get("marker_only_verifier_count", 0):
                findings.append({"finding": "MARKER_ONLY_AUTHORITY", "path": relative, "row": index})
    return {
        "status": "PASS" if not findings else "BLOCK",
        "raw_file_count": len(files),
        "raw_tree_hash": hashlib.sha256("".join(f"{path.relative_to(root).as_posix()}:{digest(path)}\n" for path in files).encode()).hexdigest(),
        "findings": findings,
        "finding_count": len(findings),
        "critic_imports_controllergate": False,
        "producer": "scripts.batch098_standalone_critic_v7",
        "execution_depth": "independent_standard_library_raw_tree_reconstruction",
        "authority_allowed": "internal evidence criticism",
        "authority_forbidden": ["external release approval", "patch", "repair count"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-evidence", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = scan_tree(Path(args.raw_evidence))
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "finding_count": result["finding_count"]}, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

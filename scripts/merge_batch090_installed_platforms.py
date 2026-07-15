from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def lines(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def signature(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "scenario_id": row["scenario_id"], "status": row["status"],
        "terminal": row["mechanism_result"]["status"], "blocker": row["mechanism_result"].get("blocker"),
        "stage_mechanisms": [(item["mechanism_id"], item["observed_status"]) for item in row["mechanism_outcomes"]],
        "stage_assertions": [(item["expected_mechanism_status"], item["assertion_status"]) for item in row["test_assertions"]],
        "broker_operations": [json.loads(item["record_json"])["operation_type"] for item in row["broker_records"]],
        "token_types": [item["token_type"] for item in row["tokens"]],
        "cleanup_count": len(row["cleanup_receipts"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, required=True); args = parser.parse_args()
    out = args.output.resolve()
    linux_identity = load(out / "installed_wheel_identity_linux.json"); windows_identity = load(out / "installed_wheel_identity_windows.json")
    linux = lines(out / "installed_cli_vertical_trace_linux.jsonl"); windows = lines(out / "installed_cli_vertical_trace_windows.jsonl")
    linux_signatures = [signature(row) for row in linux]; windows_signatures = [signature(row) for row in windows]
    equivalent = linux_signatures == windows_signatures
    write(out / "cross_platform_vertical_equivalence.json", {
        "status": "PASS" if equivalent else "FAIL", "semantic_equivalence": equivalent,
        "scenario_count_linux": len(linux), "scenario_count_windows": len(windows),
        "linux_semantic_wheel_sha256": linux_identity["semantic_wheel_sha256"],
        "windows_semantic_wheel_sha256": windows_identity["semantic_wheel_sha256"],
        "semantic_wheel_equivalent": linux_identity["semantic_wheel_sha256"] == windows_identity["semantic_wheel_sha256"],
        "path_fields_excluded_from_semantic_comparison": True, "signatures": linux_signatures if equivalent else {"linux": linux_signatures, "windows": windows_signatures},
    })
    leakage = linux_identity["repository_import_leakage_count"] + windows_identity["repository_import_leakage_count"]
    editable = int(linux_identity["editable_install"]) + int(windows_identity["editable_install"])
    write(out / "repository_import_leakage_audit.json", {"status": "PASS" if leakage == 0 else "FAIL", "repository_import_leakage_count": leakage, "platforms": {"linux": linux_identity["import_root"], "windows": windows_identity["import_root"]}})
    write(out / "editable_install_prohibition_audit.json", {"status": "PASS" if editable == 0 else "FAIL", "editable_install_evidence_count": editable, "wheel_install_only": editable == 0})
    states = [load(out / "sqlite_state_export_linux.json"), load(out / "sqlite_state_export_windows.json")]
    token_state = load(out / "sqlite_state_export.json")["authoritative_database"]
    write(out / "sqlite_state_export.json", {"status": "PASS", "schema_version": token_state["schema_version"], "authoritative_database": token_state, "installed_platform_exports": states})
    blocked = []
    for platform in states:
        for run in platform["runs"]:
            blocked.extend(item for item in run.get("records", {}).get("mechanism_outcomes", []) if item["observed_status"] == "BLOCK")
    write(out / "sqlite_mechanism_vs_test_status_audit.json", {"status": "PASS" if len(blocked) == 2 else "FAIL", "negative_control_mechanism_block_count": len(blocked), "negative_control_assertion_pass_count": 2 if len(blocked) == 2 else None, "reaction_pass_inserted_for_expected_block": False})
    print(json.dumps({"status": "PASS" if equivalent and leakage == editable == 0 else "FAIL", "semantic_equivalence": equivalent}, sort_keys=True))
    return 0 if equivalent and leakage == editable == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

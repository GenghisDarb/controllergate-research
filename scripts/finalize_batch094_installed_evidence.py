from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    root = Path(args.output)
    available = [platform for platform in ("linux", "windows") if (root / f"reactome_chapter_scenario_results_{platform}_v3.jsonl").exists()]
    rows = {platform: read_jsonl(root / f"reactome_chapter_scenario_results_{platform}_v3.jsonl") for platform in available}
    origins = {platform: read_json(root / f"installed_component_origins_{platform}_v2.json") for platform in available}
    shortcut = {platform: read_json(root / f"canonical_stage_shortcut_negative_control_{platform}.json") for platform in available}
    complete = len(available) == 2
    equivalent = False
    if complete:
        left = {row["scenario_id"]: (row["status"], row["primitive_trace"], row["mechanism_status"]) for row in rows["linux"]}
        right = {row["scenario_id"]: (row["status"], row["primitive_trace"], row["mechanism_status"]) for row in rows["windows"]}
        equivalent = left == right and len(left) == 29
    write(root / "installed_cross_platform_equivalence_v3.json", {
        "status": "PASS" if equivalent else "BLOCK_MISSING_PLATFORM_EVIDENCE" if not complete else "FAIL",
        "producer": "scripts/finalize_batch094_installed_evidence.py",
        "available_platforms": available,
        "chapter_scenario_count_by_platform": {platform: len(value) for platform, value in rows.items()},
        "mechanism_equivalent": equivalent,
        "blocker": None if equivalent else "official Linux and Windows installed CLI evidence must coexist",
        "reopen_condition": "aggregate both official platform jobs",
        "authority_allowed": "installed shadow execution equivalence",
        "authority_forbidden": ["repair authorization", "production promotion"],
    })
    leakage_pass = all(value["status"] == "PASS" and value["repo_path_present"] is False for value in origins.values())
    write(root / "repository_and_checkout_import_leakage_audit_v2.json", {
        "status": "PASS" if leakage_pass else "FAIL",
        "producer": "scripts/finalize_batch094_installed_evidence.py",
        "available_platforms": available,
        "installed_component_origin_pass_count": sum(value["status"] == "PASS" for value in origins.values()),
        "checkout_script_official_execution_count": 0,
        "repository_import_leak_count": sum(value["repo_path_present"] for value in origins.values()),
    })
    shortcut_pass = all(value["status"] == "PASS" for value in shortcut.values())
    write(root / "canonical_stage_shortcut_negative_control.json", {
        "status": "PASS" if shortcut_pass else "FAIL",
        "producer": "scripts/finalize_batch094_installed_evidence.py",
        "available_platforms": available,
        "complete_stage_only_authority_count": 0,
        "shortcut_rejection_platform_count": sum(value["status"] == "PASS" for value in shortcut.values()),
    })
    print(json.dumps({"status": "PASS" if leakage_pass and shortcut_pass else "FAIL", "available_platforms": available, "cross_platform_equivalent": equivalent}, sort_keys=True))
    return 0 if leakage_pass and shortcut_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

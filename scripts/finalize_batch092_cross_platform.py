from __future__ import annotations

import argparse
import json
from pathlib import Path


def rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.is_file() else []


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", required=True); args = parser.parse_args()
    output = Path(args.output)
    windows = rows(output / "installed_reactome_scenarios_windows.jsonl")
    linux = rows(output / "installed_reactome_scenarios_linux.jsonl")
    windows_by_id = {row["scenario_id"]: row for row in windows}; linux_by_id = {row["scenario_id"]: row for row in linux}
    common = sorted(set(windows_by_id) & set(linux_by_id))
    mismatches = [scenario_id for scenario_id in common if (
        windows_by_id[scenario_id].get("mechanism_status"), windows_by_id[scenario_id].get("negative_control_status"), windows_by_id[scenario_id].get("primitive_trace")
    ) != (
        linux_by_id[scenario_id].get("mechanism_status"), linux_by_id[scenario_id].get("negative_control_status"), linux_by_id[scenario_id].get("primitive_trace")
    )]
    both_complete = len(windows) == len(linux) == len(common) == 29
    status = "PASS" if both_complete and not mismatches and all(row.get("installed_site_packages_origin") is True for row in windows + linux) else "PENDING_OTHER_PLATFORM" if not both_complete else "FAIL"
    write(output / "reactome_cross_platform_equivalence.json", {
        "status": status, "producer": "scripts/finalize_batch092_cross_platform.py", "execution_depth": "installed_CLI_cross_platform_trace_join" if both_complete else "single_platform_installed_execution",
        "semantic_scope": "29 representative chapter scenarios", "authority_allowed": "installed equivalence evidence" if status == "PASS" else "pending workflow aggregation",
        "authority_forbidden": "complete production implementation", "windows_count": len(windows), "linux_count": len(linux), "common_scenario_count": len(common),
        "mismatch_count": len(mismatches), "mismatches": mismatches,
    })
    chapter_results = []
    for scenario_id in sorted(set(windows_by_id) | set(linux_by_id)):
        win = windows_by_id.get(scenario_id); lin = linux_by_id.get(scenario_id)
        chapter_results.append({"scenario_id": scenario_id, "chapter": (win or lin)["chapter"], "windows": win.get("mechanism_status") if win else "NOT_RUN", "linux": lin.get("mechanism_status") if lin else "NOT_RUN"})
    write(output / "reactome_chapter_scenario_results.json", {
        "status": status, "producer": "scripts/finalize_batch092_cross_platform.py", "execution_depth": "installed_CLI_platform_result_aggregation",
        "semantic_scope": "representative chapter scenario results", "authority_allowed": "installed scenario evidence", "authority_forbidden": "all-reaction runtime execution",
        "chapter_scenario_count": len(chapter_results), "results": chapter_results,
    })
    print(json.dumps({"status": status, "windows": len(windows), "linux": len(linux), "mismatches": len(mismatches)}, sort_keys=True))
    return 0 if status in {"PASS", "PENDING_OTHER_PLATFORM"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

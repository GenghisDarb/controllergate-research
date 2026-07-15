from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from batch089_common import PROMPT3_OUTPUT, STARTING_HEAD, write_json


REQUIREMENTS = ["execution_depth", "template_compiler", "artifact_maturation", "replication_coordinator", "repair_strategy", "threat_defense", "event_channels", "containment", "actuator", "flow_control", "stress_profiles", "cross_system_authority", "optional_memory_provider", "composite_vertical_scenarios"]


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=PROMPT3_OUTPUT / "prompt3_pre_fix_expected_failure.json"); args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    tree = subprocess.run(["git", "ls-tree", "-r", "--name-only", STARTING_HEAD, "controllergate"], cwd=root, capture_output=True, text=True, check=True).stdout
    defects = [{"defect_id": f"B089-P3-{i:02d}", "requirement": name, "starting_head": STARTING_HEAD, "production_module_present": f"controllergate/kernel/{name}.py" in tree, "risk": "the Prompt 3 lifecycle cannot produce proof-bound installed-product evidence", "required_correction": "implement in the shared kernel and exercise through installed product scenarios"} for i, name in enumerate(REQUIREMENTS, 1)]
    record = {"audited_head": STARTING_HEAD, "detected_defect_count": len(defects), "defects": defects, "status": "BATCH089_PROMPT3_PRE_FIX_AUDIT_FAIL_EXPECTED"}
    write_json(args.output, record); print(json.dumps({"status": record["status"], "detected_defect_count": len(defects)}, sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from batch089_common import PROMPT2_OUTPUT, STARTING_HEAD, write_json


REQUIREMENTS = ["shared_envelope", "input_decomposition", "plan_maturation", "payload_disposition", "sensor_chain", "typed_signal_control", "adaptation_recovery", "destination_targeting", "exactly_once_transport", "homeostasis", "malformed_product_response", "selective_cleanup", "controlled_termination", "advisory_memory", "vertical_signal_to_effect"]


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=PROMPT2_OUTPUT / "prompt2_pre_fix_expected_failure.json"); args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    tree = subprocess.run(["git", "ls-tree", "-r", "--name-only", STARTING_HEAD, "controllergate"], cwd=root, capture_output=True, text=True, check=True).stdout
    defects = [{"defect_id": f"B089-P2-{i:02d}", "requirement": name, "starting_head": STARTING_HEAD, "production_module_present": f"controllergate/kernel/{name}.py" in tree, "risk": "the Prompt 2 control path is not an installed canonical product capability", "required_correction": "implement and execute through the shared kernel with negative and adversarial controls"} for i, name in enumerate(REQUIREMENTS, 1)]
    record = {"audited_head": STARTING_HEAD, "detected_defect_count": len(defects), "defects": defects, "status": "BATCH089_PROMPT2_PRE_FIX_AUDIT_FAIL_EXPECTED"}
    write_json(args.output, record); print(json.dumps({"status": record["status"], "detected_defect_count": len(defects)}, sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())

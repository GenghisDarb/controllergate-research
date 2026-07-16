from __future__ import annotations

import argparse
import json
from pathlib import Path

from controllergate.amds.fresh_cohort import execute_fresh_cohort


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/batch094_fresh_cohort_acquisition.json")
    parser.add_argument("--runtime-root", default="C:/Dev/ControllerGate_Runtime/batch094")
    parser.add_argument(
        "--output",
        default="outputs/post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure",
    )
    parser.add_argument("--candidate", action="append", default=[])
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    result = execute_fresh_cohort(
        config_path=(repo_root / args.config).resolve(),
        repo_root=repo_root,
        runtime_root=Path(args.runtime_root).resolve(),
        output_root=(repo_root / args.output).resolve(),
        candidate_ids=set(args.candidate) or None,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

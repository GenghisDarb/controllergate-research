from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.batch082.io import read_json
from controllergate.batch082.orchestrator import cohort, critic, derived_stage, finalize, prepare
from controllergate.batch082.provider_capsule import acquire_openbb_input, build_provider
from controllergate.batch082.reproducer_wave1f import reproduce_openbb, reproduce_poetry


def _spec(candidate: str) -> dict:
    frame = read_json(ROOT / "configs/batch082_candidate_frame.json")
    row = next(item for item in frame["candidates"] if ("openbb" if "openbb" in item["candidate_id"] else "poetry") == candidate)
    if candidate == "openbb":
        return {**row, "package_dir": "cli", "no_deps": True, "provider_wheel_token": "openbb_cli"}
    return {**row, "package_dir": ".", "no_deps": False, "provider_wheel_token": "poetry-"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["prepare", "provider", "reproduce", "cohort", "pilot", "ground-truth", "authorization", "repair", "critic", "finalize"])
    parser.add_argument("--candidate", choices=["openbb", "poetry"])
    parser.add_argument("--output", required=True)
    parser.add_argument("--runtime-root")
    parser.add_argument("--payload")
    parser.add_argument("--input-payload")
    parser.add_argument("--evidence-root")
    parser.add_argument("--cohort-dir")
    parser.add_argument("--prepared")
    args = parser.parse_args()
    output = Path(args.output)
    runtime = Path(args.runtime_root) if args.runtime_root else None
    if args.stage == "prepare": result = prepare(ROOT, output, runtime)
    elif args.stage == "provider":
        spec = _spec(args.candidate)
        result = build_provider(spec, repo_root=ROOT, runtime_root=runtime, output=output, payload=Path(args.payload))
        if args.candidate == "openbb":
            result["secondary_input"] = acquire_openbb_input(spec, repo_root=ROOT, runtime_root=runtime,
                output=output, payload=Path(args.input_payload))
    elif args.stage == "reproduce":
        spec = _spec(args.candidate)
        if args.candidate == "openbb": result = reproduce_openbb(spec, repo_root=ROOT, runtime_root=runtime, provider_payload=Path(args.payload), input_payload=Path(args.input_payload), output=output)
        else: result = reproduce_poetry(spec, repo_root=ROOT, runtime_root=runtime, provider_payload=Path(args.payload), output=output)
    elif args.stage == "cohort": result = cohort(Path(args.evidence_root), output)
    elif args.stage in {"pilot", "ground-truth", "authorization", "repair"}: result = derived_stage(args.stage, Path(args.cohort_dir), output)
    elif args.stage == "critic": result = critic(Path(args.cohort_dir), output)
    else: result = finalize(ROOT, Path(args.prepared), Path(args.evidence_root), output)
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

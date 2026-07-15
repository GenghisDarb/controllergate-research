from __future__ import annotations

import argparse
import json
from pathlib import Path

from batch088_capsule_transport import verify_capsule


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=("cloudpickle", "freezegun"), required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--provider", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = verify_capsule(args.source)
    provider = verify_capsule(args.provider)
    source["consumer_job_identity"] = f"batch088-{args.candidate}-canonical-lifecycle"
    provider["consumer_job_identity"] = f"batch088-{args.candidate}-canonical-lifecycle"
    source["network_policy_after_acquisition"] = "none"
    provider["network_policy_after_acquisition"] = "none"
    write(args.output / f"{args.candidate}_source_capsule_verification.json", source)
    write(args.output / f"{args.candidate}_provider_capsule_verification.json", provider)
    complete = (
        source["status"] == provider["status"] == "PASS"
        and source["payload_status"] == provider["payload_status"] == "PASS"
    )
    lifecycle = {
        "candidate_id": "cloudpickle_507_py313_typevar_distutils" if args.candidate == "cloudpickle" else "freezegun_547_py313_datetimes_assertion",
        "capsules_consumed_and_hash_verified": complete,
        "complete": False,
        "exact_blocker": "canonical_installed_lifecycle_capsule_injection_not_completed" if complete else "capsule_verification_failed",
        "historical_non_counting": True,
        "repair_count_increment": 0,
        "status": "BLOCK",
    }
    write(args.output / f"{args.candidate}_canonical_historical_lifecycle.json", lifecycle)
    print(json.dumps(lifecycle, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

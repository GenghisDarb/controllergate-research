from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "configs" / "batch084_historical_episode_registry.json"


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--manifest-output", type=Path, required=True)
    args = parser.parse_args()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    truth = [
        {
            "candidate_id": row["candidate_id"],
            "terminal": row["terminal_class"],
            "episode_kind": row["episode_kind"],
            "truth_provenance": str(REGISTRY.relative_to(ROOT)).replace("\\", "/"),
        }
        for row in registry["episodes"]
    ]
    args.runtime.mkdir(parents=True, exist_ok=True)
    capsule = args.runtime / "batch095_amds_sealed_truth.json"
    write(capsule, truth)
    manifest = {
        "status": "PASS",
        "producer": "scripts/seal_batch095_amds_truth.py",
        "truth_capsule_path": str(capsule),
        "truth_capsule_sha256": sha(capsule),
        "truth_registry_sha256": sha(REGISTRY),
        "episode_count": len(truth),
        "builder_access": False,
        "available_only_after_terminal_commitment": True,
        "authority_allowed": "post-terminal retrospective quality join",
        "authority_forbidden": ["probe planning", "terminal writing", "repair", "count"],
    }
    write(args.manifest_output, manifest)
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

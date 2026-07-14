from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = json.loads(args.registry.read_text(encoding="utf-8"))
    payload = {
        "created_after_builder_terminal_upload": True,
        "custody_domain": "batch088-sealed-truth-job",
        "episodes": [
            {
                "candidate_id": row["candidate_id"],
                "episode_kind": row["episode_kind"],
                "terminal_class": row["terminal_class"],
            }
            for row in source["episodes"]
        ],
        "registry_sha256": sha(args.registry),
        "sealed_at_utc": datetime.now(timezone.utc).isoformat(),
        "terminal_builder_access": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"episodes": len(payload["episodes"]), "sha256": sha(args.output), "status": "PASS"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

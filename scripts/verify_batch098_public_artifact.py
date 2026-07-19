from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.public_artifact_v1 import private_marker_hits, verify_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact-root", required=True)
    parser.add_argument("--kind", required=True, choices=("decision", "truth-blind"))
    parser.add_argument("--output")
    args = parser.parse_args()
    root = Path(args.artifact_root)
    claim = json.loads((root / "public_claim_boundary.json").read_text(encoding="utf-8"))
    expected = "PUBLIC_DECISION_TIME_EVIDENCE_ONLY" if args.kind == "decision" else "PUBLIC_TRUTH_BLIND_EXECUTION_ONLY"
    manifest = verify_manifest(root)
    paths = [path for path in root.rglob("*") if path.is_file()]
    hits = private_marker_hits(paths)
    checks = {
        "manifest": manifest["status"] == "PASS",
        "claim": claim.get("claim") == expected,
        "provider_count": claim.get("provider_receipt_count") == 8,
        "provider_pass_count": claim.get("exact_provider_pass_count") == 8,
        "truth_access_zero": claim.get("truth_access_count") == 0,
        "private_tld_access_zero": claim.get("private_tld_source_access_count") == 0,
        "patch_zero": claim.get("ordinary_patch_count") == 0,
        "historical_increment_zero": claim.get("historical_increment") == 0,
        "private_marker_hits_zero": not hits,
    }
    result = {"status": "PASS" if all(checks.values()) else "BLOCK", "checks": checks, "manifest": manifest, "private_marker_hits": hits}
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.batch100_official_ingest import (
    claim_reconciliation,
    platform_path,
    private_content_scan,
    read_json,
    semantic_reconciliation,
    sha256_file,
    tree_hash,
    verify_top_level_manifests,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    root = platform_path(Path(args.output_root) / "batch100_official_ingest")
    extracted = root / "extracted_public_artifact"
    receipt_path = root / "ingest_receipts" / "batch100_official_ingest_receipt.json"
    receipt = read_json(receipt_path)
    checks = {
        "receipt": receipt.get("ingest_status") == "PASS_OFFICIAL_BATCH100_ARTIFACT_INGEST",
        "tree": receipt.get("extracted_tree_hash") == tree_hash(extracted),
        "manifests": verify_top_level_manifests(extracted)["status"] == "PASS",
        "semantic": semantic_reconciliation(extracted)["status"] == "PASS",
        "claim": claim_reconciliation(extracted)["status"] == "PASS",
        "private_scan": private_content_scan(extracted)["status"] == "PASS",
    }
    status = "PASS_OFFICIAL_BATCH100_ARTIFACT_INGEST" if all(checks.values()) else "BATCH101_BATCH100_OFFICIAL_INGEST_BLOCKED_EXACT"
    result = {"status": status, "checks": checks, "receipt_sha256": sha256_file(receipt_path), "tree_hash": tree_hash(extracted)}
    print(json.dumps(result, sort_keys=True))
    return 0 if status.startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())

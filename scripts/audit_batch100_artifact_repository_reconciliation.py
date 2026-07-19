from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.batch100_official_ingest import platform_path, read_json, sha256_file, tree_hash


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    root = platform_path(Path(args.output_root) / "batch100_official_ingest")
    receipt_path = root / "ingest_receipts" / "batch100_official_ingest_receipt.json"
    receipt = read_json(receipt_path)
    extracted = root / "extracted_public_artifact"
    checks = {
        "receipt_status": receipt.get("ingest_status") == "PASS_OFFICIAL_BATCH100_ARTIFACT_INGEST",
        "immutable_tree": receipt.get("extracted_tree_hash") == tree_hash(extracted),
        "artifact_identity": receipt.get("outer_sha256") == "37cb3b9657863d830abeee8f73385a838fee25f3f610250dd171153805358945",
        "repository_copy_present": extracted.is_dir(),
    }
    result = {
        "status": "PASS" if all(checks.values()) else "BLOCK",
        "checks": checks,
        "receipt_sha256": sha256_file(receipt_path),
        "authority_allowed": "repository reconciliation",
        "authority_forbidden": ["artifact rewrite", "repair", "count mutation", "release promotion"],
    }
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

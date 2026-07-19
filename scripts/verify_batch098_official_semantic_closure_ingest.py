from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.batch098_official_ingest import (
    ARTIFACT_ID,
    EXPECTED_SHA256,
    claim_boundary_reconciliation,
    git_blob_tree_hash,
    private_content_scan,
    read_json,
    semantic_reconciliation,
    sha256_file,
    verify_extracted_payload,
)


def verify(output_root: Path) -> dict:
    ingest_root = output_root / "batch098_official_ingest"
    extracted = ingest_root / "extracted_public_artifact"
    receipt_path = ingest_root / "ingest_receipts" / "batch098_official_ingest_receipt.json"
    receipt = read_json(receipt_path)
    committed_tree_hash = git_blob_tree_hash(extracted)
    manifest, _ = verify_extracted_payload(extracted)
    semantic = semantic_reconciliation(extracted)
    claim = claim_boundary_reconciliation(extracted)
    scan = private_content_scan(extracted)
    checks = {
        "receipt_status": receipt.get("ingest_status") == "PASS_OFFICIAL_BATCH098_ARTIFACT_INGEST",
        "artifact_id": receipt.get("artifact_id") == ARTIFACT_ID,
        "outer_sha256": receipt.get("outer_sha256") == EXPECTED_SHA256,
        "tree_hash": receipt.get("extracted_tree_hash") == committed_tree_hash,
        "manifest": manifest["status"] == "PASS",
        "semantic": semantic["status"] == "PASS",
        "claim": claim["status"] == "PASS",
        "private_scan": scan["status"] == "PASS",
    }
    return {
        "status": "PASS_OFFICIAL_BATCH098_ARTIFACT_INGEST" if all(checks.values()) else "BATCH099_BATCH098_OFFICIAL_INGEST_BLOCKED_EXACT",
        "checks": checks,
        "ingest_receipt_sha256": sha256_file(receipt_path),
        "extracted_tree_hash": committed_tree_hash,
        "tree_hash_source": "committed_git_blob_bytes",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    result = verify(Path(args.output_root))
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())

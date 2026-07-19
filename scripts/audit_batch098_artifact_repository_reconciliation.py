from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.batch098_official_ingest import read_json, sha256_file, tree_hash


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--receipt-sha256")
    args = parser.parse_args()
    root = Path(args.output_root) / "batch098_official_ingest"
    receipt_path = root / "ingest_receipts" / "batch098_official_ingest_receipt.json"
    receipt = read_json(receipt_path)
    observed_receipt = sha256_file(receipt_path)
    observed_tree = tree_hash(root / "extracted_public_artifact")
    checks = {
        "receipt_frozen": args.receipt_sha256 is None or args.receipt_sha256 == observed_receipt,
        "tree_frozen": receipt["extracted_tree_hash"] == observed_tree,
        "batch098_immutable": not Path("outputs/post_v2_37_hardening_batch098_causal_hypergraph_real_materialization_topology_probe_closure").is_symlink(),
    }
    result = {"status": "PASS" if all(checks.values()) else "BLOCK", "checks": checks, "receipt_sha256": observed_receipt, "extracted_tree_hash": observed_tree}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

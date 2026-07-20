from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from controllergate.evidence.batch101_official_ingest import claim_reconciliation, execution_origin_reconciliation, platform_path, private_scan, read_json, semantic_reconciliation, sha256_file, verify_manifests, verify_sealed_member_tree
parser=argparse.ArgumentParser(); parser.add_argument("--output-root", required=True); args=parser.parse_args()
root=platform_path(Path(args.output_root)/"batch101_official_ingest"); extracted=root/"extracted_public_artifact"; receipt_path=root/"ingest_receipts/batch101_official_ingest_receipt.json"; receipt=read_json(receipt_path)
checks={"receipt":receipt.get("ingest_status")=="PASS_OFFICIAL_BATCH101_ARTIFACT_INGEST","tree":verify_sealed_member_tree(extracted,root/"custody/batch101_official_extracted_member_manifest.jsonl",receipt.get("extracted_tree_hash","")),"manifests":verify_manifests(extracted)["status"]=="PASS","semantic":semantic_reconciliation(extracted)["status"]=="PASS","claim":claim_reconciliation(extracted)["status"]=="PASS","origin":execution_origin_reconciliation(extracted)["status"]=="PASS","private_scan":private_scan(extracted)["status"]=="PASS"}
status="PASS_OFFICIAL_BATCH101_ARTIFACT_INGEST" if all(checks.values()) else "BATCH102_BATCH101_OFFICIAL_INGEST_BLOCKED_EXACT"; print(json.dumps({"status":status,"checks":checks,"receipt_sha256":sha256_file(receipt_path)},sort_keys=True)); raise SystemExit(0 if status.startswith("PASS_") else 1)

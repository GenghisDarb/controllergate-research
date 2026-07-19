from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.evidence.private_truth_v2 import verify_deterministic_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output-root", required=True)
    args = parser.parse_args()
    bundle = Path(args.bundle)
    output = Path(args.output_root)
    output.mkdir(parents=True, exist_ok=True)
    result = verify_deterministic_bundle(bundle)
    result.update({
        "producer": "scripts.verify_batch098_private_sealed_truth",
        "execution_depth": "independent ZIP, manifest, schema, timing, and scoreability validation",
        "semantic_scope": "private sealed truth bundle v2",
        "authority_allowed": "bundle verification only",
        "authority_forbidden": ["repair", "repair count", "release"],
    })
    (output / "private_sealed_truth_bundle_verification_v2.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    with zipfile.ZipFile(bundle) as archive:
        rows = []
        for info in archive.infolist():
            data = archive.read(info.filename)
            import hashlib
            rows.append({"path": info.filename, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    (output / "private_sealed_truth_bundle_member_manifest_v2.jsonl").write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

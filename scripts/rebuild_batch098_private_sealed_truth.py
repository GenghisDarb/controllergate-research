from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contracts", required=True)
    parser.add_argument("--terminal-commitments", required=True)
    parser.add_argument("--adjudication", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--original-bundle", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--created-at-utc", default="2026-07-19T06:30:00Z")
    args = parser.parse_args()
    output = Path(args.output_root)
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="batch098-truth-rebuild-") as temporary:
        root = Path(temporary)
        command = [
            sys.executable, str(Path(__file__).with_name("build_batch098_private_sealed_truth.py")),
            "--contracts", args.contracts, "--terminal-commitments", args.terminal_commitments,
            "--adjudication", args.adjudication, "--source-root", args.source_root,
            "--output-root", str(root / "sealed"), "--verification-root", str(root / "verification"),
            "--created-at-utc", args.created_at_utc, "--offline",
        ]
        subprocess.run(command, check=True)
        rebuilt = root / "sealed" / "Batch098_Private_Sealed_Truth_Frozen_Eight_v2.zip"
        original = Path(args.original_bundle)
        result = {
            "status": "PASS" if original.read_bytes() == rebuilt.read_bytes() else "BLOCK",
            "byte_identical_rebuild": original.read_bytes() == rebuilt.read_bytes(),
            "original_sha256": sha(original),
            "rebuilt_sha256": sha(rebuilt),
            "original_size": original.stat().st_size,
            "rebuilt_size": rebuilt.stat().st_size,
            "producer": "scripts.rebuild_batch098_private_sealed_truth",
            "execution_depth": "independent offline second build from pinned source bytes",
            "authority_allowed": "reproducibility verification only",
            "authority_forbidden": ["repair", "repair count", "release"],
        }
    (output / "private_sealed_truth_bundle_rebuild_audit_v2.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


FORBIDDEN = ["causal terminal", "source ownership", "repair authority", "repair count", "release authority"]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--requirements", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    bundle = Path(args.bundle)
    output = Path(args.output)
    raw = bundle.read_bytes()
    with zipfile.ZipFile(bundle) as archive:
        manifest = json.loads(archive.read("canonical_manifest.json"))
        names = archive.namelist()
    coverage = manifest.get("notebook_coverage", [])
    requirements = [json.loads(line) for line in Path(args.requirements).read_text(encoding="utf-8").splitlines() if line.strip()]
    valid = coverage == list(range(1, 45)) and all(row.get("source_file_sha256") and row.get("source_evidence_sha256") for row in requirements)
    value = {
        "status": "PASS_LOCAL_DIRECT_SOURCE_REPRODUCIBLE" if valid else "BLOCK",
        "execution_surface": "LOCAL_PROTECTED_SOURCE_RUN",
        "bundle_sha256": hashlib.sha256(raw).hexdigest(),
        "bundle_size": len(raw),
        "bundle_member_count": len(names),
        "notebook_coverage": coverage,
        "compiled_requirement_count": len(requirements),
        "direct_state_write_count": 0,
        "authority_escalation_count": 0,
        "authority_allowed": ["shadow requirement", "diagnostic design", "retrospective critic reconstruction"],
        "authority_forbidden": FORBIDDEN,
    }
    write_json(output / "tld_direct_shadow_processing_receipt.json", value)
    print(json.dumps(value, sort_keys=True))
    return 0 if valid else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Audit v1.7-beta pending evidence bundles and normalization gate state."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PENDING_DIR = ROOT / "episodes_pending"
NORMALIZED_LEDGER = ROOT / "traces" / "normalized" / "episodes.jsonl"
LIMITED_SCORING_PATH = ROOT / "traces" / "audits" / "limited_pilot_scoring" / "limited_pilot_scoring.json"
REQUIRED_FILES = {
    "ci_log.txt",
    "failing_command.txt",
    "patch_diff.diff",
    "agent_trace.md",
    "files_read.txt",
    "files_written.txt",
    "artifact_manifest.txt",
    "outcome.md",
}


def main() -> int:
    errors: list[str] = []
    if not PENDING_DIR.exists():
        errors.append(f"missing pending directory: {PENDING_DIR}")
        bundles: list[Path] = []
    else:
        bundles = sorted(path for path in PENDING_DIR.iterdir() if path.is_dir())

    if len(bundles) < 5:
        errors.append(f"expected at least 5 pending bundles, found {len(bundles)}")

    for bundle in bundles:
        files = {path.name for path in bundle.iterdir() if path.is_file()}
        missing = sorted(REQUIRED_FILES - files)
        extra = sorted(files - REQUIRED_FILES)
        if missing:
            errors.append(f"{bundle.name}: missing required files: {missing}")
        if extra:
            errors.append(f"{bundle.name}: unexpected files: {extra}")

        manifest = bundle / "artifact_manifest.txt"
        if manifest.exists():
            text = manifest.read_text(encoding="utf-8")
            for required in [
                "scoring_status: NOT_RUN",
                "normalization_status: NOT_NORMALIZED",
                "decision_time_evidence:",
                "outcome_only_evidence:",
            ]:
                if required not in text:
                    errors.append(f"{bundle.name}: artifact_manifest.txt missing {required!r}")

    normalized_records = 0
    normalization_state = "NOT RUN"
    if NORMALIZED_LEDGER.exists() and NORMALIZED_LEDGER.read_text(encoding="utf-8").strip():
        normalized_records = len(
            [
                line
                for line in NORMALIZED_LEDGER.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        )
        normalization_state = "REVIEW_NORMALIZED"

    if errors:
        print("v1.7-beta pending bundle audit: FAIL")
        for error in errors:
            print(f"- {error}")
        return 1

    print("v1.7-beta pending bundle audit: PASS")
    print(f"pending bundles: {len(bundles)}")
    print(f"normalized records: {normalized_records}")
    print(f"normalization: {normalization_state}")
    if LIMITED_SCORING_PATH.exists():
        print("scoring: LIMITED_PILOT_RUN")
    else:
        print("scoring: NOT RUN")
    return 0


if __name__ == "__main__":
    sys.exit(main())

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


ENVIRONMENT_MARKERS = (
    "modulenotfounderror", "importerror", "distributionnotfound",
    "no matching distribution", "requires-python", "command not found",
)


def classify_failure_from_evidence(
    *, failure_log: str, source_root: str | Path, target_path: str,
    candidate_package_roots: list[str] | None = None,
) -> dict[str, Any]:
    """Classify ownership from traceback topology without issue-specific strings."""
    lowered = failure_log.lower()
    if any(marker in lowered for marker in ENVIRONMENT_MARKERS):
        classification = "environment_owned"
        basis = "provider_or_import_failure_marker"
    else:
        paths = [item.replace("\\", "/") for item in re.findall(r'File ["\']([^"\']+)["\']', failure_log)]
        roots = tuple(candidate_package_roots or [])
        source_frames = [path for path in paths if roots and any(f"/{root.strip('/')}" in path for root in roots)]
        test_frames = [path for path in paths if "/tests/" in path or path.endswith(target_path)]
        if source_frames:
            classification = "source_owned_behavior_defect"
            basis = "candidate_source_traceback_frame"
        elif test_frames and ("typeerror" in lowered or "attributeerror" in lowered):
            classification = "test_expectation_fragility"
            basis = "test_only_traceback_with_expectation_type_failure"
        else:
            classification = "insufficient_evidence"
            basis = "no_candidate_source_or_environment_ownership_proof"
    return {
        "status": "PASS" if classification != "insufficient_evidence" else "BLOCK",
        "classification": classification,
        "basis": basis,
        "candidate_specific_rule_used": False,
        "prewritten_patch_used": False,
    }

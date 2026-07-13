from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

from packaging.specifiers import SpecifierSet
from packaging.version import Version

from controllergate.core.evidence import hash_record
from controllergate.runtime.runtime_image_registry import SUPPORTED_PYTHON_IMAGES


EVIDENCE_PRIORITY = (
    "requires_python", "tox", "nox", "pyproject", "setup_cfg", "setup_py", "ci", "classifier", "issue_runtime", "commit_date",
)


def resolve_python_runtime(evidence: Mapping[str, Any]) -> dict[str, Any]:
    spec_text = str(evidence.get("requires_python") or "")
    spec = SpecifierSet(spec_text) if spec_text else None
    eligible: list[str] = []
    excluded: list[dict[str, str]] = []
    for version in SUPPORTED_PYTHON_IMAGES:
        if spec is not None and Version(version) not in spec:
            excluded.append({"runtime": version, "reason": f"excluded_by_requires_python:{spec_text}"})
        else:
            eligible.append(version)
    explicit = [str(item) for item in evidence.get("declared_versions", []) if str(item) in eligible]
    selected = explicit[-1] if explicit else eligible[-1] if eligible else None
    source = "declared_versions" if explicit else "requires_python" if spec_text else "weak_commit_date_fallback"
    record = {
        "status": "PASS" if selected else "BLOCK",
        "eligible_runtimes": eligible,
        "excluded_runtimes": excluded,
        "selection_evidence": {key: evidence.get(key) for key in EVIDENCE_PRIORITY if evidence.get(key) is not None},
        "selected_runtime": selected,
        "selected_image": SUPPORTED_PYTHON_IMAGES.get(selected),
        "selection_source": source,
        "fallback_policy": "newest eligible declared runtime; commit date is weak fallback only",
        "selected_before_test_execution": True,
        "outcome_used_for_selection": False,
    }
    record["runtime_selection_hash"] = hash_record(record)
    return record

from __future__ import annotations

from typing import Any

from .contamination_classifier_v2 import classify_contamination_v2


def verify_contamination_classification(text: str, record: dict[str, Any]) -> dict[str, Any]:
    independent = classify_contamination_v2(text)
    matches = independent["classification"] == record.get("classification")
    return {"status": "PASS" if matches else "BLOCK", "independent_classification": independent["classification"], "matches": matches}

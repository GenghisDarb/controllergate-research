from __future__ import annotations

from datetime import datetime
from typing import Any


def cutoff_eligible(upload_timestamp: str, cutoff: str) -> bool:
    uploaded = datetime.fromisoformat(upload_timestamp.replace("Z", "+00:00"))
    boundary = datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
    return uploaded <= boundary


def verify_release_record(record: dict[str, Any], cutoff: str) -> dict[str, Any]:
    required = ("package", "version", "artifact_filename", "sha256", "upload_timestamp", "source_url")
    missing = [name for name in required if not record.get(name)]
    eligible = not missing and cutoff_eligible(str(record["upload_timestamp"]), cutoff)
    return {
        "status": "PASS" if eligible else "BLOCK",
        "cutoff_eligible": eligible,
        "missing": missing,
        "blocker": None if eligible else "post_cutoff_or_incomplete_package_artifact",
    }

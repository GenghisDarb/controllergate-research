from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from urllib.request import Request, urlopen
from typing import Any

from packaging.version import InvalidVersion, Version


def resolve_release_before_cutoff(package: str, cutoff: datetime, *, timeout: int = 30) -> dict[str, Any]:
    url = f"https://pypi.org/pypi/{package}/json"
    request = Request(url, headers={"User-Agent": "ControllerGate-decision-time-resolver/1"})
    retrieved = datetime.now(timezone.utc)
    with urlopen(request, timeout=timeout) as response:
        body = response.read()
    data = json.loads(body)
    eligible = []
    excluded_later = 0
    for version, files in data.get("releases", {}).items():
        try: parsed = Version(version)
        except InvalidVersion: continue
        if parsed.is_prerelease: continue
        for file in files:
            stamp = file.get("upload_time_iso_8601") or file.get("upload_time")
            if not stamp: continue
            upload = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
            if upload <= cutoff:
                eligible.append((parsed, upload, file))
            else:
                excluded_later += 1
    if not eligible:
        return {"status": "BLOCK", "package": package, "blocker": "no_release_before_cutoff", "metadata_url": url, "metadata_sha256": hashlib.sha256(body).hexdigest(), "retrieved_at": retrieved.isoformat()}
    version, upload, file = max(eligible, key=lambda row: (row[0], row[1]))
    return {
        "status": "PASS", "package": package, "selected_version": str(version),
        "selected_filename": file.get("filename"), "selected_artifact_sha256": (file.get("digests") or {}).get("sha256"),
        "selected_upload_time": upload.isoformat(), "cutoff": cutoff.isoformat(), "cutoff_eligible": True,
        "later_artifact_count_excluded": excluded_later, "metadata_url": url,
        "metadata_sha256": hashlib.sha256(body).hexdigest(), "metadata_retrieved_at": retrieved.isoformat(),
    }

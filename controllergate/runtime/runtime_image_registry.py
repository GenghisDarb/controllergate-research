from __future__ import annotations

from controllergate.core.evidence import hash_record


SUPPORTED_PYTHON_IMAGES = {
    version: {
        "version": version,
        "image": f"python:{version}-slim",
        "image_digest_policy": "resolve_and_freeze_before_execution",
        "registry_record_hash": hash_record({"version": version, "image": f"python:{version}-slim"}),
    }
    for version in ("3.8", "3.9", "3.10", "3.11", "3.12", "3.13")
}

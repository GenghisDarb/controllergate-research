from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any


def verify_vendor_manifest(provider: dict[str, Any]) -> dict[str, Any]:
    root = Path(provider.get("vendor_root", ""))
    rows = provider.get("vendor_manifest", [])
    errors: list[str] = []
    for row in rows:
        path = root / row["path"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            errors.append(row["path"])
    package_count = len(provider.get("packages", []))
    acquisitions = provider.get("acquisitions", [])
    if package_count == 0 or package_count != len(acquisitions): errors.append("package_count_mismatch")
    if any(item.get("checksum") != item.get("crate_sha256") or item.get("vendor", {}).get("status") != "PASS" for item in acquisitions): errors.append("package_checksum_mismatch")
    computed = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    if computed != provider.get("vendor_hash"): errors.append("vendor_hash_mismatch")
    return {"status": "PASS" if not errors else "BLOCK", "errors": errors, "package_count": package_count, "file_count": len(rows), "vendor_hash": computed}


def run_offline_cargo_metadata(*, rust_image: str, source_root: Path, manifest_relative: str, vendor_root: Path, cargo_config: Path) -> dict[str, Any]:
    command = ["docker", "run", "--rm", "--network", "none", "--read-only", "--user", "65534:65534", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--tmpfs", "/tmp:rw,exec,nosuid,size=1g", "-v", f"{source_root.resolve()}:/src:ro", "-v", f"{vendor_root.resolve()}:/opt/cargo-vendor:ro", "-v", f"{cargo_config.resolve()}:/tmp/cargo/config.toml:ro", "-e", "PATH=/usr/local/cargo/bin:/usr/local/rustup/bin:/usr/local/bin:/usr/bin:/bin", "-e", "CARGO_HOME=/tmp/cargo", "-e", "CARGO_TARGET_DIR=/tmp/target", "-e", "CARGO_NET_OFFLINE=true", "--entrypoint", "/bin/sh", rust_image, "-c", f"/usr/local/cargo/bin/cargo metadata --locked --offline --manifest-path /src/{manifest_relative} --format-version 1 >/tmp/metadata.json && test -s /tmp/metadata.json"]
    try:
        run = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"status": "BLOCK", "blocker": "cargo_offline_metadata_unavailable", "error": type(exc).__name__, "command": command, "network": "none", "executed": False}
    return {"status": "PASS" if run.returncode == 0 else "BLOCK", "blocker": None if run.returncode == 0 else "cargo_offline_metadata_failed", "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr, "command": command, "network": "none", "executed": True}

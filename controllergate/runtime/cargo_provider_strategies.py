from __future__ import annotations

import re
from pathlib import Path
import subprocess
from typing import Any

from .cargo_vendor import build_vendor_tree


def classify_cargo_failure(stderr: str, returncode: int | None) -> str:
    text = stderr.lower()
    if returncode == 0:
        return "cargo_fetch_pass"
    filesystem_patterns = (
        r"permission denied", r"read[- ]only file system", r"unable to open database file",
        r"failed to create director(?:y|ies)", r"could not create director(?:y|ies)",
    )
    if any(re.search(pattern, text) for pattern in filesystem_patterns):
        return "cargo_cache_not_writable"
    if re.search(r"(?:http(?:/\S+)?\s+|status(?:\s+code)?\s+|response\s+)(429)\b", text):
        return "cargo_http_rate_limited"
    if re.search(r"(?:http(?:/\S+)?\s+|status(?:\s+code)?\s+|response\s+)(500|502|503|504)\b", text):
        return "cargo_http_server_error"
    if "could not resolve host" in text or "dns resolution" in text:
        return "cargo_dns_resolution_failed"
    if "certificate verify" in text or "tls certificate" in text:
        return "cargo_tls_verification_failed"
    if "failed to download" in text:
        return "cargo_static_crate_download_failed"
    if "failed to query replaced source registry" in text:
        return "cargo_registry_index_unreachable"
    if "checksum" in text or "lock file" in text or "manifest" in text:
        return "cargo_manifest_or_lock_error"
    if "connection reset" in text or "temporary failure" in text:
        return "cargo_transient_transport_failure"
    return "cargo_failure_unclassified"


def cargo_cache_writability_preflight(*, cache: Path, python_image: str) -> dict[str, Any]:
    cache.mkdir(parents=True, exist_ok=True)
    try:
        cache.chmod(0o777)
    except OSError:
        pass
    code = "import os,pathlib,sqlite3;p=pathlib.Path('/cargo-cache');p.mkdir(exist_ok=True);(p/'write.tmp').write_text('ok');(p/'write.tmp').rename(p/'rename.tmp');(p/'registry/cache/probe').mkdir(parents=True,exist_ok=True);c=sqlite3.connect(p/'.global-cache');c.execute('create table if not exists probe(v int)');c.commit();c.close();(p/'rename.tmp').unlink();(p/'.global-cache').unlink();print('cargo-cache-preflight-pass',os.getuid(),os.getgid())"
    command = ["docker", "run", "--rm", "--network", "none", "--user", "65534:65534", "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "-v", f"{cache.resolve()}:/cargo-cache:rw", "--entrypoint", "python", python_image, "-c", code]
    try:
        run = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return {"status": "BLOCK", "blocker": "cargo_cache_preflight_unavailable", "error": type(exc).__name__, "command": command}
    passed = run.returncode == 0
    return {"status": "PASS" if passed else "BLOCK", "blocker": None if passed else "cargo_cache_not_writable", "returncode": run.returncode, "stdout": run.stdout, "stderr": run.stderr, "command": command, "checks": {"directory": True, "container_user": "65534:65534", "write": passed, "rename": passed, "database_file": passed, "subdirectory": passed, "delete": passed}}


def generate_direct_vendor(*, lock_path: Path, vendor_root: Path, cutoff: str, phase_id: str, policy: dict[str, Any], ledger_path: Path) -> dict[str, Any]:
    return build_vendor_tree(lock_path=lock_path, vendor_root=vendor_root, cutoff=cutoff, phase_id=phase_id, policy=policy, ledger_path=ledger_path, container_vendor_path="/opt/cargo-vendor")

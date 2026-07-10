from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import subprocess
from typing import Any

from controllergate.core.evidence import write_json_deterministic, write_text_lf

SECRET_PATTERNS = {
    "github_token": re.compile(r"gh[opsu]_[A-Za-z0-9_]{20,}"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def normalize_output(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"/home/runner/work/[^\s:'\"]+", "<WORKSPACE>", text)
    text = re.sub(r"[A-Za-z]:\\[^\s:'\"]+", "<WINDOWS_PATH>", text)
    return text


def secret_scan(text: str) -> dict[str, Any]:
    findings = sorted(name for name, pattern in SECRET_PATTERNS.items() if pattern.search(text))
    return {"status": "PASS" if not findings else "BLOCK", "secret_classes": findings, "secret_count": len(findings)}


def record_completed_command(
    output_dir: Path, prefix: str, *, argv: list[str], cwd: str, env: dict[str, str],
    container_identity: str | None, image_digest: str | None, timeout_seconds: int,
    returncode: int, stdout: str, stderr: str, started_at: str, stopped_at: str,
    termination_signal: str | None = None, phase_classification: str = "diagnostic",
) -> dict[str, Any]:
    combined = stdout + ("\n" if stdout and stderr else "") + stderr
    scan = secret_scan(combined)
    raw_allowed = scan["status"] == "PASS"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{prefix}_stdout.txt").write_bytes((stdout if raw_allowed else "REDACTED_SECRET_DETECTED").encode("utf-8"))
    (output_dir / f"{prefix}_stderr.txt").write_bytes((stderr if raw_allowed else "REDACTED_SECRET_DETECTED").encode("utf-8"))
    (output_dir / f"{prefix}_combined.txt").write_bytes((combined if raw_allowed else "REDACTED_SECRET_DETECTED").encode("utf-8"))
    manifest = {
        "argv": argv, "working_directory": cwd, "declared_environment_variables": env,
        "container_identity": container_identity, "image_digest": image_digest,
        "start_time": started_at, "stop_time": stopped_at, "timeout_seconds": timeout_seconds,
        "exit_code": returncode, "termination_signal": termination_signal,
        "phase_classification": phase_classification,
    }
    hashes = {
        "raw_stdout_sha256": hashlib.sha256(stdout.encode()).hexdigest(),
        "raw_stderr_sha256": hashlib.sha256(stderr.encode()).hexdigest(),
        "raw_combined_sha256": hashlib.sha256(combined.encode()).hexdigest(),
        "normalized_output_sha256": hashlib.sha256(normalize_output(combined).encode()).hexdigest(),
        "path_scrubbed_output": normalize_output(combined),
        "raw_bytes_packaged": raw_allowed,
    }
    write_json_deterministic(output_dir / f"{prefix}_command_manifest.json", manifest)
    write_json_deterministic(output_dir / f"{prefix}_output_hashes.json", hashes)
    write_json_deterministic(output_dir / f"{prefix}_secret_scan.json", scan)
    return {"command_manifest": manifest, "hashes": hashes, "secret_scan": scan}


def run_host_command(output_dir: Path, prefix: str, argv: list[str], *, cwd: Path, env: dict[str, str] | None = None, timeout_seconds: int = 60, phase_classification: str = "diagnostic") -> dict[str, Any]:
    selected_env = dict(os.environ)
    if env: selected_env.update(env)
    start = datetime.now(timezone.utc).isoformat()
    try:
        completed = subprocess.run(argv, cwd=cwd, env=selected_env, text=True, capture_output=True, timeout=timeout_seconds, check=False)
        signal = None
    except subprocess.TimeoutExpired as exc:
        completed = subprocess.CompletedProcess(argv, 124, stdout=exc.stdout or "", stderr=exc.stderr or "")
        signal = "TIMEOUT"
    stop = datetime.now(timezone.utc).isoformat()
    custody = record_completed_command(output_dir, prefix, argv=argv, cwd=str(cwd), env=env or {}, container_identity=None, image_digest=None, timeout_seconds=timeout_seconds, returncode=completed.returncode, stdout=completed.stdout, stderr=completed.stderr, started_at=start, stopped_at=stop, termination_signal=signal, phase_classification=phase_classification)
    return {"status": "PASS" if completed.returncode == 0 else "BLOCK", "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "custody": custody}

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import socket
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

from controllergate.core.evidence import hash_record
from .evidence_kind import EvidenceKind
from .execution_record import ExecutionRecord


ALLOWED_EXTERNAL_OPERATION_TYPES = {
    "source_acquisition", "git_metadata", "git_checkout", "secondary_input_acquisition", "provider_acquisition",
    "provider_build", "provider_verification", "collection", "reproducer_execution",
    "target_execution", "diagnostic_probe", "patch_application", "validation",
    "duplicate_replay", "canary_installation", "canary_execution", "health_observation",
    "rollback", "proof_append", "count_decision", "plan_maturation", "transport",
    "local_actuation", "cleanup", "artifact_build",
    "service_start", "service_readiness", "service_request", "service_stop", "service_cleanup",
}

SECRET_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "PRIVATE_KEY", "CREDENTIAL")


def allocate_loopback_port() -> int:
    """Allocate a transient loopback port inside the external-operation boundary."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def wait_for_loopback_url(url: str, *, attempts: int = 50, timeout: float = 0.2, interval: float = 0.05) -> bool:
    if not url.startswith(("http://127.0.0.1:", "http://localhost:", "http://[::1]:")):
        raise ValueError("readiness URL must be loopback")
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                if response.status == 200:
                    return True
        except OSError:
            time.sleep(interval)
    return False


def execute_command(*, argv: list[str], cwd: Path, runtime_root: Path, stage_id: str, candidate_id: str, authorization_id: str, env: Mapping[str, str] | None = None, timeout: int = 120, required_sentinels: list[str] | None = None) -> tuple[subprocess.CompletedProcess[str], ExecutionRecord]:
    if not argv:
        raise ValueError("exact argv is required")
    effective_env = dict(env or {})
    started_wall = datetime.now(timezone.utc)
    started = time.monotonic()
    run = subprocess.run(argv, cwd=cwd, env=effective_env or None, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout, check=False)
    ended_wall = datetime.now(timezone.utc)
    observed = [line.strip() for line in (run.stdout + "\n" + run.stderr).splitlines() if line.strip().isupper() and " " not in line.strip()]
    record = ExecutionRecord(
        execution_id=f"command:{stage_id}:{started_wall.timestamp()}", stage_id=stage_id,
        candidate_id=candidate_id, evidence_kind=EvidenceKind.EXECUTED_COMMAND,
        authorization_id=authorization_id, operation_status="COMPLETED",
        evidence_status="RECORDED", gate_decision="PENDING_VERIFICATION", candidate_state="UNCHANGED",
        argv=argv, working_directory=str(cwd.resolve()), runtime_root_identity=str(runtime_root.resolve()),
        runtime_image_or_interpreter_identity=argv[0], process_id=None,
        start_timestamp=started_wall.isoformat(), end_timestamp=ended_wall.isoformat(),
        monotonic_duration=time.monotonic() - started, environment_allowlist_hash=hash_record(sorted(effective_env)),
        network_policy="none", return_code=run.returncode,
        stdout_hash=hashlib.sha256(run.stdout.encode()).hexdigest(), stderr_hash=hashlib.sha256(run.stderr.encode()).hexdigest(),
        required_sentinels=required_sentinels or [], observed_sentinels=observed,
        independent_verifier="execution_claim_verifier", verifier_result="PENDING",
    )
    return run, record


def execute_external_operation(
    *, operation_type: str, argv: list[str], cwd: Path, runtime_root: Path,
    stage_id: str, candidate_id: str, authorization_id: str,
    runtime_attestation: dict[str, object], platform: str, runtime: str,
    provider_identity: str | None = None, network_policy: str = "none",
    env: Mapping[str, str] | None = None, timeout: int = 120,
    required_sentinels: list[str] | None = None,
    input_hashes: dict[str, str] | None = None,
    output_paths: list[Path] | None = None,
    source_tree_hash_before: str | None = None,
    source_tree_hash_after: str | None = None,
    test_tree_hash_before: str | None = None,
    test_tree_hash_after: str | None = None,
    parent_ledger_hash: str | None = None,
    run_id: str | None = None,
    nonce: str | None = None,
    network_request_budget: int = 0,
    network_byte_budget: int = 0,
) -> tuple[subprocess.CompletedProcess[str], dict[str, object]]:
    if operation_type not in ALLOWED_EXTERNAL_OPERATION_TYPES:
        raise ValueError(f"unsupported external operation type: {operation_type}")
    if runtime_attestation.get("status") != "PASS" or not runtime_attestation.get("attestation_hash"):
        raise ValueError("verified runtime attestation required")
    started_wall = datetime.now(timezone.utc)
    started = time.monotonic()
    effective_env = dict(env or {})
    leaked = sorted(name for name in effective_env if any(marker in name.upper() for marker in SECRET_MARKERS))
    if leaked:
        raise ValueError(f"secret-bearing environment keys rejected: {','.join(leaked)}")
    if network_policy == "none" and (network_request_budget or network_byte_budget):
        raise ValueError("offline operation cannot receive network budget")
    if network_policy != "none" and (network_request_budget <= 0 or network_byte_budget <= 0):
        raise ValueError("network-enabled operation requires bounded request and byte budgets")
    run = subprocess.run(argv, cwd=cwd, env=effective_env or None, capture_output=True, text=True,
                         encoding="utf-8", errors="replace", timeout=timeout, check=False)
    ended_wall = datetime.now(timezone.utc)
    observed = [line.strip() for line in (run.stdout + "\n" + run.stderr).splitlines()
                if line.strip().isupper() and " " not in line.strip()]
    outputs = {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in (output_paths or []) if path.is_file()}
    record: dict[str, object] = {
        "execution_id": f"{operation_type}:{stage_id}:{started_wall.timestamp()}",
        "operation_id": f"{operation_type}:{stage_id}:{hash_record([argv, str(cwd), authorization_id, nonce])[:20]}",
        "candidate_id": candidate_id, "stage_id": stage_id,
        "run_id": run_id or f"{candidate_id}:canonical",
        "operation_type": operation_type, "evidence_kind": "EXECUTED_COMMAND",
        "authorization_id": authorization_id, "nonce": nonce or hash_record([authorization_id, stage_id])[:32], "argv": argv,
        "callable_identity": None, "callable_source_hash": None,
        "working_directory": str(cwd.resolve()),
        "runtime_root_identity": str(runtime_root.resolve()),
        "runtime_attestation_hash": runtime_attestation["attestation_hash"],
        "platform": platform, "runtime": runtime, "provider_identity": provider_identity,
        "network_policy": network_policy,
        "network_request_budget": network_request_budget,
        "network_byte_budget": network_byte_budget,
        "network_requests_observed": 0,
        "network_bytes_observed": 0,
        "actual_start_time": started_wall.isoformat(), "actual_end_time": ended_wall.isoformat(),
        "start_timestamp": started_wall.isoformat(), "end_timestamp": ended_wall.isoformat(),
        "monotonic_duration": time.monotonic() - started, "return_code": run.returncode,
        "stdout_hash": hashlib.sha256(run.stdout.encode()).hexdigest(),
        "stderr_hash": hashlib.sha256(run.stderr.encode()).hexdigest(),
        "required_sentinels": required_sentinels or [], "observed_sentinels": observed,
        "input_paths_and_hashes": input_hashes or {}, "input_identities": input_hashes or {},
        "output_paths_and_hashes": outputs, "output_identities": outputs,
        "source_tree_hash_before": source_tree_hash_before, "source_tree_hash_after": source_tree_hash_after,
        "test_tree_hash_before": test_tree_hash_before, "test_tree_hash_after": test_tree_hash_after,
        "independent_verifier": "controllergate.execution.execution_claim_verifier",
        "verifier_result": "PENDING", "ledger_parent_hash": parent_ledger_hash,
        "operation_status": "COMPLETED", "evidence_status": "RECORDED",
        "gate_decision": "PENDING_VERIFICATION", "candidate_state": "UNCHANGED",
        "record_hash": None,
    }
    record["record_hash"] = hash_record(record)
    return run, record


def record_external_service_event(
    *, operation_type: str, service_id: str, candidate_id: str, run_id: str,
    frame_id: str, host: str, port: int | None, runtime_root: Path,
    runtime_attestation_hash: str, parent_ledger_hash: str | None,
    values: dict[str, object],
) -> dict[str, object]:
    if operation_type not in {"service_start", "service_readiness", "service_request", "service_stop", "service_cleanup"}:
        raise ValueError("unsupported service operation type")
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("brokered local service requires loopback")
    if not runtime_attestation_hash:
        raise ValueError("runtime attestation hash required")
    record: dict[str, object] = {
        "operation_type": operation_type, "service_id": service_id,
        "candidate_id": candidate_id, "run_id": run_id, "frame_id": frame_id,
        "bound_host": host, "actual_port": port, "runtime_root_identity": str(runtime_root.resolve()),
        "runtime_attestation_hash": runtime_attestation_hash,
        "network_policy": "bounded_loopback_only", "ledger_parent_hash": parent_ledger_hash,
        "broker_identity": "controllergate.execution.execution_broker.record_external_service_event",
        **values,
    }
    record["record_hash"] = hash_record(record)
    return record


def start_brokered_service_process(
    *, argv: list[str], cwd: Path, env: Mapping[str, str] | None,
    service_id: str, candidate_id: str, run_id: str, frame_id: str,
    host: str, port: int, requested_port: int, runtime_root: Path, runtime_attestation_hash: str,
    parent_ledger_hash: str | None,
) -> tuple[subprocess.Popen[bytes], dict[str, object]]:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("brokered local service requires loopback")
    process = subprocess.Popen(argv, cwd=cwd, env=dict(env or {}) or None, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    record = record_external_service_event(
        operation_type="service_start", service_id=service_id, candidate_id=candidate_id,
        run_id=run_id, frame_id=frame_id, host=host, port=port,
        runtime_root=runtime_root, runtime_attestation_hash=runtime_attestation_hash,
        parent_ledger_hash=parent_ledger_hash,
        values={"exact_argv": argv, "cwd": str(cwd.resolve()), "process_identity": process.pid, "requested_port": requested_port, "status": "STARTED"},
    )
    return process, record

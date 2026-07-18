from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from controllergate.execution.execution_broker import allocate_loopback_port, record_external_service_event, start_brokered_service_process, wait_for_loopback_url


def _payload(mode: str) -> str:
    if mode == "one-operation":
        return "openapi: 3.0.0\ninfo:\n  title: ControllerGate fixture\n  version: '1'\npaths:\n  /status:\n    get:\n      responses:\n        '200':\n          description: ok\n"
    if mode == "empty":
        return "openapi: 3.0.0\ninfo:\n  title: Cutoff-bound modular fixture\n  version: '1'\npaths: {}\n"
    if mode == "corrupt":
        return "openapi: [not-valid\npaths:\n  /broken:\n"
    raise ValueError(f"unsupported service fixture mode: {mode}")


def execute_openapi_service_operation(
    *, broker: Any, python: Path, target_argv: list[str], cwd: Path, output_path: Path,
    mode: str, stage: str, expected_codes: set[int], environment: Mapping[str, str],
) -> dict[str, Any]:
    port = allocate_loopback_port()
    service_root = cwd / f"controllergate-loopback-{stage}"
    service_root.mkdir(parents=True, exist_ok=True)
    source = service_root / "openapi.yaml"
    source.write_text(_payload(mode), encoding="utf-8", newline="\n")
    service_id = f"{broker.contract.candidate_id}:{broker.run_id}:{stage}:{port}"
    process, start = start_brokered_service_process(
        argv=[str(python), "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(service_root)],
        cwd=cwd, env=environment, service_id=service_id, candidate_id=broker.contract.candidate_id,
        run_id=broker.run_id, frame_id=f"batch098:{broker.run_id}:materialization", host="127.0.0.1", port=port,
        requested_port=0, runtime_root=broker.runtime_root, runtime_attestation_hash=broker.attestation["attestation_hash"],
        parent_ledger_hash=broker.parent,
    )
    broker.append_service_record(start)
    ready = wait_for_loopback_url(f"http://127.0.0.1:{port}/openapi.yaml")
    readiness = record_external_service_event(
        operation_type="service_readiness", service_id=service_id, candidate_id=broker.contract.candidate_id,
        run_id=broker.run_id, frame_id=f"batch098:{broker.run_id}:materialization", host="127.0.0.1", port=port,
        runtime_root=broker.runtime_root, runtime_attestation_hash=broker.attestation["attestation_hash"],
        parent_ledger_hash=broker.parent, values={"status": "READY" if ready else "BLOCK", "probe": "/openapi.yaml"},
    )
    broker.append_service_record(readiness)
    expanded = [value.replace("{PORT}", str(port)).replace("eodhd.spec", str(output_path)) for value in target_argv]
    rc, stdout, stderr, target = broker.run(stage, "target_execution", expanded, cwd, env=environment, outputs=[output_path], timeout=300)
    request = record_external_service_event(
        operation_type="service_request", service_id=service_id, candidate_id=broker.contract.candidate_id,
        run_id=broker.run_id, frame_id=f"batch098:{broker.run_id}:materialization", host="127.0.0.1", port=port,
        runtime_root=broker.runtime_root, runtime_attestation_hash=broker.attestation["attestation_hash"],
        parent_ledger_hash=broker.parent, values={"status": "OBSERVED", "target_operation_id": target["operation_id"], "served_sha256": __import__("hashlib").sha256(source.read_bytes()).hexdigest()},
    )
    broker.append_service_record(request)
    process.terminate()
    try:
        process.communicate(timeout=5)
    except Exception:
        process.kill(); process.communicate()
    stop = record_external_service_event(
        operation_type="service_stop", service_id=service_id, candidate_id=broker.contract.candidate_id,
        run_id=broker.run_id, frame_id=f"batch098:{broker.run_id}:materialization", host="127.0.0.1", port=port,
        runtime_root=broker.runtime_root, runtime_attestation_hash=broker.attestation["attestation_hash"],
        parent_ledger_hash=broker.parent, values={"status": "STOPPED", "process_return_code": process.returncode},
    )
    broker.append_service_record(stop)
    cleanup = record_external_service_event(
        operation_type="service_cleanup", service_id=service_id, candidate_id=broker.contract.candidate_id,
        run_id=broker.run_id, frame_id=f"batch098:{broker.run_id}:materialization", host="127.0.0.1", port=port,
        runtime_root=broker.runtime_root, runtime_attestation_hash=broker.attestation["attestation_hash"],
        parent_ledger_hash=broker.parent, values={"status": "CLEANUP_RECORDED", "service_root": str(service_root)},
    )
    broker.append_service_record(cleanup)
    return {
        "status": "PASS" if ready and rc in expected_codes else "BLOCK",
        "return_code": rc,
        "stdout": stdout,
        "stderr": stderr,
        "target_record": target,
        "service_records": [start, readiness, request, stop, cleanup],
        "port": port,
        "mode": mode,
        "product_path": str(output_path),
    }

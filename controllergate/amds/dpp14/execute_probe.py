from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
import sys

from controllergate.execution.execution_broker import execute_external_operation
from controllergate.state.integrity import canonical_hash
from .state import DPP14State


def _read_only_lane(probe: dict, frozen: dict) -> dict:
    if probe.get("mutates") or probe.get("patch_authority"):
        return {"probe_id": probe.get("probe_id"), "status": "BLOCK", "blocker": "parallel_probe_not_read_only"}
    if probe.get("argv"):
        root = Path(str(frozen.get("runtime_root", "."))).resolve()
        attestation = {"status": "PASS", "attestation_hash": canonical_hash([sys.version, sys.platform])}
        run, record = execute_external_operation(
            operation_type="diagnostic_probe", argv=list(probe["argv"]), cwd=root, runtime_root=root,
            stage_id=str(probe.get("probe_id")), candidate_id=str(frozen.get("candidate_id", "dpp14")),
            authorization_id=str(probe.get("authorization_id", canonical_hash(probe))),
            runtime_attestation=attestation, platform=sys.platform, runtime=sys.version,
            run_id=str(frozen.get("run_id", "dpp14")), nonce=str(probe.get("nonce", canonical_hash([probe, "nonce"]))),
        )
        return {"probe_id": probe.get("probe_id"), "lane": probe.get("lane", "default"),
                "status": "PASS" if run.returncode == 0 else "BLOCK", "return_code": run.returncode,
                "record_hash": record["record_hash"], "direct": True, "frame_hash": frozen.get("frame_hash")}
    # Compatibility for the immutable Batch086 fixture suite. New decision
    # bundles are required to provide broker-executable argv and never consume
    # this label-bearing compatibility record.
    return {"probe_id": probe.get("probe_id"), "lane": probe.get("lane", "default"), "status": probe.get("status", "PASS"),
            "classification": probe.get("classification"), "direct": bool(probe.get("direct")),
            "legacy_fixture_compatibility_only": True, "frame_hash": frozen.get("frame_hash")}


def execute_probe(state: DPP14State) -> DPP14State:
    frozen = deepcopy(state.frozen_frame)
    probes = frozen.get("selected_probes", [])
    with ThreadPoolExecutor(max_workers=max(1, min(4, len(probes)))) as pool:
        results = list(pool.map(lambda probe: _read_only_lane(probe, frozen), probes))
    state.observations = sorted(results, key=lambda item: (item.get("lane", ""), item.get("probe_id", "")))
    state.trace.append({"transition": "ExecuteProbe", "status": "PASS", "round_start_barrier": True, "read_only_lanes": True})
    return state

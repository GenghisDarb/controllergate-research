"""Explicit adapters for the recovered Batch100 producers and frozen v4 predicates.

These adapters translate measured fields. They do not infer missing measurements,
choose a favourable predicate, or confer causal/biological authority.
"""
from __future__ import annotations

import copy
from typing import Any

from .registry_bound_semantics_candidate import canonical_hash

ADAPTER_VERSION = "batch100-to-v4-observation-adapters-local-v2"


def adapt_observation(candidate_id: str, raw: dict[str, Any]) -> dict[str, Any]:
    observation = copy.deepcopy(raw)
    derivations: list[dict[str, Any]] = []
    errors: list[str] = []

    def measured(target: str, value: Any, source: str) -> None:
        if target in observation and canonical_hash(observation[target]) != canonical_hash(value):
            errors.append("conflicting_measurements:" + target)
            observation.pop(target)
            return
        observation[target] = value
        derivations.append({"field": target, "source": source, "value": value})

    if candidate_id in {"incident_poetry_10974_init_duplicate_name", "incident_openbb_7585_modular_openapi_reproducer"}:
        if type(raw.get("return_code")) is int:
            measured("exit_code", raw["return_code"], "Batch100.semantic_observation.return_code")
    if candidate_id == "incident_poetry_10974_init_duplicate_name":
        if isinstance(raw.get("raw_project_name"), str):
            measured("generated_project_name", raw["raw_project_name"],
                     "Batch100 pyproject read; Batch101 semantic_value alias")
        # No expected directory name is substituted for the actual measured cwd.
        if isinstance(raw.get("actual_cwd_basename"), str) and raw["actual_cwd_basename"]:
            measured("cwd_basename", raw["actual_cwd_basename"], "new producer actual executed cwd.name")
    if candidate_id == "audioread_144_py313_aifc_removed":
        aifc = raw.get("aifc")
        if isinstance(aifc, dict) and aifc.get("module") == "aifc":
            if aifc.get("status") in {"IMPORTED", "FAILED"}:
                measured("module", "aifc", "batch100_audioread_harness.import_observation(aifc)")
                if aifc["status"] == "IMPORTED":
                    measured("exception_type", None, "explicit IMPORTED status; no exception")
                elif isinstance(aifc.get("exception_type"), str):
                    measured("exception_type", aifc["exception_type"], "aifc.exception_type")
        route = raw.get("route_import")
        if raw.get("route") == "rawread" and isinstance(route, dict) and route.get("module") == "audioread.rawread":
            if route.get("status") == "IMPORTED":
                measured("rawread_import", "success", "observed rawread route import")
            elif route.get("status") == "FAILED":
                measured("rawread_import", "failure", "observed rawread route import")
    receipt = {
        "version": ADAPTER_VERSION, "candidate_id": candidate_id,
        "raw_hash": canonical_hash(raw), "adapted_hash": canonical_hash(observation),
        "derivations": derivations, "errors": errors,
        "status": "ADAPTED" if not errors else "UNRESOLVED",
        "scope": "measured field translation only; not a causal or execution attestation",
    }
    receipt["receipt_hash"] = canonical_hash(receipt)
    return {"observation": observation, "receipt": receipt}

from __future__ import annotations

from typing import Any, Callable
from .probe_registry import PROBE_TYPES


def execute_probe(probe_type: str, executor: Callable[[],dict[str,Any]], authorization: dict[str,Any]) -> dict[str,Any]:
    if probe_type not in PROBE_TYPES and not probe_type.startswith(("build_","provider_","compiler_","cargo_","cmake_","pkg_config_","abi_","resource_","writable_")):
        return {"status":"BLOCK","blocker":"amds_probe_type_unregistered"}
    if not authorization.get("allowed") or authorization.get("mutation_allowed"):
        return {"status":"BLOCK","blocker":"amds_probe_authorization_invalid"}
    result=executor(); return {**result,"probe_type":probe_type,"authorization_id":authorization.get("authorization_id"),"mutation_count":0}


def executor_contracts() -> dict[str,dict[str,str]]:
    return {name:{"executor":"execute_probe","independent_verifier":"verify_probe_observation"} for name in PROBE_TYPES}

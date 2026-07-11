from __future__ import annotations

from importlib import import_module
from typing import Any


ALLOWED_BINDINGS = {
    "batch068h4_phase": "controllergate.runtime.batch068h4_pipeline:execute_phase",
    "batch068h5_phase": "controllergate.runtime.batch068h5_pipeline:execute_phase",
}


def execute_binding(binding: str, phase_id: str, context: dict[str, Any]) -> dict[str, Any]:
    target = ALLOWED_BINDINGS.get(binding)
    if target is None: return {"status": "BLOCK", "blocker": "runtime_binding_not_allowlisted", "phase_id": phase_id}
    module_name, function_name = target.split(":", 1)
    function = getattr(import_module(module_name), function_name)
    result = function(phase_id, context)
    if result.get("status") not in {"PASS", "BLOCK", "MANUAL_REVIEW"}: return {"status": "BLOCK", "blocker": "runtime_phase_invalid_status", "phase_id": phase_id}
    return result

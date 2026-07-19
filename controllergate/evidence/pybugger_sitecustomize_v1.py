"""External, preregistered py-bugger attempt-accounting instrumentation.

This file is copied to an isolated instrumentation directory as
``sitecustomize.py``.  It wraps public issue-time functions without changing
the candidate source tree and records attempted, successful, and persisted
operations separately.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def _install() -> None:
    mask = os.environ.get("CONTROLLERGATE_MUTATION_MASK")
    ledger_path = os.environ.get("CONTROLLERGATE_MUTATION_LEDGER")
    if not mask or not ledger_path:
        return
    try:
        from py_bugger import buggers
        from py_bugger.utils.modification import modifications
    except ImportError:
        return
    counter = {"value": 0}

    def wrap(name: str):
        original = getattr(buggers, name)

        def instrumented(py_files):
            index = counter["value"]
            counter["value"] += 1
            allowed = index < len(mask) and mask[index] == "1"
            before = len(modifications)
            result = original(py_files) if allowed else False
            after = len(modifications)
            event = {
                "attempt_index": index,
                "function": name,
                "mask_allowed": allowed,
                "function_result": bool(result),
                "modification_count_before": before,
                "modification_count_after": after,
                "successful": after > before,
            }
            path = Path(ledger_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
            return result

        return instrumented

    for function_name in ("module_not_found_bugger", "attribute_error_bugger", "indentation_error_bugger"):
        setattr(buggers, function_name, wrap(function_name))
    receipt = {
        "instrumentation": "pybugger-accounting-sitecustomize-v1",
        "mask_sha256": hashlib.sha256(mask.encode()).hexdigest(),
        "candidate_source_mutated": False,
        "authority_allowed": "attempt and persistence measurement",
        "authority_forbidden": ["patch", "repair authority", "count", "release"],
    }
    Path(ledger_path).with_suffix(".instrumentation.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


_install()

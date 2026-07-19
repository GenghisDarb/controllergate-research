#!/usr/bin/env python3
"""Structured Audioread issue-144 import and exact-test observation."""

from __future__ import annotations

import argparse
import importlib
import json
import sys


NODES = [
    "test/test_audioread.py::test_audioread_early_exit[test-1]",
    "test/test_audioread.py::test_audioread_early_exit[test-2]",
    "test/test_audioread.py::test_audioread_full[test-1]",
    "test/test_audioread.py::test_audioread_full[test-2]",
]


def import_observation(name: str) -> dict:
    try:
        module = importlib.import_module(name)
        return {"module": name, "status": "IMPORTED", "origin": getattr(module, "__file__", None)}
    except Exception as exc:
        return {"module": name, "status": "FAILED", "exception_type": type(exc).__name__, "exception_text": str(exc)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route", choices=("rawread", "unrelated_backend"), required=True)
    parser.add_argument("--run-exact-tests", action="store_true")
    args = parser.parse_args()
    aifc = import_observation("aifc")
    route_module = "audioread.rawread" if args.route == "rawread" else "audioread.ffdec"
    route = import_observation(route_module)
    backend_observation: dict = {}
    try:
        import audioread
        backends = audioread.available_backends()
        backend_observation = {"status": "OBSERVED", "backend_count": len(backends), "backend_names": [item.__name__ for item in backends]}
    except Exception as exc:
        backend_observation = {"status": "FAILED", "exception_type": type(exc).__name__, "exception_text": str(exc)}
    pytest_return_code = None
    if args.run_exact_tests:
        import pytest
        pytest_return_code = int(pytest.main([*NODES, "-q", "--tb=short"]))
    result = {
        "route": args.route, "aifc": aifc, "route_import": route,
        "backend_discovery": backend_observation, "exact_test_nodes": NODES,
        "exact_test_return_code": pytest_return_code,
    }
    print("BATCH100_AUDIOREAD_OBSERVATION=" + json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if route["status"] == "IMPORTED" and (pytest_return_code in {None, 0}) else 1


if __name__ == "__main__":
    raise SystemExit(main())

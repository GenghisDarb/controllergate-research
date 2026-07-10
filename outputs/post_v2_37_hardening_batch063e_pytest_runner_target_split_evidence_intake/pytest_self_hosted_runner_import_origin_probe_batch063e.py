from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

candidate_checkout = Path(os.environ["CONTROLLERGATE_CANDIDATE_CHECKOUT"]).resolve()
candidate_src = Path(os.environ["CONTROLLERGATE_CANDIDATE_SRC"]).resolve()
batch063d_version = os.environ.get("CONTROLLERGATE_BATCH063D_NORMALIZED_VERSION")
result = {
    "python_executable": sys.executable,
    "working_directory": os.getcwd(),
    "sys_path": sys.path,
    "candidate_checkout_path": str(candidate_checkout),
    "candidate_src_path": str(candidate_src),
    "batch063d_normalized_version": batch063d_version,
    "pytest_spec_origin": None,
    "pytest_file": None,
    "pytest_version": None,
    "import_succeeded": False,
    "import_exception": None,
    "traceback": None,
}
spec = importlib.util.find_spec("pytest")
result["pytest_spec_origin"] = spec.origin if spec else None
try:
    import pytest  # noqa: F401
    result["pytest_file"] = getattr(pytest, "__file__", None)
    result["pytest_version"] = getattr(pytest, "__version__", None)
    result["import_succeeded"] = True
except BaseException as exc:  # probe records import-origin failure without mutating source
    result["import_exception"] = f"{type(exc).__name__}: {exc}"
    result["traceback"] = traceback.format_exc()

origin = result["pytest_file"] or result["pytest_spec_origin"] or ""
try:
    result["runner_import_origin_equals_candidate_checkout"] = bool(origin) and Path(origin).resolve().is_relative_to(candidate_checkout)
except AttributeError:
    result["runner_import_origin_equals_candidate_checkout"] = bool(origin) and str(Path(origin).resolve()).startswith(str(candidate_checkout))
print(json.dumps(result, indent=2, sort_keys=True))

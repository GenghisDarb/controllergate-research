from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Any

from controllergate.core.evidence import write_json_deterministic
from controllergate.runtime.log_custody import record_completed_command
from controllergate.runtime.oci_probe_sandbox import create_inspect_run_remove
from controllergate.runtime.resource_policy import ResourcePolicy


PHASES = (
    (0, "container_security_inspection", "true"),
    (1, "runtime_identity", "python --version"),
    (2, "pytest_import", "{setup}; /venv/bin/python -c \"import pytest; print(pytest.__version__); print(pytest.__file__)\""),
    (3, "target_import", "{setup}; /venv/bin/python -c \"import nbclient; print(nbclient.__version__); print(nbclient.__file__)\""),
    (4, "provider_plugin_inventory", "{setup}; /venv/bin/python -m pip list --format=json"),
    (5, "pytest_configuration_parse", "{setup}; /venv/bin/python -c \"from _pytest.config import get_config; c=get_config(); c.parse(['tests/test_cli.py']); print(c.inipath)\""),
    (6, "collection_bootstrap", "{setup}; /venv/bin/python -c \"from pathlib import Path; compile(Path('tests/conftest.py').read_text(), 'tests/conftest.py', 'exec'); compile(Path('tests/test_cli.py').read_text(), 'tests/test_cli.py', 'exec'); print('bootstrap_compile_pass')\""),
    (7, "exact_target_collection", "{setup}; /venv/bin/python -m pytest --collect-only -q -p no:cacheprovider tests/test_cli.py"),
    (8, "node_set_validation", "{setup}; /venv/bin/python -m pytest --collect-only -q -p no:cacheprovider tests/test_cli.py"),
)

SETUP = "mkdir -p /tmp/home /tmp/cache /tmp/config /tmp/jupyter-data /tmp/jupyter-runtime /tmp/ipython /tmp/mpl /tmp/pycache; python -m venv /venv; /venv/bin/pip install --disable-pip-version-check --no-index --find-links /wheelhouse 'nbclient[test]'"


def phase_plan() -> list[dict[str, Any]]:
    return [{"phase": number, "phase_id": name, "command_template": command, "test_bodies_allowed": False} for number, name, command in PHASES]


def run_phases(output_dir: Path, *, image_digest: str, source: Path, wheelhouse: Path, environment: dict[str, str], authoritative: bool, stop_at_first_failure: bool = True) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    first_failure = None
    for number, phase_id, template in PHASES:
        if first_failure is not None and stop_at_first_failure:
            results.append({"phase": number, "phase_id": phase_id, "operation_status": "NOT_RUN", "gate_decision": "BLOCK", "blocker": "upstream_phase_blocked"})
            continue
        shell = template.format(setup=SETUP)
        start = datetime.now(timezone.utc).isoformat()
        result = create_inspect_run_remove(image_digest=image_digest, source=source, wheelhouse=wheelhouse, shell_script=shell, name=f"controllergate-068h1-p{number}", resource_policy=ResourcePolicy(timeout_seconds=300), environment=environment)
        stop = datetime.now(timezone.utc).isoformat()
        stdout = str(result.get("stdout") or ""); stderr = str(result.get("stderr") or result.get("output") or "")
        custody = record_completed_command(output_dir, f"probe_run{number}", argv=["sh", "-lc", shell], cwd="/source", env=environment, container_identity=result.get("container_id"), image_digest=image_digest, timeout_seconds=300, returncode=int(result.get("returncode", 1 if result.get("status") != "PASS" else 0)), stdout=stdout, stderr=stderr, started_at=start, stopped_at=stop, termination_signal="TIMEOUT" if result.get("timed_out") else None, phase_classification="authoritative" if authoritative else "diagnostic_only")
        nodes = sorted({line.strip() for line in (stdout + "\n" + stderr).splitlines() if line.strip().startswith("tests/test_cli.py::")})
        phase = {
            "phase": number, "phase_id": phase_id, "operation_status": "COMPLETED",
            "gate_decision": "PASS" if result.get("status") == "PASS" else "BLOCK",
            "returncode": result.get("returncode"), "container_id": result.get("container_id"),
            "security_observation": result.get("security_observation"), "container_removed": result.get("container_removed"),
            "raw_output_sha256": custody["hashes"]["raw_combined_sha256"], "secret_scan_status": custody["secret_scan"]["status"],
            "node_ids": nodes, "node_count": len(nodes), "test_bodies_executed": 0, "authoritative": authoritative,
            "blocker": result.get("blocker"),
        }
        results.append(phase)
        write_json_deterministic(output_dir / f"probe_run{number}_phase_decision.json", phase)
        if phase["gate_decision"] != "PASS": first_failure = phase
    return {"status": "PASS" if first_failure is None else "BLOCK", "results": results, "first_failure": first_failure, "test_bodies_executed": 0}


def classify_raw_failure(text: str) -> str:
    lowered = text.lower()
    patterns = [
        ("pytest_configuration_parse_error", ("usageerror", "error in pyproject", "unknown config option")),
        ("provider_import_failure", ("modulenotfounderror", "importerror")),
        ("warning_promoted_to_error", ("warning", "warnings")),
        ("filesystem_runtime_path_failure", ("permission denied", "read-only file system")),
        ("interpreter_compatibility_failure", ("python 3.13", "removed in python")),
    ]
    matches = [name for name, needles in patterns if any(needle in lowered for needle in needles)]
    return matches[0] if len(matches) == 1 else ("multi_signal_collection_failure" if matches else "unclassified_collection_failure")

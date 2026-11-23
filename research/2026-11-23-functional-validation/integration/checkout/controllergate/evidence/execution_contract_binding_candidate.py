"""Prevent a Batch100 execution from silently acquiring a different v4 identity.

The two inventories have explicitly different versions. Shared cells may execute
only when every consumed command, environment, fixture and provider field agrees.
New cells stay unmaterialized until their own providers/fixtures are implemented.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .registry_bound_semantics_candidate import canonical_hash

ROOT = Path(__file__).resolve().parents[2]
PRODUCER_PATH = "configs/batch100_counterfactual_cell_registry_v2.jsonl"
PROVIDER_PATH = "outputs/post_v2_37_hardening_batch100_matched_counterfactual_execution_causal_ownership_architecture_gain_master_roadmap_lock/matched_counterfactual/provider_capsule_registry_v2.jsonl"
COMPARED_FIELDS = ("cell_id", "candidate_id", "program_id", "cell_role", "exact_argv",
                   "exact_cwd", "exact_environment", "command_hash", "environment_hash",
                   "fixture_hash", "provider_capsule_id", "platform")


def rows(data: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in data.decode().splitlines() if line.strip()]


def contract_errors(producer: dict[str, Any], declared: dict[str, Any]) -> list[str]:
    errors = ["producer_declared_mismatch:" + k for k in COMPARED_FIELDS
              if canonical_hash(producer.get(k)) != canonical_hash(declared.get(k))]
    for row, label in ((producer, "producer"), (declared, "declared")):
        for field, value in (("command_hash", row.get("exact_argv")),
                             ("environment_hash", row.get("exact_environment"))):
            if row.get(field) != canonical_hash(value):
                errors.append(label + "_" + field + "_not_derived_from_contract")
    return errors


def inventory_preflight(candidate_id: str, declared_rows: list[dict[str, Any]]) -> dict[str, Any]:
    producer_rows = rows((ROOT / PRODUCER_PATH).read_bytes())
    providers = {r["capsule_id"]: r for r in rows((ROOT / PROVIDER_PATH).read_bytes())}
    producer = {r["cell_id"]: r for r in producer_rows if r["candidate_id"] == candidate_id}
    declared = {r["cell_id"]: r for r in declared_rows if r["candidate_id"] == candidate_id}
    mismatches = {}
    for cell_id, row in producer.items():
        errors = contract_errors(row, declared.get(cell_id, {}))
        if row.get("provider_capsule_id") not in providers:
            errors.append("producer_provider_not_materialized")
        if errors:
            mismatches[cell_id] = errors
    return {"status": "PASS_SHARED_PRODUCER_INVENTORY" if not mismatches else "BLOCK",
            "candidate_id": candidate_id, "producer_registry_path": PRODUCER_PATH,
            "producer_registry_sha256": hashlib.sha256((ROOT / PRODUCER_PATH).read_bytes()).hexdigest(),
            "producer_cell_count": len(producer), "declared_cell_count": len(declared),
            "new_cells_not_executable_by_this_producer": sorted(set(declared) - set(producer)),
            "mismatches": mismatches,
            "scope": "pre-execution contract compatibility; not exact provider availability"}


def make_execution_binding(cell: dict[str, Any], *, registry_bytes: bytes,
                           provider: dict[str, Any], source_commit: str,
                           observed_argv: list[str], observed_cwd: str,
                           replay_index: int, fixture_mode: str) -> dict[str, Any]:
    return {"version": "raw-execution-contract-binding-local-v1",
            "producer_registry_path": PRODUCER_PATH,
            "producer_registry_sha256": hashlib.sha256(registry_bytes).hexdigest(),
            "producer_cell_hash": canonical_hash(cell),
            "command_hash": cell["command_hash"], "environment_hash": cell["environment_hash"],
            "fixture_hash": cell["fixture_hash"], "provider_capsule_id": cell["provider_capsule_id"],
            "producer_provider_capsule_hash": provider["capsule_hash"],
            "source_commit": source_commit, "replay_index": replay_index, "fixture_mode": fixture_mode,
            "observed_argv": observed_argv, "observed_cwd": observed_cwd}


def normalized(value: str, platform: str) -> str:
    return (value.replace("\\", "/") if platform == "windows" else value).rstrip("/")


def normalized_argv(argv: list[str], platform: str) -> list[str]:
    """Normalize separators only for explicit custody-redacted absolute path slots.

Option names, relative filenames, test node strings, numbers and URLs retain
their literal bytes. Never strip a trailing slash from a command argument.
    """
    prefixes = ("${RUNTIME_ROOT}/", "${RUNTIME_ROOT}\\", "${REPOSITORY_ROOT}/", "${REPOSITORY_ROOT}\\")
    if not isinstance(argv, list) or any(not isinstance(x, str) for x in argv):
        raise ValueError("argv_not_string_array")
    return [x.replace("\\", "/") if platform == "windows" and x.startswith(prefixes) else x for x in argv]


def expected_materialization(cell: dict[str, Any], replay_index: int, platform: str,
                             fixture_mode: str) -> dict[str, Any]:
    """Exact symbolic replay of Batch100 main + prepare_fixture, not guessed paths.

Source references: main replay/source/provider/consumer layout, venv_exe and
venv_python, prepare_fixture, expansion and cwd branch. Absolute runtime and
repository roots are custody-redacted by the original producer's sanitize().
    """
    if type(replay_index) is not int or replay_index not in (1, 2):
        raise ValueError("unsupported_replay_index")
    if platform not in ("linux", "windows") or platform != cell["platform"]:
        raise ValueError("producer_platform_mismatch")
    if fixture_mode != "batch102_exact":
        raise ValueError("v4_requires_explicit_batch102_fixture_mode")
    replay = "${RUNTIME_ROOT}/cells/" + cell["cell_id"].replace(":", "_") + f"/replay-{replay_index}"
    source = replay + "/source"
    provider = replay + "/provider"
    consumer = replay + "/consumer"
    candidate = cell["candidate_id"]
    if candidate == "incident_poetry_10974_init_duplicate_name":
        consumer = replay + ("/my project with spaces" if "spaces" in cell["cell_name"] else "/my-project-with-spaces")
    values = {"RUNTIME_ROOT": "${RUNTIME_ROOT}", "LOOPBACK_PORT": "0"}
    if candidate == "darker_issue_112_relative_git_dir":
        values["ABS_GIT_DIR"] = consumer + "/.git"
    elif candidate == "py_bugger_issue_65":
        values.update(TARGET_FILE=consumer + "/target.py",
            INSTRUMENTATION_DIR="${RUNTIME_ROOT}/instrumentation/" + candidate,
            EXTERNAL_ACCOUNTING_HARNESS="${REPOSITORY_ROOT}/scripts/batch100_pybugger_internal_accounting_harness.py")
    elif candidate == "audioread_144_py313_aifc_removed":
        values["AUDIOREAD_HARNESS"] = "${REPOSITORY_ROOT}/scripts/batch100_audioread_harness.py"
    argv = list(cell["exact_argv"])
    for i, token in enumerate(argv):
        for key, value in values.items():
            token = token.replace("${" + key + "}", value)
        argv[i] = token
    executable = argv[0]
    if executable in {"python", "darker", "py-bugger", "poetry", "openbb"}:
        argv[0] = provider + ("/Scripts/" + executable + ".exe" if platform == "windows" else "/bin/" + executable)
    cwd = consumer if cell["exact_cwd"].endswith("/consumer") and candidate in {
        "darker_issue_112_relative_git_dir", "py_bugger_issue_65", "incident_poetry_10974_init_duplicate_name"} else source
    return {"argv": argv, "cwd": cwd}


def verify_execution_binding(binding: Any, declared: dict[str, Any], fresh: dict[str, Any]) -> list[str]:
    if not isinstance(binding, dict):
        return ["raw_execution_contract_binding_missing"]
    data = (ROOT / PRODUCER_PATH).read_bytes()
    old = {r["cell_id"]: r for r in rows(data)}.get(declared.get("cell_id"))
    if old is None:
        return ["producer_does_not_implement_declared_cell"]
    errors = contract_errors(old, declared)
    expected = {"version": "raw-execution-contract-binding-local-v1",
                "producer_registry_path": PRODUCER_PATH,
                "producer_registry_sha256": hashlib.sha256(data).hexdigest(),
                "producer_cell_hash": canonical_hash(old),
                "command_hash": old["command_hash"], "environment_hash": old["environment_hash"],
                "fixture_hash": old["fixture_hash"], "provider_capsule_id": old["provider_capsule_id"],
                "source_commit": fresh.get("source_commit"), "replay_index": fresh.get("replay_index"),
                "fixture_mode": "batch102_exact"}
    providers = {r["capsule_id"]: r for r in rows((ROOT / PROVIDER_PATH).read_bytes())}
    provider = providers.get(old.get("provider_capsule_id"))
    if provider is None:
        errors.append("producer_provider_capsule_missing")
    else:
        expected["producer_provider_capsule_hash"] = provider["capsule_hash"]
    for key, value in expected.items():
        if canonical_hash(binding.get(key)) != canonical_hash(value):
            errors.append("raw_execution_binding_mismatch:" + key)
    for fresh_key, cell_key in (("exact_argv_hash", "command_hash"), ("environment_hash", "environment_hash"), ("fixture_hash", "fixture_hash")):
        if fresh.get(fresh_key) != declared.get(cell_key):
            errors.append("fresh_contract_mismatch:" + fresh_key)
    if declared.get("required_source_commit") and fresh.get("source_commit") != declared["required_source_commit"]:
        errors.append("required_source_commit_mismatch")
    if not isinstance(binding.get("observed_argv"), list) or not binding["observed_argv"]:
        errors.append("observed_argv_missing")
    if not isinstance(binding.get("observed_cwd"), str) or not binding["observed_cwd"]:
        errors.append("observed_cwd_missing")
    try:
        materialized = expected_materialization(old, fresh.get("replay_index"), fresh.get("platform"), binding.get("fixture_mode"))
        if normalized_argv(binding.get("observed_argv", []), fresh.get("platform")) != materialized["argv"]:
            errors.append("observed_argv_not_declared_materialization")
        if normalized(binding.get("observed_cwd", ""), fresh.get("platform")) != materialized["cwd"]:
            errors.append("observed_cwd_not_declared_materialization")
    except (ValueError, TypeError, AttributeError) as exc:
        errors.append("materialization_unresolved:" + str(exc))
    # A new provider capsule is bound separately by fresh-execution verification.
    # The old provider hash records requested provenance; it is not an availability claim.
    return errors

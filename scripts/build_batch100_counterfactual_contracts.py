#!/usr/bin/env python3
"""Freeze candidate-specific Batch100 intervention programs before outcomes."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.amds.matched_counterfactual_v10 import canonical_hash, validate_program


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def cell(candidate: str, program: str, name: str, *, argv: list[str], env: dict[str, str], fixture: dict[str, Any], factors: dict[str, Any], role: str, platform: str = "linux", provider: str, service: dict[str, Any] | None = None) -> dict[str, Any]:
    row = {
        "cell_id": f"cell:{program}:{name}", "candidate_id": candidate, "program_id": program,
        "cell_name": name, "cell_role": role, "platform": platform, "provider_capsule_id": provider,
        "exact_argv": argv, "exact_cwd": f"${{RUNTIME_ROOT}}/batch100/{candidate}/{name}/consumer",
        "exact_environment": env, "fixture": fixture, "factor_values": factors,
        "service_identity": service, "network_policy": "loopback_only" if service else "none",
        "fresh_workspace_count": 2, "replay_count": 2, "resource_budget": {"timeout_seconds": 1800, "processes": 16, "memory_mb": 4096},
        "truth_access": 0, "private_tld_access": 0, "patch_operations": 0,
        "authority_allowed": "truth-blind candidate observation",
        "authority_forbidden": ["causal ownership before pair join", "patch", "repair count", "release"],
    }
    row["fixture_hash"] = canonical_hash(fixture)
    row["command_hash"] = canonical_hash(argv)
    row["environment_hash"] = canonical_hash(env)
    row["cell_hash"] = canonical_hash(row)
    return row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capsule-root", type=Path, required=True)
    args = parser.parse_args()
    sources = {row["candidate_id"]: row for row in read_jsonl(args.capsule_root / "source_capsule_registry_v1.jsonl")}
    provider_rows = read_jsonl(args.capsule_root / "provider_capsule_registry_v2.jsonl")
    providers = {row["capsule_id"]: row for row in provider_rows}
    programs: list[dict] = []
    cells: list[dict] = []
    semantics: list[dict] = []

    def add(candidate: str, sub: str, incident: dict, control: dict, exclusions: list[dict], changed: list[str], held: list[str], incident_predicate: dict, control_predicate: dict, factors: dict, pair_kind: str = "single_factor") -> None:
        program_id = incident["program_id"]
        program = {
            "program_id": program_id, "candidate_id": candidate, "sub_incident_id": sub,
            "source_capsule_hash": sources[candidate]["capsule_hash"],
            "provider_capsule_ids": sorted({row["provider_capsule_id"] for row in [incident, control, *exclusions]}),
            "incident_cell": {key: incident[key] for key in ("cell_id", "fixture_hash", "command_hash", "environment_hash")},
            "control_cell": {key: control[key] for key in ("cell_id", "fixture_hash", "command_hash", "environment_hash")},
            "additional_exclusion_cells": [row["cell_id"] for row in exclusions],
            "factor_names": sorted(factors), "factor_values": factors,
            "exact_argv": {row["cell_id"]: row["exact_argv"] for row in [incident, control, *exclusions]},
            "exact_cwd": {row["cell_id"]: row["exact_cwd"] for row in [incident, control, *exclusions]},
            "exact_environment": {row["cell_id"]: row["exact_environment"] for row in [incident, control, *exclusions]},
            "fixture_identity": {row["cell_id"]: row["fixture_hash"] for row in [incident, control, *exclusions]},
            "service_identity": {row["cell_id"]: row["service_identity"] for row in [incident, control, *exclusions]},
            "held_invariants": held, "changed_dimensions": changed,
            "expected_semantic_schema": f"batch100-{sub}-observation-v1",
            "incident_predicate": incident_predicate, "control_predicate": control_predicate,
            "negative_controls": [row["cell_id"] for row in exclusions],
            "replay_count": 2, "execution_order": ["AB", "BA"],
            "order_randomization_seed": int(canonical_hash([candidate, sub])[:8], 16),
            "cleanup": {"processes": "terminated", "workspaces": "deleted_after_receipt", "provider_reuse": False},
            "resource_budget": {"timeout_seconds_per_cell": 1800, "processes": 16, "memory_mb": 4096},
            "pair_kind": pair_kind,
            "authority_allowed": "matched sensitivity or interaction evidence at executed depth",
            "authority_forbidden": ["truth access", "TLD content access", "patch", "repair count", "release"],
        }
        program["program_hash"] = canonical_hash(program)
        errors = validate_program(program)
        if errors:
            raise ValueError(f"{program_id}: {errors}")
        programs.append(program)
        cells.extend([incident, control, *exclusions])
        semantic = {
            "program_id": program_id, "candidate_id": candidate, "sub_incident_id": sub,
            "schema_id": program["expected_semantic_schema"], "incident_predicate": incident_predicate,
            "control_predicate": control_predicate, "forbidden_shortcuts": ["return_code_only", "stdout_marker_only", "sealed_truth", "future_fix"],
            "independent_verifier": "controllergate.amds.matched_counterfactual_v10",
            "authority_allowed": "semantic outcome classification only",
            "authority_forbidden": ["ownership without matched evidence", "patch", "release"],
        }
        semantic["registry_hash"] = canonical_hash(semantic)
        semantics.append(semantic)

    # Darker: relative/absolute primary pair plus unset and invalid absolute controls.
    candidate = "darker_issue_112_relative_git_dir"; pid = "batch100-darker-112-git-dir"
    fixture = {"type": "deterministic-git-consumer", "tracked_path": "src/example.py", "dirty_change": "x = 2", "initial": "x=1\n"}
    p = "provider:darker_issue_112_relative_git_dir:incident-series"
    darker_argv = ["darker", "--check", "src"]
    trace = {"GIT_TRACE": "1", "CONTROLLERGATE_INSTRUMENTATION": "git-trace-v1"}
    a = cell(candidate, pid, "relative-git-dir", argv=darker_argv, env={**trace, "GIT_DIR": ".git", "LC_ALL": "C.UTF-8"}, fixture=fixture, factors={"git_dir": "relative", "route": "darker"}, role="incident", provider=p)
    b = cell(candidate, pid, "absolute-git-dir", argv=darker_argv, env={**trace, "GIT_DIR": "${ABS_GIT_DIR}", "LC_ALL": "C.UTF-8"}, fixture=fixture, factors={"git_dir": "absolute", "route": "darker"}, role="control", provider=p)
    c = cell(candidate, pid, "git-dir-unset", argv=darker_argv, env={**trace, "LC_ALL": "C.UTF-8"}, fixture=fixture, factors={"git_dir": "unset", "route": "darker"}, role="exclusion", provider=p)
    d = cell(candidate, pid, "invalid-absolute", argv=darker_argv, env={**trace, "GIT_DIR": "${RUNTIME_ROOT}/missing/.git", "LC_ALL": "C.UTF-8"}, fixture=fixture, factors={"git_dir": "invalid_absolute", "route": "darker"}, role="negative", provider=p)
    e = cell(candidate, pid, "direct-git-relative", argv=["git", "diff", "--name-only", "HEAD", "--", "src"], env={**trace, "GIT_DIR": ".git", "LC_ALL": "C.UTF-8"}, fixture=fixture, factors={"git_dir": "relative", "route": "direct_git"}, role="exclusion", provider=p)
    f = cell(candidate, pid, "direct-git-absolute", argv=["git", "diff", "--name-only", "HEAD", "--", "src"], env={**trace, "GIT_DIR": "${ABS_GIT_DIR}", "LC_ALL": "C.UTF-8"}, fixture=fixture, factors={"git_dir": "absolute", "route": "direct_git"}, role="exclusion", provider=p)
    add(candidate, "relative_git_dir", a, b, [c, d, e, f], ["environment.GIT_DIR"], ["source", "wheel", "consumer tree", "dirty state", "cwd", "command", "Git", "locale", "budget"], {"not_a_git_repository": True}, {"not_a_git_repository": False}, {"git_dir": ["relative", "absolute"], "route": ["darker", "direct_git"]}, "factorial_diagnostic")

    # Py-bugger: CLI accounting with externally injected deterministic attempt mask.
    candidate = "py_bugger_issue_65"; pid = "batch100-py-bugger-65-accounting"; p = "provider:py_bugger_issue_65:reported-cli-sensitivity"
    fixture = {"type": "deterministic-python-target", "path": "target.py", "sha_seed": "batch100-py-bugger-65", "requested_mutations": 10}
    argv = ["py-bugger", "--target-file", "${TARGET_FILE}", "-n", "10"]
    instrumentation = {"PYTHONPATH": "${INSTRUMENTATION_DIR}", "CONTROLLERGATE_INSTRUMENTATION": "pybugger-accounting-sitecustomize-v1", "PY_BUGGER_RANDOM_SEED": "10065"}
    a = cell(candidate, pid, "all-attempts-succeed", argv=argv, env={**instrumentation, "CONTROLLERGATE_MUTATION_MASK": "1111111111", "PYTHONHASHSEED": "10065"}, fixture=fixture, factors={"success_mask": "all", "route": "cli"}, role="incident", provider=p)
    b = cell(candidate, pid, "subset-attempts-fail", argv=argv, env={**instrumentation, "CONTROLLERGATE_MUTATION_MASK": "1101010011", "PYTHONHASHSEED": "10065"}, fixture=fixture, factors={"success_mask": "subset", "route": "cli"}, role="control", provider=p)
    c = cell(candidate, pid, "internal-all-success", argv=["python", "${EXTERNAL_ACCOUNTING_HARNESS}", "--target", "${TARGET_FILE}", "--mask", "1111111111"], env={**instrumentation, "CONTROLLERGATE_MUTATION_MASK": "1111111111", "PYTHONHASHSEED": "10065"}, fixture=fixture, factors={"success_mask": "all", "route": "internal"}, role="exclusion", provider=p)
    d = cell(candidate, pid, "internal-subset-failure", argv=["python", "${EXTERNAL_ACCOUNTING_HARNESS}", "--target", "${TARGET_FILE}", "--mask", "1101010011"], env={**instrumentation, "CONTROLLERGATE_MUTATION_MASK": "1101010011", "PYTHONHASHSEED": "10065"}, fixture=fixture, factors={"success_mask": "subset", "route": "internal"}, role="exclusion", provider=p)
    add(candidate, "mutation_count_accounting", a, b, [c, d], ["external_attempt_success_mask"], ["source", "provider", "target input", "requested count", "seed", "budget"], {"reported_count_basis": "attempted"}, {"reported_count_basis": "successful_or_persisted"}, {"success_mask": ["all", "subset"], "route": ["cli", "internal"]}, "factorial_diagnostic")

    # Cloudpickle: separate TypeVar and distutils programs.
    candidate = "cloudpickle_507_py313_typevar_distutils"; base = "tests/cloudpickle_test.py::CloudPickleTest::"
    pid = "batch100-cloudpickle-507-typevar"; pc = "provider:cloudpickle_507_py313_typevar_distutils:supported-control"; pi = "provider:cloudpickle_507_py313_typevar_distutils:incident-no-setuptools"
    nodes = [base + name for name in ("test_generic_subclass", "test_generic_type", "test_locally_defined_class_with_type_hints", "test_pickle_dynamic_typevar", "test_pickle_dynamic_typevar_memoization", "test_pickle_dynamic_typevar_tracking")]
    fixture = {"type": "source-test-nodes", "nodes": nodes}
    a = cell(candidate, pid, "python312-typevar", argv=["python", "-m", "pytest", *nodes, "-q", "--tb=short"], env={}, fixture=fixture, factors={"python": "3.12"}, role="incident", provider=pi)
    b = cell(candidate, pid, "python311-typevar", argv=["python", "-m", "pytest", *nodes, "-q", "--tb=short"], env={}, fixture=fixture, factors={"python": "3.11"}, role="control", provider=pc)
    add(candidate, "typevar_weakref", a, b, [], ["provider.python"], ["source", "tests", "dependencies", "command", "runner", "harness"], {"exception_type": "TypeError", "contact": "_decompose_typevar"}, {"all_nodes_pass": True}, {"python": ["3.11", "3.12"]})
    pid = "batch100-cloudpickle-507-distutils"; ps = "provider:cloudpickle_507_py313_typevar_distutils:incident-with-setuptools"
    nodes = [base + "test_module_importability"]
    fixture = {"type": "source-test-nodes", "nodes": nodes}
    a = cell(candidate, pid, "python312-no-setuptools", argv=["python", "-m", "pytest", *nodes, "-q", "--tb=short"], env={"SETUPTOOLS_COMPATIBILITY": "absent"}, fixture=fixture, factors={"python": "3.12", "setuptools": "absent"}, role="incident", provider=pi)
    b = cell(candidate, pid, "python311-no-setuptools", argv=["python", "-m", "pytest", *nodes, "-q", "--tb=short"], env={"SETUPTOOLS_COMPATIBILITY": "absent"}, fixture=fixture, factors={"python": "3.11", "setuptools": "absent"}, role="control", provider=pc)
    c = cell(candidate, pid, "python312-with-setuptools", argv=["python", "-m", "pytest", *nodes, "-q", "--tb=short"], env={"SETUPTOOLS_COMPATIBILITY": "present"}, fixture=fixture, factors={"python": "3.12", "setuptools": "present"}, role="exclusion", provider=ps)
    add(candidate, "distutils_removed", a, b, [c], ["provider.python", "provider.setuptools"], ["source", "test node", "command", "runner", "harness"], {"exception_type": "ModuleNotFoundError", "module": "distutils"}, {"module_importable": True}, {"python": ["3.11", "3.12"], "setuptools": ["absent", "present"]}, "factorial")

    # Freezegun exact beta provider is explicitly unresolved unless Actions can authenticate it.
    candidate = "freezegun_547_py313_datetimes_assertion"; pid = "batch100-freezegun-547-three-nodes"; pc = "provider:freezegun_547_py313_datetimes_assertion:supported-control"; pi = "provider:freezegun_547_py313_datetimes_assertion:exact-incident"
    nodes = ["tests/test_datetimes.py::TestUnitTestMethodDecorator::test_method_decorator_works_on_unittest_kwarg_frozen_time", "tests/test_datetimes.py::TestUnitTestMethodDecorator::test_method_decorator_works_on_unittest_kwarg_frozen_time_with_func", "tests/test_datetimes.py::TestUnitTestMethodDecorator::test_method_decorator_works_on_unittest_kwarg_hello"]
    fixture = {"type": "exact-source-test-nodes", "nodes": nodes, "timezone": "UTC"}
    a = cell(candidate, pid, "python3130b1", argv=["python", "-m", "pytest", *nodes, "-q", "--tb=short"], env={"TZ": "UTC"}, fixture=fixture, factors={"python": "3.13.0b1"}, role="incident", provider=pi)
    b = cell(candidate, pid, "python312", argv=["python", "-m", "pytest", *nodes, "-q", "--tb=short"], env={"TZ": "UTC"}, fixture=fixture, factors={"python": "3.12"}, role="control", provider=pc)
    add(candidate, "datetime_unittest_decorator", a, b, [], ["provider.python"], ["source", "tests", "dependencies", "command", "locale", "timezone", "fixture"], {"failed_node_count": 3, "actual_relation": "FakeDate != datetime"}, {"failed_node_count": 0}, {"python": ["3.12", "3.13.0b1"]})

    # Audioread provider/source-route factorial.
    candidate = "audioread_144_py313_aifc_removed"; pid = "batch100-audioread-144-aifc"; pc = "provider:audioread_144_py313_aifc_removed:supported-control"; pi = "provider:audioread_144_py313_aifc_removed:exact-incident"
    nodes = ["test/test_audioread.py::test_audioread_early_exit[test-1]", "test/test_audioread.py::test_audioread_early_exit[test-2]", "test/test_audioread.py::test_audioread_full[test-1]", "test/test_audioread.py::test_audioread_full[test-2]"]
    fixture = {"type": "source-audio-fixtures", "nodes": nodes}
    harness = ["python", "${AUDIOREAD_HARNESS}"]
    a = cell(candidate, pid, "python313-rawread", argv=[*harness, "--route", "rawread", "--run-exact-tests"], env={}, fixture=fixture, factors={"python": "3.13.0b2", "route": "rawread"}, role="incident", provider=pi)
    b = cell(candidate, pid, "python312-rawread", argv=[*harness, "--route", "rawread", "--run-exact-tests"], env={}, fixture=fixture, factors={"python": "3.12", "route": "rawread"}, role="control", provider=pc)
    c = cell(candidate, pid, "python313-unrelated", argv=[*harness, "--route", "unrelated_backend", "--run-exact-tests"], env={}, fixture=fixture, factors={"python": "3.13.0b2", "route": "unrelated_backend"}, role="exclusion", provider=pi)
    d = cell(candidate, pid, "python312-unrelated", argv=[*harness, "--route", "unrelated_backend", "--run-exact-tests"], env={}, fixture=fixture, factors={"python": "3.12", "route": "unrelated_backend"}, role="exclusion", provider=pc)
    add(candidate, "aifc_removed", a, b, [c, d], ["provider.python"], ["source", "fixtures", "command per route", "dependencies", "runner"], {"exception_type": "ModuleNotFoundError", "module": "aifc"}, {"rawread_import": "success"}, {"python": ["3.12", "3.13.0b2"], "route": ["rawread", "unrelated_backend"]}, "factorial_diagnostic")

    # pytest exact nodes with warning-mode factor.
    candidate = "pytest_13480_wdefault_unraisable_threadexception"; pid = "batch100-pytest-13480-warning-mode"; p = "provider:pytest_13480_wdefault_unraisable_threadexception:exact-incident"
    nodes = ["testing/test_threadexception.py::test_unhandled_thread_exception_after_teardown", "testing/test_unraisableexception.py::test_refcycle_unraisable", "testing/test_warnings.py::test_works_with_filterwarnings"]
    fixture = {"type": "exact-pytester-nodes", "nodes": nodes}
    a = cell(candidate, pid, "wdefault", argv=["python", "-m", "pytest", *nodes, "-Wdefault", "-q", "--tb=short"], env={}, fixture=fixture, factors={"outer_warning_mode": "default"}, role="incident", provider=p)
    b = cell(candidate, pid, "warning-default-unchanged", argv=["python", "-m", "pytest", *nodes, "-q", "--tb=short"], env={}, fixture=fixture, factors={"outer_warning_mode": "interpreter_default"}, role="control", provider=p)
    add(candidate, "warning_default_nested_pytester", a, b, [], ["command.warning_mode"], ["source", "provider", "nodes", "dependencies", "cwd", "runner", "inputs", "budget"], {"outer_return_code": 1, "collection_return_code_4": False}, {"outer_return_code": 0}, {"outer_warning_mode": ["default", "interpreter_default"]})

    # OpenBB modular/flattened secondary-source topology.
    candidate = "incident_openbb_7585_modular_openapi_reproducer"; pid = "batch100-openbb-7585-topology"; p = "provider:incident_openbb_7585_modular_openapi_reproducer:incident"
    fixture_mod = {"type": "OpenAPI-3.1", "secondary_commit": "901d6209e5738b0cbb42d48553c51fdc5f98bd7e", "topology": "modular-$ref"}
    fixture_flat = {**fixture_mod, "topology": "deterministically-flattened"}
    argv = ["openbb", "--generate-spec", "--server", "http://127.0.0.1:${LOOPBACK_PORT}", "--openapi-path", "/openapi.yaml", "--output", "eodhd.spec"]
    service = {"protocol": "HTTP-loopback", "readiness": "/openapi.yaml", "deterministic_port_policy": "broker-allocated"}
    a = cell(candidate, pid, "modular", argv=argv, env={}, fixture=fixture_mod, factors={"reference_topology": "modular"}, role="incident", provider=p, service=service)
    b = cell(candidate, pid, "flattened", argv=argv, env={}, fixture=fixture_flat, factors={"reference_topology": "flattened"}, role="control", provider=p, service=service)
    c = cell(candidate, pid, "service-unavailable", argv=argv, env={}, fixture=fixture_mod, factors={"service": "unavailable"}, role="negative", provider=p, service=service)
    d = cell(candidate, pid, "corrupt-yaml", argv=argv, env={}, fixture={**fixture_mod, "corruption": "syntax"}, factors={"input": "corrupt"}, role="negative", provider=p, service=service)
    add(candidate, "modular_openapi_topology", a, b, [c, d], ["input.reference_topology"], ["OpenBB source", "secondary source commit", "provider", "server", "port policy", "command", "output", "budget"], {"exit_code": 0, "command_count": 0, "parse_status": "success"}, {"exit_code": 0, "command_count": ">0", "semantic_input_equivalence": True}, {"reference_topology": ["modular", "flattened"]})

    # Poetry Windows path/name factorial with Linux secondary controls.
    candidate = "incident_poetry_10974_init_duplicate_name"; pid = "batch100-poetry-10974-path-name"; pw = "provider:incident_poetry_10974_init_duplicate_name:exact-platform"; pl = "provider:incident_poetry_10974_init_duplicate_name:secondary-control"
    fixture_spaces = {"type": "fresh-empty-directory", "basename": "my project with spaces", "preexisting_pyproject": False}
    fixture_hyphen = {"type": "fresh-empty-directory", "basename": "my-project-with-spaces", "preexisting_pyproject": False}
    a = cell(candidate, pid, "windows-spaces-inferred", argv=["poetry", "init", "-n"], env={}, fixture=fixture_spaces, factors={"path": "spaces", "name": "inferred", "platform": "windows"}, role="incident", provider=pw, platform="windows")
    b = cell(candidate, pid, "windows-hyphen-inferred", argv=["poetry", "init", "-n"], env={}, fixture=fixture_hyphen, factors={"path": "hyphen", "name": "inferred", "platform": "windows"}, role="control", provider=pw, platform="windows")
    c = cell(candidate, pid, "windows-spaces-explicit", argv=["poetry", "init", "-n", "--name", "my-project-with-spaces"], env={}, fixture=fixture_spaces, factors={"path": "spaces", "name": "explicit", "platform": "windows"}, role="exclusion", provider=pw, platform="windows")
    d = cell(candidate, pid, "windows-hyphen-explicit", argv=["poetry", "init", "-n", "--name", "my-project-with-spaces"], env={}, fixture=fixture_hyphen, factors={"path": "hyphen", "name": "explicit", "platform": "windows"}, role="exclusion", provider=pw, platform="windows")
    e = cell(candidate, pid, "linux-spaces-inferred", argv=["poetry", "init", "-n"], env={}, fixture=fixture_spaces, factors={"path": "spaces", "name": "inferred", "platform": "linux"}, role="secondary", provider=pl)
    add(candidate, "windows_directory_name_normalization", a, b, [c, d, e], ["directory.basename", "command.explicit_name"], ["Poetry source", "provider within platform", "configuration", "input metadata", "budget"], {"project_name": "my project with spaces", "packaging_name_valid": False}, {"project_name": "my-project-with-spaces", "packaging_name_valid": True}, {"path": ["spaces", "hyphen"], "name": ["inferred", "explicit"]}, "factorial")

    # Every referenced capsule must be present, even when its materialization state is blocked.
    missing_providers = sorted({identifier for program in programs for identifier in program["provider_capsule_ids"] if identifier not in providers})
    if missing_providers:
        raise ValueError(f"missing provider capsule identities: {missing_providers}")
    write_jsonl(ROOT / "configs/batch100_candidate_counterfactual_programs_v2.jsonl", programs)
    write_jsonl(ROOT / "configs/batch100_counterfactual_cell_registry_v2.jsonl", cells)
    write_jsonl(ROOT / "configs/batch100_outcome_semantic_registry_v2.jsonl", semantics)
    print(json.dumps({"programs": len(programs), "cells": len(cells), "semantic_contracts": len(semantics)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

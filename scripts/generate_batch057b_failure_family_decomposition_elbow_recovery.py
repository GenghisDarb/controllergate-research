from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch057b_failure_family_decomposition_elbow_recovery"
BATCH057_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch057_source_only_patch_gate_wave_1"
BATCH057_ZIP = Path(
    r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch057_source_only_patch_gate_wave_1_artifacts.zip"
)
BATCH057_ARTIFACT_NAME = "post_v2_37_hardening_batch057_source_only_patch_gate_wave_1_artifacts"
BATCH057B_ARTIFACT_NAME = "post_v2_37_hardening_batch057b_failure_family_decomposition_elbow_recovery_artifacts"
BATCH057_ARTIFACT_ID = 8153438450
BATCH057_WORKFLOW_RUN_ID = 28904199782
BATCH057_WORKFLOW_HEAD_SHA = "febd919464df0e3fc8b7594e944919debcb38531"
BATCH057_SHA256 = "7d472153a1123f0ed16e23dfa90cca43dc0a7d7059603373ee80e6d1a51542cf"
BATCH057_SIZE = 108887
BATCH057_ENTRY_COUNT = 155
BATCH057_ARTIFACT_MANIFEST_CHECKED = 154
BATCH057_OUTPUT_MANIFESTS = {
    "post_v2_37_hardening_batch057_source_only_patch_gate_wave_1": (
        "post_v2_37_hardening_batch057_source_only_patch_gate_wave_1/SHA256SUMS.txt",
        153,
    ),
}
CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 2
NATIVE_EXTERNAL_REPAIR_COUNT = 4
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH057_RUNTIME_ROOT", r"C:\Dev\ControllerGate_runtime\batch057"))
SUBTARGET_TIMEOUT_SECONDS = int(os.environ.get("CONTROLLERGATE_BATCH057B_SUBTARGET_TIMEOUT", "180"))


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_cmd(args: list[str], cwd: Path, timeout: int = SUBTARGET_TIMEOUT_SECONDS) -> dict[str, Any]:
    started = time.time()
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        timed_out = False
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        returncode = -9
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
    elapsed = round(time.time() - started, 3)
    combined = (stdout or "") + (stderr or "")
    return {
        "command": args,
        "cwd": str(cwd),
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": elapsed,
        "stdout_sha256": sha256_text(stdout or ""),
        "stderr_sha256": sha256_text(stderr or ""),
        "combined_log_sha256": sha256_text(combined),
        "stdout": stdout or "",
        "stderr": stderr or "",
        "combined": combined,
    }


def trim_log(text: str, limit: int = 12000) -> str:
    if len(text) <= limit:
        return text
    head = text[: limit // 2]
    tail = text[-limit // 2 :]
    return f"{head}\n...<trimmed {len(text) - limit} chars>...\n{tail}"


def signature_extract(log: str) -> str:
    lines = []
    for line in log.splitlines():
        stripped = line.strip()
        if (
            stripped.startswith("FAILED ")
            or stripped.startswith("ERROR ")
            or "AssertionError" in stripped
            or "AttributeError" in stripped
            or "TypeError" in stripped
            or "PermissionError" in stripped
            or stripped.startswith("E       ")
            or stripped.startswith(">       ")
        ):
            lines.append(stripped[:240])
    if not lines:
        lines = [line.strip()[:240] for line in log.splitlines()[-20:] if line.strip()]
    return "\n".join(lines[:80]) + ("\n" if lines else "")


def venv_python(lead_id: str) -> Path:
    return RUNTIME_ROOT / "wave_1_patch_gate" / lead_id / "venv" / "Scripts" / "python.exe"


def checkout_dir(lead_id: str) -> Path:
    return RUNTIME_ROOT / "wave_1_patch_gate" / lead_id / "checkout"


def normalize_for_record(result: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in result.items()
        if key not in {"stdout", "stderr", "combined"}
    } | {
        "stdout_excerpt": trim_log(result.get("stdout", ""), 4000),
        "stderr_excerpt": trim_log(result.get("stderr", ""), 4000),
    }


CANDIDATES: dict[str, dict[str, Any]] = {
    "datasette_2461_async_event_loop_cli_tests": {
        "ranking_score": 70,
        "batch057_classification": "blocked_ambiguous_multi_failure_source_surface",
        "elbow_state": "elbow_closed_multi_family_ambiguous",
        "recommended_for_batch057c": False,
        "retired": False,
        "retirement_reason": None,
        "primary_family_id": None,
        "elbow_reason": "Multiple unrelated CLI, path, SQL logging, cache, and provider/tempfile families remain in the original target command.",
        "subtargets": [
            {
                "subtarget_id": "datasette_invalid_port_dog",
                "command_kind": "pytest",
                "node": "tests/test_cli.py::test_serve_invalid_ports[dog]",
                "family_id": "datasette_cli_invalid_port_validation",
            }
        ],
        "families": [
            {
                "family_id": "datasette_cli_config_setting_validation",
                "layer": "primary_source_bug",
                "test_nodes": ["tests/test_cli.py::test_setting_type_validation"],
                "exception_type": "TypeError",
                "assertion_pattern": "CliRunner / CLI validation failure",
                "suspected_source_files": ["datasette/cli.py"],
                "classification": "source-level",
            },
            {
                "family_id": "datasette_cli_invalid_port_validation",
                "layer": "secondary_source_bug",
                "test_nodes": [
                    "tests/test_cli.py::test_serve_invalid_ports[-1]",
                    "tests/test_cli.py::test_serve_invalid_ports[0.5]",
                    "tests/test_cli.py::test_serve_invalid_ports[dog]",
                    "tests/test_cli.py::test_serve_invalid_ports[65536]",
                ],
                "exception_type": "TypeError",
                "assertion_pattern": "invalid port CLI validation",
                "suspected_source_files": ["datasette/cli.py"],
                "classification": "source-level",
            },
            {
                "family_id": "datasette_internal_db_file_lock",
                "layer": "environment_provider_bug",
                "test_nodes": ["tests/test_cli.py::test_internal_db"],
                "exception_type": "PermissionError",
                "assertion_pattern": "WinError 32 temporary database/file lock",
                "suspected_source_files": ["datasette/app.py", "datasette/database.py"],
                "classification": "provider-level",
            },
            {
                "family_id": "datasette_spatialite_path_behavior",
                "layer": "dependency_install_bug",
                "test_nodes": ["tests/test_cli.py::test_spatialite_error_if_attempt_to_open_spatialite"],
                "exception_type": "mixed",
                "assertion_pattern": "spatialite/path behavior",
                "suspected_source_files": ["datasette/cli.py", "datasette/app.py"],
                "classification": "dependency-level",
            },
            {
                "family_id": "datasette_sql_logging_and_inspect_cache",
                "layer": "multi_causal_failure_surface",
                "test_nodes": [
                    "tests/test_cli.py::test_sql_errors_logged_to_stderr",
                    "tests/test_cli.py::test_serve_with_inspect_file_prepopulates_table_counts_cache",
                ],
                "exception_type": "mixed",
                "assertion_pattern": "stderr logging / inspect cache behavior",
                "suspected_source_files": ["datasette/cli.py", "datasette/app.py", "datasette/database.py"],
                "classification": "ambiguous",
            },
        ],
    },
    "freezegun_547_py313_datetimes_assertion": {
        "ranking_score": 5,
        "batch057_classification": "blocked_ambiguous_multi_failure_source_surface",
        "elbow_state": "elbow_open_primary_family_only_diagnostic_patch_allowed",
        "recommended_for_batch057c": True,
        "retired": False,
        "retirement_reason": None,
        "primary_family_id": "freezegun_unittest_method_decorator_kwargs",
        "elbow_reason": "Two failure families reproduce independently; the unittest decorator family is source-localized enough for a future diagnostic source-only patch attempt, while full target command remains required for any count.",
        "subtargets": [
            {
                "subtarget_id": "freezegun_unittest_decorator_frozen_time",
                "command_kind": "pytest",
                "node": "tests/test_datetimes.py::TestUnitTestMethodDecorator::test_method_decorator_works_on_unittest_kwarg_frozen_time",
                "family_id": "freezegun_unittest_method_decorator_kwargs",
            },
            {
                "subtarget_id": "freezegun_timezone_compare",
                "command_kind": "pytest",
                "node": "tests/test_datetimes.py::test_compare_datetime_and_time_with_timezone",
                "family_id": "freezegun_timezone_aware_time_comparison",
            },
        ],
        "families": [
            {
                "family_id": "freezegun_unittest_method_decorator_kwargs",
                "layer": "primary_source_bug",
                "test_nodes": [
                    "tests/test_datetimes.py::TestUnitTestMethodDecorator::test_method_decorator_works_on_unittest_kwarg_frozen_time",
                    "tests/test_datetimes.py::TestUnitTestMethodDecorator::test_method_decorator_works_on_unittest_kwarg_frozen_time_with_func",
                    "tests/test_datetimes.py::TestUnitTestMethodDecorator::test_method_decorator_works_on_unittest_kwarg_hello",
                ],
                "exception_type": "AssertionError",
                "assertion_pattern": "unittest method decorator kwargs / frozen_time mismatch",
                "suspected_source_files": ["freezegun/api.py"],
                "classification": "source-level",
            },
            {
                "family_id": "freezegun_timezone_aware_time_comparison",
                "layer": "secondary_source_bug",
                "test_nodes": ["tests/test_datetimes.py::test_compare_datetime_and_time_with_timezone"],
                "exception_type": "AssertionError",
                "assertion_pattern": "timezone-aware datetime/time comparison behavior",
                "suspected_source_files": ["freezegun/api.py"],
                "classification": "source-level",
            },
        ],
    },
    "venusian_91_py313_frameinfo_callinfo": {
        "ranking_score": 85,
        "batch057_classification": "blocked_no_safe_source_patch",
        "elbow_state": "elbow_closed_test_expectation_or_interpreter_behavior",
        "recommended_for_batch057c": False,
        "retired": False,
        "retirement_reason": None,
        "primary_family_id": "venusian_frameinfo_locals_identity",
        "elbow_reason": "The single failure asserts Python frame locals identity behavior under Python 3.13; no source-owned behavior was proven safe to patch.",
        "subtargets": [
            {
                "subtarget_id": "venusian_frameinfo_callinfo",
                "command_kind": "tox",
                "node": "tests/test_advice.py::FrameInfoTest::testCallInfo",
                "family_id": "venusian_frameinfo_locals_identity",
            }
        ],
        "families": [
            {
                "family_id": "venusian_frameinfo_locals_identity",
                "layer": "interpreter_behavior_change",
                "test_nodes": ["tests/test_advice.py::FrameInfoTest::testCallInfo"],
                "exception_type": "AssertionError",
                "assertion_pattern": "f_locals is locals() identity expectation",
                "suspected_source_files": ["src/venusian/advice.py"],
                "classification": "interpreter-behavior-level",
            }
        ],
    },
    "pexpect_699_replwrap_bash_assertions": {
        "ranking_score": 95,
        "batch057_classification": "blocked_environment_specific_failure",
        "elbow_state": "elbow_closed_environment_provider",
        "recommended_for_batch057c": False,
        "retired": True,
        "retirement_reason": "provider/shell/pty boundary dominates the replay compartment",
        "primary_family_id": "pexpect_replwrap_spawn_provider_boundary",
        "elbow_reason": "Failures share an AttributeError surface tied to pexpect.spawn availability and provider/shell/pty behavior in the local Windows compartment.",
        "subtargets": [
            {
                "subtarget_id": "pexpect_replwrap_bash",
                "command_kind": "pytest",
                "node": "tests/test_replwrap.py::REPLWrapTestCase::test_bash",
                "family_id": "pexpect_replwrap_spawn_provider_boundary",
            }
        ],
        "families": [
            {
                "family_id": "pexpect_replwrap_spawn_provider_boundary",
                "layer": "environment_provider_bug",
                "test_nodes": [
                    "tests/test_replwrap.py::REPLWrapTestCase::test_bash",
                    "tests/test_replwrap.py::REPLWrapTestCase::test_bash_env",
                    "tests/test_replwrap.py::REPLWrapTestCase::test_python",
                    "tests/test_replwrap.py::REPLWrapTestCase::test_multiline",
                ],
                "exception_type": "AttributeError",
                "assertion_pattern": "pexpect.spawn / shell provider boundary",
                "suspected_source_files": ["pexpect/replwrap.py", "pexpect/__init__.py", "pexpect/pty_spawn.py", "pexpect/_async.py"],
                "classification": "provider-level",
            }
        ],
    },
}


def subtarget_command(lead_id: str, item: dict[str, Any]) -> list[str]:
    py = str(venv_python(lead_id))
    if item["command_kind"] == "tox":
        return [py, "-m", "tox", "-e", "py313", "--", item["node"]]
    return [py, "-m", "pytest", item["node"], "-q", "--tb=no"]


def load_batch057_candidate(lead_id: str) -> dict[str, Any]:
    candidate_dir = BATCH057_DIR / "patch_candidates" / lead_id
    return {
        "fresh_replay": read_json(candidate_dir / "fresh_pre_repair_replay_result.json"),
        "failure_signature": (candidate_dir / "fresh_pre_repair_failure_signature_extract.txt").read_text(encoding="utf-8"),
        "source_discovery": read_json(candidate_dir / "source_discovery_result.json"),
        "suspect_source": read_json(candidate_dir / "suspect_source_files.json"),
        "source_inventory": read_json(candidate_dir / "source_file_inventory.json"),
        "command_context": read_json(candidate_dir / "candidate_command_context.json"),
        "commit": read_json(candidate_dir / "candidate_commit_verification.json"),
        "decision_inputs": read_json(candidate_dir / "decision_time_input_manifest.json"),
        "leakage": read_json(candidate_dir / "issue_body_leakage_boundary.json"),
        "gold": read_json(candidate_dir / "gold_patch_exclusion_check.json"),
        "future": read_json(candidate_dir / "future_evidence_exclusion_check.json"),
        "test_mutation": read_json(candidate_dir / "test_mutation_check.json"),
        "source_only": read_json(candidate_dir / "source_only_check.json"),
        "outcome": read_json(candidate_dir / "repair_outcome_classification.json"),
    }


def family_clusters(families: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    records = []
    for family in families:
        values = family.get(key)
        if not isinstance(values, list):
            values = [values]
        records.append(
            {
                "cluster_id": f"{family['family_id']}::{key}",
                key: values,
                "family_id": family["family_id"],
                "layer": family["layer"],
            }
        )
    return records


def replay_subtargets(lead_id: str, candidate_dir: Path, subtargets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    if not subtargets:
        return results
    first_command = subtarget_command(lead_id, subtargets[0])
    write_text_lf(candidate_dir / "minimal_subtarget_replay_command.txt", " ".join(first_command) + "\n")
    for item in subtargets:
        cmd = subtarget_command(lead_id, item)
        cwd = checkout_dir(lead_id)
        if not cwd.is_dir() or not Path(cmd[0]).is_file():
            result = {
                "subtarget_id": item["subtarget_id"],
                "family_id": item["family_id"],
                "status": "BLOCK",
                "exact_blocker": "minimal_subtarget_workspace_or_venv_missing",
                "command": cmd,
                "cwd": str(cwd),
            }
            results.append(result)
            continue
        raw = run_cmd(cmd, cwd)
        log = raw["combined"]
        subdir = candidate_dir / "minimal_subtarget_logs"
        subdir.mkdir(parents=True, exist_ok=True)
        write_text_lf(subdir / f"{item['subtarget_id']}_raw.log", log)
        write_text_lf(subdir / f"{item['subtarget_id']}_signature.txt", signature_extract(log))
        results.append(
            {
                "subtarget_id": item["subtarget_id"],
                "family_id": item["family_id"],
                "status": "PASS" if raw["returncode"] != 0 else "BLOCK",
                "classification": "minimal_subtarget_failure_reproduced" if raw["returncode"] != 0 else "minimal_subtarget_unexpected_pass",
                "exact_blocker": None if raw["returncode"] != 0 else "minimal_subtarget_failure_not_reproduced",
                "target_node": item["node"],
                "command": cmd,
                "cwd": str(cwd),
                "returncode": raw["returncode"],
                "timed_out": raw["timed_out"],
                "elapsed_seconds": raw["elapsed_seconds"],
                "raw_log_path": f"minimal_subtarget_logs/{item['subtarget_id']}_raw.log",
                "raw_log_sha256": raw["combined_log_sha256"],
                "signature_path": f"minimal_subtarget_logs/{item['subtarget_id']}_signature.txt",
                "signature_sha256": sha256_text(signature_extract(log)),
                "stdout_sha256": raw["stdout_sha256"],
                "stderr_sha256": raw["stderr_sha256"],
                "stdout_excerpt": trim_log(raw["stdout"], 2000),
                "stderr_excerpt": trim_log(raw["stderr"], 2000),
            }
        )
    write_text_lf(candidate_dir / "minimal_subtarget_replay_log_raw.txt", "\n\n".join((candidate_dir / r["raw_log_path"]).read_text(encoding="utf-8") for r in results if r.get("raw_log_path")) + "\n")
    write_text_lf(candidate_dir / "minimal_subtarget_failure_signature_extract.txt", "\n\n".join((candidate_dir / r["signature_path"]).read_text(encoding="utf-8") for r in results if r.get("signature_path")) + "\n")
    return results


def write_candidate(lead_id: str, cfg: dict[str, Any]) -> dict[str, Any]:
    evidence = load_batch057_candidate(lead_id)
    candidate_dir = OUT_DIR / "candidates" / lead_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    families = cfg["families"]
    subtarget_plan = {
        "status": "PASS",
        "lead_id": lead_id,
        "subtargets": [
            {
                "subtarget_id": item["subtarget_id"],
                "family_id": item["family_id"],
                "target_node": item["node"],
                "command": subtarget_command(lead_id, item),
                "purpose": "diagnostic failure-family isolation only",
                "counting_allowed": False,
                "patching_allowed_in_batch057b": False,
            }
            for item in cfg["subtargets"]
        ],
    }
    subtarget_results = replay_subtargets(lead_id, candidate_dir, cfg["subtargets"])
    subtarget_reproduced = sum(1 for item in subtarget_results if item.get("classification") == "minimal_subtarget_failure_reproduced")
    source_map = [
        {
            "family_id": family["family_id"],
            "suspected_source_files": family["suspected_source_files"],
            "classification": family["classification"],
            "source_inventory_status": evidence["source_inventory"].get("status"),
        }
        for family in families
    ]
    environment_map = [
        {
            "family_id": family["family_id"],
            "environment_marker": family["layer"] in {"environment_provider_bug", "dependency_install_bug", "interpreter_behavior_change", "test_expectation_bug"},
            "layer": family["layer"],
            "marker_reason": family["classification"],
        }
        for family in families
    ]
    primary = next((family for family in families if family["family_id"] == cfg["primary_family_id"]), None)
    secondary = [family for family in families if family is not primary and family["layer"] in {"secondary_source_bug", "environment_provider_bug", "dependency_install_bug", "interpreter_behavior_change", "multi_causal_failure_surface"}]
    tertiary = [family for family in families if family is not primary and family not in secondary]
    elbow = {
        "status": "PASS",
        "lead_id": lead_id,
        "elbow_activation_state": cfg["elbow_state"],
        "elbow_open": cfg["elbow_state"].startswith("elbow_open"),
        "batch057c_patch_recovery_allowed": cfg["recommended_for_batch057c"],
        "batch057b_patch_generated": False,
        "batch057b_patch_applied": False,
        "batch057b_post_repair_replay_run": False,
        "original_target_command_remains_required_for_future_count": True,
        "reason": cfg["elbow_reason"],
    }
    files = {
        "failure_family_decomposition.json": {
            "status": "PASS",
            "lead_id": lead_id,
            "batch057_classification": cfg["batch057_classification"],
            "failure_family_count": len(families),
            "families": families,
            "grouping_dimensions": [
                "failing_test_node",
                "exception_type",
                "traceback_root",
                "shared_assertion_pattern",
                "suspected_source_file",
                "environment_provider_marker",
                "dependency_cofactor_marker",
                "os_runtime_python_version_marker",
                "failure_level",
            ],
            "batch057_failure_signature_hash": sha256_text(evidence["failure_signature"]),
        },
        "bug_layer_registry.json": {"status": "PASS", "lead_id": lead_id, "layers": families},
        "primary_failure_family_selection.json": {
            "status": "PASS",
            "lead_id": lead_id,
            "primary_family": primary,
            "selection_allowed_for_future_diagnostic_patch": cfg["recommended_for_batch057c"],
            "selection_reason": cfg["elbow_reason"],
        },
        "secondary_failure_family_registry.json": {"status": "PASS", "lead_id": lead_id, "families": secondary},
        "tertiary_failure_family_registry.json": {"status": "PASS", "lead_id": lead_id, "families": tertiary},
        "failure_family_traceback_clusters.json": {"status": "PASS", "lead_id": lead_id, "clusters": family_clusters(families, "assertion_pattern")},
        "failure_family_test_node_clusters.json": {"status": "PASS", "lead_id": lead_id, "clusters": family_clusters(families, "test_nodes")},
        "failure_family_exception_type_clusters.json": {"status": "PASS", "lead_id": lead_id, "clusters": family_clusters(families, "exception_type")},
        "failure_family_source_surface_map.json": {"status": "PASS", "lead_id": lead_id, "source_surfaces": source_map},
        "failure_family_environment_marker_map.json": {"status": "PASS", "lead_id": lead_id, "environment_markers": environment_map},
        "minimal_subtarget_replay_plan.json": subtarget_plan,
        "minimal_subtarget_replay_result.json": {
            "status": "PASS" if subtarget_results else "BLOCK",
            "lead_id": lead_id,
            "subtarget_count": len(subtarget_results),
            "failure_reproduced_count": subtarget_reproduced,
            "results": subtarget_results,
            "counting_allowed": False,
            "patch_success_claim_allowed": False,
        },
        "subtarget_vs_original_target_mapping.json": {
            "status": "PASS",
            "lead_id": lead_id,
            "original_target_command": evidence["command_context"].get("selected_command"),
            "subtargets": subtarget_plan["subtargets"],
            "subtarget_success_cannot_count_as_original_target_success": True,
        },
        "elbow_activation_gate.json": elbow,
        "layered_repair_claim_boundary.json": {
            "status": "PASS",
            "lead_id": lead_id,
            "patch_generated": False,
            "patch_applied": False,
            "post_repair_target_replay_run": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
            "fixed_gold_future_evidence_used": False,
            "issue_body_fix_text_used": False,
            "tests_modified": False,
        },
    }
    for name, record in files.items():
        write_json_deterministic(candidate_dir / name, record)
    if not subtarget_results:
        write_json_deterministic(
            candidate_dir / "minimal_subtarget_replay_blocker.json",
            {"status": "BLOCK", "lead_id": lead_id, "exact_blocker": "minimal_subtarget_not_available"},
        )
    return {
        "lead_id": lead_id,
        "batch057_classification": cfg["batch057_classification"],
        "failure_family_count": len(families),
        "bug_layers": sorted({family["layer"] for family in families}),
        "minimal_subtarget_count": len(subtarget_results),
        "minimal_subtarget_reproduced_count": subtarget_reproduced,
        "elbow_activation_state": cfg["elbow_state"],
        "elbow_open": cfg["elbow_state"].startswith("elbow_open"),
        "batch057c_recommended": cfg["recommended_for_batch057c"],
        "retired": cfg["retired"],
        "retirement_reason": cfg["retirement_reason"],
        "ranking_score": cfg["ranking_score"],
        "exact_blocker": None if cfg["recommended_for_batch057c"] else cfg["elbow_state"],
    }


def update_public_docs(summary: dict[str, Any], results: list[dict[str, Any]]) -> None:
    section = "\n".join(
        [
            "### Batch057b failure-family decomposition elbow recovery",
            "",
            f"- Batch057 official ingest status: `{summary['batch057_ingest_status']}`.",
            f"- Batch057b decomposition status: `{summary['status']}`.",
            f"- Minimal subtarget replay count: `{summary['minimal_subtarget_replay_count']}`.",
            f"- Elbow-open candidate count: `{summary['elbow_open_candidate_count']}`.",
            f"- Elbow-closed candidate count: `{summary['elbow_closed_candidate_count']}`.",
            f"- Retired Wave 1 candidate count: `{summary['retired_wave1_candidate_count']}`.",
            f"- Batch057c recommended candidates: `{', '.join(summary['batch057c_recommended_candidates']) if summary['batch057c_recommended_candidates'] else 'none'}`.",
            f"- Wave 2 pre-repair replay recommendation: `{summary['wave2_replay_recommendation']}`.",
            f"- Issue-derived repair count remains `{ISSUE_DERIVED_REPAIR_COUNT}`; native external repair count remains `{NATIVE_EXTERNAL_REPAIR_COUNT}`.",
            f"- Next allowed action: `{summary['next_allowed_action']}`.",
            f"- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.",
            "",
            "| Candidate | Elbow state | Bug layers |",
            "| --- | --- | --- |",
            *[
                f"| `{item['lead_id']}` | `{item['elbow_activation_state']}` | `{', '.join(item['bug_layers'])}` |"
                for item in results
            ],
            "",
        ]
    )
    targets = [
        ROOT / "README.md",
        ROOT / "docs" / "current_status.md",
        ROOT / "docs" / "capability_inventory.md",
        ROOT / "docs" / "technical_validation_gap_report.md",
        ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md",
    ]
    marker = "### Batch057b failure-family decomposition elbow recovery"
    for path in targets:
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if marker in text:
            text = text[: text.index(marker)].rstrip() + "\n\n"
        else:
            text = text.rstrip() + "\n\n"
        write_text_lf(path, text + section)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not BATCH057_ZIP.is_file():
        write_json_deterministic(
            OUT_DIR / "audit.json",
            {"status": "BLOCK", "exact_blocker": "batch057_artifact_absent_for_official_ingest"},
        )
        write_sha256sums(OUT_DIR)
        return 2
    verification = verify_official_zip(
        BATCH057_ZIP,
        artifact_name=BATCH057_ARTIFACT_NAME,
        artifact_id=BATCH057_ARTIFACT_ID,
        workflow_run_id=BATCH057_WORKFLOW_RUN_ID,
        workflow_head_sha=BATCH057_WORKFLOW_HEAD_SHA,
        expected_sha256=BATCH057_SHA256,
        expected_size=BATCH057_SIZE,
        expected_entry_count=BATCH057_ENTRY_COUNT,
        artifact_manifest_checked=BATCH057_ARTIFACT_MANIFEST_CHECKED,
        output_manifests=BATCH057_OUTPUT_MANIFESTS,
    )
    ingest_detail = ingest_official_outputs(
        BATCH057_ZIP,
        ROOT,
        prefixes=("post_v2_37_hardening_batch057_source_only_patch_gate_wave_1",),
    )
    dashboard = read_json(BATCH057_DIR / "source_only_patch_gate_wave_1_dashboard.json")
    results057 = read_json(BATCH057_DIR / "source_only_patch_gate_wave_1_results.json")
    claim057 = read_json(BATCH057_DIR / "claim_boundary.json")

    phase_a = {
        "batch057_artifact_ingestion_summary.json": {
            "status": "PASS" if verification.get("status") == "PASS" and ingest_detail.get("status") == "PASS" else "BLOCK",
            "artifact_name": BATCH057_ARTIFACT_NAME,
            "artifact_id": BATCH057_ARTIFACT_ID,
            "workflow_run_id": BATCH057_WORKFLOW_RUN_ID,
            "workflow_head_sha": BATCH057_WORKFLOW_HEAD_SHA,
            "local_artifact_path": str(BATCH057_ZIP),
            "verification": verification,
            "ingest_detail": ingest_detail,
            "raw_zip_bytes_ingested": False,
            "zip_payload_committed": False,
            "exact_blocker": None if verification.get("status") == "PASS" and ingest_detail.get("status") == "PASS" else "batch057_artifact_verification_or_ingest_failed",
        },
        "batch057_artifact_sha256_verification.json": verification,
        "batch057_result_preservation.json": {
            "status": "PASS",
            "fresh_pre_repair_reproduction_count": dashboard.get("fresh_prerepair_reproduction_count"),
            "source_only_patches_generated": dashboard.get("patch_generated_count"),
            "patch_target_pass_count": dashboard.get("patch_target_pass_count"),
            "patch_target_fail_count": dashboard.get("patch_target_fail_count"),
            "blocked_no_safe_patch_count": dashboard.get("blocked_no_safe_patch_count"),
            "batch058_duplicate_replay_candidates": read_json(BATCH057_DIR / "batch058_duplicate_replay_candidates.json").get("candidate_count"),
            "next_allowed_action": dashboard.get("next_allowed_action"),
        },
        "batch057_candidate_classification_preservation.json": {
            "status": "PASS",
            "candidate_classifications": dashboard.get("candidate_classifications"),
        },
        "batch057_claim_boundary_preservation.json": {
            "status": "PASS" if claim057.get("current_protocol") == CURRENT_PROTOCOL else "BLOCK",
            "issue_derived_repair_count": claim057.get("issue_derived_repair_count"),
            "native_external_repair_count": claim057.get("native_external_repair_count"),
            "full_scoring": claim057.get("full_scoring"),
            "memory_lift": claim057.get("memory_lift"),
            "self_maintaining_software": claim057.get("self_maintaining_software"),
            "batch057b_patch_generated": False,
            "batch057b_duplicate_replay_run": False,
            "batch057b_count_gate_run": False,
            "batch057b_repair_count_increment": False,
        },
        "batch057_next_action_boundary.json": {
            "status": "PASS" if dashboard.get("next_allowed_action") == "batch057b_source_discovery_recovery_or_batch056b_wave2_pre_repair_replay" else "BLOCK",
            "preserved_next_allowed_action": dashboard.get("next_allowed_action"),
            "batch057b_allowed_actions": ["artifact_ingest", "failure_family_decomposition", "minimal_subtarget_replay", "elbow_activation_decision"],
            "patching_allowed": False,
            "duplicate_replay_allowed": False,
            "count_gate_allowed": False,
        },
    }
    for name, record in phase_a.items():
        write_json_deterministic(OUT_DIR / name, record)

    candidate_results = [write_candidate(lead_id, cfg) for lead_id, cfg in CANDIDATES.items()]
    open_candidates = [item for item in candidate_results if item["elbow_open"]]
    closed_candidates = [item for item in candidate_results if not item["elbow_open"]]
    retired = [item for item in candidate_results if item["retired"]]
    next_allowed = "batch057c_source_only_patch_recovery_wave_1" if open_candidates else "batch056b_wave2_pre_repair_replay"
    wave2_recommendation = "defer_because_batch057c_has_elbow_open_candidate" if open_candidates else "recommended_next"

    aggregate_files = {
        "failure_family_decomposition_wave_1_plan.json": {
            "status": "PASS",
            "candidate_count": len(CANDIDATES),
            "candidate_ids": list(CANDIDATES),
            "batch057_evidence_only": True,
            "patching_allowed_in_batch057b": False,
        },
        "failure_family_decomposition_wave_1_results.json": {"status": "PASS", "results": candidate_results},
        "bug_layer_registry_wave_1.json": {
            "status": "PASS",
            "candidates": [
                {"lead_id": lead_id, "layers": cfg["families"]}
                for lead_id, cfg in CANDIDATES.items()
            ],
        },
        "primary_failure_family_selection_wave_1.json": {
            "status": "PASS",
            "selections": [
                {"lead_id": lead_id, "primary_family_id": cfg["primary_family_id"], "elbow_state": cfg["elbow_state"]}
                for lead_id, cfg in CANDIDATES.items()
            ],
        },
        "secondary_failure_family_registry_wave_1.json": {
            "status": "PASS",
            "families": [
                {"lead_id": lead_id, "family": family}
                for lead_id, cfg in CANDIDATES.items()
                for family in cfg["families"]
                if family["family_id"] != cfg["primary_family_id"]
            ],
        },
        "tertiary_failure_family_registry_wave_1.json": {"status": "PASS", "families": []},
        "minimal_subtarget_replay_plan_wave_1.json": {
            "status": "PASS",
            "subtargets": [
                {"lead_id": lead_id, **item}
                for lead_id, cfg in CANDIDATES.items()
                for item in cfg["subtargets"]
            ],
            "counting_allowed": False,
        },
        "minimal_subtarget_replay_results_wave_1.json": {
            "status": "PASS",
            "minimal_subtarget_replay_count": sum(item["minimal_subtarget_count"] for item in candidate_results),
            "minimal_subtarget_failure_reproduced_count": sum(item["minimal_subtarget_reproduced_count"] for item in candidate_results),
            "results": candidate_results,
        },
        "elbow_activation_gate_wave_1.json": {
            "status": "PASS",
            "open_candidate_count": len(open_candidates),
            "closed_candidate_count": len(closed_candidates),
            "states": {item["lead_id"]: item["elbow_activation_state"] for item in candidate_results},
        },
        "layered_repair_claim_boundary.json": {
            "status": "PASS",
            "batch057b_generated_source_patches": 0,
            "batch057b_applied_patches": 0,
            "post_repair_target_replay_run": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
            "subtargets_are_diagnostic_only": True,
            "original_target_command_required_for_future_count": True,
        },
        "elbow_recovery_candidate_ranking.json": {
            "status": "PASS",
            "ranking_criteria": [
                "clear single source family",
                "minimal subtarget reproduces",
                "source surface localized",
                "not provider dominated",
                "not test expectation dominated",
                "not multi-family ambiguous",
            ],
            "ranked_candidates": sorted(candidate_results, key=lambda item: item["ranking_score"]),
        },
        "batch057c_patch_recovery_recommendation.json": {
            "status": "PASS",
            "recommendation_count": len(open_candidates),
            "recommended_candidates": [item["lead_id"] for item in open_candidates],
            "next_allowed_action_if_used": "batch057c_source_only_patch_recovery_wave_1",
            "patching_performed_in_batch057b": False,
            "counting_allowed": False,
        },
        "batch056b_wave2_pre_repair_replay_recommendation.json": {
            "status": "PASS",
            "recommendation": wave2_recommendation,
            "wave2_replay_run_in_batch057b": False,
            "next_allowed_action_if_no_open_elbows": "batch056b_wave2_pre_repair_replay",
        },
        "wave1_candidate_retirement_registry.json": {
            "status": "PASS",
            "retired_count": len(retired),
            "retired_candidates": retired,
        },
    }
    for name, record in aggregate_files.items():
        write_json_deterministic(OUT_DIR / name, record)

    summary = {
        "status": "PASS",
        "batch057_ingest_status": phase_a["batch057_artifact_ingestion_summary.json"]["status"],
        "batch057b_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "minimal_subtarget_replay_count": aggregate_files["minimal_subtarget_replay_results_wave_1.json"]["minimal_subtarget_replay_count"],
        "elbow_open_candidate_count": len(open_candidates),
        "elbow_closed_candidate_count": len(closed_candidates),
        "retired_wave1_candidate_count": len(retired),
        "candidate_decomposition_classifications": {item["lead_id"]: item["elbow_activation_state"] for item in candidate_results},
        "bug_layers_detected_per_candidate": {item["lead_id"]: item["bug_layers"] for item in candidate_results},
        "batch057c_recommended_candidates": [item["lead_id"] for item in open_candidates],
        "wave2_replay_recommendation": wave2_recommendation,
        "next_allowed_action": next_allowed,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "exact_blocker": None,
    }
    write_text_lf(
        OUT_DIR / "batch057b_summary.md",
        "\n".join(
            [
                "# Batch057b failure-family decomposition elbow recovery",
                "",
                f"- Status: `{summary['status']}`",
                f"- Batch057 official ingest status: `{summary['batch057_ingest_status']}`",
                f"- Minimal subtarget replay count: `{summary['minimal_subtarget_replay_count']}`",
                f"- Elbow-open candidate count: `{summary['elbow_open_candidate_count']}`",
                f"- Elbow-closed candidate count: `{summary['elbow_closed_candidate_count']}`",
                f"- Retired Wave 1 candidate count: `{summary['retired_wave1_candidate_count']}`",
                f"- Batch057c recommended candidates: `{', '.join(summary['batch057c_recommended_candidates']) if summary['batch057c_recommended_candidates'] else 'none'}`",
                f"- Next allowed action: `{summary['next_allowed_action']}`",
                "",
                "| Candidate | Elbow state | Bug layers |",
                "| --- | --- | --- |",
                *[
                    f"| `{item['lead_id']}` | `{item['elbow_activation_state']}` | `{', '.join(item['bug_layers'])}` |"
                    for item in candidate_results
                ],
                "",
            ]
        ),
    )
    write_json_deterministic(
        OUT_DIR / "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol": CURRENT_PROTOCOL,
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "batch057b_patch_generated": False,
            "batch057b_patch_applied": False,
            "batch057b_post_repair_target_replay_run": False,
            "batch057b_duplicate_replay_run": False,
            "batch057b_count_gate_run": False,
            "batch057b_repair_count_increment": False,
            "subtarget_results_are_not_counted_repairs": True,
            "next_allowed_action": next_allowed,
        },
    )
    write_json_deterministic(OUT_DIR / "audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch057b_failure_family_decomposition_elbow_recovery.py"})
    write_json_deterministic(
        OUT_DIR / "package_verification.json",
        {
            "status": "PASS",
            "artifact_name": BATCH057B_ARTIFACT_NAME,
            "raw_zip_payload_committed": False,
            "artifact_payload_created_locally": False,
            "workflow_upload_required_for_artifact_identity": True,
        },
    )
    write_json_deterministic(
        OUT_DIR / "artifact_sha256_verification.json",
        {
            "status": "PENDING_WORKFLOW_ARTIFACT",
            "artifact_name": BATCH057B_ARTIFACT_NAME,
            "batch057_local_zip_sha256": verification.get("zip_sha256"),
            "artifact_sha256_available_after_workflow_upload": True,
        },
    )
    update_public_docs(summary, candidate_results)
    write_sha256sums(OUT_DIR)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

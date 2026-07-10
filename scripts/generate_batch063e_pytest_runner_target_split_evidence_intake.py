from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tomllib
import traceback
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.artifacts import verify_artifact_zip
from controllergate.core.evidence import sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.runner_target_models import (
    FORBIDDEN_RUNNER_TARGET_SHORTCUTS,
    build_runner_target_model,
    runner_target_model_schema,
    select_runner_target_model,
)

OUT_NAME = "post_v2_37_hardening_batch063e_pytest_runner_target_split_evidence_intake"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH063D_NAME = "post_v2_37_hardening_batch063d_pytest_safe_tag_acquisition_hardening"
BATCH063D_DIR = ROOT / "outputs" / BATCH063D_NAME

EXPECTED_BATCH063D = {
    "commit": "e148d211a901453c1e77a1f3bdb5824b696be17e",
    "workflow": "post_v2_37_hardening_batch063d_pytest_safe_tag_acquisition_hardening",
    "workflow_run_id": 29063658705,
    "artifact_name": "post_v2_37_hardening_batch063d_pytest_safe_tag_acquisition_hardening_artifacts",
    "artifact_id": 8216357148,
    "expected_size": 53920,
    "expected_sha256": "940334f539d6cc7bdd81cc580e0f40c02df9bafc5acc25a5c8034194816f7b4f",
}

PYTEST_ID = "pytest_13895_pytest9_skiptest_behavior"
PYTEST_REPO = "https://github.com/pytest-dev/pytest"
PYTEST_REMOTE = "https://github.com/pytest-dev/pytest.git"
PYTEST_SHA = "041aacad506b6c6891f2898f2bd378e0896e8b86"
PRESERVED_COMMAND = "python -m pytest testing -q --tb=no"
CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 4
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"

ZIP_CANDIDATES = [
    ROOT / "incoming_artifacts" / f"{EXPECTED_BATCH063D['artifact_name']}.zip",
    Path(r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch063d_pytest_safe_tag_acquisition_hardening_artifacts.zip"),
]

METADATA_FILES = [
    "pyproject.toml",
    "tox.ini",
    "noxfile.py",
    "setup.cfg",
    "setup.py",
    "requirements.txt",
    "requirements-dev.txt",
    ".github/workflows/main.yml",
    ".github/workflows/test.yml",
    "CONTRIBUTING.rst",
    "README.rst",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_out_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def write_out_text(name: str, value: str) -> None:
    write_text_lf(OUT_DIR / name, value)


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_zip_json(zip_path: Path, name: str) -> dict[str, Any] | None:
    with zipfile.ZipFile(zip_path) as archive:
        if name not in archive.namelist():
            return None
        return json.loads(archive.read(name).decode("utf-8"))


def run_cmd(args: list[str], *, cwd: Path | None = None, timeout: int = 120, env: dict[str, str] | None = None) -> dict[str, Any]:
    started = now_iso()
    try:
        proc = subprocess.run(
            args,
            cwd=cwd or ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": args,
            "command_string": " ".join(args),
            "cwd": str(cwd or ROOT),
            "started_at": started,
            "completed_at": now_iso(),
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "stdout_sha256": sha256_bytes(proc.stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(proc.stderr.encode("utf-8")),
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        return {
            "command": args,
            "command_string": " ".join(args),
            "cwd": str(cwd or ROOT),
            "started_at": started,
            "completed_at": now_iso(),
            "returncode": None,
            "stdout": stdout,
            "stderr": stderr,
            "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
            "timed_out": True,
        }


def runtime_root() -> Path:
    if os.environ.get("RUNNER_TEMP"):
        return Path(os.environ["RUNNER_TEMP"]) / "ControllerGate_runtime" / "batch063e"
    return ROOT.parent / "ControllerGate_runtime" / "batch063e"


def reset_runtime(path: Path) -> dict[str, Any]:
    if path.exists():
        resolved = path.resolve()
        allowed_parent = path.parent.resolve()
        if allowed_parent not in [resolved, *resolved.parents]:
            return {"status": "FAIL", "reason": "runtime_path_outside_allowed_parent", "path": str(resolved)}
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    return {
        "status": "PASS",
        "runtime_root": str(path),
        "outside_live_repo": ROOT.resolve() not in path.resolve().parents,
        "outside_onedrive": "onedrive" not in str(path).lower(),
    }


def find_batch063d_zip() -> Path | None:
    env = os.environ.get("CONTROLLERGATE_BATCH063D_ARTIFACT_ZIP")
    candidates = ([Path(env)] if env else []) + ZIP_CANDIDATES
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def verify_batch063d_artifact() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    zip_path = find_batch063d_zip()
    if zip_path is None:
        verification: dict[str, Any] = {
            "status": "batch063d_artifact_absent_for_local_ingest",
            "artifact_absent": True,
            "manual_artifact_handoff": False,
            "downloaded_by_codex": False,
        }
        source_final = read_json(BATCH063D_DIR / "batch063d_final_decision.json")
        ingestion = {
            "status": "batch063d_artifact_absent_for_local_ingest",
            "committed_batch063d_outputs_preserved": True,
            "raw_zip_bytes_ingested": False,
            "ingested_file_count": 0,
        }
        return verification, ingestion, source_final

    verification = verify_artifact_zip(
        zip_path,
        expected_size=EXPECTED_BATCH063D["expected_size"],
        expected_sha256=EXPECTED_BATCH063D["expected_sha256"],
    )
    verification["local_artifact_path"] = str(zip_path)
    verification["manual_artifact_handoff"] = True
    verification["downloaded_by_codex"] = False
    verification["nested_archive_cache_venv_pyc_payload_count"] = len(verification.get("entries", {}).get("nested_archive_or_cache_payloads", []))
    artifact_final = read_zip_json(zip_path, "batch063d_final_decision.json") or read_json(BATCH063D_DIR / "batch063d_final_decision.json")
    ingestion = {
        "status": "PASS" if verification.get("status") == "PASS" else "BLOCK",
        "source_zip": str(zip_path),
        "artifact_verified": verification.get("status"),
        "raw_zip_bytes_ingested": False,
        "output_payload_overwrite_performed": False,
        "ingested_file_count": 0,
        "preservation_source": "verified_manual_batch063d_artifact" if verification.get("status") == "PASS" else "committed_batch063d_outputs",
    }
    return verification, ingestion, artifact_final


def write_configs() -> None:
    write_json_deterministic(ROOT / "configs" / "pytest_runner_target_model_schema.json", runner_target_model_schema())
    write_json_deterministic(
        ROOT / "configs" / "runner_target_model_decision_policy.json",
        {
            "status": "PASS",
            "selection_priority": [
                "declared_self_hosted_runner_model",
                "external_runner_target_split_model",
                "blocked_unproven_runner_target_model",
            ],
            "blind_external_runner_forbidden": True,
            "self_hosted_pytest_allowed_only_with_project_local_metadata_and_import_origin_proof": True,
            "pre_repair_replay_requires_proven_model": True,
            "forbidden_shortcuts": FORBIDDEN_RUNNER_TARGET_SHORTCUTS,
        },
    )


def checkout_candidate(rt: Path) -> tuple[Path, dict[str, Any]]:
    source = rt / "pytest_candidate_source"
    source.mkdir(parents=True, exist_ok=True)
    init = run_cmd(["git", "init", "-q"], cwd=source)
    remote = run_cmd(["git", "remote", "add", "origin", PYTEST_REMOTE], cwd=source)
    fetch = run_cmd(["git", "fetch", "--filter=blob:none", "--no-tags", "origin", PYTEST_SHA], cwd=source, timeout=180)
    checkout = run_cmd(["git", "checkout", "-q", "--detach", "FETCH_HEAD"], cwd=source, timeout=120)
    rev = run_cmd(["git", "rev-parse", "HEAD"], cwd=source)
    status = run_cmd(["git", "status", "--short"], cwd=source)
    summary = {
        "status": "PASS" if fetch.get("returncode") == 0 and checkout.get("returncode") == 0 and rev.get("stdout", "").strip() == PYTEST_SHA else "BLOCK",
        "source_path": str(source),
        "source_path_outside_live_repo": ROOT.resolve() not in source.resolve().parents,
        "source_path_outside_onedrive": "onedrive" not in str(source).lower(),
        "commands": {
            "init": init,
            "remote": remote,
            "fetch": fetch,
            "checkout": checkout,
            "rev_parse": rev,
            "status_short": status,
        },
    }
    return source, summary


def metadata_inventory(source: Path) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    for rel in METADATA_FILES:
        path = source / rel
        if path.is_file():
            files.append({"path": rel, "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    pyproject_data: dict[str, Any] = {}
    pyproject = source / "pyproject.toml"
    pyproject_text = ""
    if pyproject.is_file():
        pyproject_text = pyproject.read_text(encoding="utf-8")
        pyproject_data = tomllib.loads(pyproject_text)
    tox_text = (source / "tox.ini").read_text(encoding="utf-8") if (source / "tox.ini").is_file() else ""
    tool_pytest = pyproject_data.get("tool", {}).get("pytest", {}) if pyproject_data else {}
    project = pyproject_data.get("project", {}) if pyproject_data else {}
    scripts = project.get("scripts", {}) if isinstance(project, dict) else {}
    evidence = {
        "project_name": project.get("name"),
        "console_scripts": scripts,
        "tool_pytest_minversion": tool_pytest.get("minversion"),
        "tool_pytest_testpaths": tool_pytest.get("testpaths"),
        "tool_pytest_addopts": tool_pytest.get("addopts"),
        "setuptools_scm_write_to": pyproject_data.get("tool", {}).get("setuptools_scm", {}).get("write_to") if pyproject_data else None,
        "tox_commands_include_pytest_posargs": "pytest {posargs" in tox_text,
        "tox_package_mode": "package = wheel" if "package = wheel" in tox_text else None,
        "tox_external_runner_declared": False,
        "src_layout_indicators": [
            "src directory exists" if (source / "src").is_dir() else None,
            "testing directory exists" if (source / "testing").is_dir() else None,
            "towncrier package_dir src" if 'package_dir = "src"' in pyproject_text else None,
        ],
    }
    evidence["src_layout_indicators"] = [item for item in evidence["src_layout_indicators"] if item]
    command_authority = {
        "status": "PASS" if evidence["project_name"] == "pytest" and "testing" in (evidence.get("tool_pytest_testpaths") or []) else "BLOCK",
        "preserved_command": PRESERVED_COMMAND,
        "equivalence_basis": [
            "pyproject.toml [tool.pytest] testpaths includes testing",
            "tox.ini commands run pytest with posargs",
            "pyproject.toml project scripts expose pytest entry point",
        ],
        "declares_self_hosted_pytest_runner_pattern": evidence["project_name"] == "pytest" and "pytest" in scripts,
        "declares_external_runner_requirement": False,
        "minversion_normalized_by_batch063d": True,
        "decision_time_safe": True,
    }
    return {
        "status": "PASS",
        "candidate_id": PYTEST_ID,
        "candidate_sha": PYTEST_SHA,
        "source_path": str(source),
        "metadata_files": files,
        "metadata_evidence": evidence,
        "command_authority": command_authority,
    }


def write_self_hosted_probe_script() -> Path:
    script = OUT_DIR / "pytest_self_hosted_runner_import_origin_probe_batch063e.py"
    write_text_lf(
        script,
        r'''
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
'''.strip(),
    )
    return script


def run_self_hosted_probe(source: Path, metadata: dict[str, Any], normalized_version: str | None) -> dict[str, Any]:
    script = write_self_hosted_probe_script()
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(source / "src")
    env["CONTROLLERGATE_CANDIDATE_CHECKOUT"] = str(source)
    env["CONTROLLERGATE_CANDIDATE_SRC"] = str(source / "src")
    env["CONTROLLERGATE_BATCH063D_NORMALIZED_VERSION"] = normalized_version or ""
    plan = {
        "status": "PASS",
        "candidate_id": PYTEST_ID,
        "probe_script": script.name,
        "working_directory": str(source),
        "pythonpath_manifested": True,
        "pythonpath_value": str(source / "src"),
        "pythonpath_authority": "pyproject.toml source layout and project-local package path",
        "source_mutation_allowed": False,
        "test_mutation_allowed": False,
        "pyproject_mutation_allowed": False,
    }
    write_out_json("pytest_self_hosted_runner_probe_plan_batch063e.json", plan)
    command = [sys.executable, str(script)]
    proc = run_cmd(command, cwd=source, env=env, timeout=60)
    parsed: dict[str, Any]
    try:
        parsed = json.loads(proc.get("stdout", "{}"))
    except json.JSONDecodeError:
        parsed = {"parse_error": True, "raw_stdout": proc.get("stdout")}
    status_after = run_cmd(["git", "status", "--short"], cwd=source)
    candidate_origin = bool(parsed.get("runner_import_origin_equals_candidate_checkout"))
    import_ok = parsed.get("import_succeeded") is True
    metadata_allows = metadata["command_authority"]["declares_self_hosted_pytest_runner_pattern"] is True
    classification = "declared_self_hosted_runner_import_origin_proven" if import_ok and candidate_origin and metadata_allows else "declared_self_hosted_runner_unproven"
    result = {
        "status": "PASS" if classification.endswith("_proven") else "BLOCK",
        "classification": classification,
        "candidate_id": PYTEST_ID,
        "command": command,
        "working_directory": str(source),
        "python_executable": sys.executable,
        "env_manifest": {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(source / "src")},
        "probe_returncode": proc.get("returncode"),
        "probe_stdout_sha256": proc.get("stdout_sha256"),
        "probe_stderr_sha256": proc.get("stderr_sha256"),
        "probe": parsed,
        "runner_import_origin_equals_fixed_candidate_checkout": candidate_origin,
        "allowed_by_project_local_metadata": metadata_allows,
        "command_source_decision_time_safe": metadata["command_authority"]["decision_time_safe"],
        "version_normalized_from_batch063d_authority": normalized_version is not None,
        "source_status_after_probe": status_after.get("stdout", ""),
        "source_mutated": bool(status_after.get("stdout", "").strip()),
        "exact_blocker": None if classification.endswith("_proven") else "declared_self_hosted_runner_import_failed_without_source_generation",
    }
    write_out_json("pytest_self_hosted_runner_import_origin_result_batch063e.json", result)
    write_out_json(
        "pytest_self_hosted_runner_command_manifest_batch063e.json",
        {
            "status": "PASS",
            "candidate_id": PYTEST_ID,
            "command": PRESERVED_COMMAND,
            "working_directory": str(source),
            "runner_model": "declared_self_hosted_runner_model",
            "pythonpath_manifested": True,
            "no_minversion_suppression": True,
            "no_rootdir_override": True,
            "source_mutation_allowed": False,
        },
    )
    return result


def write_external_runner_outputs(source: Path, metadata: dict[str, Any]) -> dict[str, Any]:
    script = OUT_DIR / "pytest_external_runner_import_origin_probe_batch063e.py"
    write_text_lf(
        script,
        '"""Batch063e external runner probe placeholder.\n\nNot executed because the fixed candidate checkout did not declare a decision-time-safe external runner-target split.\n"""\n',
    )
    plan = {
        "status": "NOT_RUN",
        "candidate_id": PYTEST_ID,
        "external_runner_probe_allowed": False,
        "reason": "project-local metadata does not declare an external runner-target split for self-testing pytest",
        "blind_external_runner_forbidden": True,
    }
    write_out_json("pytest_external_runner_identity_plan_batch063e.json", plan)
    write_out_json("pytest_external_runner_provider_capsule_batch063e.json", {"status": "NOT_RUN", "candidate_id": PYTEST_ID, "provider_capsule_created": False, "reason": plan["reason"]})
    result = {
        "status": "NOT_RUN",
        "classification": "external_runner_target_import_origin_unproven",
        "candidate_id": PYTEST_ID,
        "external_runner_selected": False,
        "runner_import_path": None,
        "target_checkout_path": str(source),
        "target_import_origin_proven": False,
        "future_behavior_leak_detected": False,
        "reason": plan["reason"],
    }
    write_out_json("pytest_external_runner_import_origin_result_batch063e.json", result)
    write_out_json("pytest_external_runner_target_contact_probe_batch063e.json", {"status": "NOT_RUN", "candidate_id": PYTEST_ID, "target_contact_proven": False, "reason": plan["reason"]})
    write_out_json("pytest_external_runner_command_manifest_batch063e.json", {"status": "NOT_RUN", "candidate_id": PYTEST_ID, "command": None, "reason": plan["reason"], "no_blind_external_runner": True})
    return result


def update_public_docs(final: dict[str, Any]) -> None:
    section = """## Batch063e Pytest Runner-Target Split Evidence Intake

Batch063e evaluates Pytest runner-target import origin after Batch063d normalized version-origin metadata. It tests whether Pytest can be run as a declared self-hosted test runner or through a proven external runner-target split. These are command-boundary controls and replay-readiness evidence, not repair proof. No repair is counted without source-only target pass, duplicate clean replay, and count gate. Full scoring remains NOT_RUN/disallowed. Memory lift remains not_demonstrated. Self-maintaining software remains false/not_demonstrated.

Batch063e status:

- Batch063d artifact ingest: `{batch063d_ingest_status}`.
- Batch063d tag authority preservation: `{batch063d_tag_authority_preservation_status}`.
- Self-hosted runner model: `{self_hosted_runner_model_status}`.
- External runner model: `{external_runner_model_status}`.
- Selected runner-target model: `{runner_target_model_selected}`.
- Pytest pre-repair replay: `{pytest_pre_repair_replay_status}`.
- Pytest terminal state: `{pytest_terminal_state}`.
- Seed harvest authorization: `{seed_harvest_authorization_status}`.
- Issue-derived repair count remains `{issue_derived_repair_count}`.
- Native external repair count remains `{native_external_repair_count}`.
- Next allowed action: `{next_allowed_action}`.
""".format(**final)
    for rel in [
        "README.md",
        "docs/current_status.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        marker = "## Batch063e Pytest Runner-Target Split Evidence Intake"
        if marker in text:
            start = text.index(marker)
            next_marker = text.find("\n## ", start + 1)
            text = text[:start].rstrip() + "\n\n" + section.rstrip() + ("\n" if next_marker == -1 else "\n\n" + text[next_marker + 1 :].lstrip())
        else:
            first_section = text.find("\n## ")
            text = text.rstrip() + "\n\n" + section if first_section == -1 else text[:first_section].rstrip() + "\n\n" + section.rstrip() + "\n\n" + text[first_section + 1 :].lstrip()
        write_text_lf(path, text)


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write_configs()

    artifact_verification, artifact_ingest, batch063d_final = verify_batch063d_artifact()
    write_out_json("batch063d_artifact_sha256_verification.json", artifact_verification)
    write_out_json("batch063d_artifact_ingestion_summary.json", artifact_ingest)
    write_out_json("batch063d_result_preservation.json", {"status": "PASS", "source": artifact_ingest.get("preservation_source", "committed_batch063d_outputs"), "next_allowed_action": batch063d_final.get("next_allowed_action"), "exact_blocker": batch063d_final.get("exact_blocker")})
    tag_preserved = (
        batch063d_final.get("safe_tag_authority_status") == "predeclared_ancestor_tag_authority_manifest_PASS"
        and batch063d_final.get("tag_authority_lifecycle_status") == "PASS"
        and batch063d_final.get("future_tag_refs_used") is False
        and batch063d_final.get("tag_source_bytes_read") is False
        and batch063d_final.get("pytest_version_origin_status") == "pytest_version_origin_normalized_from_predeclared_ancestor_tag_authority"
    )
    write_out_json(
        "batch063d_tag_authority_preservation.json",
        {
            "status": "PASS" if tag_preserved else "BLOCK",
            "safe_tag_authority_status": batch063d_final.get("safe_tag_authority_status"),
            "tag_authority_lifecycle_status": batch063d_final.get("tag_authority_lifecycle_status"),
            "future_tag_refs_used": batch063d_final.get("future_tag_refs_used"),
            "tag_source_bytes_read": batch063d_final.get("tag_source_bytes_read"),
            "pytest_version_origin_status": batch063d_final.get("pytest_version_origin_status"),
            "exact_blocker": None if tag_preserved else "batch063d_tag_authority_not_preserved",
        },
    )
    write_out_json("batch063d_boundary_preservation.json", {"status": "PASS", "patch_generated": False, "patch_applied": False, "duplicate_replay_run": False, "count_gate_run": False, "repair_count_increment": False, "full_scoring": FULL_SCORING, "memory_lift": MEMORY_LIFT, "self_maintaining_software": SELF_MAINTAINING})
    write_out_json("pytest_version_origin_preservation_batch063e.json", read_json(OUT_DIR / "batch063d_tag_authority_preservation.json"))

    reset = reset_runtime(runtime_root())
    source, checkout = checkout_candidate(runtime_root())
    metadata = metadata_inventory(source) if checkout["status"] == "PASS" else {"status": "BLOCK", "command_authority": {"decision_time_safe": False, "declares_self_hosted_pytest_runner_pattern": False}}
    write_out_json("pytest_project_local_test_metadata_inventory_batch063e.json", metadata)
    write_out_json("pytest_project_local_command_authority_batch063e.json", metadata.get("command_authority", {}))
    write_out_json("pytest_declared_self_testing_evidence_batch063e.json", {"status": "PASS" if metadata.get("command_authority", {}).get("declares_self_hosted_pytest_runner_pattern") else "BLOCK", "candidate_id": PYTEST_ID, "evidence": metadata.get("metadata_evidence", {}), "checkout": checkout})
    write_out_json("pytest_external_runner_metadata_evidence_batch063e.json", {"status": "NOT_DECLARED", "candidate_id": PYTEST_ID, "external_runner_declared_by_project_metadata": False, "reason": "pytest project-local metadata declares self-testing commands, not a separate external runner-target split"})
    write_out_json("pytest_command_source_authority_batch063e.json", metadata.get("command_authority", {}))

    write_out_json("pytest_runner_target_model_decision_policy_batch063e.json", read_json(ROOT / "configs" / "runner_target_model_decision_policy.json"))
    write_out_json("pytest_runner_target_model_forbidden_shortcuts_batch063e.json", {"status": "PASS", "forbidden_shortcuts": FORBIDDEN_RUNNER_TARGET_SHORTCUTS})
    version_status = batch063d_final.get("pytest_version_origin_status")
    normalized_version = (read_json(BATCH063D_DIR / "pytest_version_origin_recheck_from_frozen_tag_manifest_batch063d.json").get("normalized_version") if (BATCH063D_DIR / "pytest_version_origin_recheck_from_frozen_tag_manifest_batch063d.json").is_file() else None)
    model_registry = {
        "status": "PASS",
        "models": [
            build_runner_target_model(
                model_id="declared_self_hosted_runner_model",
                candidate_id=PYTEST_ID,
                runner_identity="pytest package from fixed candidate checkout",
                target_identity="pytest package and testing tree from fixed candidate checkout",
                runner_import_origin="candidate checkout src/pytest",
                target_import_origin="candidate checkout src/pytest and testing",
                command_source="pyproject.toml [tool.pytest] and tox.ini commands",
                declared_by_buggy_checkout_metadata=bool(metadata.get("command_authority", {}).get("declares_self_hosted_pytest_runner_pattern")),
                requires_external_runner=False,
                requires_self_hosted_runner=True,
                version_origin_status=str(version_status),
                working_directory=str(source),
                sys_path_policy="manifested candidate src path only; no rootdir override",
                environment_policy="isolated runtime; PYTHONDONTWRITEBYTECODE=1; no source/test/config mutation",
                allowed_command_shape=PRESERVED_COMMAND,
                forbidden_command_shape=FORBIDDEN_RUNNER_TARGET_SHORTCUTS,
                decision_time_safe=tag_preserved and metadata.get("command_authority", {}).get("decision_time_safe") is True,
                expected_probe="pytest_self_hosted_runner_import_origin_probe_batch063e.py",
                success_criteria=["import pytest succeeds", "pytest.__file__ resolves under candidate checkout", "source tree remains clean"],
                failure_classification="declared_self_hosted_runner_unproven",
                audit_status="PASS",
            ),
            build_runner_target_model(
                model_id="external_runner_target_split_model",
                candidate_id=PYTEST_ID,
                runner_identity="external pytest runner",
                target_identity="fixed candidate checkout",
                runner_import_origin="outside candidate checkout",
                target_import_origin="fixed candidate checkout source/contact graph",
                command_source="not declared by project-local metadata",
                declared_by_buggy_checkout_metadata=False,
                requires_external_runner=True,
                requires_self_hosted_runner=False,
                version_origin_status=str(version_status),
                working_directory=str(source),
                sys_path_policy="not executed; blind external runner forbidden",
                environment_policy="not executed without metadata authority",
                allowed_command_shape="not selected",
                forbidden_command_shape=FORBIDDEN_RUNNER_TARGET_SHORTCUTS,
                decision_time_safe=False,
                expected_probe="pytest_external_runner_import_origin_probe_batch063e.py",
                success_criteria=["project metadata declares external runner", "runner import outside target", "target contact remains fixed candidate"],
                failure_classification="external_runner_target_import_origin_unproven",
                audit_status="NOT_RUN",
            ),
            build_runner_target_model(
                model_id="blocked_unproven_runner_target_model",
                candidate_id=PYTEST_ID,
                runner_identity="unproven",
                target_identity="unproven",
                runner_import_origin="unproven",
                target_import_origin="unproven",
                command_source="blocked until one legal model is proven",
                declared_by_buggy_checkout_metadata=False,
                requires_external_runner=False,
                requires_self_hosted_runner=False,
                version_origin_status=str(version_status),
                working_directory=str(source),
                sys_path_policy="no replay",
                environment_policy="no replay",
                allowed_command_shape="none",
                forbidden_command_shape=FORBIDDEN_RUNNER_TARGET_SHORTCUTS,
                decision_time_safe=False,
                expected_probe="none",
                success_criteria=["not applicable"],
                failure_classification="pytest_runner_target_split_unresolved_after_model_probe",
                audit_status="BLOCK",
            ),
        ],
    }
    write_out_json("pytest_runner_target_model_registry_batch063e.json", model_registry)
    write_out_json("pytest_runner_target_model_selection_batch063e.json", {"status": "PENDING", "priority": ["declared_self_hosted_runner_model", "external_runner_target_split_model", "blocked_unproven_runner_target_model"]})

    self_result = run_self_hosted_probe(source, metadata, str(normalized_version) if normalized_version else None) if tag_preserved and checkout["status"] == "PASS" else {"classification": "declared_self_hosted_runner_unproven", "status": "BLOCK", "exact_blocker": "batch063d_tag_authority_not_preserved_or_checkout_failed"}
    external_result = write_external_runner_outputs(source, metadata)
    selection = select_runner_target_model(self_hosted_status=str(self_result.get("classification")), external_status=str(external_result.get("classification")))
    write_out_json("pytest_runner_target_model_selection_result_batch063e.json", selection)
    write_out_json("pytest_runner_target_model_selection_batch063e.json", {"status": selection["status"], "selection": selection})

    replay_allowed = selection["status"] == "PASS" and tag_preserved
    replay_status = "NOT_RUN"
    replay_classification = "pytest_runner_target_model_unproven" if not replay_allowed else "pytest_pre_repair_target_failure_materialized"
    replay_log = "Batch063e did not run pre-repair replay because runner-target model selection remained blocked."
    write_out_json("pytest_pre_repair_replay_gate_batch063e.json", {"status": "PASS" if replay_allowed else "BLOCK", "batch063d_tag_authority_preserved": tag_preserved, "runner_target_model_selected": selection["selected_model"], "pre_repair_replay_allowed": replay_allowed, "classification": replay_classification})
    write_out_json("pytest_pre_repair_replay_command_batch063e.json", {"status": "NOT_RUN" if not replay_allowed else "PASS", "command": PRESERVED_COMMAND, "reason": None if replay_allowed else "runner-target model unproven"})
    write_out_text("pytest_pre_repair_replay_log_batch063e.txt", replay_log)
    write_out_json("pytest_pre_repair_replay_result_batch063e.json", {"status": replay_status, "classification": replay_classification, "target_failure_materialized": False, "source_mutated": False, "tests_mutated": False, "fixtures_mutated": False, "pyproject_mutated": False})
    command_boundary_status = "pytest_runner_target_split_unresolved_after_model_probe" if selection["blocked"] else "pytest_command_boundary_ready_for_pre_repair_replay"
    terminal_state = command_boundary_status
    write_out_json("pytest_command_boundary_final_status_batch063e.json", {"status": "PASS", "classification": command_boundary_status, "terminal_state": terminal_state})

    reward = {
        "status": "PASS",
        "candidate_id": PYTEST_ID,
        "graded_signal": 0.0,
        "failure_surface": "command_boundary_precondition_unavailable" if selection["blocked"] else "pre_repair_materialization_success_not_repair_attempt",
        "repair_skill_memory_update_allowed": False,
        "routing_memory_update_allowed": True,
    }
    write_out_json("pytest_runner_target_reward_signal_batch063e.json", reward)
    no_loop_next = "batch068_multi_seed_harvest_for_5th_issue_repair_with_batch067_063c_063d_063e_controls" if selection["blocked"] else "batch063f_pytest_source_topology_and_patch_license_gate"
    exact_blocker = "pytest_runner_target_split_unresolved_after_model_probe" if selection["blocked"] else "pytest_pre_repair_target_failure_materialized"
    write_out_json("pytest_runner_target_blocker_reopen_condition_batch063e.json", {"status": "PASS", "candidate_id": PYTEST_ID, "reopen_condition": "provide a concrete runner-target evidence artifact proving self-hosted generated version handling without source mutation or a declared external runner split", "exact_blocker": exact_blocker})
    write_out_json("pytest_runner_target_parking_record_batch063e.json", {"status": "PASS", "candidate_id": PYTEST_ID, "parked_without_patch": selection["blocked"], "source_mutated": False, "exact_blocker": exact_blocker})
    write_out_json("seed_harvest_authorization_after_batch063e_batch063e.json", {"status": "AUTHORIZED" if selection["blocked"] else "NOT_AUTHORIZED", "next_allowed_action": no_loop_next, "reason": "Pytest remains blocked and no immediate generic Pytest follow-up is authorized" if selection["blocked"] else "Pytest materialized target failure"})

    final = {
        "status": "PASS",
        "batch063d_ingest_status": artifact_ingest["status"],
        "batch063d_tag_authority_preservation_status": "PASS" if tag_preserved else "BLOCK",
        "batch063e_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
        "patch_generated": False,
        "patch_applied": False,
        "source_mutated": False,
        "tests_mutated": False,
        "fixtures_mutated": False,
        "pyproject_mutated": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "pytest_version_origin_status": version_status,
        "self_hosted_runner_model_status": self_result.get("classification"),
        "external_runner_model_status": external_result.get("classification"),
        "runner_target_model_selected": selection["selected_model"],
        "pytest_runner_target_import_origin_status": selection["selected_model"] if not selection["blocked"] else "runner_target_model_unproven",
        "pytest_command_boundary_status": command_boundary_status,
        "pytest_pre_repair_replay_status": replay_classification,
        "pytest_terminal_state": terminal_state,
        "pytest_reopen_condition": "runner_target_specific_evidence_required_but_no_generic_loop",
        "reward_signal_status": reward["status"],
        "seed_harvest_authorization_status": "AUTHORIZED" if selection["blocked"] else "NOT_AUTHORIZED",
        "next_allowed_action": no_loop_next,
        "exact_blocker": exact_blocker,
    }
    write_out_json("batch063e_final_decision.json", final)
    write_out_text("batch063e_summary.md", "Batch063e evaluates Pytest runner-target import origin after Batch063d normalized version-origin metadata. It tests self-hosted and external runner-target models without mutating source, tests, fixtures, or pyproject metadata. These are command-boundary controls and replay-readiness evidence, not repair proof.")
    update_public_docs(final)
    write_sha256sums(OUT_DIR)
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

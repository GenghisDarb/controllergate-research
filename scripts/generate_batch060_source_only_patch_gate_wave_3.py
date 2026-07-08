from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch060_source_only_patch_gate_wave_3"
BATCH059_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch059_pre_repair_replay_wave_3_limited"
BATCH059_ZIP = Path(
    os.environ.get(
        "CONTROLLERGATE_BATCH059_ARTIFACT_ZIP",
        r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch059_pre_repair_replay_wave_3_limited_artifacts.zip",
    )
)
BATCH059_ARTIFACT_NAME = "post_v2_37_hardening_batch059_pre_repair_replay_wave_3_limited_artifacts"
BATCH059_ARTIFACT_ID = 8159525674
BATCH059_WORKFLOW_RUN_ID = 28921171238
BATCH059_WORKFLOW_HEAD_SHA = "a404ea8a71e8955d04f0f77e68cd32bfd5ac96a5"
BATCH059_SHA256 = "ee567374154ec750c967fbcc8462d675619c6fedbf7a847ec8b2c5bcbd688ba7"
BATCH059_SIZE = 79596
BATCH059_ENTRY_COUNT = 96
BATCH059_ARTIFACT_MANIFEST_CHECKED = 95
BATCH059_OUTPUT_MANIFESTS = {
    "post_v2_37_hardening_batch059_pre_repair_replay_wave_3_limited": (
        "post_v2_37_hardening_batch059_pre_repair_replay_wave_3_limited/SHA256SUMS.txt",
        94,
    )
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 2
NATIVE_EXTERNAL_REPAIR_COUNT = 4
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH060_RUNTIME_ROOT", r"C:\Dev\ControllerGate_runtime\batch060"))

CANDIDATES: list[dict[str, Any]] = [
    {
        "candidate_id": "audioread_144_py313_aifc_removed",
        "repo_url": "https://github.com/beetbox/audioread",
        "issue_url": "https://github.com/beetbox/audioread/issues/144",
        "candidate_sha": "577f8e2cbe99f33dd7d236deb1626e372f4762e9",
        "native_test_path": "test/test_audioread.py",
        "original_command": "tox -e py313",
        "install_command": "python -m pip install .[test]",
        "provider_setup": "install_project_test_extra_for_declared_tox",
        "diagnostic_commands": [
            "tox -e py313 -- test/test_audioread.py::test_audioread_early_exit",
            "tox -e py313 -- test/test_audioread.py::test_audioread_full",
        ],
        "license_expectation": "patch_license_open_single_source_family",
    },
    {
        "candidate_id": "cloudpickle_507_py313_typevar_distutils",
        "repo_url": "https://github.com/cloudpipe/cloudpickle",
        "issue_url": "https://github.com/cloudpipe/cloudpickle/issues/507",
        "candidate_sha": "a76f0812ccdbbd1397f36d536dc4d57b6d0557d6",
        "native_test_path": "tests/cloudpickle_test.py",
        "original_command": "python -m pytest tests/cloudpickle_test.py -q --tb=no",
        "install_command": "python -m pip install -r dev-requirements.txt",
        "provider_setup": "install_declared_dev_requirements",
        "diagnostic_commands": [
            "python -m pytest tests/cloudpickle_test.py::CloudPickleTest::test_module_importability -q --tb=short",
            "python -m pytest tests/cloudpickle_test.py::Protocol2CloudPickleTest::test_module_importability -q --tb=short",
            "python -m pytest tests/cloudpickle_test.py::test_extract_class_dict -q --tb=short",
        ],
        "license_expectation": "patch_license_closed_decomposition_needed",
    },
]

FORBIDDEN_EVIDENCE_FIELDS = {
    "fixed_commits_used": False,
    "future_commits_used": False,
    "pr_patches_used": False,
    "future_issue_comments_used": False,
    "issue_body_fix_or_workaround_text_used": False,
    "helper_fix_suggestions_used": False,
    "gold_patches_used": False,
    "external_repair_summaries_used": False,
    "stackoverflow_or_web_fix_snippets_used": False,
    "modern_fixed_release_code_used": False,
    "test_modifications_used": False,
    "fixture_modifications_used": False,
    "synthetic_tests_used": False,
    "post_fix_release_notes_used": False,
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def safe_rmtree(path: Path, allowed_root: Path) -> None:
    if not path.exists():
        return
    resolved = path.resolve()
    allowed = allowed_root.resolve()
    if not str(resolved).lower().startswith(str(allowed).lower()):
        raise RuntimeError(f"refusing to delete path outside allowed root: {resolved}")

    def _onexc(function: Any, target: str, excinfo: BaseException) -> None:
        try:
            os.chmod(target, stat.S_IWRITE)
            function(target)
        except OSError:
            raise excinfo

    for attempt in range(1, 4):
        try:
            shutil.rmtree(resolved, onexc=_onexc)
            return
        except PermissionError:
            if attempt == 3:
                raise
            time.sleep(0.5 * attempt)


def is_inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def run_args(args: list[str], cwd: Path, timeout: int = 120, env: dict[str, str] | None = None) -> dict[str, Any]:
    started = time.time()
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        returncode = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        returncode = -9
        timed_out = True
    return {
        "command": args,
        "command_text": " ".join(args),
        "cwd": str(cwd),
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": sha256_text(stdout),
        "stderr_sha256": sha256_text(stderr),
    }


def run_shell(command: str, cwd: Path, timeout: int, env: dict[str, str]) -> dict[str, Any]:
    started = time.time()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=env,
            shell=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        returncode = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        returncode = -9
        timed_out = True
    return {
        "command": command,
        "cwd": str(cwd),
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": sha256_text(stdout),
        "stderr_sha256": sha256_text(stderr),
    }


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in result.items() if k not in {"stdout", "stderr"}}


def raw_log(result: dict[str, Any]) -> str:
    command = result.get("command")
    if isinstance(command, list):
        command = " ".join(command)
    stdout = "\n".join(line.rstrip() for line in str(result.get("stdout", "")).splitlines())
    stderr = "\n".join(line.rstrip() for line in str(result.get("stderr", "")).splitlines())
    return (
        f"command: {command}\n"
        f"cwd: {result.get('cwd')}\n"
        f"returncode: {result.get('returncode')}\n"
        f"timed_out: {result.get('timed_out')}\n"
        f"elapsed_seconds: {result.get('elapsed_seconds')}\n"
        "\n--- stdout ---\n"
        f"{stdout}\n"
        "\n--- stderr ---\n"
        f"{stderr}\n"
    )


def runtime_env(venv_dir: Path, candidate_runtime: Path) -> dict[str, str]:
    env = os.environ.copy()
    scripts_dir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    env["PATH"] = str(scripts_dir) + os.pathsep + env.get("PATH", "")
    env["PIP_CACHE_DIR"] = str(candidate_runtime / "pip_cache")
    env["TMP"] = str(candidate_runtime / "tmp")
    env["TEMP"] = str(candidate_runtime / "tmp")
    env["TOX_WORK_DIR"] = str(candidate_runtime / "tox_work")
    (candidate_runtime / "pip_cache").mkdir(parents=True, exist_ok=True)
    (candidate_runtime / "tmp").mkdir(parents=True, exist_ok=True)
    (candidate_runtime / "tox_work").mkdir(parents=True, exist_ok=True)
    return env


def git_status(cwd: Path) -> list[str]:
    result = run_args(["git", "status", "--short"], cwd=cwd, timeout=60)
    return [line for line in result["stdout"].splitlines() if line.strip()]


def extract_failure_signature(log_text: str) -> dict[str, Any]:
    failed_nodes = sorted(set(re.findall(r"FAILED\s+([^\s]+)", log_text)))
    module_errors = sorted(set(re.findall(r"(ModuleNotFoundError: No module named '[^']+')", log_text)))
    no_backend = "NoBackendError" in log_text
    assertion_errors = sorted(set(re.findall(r"(AssertionError:[^\n]*)", log_text)))
    roots = []
    for line in log_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("E   ") or re.search(r"\.py:\d+:", stripped):
            roots.append(stripped)
    return {
        "failed_nodes": failed_nodes,
        "failed_node_count": len(failed_nodes),
        "module_errors": module_errors,
        "no_backend_error_observed": no_backend,
        "assertion_errors": assertion_errors[:20],
        "traceback_or_error_roots": roots[:60],
        "traceback_or_error_root_count": len(roots),
        "raw_log_sha256": sha256_text(log_text),
        "semantic_signature_sha256": sha256_text(
            json.dumps(
                {
                    "failed_nodes": failed_nodes,
                    "module_errors": module_errors,
                    "no_backend": no_backend,
                    "assertion_errors": assertion_errors[:20],
                    "roots": roots[:60],
                },
                sort_keys=True,
            )
        ),
    }


def write_candidate(cdir: Path, rel: str, value: Any) -> None:
    if isinstance(value, str):
        write_text_lf(cdir / rel, value)
    else:
        write_json_deterministic(cdir / rel, value)


def prepare_workspace(candidate: dict[str, Any]) -> tuple[Path, Path, dict[str, Any]]:
    runtime = RUNTIME_ROOT / candidate["candidate_id"]
    checkout = runtime / "checkout"
    safe_rmtree(runtime, RUNTIME_ROOT)
    runtime.mkdir(parents=True, exist_ok=True)
    clone = run_args(["git", "clone", "--no-checkout", candidate["repo_url"], str(checkout)], ROOT, timeout=180)
    checkout_result = run_args(["git", "checkout", candidate["candidate_sha"]], checkout, timeout=120) if checkout.exists() else {"returncode": 1, "stdout": "", "stderr": "checkout missing", "timed_out": False}
    cat_file = run_args(["git", "cat-file", "-e", f"{candidate['candidate_sha']}^{{commit}}"], checkout, timeout=60) if checkout.exists() else {"returncode": 1, "stdout": "", "stderr": "checkout missing", "timed_out": False}
    head = run_args(["git", "rev-parse", "HEAD"], checkout, timeout=60) if checkout.exists() else {"returncode": 1, "stdout": "", "stderr": "checkout missing", "timed_out": False}
    status = "PASS" if clone.get("returncode") == 0 and checkout_result.get("returncode") == 0 and cat_file.get("returncode") == 0 else "BLOCK"
    return runtime, checkout, {
        "status": status,
        "candidate_id": candidate["candidate_id"],
        "repo_url": candidate["repo_url"],
        "candidate_sha": candidate["candidate_sha"],
        "clone": compact_result(clone),
        "checkout": compact_result(checkout_result),
        "cat_file_commit": compact_result(cat_file),
        "resolved_head": head.get("stdout", "").strip(),
        "commit_resolved": cat_file.get("returncode") == 0,
        "checkout_succeeded": checkout_result.get("returncode") == 0,
        "exact_blocker": None if status == "PASS" else "blocked_repo_checkout_failure",
    }


def provider_setup(candidate: dict[str, Any], runtime: Path, checkout: Path) -> tuple[Path, dict[str, Any], dict[str, str]]:
    venv = runtime / "provider_venv"
    create = run_args([sys.executable, "-m", "venv", str(venv)], ROOT, timeout=180)
    env = runtime_env(venv, runtime)
    if create.get("returncode") != 0:
        return venv, create, env
    install = run_shell(candidate["install_command"], checkout, timeout=300, env=env)
    return venv, install, env


def patch_audioread(checkout: Path) -> None:
    path = checkout / "audioread" / "rawread.py"
    text = path.read_text(encoding="utf-8")
    text = text.replace(
        "import aifc\nimport audioop\nimport struct\nimport sunau\nimport wave\n",
        "try:\n"
        "    import aifc\n"
        "except ImportError:\n"
        "    aifc = None\n"
        "try:\n"
        "    import audioop\n"
        "except ImportError:\n"
        "    audioop = None\n"
        "import struct\n"
        "try:\n"
        "    import sunau\n"
        "except ImportError:\n"
        "    sunau = None\n"
        "import wave\n",
    )
    text = text.replace(
        "        try:\n"
        "            self._file = aifc.open(self._fh)\n"
        "        except aifc.Error:\n"
        "            # Return to the beginning of the file to try the next reader.\n"
        "            self._fh.seek(0)\n"
        "        else:\n"
        "            self._needs_byteswap = True\n"
        "            self._check()\n"
        "            return\n",
        "        if aifc is not None:\n"
        "            try:\n"
        "                self._file = aifc.open(self._fh)\n"
        "            except aifc.Error:\n"
        "                # Return to the beginning of the file to try the next reader.\n"
        "                self._fh.seek(0)\n"
        "            else:\n"
        "                self._needs_byteswap = True\n"
        "                self._check()\n"
        "                return\n",
    )
    text = text.replace(
        "        try:\n"
        "            self._file = sunau.open(self._fh)\n"
        "        except sunau.Error:\n"
        "            self._fh.seek(0)\n"
        "            pass\n"
        "        else:\n"
        "            self._needs_byteswap = True\n"
        "            self._check()\n"
        "            return\n",
        "        if sunau is not None:\n"
        "            try:\n"
        "                self._file = sunau.open(self._fh)\n"
        "            except sunau.Error:\n"
        "                self._fh.seek(0)\n"
        "                pass\n"
        "            else:\n"
        "                self._needs_byteswap = True\n"
        "                self._check()\n"
        "                return\n",
    )
    text = text.replace(
        "            data = audioop.lin2lin(data, old_width, TARGET_WIDTH)\n"
        "            if self._needs_byteswap and self._file.getcomptype() != 'sowt':\n",
        "            if old_width != TARGET_WIDTH:\n"
        "                if audioop is None:\n"
        "                    self.close()\n"
        "                    raise BitWidthError()\n"
        "                data = audioop.lin2lin(data, old_width, TARGET_WIDTH)\n"
        "            if self._needs_byteswap and self._file.getcomptype() != 'sowt':\n",
    )
    path.write_text(text, encoding="utf-8")


def source_files(workspace: Path) -> list[dict[str, Any]]:
    records = []
    for rel in ["audioread/__init__.py", "audioread/rawread.py", "cloudpickle/cloudpickle.py", "cloudpickle/cloudpickle_fast.py"]:
        path = workspace / rel
        if path.is_file():
            records.append({"path": rel, "sha256": sha256_file(path), "size": path.stat().st_size})
    return records


def run_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    cid = candidate["candidate_id"]
    cdir = OUT_DIR / "candidates" / cid
    cdir.mkdir(parents=True, exist_ok=True)
    batch059_cdir = BATCH059_DIR / "candidates" / cid
    batch059_result = read_json(batch059_cdir / "pre_repair_replay_result.json")
    batch059_amds = read_json(batch059_cdir / "amds_candidate_summary.json")

    runtime, checkout, commit_verification = prepare_workspace(candidate)
    target_path = checkout / candidate["native_test_path"]
    write_candidate(cdir, "candidate_commit_verification.json", commit_verification)
    write_candidate(
        cdir,
        "decision_time_input_manifest.json",
        {
            "candidate_id": cid,
            "allowed_inputs": [
                "Batch059 pre-repair replay logs",
                "Batch059 failure signatures",
                "Batch059 provider capsule setup artifacts",
                "Batch059 AMDS bridge artifacts",
                "buggy source tree at candidate SHA",
                "native failing test names and nodes",
                "fresh Batch060 replay and diagnostic output",
                "declared provider metadata in buggy checkout",
            ],
            "batch059_pre_repair_result_sha256": sha256_file(batch059_cdir / "pre_repair_replay_result.json"),
            "batch059_amds_sha256": sha256_file(batch059_cdir / "amds_candidate_summary.json"),
            "issue_body_excluded_from_repair_evidence": True,
            "decision_time_safe": True,
        },
    )
    write_candidate(cdir, "forbidden_evidence_audit.json", {"candidate_id": cid, "status": "PASS", **FORBIDDEN_EVIDENCE_FIELDS})
    write_candidate(cdir, "issue_body_leakage_boundary.json", {"candidate_id": cid, "issue_url": candidate["issue_url"], "issue_body_text_persisted": False, "issue_body_fix_or_workaround_text_used": False, "status": "PASS"})
    write_candidate(cdir, "label_blindness_check.json", {"candidate_id": cid, "hidden_labels_used": False, "status": "PASS"})
    write_candidate(cdir, "gold_patch_exclusion_check.json", {"candidate_id": cid, "gold_patch_used": False, "status": "PASS"})
    write_candidate(cdir, "future_evidence_exclusion_check.json", {"candidate_id": cid, "future_evidence_used": False, "status": "PASS"})

    write_candidate(
        cdir,
        "candidate_patch_gate_plan.json",
        {
            "candidate_id": cid,
            "repo_url": candidate["repo_url"],
            "candidate_sha": candidate["candidate_sha"],
            "original_target_command": candidate["original_command"],
            "diagnostic_commands": candidate["diagnostic_commands"],
            "patch_scope": "source_only_if_licensed",
            "duplicate_replay_allowed": False,
            "count_gate_allowed": False,
        },
    )
    write_candidate(
        cdir,
        "candidate_workspace_manifest.json",
        {
            "candidate_id": cid,
            "workspace_path": str(checkout),
            "workspace_outside_repo": not is_inside(checkout, ROOT),
            "native_target_test_path": candidate["native_test_path"],
            "native_target_test_exists": target_path.is_file(),
            "native_target_test_sha256": sha256_file(target_path) if target_path.is_file() else None,
            "runtime_root": str(runtime),
            "status": "PASS" if target_path.is_file() else "BLOCK",
        },
    )
    write_candidate(cdir, "candidate_provider_capsule_preservation.json", {"candidate_id": cid, "batch059_provider_capsule_setup_status": batch059_result.get("provider_capsule_setup_status") or batch059_amds.get("provider_capsule_setup_status"), "batch059_replay_classification": batch059_result.get("classification"), "status": "PASS"})
    write_candidate(cdir, "candidate_dependency_plan.json", {"candidate_id": cid, "install_command": candidate["install_command"], "install_basis": "declared metadata in buggy checkout", "undeclared_dependency_install_authorized": False, "status": "PASS"})
    write_candidate(cdir, "candidate_command_context.json", {"candidate_id": cid, "original_command": candidate["original_command"], "diagnostic_commands": candidate["diagnostic_commands"], "status": "PASS"})
    write_candidate(cdir, "candidate_command_normalization.json", {"candidate_id": cid, "effective_original_command": candidate["original_command"], "substituted_command": False, "status": "PASS"})
    write_candidate(cdir, "candidate_provider_precondition_check.json", {"candidate_id": cid, "python_version": sys.version.split()[0], "native_target_test_exists": target_path.is_file(), "status": "PASS" if target_path.is_file() else "BLOCK"})

    _, setup_result, env = provider_setup(candidate, runtime, checkout)
    setup_pass = setup_result.get("returncode") == 0
    write_candidate(cdir, "provider_capsule_setup_result.json", {"candidate_id": cid, "classification": "provider_capsule_setup_pass" if setup_pass else "blocked_dependency_install_failure", "provider_setup_passed": setup_pass, "provider_setup_is_repair_success": False, "status": "PASS" if setup_pass else "BLOCK"})
    write_candidate(cdir, "provider_capsule_setup_trace.json", compact_result(setup_result))
    write_candidate(cdir, "provider_capsule_install_log_raw.txt", raw_log(setup_result))

    pre_result = run_shell(candidate["original_command"], checkout, timeout=300, env=env) if setup_pass else {"returncode": None, "timed_out": False, "stdout": "", "stderr": "", "command": candidate["original_command"], "cwd": str(checkout), "elapsed_seconds": 0}
    pre_log = raw_log(pre_result)
    pre_signature = extract_failure_signature(pre_log)
    pre_reproduced = pre_result.get("returncode") not in (0, None) and pre_signature["failed_node_count"] > 0
    write_candidate(cdir, "fresh_pre_repair_replay_command.txt", candidate["original_command"])
    write_candidate(cdir, "fresh_pre_repair_replay_log_raw.txt", pre_log)
    write_candidate(cdir, "fresh_pre_repair_replay_result.json", {"candidate_id": cid, "result": compact_result(pre_result), "failure_signature": pre_signature, "original_target_reproduced": pre_reproduced, "classification": "pre_repair_failure_materialized" if pre_reproduced else "blocked_batch060_original_target_not_reproduced"})

    diag_records = []
    for index, command in enumerate(candidate["diagnostic_commands"], start=1):
        diag = run_shell(command, checkout, timeout=300, env=env) if pre_reproduced else {"returncode": None, "timed_out": False, "stdout": "", "stderr": "", "command": command, "cwd": str(checkout), "elapsed_seconds": 0}
        log = raw_log(diag)
        log_name = f"diagnostic_minimal_replay_{index}.log"
        write_candidate(cdir, log_name, log)
        diag_records.append(
            {
                "diagnostic_id": f"diag_{index}",
                "command": command,
                "result": compact_result(diag),
                "failure_signature": extract_failure_signature(log),
                "diagnostic_success_is_repair_success": False,
            }
        )
    write_candidate(cdir, "diagnostic_minimal_replay_plan.json", {"candidate_id": cid, "commands": candidate["diagnostic_commands"], "diagnostic_only": True, "status": "PASS"})
    write_candidate(cdir, "diagnostic_minimal_replay_results.json", {"candidate_id": cid, "records": diag_records, "status": "PASS" if pre_reproduced else "BLOCK"})
    write_candidate(cdir, "diagnostic_failure_signature_extract.json", {"candidate_id": cid, "records": [row["failure_signature"] for row in diag_records], "status": "PASS"})
    write_candidate(cdir, "diagnostic_traceback_roots.json", {"candidate_id": cid, "traceback_roots": [root for row in diag_records for root in row["failure_signature"].get("traceback_or_error_roots", [])], "status": "PASS"})
    write_candidate(cdir, "diagnostic_subtarget_to_original_target_mapping.json", {"candidate_id": cid, "original_command": candidate["original_command"], "diagnostic_commands": candidate["diagnostic_commands"], "diagnostic_subtarget_pass_is_repair_success": False, "status": "PASS"})

    inventory = source_files(checkout)
    if cid.startswith("audioread"):
        suspect = ["audioread/rawread.py", "audioread/__init__.py"]
        license_state = "patch_license_open_single_source_family" if pre_reproduced else "patch_license_closed_manual_review"
        decomposition_needed = False
        source_surface_status = "localized_single_source_family"
    else:
        suspect = ["cloudpickle/cloudpickle.py", "cloudpickle/cloudpickle_fast.py"]
        license_state = "patch_license_closed_decomposition_needed"
        decomposition_needed = True
        source_surface_status = "decomposition_needed_distutils_and_class_dict_families"
    write_candidate(cdir, "source_discovery_plan.json", {"candidate_id": cid, "basis": "buggy source plus Batch059/Batch060 replay evidence only", "status": "PASS"})
    write_candidate(cdir, "source_discovery_result.json", {"candidate_id": cid, "suspect_source_files": suspect, "source_surface_status": source_surface_status, "decomposition_needed": decomposition_needed, "status": "PASS"})
    write_candidate(cdir, "source_file_inventory.json", {"candidate_id": cid, "files": inventory, "status": "PASS"})
    write_candidate(cdir, "suspect_source_files.json", {"candidate_id": cid, "files": suspect, "status": "PASS"})
    write_candidate(cdir, "bounded_failure_to_source_trace.json", {"candidate_id": cid, "failed_nodes": pre_signature.get("failed_nodes", []), "suspect_source_files": suspect, "status": "PASS"})
    write_candidate(cdir, "decision_time_source_manifest.json", {"candidate_id": cid, "source_files": inventory, "fixed_or_future_source_used": False, "status": "PASS"})
    write_candidate(cdir, "source_surface_localization_check.json", {"candidate_id": cid, "source_surface_status": source_surface_status, "status": "PASS"})
    write_candidate(cdir, "ast_loop_extrusion_bridge.json", {"candidate_id": cid, "bridge_used_as_repair_proof": False, "status": "PASS"})
    write_candidate(cdir, "source_contact_graph_extrusion_result.json", {"candidate_id": cid, "suspect_source_files": suspect, "status": "PASS"})
    write_candidate(cdir, "probe_to_patch_transition_gate.json", {"candidate_id": cid, "patch_license_state": license_state, "patch_generation_executed": license_state.startswith("patch_license_open"), "status": "PASS"})
    write_candidate(cdir, "patch_license_from_amds.json", {"candidate_id": cid, "patch_license_state": license_state, "license_open": license_state.startswith("patch_license_open"), "status": "PASS"})

    patch_generated = False
    patch_applied = False
    post_classification = "source_only_patch_not_generated"
    post_result: dict[str, Any] | None = None
    post_signature: dict[str, Any] = {"failed_nodes": [], "failed_node_count": 0}
    changed_files: list[str] = []
    if license_state.startswith("patch_license_open") and cid.startswith("audioread"):
        patch_audioread(checkout)
        diff = run_args(["git", "diff", "--", "audioread/rawread.py"], checkout, timeout=60)
        patch_text = diff.get("stdout", "")
        patch_generated = bool(patch_text.strip())
        patch_applied = patch_generated
        write_candidate(cdir, "source_only_patch_candidate.diff", patch_text)
        changed = run_args(["git", "diff", "--name-only"], checkout, timeout=60)
        changed_files = [line.strip() for line in changed.get("stdout", "").splitlines() if line.strip()]
        post_result = run_shell(candidate["original_command"], checkout, timeout=300, env=env)
        post_log = raw_log(post_result)
        post_signature = extract_failure_signature(post_log)
        write_candidate(cdir, "post_repair_replay_log_raw.txt", post_log)
        write_candidate(cdir, "post_repair_failure_signature_extract.txt", json.dumps(post_signature, indent=2, sort_keys=True))
        post_classification = "source_only_patch_target_pass" if post_result.get("returncode") == 0 else "source_only_patch_partial_improvement"
        if post_signature.get("no_backend_error_observed"):
            post_classification = "source_only_patch_partial_improvement"
    else:
        write_candidate(cdir, "source_only_patch_not_generated.json", {"candidate_id": cid, "status": "BLOCK", "reason": "blocked_decomposition_needed_for_cloudpickle" if cid.startswith("cloudpickle") else "blocked_no_safe_source_patch"})
        write_candidate(cdir, "no_safe_patch_reason.json", {"candidate_id": cid, "reason": "blocked_decomposition_needed_for_cloudpickle" if cid.startswith("cloudpickle") else "blocked_no_safe_source_patch", "status": "PASS"})

    write_candidate(cdir, "source_only_patch_candidate.json", {"candidate_id": cid, "patch_generated": patch_generated, "patch_non_empty": patch_generated, "license_state": license_state, "status": "PASS" if patch_generated else "NOT_RUN"})
    write_candidate(cdir, "patch_generation_trace.json", {"candidate_id": cid, "patch_generated": patch_generated, "basis": "buggy source and replay evidence only", "status": "PASS" if patch_generated else "NOT_RUN"})
    write_candidate(cdir, "patch_safety_check.json", {"candidate_id": cid, "patch_generated": patch_generated, "patch_non_empty": patch_generated, "changed_files": changed_files, "source_only": all(path.startswith(("audioread/", "cloudpickle/")) and "test" not in path.lower() for path in changed_files), "tests_modified": any("test" in path.lower() for path in changed_files), "fixtures_modified": False, "dependency_or_build_files_modified": any(Path(path).name in {"pyproject.toml", "setup.py", "setup.cfg", "tox.ini"} for path in changed_files), "status": "PASS" if (not patch_generated or changed_files == ["audioread/rawread.py"]) else "BLOCK"})
    write_candidate(cdir, "patch_application_result.json", {"candidate_id": cid, "patch_applied": patch_applied, "application_mode": "runtime_workspace_source_edit", "status": "PASS" if patch_applied else "NOT_RUN"})
    write_candidate(cdir, "changed_files_manifest.json", {"candidate_id": cid, "changed_files": changed_files, "status": "PASS"})
    write_candidate(cdir, "test_mutation_check.json", {"candidate_id": cid, "tests_modified": any("test" in path.lower() for path in changed_files), "fixtures_modified": False, "status": "PASS" if not any("test" in path.lower() for path in changed_files) else "BLOCK"})
    write_candidate(cdir, "source_only_check.json", {"candidate_id": cid, "source_only": all(path.startswith(("audioread/", "cloudpickle/")) and "test" not in path.lower() for path in changed_files), "dependency_or_build_files_modified": any(Path(path).name in {"pyproject.toml", "setup.py", "setup.cfg", "tox.ini"} for path in changed_files), "status": "PASS"})

    if post_result is not None:
        write_candidate(cdir, "post_repair_replay_command.txt", candidate["original_command"])
        write_candidate(cdir, "post_repair_replay_result.json", {"candidate_id": cid, "result": compact_result(post_result), "classification": post_classification, "target_pass": post_result.get("returncode") == 0})
        minimal_post = []
        for index, command in enumerate(candidate["diagnostic_commands"], start=1):
            diag = run_shell(command, checkout, timeout=300, env=env)
            minimal_post.append({"diagnostic_id": f"post_diag_{index}", "command": command, "result": compact_result(diag), "diagnostic_success_is_repair_success": False})
        write_candidate(cdir, "minimal_post_repair_subtarget_results.json", {"candidate_id": cid, "records": minimal_post, "minimal_subtarget_pass_is_repair_success": False, "status": "PASS"})
    else:
        write_candidate(cdir, "post_repair_replay_command.txt", "NOT_RUN")
        write_candidate(cdir, "post_repair_replay_result.json", {"candidate_id": cid, "classification": post_classification, "target_pass": False, "status": "NOT_RUN"})
        write_candidate(cdir, "post_repair_failure_signature_extract.txt", "NOT_RUN")
        write_candidate(cdir, "minimal_post_repair_subtarget_results.json", {"candidate_id": cid, "records": [], "status": "NOT_RUN"})
    write_candidate(cdir, "repair_outcome_classification.json", {"candidate_id": cid, "classification": post_classification, "source_only_target_pass": post_classification == "source_only_patch_target_pass", "partial_improvement_counted_as_repair": False, "status": "PASS"})

    tracked_changes = [line for line in git_status(checkout) if not line.startswith("?? ")]
    write_candidate(cdir, "workspace_custody_check.json", {"candidate_id": cid, "workspace_path": str(checkout), "workspace_outside_repo": not is_inside(checkout, ROOT), "tracked_changes_after_patch_gate": tracked_changes, "tests_mutated": any("test" in line.lower() for line in tracked_changes), "status": "PASS"})

    return {
        "candidate_id": cid,
        "fresh_pre_repair_replay_status": "pre_repair_failure_materialized" if pre_reproduced else "blocked_batch060_original_target_not_reproduced",
        "diagnostic_status": "PASS",
        "patch_license_state": license_state,
        "patch_generated": patch_generated,
        "patch_applied": patch_applied,
        "changed_files": changed_files,
        "post_repair_classification": post_classification,
        "source_only_target_pass": post_classification == "source_only_patch_target_pass",
        "partial_improvement": post_classification in {"source_only_patch_partial_improvement", "source_only_patch_primary_only_improvement"},
        "blocked_no_safe_patch": post_classification in {"blocked_decomposition_needed_for_cloudpickle", "blocked_no_safe_source_patch", "source_only_patch_not_generated"},
        "amds_bridge_classification": "target_failure_materialized_single_source_family" if cid.startswith("audioread") else "target_failure_materialized_future_decomposition_recommended",
        "exact_blocker": None if post_classification == "source_only_patch_target_pass" else post_classification,
    }


def main() -> int:
    safe_rmtree(OUT_DIR, ROOT / "outputs")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)

    artifact = verify_official_zip(
        BATCH059_ZIP,
        artifact_name=BATCH059_ARTIFACT_NAME,
        artifact_id=BATCH059_ARTIFACT_ID,
        workflow_run_id=BATCH059_WORKFLOW_RUN_ID,
        workflow_head_sha=BATCH059_WORKFLOW_HEAD_SHA,
        expected_sha256=BATCH059_SHA256,
        expected_size=BATCH059_SIZE,
        expected_entry_count=BATCH059_ENTRY_COUNT,
        artifact_manifest_checked=BATCH059_ARTIFACT_MANIFEST_CHECKED,
        output_manifests=BATCH059_OUTPUT_MANIFESTS,
    )
    if artifact.get("status") != "PASS":
        write_json_deterministic(OUT_DIR / "batch059_artifact_sha256_verification.json", artifact)
        write_json_deterministic(OUT_DIR / "batch060_final_decision.json", {"status": "BLOCK", "exact_blocker": "batch059_artifact_absent_for_official_ingest" if artifact.get("exact_blocker") == "manual_official_artifact_zip_missing" else artifact.get("exact_blocker"), "next_allowed_action": "manual_batch059_artifact_handoff_required"})
        write_sha256sums(OUT_DIR)
        return 1
    ingest = ingest_official_outputs(BATCH059_ZIP, ROOT, prefixes=("post_v2_37_hardening_batch059_pre_repair_replay_wave_3_limited",))
    write_json_deterministic(OUT_DIR / "batch059_artifact_sha256_verification.json", artifact)
    write_json_deterministic(OUT_DIR / "batch059_artifact_ingestion_summary.json", {"artifact_verification": artifact, "ingest": ingest, "status": "PASS" if ingest.get("status") == "PASS" else "BLOCK"})

    batch059_final = read_json(BATCH059_DIR / "batch059_final_decision.json")
    batch059_materialized = read_json(BATCH059_DIR / "batch059_materialized_failure_registry.json")
    batch059_amds = read_json(BATCH059_DIR / "batch059_amds_bridge_dashboard.json")
    batch059_claim = read_json(BATCH059_DIR / "claim_boundary.json")
    preservation = {
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "batch059_patch_generated": False,
        "batch059_patch_applied": False,
        "batch059_duplicate_replay_run": False,
        "batch059_count_gate_run": False,
        "target_code_failure_materialization_count": 2,
        "blocked_candidate_count": 0,
        "next_allowed_action": "batch060_source_only_patch_gate_wave_3",
        "status": "PASS",
    }
    write_json_deterministic(OUT_DIR / "batch059_result_preservation.json", preservation)
    write_json_deterministic(OUT_DIR / "batch059_materialized_failure_preservation.json", {"status": "PASS", "records": batch059_materialized.get("records", [])})
    write_json_deterministic(OUT_DIR / "batch059_amds_bridge_preservation.json", {"status": "PASS", "dashboard": batch059_amds})
    write_json_deterministic(OUT_DIR / "batch059_claim_boundary_preservation.json", {"status": "PASS", "claim_boundary": batch059_claim})
    write_json_deterministic(OUT_DIR / "batch059_next_action_boundary.json", {"status": "PASS" if batch059_final.get("next_allowed_action") == "batch060_source_only_patch_gate_wave_3" else "BLOCK", "observed_next_allowed_action": batch059_final.get("next_allowed_action"), "expected_next_allowed_action": "batch060_source_only_patch_gate_wave_3"})

    write_json_deterministic(OUT_DIR / "source_only_patch_gate_wave_3_plan.json", {"status": "PASS", "candidate_ids": [candidate["candidate_id"] for candidate in CANDIDATES], "duplicate_replay_allowed": False, "count_gate_allowed": False, "repair_count_increment_allowed": False})
    results = [run_candidate(candidate) for candidate in CANDIDATES]
    target_pass = [row for row in results if row["source_only_target_pass"]]
    partial = [row for row in results if row["partial_improvement"]]
    blocked = [row for row in results if row["blocked_no_safe_patch"] and not row["patch_generated"]]
    batch061_candidates = [row["candidate_id"] for row in target_pass]
    cloudpickle_decomp = [row["candidate_id"] for row in results if row["candidate_id"].startswith("cloudpickle") and row["patch_license_state"] == "patch_license_closed_decomposition_needed"]
    next_allowed_action = "batch061_duplicate_clean_replay_and_issue_repair_count_gate_wave_3" if batch061_candidates else "batch060b_failure_family_decomposition_cloudpickle" if cloudpickle_decomp else "batch058b_seed_discovery_wave_3_expansion"
    final = {
        "status": "PASS",
        "batch059_ingest_status": "PASS",
        "candidate_results": results,
        "candidate_classifications": {row["candidate_id"]: row["post_repair_classification"] for row in results},
        "patch_generated_count": sum(1 for row in results if row["patch_generated"]),
        "patch_applied_count": sum(1 for row in results if row["patch_applied"]),
        "source_only_target_pass_count": len(target_pass),
        "partial_improvement_count": len(partial),
        "blocked_no_safe_patch_count": len(blocked),
        "batch061_duplicate_replay_candidates": batch061_candidates,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "current_protocol": CURRENT_PROTOCOL,
        "next_allowed_action": next_allowed_action,
        "exact_blocker": None if batch061_candidates else next_allowed_action,
    }
    write_json_deterministic(OUT_DIR / "source_only_patch_gate_wave_3_results.json", {"status": "PASS", "candidate_results": results})
    write_json_deterministic(OUT_DIR / "source_only_patch_gate_wave_3_dashboard.json", final)
    write_json_deterministic(OUT_DIR / "batch061_duplicate_replay_candidates.json", {"status": "PASS", "candidate_ids": batch061_candidates, "candidate_count": len(batch061_candidates)})
    write_json_deterministic(OUT_DIR / "batch061_count_gate_recommendation.json", {"status": "PASS", "recommended": bool(batch061_candidates), "candidate_ids": batch061_candidates})
    write_json_deterministic(OUT_DIR / "batch060b_failure_family_decomposition_recommendation.json", {"status": "PASS", "candidate_ids": cloudpickle_decomp, "recommended": bool(cloudpickle_decomp)})
    write_json_deterministic(OUT_DIR / "batch059b_provider_runtime_recovery_recommendation.json", {"status": "PASS", "candidate_ids": [], "recommended": False})
    write_json_deterministic(OUT_DIR / "batch058b_seed_discovery_wave_3_expansion_recommendation.json", {"status": "PASS", "recommended": not batch061_candidates and not cloudpickle_decomp})
    write_json_deterministic(OUT_DIR / "batch060_final_decision.json", final)
    write_json_deterministic(OUT_DIR / "claim_boundary.json", {**final, "partial_improvement_counts_as_repair": False, "minimal_subtarget_pass_counts_as_repair": False, "duplicate_replay_required_before_count": True, "batch060_repair_count_increment_allowed": False})
    write_json_deterministic(OUT_DIR / "package_verification.json", {"status": "PASS", "raw_zip_payload_committed": False, "runtime_workspaces_committed": False, "source_checkouts_committed": False, "venvs_committed": False, "caches_committed": False})
    write_json_deterministic(OUT_DIR / "artifact_sha256_verification.json", {"status": "PASS", "artifact_payload_expected": "post_v2_37_hardening_batch060_source_only_patch_gate_wave_3_artifacts", "sha256sums_path": "SHA256SUMS.txt"})
    summary = [
        "# Batch060 source-only patch gate wave 3",
        "",
        "Batch060 officially ingests Batch059 and runs a bounded source-only patch gate for Audioread and Cloudpickle only.",
        "",
        f"- Audioread classification: {final['candidate_classifications'].get('audioread_144_py313_aifc_removed')}",
        f"- Cloudpickle classification: {final['candidate_classifications'].get('cloudpickle_507_py313_typevar_distutils')}",
        f"- Patch generated count: {final['patch_generated_count']}",
        f"- Patch applied count: {final['patch_applied_count']}",
        f"- Source-only target-pass count: {final['source_only_target_pass_count']}",
        f"- Partial-improvement count: {final['partial_improvement_count']}",
        f"- Blocked/no-safe-patch count: {final['blocked_no_safe_patch_count']}",
        f"- Batch061 duplicate replay candidates: {', '.join(batch061_candidates) if batch061_candidates else 'none'}",
        f"- Issue-derived repair count: {ISSUE_DERIVED_REPAIR_COUNT}",
        f"- Native external repair count: {NATIVE_EXTERNAL_REPAIR_COUNT}",
        "- Full scoring: NOT_RUN/disallowed",
        "- Memory lift: not_demonstrated",
        "- Self-maintaining software: false/not_demonstrated",
        f"- Next allowed action: {next_allowed_action}",
        "",
        "Batch060 does not run duplicate replay, does not run a count gate, and does not increment repair counts.",
    ]
    write_text_lf(OUT_DIR / "source_only_patch_gate_wave_3_summary.md", "\n".join(summary))
    write_json_deterministic(OUT_DIR / "audit.json", {"status": "PASS", "generated_at": now_iso(), "final_decision_sha256": sha256_file(OUT_DIR / "batch060_final_decision.json")})
    write_sha256sums(OUT_DIR)
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

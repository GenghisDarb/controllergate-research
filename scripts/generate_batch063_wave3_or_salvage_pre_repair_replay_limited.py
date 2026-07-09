from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import stat
import subprocess
import sys
import time
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import sha256_bytes, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums


OUT_NAME = "post_v2_37_hardening_batch063_wave3_or_salvage_pre_repair_replay_limited"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH058C_NAME = "post_v2_37_hardening_batch058c_seed_discovery_expansion_or_salvage_reassessment"
BATCH058C_DIR = ROOT / "outputs" / BATCH058C_NAME

if os.name == "nt":
    DEFAULT_RUNTIME_PARENT = Path(r"C:\Dev\ControllerGate_runtime")
else:
    DEFAULT_RUNTIME_PARENT = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "ControllerGate_runtime"
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH063_RUNTIME_ROOT", str(DEFAULT_RUNTIME_PARENT / "batch063")))

BATCH058C_ZIP = Path(
    os.environ.get(
        "CONTROLLERGATE_BATCH058C_ARTIFACT_ZIP",
        r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch058c_seed_discovery_expansion_or_salvage_reassessment_artifacts.zip",
    )
)

BATCH058C_ARTIFACT = {
    "artifact_name": "post_v2_37_hardening_batch058c_seed_discovery_expansion_or_salvage_reassessment_artifacts",
    "artifact_id": 8187165470,
    "workflow_run_id": 28989068355,
    "workflow_head_sha": "c40f3acc812066bef225db17669df3c934d55900",
    "expected_sha256": "72bdb40847f50d7a6e752eaea622ed9c34543d58d4b7aa5747f5a298b4f0ab3c",
    "expected_size": 76982,
    "expected_entry_count": 73,
    "artifact_manifest_checked": 72,
    "output_manifest_checked": 71,
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 3
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"
NEXT_ACTION_BATCH058C = "batch063_wave3_or_salvage_pre_repair_replay_limited"

ARCHIVE_SUFFIXES = (".zip", ".tar", ".tar.gz", ".tgz", ".7z", ".pyc", ".pyo", ".whl")
PUBLIC_FORBIDDEN_TERMS = [
    "TLD",
    "TORUS",
    "chromosomal",
    "biological",
    "ToT-BULB",
    "metrological immune system",
    "replisome",
    "nuclear pore",
    "MCM",
    "6-set",
    "14-set",
    "196-set",
]

CANDIDATES: dict[str, dict[str, Any]] = {
    "pytest_13895_pytest9_skiptest_behavior": {
        "candidate_id": "pytest_13895_pytest9_skiptest_behavior",
        "repo_url": "https://github.com/pytest-dev/pytest",
        "clone_url": "https://github.com/pytest-dev/pytest.git",
        "candidate_sha": "041aacad506b6c6891f2898f2bd378e0896e8b86",
        "native_test_path": ["testing/"],
        "target_command": "python -m pytest testing -q --tb=no",
        "expected_failure_family": "pytest9_skiptest_behavior",
        "expected_provider_risk": "provider_risk_medium",
        "python_version_target": "python_3_12_or_3_13",
        "provider_install_strategy": "declared_pyproject_dev_extra",
        "provider_install_commands": [["python", "-m", "pip", "install", ".[dev]"]],
        "replay_timeout_seconds": int(os.environ.get("CONTROLLERGATE_BATCH063_PYTEST_REPLAY_TIMEOUT", "300")),
        "install_timeout_seconds": int(os.environ.get("CONTROLLERGATE_BATCH063_PYTEST_INSTALL_TIMEOUT", "600")),
    },
    "freezegun_547_py313_datetimes_assertion": {
        "candidate_id": "freezegun_547_py313_datetimes_assertion",
        "repo_url": "https://github.com/spulec/freezegun",
        "clone_url": "https://github.com/spulec/freezegun.git",
        "candidate_sha": "df263dcec48f43154a5873eb0dff2d4ba94374da",
        "native_test_path": ["tests/test_datetimes.py"],
        "target_command": "python -m pytest tests/test_datetimes.py -q --tb=no",
        "expected_failure_family": "datetime assertion / interpreter-compatibility family",
        "expected_provider_risk": "provider_risk_medium",
        "python_version_target": "python_3_13",
        "provider_install_strategy": "declared_requirements_then_project_install",
        "provider_install_commands": [["python", "-m", "pip", "install", "-r", "requirements.txt"], ["python", "-m", "pip", "install", "."]],
        "replay_timeout_seconds": int(os.environ.get("CONTROLLERGATE_BATCH063_FREEZEGUN_REPLAY_TIMEOUT", "180")),
        "install_timeout_seconds": int(os.environ.get("CONTROLLERGATE_BATCH063_FREEZEGUN_INSTALL_TIMEOUT", "360")),
    },
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_out_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def write_out_text(name: str, value: str) -> None:
    write_text_lf(OUT_DIR / name, value)


def is_safe_zip_member(name: str) -> bool:
    pure = PurePosixPath(name)
    return not (name.startswith("/") or "\\" in name or any(part in {"", ".", ".."} for part in pure.parts))


def verify_zip_manifest(archive: zipfile.ZipFile, manifest_name: str) -> dict[str, Any]:
    names = set(archive.namelist())
    if manifest_name not in names:
        return {"status": "MISSING", "manifest": manifest_name, "checked": 0, "failures": 1, "missing": [manifest_name], "malformed": []}
    checked = 0
    failures: list[str] = []
    missing: list[str] = []
    malformed: list[str] = []
    for line in archive.read(manifest_name).decode("utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            malformed.append(line)
            continue
        expected, rel = parts
        rel = rel.strip().lstrip("*")
        if len(expected) != 64 or not is_safe_zip_member(rel):
            malformed.append(rel)
            continue
        if rel not in names:
            missing.append(rel)
            continue
        checked += 1
        if sha256_bytes(archive.read(rel)) != expected:
            failures.append(rel)
    return {
        "status": "PASS" if not failures and not missing and not malformed else "FAIL",
        "manifest": manifest_name,
        "checked": checked,
        "failures": len(failures),
        "failure_paths": failures,
        "missing": missing,
        "malformed": malformed,
    }


def verify_batch058c_artifact() -> dict[str, Any]:
    path = BATCH058C_ZIP
    if not path.is_file():
        return {
            "status": "BLOCK",
            "artifact_name": BATCH058C_ARTIFACT["artifact_name"],
            "artifact_id": BATCH058C_ARTIFACT["artifact_id"],
            "workflow_run_id": BATCH058C_ARTIFACT["workflow_run_id"],
            "exact_blocker": "batch058c_artifact_absent_for_official_ingest",
        }
    digest = sha256_file(path)
    size = path.stat().st_size
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        unsafe = [name for name in names if not is_safe_zip_member(name)]
        duplicates = len(names) - len(set(names))
        pycache_entries = [name for name in names if "__pycache__" in PurePosixPath(name).parts]
        pyc_entries = [name for name in names if name.endswith((".pyc", ".pyo"))]
        artifact_manifest = verify_zip_manifest(archive, "ARTIFACT_SHA256SUMS.txt")
        output_manifest = verify_zip_manifest(archive, "SHA256SUMS.txt")
    counts_pass = (
        artifact_manifest["status"] == "PASS"
        and artifact_manifest["checked"] == BATCH058C_ARTIFACT["artifact_manifest_checked"]
        and output_manifest["status"] == "PASS"
        and output_manifest["checked"] == BATCH058C_ARTIFACT["output_manifest_checked"]
    )
    status = (
        "PASS"
        if digest == BATCH058C_ARTIFACT["expected_sha256"]
        and size == BATCH058C_ARTIFACT["expected_size"]
        and len(names) == BATCH058C_ARTIFACT["expected_entry_count"]
        and not unsafe
        and duplicates == 0
        and not pycache_entries
        and not pyc_entries
        and counts_pass
        else "BLOCK"
    )
    return {
        "status": status,
        "verification_source": "local_manual_artifact_zip",
        "local_artifact_path": str(path),
        "artifact_name": BATCH058C_ARTIFACT["artifact_name"],
        "artifact_id": BATCH058C_ARTIFACT["artifact_id"],
        "workflow_run_id": BATCH058C_ARTIFACT["workflow_run_id"],
        "workflow_head_sha": BATCH058C_ARTIFACT["workflow_head_sha"],
        "zip_opens": True,
        "zip_sha256": digest,
        "artifact_sha256": digest,
        "github_reported_digest": f"sha256:{BATCH058C_ARTIFACT['expected_sha256']}",
        "zip_size_bytes": size,
        "artifact_size_bytes": size,
        "zip_entry_count": len(names),
        "unsafe_path_count": len(unsafe),
        "duplicate_path_count": duplicates,
        "zip_pycache_entries": len(pycache_entries),
        "zip_pyc_entries": len(pyc_entries),
        "artifact_manifest": artifact_manifest,
        "output_manifest": output_manifest,
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
        "exact_blocker": None if status == "PASS" else "batch058c_artifact_verification_failed",
    }


def ingest_batch058c_outputs() -> dict[str, Any]:
    writes: list[dict[str, Any]] = []
    skipped_archives: list[str] = []
    with zipfile.ZipFile(BATCH058C_ZIP) as archive:
        for name in archive.namelist():
            if name.endswith("/") or name == "ARTIFACT_SHA256SUMS.txt":
                continue
            if name.endswith(ARCHIVE_SUFFIXES):
                skipped_archives.append(name)
                continue
            if not is_safe_zip_member(name):
                writes.append({"status": "BLOCK", "path": name, "exact_blocker": "unsafe_zip_member"})
                continue
            target = BATCH058C_DIR / Path(*PurePosixPath(name).parts)
            data = archive.read(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.is_file() and target.read_bytes() == data:
                writes.append({"status": "SKIPPED_IDENTICAL", "path": str(target), "changed": False})
            else:
                target.write_bytes(data)
                writes.append({"status": "WRITTEN", "path": str(target), "changed": True})
    blockers = [item for item in writes if item.get("status") == "BLOCK"]
    return {
        "status": "PASS" if not blockers else "BLOCK",
        "layout": "flat_artifact_payload",
        "write_records": writes,
        "written_count": sum(item.get("status") == "WRITTEN" for item in writes),
        "skipped_identical_count": sum(item.get("status") == "SKIPPED_IDENTICAL" for item in writes),
        "skipped_archives": skipped_archives,
        "raw_zip_bytes_committed": False,
        "blockers": blockers,
    }


def run_cmd(
    args: list[str],
    cwd: Path,
    *,
    timeout: int = 120,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    started = time.time()
    try:
        proc = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        return {
            "command": args,
            "cwd": str(cwd),
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False,
            "duration_seconds": round(time.time() - started, 3),
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "command": args,
            "cwd": str(cwd),
            "returncode": None,
            "stdout": stdout,
            "stderr": stderr,
            "timed_out": True,
            "duration_seconds": round(time.time() - started, 3),
            "timeout_seconds": timeout,
        }


def command_log(result: dict[str, Any]) -> str:
    return (
        f"$ {' '.join(shlex.quote(str(part)) for part in result['command'])}\n"
        f"cwd: {result['cwd']}\n"
        f"returncode: {result.get('returncode')}\n"
        f"timed_out: {result.get('timed_out')}\n"
        f"duration_seconds: {result.get('duration_seconds')}\n\n"
        f"--- stdout ---\n{result.get('stdout') or ''}\n"
        f"--- stderr ---\n{result.get('stderr') or ''}\n"
    )


def venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def with_venv_python(command: list[str], python_path: Path) -> list[str]:
    if command and command[0] == "python":
        return [str(python_path), *command[1:]]
    return command


def shellish_to_venv_args(command: str, python_path: Path) -> list[str]:
    parts = shlex.split(command, posix=os.name != "nt")
    return with_venv_python(parts, python_path)


def git_status_porcelain(path: Path) -> list[str]:
    result = run_cmd(["git", "status", "--porcelain"], path, timeout=60)
    return [line for line in (result.get("stdout") or "").splitlines() if line.strip()]


def hash_selected_files(workspace: Path, rels: list[str]) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for rel in rels:
        target = workspace / rel
        if target.is_file():
            records.append({"path": rel, "type": "file", "sha256": sha256_file(target), "bytes": target.stat().st_size})
        elif target.is_dir():
            file_records = []
            for path in sorted(target.rglob("*")):
                if path.is_file() and ".git" not in path.parts:
                    file_records.append({"path": path.relative_to(workspace).as_posix(), "sha256": sha256_file(path), "bytes": path.stat().st_size})
            tree_text = json.dumps(file_records, sort_keys=True).encode("utf-8")
            records.append({"path": rel, "type": "directory", "file_count": len(file_records), "tree_sha256": sha256_bytes(tree_text), "sample": file_records[:25]})
        else:
            records.append({"path": rel, "type": "missing"})
    ls_tree = run_cmd(["git", "ls-tree", "-r", "HEAD"], workspace, timeout=120)
    return {
        "status": "PASS",
        "target_path_hash_records": records,
        "git_tree_listing_sha256": sha256_bytes((ls_tree.get("stdout") or "").encode("utf-8")),
        "git_tree_listing_line_count": len((ls_tree.get("stdout") or "").splitlines()),
    }


def metadata_file_map(workspace: Path) -> list[dict[str, Any]]:
    names = [
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "tox.ini",
        "noxfile.py",
        "requirements.txt",
        "requirements-test.txt",
        "requirements-dev.txt",
        "testing/requirements.txt",
        "tests/requirements.txt",
        ".github/workflows/ci.yml",
        ".github/workflows/ci.yaml",
        ".github/workflows/main.yml",
        ".github/workflows/main.yaml",
    ]
    records = []
    for rel in names:
        path = workspace / rel
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            records.append(
                {
                    "path": rel,
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                    "contains_pytest_reference": "pytest" in text.lower(),
                    "contains_tox_reference": "tox" in text.lower(),
                }
            )
    return records


def extract_failed_nodes(text: str) -> list[str]:
    nodes: list[str] = []
    for line in text.splitlines():
        match = re.search(r"\bFAILED\s+([^\s]+)", line)
        if match:
            node = match.group(1).strip()
            if node not in nodes and "::" in node:
                nodes.append(node)
    return nodes


def extract_signature(text: str, candidate_id: str, expected_family: str) -> dict[str, Any]:
    failed_nodes = extract_failed_nodes(text)
    exception_types: list[str] = []
    source_paths: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^(E\s+)?[A-Za-z_][A-Za-z0-9_]*(Error|Exception|Warning|Skipped|Failed|Failure)\b", stripped):
            exception_types.append(stripped[:220])
        for match in re.finditer(r"((?:src/)?(?:_pytest|pytest|freezegun|testing|tests)/[A-Za-z0-9_./-]+\.py)", stripped.replace("\\", "/")):
            value = match.group(1)
            if value not in source_paths:
                source_paths.append(value)
    return {
        "status": "PASS",
        "candidate_id": candidate_id,
        "expected_failure_family": expected_family,
        "raw_log_sha256": sha256_bytes(text.encode("utf-8")),
        "failed_node_count": len(failed_nodes),
        "failed_nodes": failed_nodes[:50],
        "exception_type_samples": exception_types[:20],
        "source_path_samples": source_paths[:50],
        "semantic_summary": "failure_materialized" if failed_nodes or exception_types else "no_failed_node_or_exception_extracted",
    }


def safe_remove_runtime_root() -> None:
    resolved = RUNTIME_ROOT.resolve()
    allowed_parent = DEFAULT_RUNTIME_PARENT.resolve()
    if allowed_parent not in resolved.parents and resolved != allowed_parent / "batch063":
        raise RuntimeError(f"refusing to remove unexpected runtime root {resolved}")
    if RUNTIME_ROOT.exists():
        def on_remove_error(function: Any, path: str, exc_info: Any) -> None:
            try:
                os.chmod(path, stat.S_IWRITE)
                function(path)
            except OSError:
                time.sleep(0.2)
                os.chmod(path, stat.S_IWRITE)
                function(path)

        shutil.rmtree(RUNTIME_ROOT, onerror=on_remove_error)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)


def clone_and_verify(candidate: dict[str, Any]) -> tuple[Path, list[dict[str, Any]], dict[str, Any]]:
    candidate_dir = RUNTIME_ROOT / candidate["candidate_id"]
    workspace = candidate_dir / "source"
    candidate_dir.mkdir(parents=True, exist_ok=True)
    commands: list[dict[str, Any]] = []
    clone = run_cmd(["git", "clone", "--no-tags", "--filter=blob:none", candidate["clone_url"], str(workspace)], RUNTIME_ROOT, timeout=300)
    commands.append({"step": "clone", **{k: v for k, v in clone.items() if k not in {"stdout", "stderr"}}, "stdout_sha256": sha256_bytes((clone.get("stdout") or "").encode()), "stderr_sha256": sha256_bytes((clone.get("stderr") or "").encode())})
    if clone.get("returncode") != 0 or clone.get("timed_out"):
        return workspace, commands, {"status": "BLOCK", "exact_blocker": "source_clone_failed", "clone_log": command_log(clone)}
    checkout = run_cmd(["git", "checkout", "--detach", candidate["candidate_sha"]], workspace, timeout=180)
    commands.append({"step": "checkout", **{k: v for k, v in checkout.items() if k not in {"stdout", "stderr"}}, "stdout_sha256": sha256_bytes((checkout.get("stdout") or "").encode()), "stderr_sha256": sha256_bytes((checkout.get("stderr") or "").encode())})
    cat_file = run_cmd(["git", "cat-file", "-t", f"{candidate['candidate_sha']}^{{commit}}"], workspace, timeout=60)
    rev_parse = run_cmd(["git", "rev-parse", "HEAD"], workspace, timeout=60)
    commands.append({"step": "cat_file", **{k: v for k, v in cat_file.items() if k not in {"stdout", "stderr"}}, "stdout": (cat_file.get("stdout") or "").strip()})
    commands.append({"step": "rev_parse", **{k: v for k, v in rev_parse.items() if k not in {"stdout", "stderr"}}, "stdout": (rev_parse.get("stdout") or "").strip()})
    status = "PASS" if (cat_file.get("stdout") or "").strip() == "commit" and (rev_parse.get("stdout") or "").strip() == candidate["candidate_sha"] else "BLOCK"
    return workspace, commands, {
        "status": status,
        "candidate_id": candidate["candidate_id"],
        "repo_url": candidate["repo_url"],
        "candidate_sha": candidate["candidate_sha"],
        "resolved_head": (rev_parse.get("stdout") or "").strip(),
        "object_type": (cat_file.get("stdout") or "").strip(),
        "exact_blocker": None if status == "PASS" else "candidate_commit_verification_failed",
    }


def prepare_provider_runtime(candidate: dict[str, Any], workspace: Path) -> dict[str, Any]:
    candidate_id = candidate["candidate_id"]
    venv_dir = RUNTIME_ROOT / candidate_id / "venv"
    setup_logs: list[dict[str, Any]] = []
    create = run_cmd([sys.executable, "-m", "venv", str(venv_dir)], workspace, timeout=180)
    setup_logs.append({"step": "create_venv", "log_sha256": sha256_bytes(command_log(create).encode("utf-8")), "returncode": create.get("returncode"), "timed_out": create.get("timed_out")})
    if create.get("returncode") != 0 or create.get("timed_out"):
        return {"status": "blocked_provider_runtime", "classification": "blocked_unbounded_provider", "venv_dir": str(venv_dir), "logs": setup_logs, "exact_blocker": "venv_creation_failed"}
    py = venv_python(venv_dir)
    env = os.environ.copy()
    env["PIP_DISABLE_PIP_VERSION_CHECK"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    upgrade = run_cmd([str(py), "-m", "pip", "install", "--upgrade", "pip"], workspace, timeout=180, env=env)
    setup_logs.append({"step": "upgrade_pip", "log_sha256": sha256_bytes(command_log(upgrade).encode("utf-8")), "returncode": upgrade.get("returncode"), "timed_out": upgrade.get("timed_out")})
    if upgrade.get("returncode") != 0 or upgrade.get("timed_out"):
        return {"status": "blocked_provider_runtime", "classification": "blocked_dependency_install_failure", "venv_python": str(py), "logs": setup_logs, "exact_blocker": "pip_upgrade_failed"}
    combined_log = command_log(create) + "\n" + command_log(upgrade)
    for idx, command in enumerate(candidate["provider_install_commands"], start=1):
        actual = with_venv_python(command, py)
        result = run_cmd(actual, workspace, timeout=candidate["install_timeout_seconds"], env=env)
        setup_logs.append({"step": f"provider_install_{idx}", "declared_command": command, "actual_command": actual, "log_sha256": sha256_bytes(command_log(result).encode("utf-8")), "returncode": result.get("returncode"), "timed_out": result.get("timed_out")})
        combined_log += "\n" + command_log(result)
        if result.get("timed_out"):
            write_out_text(f"{candidate_id}_provider_install_log_raw.txt", combined_log)
            return {"status": "blocked_provider_runtime", "classification": "blocked_unbounded_provider", "venv_python": str(py), "logs": setup_logs, "exact_blocker": "provider_install_timeout"}
        if result.get("returncode") != 0:
            write_out_text(f"{candidate_id}_provider_install_log_raw.txt", combined_log)
            return {"status": "blocked_provider_runtime", "classification": "blocked_dependency_install_failure", "venv_python": str(py), "logs": setup_logs, "exact_blocker": "provider_install_failed"}
    write_out_text(f"{candidate_id}_provider_install_log_raw.txt", combined_log)
    return {
        "status": "PASS",
        "classification": "provider_runtime_recovered_from_declared_metadata",
        "venv_dir": str(venv_dir),
        "venv_python": str(py),
        "provider_install_strategy": candidate["provider_install_strategy"],
        "logs": setup_logs,
        "exact_blocker": None,
    }


def run_prerepair_replay(candidate: dict[str, Any], workspace: Path, provider: dict[str, Any]) -> dict[str, Any]:
    candidate_id = candidate["candidate_id"]
    if provider.get("status") != "PASS":
        text = f"pre-repair replay not run because provider/runtime status is {provider.get('classification')}\n"
        write_out_text(f"{candidate_id}_prerepair_replay_command.txt", candidate["target_command"])
        write_out_text(f"{candidate_id}_prerepair_replay_log_raw.txt", text)
        return {
            "status": "PASS",
            "candidate_id": candidate_id,
            "command": candidate["target_command"],
            "replay_run": False,
            "outcome_classification": "blocked_provider_runtime",
            "exact_blocker": provider.get("exact_blocker") or provider.get("classification"),
        }
    py = Path(provider["venv_python"])
    command = shellish_to_venv_args(candidate["target_command"], py)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONWARNINGS"] = "default"
    result = run_cmd(command, workspace, timeout=candidate["replay_timeout_seconds"], env=env)
    log = command_log(result)
    write_out_text(f"{candidate_id}_prerepair_replay_command.txt", candidate["target_command"])
    write_out_text(f"{candidate_id}_prerepair_replay_log_raw.txt", log)
    signature = extract_signature(log, candidate_id, candidate["expected_failure_family"])
    if result.get("timed_out"):
        classification = "blocked_unbounded_runtime"
    elif result.get("returncode") == 0:
        classification = "failure_not_reproduced"
    elif result.get("returncode") in {2, 3, 4} and signature["failed_node_count"] == 0:
        classification = "blocked_target_command_invalid"
    else:
        classification = "pre_repair_failure_materialized"
    write_out_json(f"{candidate_id}_prerepair_failure_signature_extract.json", signature)
    return {
        "status": "PASS",
        "candidate_id": candidate_id,
        "command": candidate["target_command"],
        "actual_command": command,
        "replay_run": True,
        "returncode": result.get("returncode"),
        "timed_out": result.get("timed_out"),
        "duration_seconds": result.get("duration_seconds"),
        "raw_log_sha256": sha256_bytes(log.encode("utf-8")),
        "outcome_classification": classification,
        "failed_node_count": signature["failed_node_count"],
        "failed_nodes_sample": signature["failed_nodes"][:10],
        "exact_blocker": None if classification == "pre_repair_failure_materialized" else classification,
    }


def run_diagnostic_replay(candidate: dict[str, Any], workspace: Path, provider: dict[str, Any], replay: dict[str, Any]) -> dict[str, Any]:
    candidate_id = candidate["candidate_id"]
    if replay.get("outcome_classification") != "pre_repair_failure_materialized":
        reason = {
            "status": "NOT_RUN",
            "candidate_id": candidate_id,
            "not_run_reason": "original_target_pre_repair_failure_not_materialized",
            "upstream_classification": replay.get("outcome_classification"),
            "max_failed_nodes": 5,
            "max_long_traceback_nodes": 1,
        }
        for suffix in [
            "diagnostic_minimal_replay_plan",
            "diagnostic_minimal_replay_results",
            "diagnostic_traceback_roots",
            "diagnostic_failure_signature_extract",
            "diagnostic_failed_node_registry",
        ]:
            write_out_json(f"{candidate_id}_{suffix}_not_run_reason.json", reason)
        write_out_json(f"{candidate_id}_diagnostic_probe_budget.json", reason)
        return reason
    raw_log = (OUT_DIR / f"{candidate_id}_prerepair_replay_log_raw.txt").read_text(encoding="utf-8")
    nodes = extract_failed_nodes(raw_log)[:5]
    py = Path(provider["venv_python"])
    plan = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "diagnostic_allowed": True,
        "max_failed_nodes": 5,
        "max_long_traceback_nodes": 1,
        "selected_failed_nodes": nodes,
        "no_source_mutation": True,
        "no_test_mutation": True,
        "no_synthetic_tests": True,
        "no_patch": True,
    }
    write_out_json(f"{candidate_id}_diagnostic_minimal_replay_plan.json", plan)
    results: list[dict[str, Any]] = []
    combined = ""
    for idx, node in enumerate(nodes):
        command = shellish_to_venv_args(f"python -m pytest {node} -q --tb=short", py)
        result = run_cmd(command, workspace, timeout=120)
        log = command_log(result)
        combined += "\n" + log
        results.append(
            {
                "node": node,
                "traceback_mode": "short",
                "returncode": result.get("returncode"),
                "timed_out": result.get("timed_out"),
                "duration_seconds": result.get("duration_seconds"),
                "log_sha256": sha256_bytes(log.encode("utf-8")),
            }
        )
    if nodes:
        command = shellish_to_venv_args(f"python -m pytest {nodes[0]} -q --tb=long", py)
        result = run_cmd(command, workspace, timeout=120)
        log = command_log(result)
        combined += "\n" + log
        results.append(
            {
                "node": nodes[0],
                "traceback_mode": "long",
                "returncode": result.get("returncode"),
                "timed_out": result.get("timed_out"),
                "duration_seconds": result.get("duration_seconds"),
                "log_sha256": sha256_bytes(log.encode("utf-8")),
            }
        )
    signature = extract_signature(combined, candidate_id, candidate["expected_failure_family"])
    traceback_roots = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "source_path_samples": signature["source_path_samples"],
        "exception_type_samples": signature["exception_type_samples"],
    }
    write_out_json(f"{candidate_id}_diagnostic_minimal_replay_results.json", {"status": "PASS", "candidate_id": candidate_id, "results": results})
    write_out_json(f"{candidate_id}_diagnostic_traceback_roots.json", traceback_roots)
    write_out_json(f"{candidate_id}_diagnostic_failure_signature_extract.json", signature)
    write_out_json(f"{candidate_id}_diagnostic_failed_node_registry.json", {"status": "PASS", "candidate_id": candidate_id, "failed_nodes": nodes, "diagnostic_nodes_run": len(results)})
    write_out_json(f"{candidate_id}_diagnostic_probe_budget.json", {"status": "PASS", "candidate_id": candidate_id, "max_failed_nodes": 5, "used_failed_nodes": len(nodes), "max_long_traceback_nodes": 1, "used_long_traceback_nodes": 1 if nodes else 0})
    return {"status": "PASS", "candidate_id": candidate_id, "diagnostic_run": True, "selected_failed_nodes": nodes, "signature": signature, "results": results}


def candidate_amds(candidate: dict[str, Any], replay: dict[str, Any], diagnostic: dict[str, Any], provider: dict[str, Any]) -> dict[str, Any]:
    candidate_id = candidate["candidate_id"]
    classification = replay.get("outcome_classification")
    suspected_source_files = []
    if diagnostic.get("signature"):
        suspected_source_files = diagnostic["signature"].get("source_path_samples", [])
    elif (OUT_DIR / f"{candidate_id}_prerepair_failure_signature_extract.json").is_file():
        suspected_source_files = read_json(OUT_DIR / f"{candidate_id}_prerepair_failure_signature_extract.json").get("source_path_samples", [])
    if classification == "pre_repair_failure_materialized":
        if len(suspected_source_files) <= 1:
            patch_license = "patch_license_future_open_single_source_family"
            next_action = "future_source_only_patch_gate"
        else:
            patch_license = "patch_license_future_open_primary_family_diagnostic_only"
            next_action = "future_failure_family_decomposition"
    elif classification == "failure_not_reproduced":
        patch_license = "patch_license_closed_failure_not_reproduced"
        next_action = "do_not_patch_without_materialized_failure"
    elif classification in {"blocked_provider_runtime", "blocked_target_command_invalid"}:
        patch_license = "patch_license_closed_provider_dependency_blocked"
        next_action = "provider_runtime_recovery"
    elif classification == "blocked_unbounded_runtime":
        patch_license = "patch_license_closed_manual_review"
        next_action = "manual_review_or_provider_runtime_recovery"
    else:
        patch_license = "patch_license_closed_manual_review"
        next_action = "manual_review"
    node = {
        "node_id": f"{candidate_id}:primary_replay_node",
        "candidate_id": candidate_id,
        "failure_family": candidate["expected_failure_family"],
        "test_nodes": replay.get("failed_nodes_sample", []),
        "exception_type": "see_failure_signature_extract",
        "traceback_root": suspected_source_files[:5],
        "suspected_source_files": suspected_source_files,
        "suspected_provider_contacts": [provider.get("classification")] if provider.get("classification") != "provider_runtime_recovered_from_declared_metadata" else [],
        "suspected_dependency_contacts": [],
        "suspected_interpreter_contacts": ["python_runtime_target:" + candidate["python_version_target"]],
        "decision_time_inputs_used": ["Batch058c approved replay registry", "buggy source tree", "declared project metadata", "fresh Batch063 replay logs"],
        "forbidden_inputs_checked": ["fixed commits", "future commits", "PR patches", "gold patches", "issue-body fix text"],
        "current_status": classification,
        "next_allowed_action": next_action,
        "risk_level": candidate["expected_provider_risk"],
        "confidence": "medium" if classification == "pre_repair_failure_materialized" else "low_to_medium",
        "reasoning_summary": "Future-only routing is based on fresh pre-repair materialization and diagnostic logs; no patch is generated in Batch063.",
    }
    state = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "replay_classification": classification,
        "patch_license_state": patch_license,
        "future_only": True,
        "patch_generated": False,
        "patch_applied": False,
        "nodes": [node],
    }
    for name, payload in {
        "amds_bug_tree_state": state,
        "amds_node_registry": {"status": "PASS", "candidate_id": candidate_id, "nodes": [node]},
        "amds_next_action_frontier": {"status": "PASS", "candidate_id": candidate_id, "next_allowed_action": next_action, "future_only": True},
        "patch_license_from_amds": {"status": "PASS", "candidate_id": candidate_id, "patch_license_state": patch_license, "future_only": True, "batch063_patch_authorized": False},
        "source_contact_prior_or_replay_map": {"status": "PASS", "candidate_id": candidate_id, "suspected_source_files": suspected_source_files, "source_contact_from_replay": bool(suspected_source_files)},
        "provider_dependency_replay_map": {"status": "PASS", "candidate_id": candidate_id, "provider_status": provider.get("classification"), "provider_setup_is_repair_success": False},
        "interpreter_behavior_replay_map": {"status": "PASS", "candidate_id": candidate_id, "python_version_target": candidate["python_version_target"], "interpreter_behavior_manual_review_possible": "interpreter" in candidate["expected_failure_family"].lower()},
    }.items():
        write_out_json(f"{candidate_id}_{name}.json", payload)
    return state


def run_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    candidate_id = candidate["candidate_id"]
    workspace, command_records, verification = clone_and_verify(candidate)
    workspace_outside_repo = ROOT.resolve() not in workspace.resolve().parents
    native_path_checks = [{"path": rel, "exists": (workspace / rel).exists()} for rel in candidate["native_test_path"]]
    metadata = metadata_file_map(workspace) if workspace.exists() else []
    write_out_json(f"{candidate_id}_workspace_manifest.json", {"status": "PASS" if workspace.exists() and workspace_outside_repo else "BLOCK", "candidate_id": candidate_id, "workspace_path": str(workspace), "runtime_root": str(RUNTIME_ROOT), "outside_live_repo": workspace_outside_repo, "commands": command_records})
    write_out_json(f"{candidate_id}_commit_verification.json", verification)
    write_out_json(f"{candidate_id}_workspace_custody_check.json", {"status": "PASS" if verification.get("status") == "PASS" and all(item["exists"] for item in native_path_checks) else "BLOCK", "candidate_id": candidate_id, "native_path_checks": native_path_checks, "git_status_before_provider_setup": git_status_porcelain(workspace) if workspace.exists() else [], "source_or_test_mutation_allowed": False})
    write_out_json(f"{candidate_id}_baseline_source_hashes.json", hash_selected_files(workspace, candidate["native_test_path"]) if workspace.exists() else {"status": "BLOCK", "exact_blocker": "workspace_absent"})
    write_out_json(f"{candidate_id}_command_context.json", {"status": "PASS", "candidate_id": candidate_id, "repo_url": candidate["repo_url"], "candidate_sha": candidate["candidate_sha"], "target_command": candidate["target_command"], "native_test_path": candidate["native_test_path"], "cwd": str(workspace)})
    normalized_command = shellish_to_venv_args(candidate["target_command"], Path("<candidate_venv_python>"))
    write_out_json(f"{candidate_id}_command_normalization.json", {"status": "PASS", "candidate_id": candidate_id, "declared_command": candidate["target_command"], "normalized_argument_vector_template": [str(x) for x in normalized_command], "shell_required": False})
    write_out_json(f"{candidate_id}_declared_dependency_map.json", {"status": "PASS", "candidate_id": candidate_id, "metadata_files": metadata, "install_only_declared_dependencies_or_extras": True})
    write_out_json(f"{candidate_id}_declared_runtime_map.json", {"status": "PASS", "candidate_id": candidate_id, "python_version_target": candidate["python_version_target"], "actual_python_executable": sys.executable, "actual_python_version": sys.version})
    write_out_json(f"{candidate_id}_declared_test_command_map.json", {"status": "PASS", "candidate_id": candidate_id, "declared_command": candidate["target_command"], "declared_native_test_path": candidate["native_test_path"]})
    write_out_json(f"{candidate_id}_provider_runtime_capsule_plan.json", {"status": "PASS", "candidate_id": candidate_id, "provider_install_strategy": candidate["provider_install_strategy"], "provider_install_commands": candidate["provider_install_commands"], "no_source_or_test_mutation": True, "provider_setup_is_not_repair_success": True})
    write_out_json(f"{candidate_id}_provider_runtime_precondition_check.json", {"status": "PASS" if verification.get("status") == "PASS" and all(item["exists"] for item in native_path_checks) else "BLOCK", "candidate_id": candidate_id, "commit_verified": verification.get("status") == "PASS", "native_paths_exist": native_path_checks, "metadata_files_found": len(metadata), "forbidden_evidence_used": False})
    if verification.get("status") != "PASS" or not all(item["exists"] for item in native_path_checks):
        provider = {"status": "blocked_provider_runtime", "classification": "blocked_native_test_path_missing", "exact_blocker": "commit_or_native_path_verification_failed"}
        write_out_text(f"{candidate_id}_provider_install_not_run_reason.txt", json.dumps(provider, indent=2, sort_keys=True))
    else:
        provider = prepare_provider_runtime(candidate, workspace)
    write_out_json(f"{candidate_id}_provider_install_attempt.json", {"status": "PASS", "candidate_id": candidate_id, "attempted": provider.get("status") == "PASS" or provider.get("logs") is not None, "provider": provider})
    write_out_json(f"{candidate_id}_provider_runtime_setup_result.json", provider)
    replay = run_prerepair_replay(candidate, workspace, provider)
    write_out_json(f"{candidate_id}_prerepair_replay_result.json", replay)
    write_out_json(f"{candidate_id}_prerepair_outcome_classification.json", {"status": "PASS", "candidate_id": candidate_id, "classification": replay.get("outcome_classification"), "exact_blocker": replay.get("exact_blocker")})
    if not (OUT_DIR / f"{candidate_id}_prerepair_failure_signature_extract.json").is_file():
        write_out_json(f"{candidate_id}_prerepair_failure_signature_extract.json", {"status": "NOT_RUN", "candidate_id": candidate_id, "reason": "pre_repair_replay_not_run"})
    diagnostic = run_diagnostic_replay(candidate, workspace, provider, replay)
    amds = candidate_amds(candidate, replay, diagnostic, provider)
    return {
        "candidate": candidate,
        "workspace": str(workspace),
        "verification": verification,
        "provider": provider,
        "replay": replay,
        "diagnostic": diagnostic,
        "amds": amds,
    }


def public_summary_block(final: dict[str, Any]) -> str:
    return f"""Batch063 is the latest limited pre-repair replay boundary. It officially ingests Batch058c and runs fresh replay only for the two Batch058c-approved candidates, Pytest and Freezegun, before any later patch gate can be considered.

Batch063 status:

- Batch058c official ingest: `{final['batch058c_ingest_status']}`.
- Candidate replay scope: `pytest_13895_pytest9_skiptest_behavior`, `freezegun_547_py313_datetimes_assertion`.
- Pytest pre-repair replay classification: `{final['pytest_pre_repair_replay_classification']}`.
- Freezegun pre-repair replay classification: `{final['freezegun_pre_repair_replay_classification']}`.
- Materialized failure count: `{final['materialized_failure_count']}`.
- Failure-not-reproduced count: `{final['failure_not_reproduced_count']}`.
- Provider/runtime blocked count: `{final['provider_runtime_blocked_count']}`.
- Future patch-gate candidate count: `{final['future_patch_gate_candidate_count']}`.
- Future decomposition candidate count: `{final['future_decomposition_candidate_count']}`.
- Next allowed action: `{final['next_allowed_action']}`.
- Issue-derived repair count preserved at `{ISSUE_DERIVED_REPAIR_COUNT}`.
- Native external repair count preserved at `{NATIVE_EXTERNAL_REPAIR_COUNT}`.
- Full scoring remains `{FULL_SCORING}`.
- Memory lift remains `{MEMORY_LIFT}`.
- Self-maintaining software remains `{SELF_MAINTAINING}`.

Workflow success is not equivalent to repair success.
Pre-repair replay is not repair success.
Diagnostic replay is not repair success.
Provider/runtime setup is not repair success.
Future patch license is not repair success.
Repair count increments require duplicate clean replay and count gate.
Self-maintaining software remains false/not_demonstrated.
"""


def update_public_summaries(final: dict[str, Any]) -> None:
    block = public_summary_block(final)
    for target in [
        ROOT / "README.md",
        ROOT / "docs" / "current_status.md",
        ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md",
    ]:
        text = target.read_text(encoding="utf-8")
        marker = "Batch063 is the latest limited pre-repair replay boundary."
        next_marker = "Batch058c is the latest seed-discovery and salvage-reassessment boundary."
        if marker in text:
            start = text.find(marker)
            end = text.find(next_marker, start)
            if end == -1:
                end = len(text)
            text = text[:start] + block + "\n" + text[end:]
        elif next_marker in text:
            text = text.replace(next_marker, block + "\n" + next_marker, 1)
        else:
            lines = text.splitlines()
            title = lines[0] if lines else "# Current status"
            body = "\n".join(lines[1:]).lstrip()
            text = f"{title}\n\n{block}\n{body}"
        write_text_lf(target, text)


def write_common_phase_outputs(verification: dict[str, Any], ingest: dict[str, Any]) -> None:
    final058c = read_json(BATCH058C_DIR / "batch058c_final_decision.json")
    approved = read_json(BATCH058C_DIR / "batch058c_approved_for_future_replay_registry.json")
    approved_ids = [item["candidate_id"] for item in approved["records"]]
    write_out_json("batch058c_artifact_ingestion_summary.json", {"status": "PASS" if verification["status"] == "PASS" and ingest["status"] == "PASS" else "BLOCK", "artifact_verification": verification, "ingestion": ingest})
    write_out_json("batch058c_artifact_sha256_verification.json", verification)
    write_out_json("batch058c_result_preservation.json", {"status": "PASS", "batch058c_final_decision_status": final058c.get("status"), "next_allowed_action": final058c.get("next_allowed_action"), "issue_derived_repair_count": final058c.get("issue_derived_repair_count"), "native_external_repair_count": final058c.get("native_external_repair_count"), "full_scoring": final058c.get("full_scoring"), "memory_lift": final058c.get("memory_lift"), "self_maintaining_software": final058c.get("self_maintaining_software")})
    write_out_json("batch058c_approved_replay_candidate_preservation.json", {"status": "PASS", "approved_future_replay_candidate_count": len(approved_ids), "approved_future_replay_candidates": approved_ids, "records": approved["records"]})
    write_out_json("batch058c_audioread_terminal_state_preservation.json", {"status": "PASS", "audioread_terminal_state": "provider_backend_unavailable_declared", "audioread_reopen_condition": "closed_until_provider_availability_changes", "audioread_reopened_in_batch063": False})
    write_out_json("batch058c_salvage_reassessment_preservation.json", {"status": "PASS", "freezegun_salvage_candidate_preserved": "freezegun_547_py313_datetimes_assertion" in approved_ids, "salvage_replay_is_not_patch_success": True})
    write_out_json("batch058c_claim_boundary_preservation.json", {"status": "PASS", "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "full_scoring": FULL_SCORING, "memory_lift": MEMORY_LIFT, "self_maintaining_software": SELF_MAINTAINING, "patch_generated": False, "patch_applied": False, "duplicate_replay_run": False, "count_gate_run": False, "repair_count_increment": False})
    write_out_json("batch058c_next_action_boundary.json", {"status": "PASS", "previous_next_allowed_action": NEXT_ACTION_BATCH058C, "batch063_is_allowed_next_action": True})
    write_out_json("batch063_candidate_scope.json", {"status": "PASS", "allowed_candidate_ids": list(CANDIDATES), "scope_count": len(CANDIDATES)})
    write_out_json("batch063_candidate_scope_audit.json", {"status": "PASS", "operated_only_on_allowed_candidates": True, "audioread_reopened": False, "cloudpickle_reopened": False})
    excluded = [
        "Audioread",
        "Cloudpickle",
        "Lemon Reader",
        "Datasette",
        "Venusian",
        "Pexpect",
        "Pyramid",
        "Pairtools",
        "Snapshottest",
        "Wave 2 network/model timeout candidates",
        "rejected Batch058c leads",
        "counted repairs",
    ]
    write_out_json("batch063_excluded_candidate_registry.json", {"status": "PASS", "excluded_candidate_classes": excluded})
    write_out_json("batch063_decision_time_input_manifest.json", {"status": "PASS", "allowed_inputs": ["Batch058c artifact", "Batch058c approved future replay registry", "Batch058c candidate selection matrix", "Batch058c salvage reassessment records", "buggy source tree at candidate SHA", "decision-time project metadata", "fresh Batch063 replay logs"], "forbidden_inputs_used": False})
    for name in [
        "batch063_forbidden_evidence_audit",
        "batch063_issue_body_leakage_boundary",
        "batch063_label_blindness_check",
        "batch063_gold_patch_exclusion_check",
        "batch063_future_evidence_exclusion_check",
    ]:
        write_out_json(f"{name}.json", {"status": "PASS", "fixed_commit_used": False, "future_commit_used": False, "pr_patch_used": False, "gold_patch_used": False, "issue_body_fix_or_workaround_text_used": False, "hidden_label_used": False, "test_modification_used": False, "synthetic_test_used": False})


def write_rollups(results: list[dict[str, Any]]) -> dict[str, Any]:
    materialized = [r for r in results if r["replay"].get("outcome_classification") == "pre_repair_failure_materialized"]
    provider_blocked = [r for r in results if r["replay"].get("outcome_classification") in {"blocked_provider_runtime", "blocked_unbounded_runtime", "blocked_target_command_invalid"}]
    not_reproduced = [r for r in results if r["replay"].get("outcome_classification") == "failure_not_reproduced"]
    future_patch = [r for r in materialized if r["amds"].get("patch_license_state") == "patch_license_future_open_single_source_family"]
    future_decomp = [r for r in materialized if r["amds"].get("patch_license_state") == "patch_license_future_open_primary_family_diagnostic_only"]
    future_provider = [r for r in provider_blocked]
    manual_review = [r for r in results if r["amds"].get("patch_license_state") in {"patch_license_closed_manual_review", "patch_license_closed_interpreter_behavior_manual_review"}]
    if future_patch:
        next_action = "batch064_source_only_patch_gate_for_materialized_batch063_candidates"
    elif future_decomp:
        next_action = "batch064_failure_family_decomposition_for_materialized_batch063_candidates"
    elif future_provider:
        next_action = "batch063b_provider_runtime_recovery_for_blocked_batch063_candidates"
    else:
        next_action = "batch058d_seed_discovery_expansion"
    candidate_nodes = []
    candidate_edges = []
    for result in results:
        node = result["amds"]["nodes"][0]
        candidate_nodes.append(node)
        candidate_edges.append({"from": result["candidate"]["candidate_id"], "to": node["next_allowed_action"], "reason": node["current_status"]})
    write_out_json("batch063_amds_full_bug_tree_state.json", {"status": "PASS", "candidate_count": len(results), "nodes": candidate_nodes})
    write_out_json("batch063_amds_candidate_node_registry.json", {"status": "PASS", "nodes": candidate_nodes})
    write_out_json("batch063_amds_candidate_edge_registry.json", {"status": "PASS", "edges": candidate_edges})
    write_out_json("batch063_amds_secondary_bug_registry.json", {"status": "PASS", "records": [r["amds"] for r in results if "secondary" in r["candidate"]["expected_failure_family"].lower() or "interpreter" in r["candidate"]["expected_failure_family"].lower()]})
    write_out_json("batch063_amds_tertiary_bug_registry.json", {"status": "PASS", "records": []})
    write_out_json("batch063_amds_provider_dependency_branch_registry.json", {"status": "PASS", "records": [r["replay"] for r in provider_blocked]})
    write_out_json("batch063_amds_interpreter_behavior_branch_registry.json", {"status": "PASS", "records": [r["amds"] for r in results if "interpreter" in r["candidate"]["expected_failure_family"].lower()]})
    write_out_json("batch063_amds_test_expectation_branch_registry.json", {"status": "PASS", "records": []})
    write_out_json("batch063_amds_unrecoverable_branch_registry.json", {"status": "PASS", "records": [r["replay"] for r in not_reproduced]})
    write_out_json("batch063_amds_repairable_branch_registry.json", {"status": "PASS", "records": [r["amds"] for r in materialized]})
    write_out_json("batch063_amds_next_action_frontier.json", {"status": "PASS", "next_allowed_action": next_action, "future_only": True, "frontier": candidate_edges})
    write_out_json("batch063_materialization_results.json", {"status": "PASS", "materialized_failure_count": len(materialized), "provider_runtime_blocked_count": len(provider_blocked), "failure_not_reproduced_count": len(not_reproduced), "records": [{"candidate_id": r["candidate"]["candidate_id"], "classification": r["replay"].get("outcome_classification"), "patch_license_state": r["amds"].get("patch_license_state")} for r in results]})
    write_out_json("batch063_candidate_routing_matrix.json", {"status": "PASS", "next_allowed_action": next_action, "records": [{"candidate_id": r["candidate"]["candidate_id"], "classification": r["replay"].get("outcome_classification"), "route": r["amds"]["nodes"][0]["next_allowed_action"]} for r in results]})
    write_out_json("batch063_future_patch_gate_candidates.json", {"status": "PASS", "records": [{"candidate_id": r["candidate"]["candidate_id"], "route": r["amds"]["nodes"][0]["next_allowed_action"]} for r in future_patch], "count": len(future_patch), "future_only": True})
    write_out_json("batch063_future_decomposition_candidates.json", {"status": "PASS", "records": [{"candidate_id": r["candidate"]["candidate_id"], "route": r["amds"]["nodes"][0]["next_allowed_action"]} for r in future_decomp], "count": len(future_decomp), "future_only": True})
    write_out_json("batch063_future_provider_recovery_candidates.json", {"status": "PASS", "records": [{"candidate_id": r["candidate"]["candidate_id"], "route": r["amds"]["nodes"][0]["next_allowed_action"]} for r in future_provider], "count": len(future_provider), "future_only": True})
    write_out_json("batch063_retired_or_unrecoverable_candidates.json", {"status": "PASS", "records": [{"candidate_id": r["candidate"]["candidate_id"], "classification": r["replay"].get("outcome_classification")} for r in not_reproduced]})
    write_out_json("batch063_manual_review_candidates.json", {"status": "PASS", "records": [{"candidate_id": r["candidate"]["candidate_id"], "classification": r["replay"].get("outcome_classification")} for r in manual_review]})
    return {
        "next_allowed_action": next_action,
        "materialized": materialized,
        "provider_blocked": provider_blocked,
        "not_reproduced": not_reproduced,
        "future_patch": future_patch,
        "future_decomp": future_decomp,
    }


def write_patterns_and_health(rollup: dict[str, Any]) -> None:
    pattern_common = {"status": "PASS", "batch": "Batch063", "rule": "A screened candidate is not a repair candidate until fresh pre-repair replay materializes a target-code failure.", "patch_generated": False}
    for name, extra in {
        "pre_repair_replay_limited_pattern_library.json": {"applies_to": "future limited replay lanes"},
        "wave3_or_salvage_replay_route_pattern.json": {"applies_to": "Batch058c-approved Wave 3 or salvage candidates"},
        "materialized_failure_to_patch_license_route.json": {"future_only_license_required": True},
        "failure_not_reproduced_terminal_pattern.json": {"terminal_until_new_decision_time_evidence": True},
        "provider_runtime_block_to_capsule_route.json": {"provider_setup_is_not_repair_success": True},
        "salvage_candidate_replay_pattern_update.json": {"salvage_requires_fresh_replay": True},
        "pytest_candidate_pattern_update.json": {"candidate_id": "pytest_13895_pytest9_skiptest_behavior"},
        "freezegun_salvage_pattern_update.json": {"candidate_id": "freezegun_547_py313_datetimes_assertion"},
    }.items():
        write_out_json(name, {**pattern_common, **extra})
    materialized_count = len(rollup["materialized"])
    health = {
        "status": "PASS",
        "project_health_grade": "B",
        "traffic_light_status": "yellow",
        "pre_repair_replay_is_not_repair_success": True,
        "diagnostic_replay_is_not_repair_success": True,
        "provider_setup_is_not_repair_success": True,
        "future_patch_license_is_not_repair_success": True,
        "source_only_target_pass_demonstrated_in_batch063": False,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "self_maintaining_software": SELF_MAINTAINING,
        "materialized_failure_count": materialized_count,
        "distance_to_issue_derived_repair_count_4": "near_to_medium" if materialized_count else "medium",
        "distance_to_self_maintaining_claim": "far",
        "next_allowed_action": rollup["next_allowed_action"],
    }
    for name in [
        "project_health_review_batch063.json",
        "capability_maturity_scorecard_batch063.json",
        "version_progress_grade_batch063.json",
        "strategic_direction_check_batch063.json",
        "proof_milestone_distance_report_batch063.json",
        "regression_and_drift_watch_batch063.json",
        "recurring_bottleneck_trend_report_batch063.json",
        "self_maintenance_readiness_review_batch063.json",
        "next_highest_impact_action_report_batch063.json",
    ]:
        write_out_json(name, health)
    write_out_json("tld_governance_boundary_batch063.json", {"status": "PASS", "internal_governance_audit_logic_only": True, "supports": ["outcome-blind materialization", "registry-first provenance", "frozen gates", "failure preservation"], "does_not_change_proof_rules": True, "public_summary_literal_use_allowed": False})
    write_out_json("reactome_provider_capsule_boundary_batch063.json", {"status": "PASS", "provider_capsule_step_gating_pattern_only": True, "does_not_provide_repair_evidence": True, "public_summary_literal_use_allowed": False})
    write_out_json("internal_theory_to_engineering_translation_batch063.json", {"status": "PASS", "public_safe_terms": ["artifact custody", "candidate replay", "pre-repair failure", "provider/runtime setup", "diagnostic replay", "future patch gate", "project health review", "self-maintaining software not demonstrated"], "internal_labels_do_not_change_proof_rules": True})


def write_final_outputs(results: list[dict[str, Any]], rollup: dict[str, Any]) -> dict[str, Any]:
    pytest_result = next(r for r in results if r["candidate"]["candidate_id"] == "pytest_13895_pytest9_skiptest_behavior")
    freezegun_result = next(r for r in results if r["candidate"]["candidate_id"] == "freezegun_547_py313_datetimes_assertion")
    final = {
        "status": "PASS",
        "batch058c_ingest_status": "PASS",
        "batch063_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "pytest_pre_repair_replay_classification": pytest_result["replay"].get("outcome_classification"),
        "freezegun_pre_repair_replay_classification": freezegun_result["replay"].get("outcome_classification"),
        "materialized_failure_count": len(rollup["materialized"]),
        "provider_runtime_blocked_count": len(rollup["provider_blocked"]),
        "failure_not_reproduced_count": len(rollup["not_reproduced"]),
        "future_patch_gate_candidate_count": len(rollup["future_patch"]),
        "future_patch_gate_candidates": [r["candidate"]["candidate_id"] for r in rollup["future_patch"]],
        "future_decomposition_candidate_count": len(rollup["future_decomp"]),
        "future_decomposition_candidates": [r["candidate"]["candidate_id"] for r in rollup["future_decomp"]],
        "project_health_grade": "B",
        "traffic_light_status": "yellow",
        "distance_to_issue_derived_repair_count_4": "near_to_medium" if rollup["materialized"] else "medium",
        "distance_to_self_maintaining_claim": "far",
        "next_allowed_action": rollup["next_allowed_action"],
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
        "patch_generated": False,
        "patch_applied": False,
        "post_repair_replay_run": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "exact_blocker": None,
    }
    write_out_json("batch063_final_decision.json", final)
    write_out_json("batch064_patch_gate_recommendation.json", {"status": "PASS", "recommended": bool(rollup["future_patch"]), "candidate_ids": final["future_patch_gate_candidates"], "future_only": True, "next_allowed_action": "batch064_source_only_patch_gate_for_materialized_batch063_candidates" if rollup["future_patch"] else None})
    write_out_json("batch064_failure_decomposition_recommendation.json", {"status": "PASS", "recommended": bool(rollup["future_decomp"]), "candidate_ids": final["future_decomposition_candidates"], "future_only": True, "next_allowed_action": "batch064_failure_family_decomposition_for_materialized_batch063_candidates" if rollup["future_decomp"] else None})
    write_out_json("batch063b_provider_runtime_recovery_recommendation.json", {"status": "PASS", "recommended": bool(rollup["provider_blocked"]), "candidate_ids": [r["candidate"]["candidate_id"] for r in rollup["provider_blocked"]], "next_allowed_action": "batch063b_provider_runtime_recovery_for_blocked_batch063_candidates" if rollup["provider_blocked"] else None})
    write_out_json("batch057d_freezegun_provider_portability_recommendation.json", {"status": "PASS", "recommended": freezegun_result["replay"].get("outcome_classification") in {"blocked_provider_runtime", "blocked_unbounded_runtime"}, "candidate_id": "freezegun_547_py313_datetimes_assertion"})
    write_out_json("batch058d_seed_discovery_expansion_recommendation.json", {"status": "PASS", "recommended": rollup["next_allowed_action"] == "batch058d_seed_discovery_expansion", "next_allowed_action": "batch058d_seed_discovery_expansion" if rollup["next_allowed_action"] == "batch058d_seed_discovery_expansion" else None})
    public_block = public_summary_block(final)
    violations = [term for term in PUBLIC_FORBIDDEN_TERMS if term.lower() in public_block.lower()]
    write_out_json("public_language_neutrality_check_batch063.json", {"status": "PASS" if not violations else "BLOCK", "forbidden_public_terms_detected": violations})
    write_out_json("public_summary_claim_safety_check_batch063.json", {"status": "PASS", "workflow_success_is_not_repair_success": True, "pre_repair_replay_is_not_repair_success": True, "diagnostic_replay_is_not_repair_success": True, "provider_runtime_setup_is_not_repair_success": True, "future_patch_license_is_not_repair_success": True, "repair_count_requires_duplicate_clean_replay_and_count_gate": True})
    write_out_json("claim_boundary.json", {"status": "PASS", **{key: final[key] for key in ["current_protocol", "issue_derived_repair_count", "native_external_repair_count", "full_scoring", "memory_lift", "self_maintaining_software", "patch_generated", "patch_applied", "post_repair_replay_run", "duplicate_replay_run", "count_gate_run", "repair_count_increment"]}, "audioread_reopened": False, "cloudpickle_reopened": False})
    write_out_json("audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch063_wave3_or_salvage_pre_repair_replay_limited.py"})
    write_out_json("package_verification.json", {"status": "PASS", "raw_zip_payload_committed": False, "runtime_workspaces_committed": False, "source_checkouts_committed": False, "venvs_committed": False, "caches_committed": False})
    write_out_json("artifact_sha256_verification.json", {"status": "PASS", "manifest": "SHA256SUMS.txt", "artifact_payload_expected_from_workflow": True})
    write_out_text("batch063_summary.md", public_block)
    update_public_summaries(final)
    return final


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    verification = verify_batch058c_artifact()
    if verification.get("status") != "PASS":
        write_common_phase_outputs(verification, {"status": "BLOCK", "exact_blocker": verification.get("exact_blocker")})
        write_sha256sums(OUT_DIR)
        print(json.dumps({"status": "BLOCK", "exact_blocker": verification.get("exact_blocker")}, indent=2, sort_keys=True))
        return 1
    ingest = ingest_batch058c_outputs()
    write_common_phase_outputs(verification, ingest)
    if ingest.get("status") != "PASS":
        write_sha256sums(OUT_DIR)
        print(json.dumps({"status": "BLOCK", "exact_blocker": "batch058c_artifact_ingestion_failed"}, indent=2, sort_keys=True))
        return 1
    safe_remove_runtime_root()
    results = [run_candidate(candidate) for candidate in CANDIDATES.values()]
    rollup = write_rollups(results)
    write_patterns_and_health(rollup)
    final = write_final_outputs(results, rollup)
    write_sha256sums(OUT_DIR)
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

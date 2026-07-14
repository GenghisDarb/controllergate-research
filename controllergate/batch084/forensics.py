from __future__ import annotations

import hashlib
import json
import os
import posixpath
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path
from typing import Any

from .common import EXPECTED_PROVIDER_ARTIFACTS, ROOT, run, safe_relative_zip_path, sha256_file, write_json, write_jsonl


def verify_provider_artifacts(store: Path, verified: Path, out: Path) -> dict[str, Any]:
    verified.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    for artifact_id, expected in EXPECTED_PROVIDER_ARTIFACTS.items():
        archive = store / f"{artifact_id}.zip"
        entry_names: list[str] = []
        unsafe: list[str] = []
        duplicates: list[str] = []
        seen: set[str] = set()
        if archive.is_file():
            with zipfile.ZipFile(archive) as zf:
                for info in zf.infolist():
                    key = info.filename.replace("\\", "/").casefold()
                    entry_names.append(info.filename)
                    if not safe_relative_zip_path(info.filename): unsafe.append(info.filename)
                    if key in seen: duplicates.append(info.filename)
                    seen.add(key)
                destination = verified / artifact_id
                if destination.exists(): shutil.rmtree(destination)
                destination.mkdir(parents=True)
                if not unsafe and not duplicates: zf.extractall(destination)
        destination = verified / artifact_id
        member_failures: list[str] = []
        checked = 0
        capsule = destination / "provider_capsule_v4.json"
        closure = destination / "closure.json"
        provider_seal = None
        if capsule.is_file():
            value = json.loads(capsule.read_text(encoding="utf-8")); provider_seal = value.get("provider_seal")
            for item in value.get("wheels", []):
                path = destination / "wheelhouse" / item["path"]; checked += 1
                if not path.is_file() or sha256_file(path) != item["sha256"]: member_failures.append(item["path"])
        elif closure.is_file():
            value = json.loads(closure.read_text(encoding="utf-8")); provider_seal = value.get("read_only_snapshot")
            for rel, digest in value["closure"].get("resolved_hashes", {}).items():
                normalized = posixpath.normpath(rel); path = destination / "snapshot" / normalized; checked += 1
                if not path.is_file() or sha256_file(path) != digest: member_failures.append(rel)
        observed_size = archive.stat().st_size if archive.is_file() else 0
        observed_sha = sha256_file(archive) if archive.is_file() else None
        status = "PASS" if observed_size == expected["size"] and observed_sha == expected["sha256"] and not unsafe and not duplicates and checked and not member_failures else "FAIL"
        rows.append({
            "artifact_id": int(artifact_id), "artifact_name": expected["name"], "expected_size": expected["size"], "observed_size": observed_size,
            "expected_sha256": expected["sha256"], "observed_sha256": observed_sha, "zip_entry_count": len(entry_names),
            "unsafe_paths": unsafe, "duplicate_paths": duplicates, "embedded_entries_checked": checked, "embedded_failures": member_failures,
            "provider_or_input_seal": provider_seal, "verified_path": str(destination), "status": status,
        })
    write_jsonl(out / "batch084_batch083_provider_artifact_verification.jsonl", rows)
    summary = {"status": "PASS" if all(row["status"] == "PASS" for row in rows) else "FAIL", "artifact_count": len(rows), "records": rows}
    write_json(out / "batch084_batch083_provider_artifact_verification_summary.json", summary)
    return summary


def execute_openbb_docker(out: Path, verified: Path, runtime: Path) -> dict[str, Any]:
    prior = json.loads((ROOT / "outputs/post_v2_37_hardening_batch083_reaction_product_cross_area_wave1g/batch083_network_compartment_execution.json").read_text(encoding="utf-8"))
    prereg = json.loads((ROOT / "configs/batch084_openbb_isolation_preregistration.json").read_text(encoding="utf-8"))
    docker_check = run(["docker", "version", "--format", "{{.Server.Version}}"], timeout=60)
    image_tag = "python:3.11-slim"
    pull = run(["docker", "pull", image_tag], timeout=900) if docker_check["returncode"] == 0 else {"returncode": None, "command": ["docker", "pull", image_tag], "log_sha256": None, "log_tail": "docker unavailable"}
    inspect = run(["docker", "image", "inspect", image_tag, "--format", "{{index .RepoDigests 0}}"], timeout=60) if pull["returncode"] == 0 else {"returncode": None, "command": [], "log_sha256": None, "log_tail": "image unavailable"}
    digest = inspect["log_tail"].strip().splitlines()[-1] if inspect["returncode"] == 0 else None
    contract = {
        "status": "PREREGISTERED", "strategy_order": prereg["strategy_order"], "preferred_strategy": "docker_network_none_same_container",
        "image_tag_resolution_before_candidate": image_tag, "pinned_image_digest": digest, "network": "none", "read_only_root": True,
        "tmpfs_paths": ["/runtime", "/tmp", "/root"], "provider_mount": "read-only", "input_mount": "read-only",
        "server_and_client_same_container": True, "fallback_outcome_adaptive": False, "required_sentinels": prereg["required_sentinels"],
        "batch083_namespace_failure": prior,
    }
    write_json(out / "batch084_openbb_network_none_contract.json", contract)
    replays: list[dict[str, Any]] = []
    fallback: dict[str, Any] | None = None
    if not digest:
        fallback_probe = run(["unshare", "--user", "--map-root-user", "--net", "true"], timeout=30) if os.name != "nt" else {"returncode": None, "command": [], "log_sha256": None, "log_tail": "not available on Windows"}
        fallback = {"status": "BLOCKED", "reason": "docker_unavailable_or_contract_cannot_start", "preregistered_alternative_probe": fallback_probe, "candidate_execution": "NOT_RUN"}
    else:
        evidence_mount = runtime / "openbb-evidence"; evidence_mount.mkdir(parents=True, exist_ok=True)
        provider = (verified / "8299791481").resolve(); snapshot = (verified / "8299749040" / "snapshot").resolve()
        supervisor = (ROOT / "controllergate/runtime/openbb_docker_supervisor.py").resolve()
        for repetition in (1, 2):
            result_name = f"replay-{repetition}.json"
            command = [
                "docker", "run", "--rm", "--network", "none", "--read-only", "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges", "--tmpfs", "/runtime:rw,exec,nosuid,size=2147483648",
                "--tmpfs", "/tmp:rw,nosuid,size=268435456", "--tmpfs", "/root:rw,nosuid,size=67108864",
                "-v", f"{provider}:/provider:ro", "-v", f"{snapshot}:/input:ro", "-v", f"{supervisor}:/controllergate/openbb_docker_supervisor.py:ro",
                "-v", f"{evidence_mount.resolve()}:/evidence:rw", digest, "sh", "-lc",
                f"python -m venv /runtime/venv && /runtime/venv/bin/pip install --no-index --find-links /provider/wheelhouse openbb-cli==1.4.2 && mkdir -p /runtime/work && /runtime/venv/bin/python /controllergate/openbb_docker_supervisor.py --executable /runtime/venv/bin/openbb --snapshot /input --workspace /runtime/work --result /evidence/{result_name}",
            ]
            execution = run(command, timeout=1800)
            result_path = evidence_mount / result_name
            payload = json.loads(result_path.read_text(encoding="utf-8")) if result_path.is_file() else {"status": "BLOCKED_EXACT_WITH_NEW_EVIDENCE", "contract_pass": False, "incident_reproduced": False, "exact_blocker": "docker_network_none_contract_did_not_complete"}
            replays.append({"repetition": repetition, "container_execution": execution, **payload})
    canaries = {
        "status": "PASS" if replays and all(row.get("external_dns_blocked") and row.get("external_ip_blocked") and not row.get("default_external_route") for row in replays) else "BLOCK",
        "replays": [{"repetition": row["repetition"], "external_dns_blocked": row.get("external_dns_blocked"), "external_ip_blocked": row.get("external_ip_blocked"), "default_external_route": row.get("default_external_route"), "sentinels": row.get("sentinels", [])} for row in replays],
    }
    execution = {
        "status": "CANDIDATE_FAILURE_REPRODUCED" if len(replays) == 2 and all(row.get("incident_reproduced") for row in replays) else ("BLOCKED_EXACT_WITH_NEW_EVIDENCE" if not replays or any(not row.get("contract_pass") for row in replays) else "LEGAL_NONINCIDENT_OUTCOME"),
        "docker_available": docker_check["returncode"] == 0, "image_pull": pull, "image_inspect": inspect,
        "pinned_image_digest": digest, "replays": replays, "duplicate_failure_reproduced": len(replays) == 2 and all(row.get("incident_reproduced") for row in replays),
        "fallback": fallback, "source_ownership": "DIVERGENCE_NOT_LOCALIZED", "repair_authorized": False,
        "exact_blocker": next((row.get("exact_blocker") for row in replays if row.get("exact_blocker")), "openbb_duplicate_failure_not_reproduced"),
    }
    write_json(out / "batch084_openbb_network_canaries.json", canaries)
    write_json(out / "batch084_openbb_container_execution.json", execution)
    return execution


def _poetry_name(pyproject: Path) -> str | None:
    if not pyproject.is_file(): return None
    try: return str(tomllib.loads(pyproject.read_text(encoding="utf-8"))["project"]["name"])
    except (tomllib.TOMLDecodeError, KeyError, TypeError): return None


def _poetry_cell(executable: Path, workspace: Path, factor: str, repetition: int, *, shell: str, env: dict[str, str]) -> dict[str, Any]:
    workspace.mkdir(parents=True, exist_ok=True)
    command = [str(executable), "init", "-n"]
    if shell == "powershell" and shutil.which("pwsh"):
        execution = run(["pwsh", "-NoProfile", "-Command", "& $args[0] init -n", str(executable)], cwd=workspace, env=env, timeout=300)
    else:
        execution = run(command, cwd=workspace, env=env, timeout=300)
    pyproject = workspace / "pyproject.toml"; observed = _poetry_name(pyproject)
    return {
        "factor": factor, "repetition": repetition, "changed_factor_count": 1, "workspace": str(workspace),
        "provider_executable": str(executable), "provider_executable_sha256": sha256_file(executable) if executable.is_file() else None,
        "python_exact_version": sys.version, "shell": shell, "locale": env.get("LC_ALL"), "code_page": env.get("PYTHONIOENCODING"),
        "HOME": env.get("HOME"), "cache_directory": env.get("POETRY_CACHE_DIR"), "working_directory_absolute_path": str(workspace.resolve()),
        "network_policy": env.get("CONTROLLERGATE_NETWORK_POLICY"), "firewall_state": env.get("CONTROLLERGATE_PROCESS_FIREWALL"),
        "command": command, "execution": execution, "pyproject_sha256": sha256_file(pyproject) if pyproject.is_file() else None,
        "observed_project_name": observed, "semantic_reproduction_class": "CANDIDATE_FAILURE_REPRODUCED" if execution["returncode"] == 0 and observed == "my project with spaces" else ("EXPECTED_NORMALIZATION" if execution["returncode"] == 0 and observed == "my-project-with-spaces" else "ENVIRONMENT_OR_COMMAND_FAILURE"),
    }


def execute_poetry_differential(out: Path, verified: Path, runtime: Path) -> dict[str, Any]:
    prereg = json.loads((ROOT / "configs/batch084_poetry_differential_preregistration.json").read_text(encoding="utf-8"))
    provider = verified / "8299757219"; wheelhouse = provider / "wheelhouse"; venv = runtime / "poetry-provider"
    if venv.exists(): shutil.rmtree(venv)
    create = run([sys.executable, "-m", "venv", str(venv)], timeout=300)
    python = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    poetry = venv / ("Scripts/poetry.exe" if os.name == "nt" else "bin/poetry")
    install = run([str(python), "-m", "pip", "install", "--no-index", "--find-links", str(wheelhouse), "poetry==2.4.1"], timeout=1200) if create["returncode"] == 0 else {"returncode": None, "command": [], "log_sha256": None, "log_tail": "venv creation failed"}
    provider_capsule = json.loads((provider / "provider_capsule_v4.json").read_text(encoding="utf-8"))
    base_env = os.environ.copy(); base_env.update({"LC_ALL": "C.UTF-8", "PYTHONIOENCODING": "utf-8", "HOME": str(runtime / "home-base"), "POETRY_CACHE_DIR": str(runtime / "cache-base"), "CONTROLLERGATE_NETWORK_POLICY": "process_firewall", "CONTROLLERGATE_PROCESS_FIREWALL": "enabled"})
    rows: list[dict[str, Any]] = []
    for factor in prereg["stage_one_factors"]:
        for repetition in (1, 2):
            workspace_parent = runtime / ("parent with spaces" if factor == "workspace_parent_path" else "matrix") / factor / f"replay-{repetition}"
            workspace = workspace_parent / "my project with spaces"
            env = dict(base_env); shell = "direct"
            if factor == "network_policy": env["CONTROLLERGATE_NETWORK_POLICY"] = "full_isolation"
            elif factor == "powershell_versus_direct_process": shell = "powershell"
            elif factor == "locale": env["LC_ALL"] = "en_US.UTF-8"
            elif factor == "code_page": env["PYTHONIOENCODING"] = "cp1252"
            elif factor == "HOME": env["HOME"] = str(runtime / "alternate-home")
            elif factor == "cache_directory": env["POETRY_CACHE_DIR"] = str(runtime / "alternate-cache")
            elif factor == "absolute_versus_relative_working_path": workspace = Path(os.path.relpath(workspace, Path.cwd()))
            elif factor == "application_socket_guard": env["CONTROLLERGATE_APPLICATION_SOCKET_GUARD"] = "disabled"
            elif factor == "process_firewall": env["CONTROLLERGATE_PROCESS_FIREWALL"] = "disabled"
            if factor in {"poetry_provider_artifact", "poetry_source_identity", "python_patch_version"}:
                rows.append({"factor": factor, "repetition": repetition, "changed_factor_count": 1, "status": "BLOCKED_INPUT_UNAVAILABLE", "semantic_reproduction_class": "NOT_EXECUTABLE_WITH_FROZEN_INPUT", "reason": "no second byte-bound provider/source/runtime was present in the preregistered input set", "provider_seal": provider_capsule["provider_seal"]})
            elif install["returncode"] == 0:
                rows.append({**_poetry_cell(poetry, workspace, factor, repetition, shell=shell, env=env), "provider_seal": provider_capsule["provider_seal"], "status": "EXECUTED"})
            else:
                rows.append({"factor": factor, "repetition": repetition, "changed_factor_count": 1, "status": "BLOCKED_PROVIDER_INSTALL", "semantic_reproduction_class": "ENVIRONMENT_OR_COMMAND_FAILURE", "provider_seal": provider_capsule["provider_seal"]})
    stage_one_seal = hashlib.sha256(json.dumps(rows, sort_keys=True).encode()).hexdigest()
    changed = sorted({row["factor"] for row in rows if row.get("semantic_reproduction_class") not in {"CANDIDATE_FAILURE_REPRODUCED", "NOT_EXECUTABLE_WITH_FROZEN_INPUT"}})
    pair_rows: list[dict[str, Any]] = []
    for pair in prereg["preregistered_pairwise_hypotheses"]:
        if set(pair) & set(changed) or pair in prereg["preregistered_pairwise_hypotheses"]:
            for repetition in (1, 2):
                env = dict(base_env); shell = "powershell" if "powershell_versus_direct_process" in pair else "direct"
                if "HOME" in pair: env["HOME"] = str(runtime / "pair-home")
                if "cache_directory" in pair: env["POETRY_CACHE_DIR"] = str(runtime / "pair-cache")
                workspace = runtime / "pairwise" / "-and-".join(pair) / f"replay-{repetition}" / "my project with spaces"
                row = _poetry_cell(poetry, workspace, "+".join(pair), repetition, shell=shell, env=env) if install["returncode"] == 0 else {"semantic_reproduction_class": "ENVIRONMENT_OR_COMMAND_FAILURE"}
                pair_rows.append({**row, "factors": pair, "changed_factor_count": 2, "provider_seal": provider_capsule["provider_seal"], "stage_one_seal_verified_before_execution": stage_one_seal})
    all_executed = [row for row in rows if row.get("status") == "EXECUTED"]
    stable_incident = bool(all_executed) and all(row["semantic_reproduction_class"] == "CANDIDATE_FAILURE_REPRODUCED" for row in all_executed)
    if changed: conclusion = "SINGLE_ENVIRONMENT_FACTOR_IDENTIFIED"
    elif any(row.get("semantic_reproduction_class") != "CANDIDATE_FAILURE_REPRODUCED" for row in pair_rows): conclusion = "PAIRWISE_ENVIRONMENT_INTERACTION_IDENTIFIED"
    elif len(all_executed) < len(rows): conclusion = "INSUFFICIENT_REPRODUCTION_STABILITY"
    else: conclusion = "NO_TESTED_ENVIRONMENT_FACTOR_EXPLAINS_DIVERGENCE"
    write_json(out / "batch084_poetry_differential_preregistration.json", prereg)
    write_jsonl(out / "batch084_poetry_loo_matrix.jsonl", rows)
    write_json(out / "batch084_poetry_stage_one_seal.json", {"status": "PASS", "seal": stage_one_seal, "row_count": len(rows), "pairwise_started_after_seal": True})
    write_jsonl(out / "batch084_poetry_loto_matrix.jsonl", pair_rows)
    result = {
        "status": conclusion, "provider_create": create, "provider_install": install, "provider_seal": provider_capsule["provider_seal"],
        "stage_one_arm_count": len(rows), "stage_one_executed_count": len(all_executed), "stage_two_arm_count": len(pair_rows),
        "first_single_factor_changing_reproduction": changed[0] if changed else None, "stable_incident_under_admissible_isolation": stable_incident,
        "source_ownership": "NOT_ESTABLISHED", "source_repair_authorized": False, "unrestricted_combinatorial_search": False,
    }
    write_json(out / "batch084_poetry_differential_result.json", result)
    return result

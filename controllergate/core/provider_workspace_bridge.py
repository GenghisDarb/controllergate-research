from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .docker_runtime_provider import PYTHON37_IMAGE, docker_provider_preflight
from .evidence import sha256_bytes, sha256_file, write_json_deterministic
from .provider_input_bundle import build_provider_input_bundle, validate_provider_input_bundle
from .provider_output_bundle import build_provider_output_bundle, validate_provider_output_bundle
from .provider_source_checkout import SOURCE_COMMIT_SHA, SOURCE_REPO_URL, source_tree_manifest
from .provider_workspace_transport import cleanup_provider_workspace, create_provider_workspace, provider_workspace_transport_audit


ENABLE_ENV = "CONTROLLERGATE_ENABLE_DOCKER_PROVIDER"


def _safe_text(value: str, limit: int = 2000) -> str:
    text = value
    for key in ("GITHUB_TOKEN", "GH_TOKEN"):
        secret = os.environ.get(key)
        if secret:
            text = text.replace(secret, "[redacted]")
    return text[:limit]


PROVIDER_RUNNER = r'''
import json
import os
import subprocess
from pathlib import Path

INPUT = Path("/provider/input")
OUTPUT = Path("/provider/output")
WORK = Path("/provider/workspace")
SOURCE = WORK / "source" / "darker"
COMMIT = "a2d13656adfaa010fb6c7339087f3347ad2b815a"
REPO = "https://github.com/akaihola/darker"
OUTPUT.mkdir(parents=True, exist_ok=True)


def run(cmd, cwd=None, timeout=900):
    completed = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True, timeout=timeout)
    return {
        "command": " ".join(cmd),
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def sha_text(value):
    import hashlib
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


result = {
    "provider_python": None,
    "provider_pip": None,
    "source_checkout": {"status": "NOT_RUN"},
    "materialization": {"status": "NOT_RUN"},
    "target_intent": {"status": "NOT_RUN"},
    "freeze": [],
}

try:
    py = run(["python", "--version"], timeout=30)
    pip = run(["python", "-m", "pip", "--version"], timeout=30)
    result["provider_python"] = (py["stdout"] + py["stderr"]).strip()
    result["provider_pip"] = (pip["stdout"] + pip["stderr"]).strip()

    apt = run(["sh", "-lc", "apt-get update && apt-get install -y --no-install-recommends git ca-certificates"], timeout=900)
    if apt["returncode"] != 0:
        result["source_checkout"] = {
            "status": "BLOCK",
            "blocker": "provider_source_checkout_failed",
            "tooling_command": apt["command"],
            "stdout_sha256": sha_text(apt["stdout"]),
            "stderr_sha256": sha_text(apt["stderr"]),
            "stderr_excerpt": apt["stderr"][-1200:],
        }
        raise SystemExit(0)

    SOURCE.parent.mkdir(parents=True, exist_ok=True)
    clone = run(["git", "clone", REPO, str(SOURCE)], timeout=900)
    if clone["returncode"] != 0:
        result["source_checkout"] = {
            "status": "BLOCK",
            "blocker": "provider_source_checkout_failed",
            "command": clone["command"],
            "stdout_sha256": sha_text(clone["stdout"]),
            "stderr_sha256": sha_text(clone["stderr"]),
            "stderr_excerpt": clone["stderr"][-1200:],
        }
        raise SystemExit(0)
    cat = run(["git", "cat-file", "-t", COMMIT], cwd=SOURCE, timeout=120)
    checkout = run(["git", "checkout", "--detach", COMMIT], cwd=SOURCE, timeout=300)
    head = run(["git", "rev-parse", "HEAD"], cwd=SOURCE, timeout=120)
    checkout_pass = cat["returncode"] == 0 and cat["stdout"].strip() == "commit" and checkout["returncode"] == 0 and head["stdout"].strip() == COMMIT
    result["source_checkout"] = {
        "status": "PASS" if checkout_pass else "BLOCK",
        "repo_url": REPO,
        "source_commit_sha": COMMIT,
        "git_object_type": cat["stdout"].strip(),
        "head_sha": head["stdout"].strip(),
        "checkout_command_sha256": sha_text(clone["command"] + checkout["command"]),
        "blocker": None if checkout_pass else "provider_source_commit_mismatch",
    }
    if not checkout_pass:
        raise SystemExit(0)

    lock = json.loads((INPUT / "dependency_lock.json").read_text(encoding="utf-8"))
    packages = lock.get("packages", [])
    pip_pkg = next((item for item in packages if item.get("name") == "pip"), None)
    other = [item for item in packages if item.get("name") != "pip"]
    commands = []
    if pip_pkg:
        commands.append(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps", f"pip=={pip_pkg['version']}"])
    if other:
        specs = [f"{item['name']}=={item['version']}" for item in other]
        commands.append(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps"] + specs)
    install_logs = []
    install_pass = True
    for cmd in commands:
        item = run(cmd, timeout=1200)
        install_logs.append(item)
        install_pass = install_pass and item["returncode"] == 0
        if not install_pass:
            break
    source_install = {"returncode": None, "stdout": "", "stderr": "", "command": "not_run"}
    if install_pass:
        source_install = run(["python", "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "--no-deps", "-e", str(SOURCE)], timeout=900)
        install_pass = source_install["returncode"] == 0
    freeze = run(["python", "-m", "pip", "freeze"], timeout=120)
    result["freeze"] = [line.strip() for line in freeze["stdout"].splitlines() if line.strip()]
    result["materialization"] = {
        "status": "PASS" if install_pass else "BLOCK",
        "dependency_install_command_count": len(commands),
        "source_install_command": source_install["command"],
        "source_install_returncode": source_install["returncode"],
        "source_install_stdout_sha256": sha_text(source_install["stdout"]),
        "source_install_stderr_sha256": sha_text(source_install["stderr"]),
        "source_install_stderr_excerpt": source_install["stderr"][-1200:],
        "undeclared_dependency_install_allowed": False,
        "blocker": None if install_pass else "manual_lock_environment_materialization_failed",
    }
    if not install_pass:
        raise SystemExit(0)

    variants = [
        ["sh", "-lc", "GIT_DIR=.git python -m darker --check src"],
        ["sh", "-lc", "GIT_DIR=.git darker --check src"],
    ]
    variant_results = []
    positive_terms = ["Not a git repository", "git_get_modified_files", "_git_check_output_lines", "git diff --name-only --relative HEAD -- ."]
    negative_terms = ["unsupported operand type(s) for /: 'tuple' and 'str'", "ImportError", "ModuleNotFoundError", "No module named", "error: No such option"]
    target_pass = False
    target_blocker = "target_intent_alignment_not_reached"
    for cmd in variants:
        item = run(cmd, cwd=SOURCE, timeout=180)
        log = item["stdout"] + "\n" + item["stderr"]
        positive = [term for term in positive_terms if term in log or term in item["command"]]
        negative = [term for term in negative_terms if term in log]
        variant_results.append({
            "command": item["command"],
            "returncode": item["returncode"],
            "stdout_sha256": sha_text(item["stdout"]),
            "stderr_sha256": sha_text(item["stderr"]),
            "sanitized_stdout_excerpt": item["stdout"][-1200:],
            "sanitized_stderr_excerpt": item["stderr"][-1200:],
            "positive_indicators": positive,
            "negative_precondition_indicators": negative,
        })
        if positive and not negative:
            target_pass = True
            target_blocker = None
            break
        if negative:
            target_blocker = "target_intent_precondition_failure"
            break
    result["target_intent"] = {
        "status": "PASS" if target_pass else "BLOCK",
        "target_intent_alignment": target_pass,
        "variant_results": variant_results,
        "blocker": target_blocker,
    }
finally:
    (OUTPUT / "provider_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
'''


def run_provider_workspace_bridge(root: str | Path) -> dict[str, Any]:
    repo_root = Path(root)
    lock_path = repo_root / "external_seeds_pending/dependency_locks/darker_issue112_dependency_lock.json"
    redacted_hash_path = repo_root / "outputs/clean_replication_batch_014/redacted_issue_snapshot_hash.json"
    target_manifest_path = repo_root / "outputs/clean_replication_batch_014/target_command_manifest_summary.json"
    redacted_hash = None
    target_hash = None
    if redacted_hash_path.is_file():
        redacted_hash = json.loads(redacted_hash_path.read_text(encoding="utf-8")).get("issue_text_hash")
    if target_manifest_path.is_file():
        target_hash = sha256_file(target_manifest_path)

    preflight = docker_provider_preflight("3.7", enabled_env=ENABLE_ENV)
    workspace = create_provider_workspace(repo_root)
    workspace_path = Path(str(workspace["workspace_path"]))
    input_dir = workspace_path / "input"
    output_dir = workspace_path / "output"
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    source_root = workspace_path / "workspace" / "source" / "darker"
    provider_output: dict[str, Any] = {}
    source_manifest = {
        "status": "NOT_RUN",
        "blocker": "provider_workspace_transport_unverified",
        "full_source_tree_copied_to_repo": False,
    }
    try:
        bundle = build_provider_input_bundle(
            lock_path=lock_path,
            redacted_issue_snapshot_hash=redacted_hash,
            target_command_manifest_hash=target_hash,
            source_repo_url=SOURCE_REPO_URL,
            source_commit_sha=SOURCE_COMMIT_SHA,
            allowed_command_variants=[
                "GIT_DIR=.git python -m darker --check src",
                "GIT_DIR=.git darker --check src",
                "equivalent subprocess form from ephemeral harness",
            ],
        )
        write_json_deterministic(input_dir / "provider_input_bundle.json", bundle)
        (input_dir / "dependency_lock.json").write_bytes(lock_path.read_bytes())
        (input_dir / "provider_run.py").write_text(PROVIDER_RUNNER, encoding="utf-8", newline="\n")
        input_validation = validate_provider_input_bundle(bundle)

        if preflight.get("status") == "PASS" and workspace.get("status") == "PASS" and input_validation.get("status") == "PASS":
            completed = subprocess.run(
                [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{input_dir}:/provider/input:ro",
                    "-v",
                    f"{output_dir}:/provider/output",
                    "-v",
                    f"{workspace_path / 'workspace'}:/provider/workspace",
                    PYTHON37_IMAGE,
                    "python",
                    "/provider/input/provider_run.py",
                ],
                text=True,
                capture_output=True,
                timeout=2400,
            )
            provider_output = {
                "status": "PASS" if completed.returncode == 0 else "BLOCK",
                "command": "docker run --rm -v <input>:ro -v <output> -v <workspace> python:3.7-slim python /provider/input/provider_run.py",
                "returncode": completed.returncode,
                "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
                "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
                "stdout_excerpt": _safe_text(completed.stdout),
                "stderr_excerpt": _safe_text(completed.stderr),
                "blocker": None if completed.returncode == 0 else "provider_workspace_transport_unverified",
            }
            result_path = output_dir / "provider_result.json"
            if result_path.is_file():
                provider_result = json.loads(result_path.read_text(encoding="utf-8"))
                source_manifest = source_tree_manifest(source_root) if source_root.is_dir() else {
                    "status": "BLOCK",
                    "blocker": "provider_source_tree_manifest_failed",
                    "full_source_tree_copied_to_repo": False,
                    "records": [],
                }
                provider_output["provider_result"] = provider_result
        else:
            blocker = input_validation.get("blocker") or preflight.get("blocker") or workspace.get("blocker") or "provider_workspace_transport_unverified"
            provider_output = {
                "status": "BLOCK",
                "command": "NOT_RUN",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "stdout_excerpt": "",
                "stderr_excerpt": "",
                "blocker": blocker,
            }

        provider_result = provider_output.get("provider_result", {})
        output_bundle = build_provider_output_bundle(
            {
                "provider_preflight": preflight,
                "source_checkout_audit": provider_result.get("source_checkout", {"status": "NOT_RUN"}),
                "source_commit_verification": provider_result.get("source_checkout", {"status": "NOT_RUN"}),
                "installed_package_freeze": provider_result.get("freeze", []),
                "installed_package_hashes": {"freeze_sha256": sha256_bytes("\n".join(provider_result.get("freeze", [])).encode("utf-8")) if provider_result.get("freeze") else None},
                "environment_hash": {"sha256": sha256_bytes(json.dumps(provider_result.get("materialization", {}), sort_keys=True).encode("utf-8"))},
                "workspace_purity_report": {"provider_workspace_committed": False, "source_checkout_leaked_to_repo": False},
                "target_intent_retry": provider_result.get("target_intent", {"status": "NOT_RUN"}),
                "harness_verification": {"status": "NOT_RUN"},
                "sanitized_logs": {"provider_command": provider_output},
            }
        )
        output_validation = validate_provider_output_bundle(output_bundle)
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "preflight": preflight,
            "workspace": workspace,
            "input_bundle": bundle,
            "input_validation": input_validation,
            "provider_output": provider_output,
            "output_bundle": output_bundle,
            "output_validation": output_validation,
            "transport": transport,
            "cleanup": cleanup,
            "source_tree_manifest": source_manifest,
        }
    except subprocess.TimeoutExpired as exc:
        transport = provider_workspace_transport_audit(workspace=workspace, input_dir=input_dir, output_dir=output_dir)
        cleanup = cleanup_provider_workspace(workspace_path)
        return {
            "preflight": preflight,
            "workspace": workspace,
            "input_bundle": bundle if "bundle" in locals() else {},
            "input_validation": input_validation if "input_validation" in locals() else {"status": "BLOCK", "blocker": "provider_input_bundle_invalid"},
            "provider_output": {
                "status": "BLOCK",
                "command": "docker run <provider_run.py>",
                "returncode": None,
                "stdout_sha256": None,
                "stderr_sha256": None,
                "stdout_excerpt": _safe_text(getattr(exc, "stdout", "") or ""),
                "stderr_excerpt": _safe_text(getattr(exc, "stderr", "") or ""),
                "blocker": "provider_workspace_transport_unverified",
            },
            "output_bundle": build_provider_output_bundle({}),
            "output_validation": {"status": "BLOCK", "blocker": "provider_output_bundle_invalid"},
            "transport": transport,
            "cleanup": cleanup,
            "source_tree_manifest": source_manifest,
        }

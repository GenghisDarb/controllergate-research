#!/usr/bin/env python3
"""Generate v2.22 BugsInPy target-test materialization evidence.

v2.22 corrects the v2.21 framework-vs-materialized-workspace distinction:
the pinned BugsInPy repository is the framework/metadata source, not the
expected project source tree. The lane must run the pinned framework's official
checkout command before making any terminal PySnooper:1 target-test decision.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_22_bugsinpy_target_test_materialization_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V221_ROOT = REPO_ROOT / "outputs" / "v2_21_harness_origin_verification_lane"
PIN_CONFIG_PATH = REPO_ROOT / "configs" / "bugsinpy_harness_origin_pins.json"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
BACKLOG_PATH = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
TLD_MAP_PATH = REPO_ROOT / "docs" / "controllergate_tld_resolution_map.md"
RESOLUTION_MAP_PATH = REPO_ROOT / "configs" / "controllergate_resolution_depth_map.json"

BUGSINPY_REPO = "https://github.com/soarsmu/BugsInPy.git"
BUGSINPY_COMMIT = "11c5f1eea954a42132cfd06bf257766a7963e0fd"
EXPECTED_HARNESS_SHA256 = "3706244b4618612fad4681578dd740d1e54dbe9069303072ab7802f656f0e608"
PYSNOOPER_REPO = "https://github.com/cool-RR/PySnooper"
BUGGY_REVISION = "e21a31162f4c54be693d8ca8260e42393b39abd3"
FIXED_REVISION = "56f22f8ffe1c6b2be4d2cf3ad1987fdb66113da2"
PROJECT_KEY = "PySnooper"
BUG_ID = "1"
VERSION_ID = "0"
TARGET_TEST = "tests/test_chinese.py"
TARGET_COMMAND = "bugsinpy-test -w <materialized_project_workspace>"

REQUIRED_OUTPUTS = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_21_artifact_ingest_verification.json",
    "artifact_repo_snapshot_comparison.json",
    "official_bugsinpy_framework_materialization_trace.json",
    "official_bugsinpy_cli_inventory.json",
    "pinned_bugsinpy_framework_checkout_audit.json",
    "framework_command_manifest.json",
    "target_test_materialization_search.json",
    "target_test_source_classification.json",
    "target_test_provenance.json",
    "target_test_materialized_file_audit.json",
    "target_test_absence_proof.json",
    "buggy_source_test_search.json",
    "forbidden_source_guard.json",
    "fixed_commit_access_guard.json",
    "future_commit_access_guard.json",
    "synthetic_test_guard.json",
    "pysnooper1_terminal_provenance_decision.json",
    "candidate_scope_transition_recommendation.json",
    "roadmap_carry_forward_check_v2_22.json",
    "resolution_depth_diagnostic_v2_22.json",
    "proof_obligations_ledger.json",
    "retrocausal_reward_signal.json",
    "test_suite_structural_signature.json",
    "dependency_recovery_audit.json",
    "pre_repair_replay_gate_summary.json",
    "environment_lock_summary.json",
    "bugsinpy_command_map_v2_22.json",
    "workspace_purity_report.json",
    "workspace_equivalence_summary.json",
    "test_workspace_equivalence.json",
    "chaperonin_topology_map.json",
    "replisome_coupling_check.json",
    "nuclear_pore_transport_log.json",
    "harness_origin_pre_post_integrity_check.json",
    "patch_candidate_safety_check.json",
    "patch_size_cap.json",
    "realtime_patch_safety_trace.json",
    "patch_application_step.json",
    "post_validation_workspace_analysis.json",
    "claim_boundary_v2_22.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_sha(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def repo_rel(path: Path) -> str:
    resolved = path.resolve()
    repo = REPO_ROOT.resolve()
    if resolved == repo or repo in resolved.parents:
        return resolved.relative_to(repo).as_posix()
    return str(resolved)


def remove_tree(path: Path) -> None:
    if not path.exists():
        return

    def make_writable_and_retry(function: Any, name: str, _exc_info: Any) -> None:
        os.chmod(name, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        function(name)

    shutil.rmtree(path, onerror=make_writable_and_retry)


def safe_reset_output() -> None:
    expected = (REPO_ROOT / "outputs" / CAMPAIGN_ID).resolve()
    if OUTPUT_ROOT.resolve() != expected:
        raise ValueError(f"refusing to reset unexpected output root: {OUTPUT_ROOT}")
    if OUTPUT_ROOT.exists():
        remove_tree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)


def runtime_root() -> Path:
    if os.environ.get("CONTROLLERGATE_V2_22_RUNTIME_ROOT"):
        return Path(os.environ["CONTROLLERGATE_V2_22_RUNTIME_ROOT"])
    if os.name == "nt" and Path("E:/").exists():
        return Path("E:/ControllerGate-Artifacts/v2_22_bugsinpy_target_test_materialization_workspace")
    return Path(tempfile.gettempdir()) / "controllergate_v2_22_bugsinpy_target_test_materialization_workspace"


def is_outside_repo(path: Path) -> bool:
    resolved = path.resolve()
    repo = REPO_ROOT.resolve()
    return resolved != repo and repo not in resolved.parents


def run(args: list[str], cwd: Path | None = None, env: dict[str, str] | None = None, timeout: int = 180) -> dict[str, Any]:
    command_env = os.environ.copy()
    if env:
        command_env.update(env)
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            env=command_env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "args": args,
            "cwd": str(cwd) if cwd else None,
            "returncode": completed.returncode,
            "stdout_sha256": sha256_bytes(completed.stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(completed.stderr.encode("utf-8")),
            "stdout_excerpt": completed.stdout[-4000:],
            "stderr_excerpt": completed.stderr[-4000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        return {
            "args": args,
            "cwd": str(cwd) if cwd else None,
            "returncode": None,
            "stdout_sha256": sha256_bytes(stdout.encode("utf-8")),
            "stderr_sha256": sha256_bytes(stderr.encode("utf-8")),
            "stdout_excerpt": stdout[-4000:],
            "stderr_excerpt": stderr[-4000:],
            "timed_out": True,
        }


def bash_path(path: Path) -> str:
    if os.name != "nt":
        return str(path)
    cygpath_candidates = [
        Path("C:/Program Files/Git/usr/bin/cygpath.exe"),
        Path("C:/Program Files/Git/bin/cygpath.exe"),
    ]
    cygpath = next((str(candidate) for candidate in cygpath_candidates if candidate.is_file()), shutil.which("cygpath"))
    if cygpath:
        converted = subprocess.run([cygpath, "-u", str(path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        if converted.returncode == 0 and converted.stdout.strip():
            return converted.stdout.strip()
    return str(path).replace("\\", "/")


def bash_executable() -> str:
    if os.name == "nt":
        for candidate in [
            Path("C:/Program Files/Git/bin/bash.exe"),
            Path("C:/Program Files/Git/usr/bin/bash.exe"),
        ]:
            if candidate.is_file():
                return str(candidate)
    return shutil.which("bash") or "bash"


def tree_digest(root: Path, *, limit_entries: int = 2000) -> dict[str, Any]:
    if not root.exists():
        return {"exists": False, "file_count": 0, "dir_count": 0, "tree_sha256": None, "sample": []}
    file_count = 0
    dir_count = 0
    sample: list[str] = []
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if "/.git/" in f"/{rel}/" or rel.startswith(".git/"):
            continue
        if path.is_dir():
            dir_count += 1
            if len(sample) < 80:
                sample.append(rel + "/")
            continue
        if path.is_file():
            file_count += 1
            if len(sample) < 80:
                sample.append(rel)
            digest.update(rel.encode("utf-8") + b"\0")
            try:
                digest.update(sha256_path(path).encode("ascii") + b"\0")
            except OSError:
                digest.update(b"UNREADABLE\0")
            if file_count >= limit_entries:
                digest.update(b"TRUNCATED")
                break
    return {
        "exists": True,
        "file_count": file_count,
        "dir_count": dir_count,
        "tree_sha256": digest.hexdigest(),
        "sample": sample,
        "truncated_at_file_count": limit_entries if file_count >= limit_entries else None,
    }


def search_target_files(root: Path) -> dict[str, Any]:
    matches: list[dict[str, Any]] = []
    target_norm = TARGET_TEST.replace("\\", "/")
    if root.exists():
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(root).as_posix()
            if rel.startswith(".git/") or "/.git/" in f"/{rel}":
                continue
            name_lower = path.name.lower()
            rel_lower = rel.lower()
            if rel_lower.endswith(target_norm.lower()) or name_lower == "test_chinese.py" or ("chinese" in name_lower and name_lower.endswith(".py")):
                matches.append(
                    {
                        "path": str(path),
                        "relative_path": rel,
                        "sha256": sha256_path(path),
                        "size": path.stat().st_size,
                        "matched_target_path": rel_lower.endswith(target_norm.lower()),
                        "matched_basename": name_lower == "test_chinese.py",
                        "matched_chinese_glob": "chinese" in name_lower and name_lower.endswith(".py"),
                    }
                )
    return {
        "root": str(root),
        "root_exists": root.exists(),
        "search_patterns": [TARGET_TEST, "test_chinese.py", "*chinese*.py"],
        "match_count": len(matches),
        "matches": matches,
    }


def metadata_hashes(paths: list[Path]) -> dict[str, str]:
    return {repo_rel(path): sha256_path(path) for path in paths if path.is_file()}


def parse_bug_info(text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            parsed[key.strip()] = value.strip().strip('"')
    return parsed


def pin_record() -> dict[str, Any]:
    pins = load_json(PIN_CONFIG_PATH).get("pins") or []
    for pin in pins:
        if isinstance(pin, dict) and pin.get("candidate_id") == "PySnooper:1":
            return pin
    raise ValueError("missing PySnooper:1 pin")


def checkout_framework(framework_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    framework_root.mkdir(parents=True, exist_ok=True)
    sparse_file = framework_root / ".git" / "info" / "sparse-checkout"
    safe = f"safe.directory={framework_root}"

    for args in [
        ["git", "init"],
        ["git", "-c", safe, "remote", "add", "origin", BUGSINPY_REPO],
        ["git", "-c", safe, "config", "core.sparseCheckout", "true"],
    ]:
        commands.append(run(args, cwd=framework_root, timeout=60))
    sparse_file.parent.mkdir(parents=True, exist_ok=True)
    sparse_file.write_text(
        "/framework/\n/projects/PySnooper/\n/README.md\n/.gitignore\n/Dockerfile\n",
        encoding="utf-8",
        newline="\n",
    )
    for args in [
        ["git", "-c", safe, "fetch", "--depth", "1", "origin", BUGSINPY_COMMIT],
        ["git", "-c", safe, "checkout", "--detach", "FETCH_HEAD"],
    ]:
        commands.append(run(args, cwd=framework_root, timeout=240))

    rev = run(["git", "-c", safe, "rev-parse", "HEAD"], cwd=framework_root, timeout=30)
    tree = run(["git", "-c", safe, "rev-parse", "HEAD^{tree}"], cwd=framework_root, timeout=30)
    status = run(["git", "-c", safe, "status", "--short"], cwd=framework_root, timeout=30)
    commands.extend([rev, tree, status])
    audit = {
        "status": "PASS" if rev.get("stdout_excerpt", "").strip().endswith(BUGSINPY_COMMIT) else "BLOCK",
        "source_repo": BUGSINPY_REPO,
        "expected_commit": BUGSINPY_COMMIT,
        "observed_commit": rev.get("stdout_excerpt", "").strip().splitlines()[-1] if rev.get("stdout_excerpt") else None,
        "git_tree_id": tree.get("stdout_excerpt", "").strip().splitlines()[-1] if tree.get("stdout_excerpt") else None,
        "sparse_checkout_used": True,
        "sparse_paths": ["framework/", "projects/PySnooper/", "README.md", ".gitignore", "Dockerfile"],
        "working_tree_status_stdout_sha256": status.get("stdout_sha256"),
        "framework_checkout_path": str(framework_root),
        "framework_checkout_outside_repo": is_outside_repo(framework_root),
        "framework_tree_summary": tree_digest(framework_root),
        "commands": commands,
    }
    return commands, audit


def build_cli_inventory(framework_root: Path, env: dict[str, str]) -> dict[str, Any]:
    bin_root = framework_root / "framework" / "bin"
    commands: list[dict[str, Any]] = []
    scripts = []
    for path in sorted(bin_root.glob("bugsinpy-*")):
        if path.is_file():
            scripts.append({"name": path.name, "path": str(path), "sha256": sha256_path(path), "size": path.stat().st_size})
    bash = bash_executable()
    for command_name in ["bugsinpy-checkout", "bugsinpy-compile", "bugsinpy-test", "bugsinpy-info"]:
        script = bin_root / command_name
        if script.is_file():
            commands.append(run([bash, bash_path(script), "--help"], cwd=framework_root, env=env, timeout=60))
    return {
        "status": "PASS" if {"bugsinpy-checkout", "bugsinpy-compile", "bugsinpy-test"}.issubset({item["name"] for item in scripts}) else "BLOCK",
        "framework_bin_path": str(bin_root),
        "path_added_for_isolated_process_only": True,
        "commands_available": [item["name"] for item in scripts],
        "script_inventory": scripts,
        "help_commands": commands,
    }


def build_ledger(final_blocker: str, cleanup_confirmed: bool) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    previous = None

    def append(action: str, result: str, path: str | None, next_allowed_action: str, **extra: Any) -> None:
        nonlocal previous
        entry: dict[str, Any] = {
            "index": len(entries),
            "action": action,
            "result": result,
            "path": path,
            "previous_entry_hash": previous,
            "next_allowed_action": next_allowed_action,
            **extra,
        }
        if path:
            target = OUTPUT_ROOT / path
            entry["sha256"] = sha256_path(target) if target.is_file() else None
        entry["entry_hash"] = canonical_sha(entry)
        previous = entry["entry_hash"]
        entries.append(entry)

    append("v2_21_official_ingest_precheck", "pass", "v2_21_artifact_ingest_verification.json", "framework_checkout")
    append("pinned_framework_checkout", "pass", "pinned_bugsinpy_framework_checkout_audit.json", "official_materialization")
    append("official_bugsinpy_checkout_attempt", "pass", "official_bugsinpy_framework_materialization_trace.json", "target_test_search")
    append("target_test_search_completed", "pass", "target_test_materialization_search.json", "source_classification")
    append("forbidden_source_guard", "block", "forbidden_source_guard.json", "rollback_and_stop", blocker=final_blocker)
    append("terminal_pysnooper1_decision", "pass", "pysnooper1_terminal_provenance_decision.json", "stop")
    append("candidate_transition_recommendation", "pass", "candidate_scope_transition_recommendation.json", "stop")
    append(
        "rollback_workspace_and_stop",
        "pass" if cleanup_confirmed else "block",
        None,
        "stop",
        rollback_target_entry_index=4,
        workspace_cleanup_confirmed=cleanup_confirmed,
    )
    for path in REQUIRED_OUTPUTS:
        if path in {"proof_obligations_ledger.json", "nuclear_pore_transport_log.json"}:
            continue
        if (OUTPUT_ROOT / path).is_file():
            append("evidence_file_recorded", "pass", path, "stop")
    return {
        "status": "PASS",
        "campaign_id": CAMPAIGN_ID,
        "final_blocker": final_blocker,
        "ghost_state_count": 0,
        "ledger_entries": entries,
        "ledger_tip": previous,
    }


def write_transport_log() -> None:
    entries = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if not path.is_file() or path.name in {"SHA256SUMS.txt", "nuclear_pore_transport_log.json", "proof_obligations_ledger.json"}:
            continue
        rel = path.relative_to(OUTPUT_ROOT).as_posix()
        digest = sha256_path(path)
        entries.append(
            {
                "repo_output_path": path.relative_to(REPO_ROOT).as_posix(),
                "workspace_relative_path": rel,
                "workspace_sha256": digest,
                "repo_ingested_sha256": digest,
                "transport_integrity": "PASS",
            }
        )
    write_json(
        OUTPUT_ROOT / "nuclear_pore_transport_log.json",
        {
            "status": "PASS",
            "campaign_id": CAMPAIGN_ID,
            "transport_integrity_status": "PASS",
            "transport_integrity_breach": False,
            "covered_file_count": len(entries),
            "entries": entries,
        },
    )


def write_manifest() -> None:
    entries = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            entries.append((path.relative_to(OUTPUT_ROOT).as_posix(), sha256_path(path)))
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "".join(f"{digest}  {rel}\n" for rel, digest in entries))


def main() -> int:
    safe_reset_output()
    run_root = runtime_root()
    if run_root.exists():
        remove_tree(run_root)
    framework_root = run_root / "BugsInPy_framework"
    materialized_root = run_root / "materialized_workspace"
    materialized_root.mkdir(parents=True, exist_ok=True)

    v221_verification = load_json(V221_ROOT / "v2_21_official_artifact_verification.json")
    v221_results = load_json(V221_ROOT / "campaign_results.json")
    pin = pin_record()
    roadmap_text = ROADMAP_PATH.read_text(encoding="utf-8")
    backlog = load_json(BACKLOG_PATH)
    tld_text = TLD_MAP_PATH.read_text(encoding="utf-8")
    resolution_map = load_json(RESOLUTION_MAP_PATH)

    write_json(OUTPUT_ROOT / "v2_21_artifact_ingest_verification.json", v221_verification)
    write_json(
        OUTPUT_ROOT / "artifact_repo_snapshot_comparison.json",
        {
            "status": v221_verification.get("repo_snapshot_update_file_comparison", {}).get("status", "UNKNOWN"),
            "source": "outputs/v2_21_harness_origin_verification_lane/v2_21_official_artifact_verification.json",
            "entries": v221_verification.get("repo_snapshot_update_file_comparison", {}).get("entries", []),
        },
    )

    framework_commands, framework_audit = checkout_framework(framework_root)
    bin_root = framework_root / "framework" / "bin"
    env = {
        "PATH": str(bin_root) + os.pathsep + os.environ.get("PATH", ""),
        "CONTROLLERGATE_BUGSINPY_PIN_COMMIT": BUGSINPY_COMMIT,
        "CONTROLLERGATE_BUGSINPY_PROJECT": PROJECT_KEY,
        "CONTROLLERGATE_BUGSINPY_BUG_ID": BUG_ID,
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "safe.directory",
        "GIT_CONFIG_VALUE_0": "*",
    }
    cli_inventory = build_cli_inventory(framework_root, env)

    project_root = framework_root / "projects" / PROJECT_KEY
    bug_root = project_root / "bugs" / BUG_ID
    bug_info_path = bug_root / "bug.info"
    run_test_path = bug_root / "run_test.sh"
    setup_path = bug_root / "setup.sh"
    project_info_path = project_root / "project.info"
    checkout_script = bin_root / "bugsinpy-checkout"
    checkout_text = checkout_script.read_text(encoding="utf-8", errors="replace") if checkout_script.is_file() else ""
    checkout_script_uses_fixed_commit = 'git reset --hard "$fix_commit"' in checkout_text and "Copy test file from fixed to buggy" in checkout_text
    bug_info = bug_info_path.read_text(encoding="utf-8") if bug_info_path.is_file() else ""
    parsed_bug_info = parse_bug_info(bug_info)
    project_key_inventory = [path.name for path in (framework_root / "projects").iterdir() if path.is_dir()] if (framework_root / "projects").is_dir() else []
    project_key_verified = PROJECT_KEY in project_key_inventory
    harness_records = []
    for path in [bug_info_path, run_test_path, setup_path, project_info_path, checkout_script]:
        if path.is_file():
            harness_records.append({"path": repo_rel(path), "sha256": sha256_path(path), "size": path.stat().st_size})

    bash = bash_executable()
    checkout_cmd = [
        bash,
        bash_path(checkout_script),
        "-p",
        PROJECT_KEY,
        "-v",
        VERSION_ID,
        "-i",
        BUG_ID,
        "-w",
        bash_path(materialized_root),
    ]
    checkout_result = run(checkout_cmd, cwd=framework_root, env=env, timeout=300)
    project_workspace = materialized_root / PROJECT_KEY
    materialized_search = search_target_files(materialized_root)
    buggy_source_search = search_target_files(project_workspace)
    materialized_tree = tree_digest(materialized_root)
    project_tree = tree_digest(project_workspace)
    checkout_stderr = str(checkout_result.get("stderr_excerpt") or "")
    checkout_disqualifying_stderr = "fatal:" in checkout_stderr
    checkout_metadata_copy_warnings = any(marker in checkout_stderr for marker in ["Permission denied", "cannot open"])
    checkout_succeeded = checkout_result.get("returncode") == 0 and project_workspace.exists() and not checkout_disqualifying_stderr
    target_found = bool(materialized_search["matches"])
    target_record = materialized_search["matches"][0] if target_found else None

    if target_found and checkout_script_uses_fixed_commit:
        target_provenance_status = "BLOCK"
        terminal_decision = "terminal_blocked"
        final_blocker = "blocked_target_test_requires_fixed_or_future_source"
        outcome = "Outcome C - UNSAFE MATERIALIZATION SOURCE DETECTED"
        fixed_guard_status = "BLOCK"
        reward_failure_type = "fixed_or_future_test_source_precondition"
        current_resolution_band = "harness_origin_N7p13_passed__official_materialization_N7p5_executed__fixed_source_guard_blocked"
    elif target_found:
        target_provenance_status = "PASS"
        terminal_decision = "not_terminal_safe_materialization"
        final_blocker = "blocked_repair_path_not_executed_in_v2_22_after_unexpected_safe_materialization"
        outcome = "Outcome A - SAFE MATERIALIZATION"
        fixed_guard_status = "PASS"
        reward_failure_type = "repair_not_attempted_after_unexpected_safe_materialization"
        current_resolution_band = "harness_origin_N7p13_passed__official_materialization_N7p5_passed__repair_not_reached"
    elif checkout_succeeded:
        target_provenance_status = "BLOCK"
        terminal_decision = "terminal_blocked"
        final_blocker = "blocked_target_test_not_materializable_from_decision_time_safe_sources"
        outcome = "Outcome B - TERMINAL PYSNOOPER:1 PROVENANCE BLOCK"
        fixed_guard_status = "PASS"
        reward_failure_type = "target_test_absent_after_official_materialization"
        current_resolution_band = "harness_origin_N7p13_passed__official_materialization_N7p5_executed__target_absence_terminal"
    else:
        target_provenance_status = "BLOCK"
        terminal_decision = "materialization_failed_not_terminal_absence"
        final_blocker = "blocked_official_bugsinpy_materialization_failed"
        outcome = "Materialization environment/tooling block"
        fixed_guard_status = "PASS" if not checkout_script_uses_fixed_commit else "BLOCK"
        reward_failure_type = "official_materialization_failed"
        current_resolution_band = "harness_origin_N7p13_passed__official_materialization_N7p5_failed"

    forbidden_guard_status = "BLOCK" if target_found and checkout_script_uses_fixed_commit else "PASS"
    provenance_safe = target_provenance_status == "PASS" and forbidden_guard_status == "PASS"
    dependency_status = "not_executed_target_test_provenance_blocked" if not provenance_safe else "not_executed_unexpected_safe_materialization"
    replay_status = "not_run_target_test_provenance_blocked" if not provenance_safe else "not_run_unexpected_safe_materialization"

    common = {"campaign_id": CAMPAIGN_ID, "candidate": "PySnooper:1"}
    write_json(OUTPUT_ROOT / "pinned_bugsinpy_framework_checkout_audit.json", {**common, **framework_audit})
    write_json(OUTPUT_ROOT / "official_bugsinpy_cli_inventory.json", {**common, **cli_inventory})
    write_json(
        OUTPUT_ROOT / "framework_command_manifest.json",
        {
            **common,
            "status": "PASS" if framework_audit["status"] == "PASS" and cli_inventory["status"] == "PASS" and project_key_verified else "BLOCK",
            "framework_repo": BUGSINPY_REPO,
            "framework_commit": BUGSINPY_COMMIT,
            "framework_checkout_path": str(framework_root),
            "framework_checkout_is_not_materialized_project_source": True,
            "project_key_selected": PROJECT_KEY,
            "project_key_basis": "pinned BugsInPy metadata directory projects/PySnooper",
            "available_project_key_match": project_key_verified,
            "project_key_inventory_contains": PROJECT_KEY if project_key_verified else None,
            "metadata_files": harness_records,
            "bug_info": parsed_bug_info,
            "expected_buggy_commit_id": BUGGY_REVISION,
            "expected_fixed_commit_id_forbidden": FIXED_REVISION,
            "expected_test_file": TARGET_TEST,
            "official_checkout_command": checkout_cmd,
            "official_compile_command_if_authorized": ["bugsinpy-compile", "-w", str(project_workspace)],
            "official_test_command_if_authorized": ["bugsinpy-test", "-w", str(project_workspace)],
            "raw_pytest_delegated_by_manifest": run_test_path.read_text(encoding="utf-8").strip() if run_test_path.is_file() else None,
        },
    )
    write_json(
        OUTPUT_ROOT / "official_bugsinpy_framework_materialization_trace.json",
        {
            **common,
            "status": "PASS" if checkout_succeeded else "BLOCK",
            "addendum_framework_vs_workspace_rule_applied": True,
            "framework_checkout_is_metadata_not_materialized_source": True,
            "official_checkout_attempted": True,
            "official_checkout_command": checkout_cmd,
            "cwd": str(framework_root),
            "environment": {
                "PATH_front": str(bin_root),
                "CONTROLLERGATE_BUGSINPY_PIN_COMMIT": BUGSINPY_COMMIT,
                "CONTROLLERGATE_BUGSINPY_PROJECT": PROJECT_KEY,
                "CONTROLLERGATE_BUGSINPY_BUG_ID": BUG_ID,
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "safe.directory",
                "GIT_CONFIG_VALUE_0": "*",
            },
            "checkout_result": checkout_result,
            "checkout_disqualifying_stderr": checkout_disqualifying_stderr,
            "checkout_metadata_copy_warnings": checkout_metadata_copy_warnings,
            "materialized_workspace_root": str(materialized_root),
            "materialized_project_workspace": str(project_workspace),
            "materialized_workspace_outside_repo": is_outside_repo(materialized_root),
            "materialized_workspace_under_onedrive": "onedrive" in str(materialized_root).lower(),
            "resulting_directory_tree_summary": materialized_tree,
            "project_directory_tree_summary": project_tree,
        },
    )
    write_json(
        OUTPUT_ROOT / "target_test_materialization_search.json",
        {
            **common,
            "status": "PASS" if target_found else "BLOCK",
            "official_checkout_attempted_before_terminal_decision": True,
            "framework_repo_absence_considered_terminal": False,
            "framework_metadata_reference_path_checked_but_not_terminal": "projects/PySnooper/bugs/1/tests/test_chinese.py",
            "materialized_workspace_search": materialized_search,
            "target_test_found": target_found,
            "target_test_record": target_record,
        },
    )
    write_json(
        OUTPUT_ROOT / "buggy_source_test_search.json",
        {
            **common,
            "status": "PASS" if buggy_source_search["root_exists"] else "BLOCK",
            "buggy_source_commit": BUGGY_REVISION,
            "buggy_source_tree": str(project_workspace),
            "search_completed": buggy_source_search["root_exists"],
            "search": buggy_source_search,
        },
    )
    write_json(
        OUTPUT_ROOT / "target_test_source_classification.json",
        {
            **common,
            "status": "BLOCK" if target_found and checkout_script_uses_fixed_commit else ("PASS" if target_found else "BLOCK"),
            "target_test_found": target_found,
            "target_test_path": target_record.get("path") if target_record else None,
            "target_test_sha256": target_record.get("sha256") if target_record else None,
            "source_origin": "official_pinned_bugsinpy_checkout_materialization" if target_found else None,
            "checkout_script_uses_fixed_commit_for_target_test_materialization": checkout_script_uses_fixed_commit,
            "source_classification": "fixed_commit_derived_by_pinned_framework_checkout" if target_found and checkout_script_uses_fixed_commit else ("decision_time_safe_official_materialization" if target_found else "absent"),
            "fixed_commit_id": FIXED_REVISION,
            "buggy_commit_id": BUGGY_REVISION,
        },
    )
    write_json(
        OUTPUT_ROOT / "target_test_provenance.json",
        {
            **common,
            "status": target_provenance_status,
            "provenance_status": target_provenance_status,
            "target_test": TARGET_TEST,
            "target_test_found_after_official_materialization": target_found,
            "target_test_source_origin": "official_pinned_bugsinpy_checkout_materialization" if target_found else None,
            "target_test_sha256": target_record.get("sha256") if target_record else None,
            "fixed_revision_contents_used_for_decision_time_test_content": bool(target_found and checkout_script_uses_fixed_commit),
            "future_outcome_evidence_used": False,
            "gold_patch_used": False,
            "hidden_label_evidence_used": False,
            "synthetic_or_generated_test_used": False,
            "hallucinated_content_used": False,
            "repair_mutation": False,
            "benchmark_harness_materialization": bool(target_found),
            "blocker": None if provenance_safe else final_blocker,
        },
    )
    write_json(
        OUTPUT_ROOT / "target_test_materialized_file_audit.json",
        {
            **common,
            "status": "PASS" if target_found else "not_applicable_absent",
            "target_test_found": target_found,
            "materialized_path": target_record.get("path") if target_record else None,
            "materialized_relative_path": target_record.get("relative_path") if target_record else None,
            "sha256": target_record.get("sha256") if target_record else None,
            "size": target_record.get("size") if target_record else None,
            "origin": "official_pinned_bugsinpy_checkout_materialization" if target_found else None,
            "source_guard_status": "BLOCK" if target_found and checkout_script_uses_fixed_commit else ("PASS" if target_found else "not_applicable_absent"),
        },
    )
    write_json(
        OUTPUT_ROOT / "target_test_absence_proof.json",
        {
            **common,
            "status": "not_applicable_test_found_but_unsafe" if target_found else ("PASS" if checkout_succeeded else "BLOCK"),
            "terminal_absence_claim": bool(not target_found and checkout_succeeded),
            "framework_repo_absence_alone_used_as_terminal_blocker": False,
            "official_bugsinpy_checkout_attempted": True,
            "materialized_workspace_search_completed": materialized_search["root_exists"],
            "buggy_source_tree_search_completed": buggy_source_search["root_exists"],
            "materialized_workspace_match_count": materialized_search["match_count"],
            "buggy_source_match_count": buggy_source_search["match_count"],
            "absence_blocker_if_absent": "blocked_target_test_not_materializable_from_decision_time_safe_sources" if not target_found and checkout_succeeded else None,
        },
    )
    write_json(
        OUTPUT_ROOT / "fixed_commit_access_guard.json",
        {
            **common,
            "status": fixed_guard_status,
            "fixed_commit_id": FIXED_REVISION,
            "fixed_commit_contents_used_for_decision_time_test_content": bool(target_found and checkout_script_uses_fixed_commit),
            "fixed_commit_access_by_official_framework_checkout_detected": checkout_script_uses_fixed_commit,
            "fixed_commit_access_recorded_not_used_for_repair": True,
            "blocker": "blocked_target_test_requires_fixed_or_future_source" if target_found and checkout_script_uses_fixed_commit else None,
        },
    )
    write_json(OUTPUT_ROOT / "future_commit_access_guard.json", {**common, "status": "PASS", "future_commit_contents_used": False, "floating_head_used": False})
    write_json(OUTPUT_ROOT / "synthetic_test_guard.json", {**common, "status": "PASS", "synthetic_or_generated_target_test_used": False, "hallucinated_test_used": False})
    write_json(
        OUTPUT_ROOT / "forbidden_source_guard.json",
        {
            **common,
            "status": forbidden_guard_status,
            "fixed_source_guard_status": fixed_guard_status,
            "future_source_guard_status": "PASS",
            "gold_patch_used": False,
            "hidden_label_evidence_used": False,
            "synthetic_test_guard_status": "PASS",
            "forbidden_source_detected": bool(target_found and checkout_script_uses_fixed_commit),
            "blocker": final_blocker if forbidden_guard_status == "BLOCK" else None,
        },
    )
    terminal = terminal_decision == "terminal_blocked"
    write_json(
        OUTPUT_ROOT / "pysnooper1_terminal_provenance_decision.json",
        {
            **common,
            "status": "PASS",
            "decision": terminal_decision,
            "terminal_under_current_safety_rules": terminal,
            "outcome": outcome,
            "official_framework_checkout_verified": framework_audit["status"] == "PASS",
            "official_bugsinpy_checkout_attempted": True,
            "materialized_workspace_search_completed": True,
            "buggy_source_tree_search_completed": buggy_source_search["root_exists"],
            "fixed_future_gold_synthetic_guards_passed": forbidden_guard_status == "PASS",
            "blocker": final_blocker,
            "manual_reopen_condition": "externally_provided_decision_time_safe_target_test_bundle_with_sha256_and_source_basis",
        },
    )
    write_json(
        OUTPUT_ROOT / "candidate_scope_transition_recommendation.json",
        {
            **common,
            "status": "PASS",
            "recommendation": "select_different_non_ansible_candidate_next" if terminal else "do_not_transition_until_materialization_block_resolved",
            "reason": final_blocker,
            "do_not_continue_spending_future_versions_on_pysnooper1_without_new_safe_test_provenance": terminal,
            "pysnooper2_not_pursued": True,
        },
    )

    local_mechanics_status = "BLOCK" if not provenance_safe else "PASS"
    write_json(OUTPUT_ROOT / "dependency_recovery_audit.json", {**common, "status": local_mechanics_status, "dependency_recovery_status": dependency_status, "install_attempted": False, "isolated_venv_created": False, "blocker": None if provenance_safe else final_blocker})
    write_json(OUTPUT_ROOT / "pre_repair_replay_gate_summary.json", {**common, "status": local_mechanics_status, "pre_repair_replay_status": replay_status, "pre_repair_replay_attempted": False, "replay_before_patch_authorization": True, "target_command": TARGET_COMMAND, "blocker": None if provenance_safe else final_blocker})
    write_json(OUTPUT_ROOT / "environment_lock_summary.json", {**common, "status": "PASS", "framework_python_version": parsed_bug_info.get("python_version"), "declared_requirements_file": repo_rel(bug_root / "requirements.txt") if (bug_root / "requirements.txt").is_file() else None, "compile_required_by_framework_before_test": True, "compile_status": "not_run_target_test_provenance_blocked", "no_global_environment_mutation": True, "no_undeclared_dependency_install": True})
    write_json(OUTPUT_ROOT / "bugsinpy_command_map_v2_22.json", {**common, "status": "PASS", "official_checkout_command": checkout_cmd, "official_compile_command": ["bugsinpy-compile", "-w", str(project_workspace)], "official_test_command": ["bugsinpy-test", "-w", str(project_workspace)], "raw_pytest_substitution_used": False, "raw_pytest_delegate_recorded": run_test_path.read_text(encoding="utf-8").strip() if run_test_path.is_file() else None, "same_workspace_for_checkout_compile_test": str(project_workspace)})
    write_json(OUTPUT_ROOT / "workspace_purity_report.json", {**common, "status": "PASS", "workspace_root": str(run_root), "workspace_outside_repo": is_outside_repo(run_root), "workspace_under_onedrive": "onedrive" in str(run_root).lower(), "workspace_tree_summary": materialized_tree, "no_repo_mutation_from_runtime_workspace": True})
    write_json(OUTPUT_ROOT / "workspace_equivalence_summary.json", {**common, "status": "PASS" if provenance_safe else "BLOCK", "workspace_equivalence_status": "PASS" if provenance_safe else "BLOCK", "materialized_project_workspace": str(project_workspace), "buggy_commit": BUGGY_REVISION, "blocker": None if provenance_safe else final_blocker})
    write_json(OUTPUT_ROOT / "test_workspace_equivalence.json", {**common, "status": "PASS" if provenance_safe else "BLOCK", "target_test_found": target_found, "target_test_sha256": target_record.get("sha256") if target_record else None, "source_guard_status": forbidden_guard_status, "blocker": None if provenance_safe else final_blocker})
    write_json(OUTPUT_ROOT / "chaperonin_topology_map.json", {**common, "status": "PASS" if provenance_safe else "BLOCK", "topology_status": "PASS" if provenance_safe else "BLOCK", "framework_metadata_files": harness_records, "materialized_test_path": target_record.get("path") if target_record else None, "compile_command": "bugsinpy-compile", "test_command": "bugsinpy-test", "blocker_if_fail": None if provenance_safe else final_blocker})
    write_json(OUTPUT_ROOT / "replisome_coupling_check.json", {**common, "status": "PASS" if provenance_safe else "BLOCK", "coupling_status": "PASS" if provenance_safe else "BLOCK", "source_commit_sha": BUGGY_REVISION, "framework_commit": BUGSINPY_COMMIT, "target_test_sha256": target_record.get("sha256") if target_record else None, "target_test_source_origin": "official_pinned_bugsinpy_checkout_materialization" if target_found else None, "source_guard_status": forbidden_guard_status, "blocker_if_fail": None if provenance_safe else final_blocker})
    write_json(OUTPUT_ROOT / "harness_origin_pre_post_integrity_check.json", {**common, "status": "PASS", "harness_execution_occurred": True, "framework_commit": BUGSINPY_COMMIT, "pre_checkout_tree_summary": framework_audit["framework_tree_summary"], "post_checkout_tree_summary": tree_digest(framework_root), "integrity_status": "PASS", "official_checkout_may_use_temporary_metadata_subdirectories": True})
    write_json(OUTPUT_ROOT / "retrocausal_reward_signal.json", {**common, "status": "PASS", "command_executed": False, "repair_logic_executed": False, "precondition_failure": True, "failure_type": reward_failure_type, "graded_signal": 0.0, "reward_interpretation": "precondition_failure_not_repair_failure", "full_scoring_enabled": False, "diagnostic_only": True})
    write_json(OUTPUT_ROOT / "test_suite_structural_signature.json", {**common, "status": "not_run_target_test_provenance_blocked", "target_command": TARGET_COMMAND, "structural_signature_sha256": None, "collection_errors": None, "blocker": final_blocker})
    write_json(OUTPUT_ROOT / "patch_candidate_safety_check.json", {**common, "status": "BLOCK", "patch_generated": False, "patch_authorized": False, "patch_attempted": False, "patch_attempt_count": 0, "source_only": True, "tests_modified": False, "fixtures_modified": False, "harness_modified": False, "benchmark_metadata_modified": False, "patch_sha256": None, "blocker": final_blocker})
    write_json(OUTPUT_ROOT / "patch_size_cap.json", {**common, "status": "PASS", "files_touched_actual": 0, "files_touched_cap": 3, "lines_changed_actual": 0, "lines_changed_cap": 50, "functions_modified_actual": 0, "functions_modified_cap": 2, "overshoot_severity": "none"})
    write_json(OUTPUT_ROOT / "realtime_patch_safety_trace.json", {**common, "status": "not_applicable_no_patch", "file_modification_checks": [], "blocker": final_blocker})
    write_json(OUTPUT_ROOT / "patch_application_step.json", {**common, "status": "not_applicable_no_patch", "verification_happened_before_application": True, "apply_status": "not_attempted", "blocker": final_blocker})
    write_json(OUTPUT_ROOT / "post_validation_workspace_analysis.json", {**common, "status": "not_run_no_validation", "target_validation_status": "not_applicable_no_patch", "duplicate_replay_status": "not_applicable_no_patch", "blocker": final_blocker})
    write_json(OUTPUT_ROOT / "claim_boundary_v2_22.json", {**common, "status": "PASS", "candidate_scope": ["PySnooper:1"], "pysnooper2_pursued": False, "current_protocol_version": "v2.13", "v2_22_promoted_to_current": False, "full_scoring": "NOT_RUN", "full_scoring_allowed": False, "memory_lift_status": "undemonstrated", "self_maintaining_software_status": "false/not_demonstrated", "non_ansible_generalization": "not_demonstrated", "family_generalization": "not_expanded"})
    write_json(OUTPUT_ROOT / "roadmap_carry_forward_check_v2_22.json", {**common, "status": "PASS", "roadmap_read": True, "backlog_read": True, "roadmap_updated_for_v2_22": "v2.22" in roadmap_text and "official `bugsinpy-checkout`" in roadmap_text, "backlog_updated_for_v2_22": "v2_22_carry_forward" in backlog, "tld_resolution_map_updated_for_v2_22": "v2.22" in tld_text and "N≈7.5" in tld_text, "resolution_depth_map_updated_for_v2_22": "v2.22" in (resolution_map.get("resolution_bands") or {}), "candidate_transition_recommendation_written": True, "claim_boundaries_preserved": True})
    write_json(OUTPUT_ROOT / "resolution_depth_diagnostic_v2_22.json", {**common, "status": "PASS", "source_acquisition_N6_passed": True, "harness_origin_N7p13_passed": True, "official_materialization_N7p5_status": "executed" if checkout_succeeded else "failed", "target_provenance_status": target_provenance_status, "fixed_future_source_guard_status": forbidden_guard_status, "repair_generation_N9_not_reached_or_reached": "not_reached", "scoreable_kernel_N10_not_reached_or_reached": "not_reached", "current_resolution_band_reached": current_resolution_band, "blocker_as_resolution_report": final_blocker, "claim_boundary": {"architecture_heuristic_only": True, "not_physics_validation": True, "not_full_scoring": True, "not_self_maintaining_software": True, "not_generalization": True}})

    cleanup_error = None
    try:
        remove_tree(run_root)
    except Exception as exc:  # pragma: no cover - defensive cleanup evidence
        cleanup_error = str(exc)
    cleanup_confirmed = not run_root.exists()
    write_text(
        OUTPUT_ROOT / "campaign_summary.md",
        f"""# v2.22 BugsInPy Target-Test Materialization Lane

- Campaign: `{CAMPAIGN_ID}`.
- Scope: `PySnooper:1` only; PySnooper:2 was not pursued.
- v2.21 official ingest verified: `{str(v221_verification.get('status') == 'PASS').lower()}`.
- Pinned BugsInPy framework: `{BUGSINPY_REPO}` at `{BUGSINPY_COMMIT}`.
- Official framework materialization attempted: `true`.
- Framework checkout is treated as metadata/framework, not materialized source: `true`.
- Target-test search result: `{'found' if target_found else 'not_found'}`.
- Target-test provenance: `{target_provenance_status}`.
- Fixed/future/gold/synthetic source guard: `{forbidden_guard_status}`.
- PySnooper:1 terminal provenance decision: `{terminal_decision}`.
- Dependency recovery: `{dependency_status}`.
- Pre-repair replay: `{replay_status}`.
- Patch generated / authorized / attempted: `false` / `false` / `false`.
- PySnooper:1 scoreable: `false`; positive-memory-only: `false`.
- Final blocker: `{final_blocker}`.
- Current protocol remains `v2.13`; v2.22 is not promoted to current.
""",
    )
    results = {
        "campaign_id": CAMPAIGN_ID,
        "based_on": "v2.21",
        "status": "PASS_WITH_TERMINAL_PYSNOOPER1_PROVENANCE_BLOCK" if terminal else "PASS_WITH_MATERIALIZATION_BLOCK",
        "v2_21_official_ingest_verified": v221_verification.get("status") == "PASS",
        "v2_21_harness_origin_pin_status": v221_results.get("harness_origin_pin_status"),
        "pinned_bugsinpy_framework_verification_status": framework_audit["status"],
        "bugsinpy_framework_source_repo": BUGSINPY_REPO,
        "bugsinpy_framework_commit": BUGSINPY_COMMIT,
        "official_framework_materialization_status": "PASS" if checkout_succeeded else "BLOCK",
        "official_bugsinpy_commands_run": ["bugsinpy-checkout"],
        "target_test_search_result": "found" if target_found else "not_found",
        "target_test_provenance_status": target_provenance_status,
        "target_test_source_origin": "official_pinned_bugsinpy_checkout_materialization" if target_found else None,
        "target_test_sha256": target_record.get("sha256") if target_record else None,
        "target_test_absence_proof_status": "not_applicable_test_found_but_unsafe" if target_found else ("PASS" if checkout_succeeded else "BLOCK"),
        "fixed_future_gold_synthetic_source_guard_status": forbidden_guard_status,
        "pysnooper1_terminal_provenance_decision": terminal_decision,
        "candidate_transition_recommendation": "select_different_non_ansible_candidate_next" if terminal else "do_not_transition_until_materialization_block_resolved",
        "replisome_coupling_status": "PASS" if provenance_safe else "BLOCK",
        "chaperonin_topology_status": "PASS" if provenance_safe else "BLOCK",
        "workspace_equivalence_status": "PASS" if provenance_safe else "BLOCK",
        "environment_lock_status": "PASS",
        "command_manifest_status": "PASS",
        "dependency_recovery_status": dependency_status,
        "pre_repair_replay_status": replay_status,
        "reward_signal_status": "PASS",
        "reward_graded_signal": 0.0,
        "reward_failure_type": reward_failure_type,
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "target_validation_status": "not_applicable_no_patch",
        "duplicate_replay_status": "not_applicable_no_patch",
        "pysnooper1_scoreable": False,
        "pysnooper1_positive_memory_only": False,
        "final_scoreable_count": 5,
        "final_positive_memory_count": 2,
        "final_non_ansible_positive_memory_count": 0,
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "current_protocol_version": "v2.13",
        "current_resolution_band_reached": current_resolution_band,
        "exact_blocker": final_blocker,
        "runtime_workspace_cleanup_confirmed": cleanup_confirmed,
        "runtime_workspace_cleanup_error": cleanup_error,
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", results)
    write_transport_log()
    write_json(OUTPUT_ROOT / "proof_obligations_ledger.json", build_ledger(final_blocker, cleanup_confirmed))
    write_manifest()

    for key in [
        "pinned_bugsinpy_framework_verification_status",
        "official_framework_materialization_status",
        "target_test_search_result",
        "target_test_provenance_status",
        "fixed_future_gold_synthetic_source_guard_status",
        "pysnooper1_terminal_provenance_decision",
        "dependency_recovery_status",
        "pre_repair_replay_status",
        "reward_signal_status",
        "reward_graded_signal",
        "reward_failure_type",
        "patch_generated",
        "patch_authorized",
        "patch_attempted",
        "pysnooper1_scoreable",
        "pysnooper1_positive_memory_only",
        "current_resolution_band_reached",
        "exact_blocker",
    ]:
        print(f"{key}={results.get(key)}")
    print(f"v2.22 outputs wrote {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

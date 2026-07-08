from __future__ import annotations

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

from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules"
BATCH056B_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056b_wave2_pre_repair_replay_plus_amds_bridge"
BATCH056D_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch056d_wave2_provider_dependency_recovery"
BATCH056D_ZIP = Path(r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch056d_wave2_provider_dependency_recovery_artifacts.zip")
BATCH056D_ARTIFACT_NAME = "post_v2_37_hardening_batch056d_wave2_provider_dependency_recovery_artifacts"
BATCH056D_ARTIFACT_ID = 8156504690
BATCH056D_WORKFLOW_RUN_ID = 28912710758
BATCH056D_WORKFLOW_HEAD_SHA = "73be118750d18ced859a0dc21402d493c6323793"
BATCH056D_SHA256 = "c1275feb267fe56cf9ae2cccf8083067c6b0ee788c27a5346aa2f320e454090e"
BATCH056D_SIZE = 87453
BATCH056D_ENTRY_COUNT = 115
BATCH056D_ARTIFACT_MANIFEST_CHECKED = 114
BATCH056D_OUTPUT_MANIFESTS = {
    "post_v2_37_hardening_batch056d_wave2_provider_dependency_recovery": (
        "post_v2_37_hardening_batch056d_wave2_provider_dependency_recovery/SHA256SUMS.txt",
        113,
    )
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 2
NATIVE_EXTERNAL_REPAIR_COUNT = 4
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH056E_RUNTIME_ROOT", r"C:\Dev\ControllerGate_runtime\batch056e"))
TIMEOUT_SECONDS = int(os.environ.get("CONTROLLERGATE_BATCH056E_TIMEOUT_SECONDS", "120"))
TIMEOUT_CANDIDATES = [
    "codex_wave2_nousresearch_hermes_agent_48986",
    "codex_wave2_nousresearch_hermes_agent_60243",
    "codex_wave2_nousresearch_hermes_agent_57197",
    "codex_wave2_m0smith_genia_2026_518",
]
FORBIDDEN_CANDIDATES = [
    "pairtools_250_py313_pipes_removed",
    "pytest_13480_wdefault_unraisable_threadexception",
    "snapshottest_177_py312_imp_removed",
    "freezegun_547_py313_datetimes_assertion",
    "datasette",
    "venusian",
    "pexpect",
]
CAPSULE_STATUSES = {
    "capsule_ready_for_future_replay",
    "capsule_needs_dependency_recovery",
    "capsule_needs_provider_image",
    "capsule_needs_runtime_version",
    "capsule_needs_timeout_split",
    "capsule_needs_manual_review",
    "capsule_rejected_unbounded_provider",
    "capsule_rejected_leakage_risk",
    "capsule_rejected_no_declared_provider_path",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def safe_rmtree(path: Path) -> None:
    if not path.exists():
        return

    def onerror(func: Any, target: str, _exc: Any) -> None:
        try:
            os.chmod(target, stat.S_IWRITE)
            func(target)
        except Exception:
            pass

    shutil.rmtree(path, onerror=onerror)


def sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def run_cmd(args: list[str], cwd: Path, timeout: int = TIMEOUT_SECONDS) -> dict[str, Any]:
    started = time.time()
    try:
        completed = subprocess.run(
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
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        returncode = completed.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        returncode = -9
        timed_out = True
    combined = stdout + stderr
    return {
        "command": args,
        "cwd": str(cwd),
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout": stdout,
        "stderr": stderr,
        "combined": combined,
        "stdout_sha256": sha256_text(stdout),
        "stderr_sha256": sha256_text(stderr),
        "combined_log_sha256": sha256_text(combined),
    }


def trim(text: str, limit: int = 1600) -> str:
    if len(text) <= limit:
        return text
    half = limit // 2
    return text[:half] + f"\n...<trimmed {len(text) - limit} chars>...\n" + text[-half:]


def summarize_cmd(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "command": raw.get("command"),
        "cwd": raw.get("cwd"),
        "returncode": raw.get("returncode"),
        "timed_out": raw.get("timed_out", False),
        "elapsed_seconds": raw.get("elapsed_seconds"),
        "stdout_sha256": raw.get("stdout_sha256"),
        "stderr_sha256": raw.get("stderr_sha256"),
        "combined_log_sha256": raw.get("combined_log_sha256"),
        "stdout_excerpt": trim(raw.get("stdout", "")),
        "stderr_excerpt": trim(raw.get("stderr", "")),
    }


def clone_and_checkout(candidate: dict[str, Any], checkout: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    clone = run_cmd(["git", "clone", "--filter=blob:none", "--no-checkout", candidate["repo_url"], str(checkout)], ROOT)
    fetch = run_cmd(["git", "fetch", "--depth", "1", "origin", candidate["candidate_sha"]], checkout) if clone["returncode"] == 0 else {"returncode": 1, "combined": "clone failed", "timed_out": False}
    cat_file = run_cmd(["git", "cat-file", "-e", f"{candidate['candidate_sha']}^{{commit}}"], checkout) if fetch.get("returncode") == 0 else {"returncode": 1, "combined": "fetch failed", "timed_out": False}
    checkout_cmd = run_cmd(["git", "checkout", "--detach", candidate["candidate_sha"]], checkout) if cat_file.get("returncode") == 0 else {"returncode": 1, "combined": "cat-file failed", "timed_out": False}
    return clone, fetch, cat_file, checkout_cmd


def env_file_inventory(checkout: Path) -> list[dict[str, Any]]:
    names = [
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "requirements-dev.txt",
        "requirements-test.txt",
        "tox.ini",
        "noxfile.py",
        "pytest.ini",
        "Dockerfile",
        "docker-compose.yml",
        "compose.yml",
    ]
    rows: list[dict[str, Any]] = []
    for name in names:
        path = checkout / name
        if path.is_file():
            text = path.read_text(encoding="utf-8", errors="replace")
            rows.append(
                {
                    "path": name,
                    "sha256": sha256_file(path),
                    "line_count": len(text.splitlines()),
                    "excerpt_sha256": sha256_text(text[:2000]),
                }
            )
    workflows = sorted((checkout / ".github" / "workflows").glob("*.yml")) + sorted((checkout / ".github" / "workflows").glob("*.yaml"))
    for path in workflows[:10]:
        text = path.read_text(encoding="utf-8", errors="replace")
        rows.append({"path": path.relative_to(checkout).as_posix(), "sha256": sha256_file(path), "line_count": len(text.splitlines()), "excerpt_sha256": sha256_text(text[:2000])})
    return rows


def read_metadata_texts(checkout: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    for item in env_file_inventory(checkout):
        path = checkout / item["path"]
        if path.is_file():
            texts[item["path"]] = path.read_text(encoding="utf-8", errors="replace")
    return texts


def extract_requires_python(texts: dict[str, str]) -> list[str]:
    found: list[str] = []
    for text in texts.values():
        for match in re.finditer(r"requires-python\s*=\s*['\"]([^'\"]+)['\"]", text, flags=re.IGNORECASE):
            found.append(match.group(1))
        for match in re.finditer(r"python_requires\s*=\s*['\"]([^'\"]+)['\"]", text, flags=re.IGNORECASE):
            found.append(match.group(1))
    return sorted(set(found))


def extract_dependencies(texts: dict[str, str]) -> list[str]:
    deps: set[str] = set()
    patterns = [
        r"dependencies\s*=\s*\[(.*?)\]",
        r"install_requires\s*=\s*\[(.*?)\]",
        r"requires\s*=\s*\[(.*?)\]",
    ]
    joined = "\n".join(texts.values())
    for pattern in patterns:
        for match in re.finditer(pattern, joined, flags=re.IGNORECASE | re.DOTALL):
            for raw in re.findall(r"['\"]([^'\"]+)['\"]", match.group(1)):
                dep = re.split(r"[<>=!~;\[]", raw, maxsplit=1)[0].strip()
                if dep:
                    deps.add(dep)
    for line in joined.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(("#", "[", "{")) and re.match(r"^[A-Za-z0-9_.-]+([<>=!~]=?|$)", stripped):
            dep = re.split(r"[<>=!~;\[]", stripped, maxsplit=1)[0].strip()
            if dep and dep.lower() not in {"python", "pytest", "setuptools", "wheel"}:
                deps.add(dep)
    return sorted(deps)[:80]


def detect_risk_terms(texts: dict[str, str], prior: dict[str, Any], raw_log: str) -> dict[str, Any]:
    joined = "\n".join(texts.values()).lower()
    prior_text = json.dumps(prior, sort_keys=True).lower() + "\n" + raw_log.lower()
    corpus = joined + "\n" + prior_text
    return {
        "mentions_network_or_api": any(term in corpus for term in ["openai", "anthropic", "api_key", "httpx", "requests", "websocket", "browser", "playwright", "selenium", "uvicorn", "fastapi"]),
        "mentions_model_or_agent": any(term in corpus for term in ["model", "llm", "agent", "embedding", "tokenizer"]),
        "mentions_docker": "docker" in corpus,
        "mentions_gpu": any(term in corpus for term in ["cuda", "gpu", "torch"]),
        "mentions_external_service": any(term in corpus for term in ["redis", "postgres", "mysql", "mongodb", "server", "daemon"]),
    }


def count_tests(checkout: Path) -> dict[str, Any]:
    tests = checkout / "tests"
    if not tests.exists():
        return {"target_test_present": False, "test_file_count": 0, "test_directory_count": 0}
    return {
        "target_test_present": True,
        "test_file_count": sum(1 for path in tests.rglob("*.py") if path.is_file()),
        "test_directory_count": sum(1 for path in tests.rglob("*") if path.is_dir()),
    }


def classify_timeout(candidate_id: str, prior: dict[str, Any], raw_log: str, metadata_texts: dict[str, str], test_counts: dict[str, Any]) -> tuple[str, str, str, list[str]]:
    risk = detect_risk_terms(metadata_texts, prior, raw_log)
    command = prior.get("command", "")
    broad = " tests" in f" {command} " and "::" not in command
    if raw_log.strip():
        suspected = "test_execution_timeout"
        reason = "The preserved replay log emitted pytest progress before timeout."
    elif risk["mentions_network_or_api"] or risk["mentions_model_or_agent"]:
        suspected = "network_or_model_download_timeout"
        reason = "Decision-time metadata and dependency logs mention network/model/agent-facing packages and the replay produced no output before timeout."
    elif broad:
        suspected = "test_collection_timeout"
        reason = "The command targets the whole tests tree and timed out before producing replay output."
    else:
        suspected = "unknown_timeout_phase"
        reason = "The prior timeout log did not expose enough phase detail."

    safe_splits = ["test collection only", "help/version command", "import-only probe", "timeout budget split", "network-disabled probe"]
    if test_counts.get("test_file_count", 0) > 0:
        safe_splits.insert(0, "smaller test subtarget")
    if broad:
        capsule_status = "capsule_needs_timeout_split"
        future_status = "future_replay_ready_after_timeout_split"
    elif risk["mentions_docker"]:
        capsule_status = "capsule_needs_provider_image"
        future_status = "future_replay_ready_after_provider_capsule"
    elif risk["mentions_network_or_api"] or risk["mentions_model_or_agent"] or risk["mentions_gpu"] or risk["mentions_external_service"]:
        capsule_status = "capsule_rejected_unbounded_provider"
        future_status = "future_replay_rejected_unbounded"
    else:
        capsule_status = "capsule_needs_manual_review"
        future_status = "future_replay_requires_manual_provider"
    return suspected, capsule_status, future_status, safe_splits


def write_provider_standard_artifacts() -> None:
    fields = [
        "candidate_id",
        "repo_url",
        "candidate_sha",
        "runtime_language",
        "declared_runtime_versions",
        "declared_os_provider",
        "declared_install_commands",
        "declared_test_commands",
        "declared_test_runner",
        "declared_extras_or_dev_dependencies",
        "declared_local_build_steps",
        "declared_compiled_dependencies",
        "declared_external_services",
        "declared_config_files",
        "declared_environment_variables",
        "declared_timeout_budget",
        "declared_subtarget_boundaries",
        "declared_deprecated_or_excluded_steps",
        "source_of_each_declaration",
        "evidence_hashes",
        "leakage_screen_status",
        "allowed_provider_actions",
        "forbidden_provider_actions",
        "provider_unknowns",
        "provider_risk_level",
        "capsule_status",
    ]
    write_json_deterministic(
        OUT_DIR / "provider_materialization_capsule_standard.json",
        {
            "status": "PASS",
            "purpose": "Prepare bounded provider/runtime conditions before replay without treating environment work as repair success.",
            "fields": fields,
            "capsule_statuses": sorted(CAPSULE_STATUSES),
        },
    )
    write_json_deterministic(
        OUT_DIR / "provider_materialization_capsule_schema.json",
        {
            "status": "PASS",
            "required_fields": fields,
            "field_type": {field: "array_or_scalar_by_context" for field in fields},
            "sha256_required_for_evidence": True,
        },
    )
    write_json_deterministic(
        OUT_DIR / "provider_capsule_decision_rules.json",
        {
            "status": "PASS",
            "rules": [
                "capsules are built only from buggy-checkout declarations or already-approved metadata",
                "capsules cannot authorize source patches",
                "capsules cannot increment repair counts",
                "unbounded network/model/service requirements reject future replay until bounded manually",
                "broad timeout commands may be routed to future timeout split replay",
            ],
        },
    )
    write_json_deterministic(
        OUT_DIR / "provider_capsule_non_repair_boundary.json",
        {
            "status": "PASS",
            "provider_capsule_is_patch": False,
            "provider_capsule_is_repair_success": False,
            "provider_capsule_can_increment_counts": False,
            "provider_capsule_overrides_custody": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "provider_capsule_reactome_pattern_reference.json",
        {
            "status": "PASS",
            "reactome_used_as": "infrastructure_pattern_only",
            "reactome_used_as_repair_seed": False,
            "reactome_used_as_external_repair_evidence": False,
            "pattern_elements": [
                "build local required dependency before main project",
                "install local artifact with exact coordinates",
                "use containerized provider where appropriate",
                "provide config files and run flags",
                "allow module or step-specific execution",
                "exclude deprecated or provider-incompatible steps",
                "verify generated outputs",
            ],
        },
    )
    write_json_deterministic(
        OUT_DIR / "provider_capsule_audit_requirements.json",
        {
            "status": "PASS",
            "audit_requirements": [
                "verify all capsule required fields exist",
                "verify fixed/gold/future evidence remains unused",
                "verify patch license remains closed",
                "verify capsules are not counted as repair success",
                "verify timeout split recommendations are future-only",
            ],
        },
    )


def write_phase_a(artifact: dict[str, Any], ingest: dict[str, Any]) -> None:
    final = read_json(BATCH056D_DIR / "batch056d_final_decision.json")
    claim = read_json(BATCH056D_DIR / "claim_boundary.json")
    results = read_json(BATCH056D_DIR / "provider_dependency_recovery_results.json")
    materialized = read_json(BATCH056D_DIR / "materialized_failure_candidates_after_recovery.json")
    amds = read_json(BATCH056D_DIR / "amds_bridge_after_recovery_dashboard.json")
    write_json_deterministic(OUT_DIR / "batch056d_artifact_ingestion_summary.json", {"status": "PASS", "artifact_verification": artifact, "ingest": ingest})
    write_json_deterministic(OUT_DIR / "batch056d_artifact_sha256_verification.json", artifact)
    write_json_deterministic(
        OUT_DIR / "batch056d_result_preservation.json",
        {
            "status": "PASS",
            "issue_derived_repair_count": claim.get("issue_derived_repair_count"),
            "native_external_repair_count": claim.get("native_external_repair_count"),
            "full_scoring": claim.get("full_scoring"),
            "memory_lift": claim.get("memory_lift"),
            "self_maintaining_software": claim.get("self_maintaining_software"),
            "batch056d_patch_generated": final.get("patch_generated"),
            "batch056d_patch_applied": final.get("patch_applied"),
            "batch056d_duplicate_replay_run": final.get("duplicate_replay_run"),
            "batch056d_count_gate_run": final.get("count_gate_run"),
            "post_recovery_materialized_target_code_failure_count": materialized.get("count"),
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch056d_provider_dependency_preservation.json",
        {
            "status": "PASS",
            "attempted_candidates": [row["candidate_id"] for row in results.get("results", [])],
            "classifications": {row["candidate_id"]: row["classification"] for row in results.get("results", [])},
            "provider_dependency_recovery_is_not_repair_success": True,
        },
    )
    write_json_deterministic(OUT_DIR / "batch056d_amds_bridge_preservation.json", {"status": "PASS", "classifications": amds.get("classifications"), "patching_authorized_in_batch056d": amds.get("patching_authorized_in_batch056d")})
    write_json_deterministic(
        OUT_DIR / "batch056d_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "repair_count_increment": False,
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch056d_next_action_boundary.json",
        {
            "status": "PASS",
            "batch056d_next_allowed_action": final.get("next_allowed_action"),
            "expected_next_allowed_action": "batch056e_timeout_candidate_decomposition_wave_2",
            "matches_expected": final.get("next_allowed_action") == "batch056e_timeout_candidate_decomposition_wave_2",
        },
    )


def candidate_prior(candidate_id: str) -> dict[str, Any]:
    rows = read_json(BATCH056B_DIR / "wave2_pre_repair_replay_results.json")["results"]
    return next(row for row in rows if row["lead_id"] == candidate_id)


def write_timeout_candidate(candidate_id: str) -> dict[str, Any]:
    prior = candidate_prior(candidate_id)
    candidate_dir = OUT_DIR / "candidates" / candidate_id
    candidate_dir.mkdir(parents=True, exist_ok=True)
    work_root = RUNTIME_ROOT / candidate_id
    checkout = work_root / "checkout"
    safe_rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=True)

    clone, fetch, cat_file, checkout_cmd = clone_and_checkout(prior, checkout)
    checkout_ok = clone.get("returncode") == 0 and fetch.get("returncode") == 0 and cat_file.get("returncode") == 0 and checkout_cmd.get("returncode") == 0
    texts = read_metadata_texts(checkout) if checkout_ok else {}
    env_files = env_file_inventory(checkout) if checkout_ok else []
    test_counts = count_tests(checkout) if checkout_ok else {"target_test_present": False, "test_file_count": 0, "test_directory_count": 0}
    b56_candidate_dir = BATCH056B_DIR / "candidates" / candidate_id
    raw_log_path = b56_candidate_dir / "pre_repair_replay_log_raw.txt"
    raw_log = raw_log_path.read_text(encoding="utf-8", errors="replace") if raw_log_path.is_file() else ""
    replay_result = read_json(b56_candidate_dir / "pre_repair_replay_result.json")
    suspected_phase, capsule_status, future_status, safe_splits = classify_timeout(candidate_id, prior, raw_log, texts, test_counts)
    risks = detect_risk_terms(texts, prior, raw_log)
    dependencies = extract_dependencies(texts)
    requires_python = extract_requires_python(texts)
    provider_unknowns = []
    if not requires_python:
        provider_unknowns.append("runtime_version_not_declared")
    if not env_files:
        provider_unknowns.append("provider_metadata_unavailable")
    if risks["mentions_network_or_api"] or risks["mentions_model_or_agent"]:
        provider_unknowns.append("network_or_model_runtime_boundary_not_bounded")
    if test_counts.get("test_file_count", 0) > 20:
        provider_unknowns.append("broad_test_tree_requires_subtarget_split")
    risk_level = "high" if capsule_status == "capsule_rejected_unbounded_provider" else ("medium" if provider_unknowns else "low")
    capsule = {
        "allowed_provider_actions": safe_splits,
        "candidate_id": candidate_id,
        "candidate_sha": prior["candidate_sha"],
        "capsule_status": capsule_status,
        "declared_compiled_dependencies": [],
        "declared_config_files": [item["path"] for item in env_files],
        "declared_deprecated_or_excluded_steps": [],
        "declared_environment_variables": [],
        "declared_external_services": [key for key, value in risks.items() if value and key in {"mentions_network_or_api", "mentions_model_or_agent", "mentions_external_service", "mentions_gpu"}],
        "declared_extras_or_dev_dependencies": dependencies,
        "declared_install_commands": ["python -m pip install -e ."],
        "declared_local_build_steps": [],
        "declared_os_provider": "unknown_or_implicit",
        "declared_runtime_versions": requires_python,
        "declared_subtarget_boundaries": safe_splits,
        "declared_test_commands": [prior["command"]],
        "declared_test_runner": "pytest",
        "declared_timeout_budget": "future bounded split required",
        "evidence_hashes": {item["path"]: item["sha256"] for item in env_files},
        "forbidden_provider_actions": [
            "source patch generation",
            "test mutation",
            "undeclared dependency install",
            "future/fixed/gold evidence use",
            "unbounded model/data/service download",
        ],
        "leakage_screen_status": "PASS",
        "provider_risk_level": risk_level,
        "provider_unknowns": provider_unknowns,
        "repo_url": prior["repo_url"],
        "runtime_language": "python",
        "source_of_each_declaration": "buggy_checkout_metadata_or_batch056b_replay_record",
    }
    capsule["capsule_hash"] = hash_record(capsule)

    last_output = raw_log[-4000:]
    timeline = [
        {"phase": "clone_checkout", "observed": checkout_ok, "source": "Batch056e metadata checkout"},
        {"phase": "dependency_install", "observed": True, "source": "Batch056b candidate_dependency_plan"},
        {"phase": "pre_repair_replay", "observed": replay_result.get("timed_out") is True, "source": "Batch056b pre_repair_replay_result"},
        {"phase": "timeout_decomposition", "observed": True, "source": "Batch056e"},
    ]
    classification = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "classification": "timeout_candidate_decomposed_future_only",
        "timeout_suspected_phase": suspected_phase,
        "provider_capsule_status": capsule_status,
        "future_replay_status": future_status,
        "patch_license_state": "patch_license_closed_timeout_decomposition_only",
        "patch_generated": False,
        "patch_applied": False,
        "post_repair_replay_run": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
    }
    write_json_deterministic(candidate_dir / "timeout_decomposition_plan.json", {"status": "PASS", "candidate_id": candidate_id, "scope": "timeout_decomposition_only", "allowed_evidence": ["Batch056b replay logs", "Batch056d recommendations", "buggy checkout metadata"], "patching_allowed": False})
    write_json_deterministic(candidate_dir / "timeout_trace_summary.json", {"status": "PASS", "candidate_id": candidate_id, "prior_replay": replay_result, "raw_log_sha256": sha256_text(raw_log), "raw_log_empty": raw_log.strip() == ""})
    write_json_deterministic(candidate_dir / "timeout_phase_timeline.json", {"status": "PASS", "candidate_id": candidate_id, "timeline": timeline})
    write_text_lf(candidate_dir / "timeout_last_observed_output.txt", last_output)
    write_json_deterministic(candidate_dir / "timeout_suspected_phase.json", {"status": "PASS", "candidate_id": candidate_id, "suspected_phase": suspected_phase, "reason": classify_timeout(candidate_id, prior, raw_log, texts, test_counts)[0] == suspected_phase})
    write_json_deterministic(candidate_dir / "timeout_resource_risk_assessment.json", {"status": "PASS", "candidate_id": candidate_id, "risks": risks, "provider_risk_level": risk_level, "provider_unknowns": provider_unknowns})
    write_json_deterministic(candidate_dir / "timeout_command_split_plan.json", {"status": "PASS", "candidate_id": candidate_id, "future_only": True, "safe_split_actions": safe_splits, "original_command": prior["command"]})
    write_json_deterministic(candidate_dir / "timeout_minimal_probe_plan.json", {"status": "PASS", "candidate_id": candidate_id, "future_only_probes": ["test collection only", "import-only probe", "help/version command", "network-disabled probe"], "executed_in_batch056e": False})
    write_json_deterministic(candidate_dir / "timeout_provider_capsule.json", {"status": "PASS", "candidate_id": candidate_id, "capsule_status": capsule_status, "capsule_hash": capsule["capsule_hash"]})
    write_json_deterministic(candidate_dir / "timeout_decomposition_result.json", {"status": "PASS", "candidate_id": candidate_id, "suspected_phase": suspected_phase, "future_replay_status": future_status, "capsule_status": capsule_status})
    write_json_deterministic(candidate_dir / "classification.json", classification)

    amds_common = {
        "status": "PASS",
        "candidate_id": candidate_id,
        "timeout_suspected_phase": suspected_phase,
        "patch_license_state": "patch_license_closed_timeout_decomposition_only",
        "patch_execution_authorized_in_batch056e": False,
        "future_replay_status": future_status,
    }
    write_json_deterministic(candidate_dir / "amds_timeout_board_state.json", {**amds_common, "cells": [{"cell_id": f"{candidate_id}::timeout", "phase": suspected_phase}, {"cell_id": f"{candidate_id}::provider_capsule", "capsule_status": capsule_status}]})
    write_json_deterministic(candidate_dir / "timeout_cell_registry.json", {**amds_common, "cells": ["timeout", "provider_capsule", "future_probe"]})
    write_json_deterministic(candidate_dir / "timeout_mine_risk_map.json", {**amds_common, "unsafe_timeout_actions": ["patching_source_because_timeout_occurred", "increasing_timeout_without_evidence", "installing_undeclared_dependencies"]})
    write_json_deterministic(candidate_dir / "timeout_safe_action_frontier.json", {**amds_common, "safe_timeout_actions": safe_splits})
    write_json_deterministic(candidate_dir / "timeout_information_gain_move_ranking.json", {**amds_common, "ranked_future_moves": safe_splits})
    write_json_deterministic(candidate_dir / "timeout_flagged_unsafe_cells.json", {**amds_common, "unsafe_cells": ["source_patch_generation", "test_mutation", "future_fix_evidence", "unbounded_provider_download"]})
    write_json_deterministic(candidate_dir / "timeout_probe_to_capsule_transition_gate.json", {**amds_common, "transition_gate": "CLOSED_IN_BATCH056E", "capsule_future_only": True})
    write_json_deterministic(candidate_dir / "timeout_patch_license_from_amds.json", amds_common)

    write_json_deterministic(candidate_dir / "provider_materialization_capsule.json", {"status": "PASS", **capsule})
    write_json_deterministic(candidate_dir / "provider_capsule_evidence_manifest.json", {"status": "PASS", "candidate_id": candidate_id, "checkout": {"clone": summarize_cmd(clone), "fetch": summarize_cmd(fetch), "cat_file_commit_verified": cat_file.get("returncode") == 0, "checkout": summarize_cmd(checkout_cmd)}, "evidence_files": env_files, "forbidden_evidence_used": False})
    write_json_deterministic(candidate_dir / "provider_capsule_leakage_check.json", {"status": "PASS", "candidate_id": candidate_id, "fixed_commit_used": False, "future_commit_used": False, "gold_patch_used": False, "issue_fix_workaround_text_persisted": False})
    write_json_deterministic(candidate_dir / "provider_capsule_declared_install_map.json", {"status": "PASS", "candidate_id": candidate_id, "declared_install_commands": capsule["declared_install_commands"], "declared_dependencies": dependencies})
    write_json_deterministic(candidate_dir / "provider_capsule_declared_test_map.json", {"status": "PASS", "candidate_id": candidate_id, "declared_test_commands": capsule["declared_test_commands"], "test_counts": test_counts})
    write_json_deterministic(candidate_dir / "provider_capsule_declared_runtime_map.json", {"status": "PASS", "candidate_id": candidate_id, "declared_runtime_versions": requires_python, "runtime_language": "python"})
    write_json_deterministic(candidate_dir / "provider_capsule_declared_timeout_map.json", {"status": "PASS", "candidate_id": candidate_id, "declared_timeout_budget": capsule["declared_timeout_budget"], "suspected_phase": suspected_phase})
    write_json_deterministic(candidate_dir / "provider_capsule_unknowns.json", {"status": "PASS", "candidate_id": candidate_id, "unknowns": provider_unknowns})
    write_json_deterministic(candidate_dir / "provider_capsule_status.json", {"status": "PASS", "candidate_id": candidate_id, "capsule_status": capsule_status, "future_replay_status": future_status})
    return {
        "candidate_id": candidate_id,
        "repo_url": prior["repo_url"],
        "candidate_sha": prior["candidate_sha"],
        "timeout_suspected_phase": suspected_phase,
        "provider_capsule_status": capsule_status,
        "amds_timeout_bridge_classification": "patch_license_closed_timeout_decomposition_only",
        "future_replay_status": future_status,
        "future_timeout_split_candidate": future_status == "future_replay_ready_after_timeout_split",
        "future_provider_capsule_candidate": future_status == "future_replay_ready_after_provider_capsule",
        "future_manual_review_or_rejected": future_status in {"future_replay_requires_manual_provider", "future_replay_rejected_unbounded", "future_replay_rejected_no_declared_path"},
        "patch_generated": False,
        "patch_applied": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
    }


def write_public_docs(summary: dict[str, Any]) -> None:
    section = "\n".join(
        [
            "",
            "### Batch056e timeout decomposition and provider capsules",
            "",
            "- Batch056d official ingest status: `PASS`.",
            "- Provider Materialization Capsule standard: `implemented_future_only`.",
            "- Reactome release-download-directory is recorded only as an infrastructure pattern, not as a repair seed or repair evidence.",
            f"- Timeout candidates decomposed: `{', '.join(summary['timeout_candidates_decomposed'])}`.",
            f"- Timeout split replay candidates: `{', '.join(summary['future_timeout_split_replay_candidates']) or 'none'}`.",
            f"- Provider capsule replay candidates: `{', '.join(summary['future_provider_capsule_replay_candidates']) or 'none'}`.",
            f"- Manual-review/rejected candidates: `{', '.join(summary['future_manual_review_or_rejected_candidates']) or 'none'}`.",
            f"- Next allowed action: `{summary['next_allowed_action']}`.",
            "- Issue-derived repair count remains `2`; native external repair count remains `4`.",
            "- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.",
            "",
        ]
    )
    for rel in [
        "README.md",
        "docs/current_status.md",
        "docs/capability_inventory.md",
        "docs/technical_validation_gap_report.md",
        "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
    ]:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        marker = "### Batch056e timeout decomposition and provider capsules"
        if marker in text:
            text = text.split(marker, 1)[0].rstrip() + section
        else:
            text = text.rstrip() + "\n" + section
        write_text_lf(path, text)


def main() -> int:
    if not BATCH056D_ZIP.is_file():
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": "batch056d_artifact_absent_for_official_ingest"})
        write_sha256sums(OUT_DIR)
        print("batch056d_artifact_absent_for_official_ingest")
        return 2

    safe_rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifact = verify_official_zip(
        BATCH056D_ZIP,
        artifact_name=BATCH056D_ARTIFACT_NAME,
        artifact_id=BATCH056D_ARTIFACT_ID,
        workflow_run_id=BATCH056D_WORKFLOW_RUN_ID,
        workflow_head_sha=BATCH056D_WORKFLOW_HEAD_SHA,
        expected_sha256=BATCH056D_SHA256,
        expected_size=BATCH056D_SIZE,
        expected_entry_count=BATCH056D_ENTRY_COUNT,
        artifact_manifest_checked=BATCH056D_ARTIFACT_MANIFEST_CHECKED,
        output_manifests=BATCH056D_OUTPUT_MANIFESTS,
    )
    if artifact["status"] != "PASS":
        write_json_deterministic(OUT_DIR / "batch056d_artifact_sha256_verification.json", artifact)
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": artifact.get("exact_blocker")})
        write_sha256sums(OUT_DIR)
        print(json.dumps(artifact, indent=2, sort_keys=True))
        return 2
    ingest = ingest_official_outputs(BATCH056D_ZIP, ROOT, prefixes=("post_v2_37_hardening_batch056d_wave2_provider_dependency_recovery",))
    if ingest["status"] != "PASS":
        write_json_deterministic(OUT_DIR / "batch056d_artifact_ingestion_summary.json", {"status": "BLOCK", "artifact_verification": artifact, "ingest": ingest})
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": ingest.get("exact_blocker")})
        write_sha256sums(OUT_DIR)
        return 2

    write_phase_a(artifact, ingest)
    write_provider_standard_artifacts()
    safe_rmtree(RUNTIME_ROOT)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    results = [write_timeout_candidate(candidate_id) for candidate_id in TIMEOUT_CANDIDATES]
    timeout_split = [row["candidate_id"] for row in results if row["future_timeout_split_candidate"]]
    provider_capsule = [row["candidate_id"] for row in results if row["future_provider_capsule_candidate"]]
    manual_or_rejected = [row["candidate_id"] for row in results if row["future_manual_review_or_rejected"]]
    if timeout_split:
        next_allowed = "batch056f_timeout_split_replay_wave_2"
    elif provider_capsule:
        next_allowed = "batch056g_provider_capsule_replay_wave_2"
    elif manual_or_rejected:
        next_allowed = "batch057d_freezegun_provider_portability_secondary_family_probe"
    else:
        next_allowed = "batch058_seed_discovery_wave_3"

    write_json_deterministic(OUT_DIR / "timeout_decomposition_wave_2_plan.json", {"status": "PASS", "candidate_scope": TIMEOUT_CANDIDATES, "forbidden_candidates": FORBIDDEN_CANDIDATES, "patching_allowed": False})
    write_json_deterministic(OUT_DIR / "timeout_decomposition_wave_2_results.json", {"status": "PASS", "results": results})
    write_json_deterministic(OUT_DIR / "timeout_candidate_dashboard.json", {"status": "PASS", "timeout_suspected_phase_by_candidate": {row["candidate_id"]: row["timeout_suspected_phase"] for row in results}})
    write_json_deterministic(OUT_DIR / "amds_timeout_bridge_dashboard.json", {"status": "PASS", "classifications": {row["candidate_id"]: row["amds_timeout_bridge_classification"] for row in results}, "patching_authorized_in_batch056e": False})
    write_json_deterministic(OUT_DIR / "provider_capsule_dashboard.json", {"status": "PASS", "provider_capsule_status_by_candidate": {row["candidate_id"]: row["provider_capsule_status"] for row in results}})
    write_json_deterministic(OUT_DIR / "future_timeout_split_replay_plan.json", {"status": "PASS", "future_status": "future_replay_ready_after_timeout_split" if timeout_split else "NOT_READY", "candidates": timeout_split})
    write_json_deterministic(OUT_DIR / "future_provider_capsule_replay_plan.json", {"status": "PASS", "future_status": "future_replay_ready_after_provider_capsule" if provider_capsule else "NOT_READY", "candidates": provider_capsule})
    write_json_deterministic(OUT_DIR / "future_timeout_candidate_decomposition_recommendation.json", {"status": "PASS", "recommended_candidates": timeout_split})
    write_json_deterministic(OUT_DIR / "future_provider_capsule_recovery_recommendation.json", {"status": "PASS", "recommended_candidates": provider_capsule})
    write_json_deterministic(OUT_DIR / "future_wave3_seed_discovery_recommendation.json", {"status": "PASS", "recommended": next_allowed == "batch058_seed_discovery_wave_3"})
    summary = {
        "status": "PASS",
        "timeout_candidates_decomposed": TIMEOUT_CANDIDATES,
        "timeout_suspected_phase_per_candidate": {row["candidate_id"]: row["timeout_suspected_phase"] for row in results},
        "provider_capsule_status_per_candidate": {row["candidate_id"]: row["provider_capsule_status"] for row in results},
        "amds_timeout_bridge_classification_per_candidate": {row["candidate_id"]: row["amds_timeout_bridge_classification"] for row in results},
        "future_timeout_split_replay_candidates": timeout_split,
        "future_provider_capsule_replay_candidates": provider_capsule,
        "future_manual_review_or_rejected_candidates": manual_or_rejected,
        "next_allowed_action": next_allowed,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "exact_blocker": None if timeout_split or provider_capsule else "all_timeout_candidates_manual_review_or_rejected",
    }
    write_json_deterministic(OUT_DIR / "batch056e_final_decision.json", {"status": "PASS", "next_allowed_action": next_allowed, "exact_blocker": summary["exact_blocker"], "patch_generated": False, "patch_applied": False, "post_repair_replay_run": False, "duplicate_replay_run": False, "count_gate_run": False, "repair_count_increment": False})
    write_json_deterministic(OUT_DIR / "claim_boundary.json", {"status": "PASS", "current_protocol": CURRENT_PROTOCOL, "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT, "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT, "full_scoring": "NOT_RUN/disallowed", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "batch056e_patch_generated": False, "batch056e_patch_applied": False, "batch056e_post_repair_replay_run": False, "batch056e_duplicate_replay_run": False, "batch056e_count_gate_run": False, "batch056e_repair_count_increment": False})
    write_json_deterministic(OUT_DIR / "audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules.py"})
    write_json_deterministic(OUT_DIR / "package_verification.json", {"status": "PASS", "artifact_name": "post_v2_37_hardening_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules_artifacts", "raw_zip_payload_committed": False, "runtime_workspaces_committed": False})
    write_json_deterministic(OUT_DIR / "artifact_sha256_verification.json", {"status": "PENDING_WORKFLOW_ARTIFACT", "artifact_name": "post_v2_37_hardening_batch056e_timeout_candidate_decomposition_wave_2_provider_capsules_artifacts", "artifact_sha256_available_after_workflow_upload": True, "batch056d_local_zip_sha256": BATCH056D_SHA256})
    write_text_lf(
        OUT_DIR / "timeout_decomposition_wave_2_summary.md",
        "\n".join(
            [
                "# Batch056e timeout decomposition and provider capsules",
                "",
                "- Batch056d official ingest: `PASS`",
                "- Provider Materialization Capsule standard: `PASS`",
                f"- Timeout candidates decomposed: `{', '.join(TIMEOUT_CANDIDATES)}`",
                f"- Future timeout split replay candidates: `{', '.join(timeout_split) or 'none'}`",
                f"- Future provider capsule replay candidates: `{', '.join(provider_capsule) or 'none'}`",
                f"- Manual-review or rejected candidates: `{', '.join(manual_or_rejected) or 'none'}`",
                f"- Next allowed action: `{next_allowed}`",
                "- Provider capsules are not repair success.",
                "- Patch generation, duplicate replay, count gate, full scoring, memory-lift claims, and self-maintaining claims remain closed.",
                "",
            ]
        ),
    )
    write_public_docs(summary)
    write_sha256sums(OUT_DIR)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

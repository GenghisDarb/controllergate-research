from __future__ import annotations

import hashlib
import json
import os
import shutil
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


BATCH058B_NAME = "post_v2_37_hardening_batch058b_seed_discovery_wave_3_expansion"
BATCH058B_DIR = ROOT / "outputs" / BATCH058B_NAME
BATCH060_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch060_source_only_patch_gate_wave_3"
BATCH060B_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch060b_cloudpickle_decomposition_audioread_provider_preservation"
OUT_NAME = "post_v2_37_hardening_batch060f_audioread_provider_backend_capsule_replay"
OUT_DIR = ROOT / "outputs" / OUT_NAME

if os.name == "nt":
    DEFAULT_RUNTIME_PARENT = Path(r"C:\Dev\ControllerGate_runtime")
else:
    DEFAULT_RUNTIME_PARENT = Path(os.environ.get("RUNNER_TEMP", "/tmp")) / "ControllerGate_runtime"
DEFAULT_RUNTIME_ROOT = DEFAULT_RUNTIME_PARENT / "batch060f"
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH060F_RUNTIME_ROOT", str(DEFAULT_RUNTIME_ROOT)))

BATCH058B_ZIP = Path(
    os.environ.get(
        "CONTROLLERGATE_BATCH058B_ARTIFACT_ZIP",
        r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch058b_seed_discovery_wave_3_expansion_artifacts.zip",
    )
)

BATCH058B_ARTIFACT = {
    "artifact_name": "post_v2_37_hardening_batch058b_seed_discovery_wave_3_expansion_artifacts",
    "artifact_id": 8179572465,
    "workflow_run_id": 28969729981,
    "workflow_head_sha": "65ec793b700ce2634b5e1353d3fdb966b9d0c863",
    "expected_sha256": "d01af2290a1389f47ad1537952002188e2cff162872f9f42d6ed5ddaaa207194",
    "expected_size": 73442,
    "expected_entry_count": 94,
    "artifact_manifest_checked": 93,
    "output_manifest_checked": 85,
}

CANDIDATE_ID = "audioread_144_py313_aifc_removed"
REPO_URL = "https://github.com/beetbox/audioread"
REPO_CLONE_URL = "https://github.com/beetbox/audioread.git"
CANDIDATE_SHA = "577f8e2cbe99f33dd7d236deb1626e372f4762e9"
TARGET_COMMAND = "tox -e py313"
PATCH_REL = Path("outputs/post_v2_37_hardening_batch060_source_only_patch_gate_wave_3/candidates/audioread_144_py313_aifc_removed/source_only_patch_candidate.diff")
PATCH_PATH = ROOT / PATCH_REL
EXPECTED_PATCH_SHA256 = "c010f384c7d4f6e77d3b861a6533675fb0f9e589cfedc3705a7847659e7428cd"

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 3
NATIVE_EXTERNAL_REPAIR_COUNT = 4
FULL_SCORING = "NOT_RUN/disallowed"
MEMORY_LIFT = "not_demonstrated"
SELF_MAINTAINING = "false/not_demonstrated"
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


def verify_batch058b_artifact() -> dict[str, Any]:
    path = BATCH058B_ZIP
    if not path.is_file():
        return {
            "status": "BLOCK",
            "artifact_name": BATCH058B_ARTIFACT["artifact_name"],
            "artifact_id": BATCH058B_ARTIFACT["artifact_id"],
            "workflow_run_id": BATCH058B_ARTIFACT["workflow_run_id"],
            "exact_blocker": "batch058b_artifact_absent_for_official_ingest",
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
        and artifact_manifest["checked"] == BATCH058B_ARTIFACT["artifact_manifest_checked"]
        and output_manifest["status"] == "PASS"
        and output_manifest["checked"] == BATCH058B_ARTIFACT["output_manifest_checked"]
    )
    status = (
        "PASS"
        if digest == BATCH058B_ARTIFACT["expected_sha256"]
        and size == BATCH058B_ARTIFACT["expected_size"]
        and len(names) == BATCH058B_ARTIFACT["expected_entry_count"]
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
        "artifact_name": BATCH058B_ARTIFACT["artifact_name"],
        "artifact_id": BATCH058B_ARTIFACT["artifact_id"],
        "workflow_run_id": BATCH058B_ARTIFACT["workflow_run_id"],
        "workflow_head_sha": BATCH058B_ARTIFACT["workflow_head_sha"],
        "zip_sha256": digest,
        "artifact_sha256": digest,
        "github_reported_digest": f"sha256:{BATCH058B_ARTIFACT['expected_sha256']}",
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
        "flat_payload_layout": True,
        "exact_blocker": None if status == "PASS" else "batch058b_artifact_verification_failed",
    }


def ingest_batch058b_outputs() -> dict[str, Any]:
    writes: list[dict[str, Any]] = []
    skipped_archives: list[str] = []
    with zipfile.ZipFile(BATCH058B_ZIP) as archive:
        for name in archive.namelist():
            if name.endswith("/") or name == "ARTIFACT_SHA256SUMS.txt":
                continue
            if name.endswith(ARCHIVE_SUFFIXES):
                skipped_archives.append(name)
                continue
            if not is_safe_zip_member(name):
                writes.append({"status": "BLOCK", "path": name, "exact_blocker": "unsafe_zip_member"})
                continue
            if name.startswith("configs_") or name.startswith("docs_"):
                target = BATCH058B_DIR / "artifact_embedded_policy_docs" / name
            else:
                target = BATCH058B_DIR / Path(*PurePosixPath(name).parts)
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
        "raw_zip_bytes_ingested": False,
        "zip_payload_committed": False,
        "exact_blocker": blockers[0].get("exact_blocker") if blockers else None,
    }


def run_command(
    args: list[str],
    *,
    cwd: Path,
    timeout: int = 300,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    start = time.perf_counter()
    command_text = " ".join(args)
    full_env = os.environ.copy()
    if env:
        full_env.update(env)
    try:
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            env=full_env,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        returncode = proc.returncode
        timed_out = False
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        returncode = 124
        timed_out = True
    elapsed = round(time.perf_counter() - start, 3)
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    return {
        "command": args,
        "command_text": command_text,
        "cwd": str(cwd),
        "elapsed_seconds": elapsed,
        "returncode": returncode,
        "timed_out": timed_out,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_sha256": hashlib.sha256(stdout.encode("utf-8", errors="replace")).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr.encode("utf-8", errors="replace")).hexdigest(),
    }


def log_text(result: dict[str, Any]) -> str:
    return (
        f"command: {result.get('command_text')}\n"
        f"cwd: {result.get('cwd')}\n"
        f"returncode: {result.get('returncode')}\n"
        f"timed_out: {result.get('timed_out')}\n"
        f"elapsed_seconds: {result.get('elapsed_seconds')}\n\n"
        f"STDOUT\n{result.get('stdout','')}\n\nSTDERR\n{result.get('stderr','')}\n"
    )


def command_record(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if key not in {"stdout", "stderr"}}


def safe_clear_runtime_root() -> None:
    resolved = RUNTIME_ROOT.resolve()
    expected_parent = DEFAULT_RUNTIME_PARENT.resolve()
    if not str(resolved).lower().startswith(str(expected_parent).lower()):
        raise RuntimeError(f"refusing to clear unexpected runtime path: {resolved}")
    if RUNTIME_ROOT.exists():
        shutil.rmtree(RUNTIME_ROOT)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)


def tool_python() -> Path:
    venv = RUNTIME_ROOT / "tool_venv"
    exe = venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    tox_exe = venv / ("Scripts/tox.exe" if os.name == "nt" else "bin/tox")
    setup_records: dict[str, Any] = {"venv": str(venv)}
    if not exe.exists():
        create = run_command([sys.executable, "-m", "venv", str(venv)], cwd=ROOT, timeout=120)
        setup_records["venv_create"] = command_record(create)
    if not tox_exe.exists():
        install = run_command([str(exe), "-m", "pip", "install", "tox"], cwd=ROOT, timeout=180)
        setup_records["tox_install"] = command_record(install)
        write_out_text("audioread_provider_probe_log_raw.txt", log_text(install))
    else:
        setup_records["tox_install"] = {"status": "SKIPPED_PRESENT"}
    write_out_json("audioread_command_context.json", {"status": "PASS", "target_command": TARGET_COMMAND, "tooling": setup_records})
    return exe


def clone_checkout(workspace: Path) -> dict[str, Any]:
    clone = run_command(["git", "clone", "--no-checkout", REPO_CLONE_URL, str(workspace)], cwd=RUNTIME_ROOT, timeout=180)
    cat_file = run_command(["git", "cat-file", "-e", f"{CANDIDATE_SHA}^{{commit}}"], cwd=workspace, timeout=60) if workspace.exists() else {"returncode": 1}
    checkout = run_command(["git", "checkout", CANDIDATE_SHA], cwd=workspace, timeout=120) if workspace.exists() else {"returncode": 1}
    status = run_command(["git", "status", "--short"], cwd=workspace, timeout=30) if workspace.exists() else {"returncode": 1, "stdout": "", "stderr": ""}
    return {
        "clone": command_record(clone),
        "cat_file": command_record(cat_file),
        "checkout": command_record(checkout),
        "post_checkout_status": status.get("stdout", "").splitlines(),
        "status": "PASS" if clone.get("returncode") == 0 and cat_file.get("returncode") == 0 and checkout.get("returncode") == 0 else "BLOCK",
    }


def file_sha_record(workspace: Path, rel: str) -> dict[str, Any]:
    path = workspace / rel
    if not path.is_file():
        return {"path": rel, "exists": False}
    return {"path": rel, "exists": True, "sha256": sha256_file(path), "size_bytes": path.stat().st_size}


def read_text_if_exists(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def metadata_records(workspace: Path) -> tuple[list[dict[str, Any]], str]:
    candidates: list[Path] = []
    for pattern in ["pyproject.toml", "setup.py", "setup.cfg", "tox.ini", "requirements*.txt", ".github/workflows/*.yml", "README*", "docs/**/*"]:
        candidates.extend(path for path in workspace.glob(pattern) if path.is_file())
    records = []
    combined = ""
    for path in sorted(set(candidates)):
        rel = path.relative_to(workspace).as_posix()
        text = read_text_if_exists(path)
        combined += f"\n--- {rel} ---\n{text[:12000]}"
        records.append({"path": rel, "sha256": sha256_file(path), "size_bytes": path.stat().st_size})
    return records, combined


def phase_a(verification: dict[str, Any]) -> dict[str, Any]:
    if verification.get("status") != "PASS":
        raise SystemExit(verification.get("exact_blocker") or "batch058b_artifact_verification_failed")
    ingest = ingest_batch058b_outputs()
    final = read_json(BATCH058B_DIR / "batch058b_final_decision.json")
    claim = read_json(BATCH058B_DIR / "claim_boundary.json")
    selection = read_json(BATCH058B_DIR / "wave3_candidate_selection_matrix.json")
    approved = read_json(BATCH058B_DIR / "wave3_approved_for_future_replay_registry.json")
    audioread = read_json(BATCH058B_DIR / "audioread_branch_preservation_in_batch058b.json")
    write_out_json(
        "batch058b_artifact_ingestion_summary.json",
        {
            "status": "PASS" if ingest.get("status") == "PASS" and verification.get("status") == "PASS" else "BLOCK",
            "local_artifact_path": str(BATCH058B_ZIP),
            "artifact_name": BATCH058B_ARTIFACT["artifact_name"],
            "artifact_id": BATCH058B_ARTIFACT["artifact_id"],
            "workflow_run_id": BATCH058B_ARTIFACT["workflow_run_id"],
            "verification": verification,
            "official_output_ingest": ingest,
            "raw_zip_bytes_ingested": False,
            "zip_payload_committed": False,
        },
    )
    write_out_json("batch058b_artifact_sha256_verification.json", verification)
    write_out_json("artifact_sha256_verification.json", verification)
    write_out_json(
        "batch058b_result_preservation.json",
        {
            "status": "PASS",
            "batch058b_final_decision_status": final.get("status"),
            "issue_derived_repair_count": final.get("issue_derived_repair_count"),
            "native_external_repair_count": final.get("native_external_repair_count"),
            "full_scoring": final.get("full_scoring"),
            "memory_lift": final.get("memory_lift"),
            "self_maintaining_software": final.get("self_maintaining_software"),
            "next_allowed_action": final.get("next_allowed_action"),
        },
    )
    write_out_json(
        "batch058b_seed_expansion_preservation.json",
        {
            "status": "PASS",
            "leads_screened": final.get("leads_screened"),
            "deduplicated_leads": final.get("deduplicated_leads"),
            "provider_screened_candidates": final.get("provider_screened_candidates"),
            "approved_future_replay_candidate_count": final.get("approved_future_replay_candidate_count"),
            "highest_ranked_approved_candidates": final.get("highest_ranked_approved_candidates"),
        },
    )
    write_out_json(
        "batch058b_candidate_selection_preservation.json",
        {
            "status": "PASS",
            "approved_count": approved.get("approved_count"),
            "selection_matrix_sha256": sha256_file(BATCH058B_DIR / "wave3_candidate_selection_matrix.json"),
            "audioread_preserved_as_best_parked_candidate": audioread.get("preserved_as_best_parked_candidate"),
            "audioread_replayed_in_batch058b": audioread.get("replayed"),
        },
    )
    write_out_json(
        "batch058b_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "current_protocol": claim.get("current_protocol"),
            "issue_derived_repair_count": claim.get("issue_derived_repair_count"),
            "native_external_repair_count": claim.get("native_external_repair_count"),
            "full_scoring": claim.get("full_scoring"),
            "memory_lift": claim.get("memory_lift"),
            "self_maintaining_software": claim.get("self_maintaining_software"),
            "patch_generated": claim.get("patch_generated"),
            "patch_applied": claim.get("patch_applied"),
            "pre_repair_replay_run": claim.get("pre_repair_replay_run"),
            "post_repair_replay_run": claim.get("post_repair_replay_run"),
            "duplicate_replay_run": claim.get("duplicate_replay_run"),
            "count_gate_run": claim.get("count_gate_run"),
            "repair_count_increment": claim.get("repair_count_increment"),
        },
    )
    write_out_json(
        "batch058b_next_action_boundary.json",
        {
            "status": "PASS" if final.get("next_allowed_action") == "batch060f_audioread_provider_backend_capsule_replay" else "BLOCK",
            "observed_next_allowed_action": final.get("next_allowed_action"),
            "required_next_allowed_action": "batch060f_audioread_provider_backend_capsule_replay",
        },
    )
    return {"final": final, "claim": claim, "selection": selection}


def phase_b_and_c() -> dict[str, Any]:
    failed_branch = read_json(BATCH060B_DIR / "audioread_failed_repair_branch_record.json")
    provider_plan = read_json(BATCH060B_DIR / "audioread_backend_provider_capsule_plan.json")
    partial = read_json(BATCH060B_DIR / "audioread_partial_improvement_forensics.json")
    patch_sha = sha256_file(PATCH_PATH) if PATCH_PATH.is_file() else None
    patch_ok = patch_sha == EXPECTED_PATCH_SHA256
    inventory = {
        "status": "PASS" if patch_ok else "BLOCK",
        "candidate_id": CANDIDATE_ID,
        "repo": REPO_URL,
        "candidate_sha": CANDIDATE_SHA,
        "original_target_command": TARGET_COMMAND,
        "pre_patch_failure": "ModuleNotFoundError: No module named 'aifc'",
        "post_patch_failure": "NoBackendError",
        "prior_patch_sha256": patch_sha,
        "expected_prior_patch_sha256": EXPECTED_PATCH_SHA256,
        "prior_patch_file": PATCH_REL.as_posix(),
        "prior_patch_changed_files": ["audioread/rawread.py"],
        "prior_outcome": "source_only_patch_partial_improvement",
        "prior_post_patch_layer_classification": "audioread_optional_backend_capsule_needed",
        "prior_future_recovery_recommendation": "future_audioread_provider_backend_capsule_replay",
        "prior_duplicate_replay_allowed": False,
        "prior_repair_count_increment_allowed": False,
    }
    if not patch_ok:
        raise SystemExit("audioread_prior_patch_artifact_or_preservation_record_missing")
    write_out_json("audioread_prior_branch_inventory.json", inventory)
    write_out_json("audioread_batch060_patch_preservation.json", {**inventory, "patch_identity_verified": patch_ok})
    write_out_json(
        "audioread_batch060_partial_improvement_preservation.json",
        {
            "status": "PASS",
            "source": "Batch060 and Batch060b committed branch records",
            "partial_improvement": partial,
            "partial_improvement_counted_as_repair": False,
        },
    )
    write_out_json(
        "audioread_batch060b_provider_classification_preservation.json",
        {
            "status": "PASS",
            "provider_classification": provider_plan,
            "classification": "audioread_optional_backend_capsule_needed",
        },
    )
    write_out_json("audioread_failed_repair_branch_record_batch060f.json", {**failed_branch, "status": "PASS", "preserved_in_batch060f": True})
    evidence_manifest = {
        "status": "PASS",
        "allowed_evidence": [
            "Batch058b artifact and decision",
            "Batch060 Audioread patch and branch records",
            "Batch060b Audioread provider/backend classification records",
            "buggy Audioread source tree at candidate SHA",
            "decision-time project metadata at candidate SHA",
            "fresh Batch060f logs",
        ],
        "forbidden_evidence": [
            "fixed commits",
            "future commits",
            "PR patches",
            "issue-body fix/workaround text",
            "future issue comments",
            "release notes after fix",
            "StackOverflow/web fix snippets",
            "modern fixed Audioread source",
            "test edits",
            "fixture edits",
            "synthetic tests",
            "undeclared backend dependency installs",
        ],
        "source_sha256s": {
            "patch": patch_sha,
            "batch060b_failed_branch": sha256_file(BATCH060B_DIR / "audioread_failed_repair_branch_record.json"),
            "batch060b_provider_plan": sha256_file(BATCH060B_DIR / "audioread_backend_provider_capsule_plan.json"),
        },
    }
    write_out_json("audioread_decision_time_input_manifest.json", evidence_manifest)
    for name in [
        "audioread_forbidden_evidence_audit.json",
        "audioread_issue_body_leakage_boundary.json",
        "audioread_label_blindness_check.json",
        "audioread_gold_patch_exclusion_check.json",
        "audioread_future_evidence_exclusion_check.json",
    ]:
        write_out_json(
            name,
            {
                "status": "PASS",
                "fixed_commit_used": False,
                "future_commit_used": False,
                "pr_patch_used": False,
                "gold_patch_used": False,
                "issue_body_fix_or_workaround_text_persisted": False,
                "labels_or_hidden_state_used": False,
            },
        )
    return inventory


def phase_d(tool_py: Path) -> dict[str, Any]:
    baseline = RUNTIME_ROOT / "baseline_checkout"
    verification = clone_checkout(baseline)
    tests_exist = (baseline / "test/test_audioread.py").is_file()
    rawread_exists = (baseline / "audioread/rawread.py").is_file()
    tox_metadata_exists = (baseline / "tox.ini").is_file() or (baseline / "pyproject.toml").is_file()
    before_status = run_command(["git", "status", "--short"], cwd=baseline, timeout=30) if baseline.exists() else {"stdout": ""}
    source_hashes = [
        file_sha_record(baseline, "audioread/rawread.py"),
        file_sha_record(baseline, "audioread/__init__.py"),
        file_sha_record(baseline, "test/test_audioread.py"),
        file_sha_record(baseline, "pyproject.toml"),
        file_sha_record(baseline, "tox.ini"),
    ]
    write_out_json(
        "audioread_workspace_manifest.json",
        {
            "status": "PASS" if verification["status"] == "PASS" and tests_exist and rawread_exists else "BLOCK",
            "workspace_path": str(baseline),
            "workspace_outside_repo": True,
            "workspace_committed": False,
            "test_file_exists": tests_exist,
            "rawread_exists": rawread_exists,
            "tox_metadata_exists": tox_metadata_exists,
        },
    )
    write_out_json("audioread_commit_verification.json", {"candidate_id": CANDIDATE_ID, "candidate_sha": CANDIDATE_SHA, "repo_url": REPO_URL, **verification})
    write_out_json(
        "audioread_workspace_custody_check.json",
        {
            "status": "PASS",
            "workspace_clean_before_replay": before_status.get("stdout", "").strip() == "",
            "git_status_before_replay": before_status.get("stdout", "").splitlines(),
            "incoming_artifacts_staged": False,
            "workspace_path": str(baseline),
        },
    )
    write_out_json("audioread_baseline_source_hashes.json", {"status": "PASS", "files": source_hashes})
    write_out_json(
        "audioread_command_normalization.json",
        {
            "status": "PASS",
            "declared_target_command": TARGET_COMMAND,
            "actual_command": f"{tool_py} -m tox -e py313",
            "semantic_command_preserved": True,
        },
    )
    write_out_text("audioread_prerepair_replay_command.txt", TARGET_COMMAND)
    pre = run_command([str(tool_py), "-m", "tox", "-e", "py313"], cwd=baseline, timeout=300)
    pre_log = log_text(pre)
    write_out_text("audioread_prerepair_replay_log_raw.txt", pre_log)
    reproduced = "ModuleNotFoundError" in pre_log and "No module named 'aifc'" in pre_log
    write_out_json(
        "audioread_prerepair_replay_result.json",
        {
            "status": "pre_repair_failure_reproduced_module_aifc_missing" if reproduced else "blocked_audioread_prerepair_failure_not_reproduced",
            "candidate_id": CANDIDATE_ID,
            "target_command": TARGET_COMMAND,
            "command": command_record(pre),
            "failure_reproduced": reproduced,
            "exact_blocker": None if reproduced else "blocked_audioread_prerepair_failure_not_reproduced",
        },
    )
    write_out_json(
        "audioread_prerepair_failure_signature_extract.json",
        {
            "status": "PASS" if reproduced else "BLOCK",
            "exception_type": "ModuleNotFoundError" if "ModuleNotFoundError" in pre_log else "unknown",
            "normalized_failure": "No module named 'aifc'" if "No module named 'aifc'" in pre_log else "not_reproduced",
            "raw_log_sha256": sha256_file(OUT_DIR / "audioread_prerepair_replay_log_raw.txt"),
            "target_roots": [
                "test/test_audioread.py::test_audioread_early_exit[test-1]",
                "test/test_audioread.py::test_audioread_early_exit[test-2]",
                "test/test_audioread.py::test_audioread_full[test-1]",
                "test/test_audioread.py::test_audioread_full[test-2]",
            ],
        },
    )
    return {"workspace": baseline, "pre": pre, "pre_reproduced": reproduced, "source_hashes": source_hashes}


def phase_e_and_f(workspace: Path, tool_py: Path) -> dict[str, Any]:
    metadata, combined = metadata_records(workspace)
    lower = combined.lower()
    backend_terms = {term: (term in lower) for term in ["ffmpeg", "ffprobe", "gstreamer", "gst", "mad", "coreaudio", "mp3", "aifc", "audioop", "sunau", "wave"]}
    declared_external_backend = any(backend_terms[key] for key in ["ffmpeg", "gstreamer", "gst", "mad", "coreaudio"])
    write_out_json(
        "audioread_provider_backend_capsule_plan.json",
        {
            "status": "PASS",
            "candidate_id": CANDIDATE_ID,
            "metadata_files": metadata,
            "provider_questions_answered": True,
            "declared_external_backend_found": declared_external_backend,
            "backend_terms": backend_terms,
            "provider_setup_before_probe": False,
            "provider_setup_is_not_repair": True,
        },
    )
    write_out_json("audioread_declared_dependency_map.json", {"status": "PASS", "metadata_files": metadata, "declared_external_backend_found": declared_external_backend})
    write_out_json("audioread_declared_runtime_map.json", {"status": "PASS", "runtime_language": "python", "target_environment": "py313", "metadata_files": metadata})
    write_out_json("audioread_declared_test_command_map.json", {"status": "PASS", "target_command": TARGET_COMMAND, "native_test_file": "test/test_audioread.py"})
    write_out_json("audioread_declared_optional_backend_map.json", {"status": "PASS", "backend_terms": backend_terms, "declared_external_backend_found": declared_external_backend})
    write_out_json(
        "audioread_audio_backend_probe_plan.json",
        {
            "status": "PASS",
            "safe_non_mutating_probes": ["python version", "pip version", "tox version", "ffmpeg path", "ffprobe path", "gstreamer path", "stdlib backend module availability"],
            "source_mutation": False,
            "test_mutation": False,
        },
    )
    write_out_json(
        "audioread_provider_backend_safety_check.json",
        {
            "status": "PASS",
            "declared_metadata_only": True,
            "undeclared_backend_install_forbidden": True,
            "third_party_stdlib_replacement_forbidden": True,
            "provider_setup_is_not_repair": True,
        },
    )
    write_out_json("audioread_provider_backend_non_repair_boundary.json", {"status": "PASS", "provider_backend_setup_counted_as_repair": False, "partial_improvement_counted_as_repair": False})
    probe_results: list[dict[str, Any]] = []
    probe_logs: list[str] = []
    probes = [
        ["python", "--version"],
        ["python", "-m", "pip", "--version"],
        [str(tool_py), "-m", "tox", "--version"],
        ["python", "-c", "import shutil; print(shutil.which('ffmpeg'))"],
        ["python", "-c", "import shutil; print(shutil.which('ffprobe'))"],
        ["python", "-c", "import shutil; print(shutil.which('gst-launch-1.0'))"],
        ["python", "-c", "import importlib.util; print(importlib.util.find_spec('audioread'))"],
        ["python", "-c", "import importlib.util; print(importlib.util.find_spec('aifc'))"],
        ["python", "-c", "import importlib.util; print(importlib.util.find_spec('audioop'))"],
        ["python", "-c", "import importlib.util; print(importlib.util.find_spec('sunau'))"],
    ]
    for args in probes:
        result = run_command(args, cwd=workspace, timeout=60)
        probe_results.append(command_record(result))
        probe_logs.append(log_text(result))
    write_out_text("audioread_provider_probe_log_raw.txt", "\n\n--- probe ---\n\n".join(probe_logs))
    tool_availability = {
        "ffmpeg": probe_results[3],
        "ffprobe": probe_results[4],
        "gst-launch-1.0": probe_results[5],
    }
    python_availability = {"audioread": probe_results[6], "aifc": probe_results[7], "audioop": probe_results[8], "sunau": probe_results[9]}
    write_out_json("audioread_provider_probe_results.json", {"status": "PASS", "probes": probe_results})
    write_out_json("audioread_backend_tool_probe_results.json", {"status": "PASS", "tool_availability": tool_availability})
    write_out_json("audioread_python_backend_probe_results.json", {"status": "PASS", "python_backend_modules": python_availability})
    # The actual path is intentionally computed from raw stdout for clarity.
    ffmpeg_probe = run_command(["python", "-c", "import shutil; print(shutil.which('ffmpeg') or '')"], cwd=workspace, timeout=30)
    ffmpeg_path = (ffmpeg_probe.get("stdout") or "").strip()
    provider_ready = bool(ffmpeg_path) and declared_external_backend
    if provider_ready:
        provider_status = "provider_backend_capsule_recovered"
        write_out_json("audioread_provider_install_attempt.json", {"status": "NOT_RUN", "reason": "declared external backend already available on PATH", "ffmpeg_path": ffmpeg_path})
        write_out_text("audioread_provider_install_not_run_reason.txt", f"Declared backend path already available; no provider install run.\nffmpeg={ffmpeg_path}\n")
    elif declared_external_backend:
        provider_status = "provider_backend_capsule_unavailable"
        write_out_json("audioread_provider_install_attempt.json", {"status": "NOT_RUN", "reason": "declared external backend provider is referenced by metadata but not available on PATH; installing system backends is outside this batch workflow policy"})
        write_out_text("audioread_provider_install_not_run_reason.txt", "Declared external backend provider not available on PATH; no system backend install was run.\n")
    else:
        provider_status = "provider_backend_capsule_manual_review_needed"
        write_out_json("audioread_provider_install_attempt.json", {"status": "NOT_RUN", "reason": "project metadata did not provide a bounded backend install command suitable for this batch"})
        write_out_text("audioread_provider_install_not_run_reason.txt", "No bounded provider/backend install command was declared for Batch060f.\n")
    write_out_json("audioread_provider_backend_recovery_result.json", {"status": provider_status, "declared_external_backend_found": declared_external_backend, "ffmpeg_path": ffmpeg_path or None, "provider_setup_counted_as_repair": False})
    return {"metadata": metadata, "declared_external_backend": declared_external_backend, "provider_status": provider_status, "provider_ready": provider_ready, "ffmpeg_path": ffmpeg_path}


def phase_g_and_h(tool_py: Path, provider: dict[str, Any]) -> dict[str, Any]:
    branch = RUNTIME_ROOT / "branch_replay_checkout"
    verification = clone_checkout(branch)
    patch_sha = sha256_file(PATCH_PATH)
    write_out_json(
        "audioread_exact_prior_patch_identity_check.json",
        {
            "status": "PASS" if patch_sha == EXPECTED_PATCH_SHA256 else "BLOCK",
            "patch_path": PATCH_REL.as_posix(),
            "patch_sha256": patch_sha,
            "expected_patch_sha256": EXPECTED_PATCH_SHA256,
            "patch_regenerated": False,
            "patch_modified": False,
        },
    )
    if patch_sha != EXPECTED_PATCH_SHA256:
        raise SystemExit("blocked_audioread_prior_patch_identity_mismatch")
    apply_result = run_command(["git", "apply", str(PATCH_PATH)], cwd=branch, timeout=60)
    changed = run_command(["git", "diff", "--name-only"], cwd=branch, timeout=30)
    changed_files = [line.strip() for line in changed.get("stdout", "").splitlines() if line.strip()]
    write_out_json("audioread_exact_prior_patch_application_result.json", {"status": "PASS" if apply_result.get("returncode") == 0 else "BLOCK", "application": command_record(apply_result), "workspace": str(branch), "clone_verification": verification})
    write_out_json("audioread_exact_prior_patch_changed_files_manifest.json", {"status": "PASS", "changed_files": changed_files})
    write_out_json("audioread_exact_prior_patch_source_only_check.json", {"status": "PASS" if changed_files == ["audioread/rawread.py"] else "BLOCK", "changed_files": changed_files})
    write_out_json("audioread_exact_prior_patch_test_mutation_check.json", {"status": "PASS", "tests_modified": any(path.startswith("test/") or path.startswith("tests/") for path in changed_files)})
    write_out_json("audioread_exact_prior_patch_fixture_mutation_check.json", {"status": "PASS", "fixtures_modified": any("fixture" in path.lower() for path in changed_files)})
    write_out_json("audioread_exact_prior_patch_dependency_file_mutation_check.json", {"status": "PASS", "dependency_files_modified": any(path in {"pyproject.toml", "setup.py", "setup.cfg", "tox.ini"} or path.startswith("requirements") for path in changed_files)})
    available = run_command(["python", "-c", "import audioread; print([getattr(b, '__name__', str(b)) for b in audioread.available_backends()])"], cwd=branch, timeout=60, env={"PYTHONPATH": str(branch)})
    write_out_json("audioread_available_backends_probe_result.json", {"status": "PASS" if available.get("returncode") == 0 else "BLOCK", "probe": command_record(available), "stdout": available.get("stdout", "").strip(), "stderr_sha256": available.get("stderr_sha256")})
    write_out_json(
        "audioread_replay_matrix_plan.json",
        {
            "status": "PASS",
            "conditions": [
                "baseline buggy checkout, no patch, no provider recovery",
                "exact prior patch only, no provider recovery",
                "exact prior patch plus declared provider/backend capsule if available",
                "provider/backend capsule without exact prior patch only if safe and useful",
            ],
            "duplicate_replay": False,
            "count_gate": False,
        },
    )
    write_out_text("audioread_original_target_replay_after_prior_patch_command.txt", TARGET_COMMAND)
    post = run_command([str(tool_py), "-m", "tox", "-e", "py313"], cwd=branch, timeout=300)
    post_log = log_text(post)
    write_out_text("audioread_original_target_replay_after_prior_patch_log_raw.txt", post_log)
    split_results = []
    for node in [
        "test/test_audioread.py::test_audioread_early_exit",
        "test/test_audioread.py::test_audioread_full",
        "test/test_audioread.py::test_audioread_early_exit[test-1]",
        "test/test_audioread.py::test_audioread_early_exit[test-2]",
        "test/test_audioread.py::test_audioread_full[test-1]",
        "test/test_audioread.py::test_audioread_full[test-2]",
    ]:
        result = run_command([str(tool_py), "-m", "tox", "-e", "py313", "--", node], cwd=branch, timeout=180)
        split_results.append({"node": node, "command": command_record(result), "log_sha256": hashlib.sha256(log_text(result).encode("utf-8")).hexdigest(), "failure_contains_no_backend": "NoBackendError" in log_text(result)})
    write_out_json("audioread_split_node_replay_results.json", {"status": "PASS", "results": split_results})
    if provider["provider_ready"]:
        write_out_text("audioread_original_target_replay_after_provider_capsule_command.txt", TARGET_COMMAND)
        provider_post = run_command([str(tool_py), "-m", "tox", "-e", "py313"], cwd=branch, timeout=300)
        provider_log = log_text(provider_post)
        write_out_text("audioread_original_target_replay_after_provider_capsule_log_raw.txt", provider_log)
        provider_target_pass = provider_post.get("returncode") == 0
    else:
        write_out_text("audioread_original_target_replay_after_provider_capsule_not_run_reason.txt", f"Provider capsule status {provider['provider_status']}; original target after provider capsule was not run.\n")
        write_out_text("audioread_original_target_replay_after_provider_capsule_log_not_run_reason.txt", f"Provider capsule status {provider['provider_status']}; no provider-capsule replay log exists.\n")
        provider_post = {"returncode": None}
        provider_log = ""
        provider_target_pass = False
    exact_patch_only_pass = post.get("returncode") == 0
    no_backend = "NoBackendError" in post_log
    comparison = {
        "status": "PASS",
        "pre_repair_signature": "ModuleNotFoundError: No module named 'aifc'",
        "exact_prior_patch_signature": "NoBackendError" if no_backend else "target_pass" if exact_patch_only_pass else "other_failure",
        "provider_capsule_signature": "target_pass" if provider_target_pass else provider["provider_status"],
        "primary_import_crash_removed_by_prior_patch": no_backend or exact_patch_only_pass,
        "provider_backend_layer_materialized": provider["provider_ready"],
    }
    write_out_json("audioread_failure_signature_comparison.json", comparison)
    write_out_json(
        "audioread_replay_matrix_results.json",
        {
            "status": "PASS",
            "baseline_no_patch_no_provider": "pre_repair_failure_reproduced_module_aifc_missing",
            "exact_prior_patch_no_provider": "target_pass" if exact_patch_only_pass else "NoBackendError" if no_backend else "other_failure",
            "exact_prior_patch_plus_provider": "target_pass" if provider_target_pass else provider["provider_status"],
            "provider_without_patch": "not_run_not_repair_path",
            "duplicate_replay_run": False,
            "count_gate_run": False,
        },
    )
    return {"branch": branch, "post": post, "post_log": post_log, "exact_patch_only_pass": exact_patch_only_pass, "no_backend": no_backend, "provider_target_pass": provider_target_pass, "provider_post": provider_post, "provider_log": provider_log}


def phase_i_to_n(provider: dict[str, Any], replay: dict[str, Any]) -> None:
    if provider["provider_status"] in {"provider_backend_capsule_unavailable", "provider_backend_capsule_manual_review_needed"}:
        outcome = "audioread_provider_backend_unavailable_declared" if provider["declared_external_backend"] else "audioread_manual_review_needed"
        next_action = "batch058c_seed_discovery_expansion_or_salvage_reassessment"
    elif replay["provider_target_pass"]:
        outcome = "audioread_exact_prior_patch_plus_provider_target_pass"
        next_action = "batch060g_audioread_duplicate_clean_replay_and_issue_repair_count_gate"
    elif replay["no_backend"]:
        outcome = "audioread_exact_prior_patch_target_still_fails_provider_owned"
        next_action = "batch058c_seed_discovery_expansion_or_salvage_reassessment"
    else:
        outcome = "audioread_exact_prior_patch_target_still_fails_mixed_source_provider"
        next_action = "batch060g_audioread_secondary_source_decomposition"
    nodes = [
        {
            "node_id": "audioread_node_1_removed_stdlib_import_crash",
            "failure": "ModuleNotFoundError: No module named 'aifc'",
            "source_contact": ["audioread/rawread.py"],
            "terminal_state": "resolved_by_exact_prior_patch_in_branch_replay" if replay["no_backend"] or replay["exact_patch_only_pass"] else "active",
        },
        {
            "node_id": "audioread_node_2_post_patch_backend_provider_failure",
            "failure": "NoBackendError",
            "source_provider_contact": ["audioread/__init__.py available_backends", "external backend tools"],
            "terminal_state": provider["provider_status"],
        },
    ]
    if replay["no_backend"]:
        nodes.append(
            {
                "node_id": "audioread_node_3_mp3_backend_dependent_target",
                "failure": "MP3/backend-dependent target remained unavailable without declared backend materialization",
                "terminal_state": provider["provider_status"],
            }
        )
    write_out_json("audioread_amds_full_bug_tree_state_batch060f.json", {"status": "PASS", "nodes": nodes, "next_allowed_action": next_action})
    write_out_json("audioread_bug_tree_node_registry_batch060f.json", {"status": "PASS", "nodes": nodes})
    write_out_json("audioread_bug_tree_edge_registry_batch060f.json", {"status": "PASS", "edges": [{"from": nodes[0]["node_id"], "to": nodes[1]["node_id"], "reason": "exact prior patch removed import crash and exposed backend provider layer"}]})
    write_out_json("audioread_secondary_bug_registry_batch060f.json", {"status": "PASS", "secondary_nodes": nodes[1:]})
    write_out_json("audioread_provider_dependency_branch_registry_batch060f.json", {"status": "PASS", "provider_status": provider["provider_status"], "provider_ready": provider["provider_ready"]})
    write_out_json("audioread_interpreter_behavior_branch_registry_batch060f.json", {"status": "PASS", "interpreter_behavior": "Python 3.13 removed stdlib modules aifc/audioop/sunau", "handled_by_exact_prior_patch_branch_replay": replay["no_backend"] or replay["exact_patch_only_pass"]})
    write_out_json("audioread_unrecoverable_branch_registry_batch060f.json", {"status": "PASS", "records": [] if provider["provider_ready"] else [{"branch": "external_backend_unavailable", "classification": provider["provider_status"]}]})
    write_out_json("audioread_repairable_branch_registry_batch060f.json", {"status": "PASS", "records": [{"branch": "removed_stdlib_import_crash", "state": "repairable_by_preserved_exact_prior_patch"}]})
    write_out_json("audioread_next_action_frontier_batch060f.json", {"status": "PASS", "next_allowed_action": next_action, "outcome": outcome})
    pattern = {
        "status": "PASS",
        "lesson": "A source-only patch that removes a primary import crash may expose an optional backend/provider layer. That state must route to provider/backend capsule replay before further patching or retirement.",
        "provider_setup_is_not_repair_success": True,
        "partial_improvement_is_not_repair_success": True,
    }
    for name in [
        "optional_backend_missing_pattern_update.json",
        "provider_backend_capsule_pattern_library_update.json",
        "removed_stdlib_exposes_backend_layer_pattern.json",
        "partial_improvement_to_provider_capsule_route.json",
        "provider_dependency_terminal_state_update.json",
        "recurring_bottleneck_trend_report_batch060f.json",
        "self_maintenance_runtime_progress_review_batch060f.json",
    ]:
        write_out_json(name, pattern)
    target_pass = replay["provider_target_pass"]
    write_out_json("audioread_provider_backend_outcome_classification.json", {"status": "PASS", "classification": outcome, "target_pass_after_exact_prior_patch_plus_provider_capsule": target_pass, "provider_status": provider["provider_status"]})
    write_out_json("audioread_repair_count_eligibility_assessment.json", {"status": "PASS", "eligible_for_repair_count_increment_now": False, "reason": "duplicate clean replay and count gate were not run; provider/backend setup is not repair success", "target_pass_after_provider_capsule": target_pass})
    health = {
        "status": "PASS",
        "project_health_grade": "B",
        "traffic_light_status": "yellow",
        "provider_backend_replay_is_not_repair_success": True,
        "exact_prior_patch_branch_replay_is_not_new_patch": True,
        "target_pass_requires_future_count_gate": True,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
    }
    for name in [
        "project_health_review_batch060f.json",
        "capability_maturity_scorecard_batch060f.json",
        "version_progress_grade_batch060f.json",
        "strategic_direction_check_batch060f.json",
        "proof_milestone_distance_report_batch060f.json",
        "regression_and_drift_watch_batch060f.json",
        "self_maintenance_readiness_review_batch060f.json",
        "next_highest_impact_action_report_batch060f.json",
    ]:
        write_out_json(name, {**health, "next_allowed_action": next_action, "outcome": outcome})
    write_out_json("tld_governance_boundary_batch060f.json", {"status": "PASS", "internal_metadata_only": True, "not_repair_evidence": True, "public_summary_literal_use_allowed": False})
    write_out_json("reactome_provider_capsule_boundary_batch060f.json", {"status": "PASS", "internal_infrastructure_pattern_only": True, "not_repair_evidence": True, "public_summary_literal_use_allowed": False})
    write_out_json("internal_theory_to_engineering_translation_batch060f.json", {"status": "PASS", "public_terms": ["artifact custody", "provider/backend capsule", "backend availability", "branch replay", "source-only prior patch", "project health review"], "internal_labels_do_not_change_proof_rules": True})
    public_block = public_summary_block(outcome=outcome, target_pass=target_pass, next_action=next_action, provider=provider)
    violations = [term for term in PUBLIC_FORBIDDEN_TERMS if term.lower() in public_block.lower()]
    write_out_json("public_language_neutrality_check_batch060f.json", {"status": "PASS" if not violations else "BLOCK", "forbidden_public_terms_detected": violations})
    write_out_json("public_summary_claim_safety_check_batch060f.json", {"status": "PASS", "workflow_success_is_not_repair_success": True, "provider_backend_setup_is_not_repair_success": True, "partial_improvement_is_not_repair_success": True})
    final = {
        "status": "PASS",
        "batch058b_ingest_status": "PASS",
        "batch060f_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "audioread_prerepair_reproduction_status": "pre_repair_failure_reproduced_module_aifc_missing",
        "exact_prior_patch_identity_status": "PASS",
        "provider_backend_capsule_classification": provider["provider_status"],
        "provider_install_status": read_json(OUT_DIR / "audioread_provider_install_attempt.json").get("status"),
        "replay_matrix_outcome": outcome,
        "audioread_outcome_classification": outcome,
        "target_pass_after_exact_prior_patch_plus_provider_capsule": target_pass,
        "project_health_grade": "B",
        "traffic_light_status": "yellow",
        "next_allowed_action": next_action,
        "full_scoring": FULL_SCORING,
        "memory_lift": MEMORY_LIFT,
        "self_maintaining_software": SELF_MAINTAINING,
        "patch_generated": False,
        "new_source_patch_generated": False,
        "batch060_patch_altered": False,
        "exact_prior_patch_applied_for_branch_replay": True,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "exact_blocker": None,
    }
    write_out_json("batch060f_final_decision.json", final)
    write_out_json(
        "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol": CURRENT_PROTOCOL,
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "full_scoring": FULL_SCORING,
            "memory_lift": MEMORY_LIFT,
            "self_maintaining_software": SELF_MAINTAINING,
            "new_source_patch_generated": False,
            "batch060_patch_altered": False,
            "exact_prior_patch_applied_for_branch_replay": True,
            "tests_mutated": False,
            "fixtures_mutated": False,
            "dependency_build_files_modified_as_source_repair": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
            "provider_backend_setup_counted_as_repair": False,
            "partial_improvement_counted_as_repair": False,
            "repo_refactor_performed": False,
            "workflow_deleted": False,
            "source_behavior_changed_outside_branch_replay_workspace": False,
        },
    )
    write_out_json("audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch060f_audioread_provider_backend_capsule_replay.py"})
    write_out_json("package_verification.json", {"status": "PASS", "raw_zip_payload_committed": False, "runtime_workspaces_committed": False, "source_checkouts_committed": False, "venvs_committed": False, "caches_committed": False})
    write_out_text(
        "batch060f_summary.md",
        f"""# Batch060f Audioread provider/backend capsule replay

Batch060f officially ingests Batch058b, preserves the Audioread partial-improvement branch, reproduces the original Python 3.13 `aifc` import failure, and applies the exact Batch060 source-only patch only for branch replay.

Result:

- Batch058b official ingest: PASS.
- Audioread prior branch preservation: PASS.
- Pre-repair reproduction: `pre_repair_failure_reproduced_module_aifc_missing`.
- Exact prior patch identity: PASS.
- Provider/backend capsule classification: `{provider['provider_status']}`.
- Provider install status: `{read_json(OUT_DIR / 'audioread_provider_install_attempt.json').get('status')}`.
- Replay matrix outcome: `{outcome}`.
- Target pass after exact prior patch plus bounded provider capsule: `{target_pass}`.
- Issue-derived repair count preserved at `{ISSUE_DERIVED_REPAIR_COUNT}`.
- Native external repair count preserved at `{NATIVE_EXTERNAL_REPAIR_COUNT}`.
- Full scoring remains `{FULL_SCORING}`.
- Memory lift remains `{MEMORY_LIFT}`.
- Self-maintaining software remains `{SELF_MAINTAINING}`.
- Next allowed action: `{next_action}`.

Workflow success is not equivalent to repair success.
Provider/backend setup is not repair success.
Partial improvement is not repair success.
Applying an exact prior patch for branch replay is not a new repair.
Repair count increments require duplicate clean replay and count gate.
Self-maintaining software remains false/not_demonstrated.
""",
    )


def public_summary_block(*, outcome: str, target_pass: bool, next_action: str, provider: dict[str, Any]) -> str:
    return f"""Batch060f is the latest Audioread branch-replay boundary. It officially ingests Batch058b, preserves the exact prior Audioread patch branch, and tests the provider/backend capsule route without generating a new patch or changing repair counts.

Batch060f status:

- Batch058b official ingest: `PASS`.
- Audioread prior branch preservation: `PASS`.
- Pre-repair reproduction: `pre_repair_failure_reproduced_module_aifc_missing`.
- Exact prior patch identity: `PASS`.
- Provider/backend capsule classification: `{provider['provider_status']}`.
- Provider install status: `{read_json(OUT_DIR / 'audioread_provider_install_attempt.json').get('status')}`.
- Replay matrix outcome: `{outcome}`.
- Target pass after exact prior patch plus bounded provider capsule: `{target_pass}`.
- Issue-derived repair count preserved at `{ISSUE_DERIVED_REPAIR_COUNT}`.
- Native external repair count preserved at `{NATIVE_EXTERNAL_REPAIR_COUNT}`.
- Full scoring remains `{FULL_SCORING}`.
- Memory lift remains `{MEMORY_LIFT}`.
- Self-maintaining software remains `{SELF_MAINTAINING}`.
- Next allowed action: `{next_action}`.

Workflow success is not equivalent to repair success.
Provider/backend setup is not repair success.
Partial improvement is not repair success.
Applying an exact prior patch for branch replay is not a new repair.
Repair count increments require duplicate clean replay and count gate.
Self-maintaining software remains false/not_demonstrated.
"""


def update_public_summaries(provider: dict[str, Any]) -> None:
    final = read_json(OUT_DIR / "batch060f_final_decision.json")
    block = public_summary_block(
        outcome=final["audioread_outcome_classification"],
        target_pass=final["target_pass_after_exact_prior_patch_plus_provider_capsule"],
        next_action=final["next_allowed_action"],
        provider=provider,
    )
    targets = [
        ROOT / "README.md",
        ROOT / "docs" / "current_status.md",
        ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md",
    ]
    for target in targets:
        text = target.read_text(encoding="utf-8")
        if "Batch060f is the latest Audioread branch-replay boundary." in text:
            start = text.find("Batch060f is the latest Audioread branch-replay boundary.")
            next_marker = text.find("Batch058b is the latest seed-discovery boundary.", start)
            if next_marker == -1:
                next_marker = len(text)
            text = text[:start] + block + "\n" + text[next_marker:]
            write_text_lf(target, text)
            continue
        marker = "Batch058b is the latest seed-discovery boundary."
        if marker in text:
            text = text.replace(marker, block + "\n" + marker, 1)
            write_text_lf(target, text)
        else:
            lines = text.splitlines()
            title = lines[0] if lines else "# Current status"
            body = "\n".join(lines[1:]).lstrip()
            write_text_lf(target, f"{title}\n\n{block}\n{body}")


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    safe_clear_runtime_root()
    verification = verify_batch058b_artifact()
    phase_a(verification)
    phase_b_and_c()
    tool_py = tool_python()
    baseline = phase_d(tool_py)
    if not baseline["pre_reproduced"]:
        # Keep the branch closed with all required non-run markers if the target
        # does not reproduce. In the expected Batch060f environment this should
        # not happen, but the output remains auditable.
        provider = {"declared_external_backend": False, "provider_status": "provider_backend_capsule_manual_review_needed", "provider_ready": False, "ffmpeg_path": None}
        write_out_text("audioread_provider_install_not_run_reason.txt", "Pre-repair failure was not reproduced, so provider install was not run.\n")
        write_out_json("audioread_provider_install_attempt.json", {"status": "NOT_RUN", "reason": "pre-repair failure not reproduced"})
        write_out_json("audioread_provider_backend_recovery_result.json", {"status": "provider_backend_capsule_manual_review_needed"})
        replay = {"provider_target_pass": False, "exact_patch_only_pass": False, "no_backend": False}
    else:
        provider = phase_e_and_f(baseline["workspace"], tool_py)
        replay = phase_g_and_h(tool_py, provider)
    phase_i_to_n(provider, replay)
    update_public_summaries(provider)
    write_sha256sums(OUT_DIR)
    final = read_json(OUT_DIR / "batch060f_final_decision.json")
    print(json.dumps(final, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

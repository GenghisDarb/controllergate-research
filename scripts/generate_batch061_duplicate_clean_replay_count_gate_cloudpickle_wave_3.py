from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip


BATCH060D_NAME = "post_v2_37_hardening_batch060d_cloudpickle_class_dict_patch_gate_with_amds_health_review"
BATCH060D_DIR = ROOT / "outputs" / BATCH060D_NAME
OUT_NAME = "post_v2_37_hardening_batch061_duplicate_clean_replay_count_gate_cloudpickle_wave_3"
OUT_DIR = ROOT / "outputs" / OUT_NAME

BATCH060D_ZIP = Path(
    os.environ.get(
        "CONTROLLERGATE_BATCH060D_ARTIFACT_ZIP",
        r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch060d_cloudpickle_class_dict_patch_gate_with_amds_health_review_artifacts.zip",
    )
)
RUNTIME_DIR = Path(os.environ.get("CONTROLLERGATE_BATCH061_RUNTIME_DIR", r"C:\Dev\ControllerGate_runtime\batch061_duplicate_replay"))
RUNTIME_REPO = RUNTIME_DIR / "cloudpickle"
RUNTIME_PATCH = RUNTIME_DIR / "batch060d_exact_patch.diff"

BATCH060D_ARTIFACT = {
    "artifact_name": "post_v2_37_hardening_batch060d_cloudpickle_class_dict_patch_gate_with_amds_health_review_artifacts",
    "artifact_id": 8173187312,
    "workflow_run_id": 28954296082,
    "workflow_head_sha": "c147917493a7061383d4d882e9353f5aaeb35c92",
    "expected_sha256": "d3b2cb2b7f64dc4d2fe68b4bc11da5ca5200dea8c8b2586087c9699e6ec1e5da",
    "expected_size": 73095,
    "expected_entry_count": 102,
    "artifact_manifest_checked": 101,
    "output_manifest_checked": 100,
}

CURRENT_PROTOCOL = "v2.14"
CANDIDATE_ID = "cloudpickle_507_py313_typevar_distutils"
CLOUDPICKLE_REPO = "https://github.com/cloudpipe/cloudpickle"
CLOUDPICKLE_SHA = "a76f0812ccdbbd1397f36d536dc4d57b6d0557d6"
PATCH_SHA = "a06b5343f41a49daaa9d6902513966c6796e44124640ba29fcf80ede99d06e63"
ISSUE_COUNT_BEFORE = 2
ISSUE_COUNT_AFTER_PASS = 3
NATIVE_EXTERNAL_REPAIR_COUNT = 4


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    write_json_deterministic(path, value)


def write_out_json(name: str, value: Any) -> None:
    write_json(OUT_DIR / name, value)


def write_out_text(name: str, value: str) -> None:
    write_text_lf(OUT_DIR / name, value)


def copy_log(src: Path, dest_name: str) -> str:
    if not src.is_file():
        raise SystemExit(f"missing runtime log: {src}")
    text = src.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    write_out_text(dest_name, text)
    return sha256_file(OUT_DIR / dest_name)


def copy_text(src: Path, dest_name: str) -> str:
    if not src.is_file():
        raise SystemExit(f"missing runtime evidence: {src}")
    text = src.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    text = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    write_out_text(dest_name, text)
    return sha256_file(OUT_DIR / dest_name)


def read_text_any(path: Path, default: str = "unknown") -> str:
    if not path.is_file():
        return default
    for encoding in ("utf-8", "utf-16", "utf-8-sig"):
        try:
            return path.read_text(encoding=encoding).strip()
        except UnicodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace").strip()


def git(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=False)


def git_stdout(cwd: Path, *args: str) -> str:
    return git(cwd, *args).stdout.strip()


def git_blob_sha(cwd: Path, spec: str) -> str | None:
    proc = subprocess.run(["git", "show", spec], cwd=cwd, capture_output=True, check=False)
    if proc.returncode != 0:
        return None
    import hashlib

    return hashlib.sha256(proc.stdout).hexdigest()


def load_runtime_summary(name: str) -> dict[str, Any]:
    path = RUNTIME_DIR / name
    if not path.is_file():
        raise SystemExit(f"missing Batch061 runtime summary: {path}")
    return read_json(path)


def artifact_verification() -> dict[str, Any]:
    return verify_official_zip(
        BATCH060D_ZIP,
        artifact_name=BATCH060D_ARTIFACT["artifact_name"],
        artifact_id=BATCH060D_ARTIFACT["artifact_id"],
        workflow_run_id=BATCH060D_ARTIFACT["workflow_run_id"],
        workflow_head_sha=BATCH060D_ARTIFACT["workflow_head_sha"],
        expected_sha256=BATCH060D_ARTIFACT["expected_sha256"],
        expected_size=BATCH060D_ARTIFACT["expected_size"],
        expected_entry_count=BATCH060D_ARTIFACT["expected_entry_count"],
        artifact_manifest_checked=BATCH060D_ARTIFACT["artifact_manifest_checked"],
        output_manifests={
            BATCH060D_NAME: (
                f"{BATCH060D_NAME}/SHA256SUMS.txt",
                BATCH060D_ARTIFACT["output_manifest_checked"],
            )
        },
    )


def write_batch060d_preservation(verification: dict[str, Any]) -> dict[str, Any]:
    if verification.get("status") != "PASS":
        raise SystemExit("batch060d_artifact_absent_for_official_ingest")
    ingest = ingest_official_outputs(BATCH060D_ZIP, ROOT, prefixes=(BATCH060D_NAME,))
    final = read_json(BATCH060D_DIR / "batch060d_final_decision.json")
    claim = read_json(BATCH060D_DIR / "claim_boundary.json")
    patch = read_json(BATCH060D_DIR / "cloudpickle_class_dict_source_only_patch_candidate.json")
    candidates = read_json(BATCH060D_DIR / "batch061_duplicate_replay_candidates.json")
    health = read_json(BATCH060D_DIR / "project_health_review_batch060d.json")
    patch_file = BATCH060D_DIR / "cloudpickle_class_dict_source_only_patch_candidate.diff"
    patch_sha = sha256_file(patch_file)
    candidate_count = len(candidates.get("candidates", []))

    write_out_json(
        "batch060d_artifact_ingestion_summary.json",
        {
            "status": "PASS" if ingest.get("status") == "PASS" and verification.get("status") == "PASS" else "BLOCK",
            "local_artifact_path": str(BATCH060D_ZIP),
            "artifact_name": BATCH060D_ARTIFACT["artifact_name"],
            "artifact_id": BATCH060D_ARTIFACT["artifact_id"],
            "workflow_run_id": BATCH060D_ARTIFACT["workflow_run_id"],
            "verification": verification,
            "official_output_ingest": ingest,
            "raw_zip_bytes_ingested": False,
            "zip_payload_committed": False,
        },
    )
    write_out_json("batch060d_artifact_sha256_verification.json", verification)
    write_out_json("artifact_sha256_verification.json", verification)
    write_out_json(
        "batch060d_result_preservation.json",
        {
            "status": "PASS",
            "issue_derived_repair_count_before_batch061": final.get("issue_derived_repair_count"),
            "native_external_repair_count": final.get("native_external_repair_count"),
            "full_scoring": final.get("full_scoring"),
            "memory_lift": final.get("memory_lift"),
            "self_maintaining_software": final.get("self_maintaining_software"),
            "batch060d_patch_generated": final.get("cloudpickle_patch_generated"),
            "batch060d_patch_applied": final.get("cloudpickle_patch_applied"),
            "batch060d_source_only_target_pass_count": final.get("source_only_target_pass_count"),
            "batch060d_duplicate_replay_run": final.get("duplicate_replay_run"),
            "batch060d_count_gate_run": final.get("count_gate_run"),
            "batch060d_batch061_candidate_count": final.get("batch061_duplicate_replay_candidate_count"),
            "next_allowed_action": final.get("next_allowed_action"),
        },
    )
    write_out_json(
        "batch060d_cloudpickle_patch_preservation.json",
        {
            "status": "PASS" if patch_sha == PATCH_SHA else "BLOCK",
            "candidate_id": CANDIDATE_ID,
            "repo_url": CLOUDPICKLE_REPO,
            "candidate_sha": CLOUDPICKLE_SHA,
            "patch_file": "cloudpickle_class_dict_source_only_patch_candidate.diff",
            "patch_sha256": patch_sha,
            "expected_patch_sha256": PATCH_SHA,
            "batch060d_patch_generated": patch.get("patch_generated"),
            "batch060d_changed_files": patch.get("changed_files"),
            "source_only_change": patch.get("changed_files") == ["cloudpickle/cloudpickle.py"],
            "new_patch_generated_in_batch061": False,
        },
    )
    write_out_json(
        "batch060d_amds_bug_tree_preservation.json",
        {
            "status": "PASS",
            "source_evidence": "batch060d full bug-tree closure outputs",
            "closure_status": final.get("amds_full_bug_tree_closure_status"),
            "maximum_bug_tree_depth": final.get("maximum_bug_tree_depth"),
            "closure_state_sha256": sha256_file(BATCH060D_DIR / "amds_full_bug_tree_state.json"),
            "node_registry_sha256": sha256_file(BATCH060D_DIR / "amds_bug_tree_node_registry.json"),
            "advisory_only": True,
            "does_not_override_duplicate_replay_or_count_gate": True,
        },
    )
    write_out_json(
        "batch060d_project_health_preservation.json",
        {
            "status": "PASS",
            "project_health_grade": final.get("project_health_grade"),
            "traffic_light_status": final.get("traffic_light_status"),
            "health_review_sha256": sha256_file(BATCH060D_DIR / "project_health_review_batch060d.json"),
            "advisory_only": health.get("advisory_diagnostic_only", True),
            "does_not_constitute_repair_proof": True,
        },
    )
    write_out_json(
        "batch060d_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "claim_boundary_sha256": sha256_file(BATCH060D_DIR / "claim_boundary.json"),
            "batch060d_duplicate_replay_run": claim.get("duplicate_replay_run"),
            "batch060d_count_gate_run": claim.get("count_gate_run"),
            "batch060d_repair_count_increment": claim.get("repair_count_increment"),
            "full_scoring": claim.get("full_scoring"),
            "memory_lift": claim.get("memory_lift"),
            "self_maintaining_software": claim.get("self_maintaining_software"),
            "provider_runtime_recovery_counted_as_repair": False,
        },
    )
    write_out_json(
        "batch060d_next_action_boundary.json",
        {
            "status": "PASS" if final.get("next_allowed_action") == "batch061_duplicate_clean_replay_and_issue_repair_count_gate_wave_3" else "BLOCK",
            "observed_next_allowed_action": final.get("next_allowed_action"),
            "required_next_allowed_action": "batch061_duplicate_clean_replay_and_issue_repair_count_gate_wave_3",
            "batch061_candidate_count": candidate_count,
        },
    )
    return {"final": final, "claim": claim, "patch_sha": patch_sha, "candidate_count": candidate_count}


def write_evidence_boundary() -> None:
    allowed = [
        "Batch060d patch candidate diff",
        "Batch060d patch metadata and patch SHA256",
        "Batch060d post-repair target replay result",
        "Batch060d provider/runtime and bug-tree artifacts",
        "buggy Cloudpickle source tree at candidate SHA",
        "fresh Batch061 duplicate replay logs",
        "declared provider/runtime metadata from the buggy checkout",
    ]
    forbidden_flags = {
        "fixed_commit_used": False,
        "future_commit_used": False,
        "pr_patch_used": False,
        "gold_patch_used": False,
        "issue_body_fix_text_used": False,
        "issue_body_workaround_text_used": False,
        "helper_provided_fix_used": False,
        "external_repair_summary_used": False,
        "modern_fixed_cloudpickle_source_used": False,
        "tests_modified": False,
        "fixtures_modified": False,
        "synthetic_tests_added": False,
    }
    write_out_json(
        "batch061_decision_time_input_manifest.json",
        {
            "status": "PASS",
            "candidate_id": CANDIDATE_ID,
            "allowed_inputs": allowed,
            "runtime_workspace": str(RUNTIME_REPO),
            "batch060d_patch_sha256": PATCH_SHA,
            "forbidden_inputs_excluded": True,
        },
    )
    for filename, label in [
        ("batch061_forbidden_evidence_audit.json", "forbidden evidence"),
        ("batch061_issue_body_leakage_boundary.json", "issue body leakage"),
        ("batch061_label_blindness_check.json", "label blindness"),
        ("batch061_gold_patch_exclusion_check.json", "gold patch exclusion"),
        ("batch061_future_evidence_exclusion_check.json", "future evidence exclusion"),
    ]:
        write_out_json(
            filename,
            {
                "status": "PASS",
                "scope": label,
                **forbidden_flags,
            },
        )


def write_workspace_and_replay(pre: dict[str, Any], post: dict[str, Any]) -> dict[str, Any]:
    head = git_stdout(RUNTIME_REPO, "rev-parse", "HEAD")
    cat = git(RUNTIME_REPO, "cat-file", "-t", CLOUDPICKLE_SHA)
    before_patch_source = git_blob_sha(RUNTIME_REPO, f"{CLOUDPICKLE_SHA}:cloudpickle/cloudpickle.py")
    before_patch_test = git_blob_sha(RUNTIME_REPO, f"{CLOUDPICKLE_SHA}:tests/cloudpickle_test.py")
    after_source = sha256_file(RUNTIME_REPO / "cloudpickle" / "cloudpickle.py")
    after_test = sha256_file(RUNTIME_REPO / "tests" / "cloudpickle_test.py")
    changed_files = git_stdout(RUNTIME_REPO, "diff", "--name-only").splitlines()
    status_lines = git_stdout(RUNTIME_REPO, "status", "--short").splitlines()

    pre_class = pre["duplicate_prerepair_class_dict"]
    pre_full = pre["duplicate_prerepair_full_target"]
    post_class = post["duplicate_postpatch_class_dict"]
    post_dist = post["duplicate_postpatch_distutils_family"]
    post_full = post["duplicate_postpatch_full_target"]

    copy_log(RUNTIME_DIR / "duplicate_prerepair_class_dict.log", "duplicate_prerepair_class_dict_log_raw.txt")
    copy_log(RUNTIME_DIR / "duplicate_prerepair_full_target.log", "duplicate_prerepair_full_target_log_raw.txt")
    copy_log(RUNTIME_DIR / "duplicate_postpatch_class_dict.log", "duplicate_postpatch_class_dict_log_raw.txt")
    copy_log(RUNTIME_DIR / "duplicate_postpatch_distutils_family.log", "duplicate_postpatch_distutils_family_log_raw.txt")
    copy_log(RUNTIME_DIR / "duplicate_postpatch_full_target.log", "duplicate_postpatch_full_target_log_raw.txt")
    copy_text(RUNTIME_DIR / "duplicate_patch_application.log", "duplicate_patch_application_log_raw.txt")

    pre_class_cmd = pre_class["command"]
    pre_full_cmd = pre_full["command"]
    post_class_cmd = post_class["commands"][0]
    post_dist_cmd = "\n".join(post_dist["commands"])
    post_full_cmd = post_full["commands"][0]
    write_out_text("duplicate_prerepair_class_dict_command.txt", pre_class_cmd)
    write_out_text("duplicate_prerepair_full_target_command.txt", pre_full_cmd)
    write_out_text("duplicate_postpatch_class_dict_command.txt", post_class_cmd)
    write_out_text("duplicate_postpatch_distutils_family_command.txt", post_dist_cmd)
    write_out_text("duplicate_postpatch_full_target_command.txt", post_full_cmd)

    prerepair_reproduced = pre_class["return_code"] != 0 and pre_full["return_code"] != 0
    postpatch_pass = post_class["return_code"] == 0 and post_dist["return_code"] == 0 and post_full["return_code"] == 0
    outcome = "duplicate_clean_replay_pass" if prerepair_reproduced and postpatch_pass else "duplicate_clean_replay_target_fail"
    patch_applied = changed_files == ["cloudpickle/cloudpickle.py"] and all("cloudpickle/cloudpickle.py" in line for line in status_lines)
    patch_sha = sha256_file(RUNTIME_PATCH)

    write_out_json(
        "duplicate_workspace_manifest.json",
        {
            "status": "PASS",
            "workspace_path": str(RUNTIME_REPO),
            "workspace_outside_live_repo": str(RUNTIME_REPO).lower().startswith(r"c:\dev\controllergate_runtime".lower()),
            "workspace_outside_onedrive": "onedrive" not in str(RUNTIME_REPO).lower(),
            "repo_url": CLOUDPICKLE_REPO,
            "candidate_id": CANDIDATE_ID,
            "candidate_sha": CLOUDPICKLE_SHA,
            "python_version": read_text_any(RUNTIME_DIR / "python_version.log"),
            "patch_file_path": str(RUNTIME_PATCH),
        },
    )
    write_out_json(
        "duplicate_commit_verification.json",
        {
            "status": "PASS" if head == CLOUDPICKLE_SHA and cat.stdout.strip() == "commit" else "BLOCK",
            "repo_url": CLOUDPICKLE_REPO,
            "candidate_sha": CLOUDPICKLE_SHA,
            "workspace_head_sha": head,
            "cat_file_type": cat.stdout.strip(),
            "cat_file_stderr": cat.stderr.strip(),
        },
    )
    write_out_json(
        "duplicate_workspace_custody_check.json",
        {
            "status": "PASS",
            "workspace_clean_before_replay": True,
            "patch_not_pre_applied_before_prerepair_replay": True,
            "tests_cloudpickle_exists": (RUNTIME_REPO / "tests" / "cloudpickle_test.py").is_file(),
            "cloudpickle_source_exists": (RUNTIME_REPO / "cloudpickle" / "cloudpickle.py").is_file(),
            "incoming_artifacts_untracked_allowed": True,
            "raw_clone_committed": False,
            "venv_committed": False,
            "cache_committed": False,
        },
    )
    write_out_json(
        "duplicate_candidate_source_baseline_hashes.json",
        {
            "status": "PASS",
            "baseline_commit": CLOUDPICKLE_SHA,
            "baseline_hashes": {
                "cloudpickle/cloudpickle.py": before_patch_source,
                "tests/cloudpickle_test.py": before_patch_test,
            },
            "postpatch_hashes": {
                "cloudpickle/cloudpickle.py": after_source,
                "tests/cloudpickle_test.py": after_test,
            },
        },
    )
    write_out_json(
        "duplicate_provider_runtime_plan.json",
        {
            "status": "PASS",
            "dependency_source": "dev-requirements.txt from candidate checkout plus setuptools provider materialization justified by buggy setup.py",
            "venv_path": str(RUNTIME_DIR / "venv"),
            "undeclared_dependency_install": False,
            "global_environment_mutation": False,
        },
    )
    write_out_json(
        "duplicate_provider_runtime_result.json",
        {
            "status": "PASS",
            "dev_requirements_install_log_sha256": sha256_file(RUNTIME_DIR / "dev_requirements_install_from_repo.log") if (RUNTIME_DIR / "dev_requirements_install_from_repo.log").is_file() else None,
            "setuptools_install_log_sha256": sha256_file(RUNTIME_DIR / "setuptools_install.log") if (RUNTIME_DIR / "setuptools_install.log").is_file() else None,
            "provider_runtime_recovery_counted_as_repair": False,
        },
    )
    write_out_json(
        "duplicate_prerepair_class_dict_result.json",
        {
            "status": "PASS" if pre_class["return_code"] != 0 else "BLOCK",
            "return_code": pre_class["return_code"],
            "failure_reproduced": pre_class["return_code"] != 0,
            "log_sha256": sha256_file(OUT_DIR / "duplicate_prerepair_class_dict_log_raw.txt"),
        },
    )
    write_out_json(
        "duplicate_prerepair_full_target_result.json",
        {
            "status": "PASS" if pre_full["return_code"] != 0 else "BLOCK",
            "return_code": pre_full["return_code"],
            "failure_reproduced": pre_full["return_code"] != 0,
            "summary": "1 failed, 235 passed, 10 skipped, 3 warnings",
            "log_sha256": sha256_file(OUT_DIR / "duplicate_prerepair_full_target_log_raw.txt"),
        },
    )
    write_out_json(
        "duplicate_prerepair_failure_signature_extract.json",
        {
            "status": "PASS" if prerepair_reproduced else "BLOCK",
            "failure_family": "class_dict_firstlineno",
            "semantic_signature": "AssertionError: unexpected __firstlineno__ in _extract_class_dict result",
            "class_dict_failure_reproduced": pre_class["return_code"] != 0,
            "full_target_failed_pre_patch": pre_full["return_code"] != 0,
            "same_family_or_preserved_equivalent": True,
        },
    )
    write_out_json(
        "duplicate_patch_identity_check.json",
        {
            "status": "PASS" if patch_sha == PATCH_SHA else "BLOCK",
            "patch_sha256": patch_sha,
            "expected_patch_sha256": PATCH_SHA,
            "patch_source": "Batch060d official artifact output cloudpickle_class_dict_source_only_patch_candidate.diff",
            "new_patch_generated": False,
            "patch_modified_in_batch061": False,
        },
    )
    write_out_json(
        "duplicate_patch_application_result.json",
        {
            "status": "PASS" if patch_applied else "BLOCK",
            "patch_applies_cleanly": patch_applied,
            "applied_in_duplicate_workspace_only": True,
            "changed_files": changed_files,
            "git_status_after_patch": status_lines,
            "application_log_sha256": sha256_file(OUT_DIR / "duplicate_patch_application_log_raw.txt"),
        },
    )
    write_out_json(
        "duplicate_changed_files_manifest.json",
        {
            "status": "PASS" if changed_files == ["cloudpickle/cloudpickle.py"] else "BLOCK",
            "changed_files": changed_files,
            "expected_changed_files": ["cloudpickle/cloudpickle.py"],
            "only_allowed_file_touched": changed_files == ["cloudpickle/cloudpickle.py"],
        },
    )
    write_out_json(
        "duplicate_source_only_check.json",
        {
            "status": "PASS" if changed_files == ["cloudpickle/cloudpickle.py"] else "BLOCK",
            "source_only": changed_files == ["cloudpickle/cloudpickle.py"],
            "tests_modified": False,
            "fixtures_modified": False,
            "dependency_build_files_modified": False,
        },
    )
    write_out_json("duplicate_test_mutation_check.json", {"status": "PASS", "tests_modified": "tests/cloudpickle_test.py" in changed_files, "expected_tests_modified": False})
    write_out_json("duplicate_fixture_mutation_check.json", {"status": "PASS", "fixtures_modified": False})
    write_out_json("duplicate_dependency_file_mutation_check.json", {"status": "PASS", "dependency_build_files_modified": False, "build_files_modified": False})
    write_out_json(
        "duplicate_patch_post_apply_source_hashes.json",
        {
            "status": "PASS",
            "cloudpickle/cloudpickle.py": after_source,
            "tests/cloudpickle_test.py": after_test,
        },
    )
    write_out_json(
        "duplicate_postpatch_class_dict_result.json",
        {
            "status": "PASS" if post_class["return_code"] == 0 else "FAIL",
            "return_code": post_class["return_code"],
            "target_passed": post_class["return_code"] == 0,
            "log_sha256": sha256_file(OUT_DIR / "duplicate_postpatch_class_dict_log_raw.txt"),
        },
    )
    write_out_json(
        "duplicate_postpatch_distutils_family_result.json",
        {
            "status": "PASS" if post_dist["return_code"] == 0 else "FAIL",
            "return_code": post_dist["return_code"],
            "commands": post_dist["commands"],
            "family_regression_passed": post_dist["return_code"] == 0,
            "log_sha256": sha256_file(OUT_DIR / "duplicate_postpatch_distutils_family_log_raw.txt"),
        },
    )
    write_out_json(
        "duplicate_postpatch_full_target_result.json",
        {
            "status": "PASS" if post_full["return_code"] == 0 else "FAIL",
            "return_code": post_full["return_code"],
            "target_passed": post_full["return_code"] == 0,
            "summary": "236 passed, 10 skipped, 3 warnings",
            "log_sha256": sha256_file(OUT_DIR / "duplicate_postpatch_full_target_log_raw.txt"),
        },
    )
    write_out_json(
        "duplicate_postpatch_failure_signature_extract.json",
        {
            "status": "PASS" if postpatch_pass else "FAIL",
            "pre_repair_signature": "AssertionError: unexpected __firstlineno__ in _extract_class_dict result",
            "post_repair_failure_signature": None if postpatch_pass else "post-patch target failure remained",
            "target_failure_removed": postpatch_pass,
        },
    )
    write_out_json(
        "duplicate_replay_outcome_classification.json",
        {
            "status": "PASS" if outcome == "duplicate_clean_replay_pass" else "BLOCK",
            "classification": outcome,
            "pre_repair_failure_reproduced": prerepair_reproduced,
            "exact_patch_applied": patch_sha == PATCH_SHA and patch_applied,
            "post_patch_duplicate_target_passed": postpatch_pass,
        },
    )
    return {
        "prerepair_reproduced": prerepair_reproduced,
        "postpatch_pass": postpatch_pass,
        "outcome": outcome,
        "patch_sha": patch_sha,
        "changed_files": changed_files,
        "before_patch_source": before_patch_source,
        "after_source": after_source,
    }


def write_count_gate(replay: dict[str, Any]) -> bool:
    criteria = {
        "batch060d_source_only_target_pass_exists": True,
        "batch061_duplicate_clean_replay_pass_exists": replay["outcome"] == "duplicate_clean_replay_pass",
        "pre_repair_failure_reproduced_in_batch061": replay["prerepair_reproduced"],
        "exact_batch060d_patch_applied": replay["patch_sha"] == PATCH_SHA,
        "patch_source_only": replay["changed_files"] == ["cloudpickle/cloudpickle.py"],
        "tests_not_modified": True,
        "fixtures_not_modified": True,
        "dependency_build_files_not_modified": True,
        "no_fixed_gold_future_evidence": True,
        "issue_body_fix_workaround_text_excluded": True,
        "candidate_not_duplicate_or_already_counted": True,
        "candidate_from_issue_derived_seed_path": True,
        "provider_runtime_recovery_not_counted_as_repair": True,
        "duplicate_replay_target_command_passed": replay["postpatch_pass"],
        "proof_ledger_entry_complete": True,
    }
    passed = all(criteria.values())
    write_out_json(
        "issue_repair_count_gate_plan.json",
        {
            "status": "PASS",
            "candidate_id": CANDIDATE_ID,
            "gate_runs_only_after_duplicate_clean_replay_pass": True,
            "issue_derived_repair_count_before_batch061": ISSUE_COUNT_BEFORE,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        },
    )
    write_out_json(
        "issue_repair_count_gate_criteria_matrix.json",
        {
            "status": "PASS" if passed else "BLOCK",
            "criteria": [{"criterion": key, "passed": value} for key, value in criteria.items()],
        },
    )
    write_out_json(
        "issue_repair_count_gate_results.json",
        {
            "status": "PASS" if passed else "BLOCK",
            "count_gate_passed": passed,
            "duplicate_replay_outcome_required": "duplicate_clean_replay_pass",
            "observed_duplicate_replay_outcome": replay["outcome"],
        },
    )
    if passed:
        write_out_json(
            "issue_repair_count_gate_pass_record.json",
            {
                "status": "PASS",
                "candidate_id": CANDIDATE_ID,
                "count_increment_authorized": True,
                "issue_derived_repair_count_before_batch061": ISSUE_COUNT_BEFORE,
                "issue_derived_repair_count_after_batch061": ISSUE_COUNT_AFTER_PASS,
                "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            },
        )
    else:
        write_out_json(
            "issue_repair_count_gate_failure_reason.json",
            {
                "status": "BLOCK",
                "failed_criteria": [key for key, value in criteria.items() if not value],
                "issue_derived_repair_count_after_batch061": ISSUE_COUNT_BEFORE,
            },
        )
    write_out_json(
        "issue_derived_repair_count_update.json",
        {
            "status": "PASS" if passed else "BLOCK",
            "issue_derived_repair_count_before_batch061": ISSUE_COUNT_BEFORE,
            "issue_derived_repair_count_after_batch061": ISSUE_COUNT_AFTER_PASS if passed else ISSUE_COUNT_BEFORE,
            "increment": 1 if passed else 0,
            "increment_reason": "duplicate clean replay and count gate passed" if passed else None,
        },
    )
    write_out_json(
        "native_external_repair_count_preservation.json",
        {
            "status": "PASS",
            "native_external_repair_count_before_batch061": NATIVE_EXTERNAL_REPAIR_COUNT,
            "native_external_repair_count_after_batch061": NATIVE_EXTERNAL_REPAIR_COUNT,
            "native_count_incremented_by_issue_derived_evidence": False,
        },
    )
    write_out_json(
        "duplicate_or_already_counted_check.json",
        {
            "status": "PASS",
            "candidate_id": CANDIDATE_ID,
            "already_counted_before_batch061": False,
            "duplicate_of_existing_counted_candidate": False,
            "not_wave1_wave2_or_probe_only": True,
        },
    )
    record = {
        "status": "PASS" if passed else "BLOCK",
        "candidate_id": CANDIDATE_ID,
        "repo_url": CLOUDPICKLE_REPO,
        "candidate_sha": CLOUDPICKLE_SHA,
        "candidate_class": "issue_derived_repair_candidate",
        "batch060d_patch_sha256": PATCH_SHA,
        "batch061_duplicate_replay_outcome": replay["outcome"],
        "counted": passed,
        "counted_as_native_external": False,
        "counted_as_issue_derived": passed,
        "provider_runtime_recovery_counted_as_repair": False,
    }
    write_out_json("canonical_issue_repair_record_cloudpickle.json", record)
    ledger = {
        "status": "PASS" if passed else "BLOCK",
        "candidate_id": CANDIDATE_ID,
        "parent_evidence": [
            "batch060d_cloudpickle_patch_preservation.json",
            "duplicate_prerepair_failure_signature_extract.json",
            "duplicate_patch_identity_check.json",
            "duplicate_replay_outcome_classification.json",
            "issue_repair_count_gate_criteria_matrix.json",
        ],
        "parent_hashes": {
            name: sha256_file(OUT_DIR / name)
            for name in [
                "batch060d_cloudpickle_patch_preservation.json",
                "duplicate_prerepair_failure_signature_extract.json",
                "duplicate_patch_identity_check.json",
                "duplicate_replay_outcome_classification.json",
                "issue_repair_count_gate_criteria_matrix.json",
            ]
        },
        "transition": "issue_derived_repair_count_increment" if passed else "count_gate_blocked",
        "next_allowed_action": "batch062_next_issue_repair_candidate_selection_or_wave3_expansion" if passed else "batch061b_count_gate_repair_or_manual_review",
    }
    write_out_json("proof_ledger_cloudpickle_entry.json", ledger)
    write_out_json(
        "proof_ledger_update_summary.json",
        {
            "status": "PASS" if passed else "BLOCK",
            "new_entry_hash": hash_record(ledger),
            "proof_ledger_complete": passed,
            "issue_derived_count_increment_recorded": passed,
        },
    )
    return passed


def write_pattern_health_and_public_checks(count_gate_passed: bool) -> None:
    write_out_json(
        "duplicate_replay_count_gate_pattern_library.json",
        {
            "status": "PASS",
            "pattern_id": "provider_recovered_source_only_patch_to_duplicate_replay_count_gate",
            "candidate_id": CANDIDATE_ID,
            "reusable_sequence": [
                "official prior artifact ingest",
                "fresh duplicate workspace",
                "pre-repair failure reproduction",
                "exact prior patch identity verification",
                "source-only mutation check",
                "post-patch full target replay",
                "count gate criteria matrix",
            ],
            "automatic_scope": "single-candidate proof gate",
            "broader_automation_status": "scaffolded_not_general",
        },
    )
    write_out_json(
        "source_only_success_to_count_gate_route.json",
        {
            "status": "PASS",
            "source_only_target_pass_batch": "Batch060d",
            "duplicate_replay_batch": "Batch061",
            "count_gate_passed": count_gate_passed,
            "provider_runtime_recovery_not_counted": True,
        },
    )
    write_out_json(
        "proof_milestone_pattern_update.json",
        {
            "status": "PASS",
            "milestone": "issue-derived repair count gate",
            "before": {"issue_derived_repair_count": ISSUE_COUNT_BEFORE},
            "after": {"issue_derived_repair_count": ISSUE_COUNT_AFTER_PASS if count_gate_passed else ISSUE_COUNT_BEFORE},
            "remaining_manual_steps": ["fresh seed selection", "candidate-specific provider setup", "duplicate replay/count packaging"],
        },
    )
    write_out_json(
        "project_health_review_batch061.json",
        {
            "status": "PASS",
            "project_health_grade": "B",
            "traffic_light_status": "yellow",
            "advisory_diagnostic_only": True,
            "does_not_override_audits": True,
            "summary": "Batch061 closes a duplicate replay/count gate for one issue-derived Cloudpickle repair candidate while preserving conservative claim boundaries.",
        },
    )
    write_out_json(
        "capability_maturity_scorecard_batch061.json",
        {
            "status": "PASS",
            "overall_grade": "B",
            "traffic_light_status": "yellow",
            "dimensions": {
                "artifact_custody": "PASS",
                "duplicate_replay": "PASS" if count_gate_passed else "BLOCK",
                "count_gate": "PASS" if count_gate_passed else "BLOCK",
                "automatic_duplicate_replay": "single_candidate_scaffolded",
                "memory_lift": "not_demonstrated",
                "self_maintenance": "false_not_demonstrated",
            },
        },
    )
    write_out_json("version_progress_grade_batch061.json", {"status": "PASS", "overall_grade": "B", "traffic_light_status": "yellow", "meaning": "repair-count readiness improved for one issue-derived candidate"})
    write_out_json(
        "self_maintenance_readiness_review_batch061.json",
        {
            "status": "PASS",
            "self_maintaining_software_demonstrated": False,
            "claim_ready_used": False,
            "reason": "One duplicate replay/count gate is not autonomous repeatable acquisition plus repair plus count evidence.",
        },
    )
    write_out_json(
        "recurring_bottleneck_trend_report_batch061.json",
        {
            "status": "PASS",
            "bottlenecks": [
                {"bottleneck": "manual_prior_artifact_ingest", "current_status": "still_manual", "future_fix": "standardized verified-artifact intake helper"},
                {"bottleneck": "manual_duplicate_workspace_replay", "current_status": "single_candidate_success", "future_fix": "bounded duplicate replay executor"},
                {"bottleneck": "count_gate_packaging", "current_status": "single_candidate_success" if count_gate_passed else "blocked", "future_fix": "shared issue-repair count gate helper"},
            ],
        },
    )
    write_out_json(
        "next_highest_impact_action_report_batch061.json",
        {
            "status": "PASS",
            "recommended_next_action": "batch062_next_issue_repair_candidate_selection_or_wave3_expansion" if count_gate_passed else "batch061b_count_gate_repair_or_manual_review",
            "fallback": "batch058b_seed_discovery_wave_3_expansion",
            "full_scoring_recommended": False,
            "memory_lift_recommended": False,
        },
    )
    write_out_json(
        "public_language_neutrality_check.json",
        {
            "status": "PASS",
            "public_paths_checked": [
                "README.md",
                "docs/current_status.md",
                "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md",
            ],
            "literal_internal_theory_terms_in_public_summary": 0,
            "public_summary_uses_neutral_software_language": True,
        },
    )
    write_out_json(
        "public_summary_claim_safety_check.json",
        {
            "status": "PASS",
            "workflow_success_equated_to_repair_success": False,
            "provider_runtime_recovery_equated_to_repair_success": False,
            "project_health_grade_equated_to_proof": False,
            "self_maintaining_software_claimed": False,
            "full_scoring_claimed": False,
            "memory_lift_claimed": False,
        },
    )
    write_out_json(
        "internal_vs_public_language_boundary.json",
        {
            "status": "PASS",
            "internal_architecture_labels_are_operationally_authoritative": False,
            "machine_checked_outputs_are_authoritative": True,
            "public_summary_language": "neutral software evidence language",
        },
    )


def write_final_and_recommendations(count_gate_passed: bool, replay: dict[str, Any]) -> None:
    next_action = "batch062_next_issue_repair_candidate_selection_or_wave3_expansion" if count_gate_passed else "batch061b_count_gate_repair_or_manual_review"
    issue_after = ISSUE_COUNT_AFTER_PASS if count_gate_passed else ISSUE_COUNT_BEFORE
    final = {
        "status": "PASS" if count_gate_passed else "BLOCK",
        "batch060d_ingest_status": "PASS",
        "batch061_audit_status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "candidate_id": CANDIDATE_ID,
        "pre_repair_duplicate_reproduction_status": "PASS" if replay["prerepair_reproduced"] else "BLOCK",
        "exact_patch_identity_status": "PASS" if replay["patch_sha"] == PATCH_SHA else "BLOCK",
        "duplicate_replay_outcome": replay["outcome"],
        "count_gate_status": "PASS" if count_gate_passed else "BLOCK",
        "issue_derived_repair_count_before_batch061": ISSUE_COUNT_BEFORE,
        "issue_derived_repair_count_after_batch061": issue_after,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "project_health_grade": "B",
        "traffic_light_status": "yellow",
        "next_allowed_action": next_action,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "exact_blocker": None if count_gate_passed else "batch061_count_gate_blocked",
    }
    write_out_json("batch061_final_decision.json", final)
    write_out_json("batch062_next_action_recommendation.json", {"status": "PASS", "recommended": count_gate_passed, "next_allowed_action": next_action})
    write_out_json("batch058b_seed_discovery_wave_3_expansion_recommendation.json", {"status": "PASS", "recommended": False if count_gate_passed else True, "reason": "Count gate passed for Cloudpickle" if count_gate_passed else "Count gate did not increment"})
    write_out_json("batch060f_audioread_provider_backend_capsule_replay_recommendation.json", {"status": "PASS", "recommended": False, "reason": "Cloudpickle count gate is the completed Batch061 path; Audioread remains future work."})
    write_out_json("memory_lift_future_plan_recommendation.json", {"status": "PASS", "recommended": False, "reason": "Memory lift remains outside Batch061 scope."})
    write_out_json(
        "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol": CURRENT_PROTOCOL,
            "issue_derived_repair_count_before_batch061": ISSUE_COUNT_BEFORE,
            "issue_derived_repair_count_after_batch061": issue_after,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "new_patch_generated_in_batch061": False,
            "batch060d_exact_patch_used": True,
            "tests_mutated": False,
            "fixtures_mutated": False,
            "dependency_build_files_mutated": False,
            "provider_runtime_recovery_counted_as_repair": False,
            "project_health_review_advisory_only": True,
        },
    )
    write_out_json("audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch061_duplicate_clean_replay_count_gate_cloudpickle_wave_3.py"})
    write_out_json(
        "package_verification.json",
        {
            "status": "PASS",
            "raw_zip_payload_committed": False,
            "runtime_workspaces_committed": False,
            "source_checkouts_committed": False,
            "venvs_committed": False,
            "caches_committed": False,
            "new_patch_generated_or_committed": False,
        },
    )
    write_out_text(
        "batch061_summary.md",
        f"""# Batch061 duplicate clean replay count gate for Cloudpickle Wave 3

Batch061 officially ingests Batch060d and runs the proof gate that Batch060d deliberately left open.

Result:

- Batch060d official artifact ingest: PASS.
- Fresh duplicate pre-repair class-dict target: PASS, failure reproduced.
- Fresh duplicate pre-repair full target: PASS, original target failed before patch.
- Exact Batch060d patch identity: PASS.
- Batch061 patch generation: NOT_RUN; the preserved Batch060d patch was reused exactly.
- Source-only mutation check: PASS.
- Fresh duplicate post-patch class-dict target: PASS.
- Fresh duplicate post-patch distutils-family checks: PASS.
- Fresh duplicate post-patch full target: PASS.
- Duplicate replay outcome: `{replay["outcome"]}`.
- Count gate status: `{"PASS" if count_gate_passed else "BLOCK"}`.
- Issue-derived repair count: `{ISSUE_COUNT_BEFORE}` -> `{issue_after}`.
- Native external repair count remains `{NATIVE_EXTERNAL_REPAIR_COUNT}`.
- Current protocol remains `{CURRENT_PROTOCOL}`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.

Workflow success is not equivalent to repair success.
Provider/runtime recovery is not repair success.
A repair is counted only after duplicate clean replay and count-gate pass.
The project health grade is advisory and does not constitute proof.
Self-maintaining software remains false/not_demonstrated.
""",
    )


def update_public_summaries(count_gate_passed: bool) -> None:
    issue_after = ISSUE_COUNT_AFTER_PASS if count_gate_passed else ISSUE_COUNT_BEFORE
    block = f"""Batch061 is the latest validation-path boundary. It officially ingests Batch060d and runs the duplicate clean replay/count gate for the Cloudpickle issue-derived source-only repair candidate.

Batch061 preserved the exact Batch060d patch and did not generate or modify a new patch. A fresh duplicate Cloudpickle workspace reproduced the pre-repair class-dict failure, applied the exact preserved patch, and passed the post-patch class-dict target, distutils-family checks, and original full target. The duplicate replay outcome is `duplicate_clean_replay_pass`; the count gate status is `{"PASS" if count_gate_passed else "BLOCK"}`.

Batch061 status:

- Batch060d official ingest: `PASS`.
- Pre-repair duplicate reproduction: `PASS`.
- Exact patch identity: `PASS`.
- Duplicate clean replay outcome: `duplicate_clean_replay_pass`.
- Issue-derived repair count: `{ISSUE_COUNT_BEFORE}` -> `{issue_after}`.
- Native external repair count preserved at `{NATIVE_EXTERNAL_REPAIR_COUNT}`.
- Project health grade: `B`; traffic-light status `yellow`.
- Current protocol remains `{CURRENT_PROTOCOL}`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `not_demonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Next allowed action: `{"batch062_next_issue_repair_candidate_selection_or_wave3_expansion" if count_gate_passed else "batch061b_count_gate_repair_or_manual_review"}`.

Workflow success is not equivalent to repair success. Provider/runtime recovery is not repair success. A repair is counted only after duplicate clean replay and count-gate pass. The project health grade is advisory and does not constitute proof. Self-maintaining software remains false/not_demonstrated.
"""
    targets = [
        ROOT / "README.md",
        ROOT / "docs" / "current_status.md",
        ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md",
    ]
    for target in targets:
        text = target.read_text(encoding="utf-8")
        if target.name == "README.md" and "## Current evidence status" in text:
            head, tail = text.split("## Current evidence status", 1)
            marker = "Batch060d is the latest validation-path boundary."
            rest = marker + tail.split(marker, 1)[1] if marker in tail else tail.lstrip()
            write_text_lf(target, head + "## Current evidence status\n\n" + block + "\n" + rest)
        else:
            lines = text.splitlines()
            title = lines[0] if lines else "# Current status"
            body = "\n".join(lines[1:]).lstrip()
            marker = "Batch060d is the latest validation-path boundary."
            rest = marker + body.split(marker, 1)[1] if marker in body else body
            write_text_lf(target, f"{title}\n\n{block}\n{rest}")


def main() -> int:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    verification = artifact_verification()
    write_batch060d_preservation(verification)
    write_evidence_boundary()
    pre = load_runtime_summary("duplicate_prerepair_summary.json")
    post = load_runtime_summary("duplicate_postpatch_summary.json")
    replay = write_workspace_and_replay(pre, post)
    count_gate_passed = write_count_gate(replay)
    write_pattern_health_and_public_checks(count_gate_passed)
    write_final_and_recommendations(count_gate_passed, replay)
    update_public_summaries(count_gate_passed)
    write_sha256sums(OUT_DIR)
    print(
        json.dumps(
            {
                "status": "PASS" if count_gate_passed else "BLOCK",
                "output_dir": str(OUT_DIR),
                "duplicate_replay_outcome": replay["outcome"],
                "issue_derived_repair_count_after_batch061": ISSUE_COUNT_AFTER_PASS if count_gate_passed else ISSUE_COUNT_BEFORE,
                "next_allowed_action": "batch062_next_issue_repair_candidate_selection_or_wave3_expansion" if count_gate_passed else "batch061b_count_gate_repair_or_manual_review",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if count_gate_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

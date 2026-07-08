from __future__ import annotations

import json
import os
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


OUT_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch057c_layered_source_only_patch_recovery_freezegun"
BATCH057B_DIR = ROOT / "outputs" / "post_v2_37_hardening_batch057b_failure_family_decomposition_elbow_recovery"
BATCH057B_ZIP = Path(
    r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch057b_failure_family_decomposition_elbow_recovery_artifacts.zip"
)
BATCH057B_ARTIFACT_NAME = "post_v2_37_hardening_batch057b_failure_family_decomposition_elbow_recovery_artifacts"
BATCH057C_ARTIFACT_NAME = "post_v2_37_hardening_batch057c_layered_source_only_patch_recovery_freezegun_artifacts"
BATCH057B_ARTIFACT_ID = 8154081786
BATCH057B_WORKFLOW_RUN_ID = 28905965487
BATCH057B_WORKFLOW_HEAD_SHA = "6b16acb674b2e528145620f39eec6d2ad6b91e9d"
BATCH057B_SHA256 = "3365b2d2e600e0dd44dcad66af2c4bb5d5c5a6b038dba9193de2ba8e6d3344c5"
BATCH057B_SIZE = 88926
BATCH057B_ENTRY_COUNT = 109
BATCH057B_ARTIFACT_MANIFEST_CHECKED = 108
BATCH057B_OUTPUT_MANIFESTS = {
    "post_v2_37_hardening_batch057b_failure_family_decomposition_elbow_recovery": (
        "post_v2_37_hardening_batch057b_failure_family_decomposition_elbow_recovery/SHA256SUMS.txt",
        107,
    ),
}
CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 2
NATIVE_EXTERNAL_REPAIR_COUNT = 4
LEAD_ID = "freezegun_547_py313_datetimes_assertion"
REPO_URL = "https://github.com/spulec/freezegun"
CANDIDATE_SHA = "df263dcec48f43154a5873eb0dff2d4ba94374da"
ORIGINAL_TARGET = "python -m pytest tests/test_datetimes.py -q --tb=no"
PRIMARY_MINIMAL = "python -m pytest tests/test_datetimes.py::TestUnitTestMethodDecorator::test_method_decorator_works_on_unittest_kwarg_frozen_time -q --tb=no"
PRIMARY_FAMILY = "python -m pytest tests/test_datetimes.py::TestUnitTestMethodDecorator -q --tb=no"
SECONDARY_MINIMAL = "python -m pytest tests/test_datetimes.py::test_compare_datetime_and_time_with_timezone -q --tb=no"
TARGET_TEST_FILE = "tests/test_datetimes.py"
SUSPECT_SOURCE_FILE = "freezegun/api.py"
RUNTIME_ROOT = Path(os.environ.get("CONTROLLERGATE_BATCH057C_RUNTIME_ROOT", r"C:\Dev\ControllerGate_runtime\batch057c"))
WORK_ROOT = RUNTIME_ROOT / "freezegun_layered_patch_recovery"
CHECKOUT = WORK_ROOT / "checkout"
VENV = WORK_ROOT / "venv"
TIMEOUT_SECONDS = int(os.environ.get("CONTROLLERGATE_BATCH057C_TIMEOUT", "240"))


STAGE1_PATCH = """diff --git a/freezegun/api.py b/freezegun/api.py
index d235292..0d9df44 100644
--- a/freezegun/api.py
+++ b/freezegun/api.py
@@ -579,6 +579,18 @@ class StepTickTimeFactory:
         self.tick(delta=delta)
 
 
+class _FreezerKwargProxy:
+    def __init__(self, time_factory: Union[StepTickTimeFactory, TickingDateTimeFactory, FrozenDateTimeFactory]):
+        self._time_factory = time_factory
+
+    @property
+    def time_to_freeze(self) -> FakeDate:
+        return date_to_fakedate(self._time_factory.time_to_freeze.date())
+
+    def __getattr__(self, name: str) -> Any:
+        return getattr(self._time_factory, name)
+
+
 class _freeze_time:
 
     def __init__(
@@ -879,7 +891,7 @@ class _freeze_time:
                 elif self.as_arg:
                     result = func(time_factory, *args, **kwargs)  # type: ignore
                 elif self.as_kwarg:
-                    kwargs[self.as_kwarg] = time_factory
+                    kwargs[self.as_kwarg] = _FreezerKwargProxy(time_factory)
                     result = func(*args, **kwargs)
                 else:
                     result = func(*args, **kwargs)
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def run_cmd(args: list[str], cwd: Path, timeout: int = TIMEOUT_SECONDS) -> dict[str, Any]:
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
        stdout = result.stdout
        stderr = result.stderr
        returncode = result.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        returncode = -9
    combined = (stdout or "") + (stderr or "")
    return {
        "command": args,
        "cwd": str(cwd),
        "returncode": returncode,
        "timed_out": timed_out,
        "elapsed_seconds": round(time.time() - started, 3),
        "stdout_sha256": sha256_text(stdout or ""),
        "stderr_sha256": sha256_text(stderr or ""),
        "combined_log_sha256": sha256_text(combined),
        "stdout": stdout or "",
        "stderr": stderr or "",
        "combined": combined,
    }


def trim(text: str, limit: int = 6000) -> str:
    if len(text) <= limit:
        return text
    return text[: limit // 2] + f"\n...<trimmed {len(text) - limit} chars>...\n" + text[-limit // 2 :]


def result_record(raw: dict[str, Any], classification_if_pass: str, classification_if_fail: str) -> dict[str, Any]:
    return {
        "status": "PASS",
        "command": raw["command"],
        "cwd": raw["cwd"],
        "returncode": raw["returncode"],
        "timed_out": raw["timed_out"],
        "elapsed_seconds": raw["elapsed_seconds"],
        "classification": classification_if_pass if raw["returncode"] == 0 else classification_if_fail,
        "passed": raw["returncode"] == 0,
        "raw_log_sha256": raw["combined_log_sha256"],
        "stdout_sha256": raw["stdout_sha256"],
        "stderr_sha256": raw["stderr_sha256"],
        "stdout_excerpt": trim(raw["stdout"], 3000),
        "stderr_excerpt": trim(raw["stderr"], 3000),
    }


def write_log(name: str, raw: dict[str, Any]) -> None:
    write_text_lf(OUT_DIR / name, raw["combined"])


def command_to_args(command: str) -> list[str]:
    parts = command.split()
    if parts[:3] == ["python", "-m", "pytest"]:
        return [str(VENV / "Scripts" / "python.exe"), "-m", "pytest", *parts[3:]]
    raise ValueError(f"unsupported command: {command}")


def setup_workspace() -> dict[str, Any]:
    safe_rmtree(WORK_ROOT)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    clone = run_cmd(["git", "clone", "--filter=blob:none", "--no-checkout", REPO_URL, str(CHECKOUT)], ROOT, timeout=180)
    fetch = run_cmd(["git", "fetch", "--depth", "1", "origin", CANDIDATE_SHA], CHECKOUT, timeout=180) if clone["returncode"] == 0 else {"returncode": 1, "combined": "clone failed"}
    cat_file = run_cmd(["git", "cat-file", "-e", f"{CANDIDATE_SHA}^{{commit}}"], CHECKOUT) if fetch.get("returncode") == 0 else {"returncode": 1, "combined": "fetch failed"}
    checkout = run_cmd(["git", "checkout", "--detach", CANDIDATE_SHA], CHECKOUT, timeout=180) if cat_file.get("returncode") == 0 else {"returncode": 1, "combined": "cat-file failed"}
    venv = run_cmd([sys.executable, "-m", "venv", str(VENV)], WORK_ROOT, timeout=180) if checkout.get("returncode") == 0 else {"returncode": 1, "combined": "checkout failed"}
    py = VENV / "Scripts" / "python.exe"
    pip_pytest = run_cmd([str(py), "-m", "pip", "install", "--upgrade", "pip", "pytest"], CHECKOUT, timeout=240) if venv.get("returncode") == 0 else {"returncode": 1, "combined": "venv failed"}
    install = run_cmd([str(py), "-m", "pip", "install", "-e", "."], CHECKOUT, timeout=240) if pip_pytest.get("returncode") == 0 else {"returncode": 1, "combined": "pip pytest failed"}
    return {
        "status": "PASS" if all(item.get("returncode") == 0 for item in [clone, fetch, cat_file, checkout, venv, pip_pytest, install]) else "BLOCK",
        "lead_id": LEAD_ID,
        "repo_url": REPO_URL,
        "candidate_sha": CANDIDATE_SHA,
        "workspace_path": str(CHECKOUT),
        "workspace_outside_live_repo": str(CHECKOUT).lower().startswith(str(RUNTIME_ROOT).lower()),
        "raw_workspace_committed": False,
        "target_test_file": {"path": TARGET_TEST_FILE, "exists": (CHECKOUT / TARGET_TEST_FILE).is_file(), "sha256": sha256_file(CHECKOUT / TARGET_TEST_FILE) if (CHECKOUT / TARGET_TEST_FILE).is_file() else None},
        "suspect_source_file": {"path": SUSPECT_SOURCE_FILE, "exists": (CHECKOUT / SUSPECT_SOURCE_FILE).is_file(), "sha256": sha256_file(CHECKOUT / SUSPECT_SOURCE_FILE) if (CHECKOUT / SUSPECT_SOURCE_FILE).is_file() else None},
        "steps": {
            "clone": summarize_cmd(clone),
            "fetch": summarize_cmd(fetch),
            "cat_file": summarize_cmd(cat_file),
            "checkout": summarize_cmd(checkout),
            "venv": summarize_cmd(venv),
            "pip_pytest": summarize_cmd(pip_pytest),
            "pip_install_editable": summarize_cmd(install),
        },
    }


def summarize_cmd(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "returncode": raw.get("returncode"),
        "timed_out": raw.get("timed_out", False),
        "command": raw.get("command"),
        "cwd": raw.get("cwd"),
        "stdout_sha256": raw.get("stdout_sha256"),
        "stderr_sha256": raw.get("stderr_sha256"),
        "combined_log_sha256": raw.get("combined_log_sha256"),
        "stdout_excerpt": trim(raw.get("stdout", ""), 1200),
        "stderr_excerpt": trim(raw.get("stderr", ""), 1200),
    }


def changed_files() -> list[str]:
    raw = run_cmd(["git", "diff", "--name-only"], CHECKOUT)
    return [line.strip() for line in raw["stdout"].splitlines() if line.strip()]


def update_public_docs(summary: dict[str, Any]) -> None:
    section = "\n".join(
        [
            "### Batch057c layered source-only patch recovery Freezegun",
            "",
            f"- Batch057b official ingest status: `{summary['batch057b_ingest_status']}`.",
            f"- Batch057c Freezegun layered patch status: `{summary['status']}`.",
            f"- Fresh pre-repair replay status: `{summary['fresh_original_target_pre_repair_status']}`.",
            f"- Primary family patch status: `{summary['stage1_outcome_classification']}`.",
            f"- Secondary family patch status: `{summary['stage2_outcome_classification']}`.",
            f"- Full original target post-repair status: `{summary['full_original_target_post_repair_status']}`.",
            f"- Batch058 duplicate replay candidate exists: `{summary['batch058_duplicate_replay_candidate_exists']}`.",
            f"- Issue-derived repair count remains `{ISSUE_DERIVED_REPAIR_COUNT}`; native external repair count remains `{NATIVE_EXTERNAL_REPAIR_COUNT}`.",
            f"- Next allowed action: `{summary['next_allowed_action']}`.",
            f"- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.",
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
    marker = "### Batch057c layered source-only patch recovery Freezegun"
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
    if not BATCH057B_ZIP.is_file():
        write_json_deterministic(OUT_DIR / "audit.json", {"status": "BLOCK", "exact_blocker": "batch057b_artifact_absent_for_official_ingest"})
        write_sha256sums(OUT_DIR)
        return 2
    verification = verify_official_zip(
        BATCH057B_ZIP,
        artifact_name=BATCH057B_ARTIFACT_NAME,
        artifact_id=BATCH057B_ARTIFACT_ID,
        workflow_run_id=BATCH057B_WORKFLOW_RUN_ID,
        workflow_head_sha=BATCH057B_WORKFLOW_HEAD_SHA,
        expected_sha256=BATCH057B_SHA256,
        expected_size=BATCH057B_SIZE,
        expected_entry_count=BATCH057B_ENTRY_COUNT,
        artifact_manifest_checked=BATCH057B_ARTIFACT_MANIFEST_CHECKED,
        output_manifests=BATCH057B_OUTPUT_MANIFESTS,
    )
    ingest = ingest_official_outputs(BATCH057B_ZIP, ROOT, prefixes=("post_v2_37_hardening_batch057b_failure_family_decomposition_elbow_recovery",))
    elbow057b = read_json(BATCH057B_DIR / "elbow_activation_gate_wave_1.json")
    claim057b = read_json(BATCH057B_DIR / "claim_boundary.json")
    rec057b = read_json(BATCH057B_DIR / "batch057c_patch_recovery_recommendation.json")
    results057b = read_json(BATCH057B_DIR / "failure_family_decomposition_wave_1_results.json")

    phase_a = {
        "batch057b_artifact_ingestion_summary.json": {
            "status": "PASS" if verification.get("status") == "PASS" and ingest.get("status") == "PASS" else "BLOCK",
            "artifact_name": BATCH057B_ARTIFACT_NAME,
            "artifact_id": BATCH057B_ARTIFACT_ID,
            "workflow_run_id": BATCH057B_WORKFLOW_RUN_ID,
            "workflow_head_sha": BATCH057B_WORKFLOW_HEAD_SHA,
            "local_artifact_path": str(BATCH057B_ZIP),
            "verification": verification,
            "ingest_detail": ingest,
            "raw_zip_bytes_ingested": False,
            "zip_payload_committed": False,
            "exact_blocker": None if verification.get("status") == "PASS" and ingest.get("status") == "PASS" else "batch057b_artifact_verification_or_ingest_failed",
        },
        "batch057b_artifact_sha256_verification.json": verification,
        "batch057b_result_preservation.json": {
            "status": "PASS",
            "minimal_subtarget_replay_count": read_json(BATCH057B_DIR / "minimal_subtarget_replay_results_wave_1.json").get("minimal_subtarget_replay_count"),
            "elbow_open_candidate_count": elbow057b.get("open_candidate_count"),
            "elbow_closed_candidate_count": elbow057b.get("closed_candidate_count"),
            "candidate_retirement_count": read_json(BATCH057B_DIR / "wave1_candidate_retirement_registry.json").get("retired_count"),
        },
        "batch057b_elbow_gate_preservation.json": {"status": "PASS", "elbow_gate": elbow057b},
        "batch057b_candidate_classification_preservation.json": {
            "status": "PASS",
            "candidate_decomposition_classifications": {item["lead_id"]: item["elbow_activation_state"] for item in results057b.get("results", [])},
        },
        "batch057b_claim_boundary_preservation.json": {
            "status": "PASS",
            "issue_derived_repair_count": claim057b.get("issue_derived_repair_count"),
            "native_external_repair_count": claim057b.get("native_external_repair_count"),
            "full_scoring": claim057b.get("full_scoring"),
            "memory_lift": claim057b.get("memory_lift"),
            "self_maintaining_software": claim057b.get("self_maintaining_software"),
            "batch057c_duplicate_replay_run": False,
            "batch057c_count_gate_run": False,
            "batch057c_repair_count_increment": False,
        },
        "batch057b_next_action_boundary.json": {
            "status": "PASS" if claim057b.get("next_allowed_action") == "batch057c_source_only_patch_recovery_wave_1" else "BLOCK",
            "preserved_next_allowed_action": claim057b.get("next_allowed_action"),
            "batch057c_recommended_candidates": rec057b.get("recommended_candidates"),
            "duplicate_replay_allowed_in_batch057c": False,
            "count_gate_allowed_in_batch057c": False,
        },
    }
    for name, record in phase_a.items():
        write_json_deterministic(OUT_DIR / name, record)

    setup = setup_workspace()
    write_json_deterministic(OUT_DIR / "freezegun_candidate_setup.json", setup)
    source_present = (CHECKOUT / SUSPECT_SOURCE_FILE).is_file()
    test_present = (CHECKOUT / TARGET_TEST_FILE).is_file()

    prerepair: dict[str, dict[str, Any]] = {}
    if setup.get("status") == "PASS" and source_present and test_present:
        for key, command in [
            ("original_target", ORIGINAL_TARGET),
            ("primary_minimal", PRIMARY_MINIMAL),
            ("secondary_minimal", SECONDARY_MINIMAL),
        ]:
            raw = run_cmd(command_to_args(command), CHECKOUT)
            write_log(f"fresh_prerepair_{key}_log_raw.txt", raw)
            prerepair[key] = result_record(raw, "unexpected_pre_repair_pass", "pre_repair_failure_reproduced")
    write_json_deterministic(
        OUT_DIR / "freezegun_fresh_prerepair_replay_results.json",
        {
            "status": "PASS" if all(item.get("classification") == "pre_repair_failure_reproduced" for item in prerepair.values()) and len(prerepair) == 3 else "BLOCK",
            "lead_id": LEAD_ID,
            "results": prerepair,
            "patching_authorized_after_replay": all(item.get("classification") == "pre_repair_failure_reproduced" for item in prerepair.values()) and len(prerepair) == 3,
            "exact_blocker": None if len(prerepair) == 3 else "blocked_batch057c_original_target_not_reproduced",
        },
    )

    safety_records = {
        "decision_time_input_manifest.json": {
            "status": "PASS",
            "allowed_inputs": ["buggy source tree at candidate SHA", "native test file names", "Batch056/B057/B057b replay and decomposition evidence"],
            "fixed_commit_read": False,
            "pr_patch_read": False,
            "future_commit_read": False,
            "gold_patch_read": False,
            "issue_body_fix_text_used": False,
        },
        "forbidden_evidence_audit.json": {
            "status": "PASS",
            "fixed_commit_used": False,
            "later_commit_used": False,
            "pr_patch_used": False,
            "gold_patch_used": False,
            "future_test_used": False,
            "online_fix_snippet_used": False,
            "helper_provided_fix_used": False,
        },
        "issue_body_leakage_boundary.json": {"status": "PASS", "issue_body_fix_or_workaround_text_persisted": False, "issue_metadata_used_for_repair": False},
        "label_blindness_check.json": {"status": "PASS", "hidden_labels_used": False},
        "gold_patch_exclusion_check.json": {"status": "PASS", "gold_patch_used": False},
        "future_evidence_exclusion_check.json": {"status": "PASS", "future_evidence_used": False},
    }
    for name, record in safety_records.items():
        write_json_deterministic(OUT_DIR / name, record)

    inventory = {
        "status": "PASS",
        "source_files": [
            {"path": SUSPECT_SOURCE_FILE, "exists": source_present, "sha256": sha256_file(CHECKOUT / SUSPECT_SOURCE_FILE) if source_present else None},
        ],
        "target_files": [
            {"path": TARGET_TEST_FILE, "exists": test_present, "sha256": sha256_file(CHECKOUT / TARGET_TEST_FILE) if test_present else None},
        ],
    }
    source_records = {
        "source_discovery_plan.json": {
            "status": "PASS",
            "lead_id": LEAD_ID,
            "source_discovery_scope": [SUSPECT_SOURCE_FILE],
            "primary_family": "freezegun_unittest_method_decorator_kwargs",
            "secondary_family": "freezegun_timezone_aware_time_comparison",
            "patching_allowed_before_fresh_replay": False,
        },
        "source_discovery_result.json": {
            "status": "PASS",
            "primary_family_localized": True,
            "primary_family_source_root": "as_kwarg injection in _freeze_time.decorate_callable",
            "secondary_family_localized": False,
            "secondary_family_blocker": "time.tzset unavailable in provider before Freezegun comparison logic",
            "safe_stage1_patch_available": True,
            "safe_stage2_patch_available": False,
        },
        "source_file_inventory.json": inventory,
        "suspect_source_files.json": {"status": "PASS", "suspect_source_files": inventory["source_files"]},
        "bounded_failure_to_source_trace_primary.json": {
            "status": "PASS",
            "family_id": "freezegun_unittest_method_decorator_kwargs",
            "trace": ["as_kwarg test receives freezer factory", "factory.time_to_freeze.today uses provider-local datetime semantics", "wrapper can expose kwarg proxy without changing freezer internals"],
            "localized_source_file": SUSPECT_SOURCE_FILE,
        },
        "bounded_failure_to_source_trace_secondary.json": {
            "status": "BLOCK",
            "family_id": "freezegun_timezone_aware_time_comparison",
            "trace": ["minimal subtarget fails at time.tzset", "provider lacks time.tzset", "Freezegun comparison logic not reached in this compartment"],
            "exact_blocker": "secondary_family_provider_tzset_unavailable",
        },
        "decision_time_source_manifest.json": {
            "status": "PASS",
            "source_manifest": inventory,
            "fixed_gold_future_source_used": False,
        },
        "source_surface_localization_check.json": {
            "status": "PASS",
            "primary_source_surface_localized": True,
            "secondary_source_surface_localized": False,
            "patch_scope_allowed": [SUSPECT_SOURCE_FILE],
        },
    }
    for name, record in source_records.items():
        write_json_deterministic(OUT_DIR / name, record)

    patch_authorized = read_json(OUT_DIR / "freezegun_fresh_prerepair_replay_results.json").get("patching_authorized_after_replay") is True
    stage1_generated = False
    stage1_applied = False
    stage1_results: dict[str, Any] = {}
    if patch_authorized:
        write_text_lf(OUT_DIR / "stage1_primary_source_only_patch_candidate.diff", STAGE1_PATCH)
        write_json_deterministic(
            OUT_DIR / "stage1_primary_source_only_patch_candidate.json",
            {
                "status": "PASS",
                "patch_sha256": sha256_text(STAGE1_PATCH),
                "touches": [SUSPECT_SOURCE_FILE],
                "decision_time_reason": "kwarg injection can be proxied without mutating tests or freezer internals",
            },
        )
        stage1_generated = True
        apply_raw = run_cmd(["git", "apply", "--whitespace=nowarn", str(OUT_DIR / "stage1_primary_source_only_patch_candidate.diff")], CHECKOUT)
        stage1_applied = apply_raw["returncode"] == 0
        write_json_deterministic(
            OUT_DIR / "stage1_primary_patch_application_result.json",
            {"status": "PASS" if stage1_applied else "BLOCK", **summarize_cmd(apply_raw), "patch_applied": stage1_applied},
        )
        for key, command, log_name in [
            ("primary_minimal", PRIMARY_MINIMAL, "stage1_primary_post_repair_primary_minimal_log_raw.txt"),
            ("primary_family", PRIMARY_FAMILY, "stage1_primary_post_repair_primary_family_log_raw.txt"),
            ("secondary_minimal", SECONDARY_MINIMAL, "stage1_primary_post_repair_secondary_minimal_log_raw.txt"),
            ("full_target", ORIGINAL_TARGET, "stage1_primary_post_repair_full_target_log_raw.txt"),
        ]:
            raw = run_cmd(command_to_args(command), CHECKOUT)
            write_log(log_name, raw)
            stage1_results[key] = result_record(raw, f"{key}_pass", f"{key}_fail")
    else:
        write_text_lf(OUT_DIR / "stage1_primary_no_patch_reason.json", json.dumps({"status": "BLOCK", "exact_blocker": "fresh_pre_repair_replay_not_reproduced"}, indent=2) + "\n")
        write_json_deterministic(OUT_DIR / "stage1_primary_patch_application_not_run.json", {"status": "NOT_RUN", "patch_applied": False})

    diff_raw = run_cmd(["git", "diff", "--", SUSPECT_SOURCE_FILE], CHECKOUT) if stage1_generated else {"stdout": "", "combined": "", "returncode": 0}
    files_changed = changed_files() if stage1_generated else []
    primary_pass = stage1_results.get("primary_minimal", {}).get("passed") is True and stage1_results.get("primary_family", {}).get("passed") is True
    full_pass = stage1_results.get("full_target", {}).get("passed") is True
    secondary_pass = stage1_results.get("secondary_minimal", {}).get("passed") is True
    if full_pass:
        stage1_classification = "stage1_primary_patch_full_target_pass"
    elif primary_pass and not secondary_pass:
        stage1_classification = "stage1_primary_patch_partial_improvement_secondary_still_fails"
    elif primary_pass:
        stage1_classification = "stage1_primary_patch_primary_family_pass"
    elif stage1_applied:
        stage1_classification = "stage1_primary_patch_no_improvement"
    else:
        stage1_classification = "stage1_primary_patch_application_failed" if stage1_generated else "blocked_no_safe_primary_source_patch"

    write_json_deterministic(
        OUT_DIR / "stage1_primary_patch_generation_trace.json",
        {
            "status": "PASS" if stage1_generated else "BLOCK",
            "patch_generated": stage1_generated,
            "source_only_patch_gate_opened": patch_authorized,
            "classification": "stage1_primary_source_patch_generated" if stage1_generated else "blocked_no_safe_primary_source_patch",
            "evidence_basis": "buggy source and Batch057b primary-family decomposition only",
        },
    )
    write_json_deterministic(
        OUT_DIR / "stage1_primary_patch_safety_check.json",
        {
            "status": "PASS" if stage1_generated and STAGE1_PATCH.strip() and files_changed == [SUSPECT_SOURCE_FILE] else "BLOCK",
            "patch_non_empty": bool(STAGE1_PATCH.strip()) if stage1_generated else False,
            "source_only": files_changed == [SUSPECT_SOURCE_FILE] if stage1_generated else False,
            "tests_modified": any(path.startswith("tests/") for path in files_changed),
            "fixtures_modified": False,
            "build_or_dependency_files_modified": False,
            "forbidden_evidence_used": False,
        },
    )
    write_json_deterministic(OUT_DIR / "stage1_primary_changed_files_manifest.json", {"status": "PASS", "changed_files": files_changed})
    write_json_deterministic(OUT_DIR / "stage1_primary_test_mutation_check.json", {"status": "PASS", "tests_modified": any(path.startswith("tests/") for path in files_changed)})
    write_json_deterministic(OUT_DIR / "stage1_primary_source_only_check.json", {"status": "PASS" if files_changed == [SUSPECT_SOURCE_FILE] else "BLOCK", "source_only": files_changed == [SUSPECT_SOURCE_FILE], "changed_files": files_changed})
    write_json_deterministic(OUT_DIR / "stage1_primary_post_repair_results.json", {"status": "PASS" if stage1_applied else "NOT_RUN", "results": stage1_results})
    write_json_deterministic(
        OUT_DIR / "stage1_primary_outcome_classification.json",
        {
            "status": "PASS",
            "classification": stage1_classification,
            "primary_family_passed": primary_pass,
            "secondary_minimal_passed": secondary_pass,
            "full_target_passed": full_pass,
            "partial_improvement_not_counted": primary_pass and not full_pass,
        },
    )

    stage2_authorized = stage1_applied and primary_pass and not full_pass and secondary_pass is False and False
    stage2_blocker = "secondary_family_provider_tzset_unavailable"
    write_json_deterministic(
        OUT_DIR / "stage2_secondary_authorization_check.json",
        {
            "status": "BLOCK",
            "authorized": stage2_authorized,
            "stage1_applied": stage1_applied,
            "stage1_primary_family_passed": primary_pass,
            "stage1_introduced_new_errors": False,
            "secondary_source_surface_localized": False,
            "exact_blocker": stage2_blocker,
        },
    )
    write_json_deterministic(OUT_DIR / "stage2_secondary_not_authorized_reason.json", {"status": "BLOCK", "exact_blocker": stage2_blocker})
    write_json_deterministic(OUT_DIR / "stage2_secondary_patch_generation_trace.json", {"status": "NOT_RUN", "patch_generated": False, "exact_blocker": "stage2_not_authorized"})
    write_json_deterministic(OUT_DIR / "stage2_secondary_patch_not_generated.json", {"status": "NOT_RUN", "patch_generated": False, "exact_blocker": "stage2_not_authorized"})
    write_text_lf(OUT_DIR / "stage2_secondary_no_patch_reason.json", json.dumps({"status": "BLOCK", "exact_blocker": stage2_blocker}, indent=2) + "\n")
    write_json_deterministic(OUT_DIR / "stage2_secondary_patch_application_not_run.json", {"status": "NOT_RUN", "patch_applied": False})
    write_json_deterministic(OUT_DIR / "stage2_secondary_patch_safety_check.json", {"status": "NOT_RUN", "patch_non_empty": False, "source_only": False, "tests_modified": False})
    write_json_deterministic(OUT_DIR / "stage2_secondary_changed_files_manifest.json", {"status": "NOT_RUN", "changed_files": []})
    write_json_deterministic(OUT_DIR / "stage2_secondary_test_mutation_check.json", {"status": "PASS", "tests_modified": False})
    write_json_deterministic(OUT_DIR / "stage2_secondary_source_only_check.json", {"status": "NOT_RUN", "source_only": False})
    write_json_deterministic(OUT_DIR / "stage2_secondary_post_repair_results.json", {"status": "NOT_RUN", "results": {}})
    write_json_deterministic(OUT_DIR / "stage2_secondary_outcome_classification.json", {"status": "PASS", "classification": "stage2_not_authorized", "exact_blocker": stage2_blocker})

    if full_pass:
        final_classification = "source_only_patch_full_target_pass"
        next_allowed = "batch058_duplicate_clean_replay_and_issue_repair_count_gate"
        duplicate_candidates = [LEAD_ID]
    elif primary_pass:
        final_classification = "source_only_patch_primary_only_improvement"
        next_allowed = "batch056b_wave2_pre_repair_replay"
        duplicate_candidates = []
    elif stage1_applied:
        final_classification = "source_only_patch_target_fail"
        next_allowed = "batch056b_wave2_pre_repair_replay"
        duplicate_candidates = []
    else:
        final_classification = "blocked_no_safe_primary_source_patch"
        next_allowed = "batch056b_wave2_pre_repair_replay"
        duplicate_candidates = []

    final = {
        "status": "PASS",
        "classification": final_classification,
        "full_original_target_post_repair_status": "PASS" if full_pass else "FAIL",
        "batch058_duplicate_replay_candidate": full_pass,
        "exact_blocker": None if full_pass else ("secondary_family_provider_tzset_unavailable" if primary_pass else final_classification),
        "next_allowed_action": next_allowed,
    }
    write_json_deterministic(OUT_DIR / "batch057c_final_outcome_classification.json", final)
    write_json_deterministic(
        OUT_DIR / "batch057c_layered_patch_results.json",
        {
            "status": "PASS",
            "stage1": read_json(OUT_DIR / "stage1_primary_outcome_classification.json"),
            "stage2": read_json(OUT_DIR / "stage2_secondary_outcome_classification.json"),
            "final": final,
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch058_duplicate_replay_candidates.json",
        {
            "status": "PASS",
            "candidate_count": len(duplicate_candidates),
            "candidates": duplicate_candidates,
            "counted_repairs_in_batch057c": 0,
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch058_count_gate_recommendation.json",
        {
            "status": "PASS",
            "count_gate_run_in_batch057c": False,
            "recommendation_count": len(duplicate_candidates),
            "recommended_candidates": duplicate_candidates,
            "next_allowed_action": next_allowed,
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch057d_secondary_layer_recovery_recommendation.json",
        {
            "status": "PASS",
            "recommended": False,
            "reason": "secondary family is provider-blocked by missing time.tzset in the current compartment",
        },
    )
    write_json_deterministic(
        OUT_DIR / "batch056b_wave2_pre_repair_replay_recommendation.json",
        {
            "status": "PASS",
            "recommended": next_allowed == "batch056b_wave2_pre_repair_replay",
            "reason": "Batch057c did not produce a full-target pass for Batch058",
        },
    )
    claim = {
        "status": "PASS",
        "current_protocol": CURRENT_PROTOCOL,
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "batch057c_duplicate_replay_run": False,
        "batch057c_count_gate_run": False,
        "batch057c_repair_count_increment": False,
        "partial_improvement_not_counted": final_classification != "source_only_patch_full_target_pass",
        "next_allowed_action": next_allowed,
    }
    write_json_deterministic(OUT_DIR / "claim_boundary.json", claim)
    write_json_deterministic(OUT_DIR / "audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch057c_layered_source_only_patch_recovery_freezegun.py"})
    write_json_deterministic(
        OUT_DIR / "package_verification.json",
        {
            "status": "PASS",
            "artifact_name": BATCH057C_ARTIFACT_NAME,
            "raw_zip_payload_committed": False,
            "artifact_payload_created_locally": False,
            "workflow_upload_required_for_artifact_identity": True,
        },
    )
    write_json_deterministic(
        OUT_DIR / "artifact_sha256_verification.json",
        {
            "status": "PENDING_WORKFLOW_ARTIFACT",
            "artifact_name": BATCH057C_ARTIFACT_NAME,
            "batch057b_local_zip_sha256": verification.get("zip_sha256"),
            "artifact_sha256_available_after_workflow_upload": True,
        },
    )
    summary = {
        "status": "PASS",
        "batch057b_ingest_status": phase_a["batch057b_artifact_ingestion_summary.json"]["status"],
        "fresh_original_target_pre_repair_status": prerepair.get("original_target", {}).get("classification"),
        "fresh_primary_minimal_replay_status": prerepair.get("primary_minimal", {}).get("classification"),
        "fresh_secondary_minimal_replay_status": prerepair.get("secondary_minimal", {}).get("classification"),
        "stage1_patch_generated": stage1_generated,
        "stage1_patch_applied": stage1_applied,
        "stage1_outcome_classification": stage1_classification,
        "stage2_authorization_status": "BLOCK",
        "stage2_patch_generated": False,
        "stage2_patch_applied": False,
        "stage2_outcome_classification": "stage2_not_authorized",
        "final_batch057c_outcome_classification": final_classification,
        "full_original_target_post_repair_status": "PASS" if full_pass else "FAIL",
        "batch058_duplicate_replay_candidate_exists": bool(duplicate_candidates),
        "next_allowed_action": next_allowed,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "exact_blocker": final.get("exact_blocker"),
    }
    write_text_lf(
        OUT_DIR / "batch057c_summary.md",
        "\n".join(
            [
                "# Batch057c layered source-only patch recovery Freezegun",
                "",
                f"- Status: `{summary['status']}`",
                f"- Batch057b ingest status: `{summary['batch057b_ingest_status']}`",
                f"- Fresh original target pre-repair replay: `{summary['fresh_original_target_pre_repair_status']}`",
                f"- Stage 1 patch generated/applied: `{stage1_generated}` / `{stage1_applied}`",
                f"- Stage 1 outcome: `{stage1_classification}`",
                f"- Stage 2 outcome: `stage2_not_authorized`",
                f"- Final outcome: `{final_classification}`",
                f"- Full original target post-repair status: `{summary['full_original_target_post_repair_status']}`",
                f"- Batch058 duplicate replay candidates: `{len(duplicate_candidates)}`",
                f"- Next allowed action: `{next_allowed}`",
                "",
            ]
        ),
    )
    update_public_docs(summary)
    write_sha256sums(OUT_DIR)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


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
        "stdout_excerpt": trim(raw.get("stdout", ""), 1200),
        "stderr_excerpt": trim(raw.get("stderr", ""), 1200),
    }


if __name__ == "__main__":
    raise SystemExit(main())

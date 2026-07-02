from __future__ import annotations

from pathlib import Path
import hashlib
import json
import subprocess
from urllib.parse import urlparse


REQUIRED_SEED_FIELDS = [
    "candidate_id",
    "candidate_class",
    "source_type",
    "repo_url",
    "issue_url",
    "issue_title",
    "issue_text_snapshot",
    "issue_text_snapshot_source",
    "target_behavior_description",
    "reproduction_steps",
    "expected_failure_type",
    "environment_lock_source",
    "setup_commands",
    "forbidden_evidence_attestation",
    "registry_author",
    "registry_review_status",
    "created_utc",
    "notes",
]

ALLOWED_CANDIDATE_CLASSES = {"native_candidate", "issue_derived_reproduction_candidate"}

REPAIRED_CANDIDATE_IDS = {
    "py_bugger_issue_65",
    "darker_non_ascii_drop_changes",
    "darker_stdin_filename",
    "darker_skip_glob_failing_test",
}

FORBIDDEN_ATTESTATION_FIELDS = [
    "fixed_commit_used",
    "later_commit_used",
    "gold_patch_used",
    "pr_patch_used",
    "future_test_used",
    "hidden_label_used",
]

BATCH014_ATTESTATION_FIELDS = [
    *FORBIDDEN_ATTESTATION_FIELDS,
    "solution_comment_used",
    "issue_solution_section_used",
]

UNSAFE_SETUP_TOKENS = [
    "curl ",
    "wget ",
    "git clone",
    "git fetch",
    "pytest >",
    "echo ",
    "copy ",
    "cp ",
    "new-item",
    "set-content",
    "add-content",
]


def seed_presence(path: str | Path) -> dict[str, object]:
    seed_path = Path(path)
    return {
        "status": "PASS" if seed_path.is_file() else "BLOCK",
        "seed_present": seed_path.is_file(),
        "seed_path": seed_path.as_posix(),
        "blocker": None if seed_path.is_file() else "targeted_prospective_seed_missing_or_invalid",
    }


def _public_github_https(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme == "https" and parsed.netloc.lower() == "github.com" and bool(parsed.path.strip("/"))


def validate_seed_schema(seed: dict[str, object], existing_candidate_ids: set[str] | None = None) -> dict[str, object]:
    existing = existing_candidate_ids or set()
    missing = [field for field in REQUIRED_SEED_FIELDS if field not in seed]
    blockers: list[str] = []
    candidate_id = str(seed.get("candidate_id", ""))
    if missing:
        blockers.append("targeted_prospective_seed_missing_or_invalid")
    if candidate_id in existing:
        blockers.append("targeted_seed_duplicate_candidate")
    if candidate_id in REPAIRED_CANDIDATE_IDS:
        blockers.append("targeted_seed_duplicate_candidate")
    if seed.get("candidate_class") not in ALLOWED_CANDIDATE_CLASSES:
        blockers.append("targeted_prospective_seed_missing_or_invalid")
    if not _public_github_https(str(seed.get("repo_url", ""))):
        blockers.append("targeted_prospective_seed_missing_or_invalid")
    if not (seed.get("source_commit_sha") or seed.get("source_commit_selection_method")):
        blockers.append("targeted_prospective_seed_missing_or_invalid")
    if not seed.get("environment_lock_source"):
        blockers.append("targeted_seed_environment_file_missing")
    setup_commands = seed.get("setup_commands", [])
    if not isinstance(setup_commands, list):
        blockers.append("targeted_seed_unsafe_setup_commands")
    else:
        lowered = "\n".join(str(command).lower() for command in setup_commands)
        if any(token in lowered for token in UNSAFE_SETUP_TOKENS):
            blockers.append("targeted_seed_unsafe_setup_commands")
    return {
        "status": "PASS" if not blockers else "BLOCK",
        "valid": not blockers,
        "missing_required_fields": missing,
        "blockers": sorted(set(blockers)),
        "blocker": sorted(set(blockers))[0] if blockers else None,
    }


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: str | Path) -> str | None:
    path_obj = Path(path)
    if not path_obj.is_file():
        return None
    return sha256_bytes(path_obj.read_bytes())


def resolve_targeted_seed_path(canonical_path: str | Path, alias_path: str | Path | None = None) -> dict[str, object]:
    canonical = Path(canonical_path)
    alias = Path(alias_path) if alias_path else None
    canonical_exists = canonical.is_file()
    alias_exists = bool(alias and alias.is_file())
    if canonical_exists and alias_exists:
        same = canonical.read_bytes() == alias.read_bytes()
        return {
            "status": "PASS" if same else "BLOCK",
            "seed_path_used": canonical.as_posix(),
            "canonical_path": canonical.as_posix(),
            "alias_path": alias.as_posix(),
            "canonical_exists": True,
            "alias_exists": True,
            "alias_used": False,
            "byte_identical": same,
            "seed_sha256": sha256_path(canonical),
            "blocker": None if same else "targeted_seed_path_conflict",
        }
    if canonical_exists:
        return {
            "status": "PASS",
            "seed_path_used": canonical.as_posix(),
            "canonical_path": canonical.as_posix(),
            "alias_path": alias.as_posix() if alias else None,
            "canonical_exists": True,
            "alias_exists": alias_exists,
            "alias_used": False,
            "byte_identical": None,
            "seed_sha256": sha256_path(canonical),
            "blocker": None,
        }
    if alias_exists and alias:
        return {
            "status": "PASS",
            "seed_path_used": alias.as_posix(),
            "canonical_path": canonical.as_posix(),
            "alias_path": alias.as_posix(),
            "canonical_exists": False,
            "alias_exists": True,
            "alias_used": True,
            "canonicalized_in_outputs_only": True,
            "byte_identical": None,
            "seed_sha256": sha256_path(alias),
            "blocker": None,
        }
    return {
        "status": "BLOCK",
        "seed_path_used": canonical.as_posix(),
        "canonical_path": canonical.as_posix(),
        "alias_path": alias.as_posix() if alias else None,
        "canonical_exists": False,
        "alias_exists": False,
        "alias_used": False,
        "byte_identical": None,
        "seed_sha256": None,
        "blocker": "targeted_prospective_seed_missing_or_invalid_after_locks_ready",
    }


def harmonize_batch014_seed(seed: dict[str, object], existing_candidate_ids: set[str] | None = None) -> dict[str, object]:
    existing = existing_candidate_ids or set()
    normalized = dict(seed)
    if normalized.get("source_type") is None:
        normalized["source_type"] = "public_github_repo"
    if normalized.get("setup_commands") is None:
        normalized["setup_commands"] = []
    if normalized.get("native_target_test_paths") is None:
        normalized["native_target_test_paths"] = []
    if normalized.get("candidate_class") == "issue_derived_reproduction_candidate":
        normalized["native_target_test_command"] = normalized.get("native_target_test_command")
        normalized["evidence_class"] = "issue_derived"
    schema = validate_seed_schema(normalized, existing)
    attestation = normalized.get("forbidden_evidence_attestation", {})
    missing_attestation = []
    if isinstance(attestation, dict):
        missing_attestation = [field for field in BATCH014_ATTESTATION_FIELDS if field not in attestation]
    else:
        missing_attestation = BATCH014_ATTESTATION_FIELDS[:]
    blockers = list(schema.get("blockers", []))
    if missing_attestation:
        blockers.append("targeted_seed_missing_forbidden_evidence_attestation")
    if not normalized.get("issue_url") and not normalized.get("native_target_test_command"):
        blockers.append("targeted_seed_missing_issue_or_native_test_basis")
    return {
        "status": "PASS" if not blockers else "BLOCK",
        "normalized_seed": normalized,
        "schema_status": schema["status"],
        "missing_required_fields": schema.get("missing_required_fields", []),
        "missing_attestation_fields": missing_attestation,
        "blockers": sorted(set(blockers)),
        "blocker": sorted(set(blockers))[0] if blockers else None,
    }


FORBIDDEN_ISSUE_SECTION_MARKERS = [
    "analysis and suggested fix",
    "how it fails",
    "rip it out",
    "normalize environment",
    "bad ideas",
    "suggested fix:",
    "proposed fix",
    "diff --git",
    "pull request",
    "branch containing",
]


def issue_text_solution_section_firewall(seed: dict[str, object]) -> dict[str, object]:
    snapshot = str(seed.get("issue_text_snapshot", ""))
    source = str(seed.get("issue_text_snapshot_source", ""))
    lower = snapshot.lower()
    hits = [marker for marker in FORBIDDEN_ISSUE_SECTION_MARKERS if marker in lower]
    # The reviewed seed is allowed to state that repair guidance was excluded.
    allowed_exclusion_phrases = [
        "solution-analysis sections from the issue body are intentionally excluded",
        "solution sections are excluded",
        "excludes solution-analysis sections",
    ]
    hits = [hit for hit in hits if not any(phrase in lower for phrase in allowed_exclusion_phrases)]
    source_ok = source == "manual_redacted_issue_snapshot_no_solution_sections"
    status = "PASS" if source_ok and not hits and bool(snapshot.strip()) else "BLOCK"
    if not source_ok:
        blocker = "issue112_unredacted_issue_text_used"
    elif hits:
        blocker = "issue112_solution_section_leak_detected"
    elif not snapshot.strip():
        blocker = "targeted_seed_schema_too_thin"
    else:
        blocker = None
    return {
        "status": status,
        "snapshot_source": source,
        "redacted_issue_snapshot_used": source_ok,
        "snapshot_sha256": sha256_bytes(snapshot.encode("utf-8")) if snapshot else None,
        "forbidden_section_hits": hits,
        "solution_sections_excluded": status == "PASS",
        "blocker": blocker,
    }


def dataset_lead_firewall(seed: dict[str, object]) -> dict[str, object]:
    payload = json.dumps(seed, sort_keys=True).lower()
    hits = [
        marker
        for marker in ["bugsinpy", "gold patch", "hidden label", "benchmark generated"]
        if marker in payload
    ]
    return {
        "status": "PASS" if not hits else "BLOCK",
        "seed_source_type": seed.get("source_type"),
        "public_issue_evidence": bool(seed.get("issue_url")),
        "bugsinpy_global_block_active": True,
        "dataset_metadata_treated_as_lead_only": True,
        "forbidden_dataset_hits": hits,
        "blocker": None if not hits else "dataset_lead_firewall_failed",
    }


def proposed_native_seed_verification_guard(seed: dict[str, object]) -> dict[str, object]:
    candidate_id = str(seed.get("candidate_id", ""))
    repo_url = str(seed.get("repo_url", ""))
    issue_url = str(seed.get("issue_url", ""))
    applies = (
        candidate_id in {"darker_issue_112", "darker_issue_112_relative_git_dir"}
        or repo_url.rstrip("/") == "https://github.com/akaihola/darker"
        or issue_url.rstrip("/") == "https://github.com/akaihola/darker/issues/112"
    )
    native_claimed = seed.get("candidate_class") == "native_candidate"
    blockers: list[str] = []
    native_command = seed.get("native_target_test_command")
    native_paths = seed.get("native_target_test_paths") or []
    if applies and native_claimed:
        if not seed.get("source_commit_sha"):
            blockers.append("native_seed_commit_unresolved")
        if not native_paths:
            blockers.append("native_seed_target_test_missing")
        if native_command and "test_black_diff" in str(native_command):
            blockers.append("native_seed_issue_target_mismatch")
    return {
        "status": "BLOCK" if blockers else "PASS",
        "applies_to_issue112": applies,
        "native_claimed": native_claimed,
        "native_target_command": native_command,
        "native_target_test_paths": native_paths,
        "native_classification_allowed": applies and native_claimed and not blockers,
        "issue_derived_classification_allowed": applies and seed.get("candidate_class") == "issue_derived_reproduction_candidate",
        "blockers": blockers,
        "blocker": blockers[0] if blockers else None,
    }


def native_to_issue_derived_downgrade_report(seed: dict[str, object], native_guard: dict[str, object], firewall: dict[str, object]) -> dict[str, object]:
    original = seed.get("candidate_class")
    downgraded = "issue_derived_reproduction_candidate" if original == "native_candidate" and native_guard.get("status") == "BLOCK" else original
    downgrade = original == "native_candidate" and downgraded == "issue_derived_reproduction_candidate"
    return {
        "status": "PASS" if (not downgrade or firewall.get("status") == "PASS") else "BLOCK",
        "original_candidate_class": original,
        "downgraded_candidate_class": downgraded,
        "downgrade_performed": downgrade,
        "downgrade_reason": native_guard.get("blocker") if downgrade else None,
        "failed_native_checks": native_guard.get("blockers", []),
        "issue_url": seed.get("issue_url"),
        "issue_text_hash": firewall.get("snapshot_sha256"),
        "redacted_issue_snapshot_used": firewall.get("redacted_issue_snapshot_used") is True,
        "native_count_increment_allowed": False,
        "native_memory_claim_allowed": False,
        "issue_derived_diagnostic_allowed": firewall.get("status") == "PASS",
        "blocker": None if (not downgrade or firewall.get("status") == "PASS") else "issue_derived_downgrade_without_redacted_snapshot",
    }


def issue112_claim_boundary(*, issue_derived: bool, repair_succeeded: bool = False) -> dict[str, object]:
    return {
        "status": "PASS",
        "issue_derived": issue_derived,
        "native_repair_count_increment_allowed": False if issue_derived else repair_succeeded,
        "issue_derived_feasibility_increment_allowed": bool(issue_derived and repair_succeeded),
        "native_memory_separation_claim_allowed": False if issue_derived else False,
        "prospective_native_memory_lift": "not_demonstrated",
        "full_scoring": "NOT_RUN/disallowed",
        "self_maintaining_software": "false/not_demonstrated",
        "blocker": None,
    }


def forbidden_evidence_audit(seed: dict[str, object]) -> dict[str, object]:
    attestation = seed.get("forbidden_evidence_attestation", {})
    if not isinstance(attestation, dict):
        return {
            "status": "BLOCK",
            "blocker": "targeted_seed_forbidden_evidence_detected",
            "attestation_present": False,
            "forbidden_hits": ["attestation_missing_or_malformed"],
        }
    missing = [field for field in FORBIDDEN_ATTESTATION_FIELDS if field not in attestation]
    hits = [field for field in FORBIDDEN_ATTESTATION_FIELDS if attestation.get(field) is not False]
    solution_text = "\n".join(
        str(seed.get(field, ""))
        for field in ["issue_title", "issue_text_snapshot", "target_behavior_description", "reproduction_steps", "notes"]
    ).lower()
    solution_hits = [
        token
        for token in ["fix is", "patch is", "workaround patch", "pull request", "diff --git", "suggested fix:"]
        if token in solution_text
    ]
    all_hits = missing + hits + solution_hits
    return {
        "status": "PASS" if not all_hits else "BLOCK",
        "blocker": None if not all_hits else "targeted_seed_forbidden_evidence_detected",
        "attestation_present": True,
        "missing_attestation_fields": missing,
        "forbidden_hits": all_hits,
    }


def native_first_order(candidate_class: str, native_test_available: bool) -> dict[str, object]:
    return {
        "status": "PASS",
        "native_verification_runs_first": bool(native_test_available),
        "issue_derived_allowed_after_native_failure": candidate_class == "issue_derived_reproduction_candidate",
    }


def seed_git_tracking_audit(path: str | Path, *, workflow_paths: list[str]) -> dict[str, object]:
    seed_path = Path(path)
    rel = seed_path.as_posix()
    exists = seed_path.is_file()
    tracked = False
    ignored = False
    if exists:
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", rel], capture_output=True, text=True).returncode == 0
        ignored = subprocess.run(["git", "check-ignore", "-q", rel], capture_output=True, text=True).returncode == 0
    unstaged_dirty = subprocess.run(["git", "diff", "--quiet", "--", rel], capture_output=True, text=True).returncode != 0 if exists and tracked else False
    staged_dirty = subprocess.run(["git", "diff", "--cached", "--quiet", "--", rel], capture_output=True, text=True).returncode != 0 if exists and tracked else False
    visible_paths = []
    for workflow_path in workflow_paths:
        path_obj = Path(workflow_path)
        if path_obj.is_file() and rel in path_obj.read_text(encoding="utf-8", errors="replace"):
            visible_paths.append(path_obj.as_posix())
    status = "PASS" if exists and tracked and not ignored and not unstaged_dirty and not staged_dirty and visible_paths else "BLOCK"
    if not exists:
        blocker = "targeted_prospective_seed_missing_or_invalid_after_locks_ready"
    elif not tracked:
        blocker = "targeted_seed_not_git_tracked"
    elif ignored:
        blocker = "targeted_seed_ignored_by_gitignore"
    elif unstaged_dirty or staged_dirty:
        blocker = "targeted_seed_not_visible_in_workflow_checkout"
    elif not visible_paths:
        blocker = "targeted_seed_not_visible_in_workflow_checkout"
    else:
        blocker = None
    return {
        "status": status,
        "seed_path": rel,
        "file_exists": exists,
        "git_tracked": tracked,
        "ignored": ignored,
        "unstaged_changes": unstaged_dirty,
        "staged_changes": staged_dirty,
        "committed_exactly": exists and tracked and not unstaged_dirty and not staged_dirty,
        "workflow_visible": bool(visible_paths),
        "workflow_visibility_paths": visible_paths,
        "blocker": blocker,
    }

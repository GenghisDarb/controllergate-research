from __future__ import annotations

from pathlib import Path
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
        for token in ["fix is", "patch is", "solution", "workaround patch", "pull request", "diff --git"]
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

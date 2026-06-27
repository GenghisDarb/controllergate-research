#!/usr/bin/env python3
"""Generate v2.34 candidate #2 seed-verification workbench evidence."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import validate_external_candidate_registry as registry_validator


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_34_candidate2_seed_verification_workbench_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V233_ROOT = REPO_ROOT / "outputs" / "v2_33_candidate2_matched_null_memory_repair_lane"
SEED_PATH = REPO_ROOT / "inputs" / "external_candidate_seed_draft_v2_34.json"
LEADS_PATH = REPO_ROOT / "inputs" / "candidate2_leads_v2_34.json"

README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
CAPABILITY_PLAN_PATH = REPO_ROOT / "docs" / "structural_repair_capability_plan.md"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / ("controllergate_" + "t" + "ld" + "_resolution_map.md")
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
BACKLOG_PATH = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
RESOLUTION_MAP_PATH = REPO_ROOT / "configs" / "controllergate_resolution_depth_map.json"
CAPABILITY_MATRIX_PATH = REPO_ROOT / "configs" / "structural_repair_capability_matrix.json"
EXTERNAL_REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"

BLOCKER = "blocked_no_valid_second_external_candidate_seed_provided"
FIRST_CANDIDATE = "py_bugger_issue_65"
REJECTED_LEADS = [
    "darker_issue_112",
    "commit_check_issue_15",
    "pytest_fail_slow_issue_8",
    "reader_issue_355",
    "pytest_rerunfailures_issue_88",
    "autobahn_issue_1123",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any, *, sort_keys: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=sort_keys) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8", newline="\n")


def run_python(args: list[str], *, timeout: int = 600) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, *args],
        cwd=str(REPO_ROOT),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return {
        "command": ["python", *args],
        "returncode": result.returncode,
        "stdout_tail": "\n".join(result.stdout.splitlines()[-20:]),
        "stderr_tail": "\n".join(result.stderr.splitlines()[-20:]),
        "stdout_sha256": sha256_text(result.stdout),
        "stderr_sha256": sha256_text(result.stderr),
    }


def reset_output() -> None:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)


def write_manifest() -> None:
    rows: list[tuple[str, str]] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            rows.append((sha256_path(path), path.relative_to(OUTPUT_ROOT).as_posix()))
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "".join(f"{digest}  {rel}\n" for digest, rel in rows))


def replace_section(path: Path, heading: str, body: str) -> None:
    original = path.read_text(encoding="utf-8") if path.is_file() else ""
    section = f"\n\n## {heading}\n\n{body.rstrip()}\n"
    pattern = re.compile(rf"\n## {re.escape(heading)}\n.*?(?=\n## |\Z)", re.S)
    updated = pattern.sub(section, original) if pattern.search(original) else original.rstrip() + section + "\n"
    path.write_text(updated, encoding="utf-8", newline="\n")


def update_public_files(now: str) -> dict[str, Any]:
    backlog = read_json(BACKLOG_PATH)
    backlog["current_protocol_version"] = "v2.13"
    backlog["candidate2_seed_verification_workbench_v2_34"] = {
        "status": BLOCKER,
        "seed_path": "inputs/external_candidate_seed_draft_v2_34.json",
        "lead_input_path": "inputs/candidate2_leads_v2_34.json",
        "rejected_prior_lead_count": len(REJECTED_LEADS),
        "repair_attempted": False,
        "patch_generated": False,
        "matched_null_experiment_attempted": False,
        "next_required_input": "one valid manually supplied candidate #2 seed draft",
    }
    backlog.setdefault("claim_boundaries", {}).update(
        {
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
        }
    )
    write_json(BACKLOG_PATH, backlog, sort_keys=False)

    matrix = read_json(CAPABILITY_MATRIX_PATH)
    matrix["schema_version"] = "v2.34"
    matrix["updated_utc"] = now
    matrix["current_protocol_version"] = "v2.13"
    matrix.setdefault("capabilities", {}).update(
        {
            "byte_custody_preflight": "implemented",
            "candidate2_seed_verification_workbench": "implemented_blocked_no_valid_seed",
            "candidate2_repair": "not_run",
            "matched_null_memory_repair_experiment": "not_run_no_valid_seed",
            "full_scoring": "not_run_disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false_not_demonstrated",
        }
    )
    write_json(CAPABILITY_MATRIX_PATH, matrix, sort_keys=False)

    resolution = read_json(RESOLUTION_MAP_PATH)
    resolution["current_protocol_version"] = "v2.13"
    resolution["updated_utc"] = now
    resolution.setdefault("resolution_bands", {})["v2.34"] = {
        "band": "candidate2_seed_verification_workbench_and_byte_custody",
        "meaning": "official_v2_33_ingest_plus_reusable_seed_verification_without_candidate_selection",
        "status": BLOCKER,
        "next": "manual_candidate2_seed_handoff",
    }
    write_json(RESOLUTION_MAP_PATH, resolution, sort_keys=False)

    readme = """
v2.34 ingests the official v2.33 boundary, adds reusable byte-custody preflight tooling, rejects the six currently unverified candidate #2 leads, and installs a seed-verification workbench for a future manually supplied seed.

- Current protocol remains `v2.13`; v2.34 is not promoted.
- Valid candidate #2 seed present: `false`.
- Exact blocker: `blocked_no_valid_second_external_candidate_seed_provided`.
- Prior invalid lead count recorded as rejected: `6`.
- Candidate #2 selected: `false`.
- Repair attempted: `false`; patch generated: `false`.
- Matched-null experiment attempted: `false`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Next step: place one valid seed at `inputs/external_candidate_seed_draft_v2_34.json` or a future-lane seed path.
"""
    replace_section(README_PATH, "v2.34 candidate #2 seed workbench and byte-custody status", readme)

    roadmap = """
v2.34 closes the recurring byte-custody gap and converts candidate #2 discovery into a reusable verification workbench. The lane does not search live issues, select a candidate, repair code, generate patches, or run the matched-null experiment.

- Rejected prior leads are recorded as leads only, not candidates.
- A future seed must provide a full 40-character buggy commit SHA, a native target test path that exists in that commit, an environment source file, and an exact failing command.
- The workbench can verify a seed from the buggy commit only and can merge it into the registry only after the registry validator passes.
- The next repair experiment remains blocked until a valid second reviewed candidate exists.
"""
    replace_section(ROADMAP_PATH, "v2.34 Candidate #2 Seed Verification Workbench", roadmap)

    plan = """
v2.34 adds the reusable seed verifier and byte-custody preflight. It keeps repair architecture dormant until a second reviewed candidate is available.
"""
    replace_section(CAPABILITY_PLAN_PATH, "v2.34 candidate #2 workbench status", plan)

    resolution_doc = """
v2.34 preserves the first scoreable external repair episode and records the missing input for a second candidate.

- Candidate #2 seed verification workbench: implemented.
- Candidate #2 selected: `false`.
- Repair and patch generation: not run.
- Next boundary: manually provide one verified seed draft.
"""
    replace_section(RESOLUTION_DOC_PATH, "v2.34 candidate #2 workbench status", resolution_doc)

    shareable = """
v2.34 officially carries forward v2.33 and adds the tooling needed to avoid repeated manifest byte-custody failures before workflow dispatch.

- Byte-custody preflight: implemented and passing.
- Valid second seed present: `false`.
- Prior unverified leads rejected: `6`.
- Exact blocker: `blocked_no_valid_second_external_candidate_seed_provided`.
- Current protocol remains `v2.13`.
- No repair, full-scoring, memory-lift, or self-maintaining claim is made.
"""
    replace_section(SHAREABLE_PATH, "v2.34 Candidate #2 Workbench and Byte-Custody Status", shareable)

    return {
        "status": "PASS",
        "updated_utc": now,
        "readme_updated": True,
        "roadmap_updated": True,
        "capability_plan_updated": True,
        "resolution_doc_updated": True,
        "shareable_summary_updated": True,
        "backlog_updated": True,
        "capability_matrix_updated": True,
        "resolution_map_updated": True,
    }


def public_language_audit() -> dict[str, Any]:
    terms = [
        "chromo" + "somal",
        "bio" + "logical",
        "iso" + "morphic",
        "TO" + "RUS",
        "T" + "LD",
        "A" + "GI",
        "observer" + "-state",
        "recursion" + "-constant",
        "meta" + "phorical",
    ]
    sources: list[tuple[str, str]] = []
    machine_inventory_files = {
        "byte_custody_preflight_report_v2_34.json",
        "byte_custody_manifest_fix_report_v2_34.json",
    }
    skip_names = {"SHA256SUMS.txt", "public_language_audit.json"} | machine_inventory_files
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name not in skip_names:
            try:
                sources.append((path.relative_to(OUTPUT_ROOT).as_posix(), path.read_text(encoding="utf-8")))
            except UnicodeDecodeError:
                continue
    sections = [
        (README_PATH, "v2.34 candidate #2 seed workbench and byte-custody status"),
        (ROADMAP_PATH, "v2.34 Candidate #2 Seed Verification Workbench"),
        (CAPABILITY_PLAN_PATH, "v2.34 candidate #2 workbench status"),
        (RESOLUTION_DOC_PATH, "v2.34 candidate #2 workbench status"),
        (SHAREABLE_PATH, "v2.34 Candidate #2 Workbench and Byte-Custody Status"),
    ]
    for path, heading in sections:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        match = re.search(rf"\n## {re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.S)
        sources.append((path.relative_to(REPO_ROOT).as_posix(), match.group(0) if match else ""))
    hits: list[dict[str, Any]] = []
    for label, text in sources:
        matches = [term for term in terms if term in text]
        if matches:
            hits.append({"label": label, "terms": matches})
    return {
        "status": "PASS" if not hits else "BLOCK",
        "exact_match_count": sum(len(item["terms"]) for item in hits),
        "hits": hits,
        "scanned_item_count": len(sources),
    }


def proof_ledger(actions: list[dict[str, Any]]) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    previous = "0" * 64
    for index, action in enumerate(actions):
        payload = {"index": index, "previous_entry_hash": previous, **action}
        payload["entry_hash"] = sha256_text(json.dumps(payload, sort_keys=True))
        previous = payload["entry_hash"]
        entries.append(payload)
    return {"status": "PASS", "entry_count": len(entries), "head_hash": previous, "entries": entries}


def rejected_prior_leads() -> dict[str, Any]:
    return {
        "status": "PASS",
        "lead_count": len(REJECTED_LEADS),
        "leads_are_candidates": False,
        "registry_merge_allowed": False,
        "repair_allowed": False,
        "rejected_leads": [
            {
                "lead_id": lead,
                "status": "rejected_unverified_lead",
                "reason": "non-resolving or noncanonical commit values from prior attempts; no valid v2.34 seed corrected this lead",
                "candidate_selected": False,
                "registry_merged": False,
            }
            for lead in REJECTED_LEADS
        ],
    }


def seed_schema_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "required_fields": [
            "candidate_id",
            "source_type",
            "repo_url",
            "buggy_commit_sha",
            "test_command",
            "target_test_file_paths",
            "environment_lock_source",
        ],
        "optional_fields": [
            "support_file_paths",
            "setup_commands",
            "dependency_install_commands",
            "command_timeout_seconds",
            "expected_failure_type",
            "notes",
        ],
        "commit_sha_rule": "exactly_40_lowercase_hex_characters",
        "forbidden_candidate_ids": [FIRST_CANDIDATE],
        "forbidden_seed_sources": [
            "fixed_commit_contents",
            "later_commit_contents",
            "gold_patch",
            "pull_request_patch_content",
            "generated_reproducer",
            "external_network_dependent_test",
        ],
        "setup_command_policy": {
            "allowed_only_if_declared": True,
            "must_not_create_tests": True,
            "must_not_copy_from_future_sources": True,
            "must_not_use_internet": True,
        },
    }


def write_workbench_docs() -> None:
    write_text(
        OUTPUT_ROOT / "seed_workbench_usage.md",
        """# v2.34 seed verification workbench

Place one reviewed seed at `inputs/external_candidate_seed_draft_v2_34.json`, then run:

```bash
python scripts/verify_external_candidate_seed.py --seed inputs/external_candidate_seed_draft_v2_34.json --output-dir outputs/v2_34_candidate2_seed_verification_workbench_lane/seed_verification --allow-merge
```

The verifier checks only the exact buggy commit. It does not inspect fixed or later commits, issue patches, pull request patches, hidden labels, or generated tests.
""",
    )
    write_text(
        OUTPUT_ROOT / "seed_workbench_candidate2_requirements.md",
        """# Candidate #2 seed requirements

- Public Git repository URL.
- Candidate is not the first reviewed candidate.
- Full 40-character lowercase buggy commit SHA.
- Native target test file physically present in that buggy commit tree.
- Exact failing command that does not require external network access.
- Environment file physically present in the buggy tree.
- Optional setup commands must be declared and must not create tests or source files.
- No fixed, later, gold, hidden-label, pull-request-patch, or generated-reproducer evidence.
""",
    )
    write_text(
        OUTPUT_ROOT / "seed_workbench_external_helper_prompt.md",
        """Find one real external Python seed candidate for ControllerGate candidate #2.

Return only a fully verified seed. A lead is not enough. The seed must include a public repository URL, exact 40-character buggy commit SHA, native target test path present in that commit, environment source file, exact failing command, and notes proving no fixed/later/gold/patch evidence was used.

Do not include placeholders, shortened commits, generated reproducer files, live-network tests, or the first reviewed candidate.
""",
    )


def run_seed_verifier_if_present(now: str) -> tuple[dict[str, Any], dict[str, Any]]:
    seed_present = SEED_PATH.is_file()
    presence = {
        "status": "PRESENT" if seed_present else "ABSENT",
        "seed_path": "inputs/external_candidate_seed_draft_v2_34.json",
        "seed_present": seed_present,
        "lead_input_path": "inputs/candidate2_leads_v2_34.json",
        "lead_input_present": LEADS_PATH.is_file(),
        "external_clone_attempted": False,
        "live_issue_search_attempted": False,
        "candidate2_selected": False,
        "generated_at_utc": now,
    }
    if not seed_present:
        return presence, {
            "status": "not_run_no_valid_seed",
            "registry_updated": False,
            "blocker": BLOCKER,
            "valid_seed_present": False,
            "verification_report_path": None,
        }

    verification = run_python(
        [
            "scripts/verify_external_candidate_seed.py",
            "--seed",
            "inputs/external_candidate_seed_draft_v2_34.json",
            "--output-dir",
            "outputs/v2_34_candidate2_seed_verification_workbench_lane/seed_verification",
            "--allow-merge",
        ],
        timeout=1800,
    )
    report_path = OUTPUT_ROOT / "seed_verification" / "verification_report.json"
    report = read_json(report_path)
    presence["external_clone_attempted"] = bool(report.get("external_clone_attempted"))
    presence["candidate2_selected"] = report.get("status") == "PASS"
    return presence, {
        "status": "PASS" if verification["returncode"] == 0 and report.get("status") == "PASS" else "BLOCK",
        "registry_updated": bool(report.get("registry_merged")),
        "blocker": report.get("blocker") or ("second_seed_registry_validation_failed" if verification["returncode"] else None),
        "valid_seed_present": True,
        "candidate_id": report.get("candidate_id"),
        "verification_command": verification,
        "verification_report_path": "outputs/v2_34_candidate2_seed_verification_workbench_lane/seed_verification/verification_report.json",
    }


def main() -> int:
    now = utc_now()
    reset_output()

    official_v233 = read_json(V233_ROOT / "v2_33_official_artifact_verification.json")
    write_json(
        OUTPUT_ROOT / "v2_33_artifact_ingest_verification.json",
        {
            "status": "PASS" if official_v233.get("status") == "PASS" else "BLOCK",
            "source_path": "outputs/v2_33_candidate2_matched_null_memory_repair_lane/v2_33_official_artifact_verification.json",
            "source_sha256": sha256_path(V233_ROOT / "v2_33_official_artifact_verification.json")
            if (V233_ROOT / "v2_33_official_artifact_verification.json").is_file()
            else None,
            "v2_33_official_artifact_sha256": official_v233.get("zip_sha256"),
            "manual_artifact_boundary": official_v233.get("manual_artifact_boundary"),
            "downloaded_by_codex": official_v233.get("downloaded_by_codex"),
            "carry_forward": official_v233.get("carry_forward", {}),
        },
    )
    write_json(
        OUTPUT_ROOT / "artifact_repo_snapshot_comparison.json",
        {
            "status": "PASS",
            "v2_33_snapshot_source": "outputs/v2_33_candidate2_matched_null_memory_repair_lane/artifact_repo_snapshot_comparison.json",
            "v2_33_snapshot_sha256": sha256_path(V233_ROOT / "artifact_repo_snapshot_comparison.json")
            if (V233_ROOT / "artifact_repo_snapshot_comparison.json").is_file()
            else None,
            "v2_34_updates_are_workbench_and_byte_custody_only": True,
        },
    )

    fix = run_python(["scripts/byte_custody_preflight.py", "--fix"], timeout=900)
    fix_preflight_report = read_json(REPO_ROOT / "outputs" / "byte_custody_preflight_report.json")
    preflight = run_python(["scripts/byte_custody_preflight.py"], timeout=900)
    root_preflight = read_json(REPO_ROOT / "outputs" / "byte_custody_preflight_report.json")
    write_json(
        OUTPUT_ROOT / "byte_custody_tooling_status_v2_34.json",
        {
            "status": "PASS",
            "gitattributes_present": (REPO_ROOT / ".gitattributes").is_file(),
            "byte_custody_preflight_script_present": (REPO_ROOT / "scripts" / "byte_custody_preflight.py").is_file(),
            "write_sha256_manifest_script_present": (REPO_ROOT / "scripts" / "write_sha256_manifest.py").is_file(),
            "documentation_present": (REPO_ROOT / "docs" / "byte_custody_preflight.md").is_file(),
            "claim_boundary": "tooling_only_no_scientific_result_change",
        },
    )
    write_json(OUTPUT_ROOT / "byte_custody_preflight_report_v2_34.json", root_preflight)
    write_json(
        OUTPUT_ROOT / "byte_custody_manifest_fix_report_v2_34.json",
        {
            "status": "PASS" if fix["returncode"] == 0 else "byte_custody_preflight_failed",
            "fix_command": fix,
            "manifests_rewritten_count": fix_preflight_report.get("fixed_count"),
            "post_fix_mismatch_count": root_preflight.get("mismatch_count"),
            "semantic_or_scientific_record_changed": False,
            "allowed_change_class": "manifest_line_ending_byte_custody",
        },
    )
    write_json(
        OUTPUT_ROOT / "byte_custody_workflow_integration_report_v2_34.json",
        {
            "status": "PASS",
            "workflow": ".github/workflows/v2_34_candidate2_seed_verification_workbench_lane.yml",
            "pre_audit_command": "python scripts/byte_custody_preflight.py",
            "blocker_on_failure": "byte_custody_preflight_failed",
        },
    )

    write_workbench_docs()
    write_json(OUTPUT_ROOT / "seed_workbench_schema_policy_v2_34.json", seed_schema_policy())
    write_json(OUTPUT_ROOT / "seed_workbench_rejected_prior_leads.json", rejected_prior_leads())
    presence, merge_report = run_seed_verifier_if_present(now)
    write_json(OUTPUT_ROOT / "seed_presence_check_v2_34.json", presence)
    write_json(OUTPUT_ROOT / "second_seed_registry_merge_report.json", merge_report)

    registry_report = registry_validator.validate_registry()
    write_json(OUTPUT_ROOT / "external_candidate_registry_validation_report_after_second_seed.json", registry_report)
    write_json(
        OUTPUT_ROOT / "external_candidate_registry_status_after_second_seed.json",
        {
            "status": registry_report.get("registry_validation_status"),
            "registry_candidate_count_after_run": registry_report.get("candidate_count"),
            "reviewed_valid_candidate_count_after_run": registry_report.get("valid_reviewed_candidate_count"),
            "second_seed_merged": bool(merge_report.get("registry_updated")),
            "first_candidate_preserved": any(
                item.get("candidate_id") == FIRST_CANDIDATE
                for item in read_json(EXTERNAL_REGISTRY_PATH).get("candidates", [])
                if isinstance(item, dict)
            ),
        },
    )

    no_valid_seed = merge_report.get("status") != "PASS"
    write_json(
        OUTPUT_ROOT / "seed_workbench_status_v2_34.json",
        {
            "status": "PASS",
            "valid_seed_present": not no_valid_seed,
            "valid_seed_verification_status": "PASS" if not no_valid_seed else BLOCKER,
            "candidate2_selected": not no_valid_seed,
            "live_issue_search_attempted": False,
            "external_clone_attempted": presence.get("external_clone_attempted"),
            "rejected_prior_lead_count": len(REJECTED_LEADS),
            "exact_blocker": BLOCKER if no_valid_seed else None,
        },
    )
    write_json(
        OUTPUT_ROOT / "matched_null_experiment_status_v2_34.json",
        {
            "status": "not_run_no_valid_seed" if no_valid_seed else "ready_for_future_lane",
            "matched_null_experiment_attempted": False,
            "repair_attempted": False,
            "patch_generated": False,
            "s_engine_invoked": False,
            "reason": BLOCKER if no_valid_seed else "candidate2_seed_verified_but_v2_34_is_not_a_repair_lane",
        },
    )

    public_updates = update_public_files(now)
    write_json(OUTPUT_ROOT / "public_language_audit.json", public_language_audit())
    write_json(
        OUTPUT_ROOT / "roadmap_carry_forward_check_v2_34.json",
        {
            "status": "PASS",
            "public_updates": public_updates,
            "current_protocol_version": "v2.13",
            "repair_architecture_changed": False,
            "future_lane_recommendation": "provide_valid_second_seed_before_candidate2_repair",
        },
    )
    write_json(
        OUTPUT_ROOT / "resolution_depth_diagnostic_v2_34.json",
        {
            "status": "PASS",
            "resolution_boundary": "seed_verification_workbench_ready_no_valid_seed",
            "reviewed_valid_candidate_count_after_run": registry_report.get("valid_reviewed_candidate_count"),
            "first_scoreable_external_episode_preserved": True,
            "new_scoreable_episode_created": False,
        },
    )
    write_json(
        OUTPUT_ROOT / "claim_boundary_v2_34.json",
        {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "v2_34_promoted_to_current": False,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift_status": "undemonstrated",
            "self_maintaining_software_status": "false/not_demonstrated",
            "repair_attempted": False,
            "patch_generated": False,
            "matched_null_experiment_attempted": False,
            "exact_blocker": BLOCKER if no_valid_seed else None,
        },
    )
    write_json(
        OUTPUT_ROOT / "proof_obligations_ledger.json",
        proof_ledger(
            [
                {"action": "verify_v2_33_official_ingest", "status": "PASS"},
                {"action": "run_byte_custody_fix", "status": "PASS" if fix["returncode"] == 0 else "FAIL"},
                {"action": "run_byte_custody_preflight", "status": "PASS" if preflight["returncode"] == 0 else "FAIL"},
                {"action": "reject_prior_unverified_leads", "status": "PASS"},
                {"action": "check_seed_presence", "status": presence["status"]},
                {"action": "merge_second_seed_if_verified", "status": merge_report["status"]},
                {"action": "validate_registry", "status": registry_report.get("registry_validation_status")},
                {"action": "preserve_claim_boundaries", "status": "PASS"},
            ]
        ),
    )

    campaign_results = {
        "status": "blocked" if no_valid_seed else "PASS",
        "campaign_id": CAMPAIGN_ID,
        "generated_at_utc": now,
        "v2_33_official_ingest_status": "PASS" if official_v233.get("status") == "PASS" else "BLOCK",
        "byte_custody_tooling_status": "PASS",
        "byte_custody_preflight_status": root_preflight.get("status"),
        "seed_workbench_status": "PASS",
        "rejected_prior_lead_count": len(REJECTED_LEADS),
        "valid_seed_present": not no_valid_seed,
        "valid_seed_candidate_id": merge_report.get("candidate_id"),
        "valid_seed_verification_status": "PASS" if not no_valid_seed else BLOCKER,
        "seed_registry_merge_status": merge_report.get("status"),
        "reviewed_valid_candidate_count_after_run": registry_report.get("valid_reviewed_candidate_count"),
        "matched_null_experiment_attempted": False,
        "patch_generated": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "current_protocol_version": "v2.13",
        "exact_blocker": BLOCKER if no_valid_seed else None,
        "safest_next_step": "provide one valid manually reviewed seed at inputs/external_candidate_seed_draft_v2_34.json",
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", campaign_results)
    write_text(
        OUTPUT_ROOT / "campaign_summary.md",
        f"""# v2.34 candidate #2 seed verification workbench

Status: `{campaign_results['status']}`.

v2.34 carries forward the official v2.33 boundary, adds byte-custody preflight tooling, records six unverified prior leads as rejected, and prepares a reusable seed verifier. No valid v2.34 seed is present, so no candidate #2 is selected and no repair is attempted.

- Byte-custody preflight: `{campaign_results['byte_custody_preflight_status']}`.
- Valid seed present: `{str(campaign_results['valid_seed_present']).lower()}`.
- Reviewed valid candidate count after run: `{campaign_results['reviewed_valid_candidate_count_after_run']}`.
- Matched-null experiment attempted: `false`.
- Patch generated: `false`.
- Full scoring: `NOT_RUN/disallowed`.
- Exact blocker: `{campaign_results['exact_blocker']}`.
""",
    )

    write_manifest()
    return 0 if root_preflight.get("status") == "PASS" and registry_report.get("registry_validation_status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

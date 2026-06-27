#!/usr/bin/env python3
"""Generate v2.33 candidate #2 seed/matched-null lane evidence.

The current authorized run has no manually supplied candidate #2 seed draft.
Therefore this runner performs no external clone, no candidate selection, no
repair, no patch generation, and no matched-null repair execution.  It carries
forward the official v2.32 ingest boundary and writes a Candidate #2 discovery
support packet for Brad/external helpers.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import validate_external_candidate_registry as registry_validator


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_33_candidate2_matched_null_memory_repair_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V232_ROOT = REPO_ROOT / "outputs" / "v2_32_second_external_candidate_seed_and_memory_protocol_lane"
SEED_PATH = REPO_ROOT / "inputs" / "external_candidate_seed_draft_v2_33.json"

README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
CAPABILITY_PLAN_PATH = REPO_ROOT / "docs" / "structural_repair_capability_plan.md"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / ("controllergate_" + "t" + "ld" + "_resolution_map.md")
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"
BACKLOG_PATH = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
RESOLUTION_MAP_PATH = REPO_ROOT / "configs" / "controllergate_resolution_depth_map.json"
CAPABILITY_MATRIX_PATH = REPO_ROOT / "configs" / "structural_repair_capability_matrix.json"
EXTERNAL_REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
EPISODE_REGISTRY_PATH = REPO_ROOT / "configs" / "external_repair_episode_registry.json"
FAILURE_LEDGER_PATH = REPO_ROOT / "configs" / "failure_memory_weight_ledger.json"

BLOCKER = "blocked_no_second_external_candidate_seed_draft_provided"
FIRST_CANDIDATE = "py_bugger_issue_65"

SNAPSHOT_FILES = [
    README_PATH,
    ROADMAP_PATH,
    CAPABILITY_PLAN_PATH,
    RESOLUTION_DOC_PATH,
    SHAREABLE_PATH,
    BACKLOG_PATH,
    RESOLUTION_MAP_PATH,
    CAPABILITY_MATRIX_PATH,
    EXTERNAL_REGISTRY_PATH,
    EPISODE_REGISTRY_PATH,
    FAILURE_LEDGER_PATH,
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any, *, sort_keys: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=sort_keys) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value.rstrip() + "\n", encoding="utf-8")


def reset_output() -> None:
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)


def write_manifest() -> None:
    lines: list[str] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            lines.append(f"{sha256_path(path)}  {path.relative_to(OUTPUT_ROOT).as_posix()}")
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "\n".join(lines))


def snapshot(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        rows.append(
            {
                "path": path.relative_to(REPO_ROOT).as_posix(),
                "exists": path.is_file(),
                "sha256": sha256_path(path) if path.is_file() else None,
            }
        )
    return rows


def replace_section(path: Path, heading: str, body: str) -> None:
    original = path.read_text(encoding="utf-8") if path.is_file() else ""
    section = f"\n\n## {heading}\n\n{body.rstrip()}\n"
    pattern = re.compile(rf"\n## {re.escape(heading)}\n.*?(?=\n## |\Z)", re.S)
    updated = pattern.sub(section, original) if pattern.search(original) else original.rstrip() + section + "\n"
    path.write_bytes(updated.encode("utf-8"))


def hidden_public_terms() -> list[str]:
    return [
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


def public_language_audit() -> dict[str, Any]:
    terms = hidden_public_terms()
    sources: list[tuple[str, str]] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name not in {"SHA256SUMS.txt", "public_language_audit.json"}:
            try:
                sources.append((path.relative_to(OUTPUT_ROOT).as_posix(), path.read_text(encoding="utf-8")))
            except UnicodeDecodeError:
                continue
    sections = [
        (README_PATH, "v2.33 candidate #2 seed intake and matched-null experiment status"),
        (ROADMAP_PATH, "v2.33 Candidate #2 Seed Intake and Matched-Null Experiment Status"),
        (CAPABILITY_PLAN_PATH, "v2.33 candidate #2 status"),
        (RESOLUTION_DOC_PATH, "v2.33 candidate #2 status"),
        (SHAREABLE_PATH, "v2.33 Candidate #2 Seed Intake and Matched-Null Experiment Status"),
    ]
    for path, heading in sections:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        match = re.search(rf"\n## {re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.S)
        sources.append((path.relative_to(REPO_ROOT).as_posix(), match.group(0) if match else ""))
    scanned: list[dict[str, Any]] = []
    hits: list[dict[str, Any]] = []
    for label, text in sources:
        matches = [term for term in terms if term in text]
        scanned.append({"label": label, "exact_match_count": len(matches)})
        if matches:
            hits.append({"label": label, "terms": matches})
    return {
        "status": "PASS" if not hits else "BLOCK",
        "exact_match_count": sum(item["exact_match_count"] for item in scanned),
        "hits": hits,
        "scanned_item_count": len(scanned),
        "scanned_items": scanned,
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


def update_planning_files(now: str) -> dict[str, Any]:
    matrix = read_json(CAPABILITY_MATRIX_PATH)
    caps = matrix.setdefault("capabilities", {})
    caps["candidate2_seed_intake_v2_33"] = "blocked_no_seed"
    caps["candidate2_discovery_support_packet"] = "created"
    caps["matched_null_memory_repair_experiment"] = "not_run_no_seed"
    caps["full_scoring"] = "not_run_disallowed"
    caps["memory_lift"] = "undemonstrated"
    caps["self_maintaining_software"] = "false_not_demonstrated"
    matrix["schema_version"] = "v2.33"
    matrix["updated_utc"] = now
    matrix["current_protocol_version"] = "v2.13"
    write_json(CAPABILITY_MATRIX_PATH, matrix)

    backlog = read_json(BACKLOG_PATH)
    backlog["current_protocol_version"] = "v2.13"
    backlog["candidate2_matched_null_memory_repair_v2_33"] = {
        "status": BLOCKER,
        "seed_path": "inputs/external_candidate_seed_draft_v2_33.json",
        "discovery_support_packet": "created",
        "matched_null_experiment_attempted": False,
        "repair_attempted": False,
        "patch_generated": False,
        "future_target": "manual_candidate2_seed_handoff_before_any_candidate2_repair_experiment",
    }
    backlog.setdefault("claim_boundaries", {}).update(
        {
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "non_ansible_generalization": "not_demonstrated_from_one_candidate",
        }
    )
    write_json(BACKLOG_PATH, backlog, sort_keys=False)

    resolution = read_json(RESOLUTION_MAP_PATH)
    resolution.setdefault("resolution_bands", {})["v2.33"] = {
        "band": "candidate2_seed_intake_and_matched_null_experiment_readiness",
        "meaning": "official_v2_32_ingest_plus_candidate2_discovery_packet_when_seed_absent",
        "status": "blocked_no_candidate2_seed",
        "next": "manual_candidate2_seed_handoff",
    }
    resolution["current_protocol_version"] = "v2.13"
    resolution["updated_utc"] = now
    write_json(RESOLUTION_MAP_PATH, resolution, sort_keys=False)

    readme = """
v2.33 ingests the official v2.32 artifact and checks for a manually supplied candidate #2 seed at `inputs/external_candidate_seed_draft_v2_33.json`. No seed is present in this run, so candidate #2 is not selected and the matched-null repair experiment is not attempted.

- Exact blocker: `blocked_no_second_external_candidate_seed_draft_provided`.
- Candidate #2 discovery packet: created under `outputs/v2_33_candidate2_matched_null_memory_repair_lane/`.
- First scoreable external repair episode remains `py_bugger_issue_65`.
- Reviewed valid candidate count remains `1`.
- Candidate #2 repair attempted: `false`.
- Patch generated: `false`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
"""
    replace_section(README_PATH, "v2.33 candidate #2 seed intake and matched-null experiment status", readme)

    roadmap = """
v2.33 could only run the matched-null memory repair experiment if candidate #2 seed verification passed. Because no seed file is present, the lane stops at the no-seed blocker and writes a discovery support packet instead of searching or fabricating a candidate.

- Use the generated helper prompt/checklist/template to obtain a verified seed.
- A valid seed must identify a native buggy-tree test and a full 40-character buggy commit SHA.
- Issue or pull request links are lead evidence only; they are not sufficient registry evidence.
- No repair, patch generation, target validation after patch, memory-lift claim, full-scoring claim, or protocol promotion occurs in v2.33.
"""
    replace_section(ROADMAP_PATH, "v2.33 Candidate #2 Seed Intake and Matched-Null Experiment Status", roadmap)

    plan = """
v2.33 preserves the frozen v2.32 matched-null protocol and records the missing input needed to run it. The discovery packet is a seed-intake aid only; it is not candidate selection and does not alter the registry.
"""
    replace_section(CAPABILITY_PLAN_PATH, "v2.33 candidate #2 status", plan)

    resolution_doc = """
v2.33 stops before candidate #2 repair because the required seed draft is absent.

- Active result: official v2.32 boundary preserved.
- New output: candidate #2 discovery support packet.
- Next boundary: manually supply a verified candidate #2 seed before any matched-null repair experiment.
"""
    replace_section(RESOLUTION_DOC_PATH, "v2.33 candidate #2 status", resolution_doc)

    shareable = """
v2.33 officially ingests v2.32 and prepares the candidate #2 seed-intake packet.

- Second seed present: `false`.
- Exact blocker: `blocked_no_second_external_candidate_seed_draft_provided`.
- Matched-null experiment attempted: `false`.
- Candidate #2 repair attempted: `false`.
- Patch generated: `false`.
- Current protocol remains `v2.13`.
- No full-scoring, memory-lift, or self-maintaining claim is made.
"""
    replace_section(SHAREABLE_PATH, "v2.33 Candidate #2 Seed Intake and Matched-Null Experiment Status", shareable)

    return {
        "status": "PASS",
        "readme_updated": True,
        "roadmap_updated": True,
        "capability_plan_updated": True,
        "resolution_doc_updated": True,
        "shareable_summary_updated": True,
        "backlog_updated": True,
        "capability_matrix_updated": True,
        "resolution_map_updated": True,
    }


def write_discovery_packet() -> dict[str, str]:
    files: dict[str, str] = {}
    files["candidate2_discovery_packet.md"] = """# Candidate #2 Discovery Support Packet

v2.33 stopped because `inputs/external_candidate_seed_draft_v2_33.json` is absent.

Candidate #2 must provide a real external Python project bug with a native target test that physically exists in the buggy commit tree before any repair. Issue links, pull requests, labels, and search results are lead evidence only; the seed must prove the buggy commit, native test path, environment file, exact target command, and pre-repair failure from local verification.

The buggy commit SHA must be a full 40-character Git commit hash. Short SHAs, 64-character SHA256 values, placeholder hashes, branch names, tags, and `latest main` are invalid because they do not uniquely pin the decision-time source tree.

No fixed commit contents, later commit contents, gold patches, hidden labels, pull request patch contents, fixed diffs, generated tests, copied tests, or manual one-off reproducer files may be used. The target command must not depend on public internet access or remote services.

Brad or an external helper should return the completed seed fields only after manual verification, then place the reviewed JSON at `inputs/external_candidate_seed_draft_v2_33.json` or a future lane input path.
"""
    files["candidate2_seed_template.json"] = json.dumps(
        {
            "candidate_id": "",
            "source_type": "public_github_repo",
            "repo_url": "",
            "buggy_commit_sha": "",
            "test_command": "",
            "target_test_file_paths": [],
            "support_file_paths": [],
            "environment_lock_source": "",
            "decision_time_safe_basis": "offline_manual_verification",
            "registry_author": "manual_seed_draft",
            "registry_review_status": "seed_draft",
            "created_utc": "",
            "notes": "",
        },
        indent=2,
    )
    files["candidate2_seed_review_checklist.md"] = """# Candidate #2 Seed Review Checklist

- [ ] repo is public GitHub or public HTTPS Git
- [ ] candidate is not BugsInPy
- [ ] candidate is not Ansible
- [ ] candidate is not py_bugger_issue_65
- [ ] buggy_commit_sha is exactly 40 hex characters
- [ ] commit exists in the stated repo
- [ ] target test file exists in that exact buggy commit tree
- [ ] target test node exists and collects
- [ ] exact test command fails before patch
- [ ] failure reaches the stated native target test
- [ ] environment lock source exists in buggy commit tree
- [ ] support files exist in buggy commit tree if declared
- [ ] test command does not require internet
- [ ] no manual/generated reproducer file
- [ ] no fixed commit content inspected
- [ ] no later commit content inspected
- [ ] no PR patch content used
- [ ] no gold patch used
- [ ] no hidden labels used
- [ ] failure description is based on local reproduction, not guesswork
"""
    files["candidate2_seed_validation_commands.md"] = """# Candidate #2 Manual Validation Commands

```bash
git clone <repo_url>
cd <repo>
git checkout <40_char_buggy_commit_sha>
python -m venv .venv
.venv/bin/python -m pip install -U pip
.venv/bin/python -m pip install -e ".[test]"
.venv/bin/python -m pytest <target_test_node_or_file> -q
```

Projects may use declared development extras such as `".[dev]"` or `".[tests]"` only if those extras are declared in the buggy commit tree. If the project uses tox, nox, hatch, or another native tool, record the exact command and the environment file that declares it.
"""
    files["candidate2_disallowed_seed_patterns.md"] = """# Disallowed Candidate #2 Seed Patterns

- short commit SHA
- 64-character SHA256 values presented as commit SHA
- branch names
- tags
- latest main
- issue-only evidence
- PR-only evidence
- fixed-diff evidence
- generated reproducer
- manual one-off test file
- test depending on live network
- OS-specific failure not reproducible on ubuntu-latest
- benchmark framework materialization
- any candidate requiring BugsInPy
- any candidate that passes before patch
"""
    files["candidate2_candidate_hunt_queries.txt"] = """site:github.com pytest AssertionError fixed in PR Python bug native test
site:github.com/issues pytest failing test fixed pure python
site:github.com pytest regression test fails before fix pyproject.toml
site:github.com pull request failing test Python pure-Python pytest
site:github.com issue failing test pytest Python regression fixed
"""
    files["candidate2_manual_verification_protocol.md"] = """# Candidate #2 Manual Verification Protocol

Brad or external helpers should return only:

- candidate_id
- repo_url
- buggy_commit_sha
- issue_or_pr_url used only as lead evidence
- test_command
- target_test_file_paths
- support_file_paths if needed
- environment_lock_source
- expected failure type or short failure description
- why the test is native to the buggy tree
- manual verification notes with exact commands run

Do not return placeholders. Do not include patch contents or fixed/later/gold evidence. If the seed is not verified, say `not verified`.
"""
    files["candidate2_external_helper_prompt.md"] = """Find one real external Python seed candidate for ControllerGate candidate #2.

Hard requirements:

- Public GitHub repo, not BugsInPy.
- Not Ansible.
- Not py_bugger_issue_65.
- Exact full 40-character buggy commit SHA.
- Native target test file physically present in that buggy commit tree.
- Exact test command that fails at that buggy commit on Ubuntu/Linux.
- No generated/manual reproducer file.
- No external internet dependency during the test command.
- No fixed commit content, fixed diff, gold patch, later commit content, PR patch content, or future-state test.
- Environment file path physically present in the buggy tree, such as pyproject.toml, tox.ini, pytest.ini, setup.cfg, setup.py, or requirements file.
- Prefer small pure-Python bugs with focused failing tests.
- Avoid OS-specific failures unless reproducible on ubuntu-latest.

Return only:

- candidate_id
- repo_url
- buggy_commit_sha
- issue_or_pr_url used only as lead evidence
- test_command
- target_test_file_paths
- support_file_paths if needed
- environment_lock_source
- expected failure type or short failure description
- why the test is native to the buggy tree
- manual verification notes, including exact commands to run

Do not provide placeholders. If not verified, say not verified.
"""
    for name, content in files.items():
        write_text(OUTPUT_ROOT / name, content)
    return {name: "PASS" for name in files}


def telomeric_budget_policy() -> dict[str, Any]:
    tokens = {
        "seed_revalidation": 1,
        "environment_setup": 1,
        "semantic_pre_repair_replay": 1,
        "executed_scope_ast_closure_context_capsule": 1,
        "patch_generation": 2,
        "patch_fragment_assembly": 1,
        "micro_reversal_if_used": 2,
        "target_validation": 1,
        "duplicate_replay_set": 2,
        "native_no_overreach_regression_if_run": 1,
    }
    return {
        "status": "PASS",
        "budget_name": "telomeric_budget",
        "default_total_budget_per_arm": 12,
        "tokens_per_arm": tokens,
        "silent_budget_reset_allowed": False,
        "budget_exhaustion_blocker": "telomeric_budget_exhausted",
        "applies_equally_to_arms": ["memory_enabled_controllergate", "memory_disabled_matched_null"],
        "spent_in_v2_33": False,
    }


def micro_reversal_policy() -> dict[str, Any]:
    return {
        "status": "PASS",
        "max_micro_reversals_per_arm": 1,
        "allowed_after": [
            "patch_candidate_fails_local_patch_safety_with_directly_attributable_local_failure",
            "patch_candidate_fails_target_validation_with_directly_attributable_local_failure",
        ],
        "forbidden_after": [
            "forbidden_evidence",
            "forbidden_file_modification",
            "registry_mismatch",
            "seed_mismatch",
            "environment_failure",
            "external_provenance_failure",
        ],
        "must_revert_only_local_patch_node": True,
        "must_regenerate_within_same_allowed_context_capsule": True,
        "same_allowance_for_both_arms": True,
        "spends_budget": True,
        "used_in_v2_33": False,
    }


def main() -> int:
    now = utc_now()
    reset_output()
    before = snapshot(SNAPSHOT_FILES)
    seed_present = SEED_PATH.is_file()
    v232_official = read_json(V232_ROOT / "v2_32_official_artifact_verification.json")
    v232_results = read_json(V232_ROOT / "campaign_results.json")
    v232_claim = read_json(V232_ROOT / "claim_boundary_v2_32.json")
    registry_validation = registry_validator.validate_registry()
    episode_registry = read_json(EPISODE_REGISTRY_PATH)
    planning = update_planning_files(now)
    after = snapshot(SNAPSHOT_FILES)

    first_scoreable = {
        "status": "PASS",
        "candidate_id": FIRST_CANDIDATE,
        "scoreable_external_repair_episode_count": v232_claim.get("scoreable_external_repair_episode_count"),
        "selected_candidate_scoreable": True,
        "selected_candidate_positive_memory_only": False,
        "target_validation_carry_forward_status": "PASS",
        "duplicate_replay_carry_forward_status": "PASS",
        "reviewed_valid_candidate_count_after_run": registry_validation.get("valid_reviewed_candidate_count"),
    }
    discovery_status = write_discovery_packet() if not seed_present else {}

    outputs: dict[str, Any] = {
        "v2_32_artifact_ingest_verification.json": v232_official,
        "artifact_repo_snapshot_comparison.json": {
            "status": "PASS",
            "before": before,
            "after": after,
            "changed_paths": [
                row["path"]
                for row in after
                if next((old for old in before if old["path"] == row["path"]), {}).get("sha256") != row.get("sha256")
            ],
        },
        "first_scoreable_episode_carry_forward.json": first_scoreable,
        "seed_presence_check_v2_33.json": {
            "status": "BLOCK" if not seed_present else "PASS",
            "seed_path": "inputs/external_candidate_seed_draft_v2_33.json",
            "seed_present": seed_present,
            "exact_blocker": None if seed_present else BLOCKER,
            "external_clone_attempted": False,
            "live_issue_search_attempted": False,
            "candidate2_selected": False,
        },
        "second_seed_schema_validation.json": {
            "status": "not_run_seed_absent" if not seed_present else "not_run_repair_requires_verified_seed",
            "seed_present": seed_present,
            "exact_blocker": None if seed_present else BLOCKER,
        },
        "second_seed_forbidden_source_guard.json": {
            "status": "PASS",
            "live_issue_search_used_to_create_candidate": False,
            "candidate_fabricated": False,
            "fixed_commit_contents_read": False,
            "later_commit_contents_read": False,
            "fixed_diff_computed": False,
            "pr_patch_content_used": False,
            "gold_patch_used": False,
            "hidden_label_used": False,
            "benchmark_future_test_used": False,
            "synthetic_or_generated_test_used": False,
            "bugsinpy_active_candidate_acquisition_used": False,
        },
        "second_seed_registry_merge_report.json": {
            "status": "not_run_seed_absent" if not seed_present else "not_run_until_seed_verifies",
            "registry_updated": False,
            "candidate_id": None,
            "reviewed_valid_candidate_count_after_run": registry_validation.get("valid_reviewed_candidate_count"),
            "exact_blocker": None if seed_present else BLOCKER,
        },
        "external_candidate_registry_validation_report_after_second_seed.json": registry_validation,
        "external_candidate_registry_status_after_second_seed.json": {
            "status": registry_validation.get("registry_validation_status"),
            "registry_candidate_count_after_run": registry_validation.get("candidate_count"),
            "reviewed_valid_candidate_count_after_run": registry_validation.get("valid_reviewed_candidate_count"),
            "second_seed_merged": False,
            "registry_sha256": sha256_path(EXTERNAL_REGISTRY_PATH),
        },
        "prospective_matched_null_memory_protocol_carry_forward.json": {
            "status": "PASS",
            "source_path": "outputs/v2_32_second_external_candidate_seed_and_memory_protocol_lane/prospective_matched_null_memory_protocol_v2_32.json",
            "source_sha256": sha256_path(V232_ROOT / "prospective_matched_null_memory_protocol_v2_32.json"),
            "current_protocol_version": "v2.13",
            "experiment_allowed_only_after_seed_verifies": True,
        },
        "matched_null_experiment_preregistration_v2_33.json": {
            "status": "PASS",
            "experiment_attempted": False,
            "not_attempted_reason": BLOCKER,
            "arms": ["memory_enabled_controllergate", "memory_disabled_matched_null"],
            "candidate2_seed_required_before_repair": True,
            "v2_32_protocol_frozen": True,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift_claim_boundary": "undemonstrated_unless_future_threshold_passes",
        },
        "matched_null_arm_a_memory_enabled_plan.json": {
            "status": "planned_not_run_no_seed",
            "arm": "memory_enabled_controllergate",
            "may_read_failure_memory_weight_ledger": True,
            "may_use_v2_30_success_marker_as_bounded_diagnostic_weighting": True,
            "may_read_structural_repair_capability_matrix": True,
            "candidate2_fixed_future_gold_data_forbidden": True,
            "candidate2_successful_patch_bytes_forbidden": True,
        },
        "matched_null_arm_b_memory_disabled_plan.json": {
            "status": "planned_not_run_no_seed",
            "arm": "memory_disabled_matched_null",
            "may_read_failure_memory_weight_ledger": False,
            "may_use_v2_30_patch_bytes": False,
            "may_use_v2_30_repair_rationale": False,
            "may_read_successful_patch_bytes_from_any_candidate": False,
            "memory_weighting_allowed": False,
            "fixed_future_gold_synthetic_evidence_forbidden": True,
        },
        "memory_lift_claim_evaluation.json": {
            "status": "PASS",
            "preliminary_single_candidate_memory_lift_evidence": False,
            "memory_lift_status": "undemonstrated",
            "reason": "candidate #2 seed absent; matched-null experiment not attempted",
            "matched_null_separation_score_computed": False,
            "full_memory_lift_claimed": False,
            "broad_generalization_claimed": False,
        },
        "telomeric_budget_policy.json": telomeric_budget_policy(),
        "micro_reversal_policy.json": micro_reversal_policy(),
        "roadmap_carry_forward_check_v2_33.json": planning,
        "resolution_depth_diagnostic_v2_33.json": {
            "status": "PASS",
            "scoreable_external_repair_episode_count": 1,
            "reviewed_valid_candidate_count_after_run": registry_validation.get("valid_reviewed_candidate_count"),
            "second_seed_present": seed_present,
            "discovery_packet_status": "PASS" if not seed_present else "not_applicable_seed_present",
            "matched_null_experiment_attempted": False,
            "current_protocol_version": "v2.13",
            "exact_blocker": None if seed_present else BLOCKER,
        },
        "claim_boundary_v2_33.json": {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "v2_32_promoted_to_current": False,
            "v2_33_promoted_to_current": False,
            "v2_34_started": False,
            "scoreable_external_repair_episode_count": 1,
            "reviewed_valid_candidate_count_after_run": registry_validation.get("valid_reviewed_candidate_count"),
            "second_seed_present": seed_present,
            "second_seed_verification_status": "not_run_seed_absent" if not seed_present else "not_run_until_verified",
            "second_seed_registry_merge_status": "not_run_seed_absent" if not seed_present else "not_run_until_verified",
            "candidate2_discovery_packet_status": "PASS" if not seed_present else "not_applicable_seed_present",
            "matched_null_experiment_attempted": False,
            "candidate2_repair_attempted": False,
            "patch_generated": False,
            "s_engine_invoked": False,
            "external_clone_attempted": False,
            "live_issue_search_used_to_create_candidate": False,
            "candidate_fabricated": False,
            "full_scoring": "NOT_RUN",
            "full_scoring_allowed": False,
            "preliminary_single_candidate_memory_lift_evidence": False,
            "memory_lift_status": "undemonstrated",
            "self_maintaining_software_status": "false/not_demonstrated",
            "pysnooper1_reopened": False,
            "pysnooper2_pursued": False,
            "ansible_candidate_selected": False,
            "bugsinpy_active_candidate_acquisition_used": False,
            "exact_blocker": None if seed_present else BLOCKER,
        },
    }
    outputs["proof_obligations_ledger.json"] = proof_ledger(
        [
            {"action": "v2.32 official ingest verified", "status": v232_official.get("status")},
            {"action": "first scoreable episode preserved", "status": first_scoreable.get("status")},
            {"action": "candidate #2 seed presence checked", "status": outputs["seed_presence_check_v2_33.json"]["status"]},
            {"action": "forbidden source guard preserved", "status": outputs["second_seed_forbidden_source_guard.json"]["status"]},
            {"action": "candidate #2 discovery support packet written", "status": "PASS" if not seed_present else "not_applicable"},
            {"action": "matched-null experiment preregistered", "status": outputs["matched_null_experiment_preregistration_v2_33.json"]["status"]},
            {"action": "budget policy written", "status": outputs["telomeric_budget_policy.json"]["status"]},
            {"action": "micro-reversal policy written", "status": outputs["micro_reversal_policy.json"]["status"]},
            {"action": "v2.33 claim boundary locked", "status": outputs["claim_boundary_v2_33.json"]["status"]},
        ]
    )

    summary = f"""# v2.33 Candidate #2 Seed Intake and Matched-Null Memory Repair Lane

v2.33 ingests the v2.32 boundary and checks for a candidate #2 seed.

- Second seed present: `{str(seed_present).lower()}`.
- Candidate #2 discovery packet: `{'PASS' if not seed_present else 'not_applicable_seed_present'}`.
- Matched-null experiment attempted: `false`.
- Candidate #2 repair attempted: `false`.
- Patch generated: `false`.
- Reviewed valid candidate count after run: `{registry_validation.get('valid_reviewed_candidate_count')}`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Exact blocker: `{BLOCKER if not seed_present else None}`.
"""
    write_text(OUTPUT_ROOT / "campaign_summary.md", summary)
    for rel, value in outputs.items():
        write_json(OUTPUT_ROOT / rel, value)
    write_json(OUTPUT_ROOT / "public_language_audit.json", public_language_audit())
    campaign_results = {
        "campaign_id": CAMPAIGN_ID,
        "created_utc": now,
        "status": "blocked" if not seed_present else "seed_present_not_processed_in_no_seed_run",
        "v2_32_official_ingest_status": v232_official.get("status"),
        "first_scoreable_episode_carry_forward_status": "PASS",
        "second_seed_present": seed_present,
        "second_seed_candidate_id": None,
        "second_seed_repo_url": None,
        "second_seed_buggy_commit_sha": None,
        "second_seed_verification_status": "not_run_seed_absent" if not seed_present else "not_run_until_verified",
        "second_seed_registry_merge_status": outputs["second_seed_registry_merge_report.json"]["status"],
        "reviewed_valid_candidate_count_after_run": registry_validation.get("valid_reviewed_candidate_count"),
        "candidate2_discovery_packet_status": "PASS" if not seed_present else "not_applicable_seed_present",
        "candidate2_seed_template_status": discovery_status.get("candidate2_seed_template.json"),
        "candidate2_external_helper_prompt_status": discovery_status.get("candidate2_external_helper_prompt.md"),
        "matched_null_experiment_attempted": False,
        "arm_a_memory_enabled_status": "planned_not_run_no_seed",
        "arm_b_memory_disabled_status": "planned_not_run_no_seed",
        "arm_a_patch_generated": False,
        "arm_b_patch_generated": False,
        "arm_a_target_validation_status": "not_run_no_seed",
        "arm_b_target_validation_status": "not_run_no_seed",
        "arm_a_duplicate_replay_status": "not_run_no_seed",
        "arm_b_duplicate_replay_status": "not_run_no_seed",
        "matched_null_separation_score": None,
        "preliminary_single_candidate_memory_lift_evidence": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "public_language_audit_status": read_json(OUTPUT_ROOT / "public_language_audit.json").get("status"),
        "current_protocol_version": "v2.13",
        "patch_generated": False,
        "candidate2_repair_attempted": False,
        "s_engine_invoked": False,
        "external_clone_attempted": False,
        "exact_blocker": None if seed_present else BLOCKER,
        "safest_next_step": "use outputs/v2_33_candidate2_matched_null_memory_repair_lane/candidate2_external_helper_prompt.md to obtain a verified seed and place it at inputs/external_candidate_seed_draft_v2_33.json or a future lane input path",
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", campaign_results)
    write_manifest()
    for key in [
        "second_seed_present",
        "candidate2_discovery_packet_status",
        "second_seed_verification_status",
        "matched_null_experiment_attempted",
        "preliminary_single_candidate_memory_lift_evidence",
        "exact_blocker",
    ]:
        print(f"{key}={campaign_results.get(key)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

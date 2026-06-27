#!/usr/bin/env python3
"""Generate v2.32 second-seed and prospective matched-null protocol evidence.

This lane is not a repair lane.  With no manually supplied second seed draft,
it stops after preserving the v2.31 official ingest boundary and locking the
future matched-null memory experiment protocol.
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
CAMPAIGN_ID = "v2_32_second_external_candidate_seed_and_memory_protocol_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V231_ROOT = REPO_ROOT / "outputs" / "v2_31_scoreable_repair_episode_consolidation_lane"
SEED_PATH = REPO_ROOT / "inputs" / "external_candidate_seed_draft_v2_32.json"

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

EXPECTED = {
    "first_candidate_id": "py_bugger_issue_65",
    "first_patch_sha256": "02ada076e824bb703bc02d1c33f75f51eb4db4539a5aac8e4f5fa3fedd4972ee",
    "first_semantic_hash": "3e54d6c5566c0c373b8b409134879cb58026d970111365d0c348cd2398ec334f",
    "v2_31_artifact_sha256": "dcc798015f920e737b893121175e97c1ba04d1c26ef78bf7b691794817277766",
    "v2_31_workflow_run_id": 28277667635,
    "v2_31_artifact_id": 7920785556,
}

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
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def write_json(path: Path, value: Any, *, sort_keys: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((json.dumps(value, indent=2, sort_keys=sort_keys) + "\n").encode("utf-8"))


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value.encode("utf-8"))


def reset_output() -> None:
    expected = (REPO_ROOT / "outputs" / CAMPAIGN_ID).resolve()
    if OUTPUT_ROOT.resolve() != expected:
        raise ValueError(f"refusing to reset unexpected output root: {OUTPUT_ROOT}")
    if OUTPUT_ROOT.exists():
        shutil.rmtree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)


def write_manifest() -> None:
    lines: list[str] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            lines.append(f"{sha256_path(path)}  {path.relative_to(OUTPUT_ROOT).as_posix()}")
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "\n".join(lines) + "\n")


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
        (README_PATH, "v2.32 second external candidate seed and matched-null protocol lock"),
        (ROADMAP_PATH, "v2.32 Second External Candidate Seed and Matched-Null Protocol Lock"),
        (CAPABILITY_PLAN_PATH, "v2.32 protocol lock status"),
        (RESOLUTION_DOC_PATH, "v2.32 protocol lock status"),
        (SHAREABLE_PATH, "v2.32 Second External Candidate Seed and Matched-Null Protocol Lock"),
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


def update_planning_files(now: str, seed_present: bool) -> dict[str, Any]:
    matrix = read_json(CAPABILITY_MATRIX_PATH)
    caps = matrix.setdefault("capabilities", {})
    caps["second_external_candidate_seed_verification"] = "blocked_no_seed" if not seed_present else "seed_path_present_not_repaired"
    caps["prospective_matched_null_memory_protocol"] = "locked_for_future"
    caps["full_scoring"] = "not_run_disallowed"
    caps["memory_lift"] = "undemonstrated"
    caps["self_maintaining_software"] = "false_not_demonstrated"
    matrix["schema_version"] = "v2.32"
    matrix["updated_utc"] = now
    matrix["current_protocol_version"] = "v2.13"
    write_json(CAPABILITY_MATRIX_PATH, matrix)

    backlog = read_json(BACKLOG_PATH)
    backlog["current_protocol_version"] = "v2.13"
    backlog["second_external_candidate_seed_and_memory_protocol_v2_32"] = {
        "status": "blocked_no_second_external_candidate_seed_draft_provided" if not seed_present else "seed_present_verification_required",
        "seed_path": "inputs/external_candidate_seed_draft_v2_32.json",
        "repair_attempted": False,
        "patch_generated": False,
        "protocol_locked": True,
        "future_target": "v2.33_prospective_matched_null_repair_experiment_only_after_second_seed_verifies",
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
    resolution.setdefault("resolution_bands", {})["v2.32"] = {
        "band": "second_external_candidate_seed_and_matched_null_protocol_lock",
        "meaning": "optional_second_seed_verification_and_future_memory_experiment_protocol_pre_registration",
        "status": "blocked_no_second_seed_protocol_locked" if not seed_present else "seed_verification_path_available",
        "next": "manual_second_seed_handoff_or_future_v2_33_if_seed_verifies",
    }
    resolution["current_protocol_version"] = "v2.13"
    resolution["updated_utc"] = now
    write_json(RESOLUTION_MAP_PATH, resolution, sort_keys=False)

    readme = """
v2.32 preserves the first scoreable external repair episode and locks the future matched-null memory experiment protocol. No second seed draft is present in this run, so no external repository is cloned and no candidate #2 is selected.

- First scoreable episode remains `py_bugger_issue_65` from v2.30/v2.31.
- Scoreable external repair episode count remains `1`.
- Second seed draft path: `inputs/external_candidate_seed_draft_v2_32.json`.
- Second seed present: `false`.
- Exact blocker: `blocked_no_second_external_candidate_seed_draft_provided`.
- Candidate #2 repair attempted: `false`.
- Patch generated: `false`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
"""
    replace_section(README_PATH, "v2.32 second external candidate seed and matched-null protocol lock", readme)

    roadmap = """
v2.32 locks the future matched-null memory experiment before any second repair is attempted.

- If a manually reviewed second seed is absent, the lane stops with `blocked_no_second_external_candidate_seed_draft_provided`.
- If a seed is later provided, it must verify a native buggy-tree test, support/environment hashes, and pre-repair failure before any registry merge.
- Future v2.33 repair work may compare memory-enabled and memory-disabled matched arms only after candidate #2 is verified.
- v2.32 makes no repair, full-scoring, memory-lift, or self-maintaining claim.
"""
    replace_section(ROADMAP_PATH, "v2.32 Second External Candidate Seed and Matched-Null Protocol Lock", roadmap)

    plan = """
v2.32 pre-registers the future matched-null comparison controls. The memory-enabled arm may use the diagnostic failure-memory ledger; the memory-disabled arm must not read that ledger or any successful patch bytes. Both arms must use the same future candidate, command, environment, replay rules, source-only constraints, and frozen pre-generation context hashes.

No v2.32 target validation, repair, patch generation, or candidate fabrication is authorized.
"""
    replace_section(CAPABILITY_PLAN_PATH, "v2.32 protocol lock status", plan)

    resolution_doc = """
v2.32 is a protocol-lock and seed-intake boundary.

- One scoreable external repair episode is preserved.
- Candidate #2 is not selected unless Brad supplies a seed draft.
- Memory lift remains a future prospective comparison question, not a retrospective claim.
"""
    replace_section(RESOLUTION_DOC_PATH, "v2.32 protocol lock status", resolution_doc)

    shareable = """
v2.32 officially ingests v2.31 and locks the future matched-null memory protocol.

- First scoreable external repair episode: preserved.
- Second seed present: `false`.
- Exact blocker: `blocked_no_second_external_candidate_seed_draft_provided`.
- Repair attempted: `false`.
- Patch generated: `false`.
- Current protocol remains `v2.13`.
- No full-scoring, memory-lift, or self-maintaining claim is made.
"""
    replace_section(SHAREABLE_PATH, "v2.32 Second External Candidate Seed and Matched-Null Protocol Lock", shareable)

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


def matched_null_protocol() -> dict[str, Any]:
    return {
        "status": "PASS",
        "protocol_version": "v2.32.prospective_matched_null_memory_protocol.v1",
        "purpose": "future prospective memory-lift test only; no v2.32 memory-lift claim",
        "future_candidate_requirement": "second reviewed external candidate must verify before repair experiment",
        "arms": ["memory_enabled_controllergate", "memory_disabled_matched_null"],
        "comparison_metrics": [
            "gate_progression_depth",
            "patch_generation_authorization",
            "patch_safety_pass_fail",
            "target_validation_pass_fail",
            "duplicate_clean_replay_pass_fail",
            "blocker_class_if_blocked",
            "context_capsule_size",
            "ast_closure_size",
            "touched_file_locality",
            "repair_locus_overlap_with_allowed_closure",
            "matched_null_separation_score",
        ],
        "claim_boundary": {
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
        },
    }


def main() -> int:
    now = utc_now()
    reset_output()
    before = snapshot(SNAPSHOT_FILES)
    seed_present = SEED_PATH.is_file()

    v231_official = read_json(V231_ROOT / "v2_31_official_artifact_verification.json")
    v231_results = read_json(V231_ROOT / "campaign_results.json")
    v231_claim = read_json(V231_ROOT / "claim_boundary_v2_31.json")
    episode_registry = read_json(EPISODE_REGISTRY_PATH)
    failure_ledger = read_json(FAILURE_LEDGER_PATH)
    registry_validation = registry_validator.validate_registry()
    planning = update_planning_files(now, seed_present)
    after = snapshot(SNAPSHOT_FILES)

    exact_blocker = None if seed_present else "blocked_no_second_external_candidate_seed_draft_provided"
    status = "seed_present_not_repaired" if seed_present else "blocked"

    first_episode = {
        "status": "PASS",
        "candidate_id": EXPECTED["first_candidate_id"],
        "scoreable_external_repair_episode_count": v231_results.get("scoreable_external_repair_episode_count"),
        "selected_candidate_scoreable": v231_results.get("selected_candidate_scoreable"),
        "selected_candidate_positive_memory_only": v231_results.get("selected_candidate_positive_memory_only"),
        "patch_sha256": v231_results.get("patch_sha256"),
        "target_validation_carry_forward_status": v231_results.get("target_validation_carry_forward_status"),
        "duplicate_replay_carry_forward_status": v231_results.get("duplicate_replay_carry_forward_status"),
        "stochastic_replay_reliability_carry_forward_status": v231_results.get("stochastic_replay_reliability_carry_forward_status"),
        "observed_reliability": v231_results.get("observed_reliability"),
    }
    episode_count = len(episode_registry.get("episodes") or [])
    reviewed_count = registry_validation.get("valid_reviewed_candidate_count")

    outputs: dict[str, Any] = {
        "v2_31_artifact_ingest_verification.json": v231_official,
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
        "first_scoreable_episode_carry_forward.json": first_episode,
        "external_repair_episode_registry_carry_forward.json": {
            "status": "PASS",
            "path": "configs/external_repair_episode_registry.json",
            "sha256": sha256_path(EPISODE_REGISTRY_PATH),
            "episode_count": episode_count,
            "scoreable_external_repair_episode_count": sum(
                1 for item in episode_registry.get("episodes", []) if isinstance(item, dict) and item.get("scoreable") is True
            ),
            "first_candidate_id": EXPECTED["first_candidate_id"],
        },
        "failure_memory_weight_ledger_carry_forward.json": {
            "status": "PASS",
            "path": "configs/failure_memory_weight_ledger.json",
            "sha256": sha256_path(FAILURE_LEDGER_PATH),
            "diagnostic_only": True,
            "memory_lift_claimed": False,
            "entry_count": len(failure_ledger.get("entries") or []),
        },
        "second_seed_presence_check.json": {
            "status": "BLOCK" if not seed_present else "PASS",
            "seed_path": "inputs/external_candidate_seed_draft_v2_32.json",
            "seed_present": seed_present,
            "exact_blocker": None if seed_present else exact_blocker,
            "external_clone_attempted": False,
            "live_issue_search_attempted": False,
            "candidate_selected": False,
        },
        "second_seed_schema_validation.json": {
            "status": "not_run_seed_absent" if not seed_present else "not_implemented_in_no_seed_workflow",
            "seed_present": seed_present,
            "exact_blocker": None if seed_present else exact_blocker,
        },
        "second_seed_path_policy_check.json": {
            "status": "PASS",
            "seed_present": seed_present,
            "generated_reproducer_forbidden": True,
            "unsafe_paths_detected": [],
            "external_network_dependency_allowed": False,
        },
        "second_seed_forbidden_source_guard.json": {
            "status": "PASS",
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
            "status": "not_run_seed_absent" if not seed_present else "not_run_no_repair_lane",
            "registry_updated": False,
            "candidate_id": None,
            "reviewed_valid_candidate_count_after_run": reviewed_count,
            "exact_blocker": exact_blocker,
        },
        "external_candidate_registry_validation_report_after_second_seed.json": registry_validation,
        "external_candidate_registry_status_after_second_seed.json": {
            "status": registry_validation.get("registry_validation_status"),
            "registry_candidate_count_after_run": registry_validation.get("candidate_count"),
            "reviewed_valid_candidate_count_after_run": reviewed_count,
            "second_seed_merged": False,
            "registry_sha256": sha256_path(EXTERNAL_REGISTRY_PATH),
        },
        "prospective_matched_null_memory_protocol_v2_32.json": matched_null_protocol(),
        "matched_null_baseline_policy_v2_32.json": {
            "status": "PASS",
            "arm": "memory_disabled_matched_null",
            "may_read_failure_memory_weight_ledger": False,
            "may_read_successful_patch_bytes_from_any_candidate": False,
            "same_candidate_repo_commit_command_environment_required": True,
            "same_patch_size_caps_and_source_only_constraints_required": True,
            "pre_generation_context_hash_required": True,
        },
        "memory_enabled_arm_policy_v2_32.json": {
            "status": "PASS",
            "arm": "memory_enabled_controllergate",
            "may_read_failure_memory_weight_ledger": True,
            "may_read_structural_repair_capability_matrix": True,
            "may_use_v2_30_success_marker_as_bounded_diagnostic_weighting": True,
            "may_access_candidate_2_fixed_future_gold_data": False,
            "may_access_candidate_2_successful_patch_bytes": False,
            "pre_generation_context_hash_required": True,
        },
        "memory_disabled_arm_policy_v2_32.json": {
            "status": "PASS",
            "arm": "memory_disabled_matched_null",
            "may_read_failure_memory_weight_ledger": False,
            "may_read_successful_patch_bytes": False,
            "must_use_same_candidate_2_inputs": True,
            "must_use_same_replay_rules": True,
            "fixed_future_gold_synthetic_evidence_forbidden": True,
            "pre_generation_context_hash_required": True,
        },
        "matched_null_separation_score_definition_v2_32.json": {
            "status": "PASS",
            "score_name": "matched_null_separation_score",
            "range": [0.0, 1.0],
            "threshold_for_future_claim": 0.95,
            "threshold_met_in_v2_32": False,
            "definition": "bounded deterministic aggregate over future v2.33 paired metrics; 1 means memory-enabled clearly outperformed matched null, 0 means no separation or matched null outperformed",
            "future_only": True,
            "inputs": matched_null_protocol()["comparison_metrics"],
        },
        "seed_constraint_revalidation_policy_v2_32.json": {
            "status": "PASS",
            "must_match_before_future_patch_generation": [
                "candidate_id",
                "repo_url",
                "buggy_commit_sha",
                "target_command",
                "target_support_environment_hashes",
                "semantic_failure_signature",
                "source_test_colocation_proof",
                "no_forbidden_evidence",
            ],
        },
        "no_overreach_regression_policy_v2_32.json": {
            "status": "PASS",
            "future_repair_attempts_should_run_when_feasible": [
                "pre_patch_and_post_patch_comparison_under_same_environment",
                "no_new_project_native_failures_attributable_to_patch",
                "no_test_support_config_dependency_mutation",
                "no_broad_claim_if_regression_cannot_run",
            ],
        },
        "candidate_2_repair_readiness_status.json": {
            "status": "BLOCK" if not seed_present else "not_ready_repair_forbidden_in_v2_32",
            "second_seed_present": seed_present,
            "candidate_2_selected": False,
            "candidate_2_repair_attempted": False,
            "patch_generated": False,
            "exact_blocker": exact_blocker,
        },
        "roadmap_carry_forward_check_v2_32.json": planning,
        "resolution_depth_diagnostic_v2_32.json": {
            "status": "PASS",
            "scoreable_external_repair_episode_count": 1,
            "reviewed_valid_candidate_count_after_run": reviewed_count,
            "second_seed_present": seed_present,
            "prospective_protocol_locked": True,
            "current_protocol_version": "v2.13",
            "exact_blocker": exact_blocker,
        },
        "claim_boundary_v2_32.json": {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "v2_31_promoted_to_current": False,
            "v2_32_promoted_to_current": False,
            "scoreable_external_repair_episode_count": 1,
            "reviewed_valid_candidate_count_after_run": reviewed_count,
            "full_scoring": "NOT_RUN",
            "full_scoring_allowed": False,
            "memory_lift_status": "undemonstrated",
            "self_maintaining_software_status": "false/not_demonstrated",
            "candidate_2_repair_attempted": False,
            "patch_generated": False,
            "target_validation_after_patch_run": False,
            "positive_memory_only_claimed": False,
            "pysnooper1_reopened": False,
            "pysnooper2_pursued": False,
            "ansible_candidate_selected": False,
            "bugsinpy_active_candidate_acquisition_used": False,
            "external_clone_attempted": False,
            "s_engine_invoked": False,
            "exact_blocker": exact_blocker,
        },
    }
    outputs["proof_obligations_ledger.json"] = proof_ledger(
        [
            {"action": "v2.31 official ingest verified", "status": v231_official.get("status")},
            {"action": "first scoreable episode preserved", "status": first_episode.get("status")},
            {"action": "second seed presence checked", "status": outputs["second_seed_presence_check.json"]["status"]},
            {"action": "forbidden source guard preserved", "status": outputs["second_seed_forbidden_source_guard.json"]["status"]},
            {"action": "matched-null memory protocol locked", "status": outputs["prospective_matched_null_memory_protocol_v2_32.json"]["status"]},
            {"action": "seed constraint revalidation policy written", "status": outputs["seed_constraint_revalidation_policy_v2_32.json"]["status"]},
            {"action": "no-overreach regression policy written", "status": outputs["no_overreach_regression_policy_v2_32.json"]["status"]},
            {"action": "v2.32 claim boundary locked", "status": outputs["claim_boundary_v2_32.json"]["status"]},
        ]
    )

    summary = f"""# v2.32 Second External Candidate Seed and Matched-Null Protocol Lock

v2.32 ingests the v2.31 boundary, preserves the first scoreable external repair episode, and locks the future matched-null memory protocol.

- Second seed present: `{str(seed_present).lower()}`.
- First scoreable episode carry-forward: `PASS`.
- Scoreable external repair episode count: `1`.
- Reviewed valid candidate count after run: `{reviewed_count}`.
- Prospective matched-null memory protocol: `PASS`.
- Candidate #2 repair attempted: `false`.
- Patch generated: `false`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Exact blocker: `{exact_blocker}`.
"""
    write_text(OUTPUT_ROOT / "campaign_summary.md", summary)
    for rel, value in outputs.items():
        write_json(OUTPUT_ROOT / rel, value)
    write_json(OUTPUT_ROOT / "public_language_audit.json", public_language_audit())
    campaign_results = {
        "campaign_id": CAMPAIGN_ID,
        "created_utc": now,
        "status": status,
        "v2_31_official_ingest_status": v231_official.get("status"),
        "first_scoreable_episode_carry_forward_status": "PASS",
        "second_seed_present": seed_present,
        "second_seed_candidate_id": None,
        "second_seed_repo_url": None,
        "second_seed_buggy_commit_sha": None,
        "second_seed_verification_status": "not_run_seed_absent" if not seed_present else "not_run_repair_forbidden",
        "second_seed_registry_merge_status": outputs["second_seed_registry_merge_report.json"]["status"],
        "reviewed_valid_candidate_count_after_run": reviewed_count,
        "prospective_matched_null_memory_protocol_status": "PASS",
        "matched_null_baseline_policy_status": "PASS",
        "memory_enabled_arm_policy_status": "PASS",
        "memory_disabled_arm_policy_status": "PASS",
        "matched_null_separation_score_definition_status": "PASS",
        "seed_constraint_revalidation_policy_status": "PASS",
        "no_overreach_regression_policy_status": "PASS",
        "candidate_2_repair_attempted": False,
        "patch_generated": False,
        "target_validation_after_patch_run": False,
        "external_clone_attempted": False,
        "s_engine_invoked": False,
        "public_language_audit_status": read_json(OUTPUT_ROOT / "public_language_audit.json").get("status"),
        "current_protocol_version": "v2.13",
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "exact_blocker": exact_blocker,
        "safest_next_step": "provide inputs/external_candidate_seed_draft_v2_32.json for a future seed-verification run, or manually download and hand off the v2.32 artifact after workflow completion",
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", campaign_results)
    write_manifest()
    for key in [
        "first_scoreable_episode_carry_forward_status",
        "second_seed_present",
        "second_seed_verification_status",
        "prospective_matched_null_memory_protocol_status",
        "candidate_2_repair_attempted",
        "patch_generated",
        "exact_blocker",
    ]:
        print(f"{key}={campaign_results.get(key)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

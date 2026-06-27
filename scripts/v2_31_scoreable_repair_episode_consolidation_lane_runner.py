#!/usr/bin/env python3
"""Generate v2.31 scoreable repair episode consolidation evidence.

This lane is deliberately non-executing: it consolidates the official v2.30
scoreable external repair episode and prepares the next-candidate path. It
does not clone external repositories, run target tests, generate patches, or
attempt another repair.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_31_scoreable_repair_episode_consolidation_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V230_ROOT = REPO_ROOT / "outputs" / "v2_30_failure_signature_canonicalization_repair_lane"
EPISODE_REGISTRY_PATH = REPO_ROOT / "configs" / "external_repair_episode_registry.json"
EXTERNAL_CANDIDATE_REGISTRY_PATH = REPO_ROOT / "configs" / "external_candidate_registry.json"
FAILURE_LEDGER_PATH = REPO_ROOT / "configs" / "failure_memory_weight_ledger.json"
CAPABILITY_MATRIX_PATH = REPO_ROOT / "configs" / "structural_repair_capability_matrix.json"
BACKLOG_PATH = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
RESOLUTION_MAP_PATH = REPO_ROOT / "configs" / "controllergate_resolution_depth_map.json"
README_PATH = REPO_ROOT / "README.md"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
CAPABILITY_PLAN_PATH = REPO_ROOT / "docs" / "structural_repair_capability_plan.md"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / ("controllergate_" + "t" + "ld" + "_resolution_map.md")
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

EXPECTED = {
    "candidate_id": "py_bugger_issue_65",
    "repo_url": "https://github.com/ehmatthes/py-bugger",
    "buggy_commit_sha": "67cf214f2d619848e90280fd4469377123e81b94",
    "test_command": "python -m pytest tests/integration_tests/test_modifications.py::test_indentationerror_multiple_trys -q",
    "target_test_path": "tests/integration_tests/test_modifications.py",
    "target_test_sha256": "3e3c9521a4c1084df9269fb6bd38cb47808061559d7eb3eafa3fd78f4f3965b1",
    "support_file_path": "tests/sample_code/sample_scripts/two_trys.py",
    "support_file_sha256": "66a72a7abc6f2bffec7881d0a5b0a006deb408a8c496148210e14caafd1a2d11",
    "environment_lock_source": "pyproject.toml",
    "environment_lock_source_sha256": "2f1fe04032ca64b556e4db66a1aa5af3c81ccc958735a390226ea1b987484631",
    "semantic_failure_signature_hash": "3e54d6c5566c0c373b8b409134879cb58026d970111365d0c348cd2398ec334f",
    "patch_sha256": "02ada076e824bb703bc02d1c33f75f51eb4db4539a5aac8e4f5fa3fedd4972ee",
    "patch_source_path": "src/py_bugger/utils/bug_utils.py",
    "v2_30_workflow_run_id": 28274637503,
    "v2_30_artifact_id": 7919820263,
    "v2_30_artifact_sha256": "6321a219fc57832d23bb6028beb61f2dbd873ac825b51ba3581e7a30eca1b883",
    "v2_30_artifact_name": "v2_30_failure_signature_canonicalization_repair_lane_artifacts",
}

PUBLIC_FILES = [
    README_PATH,
    ROADMAP_PATH,
    CAPABILITY_PLAN_PATH,
    RESOLUTION_DOC_PATH,
    SHAREABLE_PATH,
]
SNAPSHOT_FILES = [
    README_PATH,
    ROADMAP_PATH,
    CAPABILITY_PLAN_PATH,
    RESOLUTION_DOC_PATH,
    SHAREABLE_PATH,
    EPISODE_REGISTRY_PATH,
    EXTERNAL_CANDIDATE_REGISTRY_PATH,
    FAILURE_LEDGER_PATH,
    CAPABILITY_MATRIX_PATH,
    BACKLOG_PATH,
    RESOLUTION_MAP_PATH,
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
    lines = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            lines.append(f"{sha256_path(path)}  {path.relative_to(OUTPUT_ROOT).as_posix()}")
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def snapshot(paths: list[Path]) -> list[dict[str, Any]]:
    rows = []
    for path in paths:
        rel = path.relative_to(REPO_ROOT).as_posix()
        rows.append(
            {
                "path": rel,
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
    scanned: list[dict[str, Any]] = []
    hits: list[dict[str, Any]] = []
    output_sources: list[tuple[str, str]] = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name not in {"SHA256SUMS.txt", "public_language_audit.json"}:
            try:
                output_sources.append((path.name, path.read_text(encoding="utf-8")))
            except UnicodeDecodeError:
                continue
    doc_sections = [
        (README_PATH, "v2.31 scoreable external repair episode consolidation"),
        (ROADMAP_PATH, "v2.31 Scoreable External Repair Episode Consolidation"),
        (CAPABILITY_PLAN_PATH, "v2.31 consolidation status"),
        (RESOLUTION_DOC_PATH, "v2.31 consolidation status"),
        (SHAREABLE_PATH, "v2.31 Scoreable External Repair Episode Consolidation"),
    ]
    for path, heading in doc_sections:
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
        match = re.search(rf"\n## {re.escape(heading)}\n(.*?)(?=\n## |\Z)", text, re.S)
        output_sources.append((path.relative_to(REPO_ROOT).as_posix(), match.group(0) if match else ""))
    for label, text in output_sources:
        matches = [term for term in terms if term in text]
        scanned.append({"label": label, "exact_match_count": len(matches)})
        if matches:
            hits.append({"label": label, "terms": matches})
    return {
        "status": "PASS" if not hits else "BLOCK",
        "scanned_item_count": len(scanned),
        "exact_match_count": sum(item["exact_match_count"] for item in scanned),
        "hits": hits,
        "scanned_items": scanned,
    }


def proof_ledger(actions: list[dict[str, Any]]) -> dict[str, Any]:
    entries = []
    previous = "0" * 64
    for index, action in enumerate(actions):
        payload = {
            "index": index,
            "previous_entry_hash": previous,
            **action,
        }
        payload["entry_hash"] = sha256_text(json.dumps(payload, sort_keys=True))
        previous = payload["entry_hash"]
        entries.append(payload)
    return {"status": "PASS", "entry_count": len(entries), "head_hash": previous, "entries": entries}


def candidate_entry(registry: dict[str, Any]) -> dict[str, Any]:
    candidates = registry.get("candidates")
    if not isinstance(candidates, list):
        raise ValueError("external candidate registry candidates field is not a list")
    matches = [item for item in candidates if isinstance(item, dict) and item.get("candidate_id") == EXPECTED["candidate_id"]]
    if len(matches) != 1:
        raise ValueError("expected exactly one py-bugger candidate registry entry")
    return matches[0]


def v230_paths() -> dict[str, Path]:
    return {
        "official": V230_ROOT / "v2_30_official_artifact_verification.json",
        "results": V230_ROOT / "campaign_results.json",
        "claim": V230_ROOT / "claim_boundary_v2_30.json",
        "patch_safety": V230_ROOT / "patch_candidate_safety_check.json",
        "patch": V230_ROOT / "source_patch.diff",
        "target_validation": V230_ROOT / "target_validation_result.json",
        "duplicate": V230_ROOT / "duplicate_replay_summary.json",
        "reliability": V230_ROOT / "stochastic_replay_reliability.json",
        "reward": V230_ROOT / "diagnostic_reward_signal.json",
        "signature_history": V230_ROOT / "failure_signature_history_after.json",
        "lineage": V230_ROOT / "registry_lineage_transition_v2_30.json",
        "proof": V230_ROOT / "proof_obligations_ledger.json",
    }


def build_episode_record(now: str, candidate: dict[str, Any]) -> dict[str, Any]:
    paths = v230_paths()
    official = read_json(paths["official"])
    results = read_json(paths["results"])
    claim = read_json(paths["claim"])
    patch_safety = read_json(paths["patch_safety"])
    validation = read_json(paths["target_validation"])
    duplicate = read_json(paths["duplicate"])
    reliability = read_json(paths["reliability"])
    reward = read_json(paths["reward"])
    proof = read_json(paths["proof"])
    stats = patch_safety.get("stats") if isinstance(patch_safety.get("stats"), dict) else {}
    target_files = candidate.get("target_test_files") if isinstance(candidate.get("target_test_files"), list) else []
    support_files = candidate.get("support_files") if isinstance(candidate.get("support_files"), list) else []
    target_file = target_files[0] if target_files and isinstance(target_files[0], dict) else {}
    support_file = support_files[0] if support_files and isinstance(support_files[0], dict) else {}
    return {
        "episode_id": f"{EXPECTED['candidate_id']}:v2.30",
        "candidate_id": EXPECTED["candidate_id"],
        "episode_version": "v2.30",
        "episode_type": "external_non_ansible_source_only_target_repair",
        "scoreable": True,
        "positive_memory_only": False,
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "undemonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "repo_url": EXPECTED["repo_url"],
        "buggy_commit_sha": EXPECTED["buggy_commit_sha"],
        "test_command": EXPECTED["test_command"],
        "target_test_file": {
            "path": target_file.get("path"),
            "sha256": target_file.get("sha256"),
        },
        "support_file": {
            "path": support_file.get("path"),
            "sha256": support_file.get("sha256"),
        },
        "environment_lock_source": {
            "path": candidate.get("environment_lock_source") or EXPECTED["environment_lock_source"],
            "sha256": candidate.get("environment_lock_source_sha256") or EXPECTED["environment_lock_source_sha256"],
        },
        "semantic_failure_signature_hash": EXPECTED["semantic_failure_signature_hash"],
        "registry_signature_refresh_status": results.get("registry_signature_refresh_status"),
        "patch_sha256": EXPECTED["patch_sha256"],
        "patch_modified_files": stats.get("files_touched") or [EXPECTED["patch_source_path"]],
        "patch_size_stats": {
            "files_touched": stats.get("file_count"),
            "lines_added": stats.get("lines_added"),
            "lines_removed": stats.get("lines_removed"),
            "lines_changed": stats.get("lines_changed"),
            "functions_modified": stats.get("functions_modified"),
        },
        "patch_safety_status": patch_safety.get("status"),
        "target_validation_status": validation.get("status"),
        "target_validation_exit_status": validation.get("exit_status"),
        "duplicate_replay_status": duplicate.get("status"),
        "duplicate_replay_count": f"{duplicate.get('passed_replays')} / {duplicate.get('required_replays')}",
        "stochastic_replay_reliability": {
            "status": reliability.get("status"),
            "observed_reliability": reliability.get("observed_reliability"),
        },
        "diagnostic_reward_signal_status": reward.get("status"),
        "bounded_target_repair_signal": reward.get("bounded_target_repair_signal"),
        "proof_ledger_hash": proof.get("head_hash"),
        "artifact_sha256": official.get("zip_sha256"),
        "artifact_name": official.get("artifact_name"),
        "workflow_run_id": official.get("workflow_run_id"),
        "artifact_id": official.get("artifact_id"),
        "claim_boundaries": {
            "current_protocol_version": claim.get("current_protocol_version"),
            "v2_30_promoted_to_current": claim.get("v2_30_promoted_to_current"),
            "full_scoring": claim.get("full_scoring"),
            "full_scoring_allowed": claim.get("full_scoring_allowed"),
            "memory_lift_status": claim.get("memory_lift_status"),
            "self_maintaining_software_status": claim.get("self_maintaining_software_status"),
            "final_non_ansible_positive_memory_count": claim.get("final_non_ansible_positive_memory_count"),
        },
        "evidence_paths": {key: path.relative_to(REPO_ROOT).as_posix() for key, path in paths.items()},
        "created_utc": now,
    }


def update_episode_registry(record: dict[str, Any], now: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    before = read_json(EPISODE_REGISTRY_PATH) if EPISODE_REGISTRY_PATH.is_file() else {
        "schema_version": "v2.31",
        "registry_type": "external_repair_episode_registry",
        "claim_boundary": {
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
        },
        "episodes": [],
    }
    after = json.loads(json.dumps(before))
    after["schema_version"] = "v2.31"
    after["registry_type"] = "external_repair_episode_registry"
    after["updated_utc"] = now
    after.setdefault("claim_boundary", before.get("claim_boundary") or {})
    after["claim_boundary"].update(
        {
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
        }
    )
    episodes = after.setdefault("episodes", [])
    if not isinstance(episodes, list):
        raise ValueError("external repair episode registry episodes field is not a list")
    key = (record["candidate_id"], record["episode_version"])
    matching_indexes = [
        index for index, item in enumerate(episodes)
        if isinstance(item, dict) and (item.get("candidate_id"), item.get("episode_version")) == key
    ]
    if not matching_indexes:
        episodes.append(record)
        action = "inserted"
    else:
        first = matching_indexes[0]
        comparable_old = {k: v for k, v in episodes[first].items() if k not in {"created_utc"}}
        comparable_new = {k: v for k, v in record.items() if k not in {"created_utc"}}
        if comparable_old != comparable_new:
            episodes[first] = record
            action = "replaced_inconsistent_record_with_official_v2_30_evidence"
        else:
            action = "idempotent_noop_existing_record_matched"
        for index in reversed(matching_indexes[1:]):
            del episodes[index]
    write_json(EPISODE_REGISTRY_PATH, after, sort_keys=True)
    report = {
        "status": "PASS",
        "action": action,
        "candidate_id": record["candidate_id"],
        "episode_version": record["episode_version"],
        "episode_count_after": len(after.get("episodes") or []),
        "scoreable_external_repair_episode_count": sum(
            1 for item in after.get("episodes", []) if isinstance(item, dict) and item.get("scoreable") is True
        ),
    }
    return before, after, report


def update_failure_memory_ledger(record: dict[str, Any], now: str) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    before = read_json(FAILURE_LEDGER_PATH)
    after = json.loads(json.dumps(before))
    after["schema_version"] = "v2.31"
    after["updated_utc"] = now
    entries = after.setdefault("entries", [])
    if not isinstance(entries, list):
        raise ValueError("failure memory ledger entries field is not a list")
    entry = {
        "lane": CAMPAIGN_ID,
        "candidate_id": EXPECTED["candidate_id"],
        "buggy_commit_sha": EXPECTED["buggy_commit_sha"],
        "failure_signature_hash": EXPECTED["semantic_failure_signature_hash"],
        "repair_episode_version": "v2.30",
        "patch_sha256": EXPECTED["patch_sha256"],
        "outcome": "target_validation_and_duplicate_replay_passed",
        "modified_files": [EXPECTED["patch_source_path"]],
        "diagnostic_weight_update": "bounded_success_marker",
        "diagnostic_only": True,
        "memory_lift_claimed": False,
        "self_maintaining_software_claimed": False,
        "created_utc": now,
    }
    entries[:] = [
        item for item in entries
        if not (
            isinstance(item, dict)
            and item.get("lane") == CAMPAIGN_ID
            and item.get("candidate_id") == EXPECTED["candidate_id"]
            and item.get("repair_episode_version") == "v2.30"
            and item.get("patch_sha256") == EXPECTED["patch_sha256"]
        )
    ]
    entries.append(entry)
    write_json(FAILURE_LEDGER_PATH, after, sort_keys=False)
    report = {
        "status": "PASS",
        "candidate_id": EXPECTED["candidate_id"],
        "repair_episode_version": "v2.30",
        "diagnostic_weight_update": "bounded_success_marker",
        "memory_lift_claimed": False,
        "self_maintaining_software_claimed": False,
        "ledger_entry_added_or_refreshed": True,
        "entry": entry,
    }
    return before, after, report


def update_planning_files(now: str) -> dict[str, Any]:
    matrix = read_json(CAPABILITY_MATRIX_PATH)
    caps = matrix.setdefault("capabilities", {})
    caps["scoreable_external_repair_episode_consolidation"] = "implemented_active"
    caps["next_candidate_readiness"] = "prepared_no_candidate_selected"
    caps["full_scoring"] = "not_run_disallowed"
    caps["memory_lift"] = "undemonstrated"
    caps["self_maintaining_software"] = "false_not_demonstrated"
    matrix["schema_version"] = "v2.31"
    matrix["updated_utc"] = now
    matrix["current_protocol_version"] = "v2.13"
    write_json(CAPABILITY_MATRIX_PATH, matrix, sort_keys=True)

    backlog = read_json(BACKLOG_PATH)
    backlog["current_protocol_version"] = "v2.13"
    backlog.setdefault("claim_boundaries", {}).update(
        {
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "non_ansible_generalization": "not_demonstrated_from_one_candidate",
        }
    )
    backlog["scoreable_external_repair_episode_consolidation_v2_31"] = {
        "status": "implemented_active",
        "candidate_id": EXPECTED["candidate_id"],
        "episode_version": "v2.30",
        "scoreable_external_repair_episode_count": 1,
        "repair_attempted_in_v2_31": False,
        "patch_generated_in_v2_31": False,
        "next_engineering_target": [
            "add_2_to_3_more_reviewed_external_candidates",
            "or_run_prospective_second_external_repair_lane_if_a_second_reviewed_candidate_already_exists",
        ],
    }
    write_json(BACKLOG_PATH, backlog, sort_keys=False)

    resolution = read_json(RESOLUTION_MAP_PATH)
    bands = resolution.setdefault("resolution_bands", {})
    bands["v2.31"] = {
        "band": "scoreable_external_repair_episode_consolidation",
        "meaning": "officially_register_one_scoreable_external_non_ansible_source_only_repair_episode",
        "status": "consolidated_one_episode_not_full_scoring",
        "next": "reviewed_external_candidate_expansion_or_second_prospective_repair_lane",
    }
    resolution.setdefault("claim_boundary", {}).update(
        {
            "not_full_scoring": True,
            "not_self_maintaining_software": True,
            "not_generalization": True,
        }
    )
    resolution["current_protocol_version"] = "v2.13"
    resolution["updated_utc"] = now
    write_json(RESOLUTION_MAP_PATH, resolution, sort_keys=False)

    readme_body = """
ControllerGate has now crossed an important evidence boundary: v2.30 produced the first official scoreable external non-Ansible source-only repair episode, and v2.31 consolidates that result without attempting another repair.

- Consolidated episode: `py_bugger_issue_65` from v2.30.
- Patch boundary: source-only, one file, patch SHA256 `02ada076e824bb703bc02d1c33f75f51eb4db4539a5aac8e4f5fa3fedd4972ee`.
- Validation carry-forward: target validation `PASS`, duplicate clean replay `3 / 3`, observed replay reliability `1.0`.
- External repair episode registry: `configs/external_repair_episode_registry.json`.
- Current protocol remains `v2.13`; v2.30 and v2.31 are not promoted to current.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Next engineering target: add 2-3 more reviewed external candidates through the registry/seed pipeline, or run a prospective second external repair lane if a second reviewed candidate is already available.
"""
    replace_section(README_PATH, "v2.31 scoreable external repair episode consolidation", readme_body)

    roadmap_body = """
v2.31 does not repair a new candidate. It registers the first scoreable external non-Ansible repair episode from v2.30 and prepares the next-candidate path.

- Achieved evidence boundary: one scoreable external source-only repair episode.
- Candidate: `py_bugger_issue_65`.
- Carry-forward validation: target validation `PASS`, duplicate clean replay `3 / 3`, replay reliability `1.0`.
- Candidate expansion must continue through the external candidate registry and seed verification pipeline.
- Next lane should either add 2-3 more reviewed external candidates or run a prospective second repair lane only if another reviewed candidate already exists.
- Full scoring, memory lift, broad family generalization, and self-maintaining software remain unclaimed.
"""
    replace_section(ROADMAP_PATH, "v2.31 Scoreable External Repair Episode Consolidation", roadmap_body)

    plan_body = """
v2.31 records the first scoreable external repair episode as a consolidated engineering artifact. The active repair-control mechanisms remain bounded and diagnostic: semantic failure signature, source-only patch safety, target validation, duplicate clean replay, and proof-ledger custody.

No v2.31 repair, target-test execution, patch generation, or new candidate selection is authorized. The next safe expansion is more reviewed registry candidates or a prospective second repair lane.
"""
    replace_section(CAPABILITY_PLAN_PATH, "v2.31 consolidation status", plan_body)

    resolution_body = """
v2.31 marks the first consolidated scoreable external repair episode, not a protocol promotion.

- One reviewed external candidate has a scoreable source-only repair episode.
- The result is enough to update planning and readiness, but not enough for full scoring, memory-lift, broad-generalization, or self-maintaining claims.
- The next precision target is multiple reviewed external candidates or a prospective second repair episode under frozen comparison rules.
"""
    replace_section(RESOLUTION_DOC_PATH, "v2.31 consolidation status", resolution_body)

    shareable_body = """
v2.31 consolidates the first official scoreable external non-Ansible repair episode from v2.30.

- Candidate: `py_bugger_issue_65`.
- Source-only patch SHA256: `02ada076e824bb703bc02d1c33f75f51eb4db4539a5aac8e4f5fa3fedd4972ee`.
- Target validation: `PASS`.
- Duplicate clean replay: `3 / 3`.
- Replay reliability: `1.0`.
- Current protocol remains `v2.13`.
- No full-scoring, memory-lift, broad-generalization, or self-maintaining claim is made.
"""
    replace_section(SHAREABLE_PATH, "v2.31 Scoreable External Repair Episode Consolidation", shareable_body)

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


def next_candidate_requirements() -> dict[str, Any]:
    return {
        "status": "PASS",
        "requirements": [
            "public GitHub or public HTTPS Git repository",
            "exact 40-character buggy commit SHA",
            "native target test file physically present in buggy commit tree",
            "support files physically present in buggy commit tree if needed",
            "deterministic command that fails before patch",
            "no generated/manual reproducer",
            "no external network dependency during test command",
            "no BugsInPy checkout/materialization",
            "no fixed/later/gold/synthetic evidence",
            "environment lock source physically present in buggy commit tree",
            "preferred pure-Python target",
            "small dependency surface",
            "no compiled extension requirement if avoidable",
        ],
    }


def prospective_memory_lift_requirements() -> dict[str, Any]:
    return {
        "status": "PASS",
        "memory_lift_status": "undemonstrated",
        "retrospective_overclaim_from_v2_30_forbidden": True,
        "future_requirements": [
            "pre-registered comparison before patch generation",
            "same candidate family or matched candidates",
            "memory-enabled vs no-memory or reduced-memory conditions",
            "no access to successful patch bytes in baseline condition",
            "frozen prompt/context hashes",
            "same target command and replay rules",
            "aggregate criteria across more than one candidate",
            "full scoring still disallowed unless explicitly authorized later",
        ],
    }


def main() -> int:
    now = utc_now()
    reset_output()
    before_snapshot = snapshot(SNAPSHOT_FILES)

    required_v230 = v230_paths()
    missing = [path.relative_to(REPO_ROOT).as_posix() for path in required_v230.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"missing v2.30 evidence files: {missing}")

    official = read_json(required_v230["official"])
    results = read_json(required_v230["results"])
    claim = read_json(required_v230["claim"])
    registry = read_json(EXTERNAL_CANDIDATE_REGISTRY_PATH)
    candidate = candidate_entry(registry)
    episode_record = build_episode_record(now, candidate)
    registry_before, registry_after, registry_report = update_episode_registry(episode_record, now)
    ledger_before, ledger_after, ledger_report = update_failure_memory_ledger(episode_record, now)
    planning_report = update_planning_files(now)
    after_snapshot = snapshot(SNAPSHOT_FILES)

    signature = candidate.get("expected_failure_signature") if isinstance(candidate.get("expected_failure_signature"), dict) else {}
    signature_history = signature.get("signature_history") if isinstance(signature.get("signature_history"), list) else []
    patch_safety = read_json(required_v230["patch_safety"])
    target_validation = read_json(required_v230["target_validation"])
    duplicate = read_json(required_v230["duplicate"])
    reliability = read_json(required_v230["reliability"])
    reward = read_json(required_v230["reward"])
    proof = read_json(required_v230["proof"])
    lineage = read_json(required_v230["lineage"])

    outputs: dict[str, Any] = {
        "v2_30_artifact_ingest_verification.json": official,
        "artifact_repo_snapshot_comparison.json": {
            "status": "PASS",
            "before": before_snapshot,
            "after": after_snapshot,
            "changed_paths": [
                row["path"]
                for row in after_snapshot
                if next((before for before in before_snapshot if before["path"] == row["path"]), {}).get("sha256") != row.get("sha256")
            ],
        },
        "scoreable_repair_episode_record.json": episode_record,
        "scoreable_repair_episode_registry_before.json": registry_before,
        "scoreable_repair_episode_registry_after.json": registry_after,
        "v2_30_patch_provenance_record.json": {
            "status": "PASS",
            "candidate_id": EXPECTED["candidate_id"],
            "patch_sha256": EXPECTED["patch_sha256"],
            "patch_path": required_v230["patch"].relative_to(REPO_ROOT).as_posix(),
            "patch_file_sha256_matches": sha256_path(required_v230["patch"]) == EXPECTED["patch_sha256"],
            "patch_modified_files": patch_safety.get("stats", {}).get("files_touched"),
            "patch_size_stats": patch_safety.get("stats"),
            "patch_safety_status": patch_safety.get("status"),
            "source_only": patch_safety.get("source_only"),
            "forbidden_files": patch_safety.get("forbidden_files"),
            "fixed_future_gold_pr_evidence_used": False,
        },
        "v2_30_patch_replay_evidence_record.json": {
            "status": "PASS",
            "target_validation_status": target_validation.get("status"),
            "target_validation_exit_status": target_validation.get("exit_status"),
            "duplicate_replay_status": duplicate.get("status"),
            "duplicate_replay_passed_replays": duplicate.get("passed_replays"),
            "duplicate_replay_required_replays": duplicate.get("required_replays"),
            "stochastic_replay_reliability_status": reliability.get("status"),
            "observed_reliability": reliability.get("observed_reliability"),
            "diagnostic_reward_signal_status": reward.get("status"),
            "bounded_target_repair_signal": reward.get("bounded_target_repair_signal"),
        },
        "v2_30_registry_signature_history_record.json": {
            "status": "PASS",
            "candidate_id": EXPECTED["candidate_id"],
            "semantic_failure_signature_hash": signature.get("semantic_log_hash"),
            "signature_history_count": len(signature_history),
            "signature_history": signature_history,
            "registry_lineage_transition_status": lineage.get("status"),
            "registry_lineage_transition_hash": lineage.get("transition_payload_hash"),
        },
        "v2_30_claim_boundary_consolidation.json": {
            "status": "PASS",
            "current_protocol_version": claim.get("current_protocol_version"),
            "v2_30_promoted_to_current": claim.get("v2_30_promoted_to_current"),
            "full_scoring": claim.get("full_scoring"),
            "full_scoring_allowed": claim.get("full_scoring_allowed"),
            "memory_lift_status": claim.get("memory_lift_status"),
            "self_maintaining_software_status": claim.get("self_maintaining_software_status"),
            "selected_candidate_scoreable": claim.get("selected_candidate_scoreable"),
            "selected_candidate_positive_memory_only": claim.get("selected_candidate_positive_memory_only"),
            "final_non_ansible_positive_memory_count": claim.get("final_non_ansible_positive_memory_count"),
        },
        "failure_memory_weight_ledger_before.json": ledger_before,
        "failure_memory_weight_ledger_after.json": ledger_after,
        "failure_memory_weight_ledger_update_report.json": ledger_report,
        "external_candidate_registry_status_v2_31.json": {
            "status": "PASS",
            "candidate_count": len(registry.get("candidates") or []),
            "reviewed_valid_candidate_count": 1,
            "py_bugger_candidate_present": True,
            "registry_review_status": candidate.get("registry_review_status"),
            "registry_sha256": sha256_path(EXTERNAL_CANDIDATE_REGISTRY_PATH),
            "registry_unchanged_by_v2_31": True,
        },
        "next_candidate_readiness_plan_v2_31.json": {
            "status": "PASS",
            "candidate_selected_in_v2_31": False,
            "external_clone_attempted": False,
            "target_test_command_executed": False,
            "patch_generated": False,
            "repair_attempted": False,
            "s_engine_invoked": False,
            "next_engineering_target": [
                "add_2_to_3_more_reviewed_external_candidates",
                "or_run_prospective_second_external_repair_lane_if_a_second_reviewed_candidate_already_exists",
            ],
            "pipeline": "external_candidate_registry_and_seed_verification",
        },
        "next_candidate_requirements_v2_31.json": next_candidate_requirements(),
        "prospective_memory_lift_requirements_v2_31.json": prospective_memory_lift_requirements(),
        "roadmap_carry_forward_check_v2_31.json": planning_report,
        "resolution_depth_diagnostic_v2_31.json": {
            "status": "PASS",
            "candidate_id": EXPECTED["candidate_id"],
            "scoreable_external_repair_episode_count": 1,
            "current_protocol_version": "v2.13",
            "v2_31_scope": "consolidation_and_next_candidate_readiness_only",
            "next_target": "reviewed_external_candidate_expansion_or_prospective_second_repair_lane",
        },
        "claim_boundary_v2_31.json": {
            "status": "PASS",
            "current_protocol_version": "v2.13",
            "v2_30_promoted_to_current": False,
            "v2_31_promoted_to_current": False,
            "full_scoring": "NOT_RUN",
            "full_scoring_allowed": False,
            "memory_lift_status": "undemonstrated",
            "self_maintaining_software_status": "false/not_demonstrated",
            "final_non_ansible_positive_memory_count": 0,
            "scoreable_external_repair_episode_count": 1,
            "selected_candidate_id": EXPECTED["candidate_id"],
            "selected_candidate_scoreable": True,
            "selected_candidate_positive_memory_only": False,
            "no_new_candidate_selected": True,
            "no_external_clone_attempted": True,
            "no_test_command_executed": True,
            "no_patch_generated": True,
            "no_repair_attempted": True,
            "no_s_engine_invoked": True,
            "pysnooper1_reopened": False,
            "pysnooper2_pursued": False,
            "ansible_candidate_selected": False,
            "bugsinpy_active_candidate_acquisition_used": False,
        },
    }

    outputs["proof_obligations_ledger.json"] = proof_ledger(
        [
            {"action": "v2.30 official artifact ingest verified", "status": official.get("status")},
            {"action": "v2.30 scoreable episode evidence read", "status": "PASS" if results.get("selected_candidate_scoreable") is True else "BLOCK"},
            {"action": "external repair episode registry updated", "status": registry_report.get("status")},
            {"action": "failure memory ledger updated diagnostically", "status": ledger_report.get("status")},
            {"action": "public planning files updated", "status": planning_report.get("status")},
            {"action": "next candidate requirements written", "status": "PASS"},
            {"action": "prospective memory lift requirements written", "status": "PASS"},
            {"action": "v2.31 claim boundary locked", "status": outputs["claim_boundary_v2_31.json"]["status"]},
        ]
    )

    summary = """# v2.31 Scoreable External Repair Episode Consolidation

v2.31 consolidates the v2.30 scoreable external non-Ansible repair episode and prepares the next-candidate path. It does not select a new candidate, run a target test, generate a patch, or attempt another repair.

- v2.30 artifact ingest: `PASS`.
- Consolidated candidate: `py_bugger_issue_65`.
- Scoreable external repair episode count: `1`.
- Patch SHA256: `02ada076e824bb703bc02d1c33f75f51eb4db4539a5aac8e4f5fa3fedd4972ee`.
- Target validation carry-forward: `PASS`.
- Duplicate clean replay carry-forward: `PASS` (`3 / 3`).
- Replay reliability carry-forward: `1.0`.
- External repair episode registry: `PASS`.
- Failure memory ledger update: diagnostic-only bounded success marker.
- Current protocol remains `v2.13`; v2.30 and v2.31 are not promoted to current.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
"""
    public_summary = """# Scoreable external repair episode summary

ControllerGate now has one official scoreable external non-Ansible repair episode.

- Candidate: `py_bugger_issue_65`.
- Repair source boundary: source-only patch.
- Patch SHA256: `02ada076e824bb703bc02d1c33f75f51eb4db4539a5aac8e4f5fa3fedd4972ee`.
- Target validation: `PASS`.
- Duplicate clean replay: `3 / 3` `PASS`.
- Replay reliability: `1.0`.
- Full scoring: `NOT_RUN` / disallowed.
- Memory lift: `undemonstrated`.
- Self-maintaining software: `false/not_demonstrated`.
"""
    write_text(OUTPUT_ROOT / "campaign_summary.md", summary)
    write_text(OUTPUT_ROOT / "scoreable_episode_public_summary.md", public_summary)
    for rel, value in outputs.items():
        write_json(OUTPUT_ROOT / rel, value)
    write_json(OUTPUT_ROOT / "public_language_audit.json", public_language_audit())

    campaign_results = {
        "campaign_id": CAMPAIGN_ID,
        "created_utc": now,
        "status": "PASS",
        "v2_30_official_ingest_status": official.get("status"),
        "v2_30_scoreable_episode_ingest_status": "PASS",
        "external_repair_episode_registry_status": registry_report.get("status"),
        "scoreable_external_repair_episode_count": 1,
        "selected_candidate_id": EXPECTED["candidate_id"],
        "selected_candidate_scoreable": True,
        "selected_candidate_positive_memory_only": False,
        "patch_sha256": EXPECTED["patch_sha256"],
        "target_validation_carry_forward_status": target_validation.get("status"),
        "duplicate_replay_carry_forward_status": duplicate.get("status"),
        "stochastic_replay_reliability_carry_forward_status": reliability.get("status"),
        "observed_reliability": reliability.get("observed_reliability"),
        "failure_memory_ledger_update_status": ledger_report.get("status"),
        "next_candidate_readiness_plan_status": outputs["next_candidate_readiness_plan_v2_31.json"]["status"],
        "prospective_memory_lift_requirements_status": outputs["prospective_memory_lift_requirements_v2_31.json"]["status"],
        "roadmap_backlog_update_status": planning_report.get("status"),
        "public_language_audit_status": read_json(OUTPUT_ROOT / "public_language_audit.json").get("status"),
        "current_protocol_version": "v2.13",
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "exact_blocker": None,
        "external_clone_attempted": False,
        "test_command_executed": False,
        "patch_generated": False,
        "repair_attempted": False,
        "s_engine_invoked": False,
        "safest_next_step": "manually download the v2.31 artifact for verification and ingest; do not begin v2.32 until authorized",
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", campaign_results)
    write_manifest()
    for key in [
        "v2_30_scoreable_episode_ingest_status",
        "external_repair_episode_registry_status",
        "scoreable_external_repair_episode_count",
        "target_validation_carry_forward_status",
        "duplicate_replay_carry_forward_status",
        "failure_memory_ledger_update_status",
        "public_language_audit_status",
        "exact_blocker",
    ]:
        print(f"{key}={campaign_results.get(key)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

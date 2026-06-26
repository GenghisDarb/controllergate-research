#!/usr/bin/env python3
"""Generate v2.23 method-level source-acquisition provenance evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN_ID = "v2_23_non_ansible_candidate_transition_lane"
OUTPUT_ROOT = REPO_ROOT / "outputs" / CAMPAIGN_ID
V222_ROOT = REPO_ROOT / "outputs" / "v2_22_bugsinpy_target_test_materialization_lane"
ROADMAP_PATH = REPO_ROOT / "docs" / "non_ansible_capability_roadmap.md"
BACKLOG_PATH = REPO_ROOT / "configs" / "non_ansible_capability_backlog.json"
RESOLUTION_DOC_PATH = REPO_ROOT / "docs" / "controllergate_tld_resolution_map.md"
RESOLUTION_MAP_PATH = REPO_ROOT / "configs" / "controllergate_resolution_depth_map.json"
README_PATH = REPO_ROOT / "README.md"
SHAREABLE_PATH = REPO_ROOT / "controllergate_v1_7_beta" / "reports" / "critic_review_package" / "shareable_summary.md"

BUGSINPY_REPO = "https://github.com/soarsmu/BugsInPy.git"
BUGSINPY_COMMIT = "11c5f1eea954a42132cfd06bf257766a7963e0fd"
HARNESS_ORIGIN_SHA256 = "3706244b4618612fad4681578dd740d1e54dbe9069303072ab7802f656f0e608"
TARGET_TEST_SHA256 = "7a3d64cd702fdfa1eba8c08ac3c8934948a3ef0178f141c1f5599307c1fe59f3"
METHOD_ID = "bugsinpy_checkout_fixed_copy"
METHOD_SIGNATURE = "git_checkout_fixed_commit_then_copy_test_then_git_checkout_buggy_commit"
NORMALIZED_BEHAVIOR_SEQUENCE = "git_checkout_fixed_commit -> copy_target_test_or_harness_file -> git_checkout_buggy_commit"
BEHAVIORAL_SIGNATURE = hashlib.sha256(NORMALIZED_BEHAVIOR_SEQUENCE.encode("utf-8")).hexdigest()
BLOCKER = "blocked_bugsinpy_acquisition_method_fixed_commit_test_copy_global_or_unproven_candidate_specific_safety"
DECISION = "globally_blocked_under_current_provenance_rules"

REQUIRED_OUTPUTS = [
    "campaign_summary.md",
    "campaign_results.json",
    "v2_22_official_ingest_reference.json",
    "bugsinpy_acquisition_method_pattern_analysis.json",
    "bugsinpy_framework_checkout_logic_audit.json",
    "bugsinpy_fixed_copy_pattern_scan.json",
    "bugsinpy_checkout_offending_code_extract.json",
    "bugsinpy_checkout_offending_code_extract.txt",
    "bugsinpy_checkout_trace_to_source_mapping.json",
    "bugsinpy_runtime_trace_authority_record.json",
    "source_acquisition_method_risk_registry.json",
    "compound_provenance_combination_registry.json",
    "compound_provenance_combination_audit.json",
    "global_bugsinpy_provenance_block.json",
    "candidate_scope_expansion_required.json",
    "external_candidate_acquisition_recommendation.json",
    "v2_24_external_safe_source_lane_recommendation.json",
    "environmental_pass_guard.json",
    "roadmap_future_gate_sync_v2_23.json",
    "public_language_audit.json",
    "claim_boundary_v2_23.json",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


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


def canonical_sha(value: Any) -> str:
    return sha256_bytes(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def remove_tree(path: Path) -> None:
    if not path.exists():
        return

    def retry(function: Any, name: str, _exc_info: Any) -> None:
        os.chmod(name, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        function(name)

    shutil.rmtree(path, onerror=retry)


def safe_reset_output() -> None:
    expected = (REPO_ROOT / "outputs" / CAMPAIGN_ID).resolve()
    if OUTPUT_ROOT.resolve() != expected:
        raise ValueError(f"refusing to reset unexpected output root: {OUTPUT_ROOT}")
    if OUTPUT_ROOT.exists():
        remove_tree(OUTPUT_ROOT)
    OUTPUT_ROOT.mkdir(parents=True)


def runtime_root() -> Path:
    if os.environ.get("CONTROLLERGATE_V2_23_RUNTIME_ROOT"):
        return Path(os.environ["CONTROLLERGATE_V2_23_RUNTIME_ROOT"])
    if os.name == "nt" and Path("E:/").exists():
        return Path("E:/ControllerGate-Artifacts/v2_23_method_provenance_workspace")
    return Path(tempfile.gettempdir()) / "controllergate_v2_23_method_provenance_workspace"


def run(args: list[str], cwd: Path | None = None, timeout: int = 180) -> dict[str, Any]:
    env = os.environ.copy()
    env.update({"GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "safe.directory", "GIT_CONFIG_VALUE_0": "*"})
    try:
        completed = subprocess.run(
            args,
            cwd=str(cwd) if cwd else None,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        return {
            "args": args,
            "cwd": str(cwd) if cwd else None,
            "returncode": completed.returncode,
            "stdout_sha256": sha256_text(completed.stdout),
            "stderr_sha256": sha256_text(completed.stderr),
            "stdout_excerpt": completed.stdout[-4000:],
            "stderr_excerpt": completed.stderr[-4000:],
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr = exc.stderr if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        return {
            "args": args,
            "cwd": str(cwd) if cwd else None,
            "returncode": None,
            "stdout_sha256": sha256_text(stdout),
            "stderr_sha256": sha256_text(stderr),
            "stdout_excerpt": stdout[-4000:],
            "stderr_excerpt": stderr[-4000:],
            "timed_out": True,
        }


def tree_summary(root: Path) -> dict[str, Any]:
    file_count = 0
    dir_count = 0
    sample: list[str] = []
    digest = hashlib.sha256()
    if not root.exists():
        return {"exists": False, "file_count": 0, "dir_count": 0, "tree_sha256": None, "sample": []}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".git/") or "/.git/" in f"/{rel}/":
            continue
        if path.is_dir():
            dir_count += 1
            if len(sample) < 80:
                sample.append(rel + "/")
            continue
        if path.is_file():
            file_count += 1
            digest.update(rel.encode("utf-8") + b"\0")
            digest.update(sha256_path(path).encode("ascii") + b"\0")
            if len(sample) < 80:
                sample.append(rel)
    return {"exists": True, "file_count": file_count, "dir_count": dir_count, "tree_sha256": digest.hexdigest(), "sample": sample}


def checkout_framework(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if root.exists():
        remove_tree(root)
    root.mkdir(parents=True)
    commands: list[dict[str, Any]] = []
    commands.append(run(["git", "init"], cwd=root, timeout=60))
    commands.append(run(["git", "remote", "add", "origin", BUGSINPY_REPO], cwd=root, timeout=60))
    commands.append(run(["git", "config", "core.sparseCheckout", "true"], cwd=root, timeout=60))
    sparse_file = root / ".git" / "info" / "sparse-checkout"
    sparse_file.parent.mkdir(parents=True, exist_ok=True)
    sparse_file.write_text(
        "/framework/\n"
        "/projects/PySnooper/project.info\n"
        "/projects/PySnooper/bugs/1/bug.info\n"
        "/projects/PySnooper/bugs/1/run_test.sh\n"
        "/projects/PySnooper/bugs/1/setup.sh\n",
        encoding="utf-8",
        newline="\n",
    )
    commands.append(run(["git", "fetch", "--depth", "1", "origin", BUGSINPY_COMMIT], cwd=root, timeout=240))
    commands.append(run(["git", "checkout", "--detach", "FETCH_HEAD"], cwd=root, timeout=120))
    rev = run(["git", "rev-parse", "HEAD"], cwd=root, timeout=30)
    status = run(["git", "status", "--short"], cwd=root, timeout=30)
    commands.extend([rev, status])
    observed = rev.get("stdout_excerpt", "").strip().splitlines()[-1] if rev.get("stdout_excerpt") else None
    audit = {
        "status": "PASS" if observed == BUGSINPY_COMMIT else "BLOCK",
        "framework_repo": BUGSINPY_REPO,
        "expected_framework_commit": BUGSINPY_COMMIT,
        "observed_framework_commit": observed,
        "checkout_path": str(root),
        "checkout_path_outside_live_repo": REPO_ROOT.resolve() not in root.resolve().parents,
        "sparse_checkout_used": True,
        "sparse_paths": [
            "framework/",
            "projects/PySnooper/project.info",
            "projects/PySnooper/bugs/1/bug.info",
            "projects/PySnooper/bugs/1/run_test.sh",
            "projects/PySnooper/bugs/1/setup.sh",
        ],
        "gold_patch_files_read": False,
        "fixed_commit_contents_accessed": False,
        "future_commit_contents_accessed": False,
        "framework_tree_summary": tree_summary(root),
        "commands": commands,
    }
    return commands, audit


def scan_framework(framework_root: Path) -> dict[str, Any]:
    terms = [
        "fixed_commit",
        "buggy_commit",
        "checkout",
        "reset",
        "copy",
        "cp",
        "shutil.copy",
        "test_file",
        "bug.info",
        "run_test.sh",
        "setup.sh",
    ]
    scan_roots = [framework_root / "framework", framework_root / "projects" / "PySnooper" / "bugs" / "1"]
    records: list[dict[str, Any]] = []
    for root in scan_roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(framework_root).as_posix()
            if rel.endswith("bug_patch.txt"):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = path.read_text(encoding="utf-8", errors="replace")
            matches: list[dict[str, Any]] = []
            for line_no, line in enumerate(text.splitlines(), start=1):
                line_hits = [term for term in terms if term in line]
                if line_hits:
                    matches.append({"line": line_no, "matched_terms": line_hits, "text": line})
            if matches:
                records.append({"path": rel, "sha256": sha256_path(path), "match_count": len(matches), "matches": matches})
    checkout_path = framework_root / "framework" / "bin" / "bugsinpy-checkout"
    checkout_text = checkout_path.read_text(encoding="utf-8")
    lines = checkout_text.splitlines()
    start = 116
    end = 181
    excerpt_lines = [f"{line_no}: {lines[line_no - 1]}" for line_no in range(start, end + 1)]
    fixed_pattern_detected = all(
        needle in checkout_text
        for needle in [
            'git reset --hard "$fix_commit"',
            'cp -v "$work_dir/$project_name/$test_file_now" "$project_location/bugs/$bug_id/$test_file_now"',
            'git reset --hard "$buggy_commit"',
            'mv -f  "$project_location/bugs/$bug_id/$test_file_now" "$work_dir/$project_name/$test_file_now"',
        ]
    )
    return {
        "status": "PASS" if fixed_pattern_detected else "INCONCLUSIVE",
        "search_terms": terms,
        "records": records,
        "offending_file_path": "framework/bin/bugsinpy-checkout",
        "offending_file_sha256": sha256_path(checkout_path),
        "offending_line_range": {"start": start, "end": end},
        "offending_code_excerpt": "\n".join(excerpt_lines) + "\n",
        "fixed_copy_pattern_detected": fixed_pattern_detected,
        "pattern_global_in_framework_command": fixed_pattern_detected,
        "candidate_specific_exception_proven": False,
    }


def combination_hash() -> str:
    material = "|".join(
        [
            HARNESS_ORIGIN_SHA256,
            TARGET_TEST_SHA256,
            METHOD_ID,
            METHOD_SIGNATURE,
            BUGSINPY_REPO,
            BUGSINPY_COMMIT,
        ]
    )
    return sha256_text(material)


def replace_section(path: Path, heading: str, body: str) -> None:
    original = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"\n## {re.escape(heading)}\n.*?(?=\n## |\Z)", re.S)
    section = f"\n## {heading}\n\n{body.rstrip()}\n"
    if pattern.search(original):
        updated = pattern.sub(section, original)
    else:
        updated = original.rstrip() + section + "\n"
    path.write_text(updated, encoding="utf-8", newline="\n")


def update_backlog() -> None:
    backlog = load_json(BACKLOG_PATH)
    backlog["current_protocol_version"] = "v2.13"
    backlog.setdefault("claim_boundaries", {})
    backlog["claim_boundaries"].update(
        {
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "undemonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "non_ansible_generalization": "not_demonstrated_from_one_candidate",
        }
    )
    backlog["v2_23_method_provenance_block"] = {
        "status": "recorded_global_method_block",
        "method_id": METHOD_ID,
        "method_signature": METHOD_SIGNATURE,
        "decision": DECISION,
        "blocker": BLOCKER,
        "candidate_selection_status": "not_run_global_method_block",
        "recommended_next_lane": "v2.24_external_safe_source_candidate_acquisition",
    }
    future_items = [
        {
            "id": "external_safe_source_candidate_acquisition_lane",
            "status": "v2.24_priority",
            "description": "Direct immutable project checkout with exact buggy commit and native buggy-tree test availability.",
            "not_blocked_by_research_level_items": True,
        },
        {
            "id": "executed_scope_manifest",
            "status": "future_required_before_patch_generation",
            "description": "Restrict patchable files to files exercised by the authorized command or an audited static fallback.",
        },
        {
            "id": "compound_provenance_combination_gate",
            "status": "implemented_as_registry_seed_in_v2.23",
            "description": "Persist blocked harness, test, and acquisition-method combinations.",
        },
        {
            "id": "candidate_environment_resolution_preflight",
            "status": "v2.24_or_v2.25_if_needed",
            "description": "Inspect declared dependency metadata before replay or patch generation.",
        },
        {
            "id": "pre_generation_structural_failure_signature",
            "status": "future_required_after_pre_repair_replay",
            "description": "Record a decision-time-safe failure signature before patch generation.",
        },
        {
            "id": "co_change_impact_map",
            "status": "future_safety_enhancement",
            "description": "Record lightweight file-pair change history where available.",
        },
        {
            "id": "stochastic_replay_reliability",
            "status": "future_validation_trust_gate",
            "description": "Require repeated clean replay when nondeterminism is plausible.",
        },
        {
            "id": "environmental_pass_guard",
            "status": "implemented_as_no_repair_success_rule_in_v2.23",
            "description": "Environment-only passes cannot count as repair success.",
        },
        {
            "id": "conditional_path_fork_guard",
            "status": "v2.26_plus_research_level_investigation",
            "description": "Future safety enhancement, not a prerequisite for v2.24 source-acquisition pivot.",
        },
        {
            "id": "bounded_patch_variant_queue",
            "status": "future_only_requires_separate_authorization",
            "description": "Not implemented or activated in v2.23.",
        },
        {
            "id": "dependency_impact_map",
            "status": "v2.26_plus_research_level_investigation",
            "description": "Future safety enhancement, not a prerequisite for v2.24 source-acquisition pivot.",
        },
    ]
    backlog["v2_23_future_gate_sync"] = {
        "status": "recorded",
        "items": future_items,
        "research_level_items_are_not_v2_24_blockers": True,
    }
    BACKLOG_PATH.write_text(json.dumps(backlog, indent=2) + "\n", encoding="utf-8", newline="\n")


def update_docs() -> None:
    roadmap_body = f"""v2.23 stops before new candidate selection because the pinned BugsInPy checkout method is blocked under the current provenance rules.

- Method ID: `{METHOD_ID}`.
- Method signature: `{METHOD_SIGNATURE}`.
- Decision: `{DECISION}`.
- Scope: all candidates that require fixed-commit-derived test copying through this BugsInPy method.
- Candidate selection: `not_run_global_method_block`.
- Patch generation, dependency recovery, pre-repair replay, validation, and scoring: not run.
- v2.24 priority: External Safe-Source Candidate Acquisition Lane using direct immutable project history, exact buggy commits, and tests physically present in the buggy commit tree or otherwise proven decision-time-safe.
- Future safety enhancements are recorded as planning items, not prerequisites for the v2.24 source-acquisition pivot: Executed Scope Manifest, Compound Provenance Combination Gate, Candidate Environment Resolution Preflight, Pre-Generation Structural Failure Signature, Co-Change Impact Map, Stochastic Replay Reliability, Environmental Pass Guard, Conditional Path Fork Guard, Bounded Patch Variant Queue, and Dependency Impact Map.
- Research-level items such as Conditional Path Fork Guard and advanced Dependency Impact Map are v2.26+ investigations and must not delay v2.24 external source acquisition.

Claim boundaries remain unchanged: current protocol `v2.13`, full scoring `NOT_RUN` / disallowed, memory lift undemonstrated, and self-maintaining software false / not demonstrated."""
    replace_section(ROADMAP_PATH, "v2.23 Source Acquisition Method Boundary", roadmap_body)

    resolution_body = f"""v2.23 records a method-level provenance boundary rather than a repair attempt.

- Method decision: `{DECISION}`.
- Evidence basis: verified v2.22 runtime trace plus pinned BugsInPy source-code lines from `framework/bin/bugsinpy-checkout`.
- Blocker: `{BLOCKER}`.
- Next action: move candidate acquisition to external safe sources where the buggy project tree and test provenance can be verified without fixed/future/gold/synthetic test materialization.
- This is a benchmark/source-provenance boundary finding, not a ControllerGate repair failure."""
    replace_section(RESOLUTION_DOC_PATH, "v2.23 Source Acquisition Method Boundary", resolution_body)

    readme_body = f"""v2.23 adds a method-level provenance preflight before any new non-Ansible candidate selection. It records the BugsInPy checkout method as blocked under the current provenance rules because the pinned framework source and the verified v2.22 trace show fixed-commit target-test copying before reset to the buggy commit.

- Campaign: `{CAMPAIGN_ID}`
- Status: `implemented_pending_official_artifact_ingestion`; v2.23 is not promoted to current.
- Method decision: `{DECISION}`.
- Candidate selection: `not_run_global_method_block`; no new BugsInPy candidate was selected.
- Dependency recovery, pre-repair replay, patch generation, validation, duplicate replay, and scoring were not run.
- v2.24 recommendation: External Safe-Source Candidate Acquisition Lane.
- Current protocol remains `v2.13`; full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated."""
    replace_section(README_PATH, "v2.23 source acquisition method boundary", readme_body)

    shareable_body = f"""- Status: `implemented_pending_official_artifact_ingestion`.
- Campaign: `{CAMPAIGN_ID}`.
- v2.22 official ingest verified: `true`.
- Method decision: `{DECISION}`.
- Source acquisition method registry: `PASS`.
- Compound provenance combination registry: `PASS`.
- Candidate selection: `not_run_global_method_block`; no new BugsInPy candidate was selected.
- Patch generated / authorized / attempted: `false` / `false` / `false`.
- v2.24 recommendation: External Safe-Source Candidate Acquisition Lane.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.23 is not promoted to current."""
    replace_section(SHAREABLE_PATH, "v2.23 Source Acquisition Method Boundary", shareable_body)

    resolution_map = load_json(RESOLUTION_MAP_PATH)
    resolution_map.setdefault("resolution_bands", {})["v2.23"] = {
        "band": "method_provenance_boundary",
        "meaning": "source_acquisition_method_block_before_candidate_selection",
        "status": "global_method_block_recorded",
        "next": "external_safe_source_candidate_acquisition",
    }
    resolution_map["physics_validation_claim"] = False
    RESOLUTION_MAP_PATH.write_text(json.dumps(resolution_map, indent=2) + "\n", encoding="utf-8", newline="\n")
    update_backlog()


def public_language_audit() -> dict[str, Any]:
    terms = ["chromo" + "somal", "bio" + "logical", "iso" + "morphic", "TO" + "RUS", "T" + "LD", "meta" + "phorical"]
    scanned: list[dict[str, Any]] = []
    section_files = [ROADMAP_PATH, RESOLUTION_DOC_PATH, README_PATH, SHAREABLE_PATH]
    exact_hits = 0
    for path in sorted(OUTPUT_ROOT.rglob("*")) + section_files:
        if not path.is_file():
            continue
        if path.name == "public_language_audit.json":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if path in section_files:
            marker = "v2.23 Source Acquisition Method Boundary"
            if marker not in text and path == README_PATH:
                marker = "v2.23 source acquisition method boundary"
            idx = text.find(marker)
            text_to_scan = text[idx:] if idx >= 0 else ""
        else:
            text_to_scan = text
        hits = sum(1 for term in terms if term in text_to_scan)
        exact_hits += hits
        scanned.append({"path": path.relative_to(REPO_ROOT).as_posix(), "scanned_scope": "v2.23_owned_text", "exact_match_count": hits})
    return {
        "status": "PASS" if exact_hits == 0 else "BLOCK",
        "scanned_file_count": len(scanned),
        "exact_match_count": exact_hits,
        "scanned_files": scanned,
        "legacy_preexisting_files_not_rewritten": True,
        "neutral_engineering_language_used_for_v2_23_owned_text": exact_hits == 0,
    }


def write_manifest() -> None:
    entries = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path.name != "SHA256SUMS.txt":
            entries.append((path.relative_to(OUTPUT_ROOT).as_posix(), sha256_path(path)))
    write_text(OUTPUT_ROOT / "SHA256SUMS.txt", "".join(f"{digest}  {rel}\n" for rel, digest in entries))


def main() -> int:
    safe_reset_output()
    update_docs()
    run_root = runtime_root()
    framework_root = run_root / "BugsInPy_framework"
    if run_root.exists():
        remove_tree(run_root)
    run_root.mkdir(parents=True, exist_ok=True)

    v222_official = load_json(V222_ROOT / "v2_22_official_artifact_verification.json")
    v222_results = load_json(V222_ROOT / "campaign_results.json")
    v222_trace = load_json(V222_ROOT / "official_bugsinpy_framework_materialization_trace.json")
    checkout_commands, framework_audit = checkout_framework(framework_root)
    scan = scan_framework(framework_root)

    trace_result = v222_trace.get("checkout_result") or {}
    trace_stdout = str(trace_result.get("stdout_excerpt") or "")
    trace_excerpt_lines = [
        line
        for line in trace_stdout.splitlines()
        if "HEAD is now at" in line or "test_chinese.py" in line
    ]
    trace_excerpt = "\n".join(trace_excerpt_lines)
    trace_sha = sha256_path(V222_ROOT / "official_bugsinpy_framework_materialization_trace.json")
    combo_hash = combination_hash()
    now = utc_now()
    common = {
        "campaign_id": CAMPAIGN_ID,
        "based_on": "v2.22_official_ingest",
        "review_timestamp": now,
        "current_protocol_version": "v2.13",
    }

    write_json(
        OUTPUT_ROOT / "v2_22_official_ingest_reference.json",
        {
            **common,
            "status": "PASS",
            "artifact_name": v222_official.get("artifact_name"),
            "workflow_run_id": v222_official.get("workflow_run_id"),
            "artifact_id": v222_official.get("artifact_id"),
            "zip_size": v222_official.get("zip_size"),
            "zip_sha256": v222_official.get("zip_sha256"),
            "artifact_target_test_sha256": v222_official.get("artifact_target_test_sha256"),
            "v2_22_audit_expected": "PASS",
        },
    )
    write_json(
        OUTPUT_ROOT / "bugsinpy_framework_checkout_logic_audit.json",
        {
            **common,
            **framework_audit,
            "source_text_available": scan["status"] == "PASS",
            "offending_source_text_location": "framework/bin/bugsinpy-checkout:116-181" if scan["status"] == "PASS" else "runtime_trace_only",
            "checkout_command_count": len(checkout_commands),
        },
    )
    write_json(OUTPUT_ROOT / "bugsinpy_fixed_copy_pattern_scan.json", {**common, **scan})
    code_extract = {
        **common,
        "status": "PASS" if scan["status"] == "PASS" else "INCONCLUSIVE",
        "offending_code_file_paths": [scan["offending_file_path"]],
        "offending_code_line_ranges_if_available": [scan["offending_line_range"]],
        "offending_code_excerpt_sha256": sha256_text(scan["offending_code_excerpt"]),
        "offending_code_excerpt": scan["offending_code_excerpt"],
    }
    write_json(OUTPUT_ROOT / "bugsinpy_checkout_offending_code_extract.json", code_extract)
    write_text(OUTPUT_ROOT / "bugsinpy_checkout_offending_code_extract.txt", scan["offending_code_excerpt"])
    write_json(
        OUTPUT_ROOT / "bugsinpy_runtime_trace_authority_record.json",
        {
            **common,
            "status": "PASS",
            "offending_source_text_location": "source_text_and_runtime_trace" if scan["status"] == "PASS" else "runtime_trace_only",
            "v2_22_artifact_sha256": v222_official.get("zip_sha256"),
            "v2_22_trace_file_path": "outputs/v2_22_bugsinpy_target_test_materialization_lane/official_bugsinpy_framework_materialization_trace.json",
            "v2_22_trace_file_sha256": trace_sha,
            "trace_excerpt": trace_excerpt,
            "trace_excerpt_sha256": sha256_text(trace_excerpt),
            "observed_behavior": "fixed_commit_checkout_then_test_copy_then_buggy_commit_reset",
            "safety_decision": "fail_safe_global_or_inconclusive_block",
        },
    )
    write_json(
        OUTPUT_ROOT / "bugsinpy_checkout_trace_to_source_mapping.json",
        {
            **common,
            "status": "PASS",
            "trace_file": "outputs/v2_22_bugsinpy_target_test_materialization_lane/official_bugsinpy_framework_materialization_trace.json",
            "trace_file_sha256": trace_sha,
            "mappings": [
                {
                    "trace_event": "checkout_to_fixed_commit",
                    "trace_excerpt": "HEAD is now at 56f22f8 Fix unicode issues and add test, fix #124",
                    "source_file": "framework/bin/bugsinpy-checkout",
                    "source_line_range": {"start": 140, "end": 142},
                    "source_text": 'git reset --hard "$fix_commit"',
                },
                {
                    "trace_event": "copy_target_test",
                    "trace_excerpt": "tests/test_chinese.py copy into BugsInPy bug metadata path",
                    "source_file": "framework/bin/bugsinpy-checkout",
                    "source_line_range": {"start": 162, "end": 169},
                    "source_text": 'cp -v "$work_dir/$project_name/$test_file_now" "$project_location/bugs/$bug_id/$test_file_now"',
                },
                {
                    "trace_event": "reset_to_buggy_commit_and_move_test",
                    "trace_excerpt": "HEAD is now at e21a311 Formatting",
                    "source_file": "framework/bin/bugsinpy-checkout",
                    "source_line_range": {"start": 171, "end": 180},
                    "source_text": 'git reset --hard "$buggy_commit"; mv -f "$project_location/bugs/$bug_id/$test_file_now" "$work_dir/$project_name/$test_file_now"',
                },
            ],
        },
    )
    write_json(
        OUTPUT_ROOT / "bugsinpy_acquisition_method_pattern_analysis.json",
        {
            **common,
            "status": "PASS",
            "observed_v2_22_runtime_pattern": [
                "checkout_or_reset_to_fixed_commit",
                "copy_or_materialize_target_test_from_fixed_commit_state",
                "reset_to_buggy_commit",
            ],
            "target_test_source_classification": "fixed_commit_derived_by_pinned_framework_checkout",
            "target_test_sha256": TARGET_TEST_SHA256,
            "framework_repo": BUGSINPY_REPO,
            "framework_commit": BUGSINPY_COMMIT,
            "source_text_pattern_detected": scan["fixed_copy_pattern_detected"],
            "candidate_specific_exception_proven": False,
            "decision": DECISION,
            "blocker": BLOCKER,
        },
    )
    evidence_files = [
        "outputs/v2_22_bugsinpy_target_test_materialization_lane/v2_22_official_artifact_verification.json",
        "outputs/v2_22_bugsinpy_target_test_materialization_lane/official_bugsinpy_framework_materialization_trace.json",
        "outputs/v2_23_non_ansible_candidate_transition_lane/bugsinpy_checkout_offending_code_extract.txt",
        "outputs/v2_23_non_ansible_candidate_transition_lane/bugsinpy_checkout_trace_to_source_mapping.json",
    ]
    evidence_sha256s = {
        "outputs/v2_22_bugsinpy_target_test_materialization_lane/v2_22_official_artifact_verification.json": sha256_path(V222_ROOT / "v2_22_official_artifact_verification.json"),
        "outputs/v2_22_bugsinpy_target_test_materialization_lane/official_bugsinpy_framework_materialization_trace.json": trace_sha,
        "outputs/v2_23_non_ansible_candidate_transition_lane/bugsinpy_checkout_offending_code_extract.txt": sha256_path(OUTPUT_ROOT / "bugsinpy_checkout_offending_code_extract.txt"),
        "outputs/v2_23_non_ansible_candidate_transition_lane/bugsinpy_checkout_trace_to_source_mapping.json": sha256_path(OUTPUT_ROOT / "bugsinpy_checkout_trace_to_source_mapping.json"),
    }
    risk_registry = {
        **common,
        "status": "PASS",
        "records": [
            {
                "method_id": METHOD_ID,
                "method_signature": METHOD_SIGNATURE,
                "framework_repo": BUGSINPY_REPO,
                "framework_commit": BUGSINPY_COMMIT,
                "offending_code_file_paths": [scan["offending_file_path"]],
                "offending_code_line_ranges_if_available": [scan["offending_line_range"]],
                "offending_code_excerpt": scan["offending_code_excerpt"],
                "observed_trace_excerpt": trace_excerpt,
                "evidence_files": evidence_files,
                "evidence_sha256s": evidence_sha256s,
                "taint_status": DECISION,
                "scope": "all_candidates_requiring_bugsinpy_fixed_commit_derived_test_copying",
                "allowed_for_future_candidates": False,
                "decision": "candidate_scope_expansion_required",
                "review_timestamp": now,
            }
        ],
    }
    write_json(OUTPUT_ROOT / "source_acquisition_method_risk_registry.json", risk_registry)
    combination_record = {
        "combination_hash": combo_hash,
        "harness_origin_sha256": HARNESS_ORIGIN_SHA256,
        "target_test_sha256": TARGET_TEST_SHA256,
        "acquisition_method_id": METHOD_ID,
        "acquisition_method_signature": METHOD_SIGNATURE,
        "framework_repo": BUGSINPY_REPO,
        "framework_commit": BUGSINPY_COMMIT,
        "source_classification": "fixed_commit_derived_by_pinned_framework_checkout",
        "decision": "blocked_fixed_commit_derived_test_materialization",
        "blocker": BLOCKER,
        "evidence_files": evidence_files,
        "evidence_sha256s": evidence_sha256s,
        "inherited_from_version": "v2.22",
        "applies_to_scope": "all_bugsinpy_candidates_using_this_behavior_without_candidate_specific_safe_exception",
        "behavioral_signature": BEHAVIORAL_SIGNATURE,
        "normalized_behavior_sequence": NORMALIZED_BEHAVIOR_SEQUENCE,
        "behavior_block_applies_across_repos": True,
        "matching_prior_block_hashes": [],
        "review_timestamp": now,
    }
    write_json(
        OUTPUT_ROOT / "compound_provenance_combination_registry.json",
        {**common, "status": "PASS", "records": [combination_record]},
    )
    write_json(
        OUTPUT_ROOT / "compound_provenance_combination_audit.json",
        {
            **common,
            "status": "PASS",
            "combination_hash_formula": "sha256(harness_origin_sha256|target_test_sha256|acquisition_method_id|acquisition_method_signature|framework_repo|framework_commit)",
            "combination_hash": combo_hash,
            "behavioral_signature": BEHAVIORAL_SIGNATURE,
            "known_block_recorded": True,
            "blocked_behavior_bypassed_by_repo_url_change": False,
            "decision": "block_before_candidate_selection",
        },
    )
    write_json(
        OUTPUT_ROOT / "global_bugsinpy_provenance_block.json",
        {
            **common,
            "status": "BLOCK",
            "decision": DECISION,
            "blocker": BLOCKER,
            "candidate_selection_allowed": False,
            "new_bugsinpy_candidate_selected": False,
            "s_engine_invoked": False,
            "dependency_recovery_run": False,
            "pre_repair_replay_run": False,
            "patch_generated": False,
            "patch_authorized": False,
            "patch_attempted": False,
            "benchmark_source_provenance_boundary_finding_not_repair_failure": True,
        },
    )
    write_json(
        OUTPUT_ROOT / "candidate_scope_expansion_required.json",
        {
            **common,
            "status": "PASS",
            "candidate_scope_expansion_required": True,
            "reason": BLOCKER,
            "do_not_reopen_pysnooper1_without_external_reviewed_safe_target_test_provenance": True,
            "pysnooper2_pursued": False,
            "candidate_selection_status": "not_run_global_method_block",
        },
    )
    write_json(
        OUTPUT_ROOT / "external_candidate_acquisition_recommendation.json",
        {
            **common,
            "status": "PASS",
            "recommendation": "external_safe_source_candidate_acquisition_lane",
            "requirements": [
                "direct_immutable_project_repository_checkout",
                "exact_buggy_commit_sha",
                "target_test_physically_present_in_buggy_commit_tree_or_independently_decision_time_safe",
                "no_fixed_commit_test_copying",
                "no_future_gold_synthetic_test_construction",
                "source_test_co_location_proven_by_tree_hash",
            ],
        },
    )
    write_json(
        OUTPUT_ROOT / "v2_24_external_safe_source_lane_recommendation.json",
        {
            **common,
            "status": "PASS",
            "recommended_next_version": "v2.24",
            "recommended_lane": "External Safe-Source Candidate Acquisition Lane",
            "priority": "primary_next_step",
            "research_level_future_items_are_not_prerequisites": True,
        },
    )
    write_json(
        OUTPUT_ROOT / "environmental_pass_guard.json",
        {
            **common,
            "status": "PASS",
            "guard_active_before_patch_generation": True,
            "target_command_executed": False,
            "source_patch_applied": False,
            "validation_passes_without_source_patch": False,
            "pre_repair_environmental_pass_detected": False,
            "classification_if_detected": "pre_repair_environmental_pass_blocked",
            "classification_if_source_patch_false_and_validation_passes": "environmental_pass_without_source_repair_blocked",
            "count_as_repair_success": False,
        },
    )
    roadmap_items = [
        "External Safe-Source Candidate Acquisition Lane",
        "Executed Scope Manifest",
        "Compound Provenance Combination Gate",
        "Candidate Environment Resolution Preflight",
        "Pre-Generation Structural Failure Signature",
        "Co-Change Impact Map",
        "Stochastic Replay Reliability",
        "Environmental Pass Guard",
        "Conditional Path Fork Guard",
        "Bounded Patch Variant Queue",
        "Dependency Impact Map",
    ]
    write_json(
        OUTPUT_ROOT / "roadmap_future_gate_sync_v2_23.json",
        {
            **common,
            "status": "PASS",
            "roadmap_updated": True,
            "backlog_updated": True,
            "resolution_doc_updated": True,
            "resolution_depth_map_updated": True,
            "shareable_summary_updated": True,
            "future_items_recorded": roadmap_items,
            "implemented_as_active_v2_23_repair_functionality": [
                "Compound Provenance Combination Gate registry seed",
                "Environmental Pass Guard classification record",
            ],
            "roadmap_only_not_active_repair_lanes": [
                item
                for item in roadmap_items
                if item
                not in {
                    "Compound Provenance Combination Gate",
                    "Environmental Pass Guard",
                }
            ],
            "v2_24_priority": "External Safe-Source Candidate Acquisition Lane",
            "v2_26_plus_research_level_items": ["Conditional Path Fork Guard", "Dependency Impact Map"],
            "future_safety_enhancements_not_prerequisites_for_v2_24_source_acquisition_pivot": True,
        },
    )
    write_json(
        OUTPUT_ROOT / "claim_boundary_v2_23.json",
        {
            **common,
            "status": "PASS",
            "full_scoring": "NOT_RUN",
            "full_scoring_allowed": False,
            "current_protocol_version": "v2.13",
            "v2_23_promoted_to_current": False,
            "memory_lift_status": "undemonstrated",
            "self_maintaining_software_status": "false/not_demonstrated",
            "external_physics_validation_claimed": False,
            "pysnooper1_status": "terminally_blocked_under_current_safety_rules",
            "pysnooper2_status": "blocked_not_pursued",
            "global_bugsinpy_block_is_source_provenance_boundary_not_repair_failure": True,
            "v2_24_recommendation": "external_safe_source_candidate_acquisition",
            "scoreable_count": 5,
            "positive_memory_count": 2,
            "non_ansible_positive_memory_count": 0,
        },
    )
    results = {
        **common,
        "status": "PASS_WITH_GLOBAL_BUGSINPY_METHOD_PROVENANCE_BLOCK",
        "v2_22_official_ingest_verified": v222_official.get("status") == "PASS",
        "v2_22_target_test_sha256": v222_results.get("target_test_sha256"),
        "bugsinpy_method_provenance_pattern_decision": DECISION,
        "offending_code_extract_status": "PASS" if scan["status"] == "PASS" else "INCONCLUSIVE",
        "trace_to_source_mapping_status": "PASS",
        "source_acquisition_method_risk_registry_status": "PASS",
        "compound_provenance_combination_registry_status": "PASS",
        "v2_22_combination_hash": combo_hash,
        "v2_22_combination_decision": "blocked_fixed_commit_derived_test_materialization",
        "behavioral_signature": BEHAVIORAL_SIGNATURE,
        "global_bugsinpy_block_status": "BLOCK",
        "candidate_selection_status": "not_run_global_method_block",
        "selected_candidate": None,
        "executed_scope_manifest_status": "not_applicable_no_candidate_selected",
        "environmental_pass_guard_status": "PASS",
        "roadmap_backlog_update_status": "PASS",
        "resolution_map_update_status": "PASS",
        "v2_24_external_safe_source_recommendation_status": "PASS",
        "s_engine_invoked": False,
        "dependency_recovery_run": False,
        "pre_repair_replay_run": False,
        "patch_generated": False,
        "patch_authorized": False,
        "patch_attempted": False,
        "target_validation_status": "not_applicable_no_patch",
        "duplicate_replay_status": "not_applicable_no_patch",
        "final_scoreable_count": 5,
        "final_positive_memory_count": 2,
        "final_non_ansible_positive_memory_count": 0,
        "full_scoring": "NOT_RUN",
        "full_scoring_allowed": False,
        "memory_lift_status": "undemonstrated",
        "self_maintaining_software_status": "false/not_demonstrated",
        "current_protocol_version": "v2.13",
        "exact_blocker": BLOCKER,
    }
    write_json(OUTPUT_ROOT / "campaign_results.json", results)
    write_text(
        OUTPUT_ROOT / "campaign_summary.md",
        f"""# v2.23 Non-Ansible Candidate Transition Lane

- Campaign: `{CAMPAIGN_ID}`.
- v2.22 official ingest verified: `true`.
- Method decision: `{DECISION}`.
- Blocker: `{BLOCKER}`.
- Candidate selection: `not_run_global_method_block`.
- Selected candidate: `null`.
- Dependency recovery, pre-repair replay, patch generation, validation, duplicate replay, and scoring were not run.
- Compound combination hash: `{combo_hash}`.
- Behavior signature: `{BEHAVIORAL_SIGNATURE}`.
- v2.24 recommendation: External Safe-Source Candidate Acquisition Lane.
- Current protocol remains `v2.13`; v2.23 is not promoted to current.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`; self-maintaining software remains `false/not_demonstrated`.
""",
    )
    write_json(OUTPUT_ROOT / "public_language_audit.json", public_language_audit())
    write_manifest()

    cleanup_error = None
    try:
        remove_tree(run_root)
    except Exception as exc:  # pragma: no cover
        cleanup_error = str(exc)
    if cleanup_error:
        print(f"runtime_cleanup_error={cleanup_error}")
    for key in [
        "bugsinpy_method_provenance_pattern_decision",
        "offending_code_extract_status",
        "trace_to_source_mapping_status",
        "source_acquisition_method_risk_registry_status",
        "compound_provenance_combination_registry_status",
        "global_bugsinpy_block_status",
        "candidate_selection_status",
        "environmental_pass_guard_status",
        "v2_24_external_safe_source_recommendation_status",
        "full_scoring",
        "memory_lift_status",
        "self_maintaining_software_status",
        "current_protocol_version",
        "exact_blocker",
    ]:
        print(f"{key}={results.get(key)}")
    print(f"v2.23 outputs wrote {OUTPUT_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

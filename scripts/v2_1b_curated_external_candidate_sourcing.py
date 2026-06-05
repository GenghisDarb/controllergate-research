#!/usr/bin/env python3
"""Run v2.1b curated external candidate sourcing preflight.

This harness expands candidate sourcing toward curated/known-reproducible
sources. It ranks candidates for future v2.2 replay attempts only. It does not
execute repairs, run memory-vs-no-memory scoring, or contact upstream projects.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = REPO_ROOT / "inputs" / "v2_1b_curated_candidate_sources.json"
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_1b_curated_external_candidate_sourcing"

VALID_TIERS = {
    "tier_1_curated_bug_benchmarks",
    "tier_2_small_public_repos_with_simple_tests",
    "tier_3_archived_public_repos_with_dependency_drift",
    "tier_4_forked_issue_replay_candidates",
    "tier_5_user_owned_fallback_not_external",
}

CONTROLLED_STATUSES = {
    "ready_for_v2_2_candidate",
    "needs_manual_review",
    "not_ready",
    "blocked_candidate_source_unavailable",
    "blocked_local_replay_failed",
    "rejected_no_local_test_command",
    "rejected_no_deterministic_failure",
    "rejected_private_service_required",
    "rejected_license_or_ethics_unclear",
    "rejected_runtime_too_large",
    "rejected_environment_not_reproducible",
    "rejected_subjective_validator",
    "rejected_security_exploit_target",
    "rejected_remote_ci_only",
    "rejected_no_baseline_path",
    "rejected_no_corruption_check",
}

REQUIRED_INPUT_FIELDS = {
    "candidate_id",
    "candidate_source_family",
    "source_tier",
    "language_hint",
    "license_hint",
    "expected_setup_command",
    "expected_test_command",
    "known_failure_description",
    "expected_memory_relevance",
    "notes",
}

LICENSE_NAMES = ("LICENSE", "LICENSE.txt", "LICENSE.md", "COPYING", "COPYING.txt", "NOTICE")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_recursive_manifest(directory: Path) -> None:
    paths = sorted(
        [path for path in directory.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: str(path.relative_to(directory)).replace("\\", "/"),
    )
    lines = [f"{sha_file(path)}  {str(path.relative_to(directory)).replace(chr(92), '/')}" for path in paths]
    write_text(directory / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def resolve_local_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def run_git(repo: Path, *args: str) -> str | None:
    safe = str(repo.resolve()).replace("\\", "/")
    try:
        result = subprocess.run(
            ["git", "-c", f"safe.directory={safe}", "-C", str(repo), *args],
            text=True,
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return result.stdout.strip()


def repo_file_count(root: Path) -> int:
    count = 0
    for path in root.rglob("*"):
        if ".git" in path.parts:
            continue
        if path.is_file():
            count += 1
            if count > 10000:
                break
    return count


def license_status(root: Path | None, license_hint: str) -> dict[str, Any]:
    files: list[dict[str, str]] = []
    if root and root.exists():
        for name in LICENSE_NAMES:
            path = root / name
            if path.exists() and path.is_file():
                first_line = next(
                    (line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()),
                    "",
                )
                files.append({"path": name, "first_line": first_line, "sha256": sha_file(path)})
    lowered = license_hint.lower()
    unclear_tokens = ["unavailable", "must be verified", "unclear"]
    status = "clear" if files or (license_hint and not any(token in lowered for token in unclear_tokens)) else "unclear"
    return {"status": status, "license_hint": license_hint, "license_files_found": files}


def detect_ecosystem(root: Path | None, language_hint: str) -> dict[str, Any]:
    hint = (language_hint or "").lower()
    signals: list[str] = []
    ecosystem = "unknown"
    if root and root.exists():
        file_map = {
            "python": ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt", "tox.ini", "pytest.ini"],
            "javascript_typescript": ["package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "tsconfig.json"],
            "rust": ["Cargo.toml"],
            "go": ["go.mod"],
            "java": ["pom.xml", "build.gradle", "build.gradle.kts", "gradlew"],
            "flutter_dart": ["pubspec.yaml"],
        }
        for name, files in file_map.items():
            observed = [file for file in files if (root / file).exists()]
            if observed:
                ecosystem = name
                signals.extend(observed)
                break
        if ecosystem == "unknown" and list(root.rglob("*.py"))[:1]:
            ecosystem = "python"
            signals.append("*.py")
    if ecosystem == "unknown":
        ecosystem = {
            "python": "python",
            "py": "python",
            "javascript": "javascript_typescript",
            "typescript": "javascript_typescript",
            "js": "javascript_typescript",
            "ts": "javascript_typescript",
            "rust": "rust",
            "go": "go",
            "java": "java",
            "flutter": "flutter_dart",
            "dart": "flutter_dart",
            "shell": "generic_shell",
        }.get(hint, "unknown")
    return {"ecosystem": ecosystem, "signals": signals, "language_hint": language_hint}


def command_available(candidate: dict[str, Any], root: Path | None, ecosystem: str) -> tuple[bool, list[str], list[str]]:
    commands: list[str] = []
    sources: list[str] = []
    expected_test = str(candidate.get("expected_test_command") or "").strip()
    if expected_test and "unavailable" not in expected_test.lower():
        commands.append(expected_test)
        sources.append("descriptor_expected_test_command")
    if root and root.exists():
        if ecosystem == "python":
            if (root / "pyproject.toml").exists() or (root / "pytest.ini").exists() or (root / "tests").exists():
                if "python -m pytest" not in commands:
                    commands.append("python -m pytest")
                    sources.append("detected_python_pytest")
        elif ecosystem == "javascript_typescript" and (root / "package.json").exists():
            text = (root / "package.json").read_text(encoding="utf-8", errors="replace")
            if '"test"' in text and "npm test" not in commands:
                commands.append("npm test")
                sources.append("detected_npm_test")
        elif ecosystem == "rust" and (root / "Cargo.toml").exists():
            commands.append("cargo test")
            sources.append("detected_cargo_test")
        elif ecosystem == "go" and (root / "go.mod").exists():
            commands.append("go test ./...")
            sources.append("detected_go_test")
        elif ecosystem == "java":
            if (root / "pom.xml").exists():
                commands.append("mvn test")
                sources.append("detected_maven_test")
            elif (root / "gradlew").exists():
                commands.append("./gradlew test")
                sources.append("detected_gradlew_test")
        elif ecosystem == "flutter_dart" and (root / "pubspec.yaml").exists():
            commands.append("flutter test")
            sources.append("detected_flutter_test")
    deduped = list(dict.fromkeys(commands))
    return bool(deduped), deduped, sources[: len(deduped)]


def has_known_failure(candidate: dict[str, Any]) -> bool:
    description = str(candidate.get("known_failure_description") or "").strip().lower()
    issue = candidate.get("issue_or_bug_reference")
    if issue:
        return True
    unavailable_markers = [
        "no specific",
        "no deterministic",
        "no local",
        "no known",
        "not yet",
        "unavailable",
    ]
    return bool(description) and not any(marker in description for marker in unavailable_markers)


def source_quality_score(
    candidate: dict[str, Any],
    command_present: bool,
    file_count: int,
    license_info: dict[str, Any],
    known_failure: bool,
) -> tuple[int, dict[str, int]]:
    family = str(candidate.get("candidate_source_family") or "").lower()
    tier = candidate.get("source_tier")
    source_quality = {
        "curated_bug_benchmark": 25 if tier == "tier_1_curated_bug_benchmarks" else 0,
        "known_reproducible_failure": 25 if known_failure else 0,
        "clear_deterministic_command": 20 if command_present else 0,
        "small_bounded_runtime": 10 if file_count and file_count <= 5000 else (10 if "small" in family else 0),
        "license_clarity": 10 if license_info["status"] == "clear" else 0,
        "memory_relevance": 10 if candidate.get("expected_memory_relevance") else 0,
    }
    return min(100, sum(source_quality.values())), source_quality


def readiness_score(
    root: Path | None,
    command_present: bool,
    license_info: dict[str, Any],
    file_count: int,
    known_failure: bool,
    private_or_secret: bool,
) -> tuple[int, dict[str, int]]:
    local_exists = bool(root and root.exists() and (root / ".git").exists())
    bounded_runtime = local_exists and file_count <= 5000
    score = {
        "deterministic_local_command": 20 if command_present else 0,
        "environment_reproducibility": 15 if local_exists and not private_or_secret else 0,
        "license_ethics_clarity": 10 if license_info["status"] == "clear" else 0,
        "bounded_runtime": 10 if bounded_runtime else 0,
        "artifact_custody_feasibility": 15 if local_exists else 0,
        "baseline_comparability": 10 if command_present and not private_or_secret else 0,
        "corruption_check_availability": 10 if local_exists and command_present else 0,
        "memory_relevance": 10 if known_failure else 5 if local_exists else 0,
    }
    return min(100, sum(score.values())), score


def classify_candidate(
    candidate: dict[str, Any],
    root: Path | None,
    license_info: dict[str, Any],
    command_present: bool,
    known_failure: bool,
    readiness: int,
    source_quality: int,
) -> tuple[str, str]:
    missing = sorted(field for field in REQUIRED_INPUT_FIELDS if field not in candidate)
    if missing:
        return "not_ready", f"Candidate descriptor missing required fields: {', '.join(missing)}"
    if candidate.get("source_tier") not in VALID_TIERS:
        return "not_ready", "Candidate source tier is outside the controlled vocabulary."
    notes = f"{candidate.get('notes', '')} {candidate.get('known_failure_description', '')}".lower()
    if "security exploit" in notes:
        return "rejected_security_exploit_target", "Security exploit tasks are disallowed."
    if "private service" in notes or "private api" in notes or "secret" in notes or "paid service" in notes:
        return "rejected_private_service_required", "Candidate appears to require private services, credentials, or paid APIs."
    if root is None or not root.exists() or not (root / ".git").exists():
        return "blocked_candidate_source_unavailable", "Candidate source is not locally available; no network clone was attempted."
    if license_info["status"] != "clear":
        return "rejected_license_or_ethics_unclear", "License/ethics status is unclear."
    if not command_present:
        return "rejected_no_local_test_command", "No deterministic local test/build/lint command is available."
    if not known_failure:
        return "needs_manual_review", "Local source and deterministic command exist, but no reproducible failing issue/bug reference is known yet."
    if readiness >= 75 and source_quality >= 70:
        return "ready_for_v2_2_candidate", "Candidate appears ready for future v2.2 replay execution, not repair scoring now."
    return "needs_manual_review", "Candidate has promising metadata but needs human review before v2.2."


def evaluate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    root = resolve_local_path(candidate.get("local_path"))
    git_head = run_git(root, "rev-parse", "HEAD") if root and root.exists() else None
    git_branch = run_git(root, "rev-parse", "--abbrev-ref", "HEAD") if root and root.exists() else None
    file_count = repo_file_count(root) if root and root.exists() and (root / ".git").exists() else 0
    ecosystem = detect_ecosystem(root, str(candidate.get("language_hint") or ""))
    license_info = license_status(root, str(candidate.get("license_hint") or ""))
    command_present, commands, command_sources = command_available(candidate, root, ecosystem["ecosystem"])
    known_failure = has_known_failure(candidate)
    private_or_secret = any(
        token in f"{candidate.get('notes', '')} {candidate.get('known_failure_description', '')}".lower()
        for token in ["private service", "private api", "secret", "paid service"]
    )
    readiness, readiness_breakdown = readiness_score(root, command_present, license_info, file_count, known_failure, private_or_secret)
    quality, quality_breakdown = source_quality_score(candidate, command_present, file_count, license_info, known_failure)
    status, reason = classify_candidate(candidate, root, license_info, command_present, known_failure, readiness, quality)
    return {
        "candidate_id": candidate.get("candidate_id"),
        "candidate_source_family": candidate.get("candidate_source_family"),
        "source_tier": candidate.get("source_tier"),
        "repo_url": candidate.get("repo_url"),
        "dataset_reference": candidate.get("dataset_reference"),
        "local_path": str(root) if root else None,
        "language_hint": candidate.get("language_hint"),
        "license_ethics": license_info,
        "source_custody": {
            "local_source_available": bool(root and root.exists() and (root / ".git").exists()),
            "git_head_sha": git_head,
            "git_branch": git_branch,
            "no_upstream_disruption_required": True,
            "remote_ci_logs_used": False,
        },
        "ecosystem_detection": ecosystem,
        "command_detection": {
            "deterministic_command_available": command_present,
            "commands": commands,
            "sources": command_sources,
            "expected_setup_command": candidate.get("expected_setup_command"),
            "expected_test_command": candidate.get("expected_test_command"),
        },
        "replay_preflight": {
            "clean_checkout_feasible": bool(root and root.exists() and (root / ".git").exists()),
            "local_failure_reproducible_now": known_failure and bool(root and root.exists()),
            "known_failure_description": candidate.get("known_failure_description"),
            "issue_or_bug_reference": candidate.get("issue_or_bug_reference"),
            "runtime_budget_likely_bounded": bool(file_count and file_count <= 5000),
            "environment_reproducible": bool(root and root.exists() and not private_or_secret),
            "no_private_service_or_secret_required": not private_or_secret,
            "artifact_custody_feasible": bool(root and root.exists()),
            "no_memory_baseline_feasible": command_present and not private_or_secret,
            "memory_enabled_path_feasible": command_present and not private_or_secret,
            "corruption_downstream_check_feasible": command_present and bool(root and root.exists()),
        },
        "memory_relevance": {
            "expected_memory_relevance": candidate.get("expected_memory_relevance"),
            "score_component": quality_breakdown["memory_relevance"],
        },
        "readiness_score": readiness,
        "readiness_score_breakdown": readiness_breakdown,
        "source_quality_score": quality,
        "source_quality_score_breakdown": quality_breakdown,
        "classification": status,
        "classification_reason": reason,
        "claim_boundaries": {
            "candidate_readiness_is_not_repair_success": True,
            "ready_candidate_only_authorizes_future_v2_2_attempt": status == "ready_for_v2_2_candidate",
            "repair_scoring_run": False,
            "memory_vs_no_memory_repairs_run": False,
            "external_memory_lift_demonstrated": False,
            "self_maintaining_software_demonstrated": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
        },
    }


def summary_markdown(ranked: list[dict[str, Any]], handoff: dict[str, Any], gap_analysis: dict[str, Any]) -> str:
    ready = [item for item in ranked if item["classification"] == "ready_for_v2_2_candidate"]
    review = [item for item in ranked if item["classification"] == "needs_manual_review"]
    rejected_or_blocked = [item for item in ranked if item["classification"].startswith(("rejected", "blocked"))]
    best_families = gap_analysis["best_source_families"]
    lines = [
        "# v2.1b Curated External Candidate Sourcing Result",
        "",
        "v2.1b improves candidate sourcing quality.",
        "",
        f"- Candidate pool produced: true",
        f"- Candidates evaluated: {len(ranked)}",
        f"- Ready candidates count: {len(ready)}",
        f"- Manual-review candidates count: {len(review)}",
        f"- Rejected/blocked candidates count: {len(rejected_or_blocked)}",
        f"- Best source families: {', '.join(best_families) if best_families else 'none'}",
        f"- v2.2 handoff recommendation: `{handoff['recommendation']}`",
        "- Candidate readiness is not repair success.",
        "- Ready candidates only authorize future v2.2 replay attempts.",
        "- Blocked acquisition is not negative capability evidence.",
        "- External memory lift remains undemonstrated.",
        "- Self-maintaining software remains undemonstrated.",
        "- Full scoring remains disallowed.",
        "",
        "## Ranked Candidates",
        "",
    ]
    for item in ranked:
        lines.append(
            f"- `{item['candidate_id']}`: readiness {item['readiness_score']}, source quality {item['source_quality_score']}, classification `{item['classification']}`"
        )
    lines.extend(
        [
            "",
            "## Source Gap Analysis",
            "",
            gap_analysis["summary"],
        ]
    )
    return "\n".join(lines) + "\n"


def gap_analysis(ranked: list[dict[str, Any]]) -> dict[str, Any]:
    ready = [item for item in ranked if item["classification"] == "ready_for_v2_2_candidate"]
    review = [item for item in ranked if item["classification"] == "needs_manual_review"]
    blocked_source = [item for item in ranked if item["classification"] == "blocked_candidate_source_unavailable"]
    no_failure_review = [item for item in ranked if item["classification"] == "needs_manual_review"]
    best = sorted(ranked, key=lambda item: (-item["source_quality_score"], -item["readiness_score"]))[:3]
    summary = (
        "Curated source quality improved, but v2.1b still did not acquire a ready v2.2 candidate. "
        "Curated benchmark descriptors are blocked because local datasets/checkouts are unavailable. "
        "Local public Python repos have clone, license, and command feasibility, but lack known deterministic failing issue branches. "
        "The next acquisition step should supply local benchmark datasets or issue-branch descriptors with exact failing commands."
    )
    return {
        "ready_candidate_count": len(ready),
        "manual_review_candidate_count": len(review),
        "blocked_source_unavailable_count": len(blocked_source),
        "manual_review_missing_known_failure_count": len(no_failure_review),
        "best_source_families": [item["candidate_source_family"] for item in best],
        "desired_next_sources": [
            "local BugsInPy-style task manifests with checkout/test commands",
            "local QuixBugs-style checkout with deterministic failing test command",
            "known public issue branches with exact local reproduction commands",
            "archived dependency-drift repos with pinned old/new environment commands",
        ],
        "summary": summary,
        "blocked_acquisition_is_negative_capability_evidence": False,
    }


def main() -> int:
    input_data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    candidates = input_data.get("candidates", [])
    if not isinstance(candidates, list):
        raise SystemExit("v2.1b input must contain a candidates list")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = [evaluate_candidate(candidate) for candidate in candidates]
    ranked = sorted(results, key=lambda item: (-item["readiness_score"], -item["source_quality_score"], str(item["candidate_id"])))
    ready = [item for item in ranked if item["classification"] == "ready_for_v2_2_candidate"]
    review = [item for item in ranked if item["classification"] == "needs_manual_review"]
    rejected_or_blocked = [item for item in ranked if item["classification"].startswith(("rejected", "blocked"))]
    if len(ready) >= 3:
        recommendation = "v2_2_external_fork_limited_replay_execution"
    elif len(ready) >= 1:
        recommendation = "v2_2_small_external_fork_probe"
    elif review:
        recommendation = "manual_candidate_triage_before_v2_2"
    else:
        recommendation = "continue_curated_candidate_acquisition"
    handoff = {
        "recommendation": recommendation,
        "ready_candidate_count": len(ready),
        "manual_review_candidate_count": len(review),
        "rejected_or_blocked_candidate_count": len(rejected_or_blocked),
        "ready_candidate_ids": [item["candidate_id"] for item in ready],
        "manual_review_candidate_ids": [item["candidate_id"] for item in review],
        "v2_2_authorized_next_step": bool(ready),
        "repair_execution_allowed_now": False,
        "scoring_allowed_now": False,
        "external_memory_lift_demonstrated": False,
        "self_maintaining_software_demonstrated": False,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
    }
    gap = gap_analysis(ranked)
    search_log = {
        "harness_id": "v2_1b_curated_external_candidate_sourcing",
        "harness_status": "curated_candidate_preflight_completed",
        "input_path": str(INPUT_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(ranked),
        "upstream_interactions": "none",
        "remote_ci_logs_used": False,
        "repairs_executed": False,
        "memory_vs_no_memory_scoring_run": False,
        "candidate_readiness_is_repair_success": False,
        "external_memory_lift_demonstrated": False,
        "self_maintaining_software_demonstrated": False,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
    }
    preflight = {
        "schema_version": "1.0",
        "results": ranked,
        "ready_candidate_count": len(ready),
        "manual_review_candidate_count": len(review),
        "rejected_or_blocked_candidate_count": len(rejected_or_blocked),
    }
    rejection_table = {
        "controlled_classifications": sorted(CONTROLLED_STATUSES),
        "records": [
            {
                "candidate_id": item["candidate_id"],
                "candidate_source_family": item["candidate_source_family"],
                "classification": item["classification"],
                "readiness_score": item["readiness_score"],
                "source_quality_score": item["source_quality_score"],
                "reason": item["classification_reason"],
            }
            for item in ranked
            if item["classification"] != "ready_for_v2_2_candidate"
        ],
        "classification_counts": {
            classification: sum(1 for item in ranked if item["classification"] == classification)
            for classification in sorted(CONTROLLED_STATUSES)
        },
    }
    ranked_pool = {
        "ranking_order": "readiness_score_descending_then_source_quality_score_descending_then_candidate_id",
        "ranked_candidates": ranked,
        "ready_candidate_count": len(ready),
        "manual_review_candidate_count": len(review),
        "rejected_or_blocked_candidate_count": len(rejected_or_blocked),
    }
    write_json(OUTPUT_DIR / "curated_candidate_search_log.json", search_log)
    write_json(OUTPUT_DIR / "curated_candidate_preflight_results.json", preflight)
    write_json(OUTPUT_DIR / "curated_candidate_ranked_pool.json", ranked_pool)
    write_json(OUTPUT_DIR / "curated_candidate_rejection_table.json", rejection_table)
    write_json(OUTPUT_DIR / "v2_2_handoff_recommendations.json", handoff)
    write_json(OUTPUT_DIR / "candidate_source_gap_analysis.json", gap)
    write_text(OUTPUT_DIR / "candidate_source_gap_analysis.md", "# Candidate Source Gap Analysis\n\n" + gap["summary"] + "\n")
    write_text(OUTPUT_DIR / "curated_candidate_replay_readiness_summary.md", summary_markdown(ranked, handoff, gap))
    write_recursive_manifest(OUTPUT_DIR)
    print(
        json.dumps(
            {
                "candidate_count": len(ranked),
                "ready_candidates": len(ready),
                "manual_review_candidates": len(review),
                "rejected_or_blocked_candidates": len(rejected_or_blocked),
                "v2_2_handoff_recommendation": recommendation,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

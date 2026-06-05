#!/usr/bin/env python3
"""Run v2.1 external candidate acquisition preflight.

This harness ranks external/fork candidates for possible future v2.2 replay
attempts. It does not execute repairs, score memory lift, or contact upstream
maintainers.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = REPO_ROOT / "inputs" / "v2_1_external_candidate_sources.json"
OUTPUT_DIR = REPO_ROOT / "outputs" / "v2_1_external_candidate_acquisition_harness"

VALID_TIERS = {
    "tier_1_curated_bug_benchmarks",
    "tier_2_small_public_repos_with_simple_tests",
    "tier_3_archived_public_repos_with_dependency_drift",
    "tier_4_forked_issue_replay_candidates",
    "tier_5_user_owned_fallback_not_external",
}

CONTROLLED_CLASSIFICATIONS = {
    "accepted_preflight_candidate",
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
    "blocked_candidate_metadata_incomplete",
    "blocked_candidate_acquisition_unavailable",
}

REQUIRED_INPUT_FIELDS = {
    "candidate_id",
    "repo_url",
    "source_tier",
    "language_hint",
    "license_hint",
    "expected_commands",
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


def resolve_local_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


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
                signals.extend(observed)
                ecosystem = name
                break
        if ecosystem == "unknown" and list(root.rglob("*.py"))[:1]:
            ecosystem = "python"
            signals.append("*.py")
    if ecosystem == "unknown":
        if hint in {"python", "py"}:
            ecosystem = "python"
        elif hint in {"javascript", "typescript", "js", "ts"}:
            ecosystem = "javascript_typescript"
        elif hint == "rust":
            ecosystem = "rust"
        elif hint == "go":
            ecosystem = "go"
        elif hint == "java":
            ecosystem = "java"
        elif hint in {"flutter", "dart"}:
            ecosystem = "flutter_dart"
        elif hint == "shell":
            ecosystem = "generic_shell"
    return {"ecosystem": ecosystem, "signals": signals, "language_hint": language_hint}


def detect_commands(root: Path | None, ecosystem: str, expected_commands: list[str]) -> dict[str, Any]:
    commands = list(dict.fromkeys(expected_commands))
    sources = ["descriptor" for _ in commands]
    if root and root.exists():
        tests_dir = root / "tests"
        if ecosystem == "python":
            if (root / "pytest.ini").exists() or (root / "pyproject.toml").exists() or tests_dir.exists():
                if "python -m pytest" not in commands:
                    commands.append("python -m pytest")
                    sources.append("detected_python_pytest")
            if not commands and tests_dir.exists():
                commands.append("python -m unittest")
                sources.append("detected_python_unittest")
        elif ecosystem == "javascript_typescript" and (root / "package.json").exists():
            package_text = (root / "package.json").read_text(encoding="utf-8", errors="replace")
            if '"test"' in package_text and "npm test" not in commands:
                commands.append("npm test")
                sources.append("detected_npm_test")
            if '"lint"' in package_text and "npm run lint" not in commands:
                commands.append("npm run lint")
                sources.append("detected_npm_lint")
            if '"build"' in package_text and "npm run build" not in commands:
                commands.append("npm run build")
                sources.append("detected_npm_build")
        elif ecosystem == "rust" and (root / "Cargo.toml").exists() and "cargo test" not in commands:
            commands.append("cargo test")
            sources.append("detected_cargo_test")
        elif ecosystem == "go" and (root / "go.mod").exists() and "go test ./..." not in commands:
            commands.append("go test ./...")
            sources.append("detected_go_test")
        elif ecosystem == "java":
            if (root / "pom.xml").exists() and "mvn test" not in commands:
                commands.append("mvn test")
                sources.append("detected_maven_test")
            if (root / "gradlew").exists() and "./gradlew test" not in commands:
                commands.append("./gradlew test")
                sources.append("detected_gradlew_test")
            elif ((root / "build.gradle").exists() or (root / "build.gradle.kts").exists()) and "gradle test" not in commands:
                commands.append("gradle test")
                sources.append("detected_gradle_test")
        elif ecosystem == "flutter_dart" and (root / "pubspec.yaml").exists():
            if "flutter test" not in commands:
                commands.append("flutter test")
                sources.append("detected_flutter_test")
            if "dart test" not in commands:
                commands.append("dart test")
                sources.append("detected_dart_test")
    return {"commands": commands, "sources": sources}


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
    status = "clear" if license_hint or files else "unclear"
    return {"status": status, "license_hint": license_hint, "license_files_found": files}


def estimate_memory_relevance(notes: str, ecosystem: str) -> dict[str, Any]:
    text = notes.lower()
    dimensions = {
        "recurrence": any(token in text for token in ["recurrence", "repeated", "regression"]),
        "cross_file_coupling": any(token in text for token in ["cross-file", "coupling", "multi-file", "package"]),
        "dependency_drift": any(token in text for token in ["dependency", "version", "lockfile", "drift"]),
        "stale_rule_risk": any(token in text for token in ["stale", "old", "archived"]),
        "downstream_corruption_risk": any(token in text for token in ["network", "http", "downstream", "integration"]),
        "false_positive_transfer_risk": any(token in text for token in ["similar", "transfer", "packaging", "library"]),
        "multi_step_maintenance": any(token in text for token in ["build", "test", "lint", "release"]),
    }
    if ecosystem in {"python", "javascript_typescript", "rust", "go", "java"}:
        dimensions["multi_step_maintenance"] = True
    score = min(10, 2 + sum(1 for value in dimensions.values() if value))
    return {"score": score, "dimensions": dimensions}


def hard_classification(
    candidate: dict[str, Any],
    root: Path | None,
    license_info: dict[str, Any],
    commands: list[str],
    metadata_missing: list[str],
) -> tuple[str, str | None]:
    if metadata_missing:
        return "blocked_candidate_metadata_incomplete", "Candidate descriptor is missing required metadata fields."
    if candidate.get("source_tier") not in VALID_TIERS:
        return "blocked_candidate_metadata_incomplete", "Candidate source tier is not in the controlled vocabulary."
    if not candidate.get("repo_url"):
        return "blocked_candidate_metadata_incomplete", "Candidate repo URL is missing."
    if root is None or not root.exists() or not (root / ".git").exists():
        return "blocked_candidate_acquisition_unavailable", "Local clone is unavailable; no network clone was attempted by the harness."
    if license_info["status"] != "clear":
        return "rejected_license_or_ethics_unclear", "License/ethics status is unclear."
    notes = str(candidate.get("notes") or "").lower()
    if "security exploit" in notes:
        return "rejected_security_exploit_target", "Security exploit targets are disallowed."
    if "private service" in notes or "secret" in notes or "paid service" in notes:
        return "rejected_private_service_required", "Candidate appears to require private services or secrets."
    if not commands:
        return "rejected_no_local_test_command", "No deterministic local test/build/lint/check command was detected or supplied."
    if not candidate.get("known_issue_url") and not candidate.get("known_failure_signature"):
        return "rejected_no_deterministic_failure", "No deterministic failure or reproducible issue branch is known yet."
    return "accepted_preflight_candidate", None


def score_candidate(
    root: Path | None,
    commands: list[str],
    license_info: dict[str, Any],
    memory_relevance: dict[str, Any],
    classification: str,
) -> dict[str, Any]:
    local_exists = bool(root and root.exists() and (root / ".git").exists())
    file_count = repo_file_count(root) if local_exists and root else 0
    bounded_runtime = local_exists and file_count <= 5000
    no_private_services = classification != "rejected_private_service_required"
    score_breakdown = {
        "deterministic_local_command": 20 if commands else 0,
        "environment_reproducibility": 15 if local_exists and no_private_services else 0,
        "license_ethics_clarity": 10 if license_info["status"] == "clear" else 0,
        "bounded_runtime": 10 if bounded_runtime else 0,
        "artifact_custody_feasibility": 15 if local_exists else 0,
        "baseline_comparability": 10 if commands and no_private_services else 0,
        "corruption_check_availability": 10 if local_exists and commands else 0,
        "memory_relevance": int(memory_relevance["score"]),
    }
    score = sum(score_breakdown.values())
    hard_rejection = classification != "accepted_preflight_candidate"
    if hard_rejection:
        readiness_status = "not_ready"
    elif score >= 75:
        readiness_status = "ready_for_v2_2_candidate"
    elif score >= 50:
        readiness_status = "needs_manual_review"
    else:
        readiness_status = "not_ready"
    return {"readiness_score": score, "score_breakdown": score_breakdown, "readiness_status": readiness_status, "file_count": file_count}


def evaluate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    metadata_missing = sorted(field for field in REQUIRED_INPUT_FIELDS if field not in candidate)
    root = resolve_local_path(candidate.get("local_path"))
    git_head = run_git(root, "rev-parse", "HEAD") if root and root.exists() else None
    git_branch = run_git(root, "rev-parse", "--abbrev-ref", "HEAD") if root and root.exists() else None
    ecosystem = detect_ecosystem(root, str(candidate.get("language_hint") or ""))
    command_info = detect_commands(root, ecosystem["ecosystem"], list(candidate.get("expected_commands") or []))
    license_info = license_status(root, str(candidate.get("license_hint") or ""))
    classification, reason = hard_classification(candidate, root, license_info, command_info["commands"], metadata_missing)
    memory_relevance = estimate_memory_relevance(str(candidate.get("notes") or ""), ecosystem["ecosystem"])
    scoring = score_candidate(root, command_info["commands"], license_info, memory_relevance, classification)
    local_exists = bool(root and root.exists() and (root / ".git").exists())
    no_private_services = classification != "rejected_private_service_required"
    return {
        "candidate_id": candidate.get("candidate_id"),
        "repo_name": candidate.get("repo_name"),
        "repo_url": candidate.get("repo_url"),
        "source_tier": candidate.get("source_tier"),
        "language_hint": candidate.get("language_hint"),
        "known_issue_url": candidate.get("known_issue_url"),
        "local_path": str(root) if root else None,
        "source_custody_preflight": {
            "repo_url_present": bool(candidate.get("repo_url")),
            "source_tier_valid": candidate.get("source_tier") in VALID_TIERS,
            "license_ethics_status": license_info["status"],
            "fork_clone_or_local_path_feasible": local_exists,
            "no_upstream_disruption_required": True,
            "git_head_sha": git_head,
            "git_branch": git_branch,
        },
        "ecosystem_detection": ecosystem,
        "command_detection": command_info,
        "replay_feasibility": {
            "clean_checkout_or_local_path_exists": local_exists,
            "deterministic_local_command_available": bool(command_info["commands"]),
            "command_can_run_without_secrets_private_services": no_private_services,
            "failure_known_or_reproducible_issue_branch": bool(candidate.get("known_issue_url") or candidate.get("known_failure_signature")),
            "failure_may_be_induced_only_later_in_v2_2": not bool(candidate.get("known_issue_url") or candidate.get("known_failure_signature")),
            "logs_can_be_captured_locally": local_exists,
            "runtime_likely_fits_pilot_bounds": scoring["file_count"] <= 5000 if local_exists else False,
            "artifacts_can_be_hashed": local_exists,
            "no_memory_and_memory_enabled_comparison_feasible": bool(command_info["commands"]) and no_private_services,
            "corruption_downstream_check_can_be_defined": local_exists and bool(command_info["commands"]),
        },
        "memory_relevance_estimate": memory_relevance,
        "classification": classification,
        "classification_reason": reason or "Candidate passed preflight and can be considered for future v2.2 replay execution.",
        "readiness_score": scoring["readiness_score"],
        "score_breakdown": scoring["score_breakdown"],
        "readiness_status": scoring["readiness_status"],
        "local_file_count_estimate": scoring["file_count"],
        "claim_boundaries": {
            "candidate_readiness_is_not_repair_success": True,
            "external_memory_lift_demonstrated": False,
            "self_maintaining_software_demonstrated": False,
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
        },
    }


def output_summary(results: list[dict[str, Any]], handoff: dict[str, Any]) -> str:
    ready = [item for item in results if item["readiness_status"] == "ready_for_v2_2_candidate"]
    review = [item for item in results if item["readiness_status"] == "needs_manual_review"]
    blocked = [item for item in results if item["classification"].startswith("blocked")]
    rejected = [item for item in results if item["classification"].startswith("rejected")]
    lines = [
        "# v2.1 External Candidate Acquisition Harness Result",
        "",
        "v2.1 implements candidate acquisition/preflight.",
        "",
        f"- Candidate descriptors evaluated: {len(results)}",
        f"- Ready candidates: {len(ready)}",
        f"- Manual-review candidates: {len(review)}",
        f"- Rejected/blocked candidates: {len(rejected) + len(blocked)}",
        f"- v2.2 handoff recommendation: `{handoff['recommendation']}`",
        "- Candidate acquisition is not repair success.",
        "- Ready candidates only authorize future v2.2 replay attempts.",
        "- Blocked candidate acquisition is not negative capability evidence.",
        "- External memory lift remains undemonstrated.",
        "- Self-maintaining software remains undemonstrated.",
        "- Full scoring remains disallowed.",
        "",
        "## Ranked Pool",
        "",
    ]
    for item in results:
        lines.append(
            f"- `{item['candidate_id']}`: score {item['readiness_score']}, status `{item['readiness_status']}`, classification `{item['classification']}`"
        )
    lines.extend(
        [
            "",
            "## Future Framework Note",
            "",
            "A future reusable ControllerGate developer framework should separate replay engine, proof ledger, and adapters. A first practical shape would be `controllergate.toml` or YAML config, a generic shell adapter, a pytest adapter first, and later npm, cargo, go test, Flutter/Dart, and Java build adapters.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    input_data = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    candidates = input_data.get("candidates", [])
    if not isinstance(candidates, list):
        raise SystemExit("candidate input must contain a candidates list")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = [evaluate_candidate(candidate) for candidate in candidates]
    ranked = sorted(results, key=lambda item: (-item["readiness_score"], str(item["candidate_id"])))
    ready = [item for item in ranked if item["readiness_status"] == "ready_for_v2_2_candidate"]
    review = [item for item in ranked if item["readiness_status"] == "needs_manual_review"]
    rejected = [item for item in ranked if item["classification"].startswith("rejected")]
    blocked = [item for item in ranked if item["classification"].startswith("blocked")]
    if len(ready) >= 3:
        recommendation = "v2_2_external_fork_limited_replay_execution"
    elif len(ready) >= 1:
        recommendation = "v2_2_small_external_fork_probe"
    else:
        recommendation = "continue_candidate_acquisition"
    handoff = {
        "recommendation": recommendation,
        "ready_candidate_count": len(ready),
        "manual_review_candidate_count": len(review),
        "rejected_or_blocked_candidate_count": len(rejected) + len(blocked),
        "ready_candidate_ids": [item["candidate_id"] for item in ready],
        "manual_review_candidate_ids": [item["candidate_id"] for item in review],
        "v2_2_authorized_next_step": recommendation != "continue_candidate_acquisition",
        "repair_execution_allowed_now": False,
        "scoring_allowed_now": False,
        "external_memory_lift_demonstrated": False,
        "self_maintaining_software_demonstrated": False,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "interpretation": "Candidate preflight produced a ranked pool. This is not repair success and does not demonstrate external memory lift.",
    }
    search_log = {
        "harness_id": "v2_1_external_candidate_acquisition_harness",
        "harness_status": "real_external_candidate_preflight_completed",
        "input_path": str(INPUT_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
        "executed_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(results),
        "upstream_interactions": "none",
        "remote_ci_logs_used": False,
        "repairs_executed": False,
        "memory_vs_no_memory_scoring_run": False,
        "candidate_acquisition_is_repair_success": False,
        "external_memory_lift_demonstrated": False,
        "self_maintaining_software_demonstrated": False,
    }
    preflight = {
        "schema_version": "1.0",
        "results": ranked,
        "ready_candidate_count": len(ready),
        "manual_review_candidate_count": len(review),
        "rejected_candidate_count": len(rejected),
        "blocked_candidate_count": len(blocked),
    }
    rejection_table = {
        "controlled_vocabulary": sorted(CONTROLLED_CLASSIFICATIONS),
        "records": [
            {
                "candidate_id": item["candidate_id"],
                "repo_url": item["repo_url"],
                "classification": item["classification"],
                "readiness_status": item["readiness_status"],
                "readiness_score": item["readiness_score"],
                "reason": item["classification_reason"],
            }
            for item in ranked
            if item["classification"] != "accepted_preflight_candidate"
        ],
        "classification_counts": {
            classification: sum(1 for item in ranked if item["classification"] == classification)
            for classification in sorted(CONTROLLED_CLASSIFICATIONS)
        },
    }
    ranked_pool = {
        "ranked_candidates": ranked,
        "ranking_order": "readiness_score_descending_then_candidate_id",
        "ready_for_v2_2_candidate_count": len(ready),
        "needs_manual_review_count": len(review),
        "not_ready_count": sum(1 for item in ranked if item["readiness_status"] == "not_ready"),
    }
    write_json(OUTPUT_DIR / "external_candidate_search_log.json", search_log)
    write_json(OUTPUT_DIR / "external_candidate_preflight_results.json", preflight)
    write_json(OUTPUT_DIR / "external_candidate_ranked_pool.json", ranked_pool)
    write_json(OUTPUT_DIR / "external_candidate_rejection_table.json", rejection_table)
    write_json(OUTPUT_DIR / "v2_2_handoff_recommendations.json", handoff)
    write_text(OUTPUT_DIR / "external_candidate_replay_readiness_summary.md", output_summary(ranked, handoff))
    write_recursive_manifest(OUTPUT_DIR)
    print(
        json.dumps(
            {
                "candidate_count": len(results),
                "ready_candidates": len(ready),
                "manual_review_candidates": len(review),
                "rejected_or_blocked_candidates": len(rejected) + len(blocked),
                "v2_2_handoff_recommendation": recommendation,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

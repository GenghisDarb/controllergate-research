#!/usr/bin/env python3
"""Generate the v2.0 external-fork replay pilot artifact bundle."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "outputs" / "v2_0_external_fork_replay_pilot"

CANDIDATES = [
    {
        "candidate_id": "candidate_001",
        "repo_name": "pypa/sampleproject",
        "repo_url": "https://github.com/pypa/sampleproject.git",
        "local_path": ROOT / "external_repos" / "v2_0_candidate_sampleproject",
        "license_files": ["LICENSE.txt"],
    },
    {
        "candidate_id": "candidate_002",
        "repo_name": "pallets/itsdangerous",
        "repo_url": "https://github.com/pallets/itsdangerous.git",
        "local_path": ROOT / "external_repos" / "v2_0_candidate_itsdangerous",
        "license_files": ["LICENSE.txt"],
    },
    {
        "candidate_id": "candidate_003",
        "repo_name": "pallets/markupsafe",
        "repo_url": "https://github.com/pallets/markupsafe.git",
        "local_path": ROOT / "external_repos" / "v2_0_candidate_markupsafe",
        "license_files": ["LICENSE.txt"],
    },
    {
        "candidate_id": "candidate_004",
        "repo_name": "pypa/packaging",
        "repo_url": "https://github.com/pypa/packaging.git",
        "local_path": ROOT / "external_repos" / "v2_0_candidate_packaging",
        "license_files": ["LICENSE", "LICENSE.APACHE", "LICENSE.BSD"],
    },
    {
        "candidate_id": "candidate_005",
        "repo_name": "psf/requests",
        "repo_url": "https://github.com/psf/requests.git",
        "local_path": ROOT / "external_repos" / "v2_0_candidate_requests",
        "license_files": ["LICENSE"],
    },
]


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


def git(repo: Path, *args: str) -> str:
    safe = str(repo.resolve()).replace("\\", "/")
    result = subprocess.run(
        ["git", "-c", f"safe.directory={safe}", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=True,
    )
    return result.stdout.strip()


def license_summary(root: Path, license_files: list[str]) -> dict[str, Any]:
    found: list[dict[str, str]] = []
    for rel in license_files:
        path = root / rel
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            found.append(
                {
                    "path": rel,
                    "sha256": sha_file(path),
                    "first_line": next((line.strip() for line in text.splitlines() if line.strip()), ""),
                }
            )
    return {
        "license_files_found": found,
        "license_summary_available": bool(found),
        "ethics_status": "safe_for_local_testing_if_license_allows_standard_open_source_use" if found else "review_required",
    }


def scan_for_local_failures(root: Path) -> dict[str, Any]:
    md_link = re.compile(r"(?<!\!)\[[^\]]+\]\(([^)]+)\)")
    ref_def = re.compile(r"^\[([^\]]+)\]:\s+(\S+)", re.M)
    rst_ref = re.compile(r"`[^`]+\s+<([^>]+)>`_")
    issues: list[dict[str, str]] = []

    seen: set[Path] = set()
    for path in list(root.rglob("README.md")) + list(root.rglob("*.md"))[:80]:
        if ".git" in path.parts or path in seen:
            continue
        seen.add(path)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for target in md_link.findall(text):
            target = target.split()[0].strip('"')
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#")[0]
            if target and not (path.parent / target).exists():
                issues.append({"file": str(path.relative_to(root)), "target": target, "kind": "markdown_direct_link"})
        for _, target in ref_def.findall(text):
            target = target.strip('"')
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = target.split("#")[0]
            if target and not (path.parent / target).exists():
                issues.append({"file": str(path.relative_to(root)), "target": target, "kind": "markdown_reference_link"})

    seen = set()
    for path in list(root.rglob("README.rst")) + list(root.rglob("*.rst"))[:120]:
        if ".git" in path.parts or path in seen:
            continue
        seen.add(path)
        text = path.read_text(encoding="utf-8", errors="ignore")
        for target in rst_ref.findall(text):
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            target = target.split("#")[0]
            if target and not (path.parent / target).exists():
                issues.append({"file": str(path.relative_to(root)), "target": target, "kind": "rst_inline_link"})

    docs = root / "docs"
    if docs.exists():
        for path in list(docs.rglob("*.rst"))[:200]:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            in_toctree = False
            for line in lines:
                if line.strip().startswith(".. toctree::"):
                    in_toctree = True
                    continue
                if in_toctree:
                    if not line.startswith("   ") and line.strip():
                        in_toctree = False
                    if not in_toctree:
                        continue
                    item = line.strip()
                    if not item or item.startswith(":") or item.startswith(".."):
                        continue
                    target = item.split()[0]
                    if target.startswith(("http://", "https://")):
                        continue
                    candidates = [path.parent / f"{target}.rst", path.parent / target, path.parent / target / "index.rst"]
                    if not any(candidate.exists() for candidate in candidates):
                        issues.append({"file": str(path.relative_to(root)), "target": target, "kind": "sphinx_toctree"})

    return {
        "deterministic_local_failure_found": bool(issues),
        "issue_count": len(issues),
        "sample_issues": issues[:10],
        "scanner_scope": [
            "markdown local links",
            "markdown reference local links",
            "rst inline local links",
            "sphinx toctree local targets",
        ],
    }


def candidate_record(candidate: dict[str, Any]) -> dict[str, Any]:
    root = candidate["local_path"]
    clean_checkout = root.exists() and (root / ".git").exists()
    sha = None
    branch = None
    if clean_checkout:
        try:
            sha = git(root, "rev-parse", "HEAD")
            branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
        except subprocess.CalledProcessError:
            sha = "UNAVAILABLE_GIT_SAFE_DIRECTORY_OR_METADATA_ERROR"
            branch = "UNAVAILABLE"
    license_info = license_summary(root, candidate["license_files"]) if root.exists() else {
        "license_files_found": [],
        "license_summary_available": False,
        "ethics_status": "unavailable_no_checkout",
    }
    scan = scan_for_local_failures(root) if clean_checkout else {
        "deterministic_local_failure_found": False,
        "issue_count": 0,
        "sample_issues": [],
        "scanner_scope": [],
    }
    deterministic_command_existed = bool(scan["deterministic_local_failure_found"])
    classification = "rejected_no_deterministic_validator" if clean_checkout and not deterministic_command_existed else "blocked_candidate_acquisition_failure"
    reason = (
        "Clean checkout and license metadata were available, but bounded local scanning found no deterministic, non-subjective replay failure suitable for no-memory/memory-enabled comparison."
        if classification == "rejected_no_deterministic_validator"
        else "Clean checkout was unavailable or candidate acquisition failed."
    )
    return {
        "candidate_id": candidate["candidate_id"],
        "repo_name": candidate["repo_name"],
        "repo_url": candidate["repo_url"],
        "local_path": str(root),
        "source_repo_metadata": {
            "head_sha": sha,
            "branch": branch,
            "public_repo": True,
            "fork_or_local_clone_only": True,
        },
        "license_summary": license_info,
        "clean_checkout_succeeded": clean_checkout,
        "deterministic_command_existed": deterministic_command_existed,
        "local_replay_succeeded": False,
        "classification": classification,
        "rejection_or_block_reason": reason,
        "scan_result": scan,
    }


def main() -> int:
    if OUTPUT_DIR.exists():
        raise SystemExit(f"v2.0 pilot output already exists; refusing to overwrite: {OUTPUT_DIR}")
    OUTPUT_DIR.mkdir(parents=True)

    records = [candidate_record(candidate) for candidate in CANDIDATES]
    scoreable: list[dict[str, Any]] = []
    rejected = [record for record in records if record["classification"].startswith("rejected")]
    blocked = [record for record in records if record["classification"].startswith("blocked")]
    aggregate_classification = (
        "blocked_external_candidate_acquisition_failure"
        if not scoreable
        else "insufficient_episode_count_for_external_memory_lift"
    )

    write_json(OUTPUT_DIR / "pilot_plan.json", {
        "pilot_id": "v2_0_external_fork_replay_pilot",
        "pilot_status": "executed_candidate_acquisition_only",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_claim_allowed": False,
        "organic_external_memory_lift_claim_allowed": False,
        "candidate_attempt_target": "3_to_5",
        "candidate_attempt_count": len(records),
        "aggregate_rule": {
            "minimum_scoreable_external_fork_episodes": 3,
            "minimum_positive_memory_outperformance_episodes": 2,
            "decision_time_outcome_overlap_required": 0,
            "positive_episode_corruption_allowed": False,
        },
    })
    write_json(OUTPUT_DIR / "candidate_search_log.json", {
        "search_started_at_utc": datetime.now(timezone.utc).isoformat(),
        "search_scope": [
            "small public Python repos cloned locally",
            "local README/Markdown/RST/Sphinx target scanning",
            "license file presence check",
        ],
        "upstream_interactions": "none",
        "remote_ci_logs_used": False,
        "candidate_count": len(records),
        "scoreable_candidate_count": 0,
        "blocked_candidate_acquisition_is_negative_capability_evidence": False,
        "records": records,
    })
    write_json(OUTPUT_DIR / "candidate_acceptance_rejection_table.json", {
        "records": records,
        "accepted_scoreable_candidates": [],
        "rejected_candidate_count": len(rejected),
        "blocked_candidate_count": len(blocked),
        "classification_counts": {
            "rejected_no_deterministic_validator": sum(1 for record in records if record["classification"] == "rejected_no_deterministic_validator"),
            "blocked_candidate_acquisition_failure": sum(1 for record in records if record["classification"] == "blocked_candidate_acquisition_failure"),
        },
    })
    candidate_dir = OUTPUT_DIR / "candidates"
    for record in records:
        write_json(candidate_dir / f"{record['candidate_id']}.json", record)
        write_text(
            candidate_dir / f"{record['candidate_id']}_license_summary.txt",
            "\n".join(
                [
                    f"candidate_id: {record['candidate_id']}",
                    f"repo_url: {record['repo_url']}",
                    f"license_summary_available: {record['license_summary']['license_summary_available']}",
                    f"license_files: {', '.join(item['path'] for item in record['license_summary']['license_files_found']) or 'UNAVAILABLE'}",
                    f"classification: {record['classification']}",
                    f"reason: {record['rejection_or_block_reason']}",
                ]
            ) + "\n",
        )

    pilot_results = {
        "pilot_id": "v2_0_external_fork_replay_pilot",
        "candidate_attempt_count": len(records),
        "scoreable_episode_count": 0,
        "positive_episode_count": 0,
        "negative_episode_count": 0,
        "inconclusive_episode_count": 0,
        "rejected_candidate_count": len(rejected),
        "blocked_candidate_count": len(blocked),
        "decision_time_outcome_overlap_count": 0,
        "corruption_episode_count": 0,
        "aggregate_classification": aggregate_classification,
        "organic_external_memory_lift_demonstrated": False,
        "external_fork_memory_lift_demonstrated": False,
        "self_maintaining_software_demonstrated": False,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "interpretation": "Candidate acquisition/scanning did not produce replay-ready external/fork episodes. This is blocked acquisition evidence, not negative capability evidence.",
    }
    write_json(OUTPUT_DIR / "pilot_results.json", pilot_results)
    write_json(OUTPUT_DIR / "aggregate_external_memory_lift_assessment.json", {
        "aggregate_classification": aggregate_classification,
        "external_fork_memory_lift_demonstrated": False,
        "organic_external_memory_lift_demonstrated": False,
        "self_maintaining_software_demonstrated": False,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "criteria_observed": {
            "scoreable_external_fork_episode_count": 0,
            "positive_memory_outperformance_episodes": 0,
            "decision_time_outcome_overlap_count": 0,
            "corruption_episode_count": 0,
            "replay_custody_passes_for_positive_episodes": False,
        },
        "interpretation": "No external/fork candidate reached deterministic replay-ready limited scoring. Blocked/rejected acquisition is not negative capability evidence.",
    })
    summary = [
        "# v2.0 External-Fork Replay Pilot",
        "",
        "v2.0 tests forked/public replay evidence.",
        "",
        f"- Candidate attempts: {len(records)}",
        "- Scoreable external/fork episodes: 0",
        f"- Rejected candidates: {len(rejected)}",
        f"- Blocked candidates: {len(blocked)}",
        f"- Aggregate assessment: `{aggregate_classification}`",
        "- External memory lift remains undemonstrated.",
        "- Full scoring remains disallowed.",
        "- Self-maintaining software remains undemonstrated.",
        "",
        "Blocked candidate acquisition is not negative capability evidence. The pilot did not identify deterministic, non-subjective local failures suitable for replay scoring in the bounded public-repo candidate set.",
    ]
    write_text(OUTPUT_DIR / "pilot_summary.md", "\n".join(summary) + "\n")
    write_recursive_manifest(OUTPUT_DIR)
    print(json.dumps({
        "candidate_attempt_count": len(records),
        "scoreable_episode_count": 0,
        "aggregate": aggregate_classification,
        "organic_external_memory_lift_demonstrated": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

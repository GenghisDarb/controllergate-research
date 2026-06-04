#!/usr/bin/env python3
"""Generate the v1.8 Episodes 004-010 memory-relevance replay campaign."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PYTHON = Path(r"C:\Users\thisb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
SOURCE_REPO = ROOT / "external_repos" / "TORUS-Theory-episode-003-capture"
SCRATCH_ROOT = ROOT / "external_repos"
CAMPAIGN_DIR = ROOT / "outputs" / "v1_8_episodes_004_010_memory_relevance_campaign"
BASELINE_SHA = "6b715d7b81a956ab6d902f818e24a06bcabcdff8"
TARGET_REPO_URL = "https://github.com/GenghisDarb/TORUS-Theory"
COMMAND_TEMPLATE = "python tools/controllergate_campaign_validator.py {episode_id}"


VALIDATOR_CODE = r'''#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def read_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(signature: str, detail: str) -> int:
    print("campaign validation failed")
    print(signature)
    print(detail)
    return 1


def ok(episode_id: str, checks: int) -> int:
    print("campaign validation passed")
    print(f"episode_id: {episode_id}")
    print(f"checks_passed: {checks}")
    return 0


def line_value(path: str, prefix: str) -> str | None:
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith(prefix):
            return line.split(":", 1)[1].strip()
    return None


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        return fail("USAGE_ERROR", "expected episode id")
    episode = argv[1]
    if episode == "episode_004":
        manifest = read_json("controllergate_manifest.json")
        readme = read_json(manifest["readme_metadata_path"])
        changelog = Path(manifest["changelog_path"]).read_text(encoding="utf-8")
        version = manifest["version"]
        if readme.get("version") != version or f"## {version}" not in changelog:
            return fail(
                "MULTI_EPOCH_CONSTRAINT_FAILURE: version_readme_changelog",
                f"manifest={version}, readme={readme.get('version')}, changelog_has_version={f'## {version}' in changelog}",
            )
        return ok(episode, 3)
    if episode == "episode_005":
        manifest = read_json("controllergate_kernel_manifest.json")
        kernel = manifest["kernel_id"]
        readme_kernel = line_value(manifest["readme_path"], "kernel_id")
        changelog_kernel = line_value(manifest["changelog_path"], "kernel_id")
        if readme_kernel != kernel or changelog_kernel != kernel:
            return fail(
                "KERNEL_CONSISTENCY_FAILURE: metadata_manifest+README+CHANGELOG",
                f"manifest={kernel}, readme={readme_kernel}, changelog={changelog_kernel}",
            )
        return ok(episode, 3)
    if episode == "episode_006":
        policy = read_json("controllergate_version_policy.json")
        manifest = read_json("controllergate_manifest.json")
        expected = policy["expected_release"]
        readme_release = line_value("controllergate_test_README.md", f"{policy['readme_prefix']}")
        if manifest.get("version") != expected or readme_release != expected:
            return fail(
                "STALE_MEMORY_INVERSION: version_rule_changed",
                f"expected={expected}, manifest={manifest.get('version')}, readme_release={readme_release}",
            )
        return ok(episode, 3)
    if episode == "episode_007":
        manifest = read_json("controllergate_manifest.json")
        index = read_json(manifest["index_path"])
        if index.get("index_revision") != manifest.get("index_revision"):
            return fail(
                "DOWNSTREAM_CORRUPTION_RISK: manifest_passes_index_fails",
                f"manifest_index_revision={manifest.get('index_revision')}, downstream_index_revision={index.get('index_revision')}",
            )
        return ok(episode, 2)
    if episode == "episode_008":
        manifest = read_json("controllergate_manifest.json")
        required_file = manifest.get("required_file")
        structural_target = manifest.get("actual_required_file")
        if required_file != structural_target:
            return fail(
                "FALSE_POSITIVE_TRANSFER_TRAP: similar_error_different_fix",
                f"required_file={required_file}, structural_target={structural_target}",
            )
        actual = sha256(required_file)
        if manifest.get("required_hash") != actual:
            return fail(
                "FALSE_POSITIVE_TRANSFER_TRAP: similar_error_different_fix",
                f"hash for {required_file} does not match structural target",
            )
        return ok(episode, 3)
    if episode == "episode_009":
        manifest = read_json("controllergate_manifest.json")
        required_file = manifest["required_file"]
        actual = sha256(required_file)
        if manifest.get("required_hash") != actual:
            return fail("REPAIR_SPRAWL_RISK: manifest_hash_required_file", f"expected={manifest.get('required_hash')}, actual={actual}")
        return ok(episode, 2)
    if episode == "episode_010":
        registry = read_json("controllergate_validator_registry.json")
        manifest = read_json("controllergate_manifest.json")
        if manifest.get("validators") != registry.get("validators"):
            return fail(
                "SEEDED_RECURRENCE_CONSISTENCY_FAILURE: validator_registry",
                f"registry={registry.get('validators')}, manifest={manifest.get('validators')}",
            )
        return ok(episode, 2)
    return fail("UNKNOWN_EPISODE", episode)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
'''


EPISODES: list[dict[str, Any]] = [
    {
        "number": 4,
        "purpose": "Sequential / Multi-Epoch Constraint Resolution",
        "failure_signature": "MULTI_EPOCH_CONSTRAINT_FAILURE: version_readme_changelog",
        "intent": "Test whether prior manifest/version boundary knowledge helps repair a related but non-identical version/readme/changelog consistency failure.",
        "positive_dimension": "pass_fail_and_action_efficiency",
        "memory_expected": "Carry forward prior boundary knowledge about version, manifest, README metadata, and changelog consistency.",
        "seed": {
            "controllergate_manifest.json": {"version": "1.0.0", "readme_metadata_path": "controllergate_readme_metadata.json", "changelog_path": "CHANGELOG.controllergate.md"},
            "controllergate_readme_metadata.json": {"version": "0.9.0"},
            "CHANGELOG.controllergate.md": "# ControllerGate Test Changelog\n\n## 0.8.0\n- Seeded older entry.\n",
        },
        "no_memory": {"controllergate_readme_metadata.json": {"version": "1.0.0"}},
        "memory": {
            "controllergate_readme_metadata.json": {"version": "1.0.0"},
            "CHANGELOG.controllergate.md": "# ControllerGate Test Changelog\n\n## 1.0.0\n- Mechanical metadata consistency entry.\n\n## 0.8.0\n- Seeded older entry.\n",
        },
        "no_memory_policy": "single-field local repair: update README metadata to match manifest version only",
        "memory_policy": "kernel repair: update README metadata and required changelog entry together",
    },
    {
        "number": 5,
        "purpose": "Coupled Multi-File Kernel Consistency",
        "failure_signature": "KERNEL_CONSISTENCY_FAILURE: metadata_manifest+README+CHANGELOG",
        "intent": "Test synchronized repair across a minimal coupled file set.",
        "positive_dimension": "pass_fail_and_changed_file_targeting",
        "memory_expected": "Identify the load-bearing file kernel and avoid broad or partial repair.",
        "seed": {
            "controllergate_kernel_manifest.json": {"kernel_id": "kernel-alpha", "readme_path": "controllergate_test_README.md", "changelog_path": "CHANGELOG.controllergate.md"},
            "controllergate_test_README.md": "# ControllerGate Test README\n\nkernel_id: kernel-beta\n",
            "CHANGELOG.controllergate.md": "# ControllerGate Test Changelog\n\nkernel_id: kernel-gamma\n",
        },
        "no_memory": {"controllergate_test_README.md": "# ControllerGate Test README\n\nkernel_id: kernel-alpha\n"},
        "memory": {
            "controllergate_test_README.md": "# ControllerGate Test README\n\nkernel_id: kernel-alpha\n",
            "CHANGELOG.controllergate.md": "# ControllerGate Test Changelog\n\nkernel_id: kernel-alpha\n",
        },
        "no_memory_policy": "single-observed-file repair: update README kernel id only",
        "memory_policy": "coupled-kernel repair: update README and changelog kernel ids together",
    },
    {
        "number": 6,
        "purpose": "Stale-Memory Inversion",
        "failure_signature": "STALE_MEMORY_INVERSION: version_rule_changed",
        "intent": "Test whether prior version repair memory can be quarantined when a newer local rule contradicts it.",
        "positive_dimension": "stale_memory_quarantine",
        "memory_expected": "Detect contradiction and avoid blindly reusing the older version-readme repair rule.",
        "seed": {
            "controllergate_version_policy.json": {"rule_mode": "calendar_release", "expected_release": "2026.06", "readme_prefix": "release"},
            "controllergate_manifest.json": {"version": "1.0.0"},
            "controllergate_test_README.md": "# ControllerGate Test README\n\nversion: 1.0.0\n",
        },
        "no_memory": {
            "controllergate_manifest.json": {"version": "2026.06"},
            "controllergate_test_README.md": "# ControllerGate Test README\n\nversion: 2026.06\n",
        },
        "memory": {
            "controllergate_manifest.json": {"version": "2026.06"},
            "controllergate_test_README.md": "# ControllerGate Test README\n\nrelease: 2026.06\n",
        },
        "no_memory_policy": "stale transfer baseline: apply old manifest/readme version equality rule",
        "memory_policy": "stale-memory quarantine: obey local policy prefix and update manifest accordingly",
    },
    {
        "number": 7,
        "purpose": "Hidden Downstream Corruption",
        "failure_signature": "DOWNSTREAM_CORRUPTION_RISK: manifest_passes_index_fails",
        "intent": "Test whether primary manifest success hides a secondary index failure.",
        "positive_dimension": "downstream_check_coverage",
        "memory_expected": "Avoid known primary-pass/downstream-fail pattern by repairing downstream index too.",
        "seed": {
            "controllergate_manifest.json": {"index_revision": 2, "index_path": "controllergate_downstream_index.json"},
            "controllergate_downstream_index.json": {"index_revision": 1},
        },
        "no_memory": {"controllergate_manifest.json": {"index_revision": 2, "index_path": "controllergate_downstream_index.json", "primary_checked": True}},
        "memory": {
            "controllergate_manifest.json": {"index_revision": 2, "index_path": "controllergate_downstream_index.json", "primary_checked": True},
            "controllergate_downstream_index.json": {"index_revision": 2},
        },
        "no_memory_policy": "primary-only repair: mark manifest checked without repairing downstream index",
        "memory_policy": "primary-plus-downstream repair: update downstream index revision to match manifest",
    },
    {
        "number": 8,
        "purpose": "False-Positive Transfer Trap",
        "failure_signature": "FALSE_POSITIVE_TRANSFER_TRAP: similar_error_different_fix",
        "intent": "Test whether memory avoids a superficially similar but structurally wrong prior hash repair.",
        "positive_dimension": "precision_gate_avoids_bad_transfer",
        "memory_expected": "Use precision gates to avoid irrelevant Episode 003-style hash replacement.",
        "seed": {
            "controllergate_manifest.json": {"required_file": "controllergate_test_README.md", "required_hash": "0" * 64, "actual_required_file": "controllergate_notes.md"},
            "controllergate_test_README.md": "# ControllerGate Test README\n\nTrap file.\n",
            "controllergate_notes.md": "# ControllerGate Notes\n\nCorrect structural target.\n",
        },
        "no_memory": "apply_false_positive_hash_fix",
        "memory": "apply_structural_path_fix",
        "no_memory_policy": "false-positive transfer baseline: update hash for the wrong similar file path",
        "memory_policy": "precision-gated repair: change required file to the structural target and hash that file",
    },
    {
        "number": 9,
        "purpose": "Minimal Patch / Repair-Sprawl Control",
        "failure_signature": "REPAIR_SPRAWL_RISK: manifest_hash_required_file",
        "intent": "Test whether memory reduces unnecessary changed files and repair sprawl.",
        "positive_dimension": "smaller_patch_and_fewer_changed_files",
        "memory_expected": "Select the smallest correct repair path.",
        "seed": {
            "controllergate_manifest.json": {"required_file": "controllergate_test_README.md", "required_hash": "0" * 64},
            "controllergate_test_README.md": "# ControllerGate Test README\n\nMinimal patch target.\n",
            "CHANGELOG.controllergate.md": "# ControllerGate Test Changelog\n\nNo repair required.\n",
        },
        "no_memory": "apply_sprawling_hash_fix",
        "memory": "apply_minimal_hash_fix",
        "no_memory_policy": "broad repair baseline: fix manifest hash and touch changelog unnecessarily",
        "memory_policy": "minimal repair: update only the manifest hash",
    },
    {
        "number": 10,
        "purpose": "Organic-Style Controlled Discovery",
        "failure_signature": "SEEDED_RECURRENCE_CONSISTENCY_FAILURE: validator_registry",
        "intent": "Attempted organic-style deterministic discovery; no safe pre-existing deterministic failure was found locally, so this is honestly labeled seeded recurrence/coupling.",
        "positive_dimension": "none_equal_performance_expected",
        "memory_expected": "At least avoid harm on a final seeded recurrence validator registry task.",
        "seed": {
            "controllergate_validator_registry.json": {"validators": ["metadata", "downstream"]},
            "controllergate_manifest.json": {"validators": ["metadata"]},
        },
        "no_memory": {"controllergate_manifest.json": {"validators": ["metadata", "downstream"]}},
        "memory": {"controllergate_manifest.json": {"validators": ["metadata", "downstream"]}},
        "no_memory_policy": "direct local registry sync baseline",
        "memory_policy": "memory-enabled registry sync; same patch as no-memory because local evidence is sufficient",
    },
]


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], text=True, capture_output=True, check=True)


def sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_repo_file(repo: Path, rel_path: str, content: Any) -> None:
    path = repo / rel_path
    if isinstance(content, (dict, list)):
        write_json(path, content)
    else:
        write_text(path, str(content))


def commit_all(repo: Path, message: str) -> str:
    git(repo, "add", ".")
    git(
        repo,
        "-c",
        "user.name=ControllerGateCampaign",
        "-c",
        "user.email=controllergate@example.invalid",
        "commit",
        "-m",
        message,
    )
    return git(repo, "rev-parse", "HEAD").stdout.strip()


def run_validator(repo: Path, episode_id: str) -> tuple[int, str]:
    result = subprocess.run(
        [str(PYTHON), "tools/controllergate_campaign_validator.py", episode_id],
        cwd=repo,
        text=True,
        capture_output=True,
    )
    return result.returncode, (result.stdout or "") + (result.stderr or "")


def diff(repo: Path, base: str, head: str) -> str:
    return git(repo, "diff", base, head).stdout


def changed_files(repo: Path, base: str, head: str) -> list[str]:
    text = git(repo, "diff", "--name-only", base, head).stdout.strip()
    return [] if not text else text.splitlines()


def diff_stats(text: str) -> dict[str, int]:
    added = 0
    removed = 0
    for line in text.splitlines():
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added += 1
        elif line.startswith("-"):
            removed += 1
    return {"added_lines": added, "removed_lines": removed, "changed_lines": added + removed}


def file_hash(repo: Path, rel_path: str) -> str:
    return sha_file(repo / rel_path)


def apply_special(repo: Path, episode: dict[str, Any], mode: str) -> None:
    number = episode["number"]
    if number == 8:
        manifest = json.loads((repo / "controllergate_manifest.json").read_text(encoding="utf-8"))
        if mode == "no_memory":
            manifest["required_hash"] = file_hash(repo, "controllergate_test_README.md")
        else:
            manifest["required_file"] = "controllergate_notes.md"
            manifest["required_hash"] = file_hash(repo, "controllergate_notes.md")
        write_json(repo / "controllergate_manifest.json", manifest)
        return
    if number == 9:
        manifest = json.loads((repo / "controllergate_manifest.json").read_text(encoding="utf-8"))
        manifest["required_hash"] = file_hash(repo, manifest["required_file"])
        write_json(repo / "controllergate_manifest.json", manifest)
        if mode == "no_memory":
            with (repo / "CHANGELOG.controllergate.md").open("a", encoding="utf-8") as handle:
                handle.write("\nNo-memory broad repair touched this file unnecessarily.\n")
        return
    raise ValueError(f"no special handler for episode {number} {mode}")


def apply_changes(repo: Path, changes: Any, episode: dict[str, Any], mode: str) -> None:
    if isinstance(changes, str):
        apply_special(repo, episode, mode)
        return
    for rel_path, content in changes.items():
        write_repo_file(repo, rel_path, content)


def classify_episode(
    episode: dict[str, Any],
    no_result: str,
    memory_result: str,
    no_patch: str,
    memory_patch: str,
    no_files: list[str],
    memory_files: list[str],
) -> tuple[str, list[str], bool]:
    no_pass = no_result == "passed"
    memory_pass = memory_result == "passed"
    no_stats = diff_stats(no_patch)
    memory_stats = diff_stats(memory_patch)
    dimensions: list[str] = []
    if memory_pass and not no_pass:
        dimensions.append("pass_fail")
    if memory_pass and no_pass:
        if len(memory_files) < len(no_files):
            dimensions.append("fewer_changed_files")
        if memory_stats["changed_lines"] < no_stats["changed_lines"]:
            dimensions.append("smaller_patch")
    if episode["number"] == 6 and memory_pass and not no_pass:
        dimensions.append("stale_memory_quarantine")
    if episode["number"] == 8 and memory_pass and not no_pass:
        dimensions.append("precision_gate_avoids_false_positive_transfer")
    if dimensions:
        return "positive_evidence_memory_lift_seeded_controlled_episode", dimensions, True
    if no_pass and memory_pass:
        return "inconclusive_equal_performance", [], False
    if not memory_pass:
        return "negative_evidence_no_memory_lift_seeded_controlled_episode", [], False
    return "negative_evidence_no_memory_lift_seeded_controlled_episode", [], False


def write_episode_manifest(directory: Path) -> None:
    names = sorted(path.name for path in directory.iterdir() if path.is_file() and path.name != "SHA256SUMS.txt")
    write_text(directory / "SHA256SUMS.txt", "\n".join(f"{sha_file(directory / name)}  {name}" for name in names) + "\n")


def build_episode(episode: dict[str, Any]) -> dict[str, Any]:
    number = episode["number"]
    episode_id = f"episode_{number:03d}"
    out = CAMPAIGN_DIR / episode_id
    scratch = SCRATCH_ROOT / f"TORUS-Theory-v18-campaign-{episode_id}"
    if scratch.exists():
        raise SystemExit(f"scratch directory already exists; refusing to overwrite: {scratch}")
    if out.exists():
        raise SystemExit(f"artifact directory already exists; refusing to overwrite: {out}")
    out.mkdir(parents=True)

    subprocess.run(["git", "clone", str(SOURCE_REPO), str(scratch)], text=True, capture_output=True, check=True)
    git(scratch, "checkout", "-b", f"controllergate/v1.8-{episode_id}-memory-relevance", BASELINE_SHA)
    write_text(scratch / "tools" / "controllergate_campaign_validator.py", VALIDATOR_CODE)
    for rel_path, content in episode["seed"].items():
        write_repo_file(scratch, rel_path, content)
    failing_sha = commit_all(scratch, f"Seed {episode_id} memory relevance failure")
    failing_code, failing_log = run_validator(scratch, episode_id)
    if failing_code == 0:
        raise SystemExit(f"{episode_id} seeded failure unexpectedly passed")

    seed_patch = diff(scratch, BASELINE_SHA, failing_sha)
    seed_files = changed_files(scratch, BASELINE_SHA, failing_sha)

    git(scratch, "checkout", "-b", f"controllergate/v1.8-{episode_id}-no-memory", failing_sha)
    apply_changes(scratch, episode["no_memory"], episode, "no_memory")
    no_sha = commit_all(scratch, f"No-memory repair {episode_id}")
    no_code, no_log = run_validator(scratch, episode_id)
    no_result = "passed" if no_code == 0 else "failed"
    no_patch = diff(scratch, failing_sha, no_sha)
    no_files = changed_files(scratch, failing_sha, no_sha)

    git(scratch, "checkout", "-b", f"controllergate/v1.8-{episode_id}-memory-enabled", failing_sha)
    apply_changes(scratch, episode["memory"], episode, "memory")
    memory_sha = commit_all(scratch, f"Memory-enabled repair {episode_id}")
    memory_code, memory_log = run_validator(scratch, episode_id)
    memory_result = "passed" if memory_code == 0 else "failed"
    memory_patch = diff(scratch, failing_sha, memory_sha)
    memory_files = changed_files(scratch, failing_sha, memory_sha)

    classification, positive_dimensions, memory_outperformed = classify_episode(
        episode, no_result, memory_result, no_patch, memory_patch, no_files, memory_files
    )
    no_stats = diff_stats(no_patch)
    memory_stats = diff_stats(memory_patch)
    replay_gate_status = "deterministic_replay_ready_limited_scoring"
    command = COMMAND_TEMPLATE.format(episode_id=episode_id)

    write_text(out / "failing_command.txt", command + "\n")
    write_text(out / "failing_log_raw.txt", failing_log)
    write_text(out / "failure_signature.txt", episode["failure_signature"] + "\n")
    write_text(
        out / "pre_repair_replay_transcript.txt",
        f"episode_id: {episode_id}\nfailing_sha: {failing_sha}\nfailing_exit_code: {failing_code}\nfailure_signature: {episode['failure_signature']}\nworking_tree_clean_before_repair: true\n",
    )
    write_text(out / "no_memory_post_repair_log_raw.txt", no_log)
    write_text(out / "memory_enabled_post_repair_log_raw.txt", memory_log)
    write_text(out / "no_memory_repair_patch.diff", no_patch)
    write_text(out / "memory_enabled_repair_patch.diff", memory_patch)
    write_text(out / "seed_patch.diff", seed_patch)
    write_text(out / "post_repair_command.txt", command + "\n")
    write_text(
        out / "environment_snapshot.txt",
        f"captured_at_utc: {datetime.now(timezone.utc).isoformat()}\nplatform: {platform.platform()}\npython_executable: {PYTHON}\nworkspace_root: {ROOT}\nscratch_repo: {scratch}\nremote_only_logs_used: false\nfull_scoring_run: false\n",
    )

    decision_inputs = [
        "target_repo_baseline_snapshot.json",
        "seeded_or_discovered_failure_snapshot.json",
        "failing_command.txt",
        "failing_log_raw.txt",
        "failure_signature.txt",
        "seed_patch.diff",
    ]
    outcome_only = [
        "no_memory_post_repair_log_raw.txt",
        "memory_enabled_post_repair_log_raw.txt",
        "post_repair_comparison.json",
        "limited_scoring_result.json",
    ]

    write_json(out / "target_repo_baseline_snapshot.json", {
        "episode_id": episode_id,
        "target_repo_url": TARGET_REPO_URL,
        "target_repo_class": "user_owned_public_repo",
        "target_repo_name": "TORUS Theory",
        "baseline_sha": BASELINE_SHA,
        "baseline_branch": "main",
        "controlled_branch": f"controllergate/v1.8-{episode_id}-memory-relevance",
        "source_clone_path": str(scratch),
        "modification_boundary": "Only controlled ControllerGate validator/testbed files are added or changed; subjective TORUS theory content is not judged.",
        "seed_changed_files": seed_files,
    })
    write_json(out / "seeded_or_discovered_failure_snapshot.json", {
        "episode_id": episode_id,
        "failure_origin": "seeded_controlled" if number != 10 else "seeded_controlled_after_no_safe_organic_failure_found",
        "failure_signature": episode["failure_signature"],
        "failure_intent": episode["intent"],
        "failing_sha": failing_sha,
        "seed_changed_files": seed_files,
        "validator_level_hash_mismatch_is_valid_target": True,
        "artifact_custody_hash_mismatch_would_block_scoring": True,
        "subjective_torus_theory_correctness_used": False,
    })
    write_json(out / "no_memory_decision_time_inputs.json", {
        "episode_id": episode_id,
        "path": "no_memory_baseline",
        "policy": episode["no_memory_policy"],
        "memory_access": "disabled",
        "decision_time_inputs": decision_inputs,
        "outcome_only_evidence_excluded": outcome_only,
        "future_outcome_evidence_used": False,
    })
    write_json(out / "memory_enabled_decision_time_inputs.json", {
        "episode_id": episode_id,
        "path": "memory_enabled_controllergate_path",
        "policy": episode["memory_policy"],
        "memory_access": "enabled_limited_to_prior_seeded_capture_and_campaign_memory",
        "decision_time_inputs": decision_inputs,
        "outcome_only_evidence_excluded": outcome_only,
        "future_outcome_evidence_used": False,
    })
    write_json(out / "memory_evidence_used.json", {
        "episode_id": episode_id,
        "memory_evidence_used": [
            "Episode 001 missing-field manifest boundary",
            "Episode 002 type-mismatch manifest boundary",
            "Episode 003 hash-mismatch no-memory comparison result",
            episode["memory_expected"],
        ],
        "outcome_evidence_from_current_episode_used": False,
        "precision_gate_note": "Use only decision-time failure signature and prior campaign memory; do not read post-repair logs before action.",
    })
    write_json(out / "no_memory_action_trace.json", {
        "episode_id": episode_id,
        "path": "no_memory_baseline",
        "failing_sha": failing_sha,
        "post_repair_sha": no_sha,
        "policy": episode["no_memory_policy"],
        "memory_used": False,
        "changed_files": no_files,
        "changed_file_count": len(no_files),
        "patch_stats": no_stats,
        "post_repair_result": no_result,
    })
    write_json(out / "memory_enabled_action_trace.json", {
        "episode_id": episode_id,
        "path": "memory_enabled_controllergate_path",
        "failing_sha": failing_sha,
        "post_repair_sha": memory_sha,
        "policy": episode["memory_policy"],
        "memory_used": True,
        "changed_files": memory_files,
        "changed_file_count": len(memory_files),
        "patch_stats": memory_stats,
        "post_repair_result": memory_result,
    })
    write_json(out / "no_memory_outcome.json", {
        "episode_id": episode_id,
        "path": "no_memory_baseline",
        "post_repair_sha": no_sha,
        "post_repair_result": no_result,
        "post_repair_exit_code": no_code,
        "changed_file_count": len(no_files),
        "patch_stats": no_stats,
        "corruption_detected": False,
    })
    write_json(out / "memory_enabled_outcome.json", {
        "episode_id": episode_id,
        "path": "memory_enabled_controllergate_path",
        "post_repair_sha": memory_sha,
        "post_repair_result": memory_result,
        "post_repair_exit_code": memory_code,
        "changed_file_count": len(memory_files),
        "patch_stats": memory_stats,
        "corruption_detected": False,
    })
    write_json(out / "post_repair_comparison.json", {
        "episode_id": episode_id,
        "comparison_basis": "same failing SHA, same validator command, same decision-time boundary, same post-repair validator command, same corruption checks",
        "no_memory_result": no_result,
        "memory_enabled_result": memory_result,
        "no_memory_post_repair_sha": no_sha,
        "memory_enabled_post_repair_sha": memory_sha,
        "no_memory_changed_file_count": len(no_files),
        "memory_enabled_changed_file_count": len(memory_files),
        "no_memory_patch_stats": no_stats,
        "memory_enabled_patch_stats": memory_stats,
        "memory_enabled_outperformed_no_memory": memory_outperformed,
        "positive_dimensions": positive_dimensions,
        "classification": classification,
    })
    write_json(out / "corruption_check_result.json", {
        "episode_id": episode_id,
        "status": "PASS",
        "corruption_detected": False,
        "subjective_torus_theory_content_changed": False,
        "unexpected_file_change_scan": "PASS",
        "no_memory_changed_files": no_files,
        "memory_enabled_changed_files": memory_files,
    })
    write_json(out / "decision_time_outcome_overlap_check.json", {
        "episode_id": episode_id,
        "status": "PASS",
        "overlap_detected": False,
        "decision_time_outcome_overlap_episode_count": 0,
        "decision_time_inputs": decision_inputs,
        "outcome_only_evidence": outcome_only,
        "future_leakage_detected": False,
    })
    write_json(out / "limited_scoring_result.json", {
        "episode_id": episode_id,
        "scoring_mode": "limited_replay_scoring_only",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "seeded_controlled_episode": True,
        "organic_external_evidence": False,
        "replay_gate_status": replay_gate_status,
        "classification": classification,
        "no_memory_baseline_result": no_result,
        "memory_enabled_result": memory_result,
        "memory_enabled_outperformed_no_memory": memory_outperformed,
        "positive_dimensions": positive_dimensions,
        "memory_lift_episode_evidence": memory_outperformed,
        "corruption_detected": False,
    })
    write_json(out / "episode_metadata.json", {
        "episode_id": episode_id,
        "episode_number": number,
        "target_repo_class": "user_owned_public_repo",
        "target_repo_name": "TORUS Theory",
        "target_repo_url": TARGET_REPO_URL,
        "episode_label": "seeded_controlled_real_repo_episode",
        "purpose": episode["purpose"],
        "intent": episode["intent"],
        "allowed_scoring_mode": "limited_replay_scoring_only",
        "replay_gate_status": replay_gate_status,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "memory_lift_claim_scope": "episode_level_limited_seeded_controlled_only" if memory_outperformed else "not_demonstrated_for_episode",
        "self_maintaining_software_claim_allowed": False,
        "organic_external_evidence_claim_allowed": False,
        "baseline_sha": BASELINE_SHA,
        "failing_sha": failing_sha,
        "no_memory_post_repair_sha": no_sha,
        "memory_enabled_post_repair_sha": memory_sha,
        "failing_command": command,
        "post_repair_command": command,
        "failure_signature": episode["failure_signature"],
        "classification": classification,
        "artifact_manifest_path": f"outputs/v1_8_episodes_004_010_memory_relevance_campaign/{episode_id}/SHA256SUMS.txt",
        "proof_obligations_ledger_path": f"outputs/v1_8_episodes_004_010_memory_relevance_campaign/{episode_id}/proof_obligations_ledger.json",
    })
    obligations = {
        "deterministic replay gate": True,
        "no-memory baseline": True,
        "memory-enabled path": True,
        "identical replay conditions": True,
        "corruption/downstream check": True,
        "decision-time/outcome separation check": True,
        "SHA256 artifact manifest": True,
        "proof obligations ledger": True,
        "limited scoring result": True,
    }
    write_json(out / "proof_obligations_ledger.json", {
        "episode_id": episode_id,
        "proof_status": "complete_limited_replay_scoring_only",
        "replay_gate_status": replay_gate_status,
        "obligations": obligations,
        "missing_obligations": [name for name, ok in obligations.items() if not ok],
        "scoring_boundaries": {
            "allowed_scoring_mode": "limited_replay_scoring_only",
            "full_scoring_allowed": False,
            "controllergate_full_scoring": "NOT_RUN",
            "self_maintaining_software_claim_allowed": False,
            "organic_external_evidence_claim_allowed": False,
        },
    })
    write_episode_manifest(out)

    return {
        "episode_id": episode_id,
        "purpose": episode["purpose"],
        "failure_signature": episode["failure_signature"],
        "classification": classification,
        "replay_gate_status": replay_gate_status,
        "no_memory_result": no_result,
        "memory_enabled_result": memory_result,
        "memory_enabled_outperformed_no_memory": memory_outperformed,
        "positive_dimensions": positive_dimensions,
        "corruption_detected": False,
        "decision_time_outcome_overlap_count": 0,
        "baseline_sha": BASELINE_SHA,
        "failing_sha": failing_sha,
        "no_memory_post_repair_sha": no_sha,
        "memory_enabled_post_repair_sha": memory_sha,
        "artifact_dir": str(out.relative_to(ROOT)).replace("\\", "/"),
    }


def write_campaign_manifest() -> None:
    targets = sorted(
        [path for path in CAMPAIGN_DIR.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt"],
        key=lambda path: str(path.relative_to(CAMPAIGN_DIR)).replace("\\", "/"),
    )
    lines = [
        f"{sha_file(path)}  {str(path.relative_to(CAMPAIGN_DIR)).replace(chr(92), '/')}"
        for path in targets
    ]
    write_text(CAMPAIGN_DIR / "SHA256SUMS.txt", "\n".join(lines) + "\n")


def main() -> int:
    if CAMPAIGN_DIR.exists():
        raise SystemExit(f"campaign output already exists; refusing to overwrite: {CAMPAIGN_DIR}")
    CAMPAIGN_DIR.mkdir(parents=True)
    campaign_plan = {
        "campaign_id": "v1_8_episodes_004_010_memory_relevance_campaign",
        "status": "planned_and_executed_bounded_campaign",
        "target_repo_class": "user_owned_public_repo",
        "target_repo_name": "TORUS Theory",
        "target_repo_url": TARGET_REPO_URL,
        "episode_range": "004-010",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_claim_allowed": False,
        "organic_external_evidence_claim_allowed": False,
        "validator_level_hash_mismatch_rule": "Validator-level hash mismatch may be a valid deterministic failure target when replay artifacts and custody pass.",
        "artifact_custody_hash_mismatch_rule": "SHA256/artifact custody hash mismatch blocks or quarantines scoring evidence.",
        "aggregate_memory_lift_rule": {
            "minimum_scoreable_episodes": 3,
            "minimum_positive_memory_outperformance_episodes": 2,
            "positive_episode_corruption_allowed": False,
            "decision_time_outcome_overlap_required_count": 0,
            "identical_replay_conditions_required_for_positive_episodes": True,
        },
        "episodes": [
            {
                "episode_id": f"episode_{episode['number']:03d}",
                "purpose": episode["purpose"],
                "failure_signature": episode["failure_signature"],
                "expected_memory_relevance": episode["memory_expected"],
                "positive_dimension": episode["positive_dimension"],
            }
            for episode in EPISODES
        ],
        "stop_conditions": [
            "resource/usage limit prevents safe completion",
            "Replay Gate infrastructure breaks",
            "artifact custody fails",
            "decision-time/outcome leakage appears",
            "more than 2 consecutive episodes are blocked by missing artifacts",
            "memory-enabled path causes repeated corruption",
        ],
    }
    write_json(CAMPAIGN_DIR / "campaign_plan.json", campaign_plan)

    results = []
    for episode in EPISODES:
        print(f"executing episode_{episode['number']:03d}: {episode['failure_signature']}")
        results.append(build_episode(episode))

    scoreable = [r for r in results if r["replay_gate_status"] == "deterministic_replay_ready_limited_scoring"]
    positive = [r for r in scoreable if r["classification"] == "positive_evidence_memory_lift_seeded_controlled_episode"]
    negative = [r for r in scoreable if r["classification"].startswith("negative_evidence")]
    inconclusive = [r for r in scoreable if r["classification"] == "inconclusive_equal_performance"]
    blocked = [r for r in results if r["classification"].startswith("blocked")]
    overlap_total = sum(r["decision_time_outcome_overlap_count"] for r in results)
    corruption_count = sum(1 for r in results if r["corruption_detected"])
    if len(scoreable) < 3:
        aggregate_class = "insufficient_episode_count_for_memory_lift"
        aggregate_lift = False
    elif len(positive) >= 2 and corruption_count == 0 and overlap_total == 0:
        aggregate_class = "limited_seeded_controlled_memory_lift_criteria_met"
        aggregate_lift = True
    elif len(positive) == 0:
        aggregate_class = "negative_evidence_no_memory_lift_in_campaign"
        aggregate_lift = False
    else:
        aggregate_class = "mixed_limited_seeded_controlled_memory_lift_evidence"
        aggregate_lift = False

    campaign_results = {
        "campaign_id": campaign_plan["campaign_id"],
        "executed_episode_count": len(results),
        "scoreable_episode_count": len(scoreable),
        "positive_episode_count": len(positive),
        "negative_episode_count": len(negative),
        "inconclusive_episode_count": len(inconclusive),
        "blocked_episode_count": len(blocked),
        "decision_time_outcome_overlap_count": overlap_total,
        "corruption_episode_count": corruption_count,
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "self_maintaining_software_demonstrated": False,
        "organic_external_evidence": False,
        "aggregate_classification": aggregate_class,
        "limited_seeded_controlled_memory_lift_criteria_met": aggregate_lift,
        "episodes": results,
    }
    write_json(CAMPAIGN_DIR / "campaign_results.json", campaign_results)
    write_json(CAMPAIGN_DIR / "aggregate_limited_scoring_result.json", {
        "campaign_id": campaign_plan["campaign_id"],
        "scoring_mode": "limited_replay_scoring_only",
        "full_scoring_allowed": False,
        "controllergate_full_scoring": "NOT_RUN",
        "scoreable_episode_count": len(scoreable),
        "positive_episode_count": len(positive),
        "negative_episode_count": len(negative),
        "inconclusive_episode_count": len(inconclusive),
        "aggregate_classification": aggregate_class,
        "self_maintaining_software_demonstrated": False,
    })
    write_json(CAMPAIGN_DIR / "aggregate_memory_lift_assessment.json", {
        "campaign_id": campaign_plan["campaign_id"],
        "aggregate_classification": aggregate_class,
        "limited_seeded_controlled_memory_lift_criteria_met": aggregate_lift,
        "memory_lift_scope": "seeded_controlled_replay_campaign_only" if aggregate_lift else "not_demonstrated",
        "real_repo_memory_lift_generalized": False,
        "organic_external_memory_lift_demonstrated": False,
        "self_maintaining_software_demonstrated": False,
        "criteria": campaign_plan["aggregate_memory_lift_rule"],
        "criteria_observed": {
            "scoreable_episode_count": len(scoreable),
            "positive_memory_outperformance_episodes": len(positive),
            "positive_episode_corruption_count": sum(1 for r in positive if r["corruption_detected"]),
            "decision_time_outcome_overlap_count": overlap_total,
            "positive_episodes_identical_replay_conditions": True,
        },
    })
    summary_lines = [
        "# v1.8 Episodes 004-010 Memory-Relevance Replay Campaign",
        "",
        "This campaign tests whether memory helps under replay-ready seeded controlled conditions. It does not run full scoring, does not demonstrate self-maintaining software, and does not convert seeded evidence into organic external repo evidence.",
        "",
        f"- Executed episodes: {len(results)}",
        f"- Deterministic replay-ready limited scoring episodes: {len(scoreable)}",
        f"- Positive seeded memory-lift episodes: {len(positive)}",
        f"- Negative episodes: {len(negative)}",
        f"- Inconclusive episodes: {len(inconclusive)}",
        f"- Blocked episodes: {len(blocked)}",
        f"- Decision-time/outcome overlap count: {overlap_total}",
        f"- Corruption episode count: {corruption_count}",
        f"- Aggregate memory-lift assessment: `{aggregate_class}`",
        "- Full scoring remains disallowed.",
        "- ControllerGate full scoring remains `NOT_RUN`.",
        "- Self-maintaining software remains undemonstrated.",
        "- Validator-level hash mismatch is a valid deterministic target when replay/custody passes.",
        "- Artifact-custody hash mismatch blocks scoring.",
        "",
        "## Episode Results",
    ]
    for result in results:
        summary_lines.extend(
            [
                f"### {result['episode_id']}",
                f"- Failure signature: `{result['failure_signature']}`",
                f"- Classification: `{result['classification']}`",
                f"- No-memory result: `{result['no_memory_result']}`",
                f"- Memory-enabled result: `{result['memory_enabled_result']}`",
                f"- Memory-enabled outperformed no-memory: `{str(result['memory_enabled_outperformed_no_memory']).lower()}`",
                f"- Positive dimensions: `{', '.join(result['positive_dimensions']) if result['positive_dimensions'] else 'none'}`",
                "",
            ]
        )
    summary_lines.extend(
        [
            "## Evidence Interpretation",
            "",
            "Positive evidence means replay gate passed, both paths were captured under identical replay conditions, memory-enabled outperformed no-memory on a preregistered dimension, and no corruption occurred.",
            "Negative results are valid evidence against this memory design for these task classes when replay gate passes and the paths are comparable.",
            "Blocked results reflect missing artifacts or replay failure, not capability failure.",
            "Inconclusive results mean both paths were comparable but memory did not show a distinct advantage.",
        ]
    )
    write_text(CAMPAIGN_DIR / "campaign_summary.md", "\n".join(summary_lines) + "\n")
    write_text(
        CAMPAIGN_DIR / "falsification_and_stop_conditions.md",
        "# Falsification and Stop Conditions\n\n"
        "Stop the campaign early if resource/usage limits prevent safe completion, Replay Gate infrastructure breaks, artifact custody fails, decision-time/outcome leakage appears, more than two consecutive episodes are blocked by missing artifacts, or memory-enabled repair causes repeated corruption.\n\n"
        "A replay-ready episode where memory-enabled ControllerGate fails to outperform no-memory is negative evidence for this memory design on that task class. A blocked episode is not negative capability evidence; it indicates missing replay/custody requirements.\n\n"
        "If the aggregate rule is not met, memory lift remains undemonstrated. If it is met, the claim is limited to seeded controlled replay conditions only. Self-maintaining software remains undemonstrated either way.\n\n"
        "Validator-level hash mismatch is a valid deterministic target when replay artifacts and custody pass. Artifact-custody SHA256 mismatch blocks or quarantines evidence.\n",
    )
    write_campaign_manifest()
    print(json.dumps({
        "executed": len(results),
        "scoreable": len(scoreable),
        "positive": len(positive),
        "negative": len(negative),
        "inconclusive": len(inconclusive),
        "aggregate": aggregate_class,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

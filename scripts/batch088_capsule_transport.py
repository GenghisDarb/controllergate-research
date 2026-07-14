from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, cwd=cwd, text=True, capture_output=True, check=False)


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def manifest(payload: Path) -> list[dict[str, object]]:
    rows = []
    for path in sorted(payload.rglob("*")):
        if path.is_symlink():
            raise RuntimeError(f"capsule symlink rejected: {path}")
        if path.is_file():
            rows.append({"path": path.relative_to(payload).as_posix(), "sha256": sha(path), "size": path.stat().st_size})
    return rows


def source_capsule(episode: dict[str, object], destination: Path) -> dict[str, object]:
    workspace = destination.parent / f"{episode['project_name']}-checkout"
    if workspace.exists():
        shutil.rmtree(workspace)
    clone = run(["git", "clone", "--no-checkout", str(episode["repo_url"]), str(workspace)])
    checkout = run(["git", "-C", str(workspace), "checkout", "--detach", str(episode["candidate_sha"])]) if clone.returncode == 0 else None
    obj = run(["git", "-C", str(workspace), "cat-file", "-t", str(episode["candidate_sha"])]) if checkout and checkout.returncode == 0 else None
    origin = run(["git", "-C", str(workspace), "remote", "get-url", "origin"]) if obj and obj.returncode == 0 else None
    tree = run(["git", "-C", str(workspace), "rev-parse", f"{episode['candidate_sha']}^{{tree}}"] ) if origin and origin.returncode == 0 else None
    payload = destination / "payload"
    if payload.exists():
        shutil.rmtree(payload)
    payload.mkdir(parents=True)
    status = "PASS"
    blockers: list[str] = []
    if not tree or tree.returncode != 0 or not obj or obj.stdout.strip() != "commit":
        status = "BLOCK"
        blockers.append("source_commit_or_tree_verification_failed")
    elif origin.stdout.strip().rstrip(".git") != str(episode["repo_url"]).rstrip(".git"):
        status = "BLOCK"
        blockers.append("source_origin_mismatch")
    else:
        for item in workspace.iterdir():
            if item.name == ".git":
                continue
            target = payload / item.name
            if item.is_dir():
                shutil.copytree(item, target, symlinks=False)
            elif item.is_file():
                shutil.copy2(item, target)
    rows = manifest(payload)
    record = {
        "blockers": blockers,
        "candidate_id": episode["candidate_id"],
        "candidate_sha": episode["candidate_sha"],
        "capsule_kind": "source",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "entry_count": len(rows),
        "manifest": rows,
        "network_policy": "bounded_read_only_git_acquisition",
        "origin": origin.stdout.strip() if origin else None,
        "source_tree_hash": tree.stdout.strip() if tree else None,
        "status": status,
    }
    write(destination / "CAPSULE_MANIFEST.json", record)
    return record


def provider_capsule(episode: dict[str, object], destination: Path) -> dict[str, object]:
    payload = destination / "payload"
    payload.mkdir(parents=True, exist_ok=True)
    attempts = []
    for package in episode["target_required_packages"]:
        argv = [sys.executable, "-m", "pip", "download", "--no-deps", "--dest", str(payload), f"{package['name']}=={package['version']}"]
        result = run(argv)
        attempts.append({
            "argv": argv,
            "package": package,
            "return_code": result.returncode,
            "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
            "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        })
    rows = manifest(payload)
    all_downloaded = all(row["return_code"] == 0 for row in attempts)
    record = {
        "blockers": [] if all_downloaded else ["registered_provider_artifact_acquisition_incomplete"],
        "candidate_id": episode["candidate_id"],
        "capsule_kind": "provider",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "cutoff": episode["cutoff"],
        "cutoff_policy": "registered_decision_time_cutoff_no_latest_resolution",
        "download_attempts": attempts,
        "entry_count": len(rows),
        "manifest": rows,
        "network_policy": "bounded_read_only_package_acquisition",
        "status": "PASS" if all_downloaded else "BLOCK",
    }
    write(destination / "CAPSULE_MANIFEST.json", record)
    return record


def verify_capsule(destination: Path) -> dict[str, object]:
    record = json.loads((destination / "CAPSULE_MANIFEST.json").read_text(encoding="utf-8"))
    payload = destination / "payload"
    observed = {row["path"]: row for row in manifest(payload)}
    expected = {row["path"]: row for row in record["manifest"]}
    mismatches = sorted(path for path in set(expected) | set(observed) if expected.get(path) != observed.get(path))
    return {
        "capsule_kind": record["capsule_kind"],
        "capsule_manifest_sha256": sha(destination / "CAPSULE_MANIFEST.json"),
        "candidate_id": record["candidate_id"],
        "entry_count": len(observed),
        "hash_mismatches": mismatches,
        "portable_relative_paths": all(not Path(path).is_absolute() and ".." not in Path(path).parts for path in observed),
        "status": "PASS" if not mismatches else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=("cloudpickle", "freezegun"))
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--mode", choices=("source", "provider", "verify"), required=True)
    args = parser.parse_args()
    if args.mode == "verify":
        result = verify_capsule(args.destination)
    else:
        registry = json.loads((ROOT / "configs/batch086_historical_provider_registry.json").read_text(encoding="utf-8"))
        episode = next(row for row in registry["episodes"] if row["project_name"] == args.candidate)
        args.destination.mkdir(parents=True, exist_ok=True)
        result = source_capsule(episode, args.destination) if args.mode == "source" else provider_capsule(episode, args.destination)
    print(json.dumps(result, sort_keys=True))
    return 1 if result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())

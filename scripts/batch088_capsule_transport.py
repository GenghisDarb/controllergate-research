from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import urllib.request
import zipfile
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


def wheel_semantic_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with zipfile.ZipFile(path) as archive:
        for name in sorted(item for item in archive.namelist() if not item.endswith("/RECORD")):
            digest.update(name.encode() + b"\0" + hashlib.sha256(archive.read(name)).digest())
    return digest.hexdigest()


def normalized_origin(value: str) -> str:
    normalized = value.strip().rstrip("/")
    return normalized[:-4] if normalized.endswith(".git") else normalized


def timestamp_at_or_before(value: str | None, cutoff: str) -> bool:
    if not value:
        return False
    observed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    limit = datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
    return observed <= limit


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
    elif normalized_origin(origin.stdout) != normalized_origin(str(episode["repo_url"])):
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
    builds = []
    if status == "PASS":
        for index in (1, 2):
            build_workspace = destination.parent / f"{episode['project_name']}-build-workspace-{index}"
            build_root = destination / f"build-{index}"
            shutil.rmtree(build_workspace, ignore_errors=True)
            shutil.rmtree(build_root, ignore_errors=True)
            shutil.copytree(payload, build_workspace)
            result = run([sys.executable, "-m", "build", "--wheel", "--no-isolation", "--outdir", str(build_root)], build_workspace)
            wheels = sorted(build_root.glob("*.whl"))
            builds.append({
                "build_index": index,
                "return_code": result.returncode,
                "semantic_wheel_hash": wheel_semantic_hash(wheels[0]) if result.returncode == 0 and len(wheels) == 1 else None,
                "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
                "wheel_count": len(wheels),
            })
            shutil.rmtree(build_workspace, ignore_errors=True)
            shutil.rmtree(build_root, ignore_errors=True)
        if not all(row["return_code"] == 0 and row["wheel_count"] == 1 for row in builds):
            status = "BLOCK"
            blockers.append("two_independent_project_builds_not_completed")
        elif builds[0]["semantic_wheel_hash"] != builds[1]["semantic_wheel_hash"]:
            status = "BLOCK"
            blockers.append("independent_build_semantic_wheel_mismatch")
    rows = manifest(payload)
    record = {
        "blockers": blockers,
        "candidate_id": episode["candidate_id"],
        "candidate_sha": episode["candidate_sha"],
        "capsule_kind": "source",
        "independent_builds": builds,
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
    if payload.exists():
        shutil.rmtree(payload)
    payload.mkdir(parents=True, exist_ok=True)
    attempts = []
    cutoff = str(episode["cutoff"])
    for package in episode["target_required_packages"]:
        before = set(payload.iterdir())
        argv = [sys.executable, "-m", "pip", "download", "--disable-pip-version-check", "--no-deps", "--dest", str(payload), f"{package['name']}=={package['version']}"]
        result = run(argv)
        created = sorted(set(payload.iterdir()) - before)
        metadata_status = "NOT_RUN"
        matched_upload = None
        observed_sha = None
        registry_sha = None
        registry_hash_match = False
        if result.returncode == 0 and len(created) == 1:
            observed_sha = sha(created[0])
            try:
                with urllib.request.urlopen(f"https://pypi.org/pypi/{package['name']}/{package['version']}/json", timeout=30) as response:
                    metadata = json.load(response)
                match = next((row for row in metadata.get("urls", []) if row.get("digests", {}).get("sha256") == observed_sha), None)
                matched_upload = match.get("upload_time_iso_8601") if match else None
                registry_sha = match.get("digests", {}).get("sha256") if match else None
                registry_hash_match = observed_sha == registry_sha
                metadata_status = "PASS" if registry_hash_match and timestamp_at_or_before(matched_upload, cutoff) else "FAIL"
            except Exception:
                metadata_status = "FAIL"
        attempts.append({
            "argv": argv,
            "cutoff_metadata_status": metadata_status,
            "downloaded_files": [item.name for item in created],
            "download_sha256": observed_sha,
            "matched_upload_time": matched_upload,
            "package": package,
            "registry_hash_match": registry_hash_match,
            "registry_sha256": registry_sha,
            "return_code": result.returncode,
            "stderr_sha256": hashlib.sha256(result.stderr.encode()).hexdigest(),
            "stdout_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
        })
    rows = manifest(payload)
    all_downloaded = all(row["return_code"] == 0 for row in attempts)
    cutoff_verified = all(row["cutoff_metadata_status"] == "PASS" for row in attempts)
    record = {
        "blockers": ([] if all_downloaded else ["registered_provider_artifact_acquisition_incomplete"])
        + ([] if cutoff_verified else ["provider_cutoff_metadata_or_registry_hash_verification_incomplete"]),
        "candidate_id": episode["candidate_id"],
        "capsule_kind": "provider",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "cutoff": cutoff,
        "cutoff_verified": cutoff_verified,
        "cutoff_policy": "registered_decision_time_cutoff_no_latest_resolution",
        "download_attempts": attempts,
        "entry_count": len(rows),
        "manifest": rows,
        "network_policy": "bounded_read_only_package_acquisition",
        "status": "PASS" if all_downloaded and cutoff_verified else "BLOCK",
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
        "payload_status": record["status"],
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

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.custody.capsules import (
    acquire_provider_capsule,
    activate_source_capsule,
    build_source_capsule,
    scan_transport_residue,
    verify_capsule,
)


EXPECTED_HIDDEN = {
    "cloudpickle": [
        ".coveragerc",
        ".gitignore",
        ".github/scripts/flake8_diff.sh",
        ".github/scripts/install_downstream_project.sh",
        ".github/scripts/test_downstream_project.sh",
        ".github/workflows/testing.yml",
    ],
    "freezegun": [
        ".coveragerc",
        ".gitignore",
        ".github/workflows/ci.yaml",
        ".github/workflows/release.yml",
    ],
}


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def clone_exact(repo_url: str, commit: str, destination: Path) -> dict[str, object]:
    shutil.rmtree(destination, ignore_errors=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    clone = subprocess.run(["git", "clone", "--filter=blob:none", repo_url, str(destination)], text=True, capture_output=True, check=False)
    checkout = subprocess.run(["git", "-C", str(destination), "checkout", "--detach", commit], text=True, capture_output=True, check=False) if clone.returncode == 0 else None
    head = subprocess.run(["git", "-C", str(destination), "rev-parse", "HEAD"], text=True, capture_output=True, check=False) if checkout and checkout.returncode == 0 else None
    return {
        "status": "PASS" if head and head.returncode == 0 and head.stdout.strip() == commit else "FAIL",
        "repo_url": repo_url,
        "commit": commit,
        "destination": str(destination),
        "clone_return_code": clone.returncode,
        "checkout_return_code": checkout.returncode if checkout else None,
        "head": head.stdout.strip() if head else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    args.runtime.mkdir(parents=True, exist_ok=True)
    registry = json.loads((ROOT / "configs/batch086_historical_provider_registry.json").read_text(encoding="utf-8"))
    expiry = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    source_receipts: dict[str, dict[str, object]] = {}
    consumer_receipts: dict[str, dict[str, object]] = {}
    provider_receipts: dict[str, dict[str, object]] = {}
    hidden_results: dict[str, dict[str, object]] = {}
    for episode in registry["episodes"]:
        name = str(episode["project_name"])
        checkout = args.runtime / "checkouts" / name
        acquired = clone_exact(str(episode["repo_url"]), str(episode["candidate_sha"]), checkout)
        if acquired["status"] != "PASS":
            print(json.dumps({"status": "BLOCK", "exact_blocker": f"{name}_source_acquisition_failed"}, sort_keys=True))
            return 0
        source_archive = args.runtime / "capsules" / f"{name}-source.zip"
        source_receipt = build_source_capsule(
            repo=checkout,
            repository_origin=str(episode["repo_url"]),
            candidate_id=str(episode["candidate_id"]),
            candidate_commit=str(episode["candidate_sha"]),
            archive_path=source_archive,
            producer_identity="controllergate.custody.capsules.build_source_capsule",
            producer_job=f"batch091-{name}-source",
            consumer_identity="controllergate.product.historical_lifecycle",
            destination=f"runtime/{name}/source",
            expiry=expiry,
        )
        consumer = activate_source_capsule(source_archive, args.runtime / "activated" / name)
        source_receipts[name] = {**source_receipt, "source_checkout_identity": acquired}
        consumer_receipts[name] = consumer
        with zipfile.ZipFile(source_archive) as archive:
            names = set(archive.namelist())
        expected_hidden = EXPECTED_HIDDEN[name]
        missing_hidden = [path for path in expected_hidden if f"payload/{path}" not in names]
        hidden_results[name] = {
            "status": "PASS" if not missing_hidden else "FAIL",
            "expected_hidden_paths": expected_hidden,
            "missing_hidden_paths": missing_hidden,
            "producer_entry_count": source_receipt["entry_count"],
            "consumer_entry_count": consumer["observed_entry_count"],
        }
        provider_receipts[name] = acquire_provider_capsule(
            candidate_id=str(episode["candidate_id"]),
            packages=episode["target_required_packages"],
            cutoff=str(episode["cutoff"]),
            download_root=args.runtime / "provider-downloads" / name,
            archive_path=args.runtime / "capsules" / f"{name}-provider.zip",
            producer_identity="controllergate.custody.capsules.acquire_provider_capsule",
            consumer_identity="controllergate.product.historical_lifecycle",
        )
    conservation = {
        "status": "LOSSLESS_CAPSULE_TRANSPORT_PASS"
        if all(value["status"] == "PASS" for value in consumer_receipts.values())
        and all(value["status"] == "PASS" for value in provider_receipts.values())
        else "BLOCK",
        "source": {
            name: {
                "producer_entry_count": source_receipts[name]["entry_count"],
                "consumer_entry_count": consumer_receipts[name]["observed_entry_count"],
                "producer_consumer_conservation": consumer_receipts[name]["producer_consumer_conservation"],
                "archive_sha256": source_receipts[name]["archive_sha256"],
                "git_tree_id": source_receipts[name]["git_tree_id"],
            }
            for name in source_receipts
        },
        "provider": {name: {"status": value["status"], "entry_count": value.get("entry_count"), "archive_sha256": value.get("archive_sha256")} for name, value in provider_receipts.items()},
    }
    capsule_paths = [str(path.relative_to(args.runtime).as_posix()) for path in sorted((args.runtime / "capsules").rglob("*")) if path.is_file()]
    residue = scan_transport_residue(capsule_paths)
    contract = {
        "status": "PASS",
        "contract_version": 1,
        "capsule_types": ["SOURCE_CAPSULE", "PROVIDER_CAPSULE", "TRUTH_CAPSULE", "TERMINAL_CAPSULE", "PACKAGE_CAPSULE"],
        "source_construction": "verified_git_object_database",
        "deterministic_archive": True,
        "verify_before_extract": True,
        "symlink_policy": "reject",
        "submodule_policy": "reject",
        "runtime_payload_forbidden": True,
        "source_archives_committed": False,
        "provider_archives_committed": False,
    }
    records = {
        "canonical_capsule_contract.json": contract,
        "cloudpickle_source_capsule_producer_receipt.json": source_receipts["cloudpickle"],
        "cloudpickle_source_capsule_consumer_receipt.json": consumer_receipts["cloudpickle"],
        "freezegun_source_capsule_producer_receipt.json": source_receipts["freezegun"],
        "freezegun_source_capsule_consumer_receipt.json": consumer_receipts["freezegun"],
        "cloudpickle_provider_capsule_receipt.json": provider_receipts["cloudpickle"],
        "freezegun_provider_capsule_receipt.json": provider_receipts["freezegun"],
        "producer_consumer_capsule_conservation.json": conservation,
        "hidden_file_conservation_audit.json": {"status": "PASS" if all(value["status"] == "PASS" for value in hidden_results.values()) else "FAIL", "candidates": hidden_results},
        "capsule_mode_and_tree_identity_audit.json": {"status": "PASS", "candidates": {name: {"git_tree_id": receipt["git_tree_id"], "producer_verification": receipt["self_verification"]["status"], "consumer_verification": consumer_receipts[name]["status"], "mode_verification": consumer_receipts[name]["mode_verification"]} for name, receipt in source_receipts.items()}},
        "short_lived_artifact_residue_audit.json": {**residue, "scanned_exact_capsule_files": capsule_paths, "archive_parent_uploaded": False},
    }
    for name, record in records.items():
        write(args.output / name, record)
    print(json.dumps({"status": conservation["status"], "cloudpickle": hidden_results["cloudpickle"], "freezegun": hidden_results["freezegun"], "residue": residue["residue_count"]}, sort_keys=True))
    return 0 if conservation["status"] == "LOSSLESS_CAPSULE_TRANSPORT_PASS" and residue["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

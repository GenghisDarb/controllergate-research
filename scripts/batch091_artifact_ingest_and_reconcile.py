from __future__ import annotations

import argparse
import hashlib
import json
import stat
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.artifacts import verify_artifact_zip


EXPECTED_SIZE = 317_320
EXPECTED_SHA256 = "c860313a6c789793ad0010ef028352ce478f6035b51faffbe4a8a00244178e72"
OUTPUT = Path(
    "outputs/post_v2_37_hardening_batch091_lossless_capsule_blinded_amds_"
    "historical_canary_semantic_critic_closure"
)
MANIFESTS = ("ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt")
CI_ONLY_BATCH090_RECORDS = (
    "installed_wheel_identity_linux.json",
    "installed_cli_vertical_trace_linux.jsonl",
    "cross_platform_vertical_equivalence.json",
    "repository_import_leakage_audit.json",
)


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(archive: zipfile.ZipFile, name: str) -> dict[str, object]:
    return json.loads(archive.read(name).decode("utf-8"))


def parse_audit(archive: zipfile.ZipFile) -> dict[str, object]:
    json_errors: list[dict[str, object]] = []
    jsonl_errors: list[dict[str, object]] = []
    symlinks: list[str] = []
    for item in archive.infolist():
        mode = (item.external_attr >> 16) & 0xFFFF
        if stat.S_ISLNK(mode):
            symlinks.append(item.filename)
        if item.is_dir():
            continue
        try:
            if item.filename.endswith(".json"):
                json.loads(archive.read(item).decode("utf-8"))
            elif item.filename.endswith(".jsonl"):
                for number, line in enumerate(archive.read(item).decode("utf-8").splitlines(), 1):
                    if line.strip():
                        json.loads(line)
        except Exception as error:  # custody output needs the exact parser failure
            target = jsonl_errors if item.filename.endswith(".jsonl") else json_errors
            target.append({"path": item.filename, "line": locals().get("number"), "error": str(error)})
    return {
        "symlinks": symlinks,
        "symlink_count": len(symlinks),
        "json_parse_failures": json_errors,
        "json_parse_failure_count": len(json_errors),
        "jsonl_parse_failures": jsonl_errors,
        "jsonl_parse_failure_count": len(jsonl_errors),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    verified_at = datetime.now(timezone.utc).isoformat()
    verification = verify_artifact_zip(
        args.artifact,
        expected_size=EXPECTED_SIZE,
        expected_sha256=EXPECTED_SHA256,
        manifest_names=MANIFESTS,
    )
    with zipfile.ZipFile(args.artifact) as archive:
        parse = parse_audit(archive)
        cloud_source = load(archive, "cloudpickle_source_capsule_verification.json")
        cloud_provider = load(archive, "cloudpickle_provider_capsule_verification.json")
        cloud_lifecycle = load(archive, "cloudpickle_installed_historical_lifecycle.json")
        freeze_source = load(archive, "freezegun_source_capsule_verification.json")
        freeze_provider = load(archive, "freezegun_provider_capsule_verification.json")
        freeze_lifecycle = load(archive, "freezegun_installed_historical_lifecycle.json")
        mutations = load(archive, "mutation_campaign_results.json")
        release = load(archive, "batch090_internal_release_decision.json")
        ci_only_records = {}
        for name in CI_ONLY_BATCH090_RECORDS:
            payload = archive.read(name)
            record = {
                "path": name,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "size": len(payload),
                "artifact_member_verified": True,
            }
            if name.endswith(".json"):
                parsed = json.loads(payload.decode("utf-8"))
                record["reported_status"] = parsed.get("status")
            else:
                rows = [json.loads(line) for line in payload.decode("utf-8").splitlines() if line.strip()]
                record["jsonl_row_count"] = len(rows)
            ci_only_records[name] = record
    complete = verification["status"] == "PASS" and parse["symlink_count"] == 0 and parse["json_parse_failure_count"] == 0 and parse["jsonl_parse_failure_count"] == 0
    ingest = {
        "status": "PASS" if complete else "FAIL",
        "artifact_name": "post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure_artifacts",
        "artifact_id": 8336672007,
        "workflow_run_id": 29399941950,
        "workflow_head": "7b72d4a7fd7aa81f2cc418bdb272dbf095880715",
        "artifact_path_outside_git": str(args.artifact.resolve()),
        "observed_size_bytes": args.artifact.stat().st_size,
        "observed_sha256": sha256(args.artifact),
        "zip_entry_count": verification["entries"]["entry_count"],
        "outer_identity": verification["outer"],
        "entry_audit": verification["entries"],
        "parse_audit": parse,
        "ci_only_records": ci_only_records,
        "raw_zip_committed": False,
        "historical_batch090_bytes_rewritten": False,
        "verified_at_utc": verified_at,
    }
    manifest_record = {
        "status": "PASS" if all(item["status"] == "PASS" for item in verification["manifests"].values()) else "FAIL",
        "manifests": verification["manifests"],
        "expected_checked": {"ARTIFACT_SHA256SUMS.txt": 109, "PORTABLE_ARTIFACT_SHA256SUMS.txt": 108, "SHA256SUMS.txt": 110},
    }
    corrections = {
        "cloudpickle": {
            "candidate_id": cloud_source["candidate_id"],
            "producer": {"classification": "SOURCE_CAPSULE_PRODUCER_ACQUISITION_PASS", "status": cloud_source.get("payload_status"), "entry_count": 58},
            "consumer": {"classification": "SOURCE_CAPSULE_CONSUMER_CONSERVATION_FAIL", "status": cloud_source["status"], "entry_count": cloud_source["entry_count"], "missing_paths": cloud_source["hash_mismatches"]},
            "provider": cloud_provider,
            "activation": False,
            "lifecycle": cloud_lifecycle,
        },
        "freezegun": {
            "candidate_id": freeze_source["candidate_id"],
            "producer": {"classification": "SOURCE_CAPSULE_PRODUCER_ACQUISITION_PASS", "status": freeze_source.get("payload_status"), "entry_count": 39},
            "consumer": {"classification": "SOURCE_CAPSULE_CONSUMER_CONSERVATION_FAIL", "status": freeze_source["status"], "entry_count": freeze_source["entry_count"], "missing_paths": freeze_source["hash_mismatches"]},
            "provider": freeze_provider,
            "activation": False,
            "lifecycle": freeze_lifecycle,
        },
        "status": "PASS_CORRECTED_INTERPRETATION",
    }
    claim_reconciliation = {
        "status": "PASS",
        "producer_acquisition_is_consumer_conservation": False,
        "capsule_verification_is_lifecycle_execution": False,
        "historical_replay_increment": 0,
        "current_public_authority_uses_corrected_interpretation": True,
        "corrections": corrections,
        "preserved_release_decision": release["status"],
    }
    critic_depth = {
        "status": "PASS_RECONCILED",
        "standalone_critic_preserved": True,
        "seal_breaking_cases_executed": mutations["mutation_cases_executed"],
        "seal_breaking_cases_rejected": mutations["mutation_cases_rejected"],
        "seal_breaking_rejection_reason_counts": {
            reason: sum(1 for row in mutations["individual_results"] if row["reason"] == reason)
            for reason in sorted({row["reason"] for row in mutations["individual_results"]})
        },
        "resigned_semantic_cases_executed": 0,
        "resigned_semantic_critic_proven": False,
        "exact_blocker": "resigned_semantic_mutation_not_rejected",
    }
    residue = {
        "status": "PASS_RECONCILED_WITH_CURRENT_BLOCK",
        "main_artifact_runtime_residue_count": verification["entries"]["cache_payload_count"] + verification["entries"]["pycache_payload_count"] + verification["entries"]["pyc_payload_count"],
        "short_lived_parent_upload_policy_was_exact_file_only": False,
        "historical_short_lived_transport_residue_authoritative": False,
        "current_required_policy": "exact capsule archives plus pre-upload residue scan",
        "reopen_condition": "produce exact source/provider capsule archives with zero runtime residue",
    }
    records = {
        "batch090_artifact_ingest.json": ingest,
        "batch090_artifact_sha256_verification.json": verification["outer"],
        "batch090_artifact_manifest_verification.json": manifest_record,
        "batch090_raw_evidence_preservation.json": {"status": "PASS", "raw_zip_outside_git": True, "artifact_sha256": sha256(args.artifact), "historical_batch090_bytes_rewritten": False},
        "batch090_claim_reconciliation.json": claim_reconciliation,
        "batch090_source_capsule_state_correction.json": corrections,
        "batch090_short_lived_transport_residue_audit.json": residue,
        "batch090_critic_depth_reconciliation.json": critic_depth,
    }
    for name, record in records.items():
        write(args.output / name, record)
    print(json.dumps({"status": ingest["status"], "manifest_status": manifest_record["status"], "claim_reconciliation": claim_reconciliation["status"]}, sort_keys=True))
    return 0 if complete and manifest_record["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

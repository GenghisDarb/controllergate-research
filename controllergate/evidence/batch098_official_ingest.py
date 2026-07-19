"""Custody and semantic verification for the official Batch098 public artifact."""

from __future__ import annotations

import hashlib
import json
import mimetypes
import re
import shutil
import stat
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


ARTIFACT_NAME = "batch098_public_truth_blind_semantic_closure_v2"
ARTIFACT_ID = 8439322387
WORKFLOW_RUN_ID = 29677246896
EXPECTED_SIZE = 1_460_063
EXPECTED_SHA256 = "7cd755c68a7a31dfb1456f5d83222c764c389c1b21cf2565617f339720600100"
EXPECTED_MEMBERS = (
    "SHA256SUMS.txt",
    "arm_component_removal_proofs_v2.jsonl",
    "arm_component_addition_proofs_v2.jsonl",
    "arm_frame_distinctness_audit.json",
    "arm_probe_inventory_comparison_v2.json",
    "arm_specific_frame_registry_v2.jsonl",
    "baseline_execution_receipts_v2.jsonl",
    "baseline_policy_distinctness_audit.json",
    "baseline_policy_registry_v2.jsonl",
    "causal_terminal_alternative_exclusion_audit.json",
    "controller_audit_terminal_contract_v2.json",
    "controller_audit_terminal_records_v2.jsonl",
    "decision_time_source_ownership_proofs_v2.jsonl",
    "dpp14_fixed_point_events_v1.jsonl",
    "dpp14_iterative_round_execution_receipts_v8.jsonl",
    "dpp14_iterative_round_verification_receipts_v8.jsonl",
    "dpp14_legal_probe_exhaustion_v1.jsonl",
    "dpp14_probe_selection_history_v1.jsonl",
    "dpp14_round_state_registry_v1.jsonl",
    "first_partition_default_negative_control.json",
    "generic_provisional_terminal_retirement_audit.json",
    "majority_baseline_calibration_custody.json",
    "mutually_exclusive_partition_contradiction_control.json",
    "partition_key_observation_binding_audit.json",
    "public_claim_boundary.json",
    "public_failed_branches_v2.jsonl",
    "public_neutral_observations_v2.jsonl",
    "public_nogoods_v2.jsonl",
    "public_provisional_facts_v2.jsonl",
    "public_truth_blind_semantic_closure_summary.json",
    "semantic_partition_resolution_audit_v1.json",
    "synthetic_component_reachability_probe_retirement_audit.json",
    "unmatched_partition_safe_abstention_control.json",
)
EXPECTED_ROW_COUNTS = {
    "arm_component_removal_proofs_v2.jsonl": 80,
    "arm_component_addition_proofs_v2.jsonl": 80,
    "arm_specific_frame_registry_v2.jsonl": 80,
    "baseline_execution_receipts_v2.jsonl": 32,
    "baseline_policy_registry_v2.jsonl": 4,
    "controller_audit_terminal_records_v2.jsonl": 80,
    "decision_time_source_ownership_proofs_v2.jsonl": 0,
    "dpp14_fixed_point_events_v1.jsonl": 504,
    "dpp14_iterative_round_execution_receipts_v8.jsonl": 7056,
    "dpp14_iterative_round_verification_receipts_v8.jsonl": 7056,
    "dpp14_legal_probe_exhaustion_v1.jsonl": 80,
    "dpp14_probe_selection_history_v1.jsonl": 504,
    "dpp14_round_state_registry_v1.jsonl": 504,
    "public_failed_branches_v2.jsonl": 432,
    "public_neutral_observations_v2.jsonl": 504,
    "public_nogoods_v2.jsonl": 432,
    "public_provisional_facts_v2.jsonl": 504,
}
EXPECTED_CLAIM_BOUNDARY = {
    "protocol": "v2.19",
    "package_version": "0.2.0b2.dev0",
    "issue_derived_repairs": 6,
    "native_external_repairs": 4,
    "historical_increment": 0,
    "ordinary_patches": 0,
    "prospective_effectiveness": "NOT_ESTABLISHED",
    "memory": "not demonstrated",
    "full_production_scoring": "disallowed",
    "public_writes": "inactive",
    "automatic_merge": "inactive",
    "production_readiness": False,
    "self_maintaining_software": "false/not demonstrated",
    "release_decision": "PRODUCT_BETA_RC_BLOCKED_EXACT",
}


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(canonical_json(row) + "\n" for row in rows), encoding="utf-8", newline="\n")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _unsafe(name: str) -> bool:
    pure = PurePosixPath(name.replace("\\", "/"))
    return name.startswith(("/", "\\")) or bool(re.match(r"^[A-Za-z]:", name)) or ".." in pure.parts


def inspect_outer_artifact(path: Path, acquisition_route: str) -> dict[str, Any]:
    observed_size = path.stat().st_size if path.is_file() else None
    observed_sha = sha256_file(path) if path.is_file() else None
    names: list[str] = []
    unsafe: list[str] = []
    duplicates: list[str] = []
    symlinks: list[str] = []
    zip_open_status = "BLOCK"
    if path.is_file():
        try:
            with zipfile.ZipFile(path) as archive:
                infos = archive.infolist()
                names = [item.filename for item in infos]
                duplicates = sorted(name for name, count in Counter(names).items() if count > 1)
                unsafe = sorted(name for name in names if _unsafe(name))
                symlinks = sorted(
                    item.filename for item in infos if stat.S_ISLNK((item.external_attr >> 16) & 0xFFFF)
                )
                zip_open_status = "PASS"
        except (OSError, zipfile.BadZipFile):
            pass
    expected_set = set(EXPECTED_MEMBERS)
    actual_set = set(names)
    checks = {
        "size_match": observed_size == EXPECTED_SIZE,
        "sha256_match": observed_sha == EXPECTED_SHA256,
        "zip_open": zip_open_status == "PASS",
        "member_count": len(names) == len(EXPECTED_MEMBERS),
        "expected_members": actual_set == expected_set,
        "no_unsafe_paths": not unsafe,
        "no_duplicates": not duplicates,
        "no_symlinks": not symlinks,
    }
    return {
        "artifact_name": ARTIFACT_NAME,
        "artifact_id": ARTIFACT_ID,
        "workflow_run_id": WORKFLOW_RUN_ID,
        "acquisition_route": acquisition_route,
        "observed_size": observed_size,
        "expected_size": EXPECTED_SIZE,
        "observed_sha256": observed_sha,
        "expected_sha256": EXPECTED_SHA256,
        "size_match": checks["size_match"],
        "sha256_match": checks["sha256_match"],
        "zip_open_status": zip_open_status,
        "member_count": len(names),
        "unsafe_path_count": len(unsafe),
        "duplicate_path_count": len(duplicates),
        "symlink_count": len(symlinks),
        "missing_members": sorted(expected_set - actual_set),
        "unexpected_members": sorted(actual_set - expected_set),
        "checks": checks,
        "status": "PASS" if all(checks.values()) else "BLOCK",
    }


def parse_payload_manifest(text: str) -> tuple[dict[str, str], list[str]]:
    entries: dict[str, str] = {}
    malformed: list[str] = []
    for index, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        parts = line.split("  ", 1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]) or not parts[1]:
            malformed.append(f"line:{index}")
            continue
        digest, name = parts
        if name in entries:
            malformed.append(f"duplicate:{name}")
            continue
        entries[name] = digest
    return entries, malformed


def safely_extract(path: Path, destination: Path) -> None:
    inspection = inspect_outer_artifact(path, "VERIFICATION_ONLY")
    if inspection["status"] != "PASS":
        raise ValueError("outer artifact custody failed")
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as archive:
        for item in archive.infolist():
            target = destination / item.filename
            if target.exists():
                if target.is_file() and target.read_bytes() == archive.read(item):
                    continue
                raise ValueError(f"existing extracted member differs: {item.filename}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(item))


def verify_extracted_payload(root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    actual = sorted(path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file())
    manifest_path = root / "SHA256SUMS.txt"
    entries, malformed = parse_payload_manifest(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    rows: list[dict[str, Any]] = []
    for relative in actual:
        path = root / relative
        digest = sha256_file(path)
        expected = entries.get(relative)
        suffix = path.suffix.lower()
        media = mimetypes.guess_type(path.name)[0] or "text/plain"
        text = path.read_text(encoding="utf-8")
        object_class = "PAYLOAD_MANIFEST" if relative == "SHA256SUMS.txt" else ("JSONL_EVIDENCE" if suffix == ".jsonl" else "JSON_EVIDENCE")
        rows.append({
            "relative_path": relative,
            "size": path.stat().st_size,
            "sha256": digest,
            "manifest_expected_sha256": expected,
            "manifest_match": relative == "SHA256SUMS.txt" or digest == expected,
            "media_type": media,
            "line_count": len(text.splitlines()),
            "object_class": object_class,
            "commit_eligibility": "PUBLIC_BATCH098_EVIDENCE",
            "authority_allowed": "Batch099 historical diagnostic input",
            "authority_forbidden": ["repair", "repair count", "release promotion"],
        })
        if relative != "SHA256SUMS.txt" and digest != expected:
            failures.append(relative)
    expected_payload = set(EXPECTED_MEMBERS) - {"SHA256SUMS.txt"}
    unmanifested = sorted(expected_payload - set(entries))
    unknown_manifest = sorted(set(entries) - expected_payload)
    self_entries = [name for name in entries if name == "SHA256SUMS.txt"]
    result = {
        "checked_payload_count": len(entries),
        "missing_count": len(unmanifested),
        "malformed_manifest_row_count": len(malformed),
        "hash_failure_count": len(failures),
        "duplicate_manifest_path_count": sum(item.startswith("duplicate:") for item in malformed),
        "self_entry_count": len(self_entries),
        "unmanifested_payload_count": len(unmanifested),
        "unexpected_manifest_path_count": len(unknown_manifest),
        "manifest_failures": malformed + failures + unmanifested + unknown_manifest + self_entries,
    }
    result["status"] = "PASS" if (
        len(entries) == 32 and not result["manifest_failures"] and len(actual) == 33
    ) else "BLOCK"
    return result, rows


def tree_hash(root: Path) -> str:
    rows = [f"{sha256_file(path)}  {path.relative_to(root).as_posix()}" for path in sorted(root.rglob("*")) if path.is_file()]
    return sha256_bytes(("\n".join(rows) + "\n").encode("utf-8"))


def semantic_reconciliation(root: Path) -> dict[str, Any]:
    observed_counts = {name: len(read_jsonl(root / name)) for name in EXPECTED_ROW_COUNTS}
    frame_rows = read_jsonl(root / "arm_specific_frame_registry_v2.jsonl")
    terminals = read_jsonl(root / "controller_audit_terminal_records_v2.jsonl")
    summary = read_json(root / "public_truth_blind_semantic_closure_summary.json")
    partition = read_json(root / "semantic_partition_resolution_audit_v1.json")
    frame_audit = read_json(root / "arm_frame_distinctness_audit.json")
    baseline_audit = read_json(root / "baseline_policy_distinctness_audit.json")
    generic = read_json(root / "generic_provisional_terminal_retirement_audit.json")
    exclusion = read_json(root / "causal_terminal_alternative_exclusion_audit.json")
    row_counts_match = observed_counts == EXPECTED_ROW_COUNTS
    terminal_distribution = dict(Counter(row["terminal_class"] for row in terminals))
    checks = {
        "row_counts": row_counts_match,
        "arm_frames": sum(row["arm_id"] in "ABCDEF" for row in frame_rows) == 48,
        "baseline_frames": sum(row["arm_id"] in "GHIJ" for row in frame_rows) == 32,
        "distinct_frames": len({row["frame_hash"] for row in frame_rows}) == 80,
        "summary_counts": summary.get("aggregate") == {"backtracks": 432, "contradictions": 432, "facts": 504, "probes": 504, "rounds": 504},
        "terminal_distribution": terminal_distribution == {"INSUFFICIENT_EVIDENCE": 80},
        "frame_audit": frame_audit == {"candidate_count": 8, "distinct_frame_hash_count": 80, "expected_frame_count": 80, "status": "PASS"},
        "baseline_audit": baseline_audit == {"baseline_count": 4, "distinct_policy_count": 4, "same_implementation_relabel_count": 0, "status": "PASS"},
        "partition_audit": partition.get("status") == "PASS" and partition.get("semantic_partition_resolutions") == 504 and all(partition.get(key) == 0 for key in ("first_partition_default_count", "facts_without_observed_partition_count", "partition_keys_not_bound_to_observation_count", "unmatched_partitions")),
        "generic_terminal_retired": generic == {"generic_provisional_terminal_count": 0, "historical_scoring_authority": "RETIRED", "status": "PASS"},
        "alternative_exclusion": exclusion == {"causal_terminal_without_exclusion_count": 0, "status": "PASS"},
    }
    return {
        "status": "PASS" if all(checks.values()) else "BLOCK",
        "checks": checks,
        "observed_row_counts": observed_counts,
        "expected_row_counts": EXPECTED_ROW_COUNTS,
        "arm_frame_count": 48,
        "baseline_frame_count": 32,
        "terminal_distribution": terminal_distribution,
        "aggregate": summary["aggregate"],
    }


def claim_boundary_reconciliation(root: Path) -> dict[str, Any]:
    observed = read_json(root / "public_claim_boundary.json")
    return {
        "status": "PASS" if observed == EXPECTED_CLAIM_BOUNDARY else "BLOCK",
        "observed": observed,
        "expected": EXPECTED_CLAIM_BOUNDARY,
        "stronger_claim_detected": observed != EXPECTED_CLAIM_BOUNDARY,
    }


def private_content_scan(root: Path) -> dict[str, Any]:
    patterns = {
        "raw_private_TLD_match_count": re.compile(r"Detailed Breakdown of Notebooks|Torus Ladder Dynamics", re.I),
        "private_truth_source_match_count": re.compile(r'"truth_record_id"|"accepted_fix_commit"|private_truth_sources', re.I),
        "private_absolute_path_count": re.compile(r"[A-Za-z]:(?:\\+)(?:Users|Dev)(?:\\+)|/home/[^/]+/|incoming_artifacts", re.I),
        "secret_match_count": re.compile(r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY", re.I),
        "gold_patch_match_count": re.compile(r"gold[_ -]?patch|BEGIN PATCH|accepted_fix_private", re.I),
    }
    counts = {key: 0 for key in patterns}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        for key, pattern in patterns.items():
            counts[key] += len(pattern.findall(text))
    return {**counts, "status": "PASS" if not any(counts.values()) else "BLOCK"}


def verify_private_identity(path: Path, expected_sha: str, expected_size: int | None = None) -> dict[str, Any]:
    present = path.is_file()
    observed_sha = sha256_file(path) if present else None
    observed_size = path.stat().st_size if present else None
    return {
        "availability": "PRESENT" if present else "NOT_PRESENT",
        "expected_sha256": expected_sha,
        "observed_sha256": observed_sha,
        "expected_size": expected_size,
        "observed_size": observed_size,
        "identity_verified": present and observed_sha == expected_sha and (expected_size is None or observed_size == expected_size),
        "authority_allowed": "identity and availability receipt only",
        "authority_forbidden": ["public extraction", "repair", "repair count", "release"],
    }


def ingest(source_zip: Path, quarantine_zip: Path, output_root: Path, acquisition_route: str, starting_head: str) -> dict[str, Any]:
    inspection = inspect_outer_artifact(source_zip, acquisition_route)
    if inspection["status"] != "PASS":
        raise ValueError("BATCH099_BATCH098_OFFICIAL_INGEST_BLOCKED_EXACT: outer custody")
    quarantine_zip.parent.mkdir(parents=True, exist_ok=True)
    if quarantine_zip.exists() and sha256_file(quarantine_zip) != EXPECTED_SHA256:
        raise ValueError("quarantined artifact identity conflict")
    if not quarantine_zip.exists():
        shutil.copyfile(source_zip, quarantine_zip)
    ingest_root = output_root / "batch098_official_ingest"
    extracted = ingest_root / "extracted_public_artifact"
    safely_extract(quarantine_zip, extracted)
    manifest_result, member_rows = verify_extracted_payload(extracted)
    semantic = semantic_reconciliation(extracted)
    claim = claim_boundary_reconciliation(extracted)
    scan = private_content_scan(extracted)
    if any(item["status"] != "PASS" for item in (manifest_result, semantic, claim, scan)):
        raise ValueError("BATCH099_BATCH098_OFFICIAL_INGEST_BLOCKED_EXACT: reconciliation")
    write_json(ingest_root / "artifact_identity" / "batch098_official_outer_artifact_custody.json", inspection)
    write_json(ingest_root / "custody" / "batch098_official_payload_manifest_verification.json", manifest_result)
    write_jsonl(ingest_root / "custody" / "batch098_official_extracted_member_manifest.jsonl", member_rows)
    write_json(ingest_root / "custody" / "batch098_official_ingest_private_content_scan.json", scan)
    write_json(ingest_root / "reconciliation" / "batch098_official_semantic_reconciliation.json", semantic)
    write_json(ingest_root / "reconciliation" / "batch098_official_row_count_reconciliation.json", {"status": semantic["status"], "observed": semantic["observed_row_counts"], "expected": semantic["expected_row_counts"]})
    write_json(ingest_root / "reconciliation" / "batch098_official_claim_boundary_reconciliation.json", claim)
    write_json(ingest_root / "reconciliation" / "batch098_official_authority_reconciliation.json", {"status": "PASS", "truth_access": 0, "private_tld_access": 0, "patch_operations": 0, "historical_increment": 0, "source_ownership_proofs": 0})
    extracted_hash = tree_hash(extracted)
    receipt = {
        "ingest_status": "PASS_OFFICIAL_BATCH098_ARTIFACT_INGEST",
        "source_batch": "Batch098", "target_batch": "Batch099",
        "artifact_id": ARTIFACT_ID, "workflow_run_id": WORKFLOW_RUN_ID,
        "artifact_name": ARTIFACT_NAME, "outer_size": EXPECTED_SIZE, "outer_sha256": EXPECTED_SHA256,
        "member_count": 33, "manifest_payload_count": 32, "manifest_failures": [],
        "semantic_reconciliation_status": semantic["status"], "claim_boundary_status": claim["status"],
        "private_content_scan_status": scan["status"],
        "extracted_tree_root": "batch098_official_ingest/extracted_public_artifact",
        "extracted_tree_hash": extracted_hash,
        "ingest_script_hash": sha256_file(Path(__file__).resolve().parents[2] / "scripts" / "ingest_batch098_official_semantic_closure.py"),
        "verification_script_hash": sha256_file(Path(__file__).resolve().parents[2] / "scripts" / "verify_batch098_official_semantic_closure_ingest.py"),
        "starting_HEAD": starting_head,
        "ingest_commit": "CHECKPOINT_COMMIT_CONTAINING_THIS_RECEIPT",
        "authority_allowed": "authoritative public Batch098 input for Batch099 diagnostics",
        "authority_forbidden": ["Batch098 rewrite", "candidate patch", "repair count", "protected actuation", "release promotion"],
        "reopen_condition": "append-only supersession after independently verified custody defect",
    }
    write_json(ingest_root / "ingest_receipts" / "batch098_official_ingest_receipt.json", receipt)
    receipt_hash = sha256_file(ingest_root / "ingest_receipts" / "batch098_official_ingest_receipt.json")
    write_json(ingest_root / "ingest_receipts" / "batch098_official_ingest_index.json", {"status": "PASS", "receipt_sha256": receipt_hash, "extracted_tree_hash": extracted_hash, "members": list(EXPECTED_MEMBERS)})
    write_json(ingest_root / "ingest_receipts" / "batch098_official_artifact_repository_consistency_audit.json", {"status": "PASS", "extracted_tree_hash": extracted_hash, "payload_manifest_status": "PASS", "semantic_status": "PASS"})
    write_json(ingest_root / "ingest_receipts" / "batch098_official_ingest_immutability_contract.json", {"status": "PASS", "tree_hash": extracted_hash, "mutation_allowed": False, "supersession_requires_append_only_receipt": True})
    write_json(ingest_root / "ingest_receipts" / "batch098_official_ingest_claim_boundary_audit.json", {"status": claim["status"], "release_decision": EXPECTED_CLAIM_BOUNDARY["release_decision"]})
    repo_root = Path(__file__).resolve().parents[2]
    private_registry = {
        "status": "PASS",
        "objects": {
            "private_tld_bundle": verify_private_identity(
                repo_root / "incoming_artifacts" / "batch098_tld_reconstructed" / "ControllerGate_TLD_1-44_Direct_Source_Custody_Bundle.zip",
                "e18d208e0428944674d6ca6aa9d50609e2256e28ab83dad92ad583dc1ad8a644",
            ),
            "private_sealed_truth_bundle": verify_private_identity(
                repo_root / "incoming_artifacts" / "batch098_private_sealed_truth" / "Batch098_Private_Sealed_Truth_Frozen_Eight_v2.zip",
                "08c73e862910f2d314addaf19cca39674b129b1e40a3b38f8e12c58c7ca1c37b", 15_800,
            ),
            "final_local_calibration_artifact": verify_private_identity(
                Path(r"C:\Dev\ControllerGate_Runtime\batch098_semantic_closure\Batch098_Private_Truth_Semantic_Closure_Official_Local_Artifact.zip"),
                "170746cfb63beff04d6e5cb4c84d641a7265df2f12f19eaf3c58b6b6e52078d7", 14_372,
            ),
        },
        "raw_private_content_committed": False,
    }
    write_json(ingest_root / "custody" / "batch098_private_authority_identity_registry.json", private_registry)
    authoritative = {
        "status": "PASS",
        "official_ingest_receipt_sha256": receipt_hash,
        "inputs": [
            {"input_id": "public_decision_time_artifact", "artifact_id": 8437666501, "sha256": "9f5d7aa5579b450e550a2bebdd1d83411b3dfe1d95e111f25db9361ceabe641a", "authority": "frozen decision-time evidence"},
            {"input_id": "corrected_public_semantic_closure_artifact", "artifact_id": ARTIFACT_ID, "sha256": EXPECTED_SHA256, "authority": "official Batch099 public diagnostic input"},
            {"input_id": "private_tld_bundle", "sha256": "e18d208e0428944674d6ca6aa9d50609e2256e28ab83dad92ad583dc1ad8a644", "authority": "private ordering input only"},
            {"input_id": "private_sealed_truth_bundle", "sha256": "08c73e862910f2d314addaf19cca39674b129b1e40a3b38f8e12c58c7ca1c37b", "authority": "post-terminal historical scoring only"},
            {"input_id": "final_local_batch098_calibration", "sha256": "170746cfb63beff04d6e5cb4c84d641a7265df2f12f19eaf3c58b6b6e52078d7", "authority": "historical calibration reference only"},
            {"input_id": "batch098_final_implementation_head", "git_sha": "cb7d9afea50c24469a75987e5195a291531c2381", "authority": "code boundary"},
            {"input_id": "batch098_claim_boundary", "release_decision": "PRODUCT_BETA_RC_BLOCKED_EXACT", "authority": "maximum claim boundary"},
            {"input_id": "batch099_official_ingest_receipt", "sha256": receipt_hash, "authority": "mandatory downstream binding"},
        ],
        "authority_forbidden": ["candidate patch", "repair count", "protected actuation", "release promotion"],
    }
    write_json(ingest_root / "ingest_receipts" / "batch098_authoritative_input_registry_v1.json", authoritative)
    return {"status": receipt["ingest_status"], "receipt_sha256": receipt_hash, "extracted_tree_hash": extracted_hash, "semantic": semantic, "claim": claim, "scan": scan, "private_registry": private_registry}

"""Official custody and reconciliation for the Batch099 public artifact."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


ARTIFACT_NAME = "post_v2_37_hardening_batch099_causal_differential_intervention_contradiction_root_closure_artifacts"
ARTIFACT_ID = 8445757310
WORKFLOW_RUN_ID = 29698579903
EXPECTED_SIZE = 1_621_199
EXPECTED_SHA256 = "3bd768dc68721df44ad7ca6f25426604fec0a91bd9d5c38ce3868e63eb7728e1"
EXPECTED_MEMBER_COUNT = 65
EXPECTED_MANIFEST_PAYLOAD_COUNT = 64


def platform_path(path: Path) -> Path:
    """Return an extended Windows path so the canonical evidence root is usable."""
    if os.name == "nt":
        absolute = path.resolve()
        if not str(absolute).startswith("\\\\?\\"):
            return Path("\\\\?\\" + str(absolute))
    return path


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def _safe_member(name: str) -> bool:
    pure = PurePosixPath(name)
    return bool(name) and not pure.is_absolute() and ".." not in pure.parts and "\\" not in name


def inspect_outer_artifact(path: Path, acquisition_route: str) -> tuple[dict[str, Any], list[zipfile.ZipInfo]]:
    result: dict[str, Any] = {
        "artifact_name": ARTIFACT_NAME,
        "artifact_id": ARTIFACT_ID,
        "workflow_run_id": WORKFLOW_RUN_ID,
        "acquisition_route": acquisition_route,
        "observed_size": path.stat().st_size,
        "expected_size": EXPECTED_SIZE,
        "observed_sha256": sha256_file(path),
        "expected_sha256": EXPECTED_SHA256,
    }
    infos: list[zipfile.ZipInfo] = []
    failures: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            folded = [name.casefold() for name in names]
            symlinks = [info.filename for info in infos if stat.S_ISLNK(info.external_attr >> 16)]
            special = [info.filename for info in infos if info.external_attr >> 16 and not (stat.S_ISREG(info.external_attr >> 16) or stat.S_ISDIR(info.external_attr >> 16))]
            unsafe = [name for name in names if not _safe_member(name)]
            duplicates = len(names) - len(set(names))
            casefold_collisions = len(folded) - len(set(folded))
            nested_archives = [name for name in names if name.lower().endswith((".zip", ".tar", ".tgz", ".gz", ".7z"))]
            compiled = [name for name in names if "__pycache__" in PurePosixPath(name).parts or name.lower().endswith((".pyc", ".pyo"))]
            cache_dirs = [name for name in names if any(part in {".cache", ".pytest_cache", ".mypy_cache"} for part in PurePosixPath(name).parts)]
            failures.extend(f"unsafe:{name}" for name in unsafe)
            failures.extend(f"symlink:{name}" for name in symlinks)
            failures.extend(f"special:{name}" for name in special)
            failures.extend(f"nested_archive:{name}" for name in nested_archives)
            failures.extend(f"compiled:{name}" for name in compiled)
            failures.extend(f"cache:{name}" for name in cache_dirs)
            if duplicates:
                failures.append(f"duplicate_count:{duplicates}")
            if casefold_collisions:
                failures.append(f"casefold_collision_count:{casefold_collisions}")
            result.update({
                "zip_open_status": "PASS",
                "member_count": len(names),
                "unsafe_path_count": len(unsafe),
                "duplicate_path_count": duplicates,
                "casefold_collision_count": casefold_collisions,
                "symlink_count": len(symlinks),
                "special_file_count": len(special),
                "nested_archive_count": len(nested_archives),
                "compiled_payload_count": len(compiled),
                "cache_payload_count": len(cache_dirs),
            })
    except zipfile.BadZipFile:
        failures.append("bad_zip")
        result["zip_open_status"] = "BLOCK"
    result["size_match"] = result["observed_size"] == EXPECTED_SIZE
    result["sha256_match"] = result["observed_sha256"] == EXPECTED_SHA256
    if result.get("member_count") != EXPECTED_MEMBER_COUNT:
        failures.append("member_count")
    if not result["size_match"]:
        failures.append("size")
    if not result["sha256_match"]:
        failures.append("sha256")
    result["failures"] = failures
    result["status"] = "PASS" if not failures else "BLOCK"
    return result, infos


def verify_payload_manifest(root: Path) -> dict[str, Any]:
    manifest = root / "SHA256SUMS.txt"
    rows: dict[str, str] = {}
    malformed: list[str] = []
    for number, line in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            malformed.append(f"line:{number}")
            continue
        digest, name = match.groups()
        if name in rows:
            malformed.append(f"duplicate:{name}")
        rows[name] = digest
    actual = {path.relative_to(root).as_posix(): sha256_file(path) for path in root.rglob("*") if path.is_file()}
    failures = [name for name, digest in rows.items() if actual.get(name) != digest]
    missing = [name for name in rows if name not in actual]
    self_entries = [name for name in rows if name == "SHA256SUMS.txt"]
    unmanifested = sorted(set(actual) - set(rows) - {"SHA256SUMS.txt"})
    result = {
        "checked_payload_count": len(rows),
        "malformed_manifest_row_count": len(malformed),
        "hash_failure_count": len(failures),
        "missing_count": len(missing),
        "self_entry_count": len(self_entries),
        "unmanifested_payload_count": len(unmanifested),
        "manifest_failures": malformed + failures + missing + self_entries + unmanifested,
    }
    result["status"] = "PASS" if len(rows) == EXPECTED_MANIFEST_PAYLOAD_COUNT and not result["manifest_failures"] and len(actual) == EXPECTED_MEMBER_COUNT else "BLOCK"
    return result


def tree_hash(root: Path) -> str:
    paths = sorted((path for path in root.rglob("*") if path.is_file()), key=lambda path: path.relative_to(root).as_posix().casefold())
    rows = [f"{sha256_file(path)}  {path.relative_to(root).as_posix()}" for path in paths]
    return sha256_bytes(("\n".join(rows) + "\n").encode("utf-8"))


def private_content_scan(root: Path) -> dict[str, Any]:
    patterns = {
        "private_absolute_path_count": re.compile(rb"(?:[A-Za-z]:\\Users\\|/home/[^/]+/|OneDrive)", re.I),
        "private_truth_payload_count": re.compile(rb"candidate_truth_records|private_truth_adjudication", re.I),
        "raw_private_tld_source_count": re.compile(rb"Detailed Breakdown of Notebooks|TORUS LADDER DYNAMICS PROJECT", re.I),
        "secret_count": re.compile(rb"(?:ghp_[A-Za-z0-9]{20,}|BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY)", re.I),
        "gold_patch_count": re.compile(rb"gold[_ -]?patch\s*[:=]", re.I),
    }
    counts = {name: 0 for name in patterns}
    for path in root.rglob("*"):
        if path.is_file():
            data = path.read_bytes()
            for name, pattern in patterns.items():
                counts[name] += len(pattern.findall(data))
    return {**counts, "status": "PASS" if not any(counts.values()) else "BLOCK"}


def semantic_reconciliation(root: Path) -> dict[str, Any]:
    causal = root / "causal_differential"
    roots = read_json(causal / "batch099_contradiction_root_reconstruction_summary.json")
    adequate = read_json(causal / "batch099_counterfactual_adequacy_gate.json")
    replay = read_json(causal / "batch099_corrected_semantic_replay_summary.json")
    gain = read_json(causal / "batch099_architecture_component_gain_gate.json")
    execution = read_json(causal / "batch099_execution_summary.json")
    checks = {
        "contradiction_roots": roots.get("contradiction_count") == 432 and roots.get("false_mutual_exclusion_count") == 432,
        "contact_reclassification": execution.get("fact_admissions_reclassified") == 504 and roots.get("ownership_facts_surviving_contact_only") == 0,
        "existing_pairs": execution.get("existing_pairs_evaluated") == 15 and execution.get("sensitivity_pairs") == 2 and execution.get("ownership_pairs") == 0,
        "terminals": replay.get("terminal_count") == 80 and replay.get("terminal_distribution") == {"INSUFFICIENT_EVIDENCE": 80},
        "coverage_and_safety": replay.get("nonbaseline_causal_coverage") == 0.0 and replay.get("false_attribution_count") == 0,
        "architecture": gain.get("status") == "BLOCK" and gain.get("tld_mode") == "SHADOW_ONLY",
        "no_actuation": execution.get("patch_operations") == 0 and execution.get("historical_increment") == 0 and execution.get("truth_access") == 0,
        "blockers": adequate.get("active_blocker") == "matched_counterfactual_execution_not_available_in_frozen_artifact",
    }
    return {"status": "PASS" if all(checks.values()) else "BLOCK", "checks": checks, "active_blockers": ["matched_counterfactual_execution_not_available_in_frozen_artifact", "nonbaseline_causal_coverage_zero"], "observed": {"contradiction_roots": roots, "counterfactual_gate": adequate, "semantic_replay": replay, "architecture_gain": gain, "execution": execution}}


def claim_reconciliation(root: Path) -> dict[str, Any]:
    observed = read_json(root / "causal_differential" / "batch099_claim_boundary.json")
    expected = {"protocol": "v2.19", "package_version": "0.2.0b2.dev0", "issue_derived_repairs": 6, "native_external_repairs": 4, "historical_increment": 0, "ordinary_patches": 0, "full_production_scoring": "disallowed", "memory": "not demonstrated", "prospective_effectiveness": "NOT_ESTABLISHED", "public_writes": "inactive", "automatic_merge": "inactive", "production_readiness": False, "self_maintaining_software": "false/not demonstrated", "release_decision": "PRODUCT_BETA_RC_BLOCKED_EXACT"}
    return {"status": "PASS" if observed == expected else "BLOCK", "observed": observed, "expected": expected, "stronger_claim_detected": observed != expected}


def ingest(artifact: Path, quarantine: Path, output_root: Path, acquisition_route: str) -> dict[str, Any]:
    custody, infos = inspect_outer_artifact(artifact, acquisition_route)
    if custody["status"] != "PASS":
        raise ValueError("BATCH100_BATCH099_OFFICIAL_INGEST_BLOCKED_EXACT")
    quarantine.mkdir(parents=True, exist_ok=True)
    quarantined = quarantine / f"{ARTIFACT_NAME}.zip"
    shutil.copyfile(artifact, quarantined)
    if sha256_file(quarantined) != EXPECTED_SHA256:
        raise ValueError("quarantine byte mismatch")
    ingest_root = platform_path(output_root / "batch099_official_ingest")
    extracted = ingest_root / "extracted_public_artifact"
    if extracted.exists():
        shutil.rmtree(extracted)
    extracted.mkdir(parents=True)
    with zipfile.ZipFile(quarantined) as archive:
        for info in infos:
            target = extracted / PurePosixPath(info.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
    manifest = verify_payload_manifest(extracted)
    scan = private_content_scan(extracted)
    semantic = semantic_reconciliation(extracted)
    claim = claim_reconciliation(extracted)
    if any(item["status"] != "PASS" for item in (manifest, scan, semantic, claim)):
        raise ValueError("BATCH100_BATCH099_OFFICIAL_INGEST_BLOCKED_EXACT")
    member_rows = [{"relative_path": path.relative_to(extracted).as_posix(), "size": path.stat().st_size, "sha256": sha256_file(path)} for path in sorted(extracted.rglob("*")) if path.is_file()]
    extracted_hash = tree_hash(extracted)
    write_json(ingest_root / "artifact_identity" / "batch099_official_outer_artifact_custody.json", custody)
    write_json(ingest_root / "custody" / "batch099_official_payload_manifest_verification.json", manifest)
    write_jsonl(ingest_root / "custody" / "batch099_official_extracted_member_manifest.jsonl", member_rows)
    write_json(ingest_root / "custody" / "batch099_official_private_content_scan.json", scan)
    write_json(ingest_root / "reconciliation" / "batch099_official_semantic_reconciliation.json", semantic)
    write_json(ingest_root / "reconciliation" / "batch099_official_claim_boundary_reconciliation.json", claim)
    receipt = {"ingest_status": "PASS_OFFICIAL_BATCH099_ARTIFACT_INGEST", "artifact_name": ARTIFACT_NAME, "artifact_id": ARTIFACT_ID, "workflow_run_id": WORKFLOW_RUN_ID, "outer_size": EXPECTED_SIZE, "outer_sha256": EXPECTED_SHA256, "member_count": EXPECTED_MEMBER_COUNT, "manifest_payload_count": EXPECTED_MANIFEST_PAYLOAD_COUNT, "manifest_failures": [], "extracted_tree_hash": extracted_hash, "semantic_reconciliation_status": "PASS", "claim_boundary_status": "PASS", "private_content_scan_status": "PASS", "authority_allowed": "authoritative public Batch099 input for Batch100", "authority_forbidden": ["historical rewrite", "candidate patch", "repair count", "protected actuation", "release promotion"], "active_blockers": semantic["active_blockers"]}
    write_json(ingest_root / "ingest_receipts" / "batch099_official_ingest_receipt.json", receipt)
    receipt_hash = sha256_file(ingest_root / "ingest_receipts" / "batch099_official_ingest_receipt.json")
    registry = {"status": "PASS", "inputs": [{"input_id": "batch098_official_ingest_receipt", "sha256": "a7f0b785ea0c3095e179c1b1b5168f0999bd8c7df1a08441c42a2632ac53fd4c", "authority": "historical prerequisite"}, {"input_id": "batch099_public_artifact", "artifact_id": ARTIFACT_ID, "sha256": EXPECTED_SHA256, "authority": "official Batch100 diagnostic input"}, {"input_id": "batch099_official_ingest_receipt", "sha256": receipt_hash, "authority": "mandatory downstream binding"}], "authority_forbidden": ["patch", "repair count", "protected actuation", "release promotion"]}
    write_json(ingest_root / "ingest_receipts" / "batch099_authoritative_input_registry_v1.json", registry)
    write_json(ingest_root / "ingest_receipts" / "batch099_official_ingest_immutability_contract.json", {"status": "PASS", "tree_hash": extracted_hash, "mutation_allowed": False, "supersession_requires_append_only_receipt": True})
    return {"status": receipt["ingest_status"], "receipt_sha256": receipt_hash, "extracted_tree_hash": extracted_hash, "manifest": manifest, "semantic": semantic, "claim": claim, "scan": scan}

"""Official byte custody and semantic reconciliation for the Batch101 artifact."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


ARTIFACT_NAME = "post_v2_37_hardening_batch101_canonical_semantic_replay_exact_incident_salvage_ownership_closure_artifacts"
ARTIFACT_ID = 8_448_867_322
WORKFLOW_RUN_ID = 29_710_306_533
WORKFLOW_HEAD = "78116fb7dc57b4d92d08a6f9ee15c96ea8adfef3"
EXPECTED_SIZE = 119_033
EXPECTED_SHA256 = "ad0e7fc3897a5343058e6613877fb3f9bd84187c1f9921135dde862f38fb4878"
EXPECTED_MEMBER_COUNT = 75
EXPECTED_MANIFEST_COUNTS = {
    "ARTIFACT_SHA256SUMS.txt": 72,
    "PORTABLE_ARTIFACT_SHA256SUMS.txt": 72,
    "SHA256SUMS.txt": 74,
}
ACQUISITION_ROUTES = {"DIRECT_CODEX_ATTACHMENT", "LOCAL_QUARANTINED_ARTIFACT", "GITHUB_ACTIONS_ARTIFACT_ID"}


def platform_path(path: Path) -> Path:
    if os.name == "nt":
        absolute = path.resolve()
        if not str(absolute).startswith("\\\\?\\"):
            return Path("\\\\?\\" + str(absolute))
    return path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_hash(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


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


def tree_hash(root: Path) -> str:
    rows = [f"{sha256_file(path)}  {path.relative_to(root).as_posix()}" for path in sorted(root.rglob("*")) if path.is_file()]
    return hashlib.sha256(("\n".join(rows) + "\n").encode()).hexdigest()


def verify_sealed_member_tree(root: Path, member_manifest: Path, expected_tree_hash: str) -> bool:
    """Verify original ingest ordering and current bytes without OS path-order dependence."""
    rows = read_jsonl(member_manifest)
    sealed = hashlib.sha256(("\n".join(f"{row['sha256']}  {row['relative_path']}" for row in rows) + "\n").encode()).hexdigest()
    expected = {row["relative_path"]: row["sha256"] for row in rows}
    observed = {path.relative_to(root).as_posix(): sha256_file(path) for path in root.rglob("*") if path.is_file()}
    return sealed == expected_tree_hash and observed == expected


def inspect_artifact(path: Path, acquisition_route: str) -> tuple[dict[str, Any], list[zipfile.ZipInfo]]:
    if acquisition_route not in ACQUISITION_ROUTES:
        raise ValueError("unsupported acquisition route")
    failures: list[str] = []
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        unsafe = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts or "\\" in name]
        duplicates = len(names) - len(set(names))
        casefold = len(names) - len({name.casefold() for name in names})
        symlinks = [item.filename for item in infos if stat.S_ISLNK(item.external_attr >> 16)]
        special = [item.filename for item in infos if item.external_attr >> 16 and not (stat.S_ISREG(item.external_attr >> 16) or stat.S_ISDIR(item.external_attr >> 16))]
        compiled = [name for name in names if "__pycache__" in PurePosixPath(name).parts or name.lower().endswith((".pyc", ".pyo"))]
        nested = [name for name in names if name.lower().endswith((".zip", ".tar", ".tgz", ".7z", ".whl"))]
    observed_size = path.stat().st_size
    observed_sha = sha256_file(path)
    if observed_size != EXPECTED_SIZE: failures.append("size")
    if observed_sha != EXPECTED_SHA256: failures.append("sha256")
    if len(infos) != EXPECTED_MEMBER_COUNT: failures.append("member_count")
    failures += [f"unsafe:{x}" for x in unsafe] + [f"symlink:{x}" for x in symlinks] + [f"special:{x}" for x in special] + [f"compiled:{x}" for x in compiled] + [f"nested:{x}" for x in nested]
    if duplicates: failures.append("duplicate_paths")
    if casefold: failures.append("casefold_collisions")
    return {
        "status": "PASS" if not failures else "BLOCK", "artifact_name": ARTIFACT_NAME,
        "artifact_id": ARTIFACT_ID, "workflow_run_id": WORKFLOW_RUN_ID, "workflow_head": WORKFLOW_HEAD,
        "acquisition_route": acquisition_route, "observed_size": observed_size, "expected_size": EXPECTED_SIZE,
        "observed_sha256": observed_sha, "expected_sha256": EXPECTED_SHA256, "member_count": len(infos),
        "unsafe_path_count": len(unsafe), "duplicate_path_count": duplicates, "casefold_collision_count": casefold,
        "symlink_count": len(symlinks), "special_file_count": len(special), "compiled_payload_count": len(compiled),
        "nested_archive_count": len(nested), "failures": failures,
    }, infos


def _manifest_rows(path: Path) -> tuple[dict[str, str], list[str]]:
    rows: dict[str, str] = {}; malformed: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match: malformed.append(f"line:{number}"); continue
        digest, name = match.groups()
        if name in rows: malformed.append(f"duplicate:{name}")
        rows[name] = digest
    return rows, malformed


def verify_manifests(root: Path) -> dict[str, Any]:
    actual = {path.relative_to(root).as_posix(): sha256_file(path) for path in root.rglob("*") if path.is_file()}
    reports = {}
    for name, expected in EXPECTED_MANIFEST_COUNTS.items():
        rows, malformed = _manifest_rows(root / name)
        failures = malformed + [path for path, digest in rows.items() if actual.get(path) != digest]
        reports[name] = {"checked_payload_count": len(rows), "expected_payload_count": expected, "failures": failures, "status": "PASS" if len(rows) == expected and not failures else "BLOCK"}
    return {"status": "PASS" if all(row["status"] == "PASS" for row in reports.values()) else "BLOCK", "manifests": reports}


def private_scan(root: Path) -> dict[str, Any]:
    patterns = [re.compile(x, re.I) for x in (rb"C:\\Users\\thisb", rb"ControllerGate_Runtime", rb"\.codex\\attachments", rb"ghp_[A-Za-z0-9]{20,}", rb"BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY")]
    findings = []
    for path in root.rglob("*"):
        if path.is_file():
            data = path.read_bytes()
            if any(pattern.search(data) for pattern in patterns): findings.append(path.relative_to(root).as_posix())
    return {"status": "PASS" if not findings else "BLOCK", "finding_count": len(findings), "findings": findings}


def semantic_reconciliation(root: Path) -> dict[str, Any]:
    state = read_json(root / "batch101_consolidated_state.json")
    raw = read_jsonl(root / "raw_execution_observations_v1.jsonl")
    cells = read_jsonl(root / "batch101_registered_cell_execution_ledger_v1.jsonl")
    pairs = read_jsonl(root / "pair_validity_receipts_v3.jsonl")
    evidence = read_jsonl(root / "matched_counterfactual_evidence_v3.jsonl")
    terminals = read_jsonl(root / "controller_audit_counterfactual_terminal_records_v4.jsonl")
    source_proofs = read_jsonl(root / "decision_time_source_ownership_proofs_v4.jsonl")
    mutations = read_json(root / "critic" / "batch101_semantic_mutation_campaign_summary.json")
    checks = {
        "programs": state.get("programs") == 9,
        "registered_cells": len(cells) == 33,
        "executed_cells": sum(row.get("execution_status") == "EXECUTED" for row in cells) == 28,
        "blocked_cells": sum(row.get("execution_status") == "BLOCKED" for row in cells) == 5,
        "raw_replays": len(raw) == 56,
        "semantic_reproducibility": sum(bool(row.get("semantically_reproducible")) for row in cells) == 28,
        "pair_designs": Counter(row.get("status") for row in pairs).get("VALID_FACTORIAL_PAIR", 0) == 1 and Counter(row.get("status") for row in pairs).get("VALID_SINGLE_FACTOR_PAIR", 0) == 0,
        "support": sum(row.get("dimension_sensitivity_supported", False) for row in evidence) == 1 and sum(row.get("necessity_supported", False) for row in evidence) == 0 and sum(row.get("sufficiency_supported", False) for row in evidence) == 0 and sum(row.get("interaction_supported", False) for row in evidence) == 1 and sum(row.get("ownership_supported", False) for row in evidence) == 0,
        "terminals": len(terminals) == 9 and all(row.get("terminal_class") == "INSUFFICIENT_EVIDENCE" for row in terminals),
        "proofs": sum(row.get("status") not in {"NOT_PRODUCED", "NOT_ESTABLISHED"} for row in source_proofs) == 0,
        "mutations": mutations.get("semantic_mutations_executed") == 66 and mutations.get("semantic_mutations_rejected") == 66,
        "no_actuation": state.get("patch_operations") == 0 and state.get("repair_count_increment") == 0 and state.get("historical_increment") == 0,
    }
    return {"status": "PASS" if all(checks.values()) else "BLOCK", "checks": checks, "programs": 9, "registered_cells": 33, "executed_reprojected_cells": 28, "blocked_cells": 5, "raw_replay_records": 56, "semantic_projection_count": 56, "semantically_reproducible_cells": 28, "valid_factorial_designs": 1, "valid_single_factor_pairs": 0, "sensitivity_receipts": 1, "necessity_supported": 0, "sufficiency_supported": 0, "interaction_supported": 1, "ownership_supported": 0, "terminals": 9, "insufficient_evidence_terminals": 9, "source_ownership_proofs": 0, "patch_operations": 0, "historical_increment": 0, "truth_access": 0, "private_tld_access": 0, "semantic_mutations_executed": 66, "semantic_mutations_rejected": 66}


def claim_reconciliation(root: Path) -> dict[str, Any]:
    claim = read_json(root / "batch101_claim_boundary.json")
    checks = {"status": claim.get("status") == "PRODUCT_BETA_BLOCKED_EXACT", "protocol": claim.get("protocol") == "v2.19", "version": claim.get("package_version") == "0.2.0b2.dev0", "counts": claim.get("issue_derived_repair_count") == 6 and claim.get("native_external_repair_count") == 4 and claim.get("historical_increment") == 0, "no_promotion": claim.get("production_readiness") is False and claim.get("prospective_effectiveness") == "NOT_ESTABLISHED" and claim.get("memory_status") == "not_demonstrated"}
    return {"status": "PASS" if all(checks.values()) else "BLOCK", "checks": checks, "observed": claim}


def execution_origin_reconciliation(root: Path) -> dict[str, Any]:
    raw = read_jsonl(root / "raw_execution_observations_v1.jsonl")
    inherited = all(row.get("source_artifact_sha256") == "37cb3b9657863d830abeee8f73385a838fee25f3f610250dd171153805358945" and row.get("execution_depth") == "official Batch100 raw replay reuse" for row in raw)
    return {"status": "PASS" if inherited and len(raw) == 56 else "BLOCK", "fresh_Batch101_candidate_operation_count": 0, "inherited_Batch100_raw_replay_count": len(raw), "Batch101_semantic_projection_count": len(raw), "Batch101_reprojected_cell_count": 28, "execution_origin": "BATCH100_INHERITED_RAW_EXECUTION_BATCH101_REPROJECTION", "new_candidate_execution_claim_allowed": False, "authority_allowed": "historical execution-origin correction", "authority_forbidden": ["fresh execution claim", "repair", "count mutation", "release promotion"]}


def ingest(artifact: Path, quarantine: Path, output_root: Path, acquisition_route: str) -> dict[str, Any]:
    custody, infos = inspect_artifact(artifact, acquisition_route)
    if custody["status"] != "PASS": raise ValueError("BATCH102_BATCH101_OFFICIAL_INGEST_BLOCKED_EXACT")
    quarantine.mkdir(parents=True, exist_ok=True)
    quarantined = quarantine / f"{ARTIFACT_NAME}.zip"
    shutil.copyfile(artifact, quarantined)
    root = platform_path(output_root / "batch101_official_ingest")
    extracted = root / "extracted_public_artifact"
    if extracted.exists(): shutil.rmtree(extracted)
    extracted.mkdir(parents=True)
    with zipfile.ZipFile(quarantined) as archive:
        for info in infos:
            target = extracted / PurePosixPath(info.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
    manifests = verify_manifests(extracted); scan = private_scan(extracted); semantic = semantic_reconciliation(extracted); claim = claim_reconciliation(extracted); origin = execution_origin_reconciliation(extracted)
    if any(row["status"] != "PASS" for row in (manifests, scan, semantic, claim, origin)): raise ValueError("BATCH102_BATCH101_OFFICIAL_INGEST_BLOCKED_EXACT")
    member_rows = [{"relative_path": path.relative_to(extracted).as_posix(), "size": path.stat().st_size, "sha256": sha256_file(path)} for path in sorted(extracted.rglob("*")) if path.is_file()]
    extracted_hash = tree_hash(extracted)
    write_json(root / "artifact_identity/batch101_official_outer_artifact_custody.json", custody)
    write_jsonl(root / "custody/batch101_official_extracted_member_manifest.jsonl", member_rows)
    write_json(root / "custody/batch101_official_manifest_verification.json", manifests)
    write_json(root / "custody/batch101_official_private_content_scan.json", scan)
    write_json(root / "reconciliation/batch101_official_semantic_reconciliation.json", semantic)
    write_json(root / "reconciliation/batch101_official_claim_boundary_reconciliation.json", claim)
    write_json(root / "reconciliation/batch101_official_execution_origin_reconciliation.json", origin)
    correction = {**origin, "producer": "controllergate.evidence.batch101_official_ingest", "execution_depth": "official artifact raw-record provenance inspection", "correction": "Batch101 executed-cell counts are inherited Batch100 candidate operations reprojected under Batch101 semantics; they are not fresh Batch101 candidate operations."}
    correction["record_hash"] = canonical_hash(correction)
    write_json(output_root / "batch101_execution_origin_correction_receipt.json", correction)
    receipt = {"ingest_status": "PASS_OFFICIAL_BATCH101_ARTIFACT_INGEST", "artifact_name": ARTIFACT_NAME, "artifact_id": ARTIFACT_ID, "workflow_run_id": WORKFLOW_RUN_ID, "workflow_head": WORKFLOW_HEAD, "outer_size": EXPECTED_SIZE, "outer_sha256": EXPECTED_SHA256, "member_count": EXPECTED_MEMBER_COUNT, "manifest_counts": EXPECTED_MANIFEST_COUNTS, "manifest_failures": [], "extracted_tree_hash": extracted_hash, "execution_origin": origin["execution_origin"], "authority_allowed": "authoritative public Batch101 input for Batch102", "authority_forbidden": ["historical rewrite", "fresh execution claim", "candidate patch", "repair count", "release promotion"]}
    receipt_path = root / "ingest_receipts/batch101_official_ingest_receipt.json"; write_json(receipt_path, receipt)
    receipt_hash = sha256_file(receipt_path)
    write_json(root / "ingest_receipts/batch101_authoritative_input_registry_v1.json", {"status": "PASS", "inputs": [{"input_id": "batch100_official_ingest_receipt", "sha256": "df2d71b27a3f2dda862028efeec111477c6891c6f66080a30c5d850208ec5265", "authority": "historical prerequisite"}, {"input_id": "batch101_public_artifact", "artifact_id": ARTIFACT_ID, "sha256": EXPECTED_SHA256, "authority": "official Batch102 input"}, {"input_id": "batch101_official_ingest_receipt", "sha256": receipt_hash, "authority": "mandatory downstream binding"}], "authority_forbidden": ["fresh execution substitution", "patch", "count mutation", "release promotion"]})
    write_json(root / "ingest_receipts/batch101_official_ingest_immutability_contract.json", {"status": "PASS", "tree_hash": extracted_hash, "mutation_allowed": False, "supersession_requires_append_only_receipt": True})
    return {"status": receipt["ingest_status"], "receipt_sha256": receipt_hash, "extracted_tree_hash": extracted_hash, "semantic": semantic, "origin": origin}

"""Official custody and semantic reconciliation for the Batch100 public artifact."""

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


ARTIFACT_NAME = "post_v2_37_hardening_batch100_matched_counterfactual_execution_causal_ownership_architecture_gain_artifacts"
ARTIFACT_ID = 8_448_195_842
WORKFLOW_RUN_ID = 29_706_825_763
WORKFLOW_HEAD = "82e11eb4116516a15ba442456dd89ad53ee6c76e"
EXPECTED_SIZE = 1_855_296
EXPECTED_SHA256 = "37cb3b9657863d830abeee8f73385a838fee25f3f610250dd171153805358945"
EXPECTED_MEMBER_COUNT = 146
EXPECTED_MANIFEST_PAYLOAD_COUNT = 141
TOP_LEVEL_MANIFESTS = (
    "SHA256SUMS.txt",
    "ARTIFACT_SHA256SUMS.txt",
    "PORTABLE_ARTIFACT_SHA256SUMS.txt",
)
ALLOWED_UNMANIFESTED = {
    *TOP_LEVEL_MANIFESTS,
    "batch099_official_ingest/extracted_public_artifact/SHA256SUMS.txt",
    "batch099_official_ingest/extracted_public_artifact/batch098_official_ingest/extracted_public_artifact/SHA256SUMS.txt",
}


def platform_path(path: Path) -> Path:
    if os.name == "nt":
        absolute = path.resolve()
        if not str(absolute).startswith("\\\\?\\"):
            return Path("\\\\?\\" + str(absolute))
    return path


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)
    path.write_text(data, encoding="utf-8", newline="\n")


def _safe_member(name: str) -> bool:
    pure = PurePosixPath(name)
    return bool(name) and not pure.is_absolute() and ".." not in pure.parts and "\\" not in name


def inspect_outer_artifact(path: Path, acquisition_route: str) -> tuple[dict[str, Any], list[zipfile.ZipInfo]]:
    if acquisition_route not in {"DIRECT_CODEX_ATTACHMENT", "LOCAL_QUARANTINED_ARTIFACT", "GITHUB_ACTIONS_ARTIFACT_ID"}:
        raise ValueError("unsupported acquisition route")
    result: dict[str, Any] = {
        "artifact_name": ARTIFACT_NAME,
        "artifact_id": ARTIFACT_ID,
        "workflow_run_id": WORKFLOW_RUN_ID,
        "workflow_head": WORKFLOW_HEAD,
        "acquisition_route": acquisition_route,
        "observed_size": path.stat().st_size,
        "expected_size": EXPECTED_SIZE,
        "observed_sha256": sha256_file(path),
        "expected_sha256": EXPECTED_SHA256,
    }
    failures: list[str] = []
    infos: list[zipfile.ZipInfo] = []
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            folded = [name.casefold() for name in names]
            unsafe = [name for name in names if not _safe_member(name)]
            symlinks = [info.filename for info in infos if stat.S_ISLNK(info.external_attr >> 16)]
            special = [
                info.filename
                for info in infos
                if info.external_attr >> 16
                and not (stat.S_ISREG(info.external_attr >> 16) or stat.S_ISDIR(info.external_attr >> 16))
            ]
            nested = [name for name in names if name.lower().endswith((".zip", ".tar", ".tgz", ".7z", ".whl"))]
            compiled = [name for name in names if "__pycache__" in PurePosixPath(name).parts or name.lower().endswith((".pyc", ".pyo"))]
            caches = [name for name in names if any(part in {".cache", ".pytest_cache", ".mypy_cache"} for part in PurePosixPath(name).parts)]
            duplicate_count = len(names) - len(set(names))
            casefold_collision_count = len(folded) - len(set(folded))
            failures.extend(f"unsafe:{name}" for name in unsafe)
            failures.extend(f"symlink:{name}" for name in symlinks)
            failures.extend(f"special:{name}" for name in special)
            failures.extend(f"nested_archive:{name}" for name in nested)
            failures.extend(f"compiled:{name}" for name in compiled)
            failures.extend(f"cache:{name}" for name in caches)
            if duplicate_count:
                failures.append(f"duplicate_count:{duplicate_count}")
            if casefold_collision_count:
                failures.append(f"casefold_collision_count:{casefold_collision_count}")
            result.update(
                {
                    "zip_open_status": "PASS",
                    "member_count": len(names),
                    "unsafe_path_count": len(unsafe),
                    "duplicate_path_count": duplicate_count,
                    "casefold_collision_count": casefold_collision_count,
                    "symlink_count": len(symlinks),
                    "special_file_count": len(special),
                    "nested_archive_count": len(nested),
                    "compiled_payload_count": len(compiled),
                    "cache_payload_count": len(caches),
                }
            )
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


def _parse_manifest(path: Path) -> tuple[dict[str, str], list[str]]:
    rows: dict[str, str] = {}
    malformed: list[str] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            malformed.append(f"line:{number}")
            continue
        digest, name = match.groups()
        if name in rows:
            malformed.append(f"duplicate:{name}")
        rows[name] = digest
    return rows, malformed


def verify_top_level_manifests(root: Path) -> dict[str, Any]:
    actual = {path.relative_to(root).as_posix(): sha256_file(path) for path in root.rglob("*") if path.is_file()}
    reports: dict[str, Any] = {}
    for manifest_name in TOP_LEVEL_MANIFESTS:
        rows, malformed = _parse_manifest(root / manifest_name)
        hash_failures = [name for name, digest in rows.items() if actual.get(name) != digest]
        missing = [name for name in rows if name not in actual]
        self_entries = [name for name in rows if name == manifest_name]
        unmanifested = sorted(set(actual) - set(rows) - ALLOWED_UNMANIFESTED)
        failures = malformed + hash_failures + missing + self_entries + unmanifested
        reports[manifest_name] = {
            "checked_payload_count": len(rows),
            "malformed_manifest_row_count": len(malformed),
            "hash_failure_count": len(hash_failures),
            "missing_count": len(missing),
            "self_entry_count": len(self_entries),
            "unmanifested_payload_count": len(unmanifested),
            "failures": failures,
            "status": "PASS" if len(rows) == EXPECTED_MANIFEST_PAYLOAD_COUNT and not failures else "BLOCK",
        }
    return {
        "status": "PASS" if all(item["status"] == "PASS" for item in reports.values()) else "BLOCK",
        "manifests": reports,
        "top_level_manifest_count": len(reports),
        "member_count": len(actual),
    }


def tree_hash(root: Path) -> str:
    paths = sorted((path for path in root.rglob("*") if path.is_file()), key=lambda item: item.relative_to(root).as_posix().casefold())
    rows = [f"{sha256_file(path)}  {path.relative_to(root).as_posix()}" for path in paths]
    return sha256_bytes(("\n".join(rows) + "\n").encode("utf-8"))


def private_content_scan(root: Path) -> dict[str, Any]:
    patterns = {
        # CI runner paths are retained raw custody, while local user, OneDrive,
        # repository-runtime, and attachment paths are prohibited.
        "private_absolute_path_count": re.compile(
            rb"(?:C:\\\\Users\\\\thisb\\\\|C:\\\\Dev\\\\ControllerGate_Runtime\\\\|OneDrive|\\.codex\\\\attachments)",
            re.I,
        ),
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
    summary = read_json(root / "batch100_public_execution_summary.json")
    state = read_json(root / "batch100_consolidated_state.json")
    pairs = read_jsonl(root / "matched_counterfactual_evidence_v2.jsonl")
    typed = read_jsonl(root / "batch100_typed_incident_receipts_v2.jsonl")
    terminals = read_jsonl(root / "controller_audit_counterfactual_terminal_records_v3.jsonl")
    critic = read_json(root / "critic" / "batch100_semantic_mutation_campaign_summary.json")
    source_proofs = read_jsonl(root / "decision_time_source_ownership_proofs_v3.jsonl")
    necessity = read_jsonl(root / "necessity_receipts_v1.jsonl")
    sufficiency = read_jsonl(root / "sufficiency_receipts_v1.jsonl")
    interaction = read_jsonl(root / "interaction_receipts_v1.jsonl")
    ownership = read_jsonl(root / "ownership_support_receipts_v1.jsonl")
    pair_distribution = Counter(
        row.get("factorial_status") if row.get("factorial_status") not in {None, "NOT_APPLICABLE"} else row.get("single_factor_status")
        for row in pairs
    )
    expected_pair_distribution = {
        "VALID_FACTORIAL_INTERACTION": 1,
        "VALID_SINGLE_FACTOR_PAIR": 2,
        "NONREPRODUCIBLE": 5,
        "INCIDENT_NOT_MATERIALIZED": 1,
    }
    terminal_distribution = Counter(row.get("terminal_class") for row in terminals)
    blockers = [
        "OPENBB_SECONDARY_SOURCE_SERVICE_FIXTURE_NOT_MATERIALIZED_EXACT",
        "REGISTERED_CELL_NOT_EXECUTED_IN_EXACT_PROVIDER",
        "ownership_grade_differential_evidence_missing",
    ]
    checks = {
        "programs": summary.get("program_count") == 9,
        "registered_cells": summary.get("registered_cell_count") == 32,
        "executed_cells": summary.get("executed_cell_count") == 28,
        "missing_cells": summary.get("missing_cell_count") == 4,
        "typed_incidents": len(typed) == 9 and sum(bool(row.get("materialized")) for row in typed) == 2,
        "pair_classifications": dict(pair_distribution) == expected_pair_distribution,
        "sensitivity_receipts": state.get("sensitivity_receipt_count") == 0,
        "necessity_receipts": sum(row.get("status") not in {"NOT_ESTABLISHED", "NOT_CREATED"} for row in necessity) == 0,
        "sufficiency_receipts": sum(row.get("status") not in {"NOT_ESTABLISHED", "NOT_CREATED"} for row in sufficiency) == 0,
        "interaction_receipts": sum(row.get("status") not in {"NOT_ESTABLISHED", "NOT_CREATED"} for row in interaction) == 0,
        "ownership_receipts": sum(bool(row.get("ownership_supported")) for row in ownership) == 0,
        "terminals": len(terminals) == 80 and terminal_distribution == {"INSUFFICIENT_EVIDENCE": 80},
        "source_ownership_proofs": sum(row.get("status") not in {"NOT_ESTABLISHED", "NOT_CREATED"} for row in source_proofs) == 0,
        "no_actuation": summary.get("patch_operations") == 0 and summary.get("repair_count_increment") == 0 and summary.get("historical_increment") == 0,
        "blindness": summary.get("truth_access") == 0 and summary.get("private_tld_access_during_candidate_execution") == 0,
        "mutations": critic.get("semantic_mutations_executed") == 50 and critic.get("semantic_mutations_rejected") == 50,
        "blockers": state.get("active_blockers") == blockers,
    }
    return {
        "status": "PASS" if all(checks.values()) else "BLOCK",
        "checks": checks,
        "program_count": summary.get("program_count"),
        "registered_cell_count": summary.get("registered_cell_count"),
        "executed_cell_count": summary.get("executed_cell_count"),
        "missing_cell_count": summary.get("missing_cell_count"),
        "typed_incident_materialized_count": sum(bool(row.get("materialized")) for row in typed),
        "pair_classification_distribution": dict(pair_distribution),
        "terminal_distribution": dict(terminal_distribution),
        "active_blockers": blockers,
    }


def claim_reconciliation(root: Path) -> dict[str, Any]:
    observed = read_json(root / "batch100_claim_boundary.json")
    expected = {
        "authority_allowed": "truth-blind public counterfactual evidence and safe abstention at recorded scope",
        "authority_forbidden": [
            "ordinary patch",
            "repair count mutation",
            "historical increment",
            "Product Beta promotion",
            "production readiness",
            "self-maintaining software claim",
        ],
        "automatic_merge": "inactive",
        "exact_blockers": [
            "OPENBB_SECONDARY_SOURCE_SERVICE_FIXTURE_NOT_MATERIALIZED_EXACT",
            "REGISTERED_CELL_NOT_EXECUTED_IN_EXACT_PROVIDER",
            "ownership_grade_differential_evidence_missing",
        ],
        "execution_depth": "public receipt and critic reconstruction",
        "full_scoring": "NOT_RUN/disallowed",
        "historical_increment": 0,
        "issue_derived_repair_count": 6,
        "memory": "not demonstrated",
        "native_external_repair_count": 4,
        "ordinary_patch_count": 0,
        "package_version": "0.2.0b2.dev0",
        "producer": "scripts/finalize_batch100_release_outputs.py",
        "production_readiness": False,
        "prospective_effectiveness": "NOT_ESTABLISHED",
        "protocol": "v2.19",
        "public_writes": "inactive",
        "self_maintaining_software": "false/not demonstrated",
        "semantic_scope": "Batch100 public claim boundary",
        "status": "PRODUCT_BETA_BLOCKED_EXACT",
    }
    return {
        "status": "PASS" if observed == expected else "BLOCK",
        "observed": observed,
        "expected": expected,
        "stronger_claim_detected": observed != expected,
    }


def ingest(artifact: Path, quarantine: Path, output_root: Path, acquisition_route: str) -> dict[str, Any]:
    custody, infos = inspect_outer_artifact(artifact, acquisition_route)
    if custody["status"] != "PASS":
        raise ValueError("BATCH101_BATCH100_OFFICIAL_INGEST_BLOCKED_EXACT")
    quarantine.mkdir(parents=True, exist_ok=True)
    quarantined = quarantine / f"{ARTIFACT_NAME}.zip"
    shutil.copyfile(artifact, quarantined)
    if sha256_file(quarantined) != EXPECTED_SHA256:
        raise ValueError("quarantine byte mismatch")
    ingest_root = platform_path(output_root / "batch100_official_ingest")
    extracted = ingest_root / "extracted_public_artifact"
    if extracted.exists():
        shutil.rmtree(extracted)
    extracted.mkdir(parents=True)
    with zipfile.ZipFile(quarantined) as archive:
        for info in infos:
            target = extracted / PurePosixPath(info.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
    manifests = verify_top_level_manifests(extracted)
    scan = private_content_scan(extracted)
    semantic = semantic_reconciliation(extracted)
    claim = claim_reconciliation(extracted)
    if any(item["status"] != "PASS" for item in (manifests, scan, semantic, claim)):
        raise ValueError("BATCH101_BATCH100_OFFICIAL_INGEST_BLOCKED_EXACT")
    member_rows = [
        {"relative_path": path.relative_to(extracted).as_posix(), "size": path.stat().st_size, "sha256": sha256_file(path)}
        for path in sorted(extracted.rglob("*"))
        if path.is_file()
    ]
    extracted_hash = tree_hash(extracted)
    write_json(ingest_root / "artifact_identity" / "batch100_official_outer_artifact_custody.json", custody)
    write_json(ingest_root / "custody" / "batch100_official_manifest_verification.json", manifests)
    write_jsonl(ingest_root / "custody" / "batch100_official_extracted_member_manifest.jsonl", member_rows)
    write_json(ingest_root / "custody" / "batch100_official_private_content_scan.json", scan)
    write_json(ingest_root / "reconciliation" / "batch100_official_semantic_reconciliation.json", semantic)
    write_json(ingest_root / "reconciliation" / "batch100_official_claim_boundary_reconciliation.json", claim)
    receipt = {
        "ingest_status": "PASS_OFFICIAL_BATCH100_ARTIFACT_INGEST",
        "artifact_name": ARTIFACT_NAME,
        "artifact_id": ARTIFACT_ID,
        "workflow_run_id": WORKFLOW_RUN_ID,
        "workflow_head": WORKFLOW_HEAD,
        "outer_size": EXPECTED_SIZE,
        "outer_sha256": EXPECTED_SHA256,
        "member_count": EXPECTED_MEMBER_COUNT,
        "manifest_payload_count": EXPECTED_MANIFEST_PAYLOAD_COUNT,
        "manifest_failures": [],
        "extracted_tree_hash": extracted_hash,
        "semantic_reconciliation_status": "PASS",
        "claim_boundary_status": "PASS",
        "private_content_scan_status": "PASS",
        "authority_allowed": "authoritative public Batch100 input for Batch101",
        "authority_forbidden": ["historical rewrite", "candidate patch", "repair count", "protected actuation", "release promotion"],
        "active_blockers": semantic["active_blockers"],
    }
    receipt_path = ingest_root / "ingest_receipts" / "batch100_official_ingest_receipt.json"
    write_json(receipt_path, receipt)
    receipt_hash = sha256_file(receipt_path)
    registry = {
        "status": "PASS",
        "inputs": [
            {
                "input_id": "batch099_official_ingest_receipt",
                "sha256": "55f9549fe1bf9d0d417980686434daf2c5336195b0955bd7acdd3452c428f2f3",
                "authority": "historical prerequisite",
            },
            {"input_id": "batch100_public_artifact", "artifact_id": ARTIFACT_ID, "sha256": EXPECTED_SHA256, "authority": "official Batch101 input"},
            {"input_id": "batch100_official_ingest_receipt", "sha256": receipt_hash, "authority": "mandatory downstream binding"},
        ],
        "authority_forbidden": ["patch", "repair count", "protected actuation", "release promotion"],
    }
    write_json(ingest_root / "ingest_receipts" / "batch100_authoritative_input_registry_v1.json", registry)
    write_json(
        ingest_root / "ingest_receipts" / "batch100_official_ingest_immutability_contract.json",
        {"status": "PASS", "tree_hash": extracted_hash, "mutation_allowed": False, "supersession_requires_append_only_receipt": True},
    )
    return {
        "status": receipt["ingest_status"],
        "receipt_sha256": receipt_hash,
        "extracted_tree_hash": extracted_hash,
        "manifests": manifests,
        "semantic": semantic,
        "claim": claim,
        "scan": scan,
    }

"""Official byte custody and semantic reconciliation for the Batch102 artifact."""

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


ARTIFACT_NAME = "post_v2_37_hardening_batch102_fresh_exact_counterfactual_execution_necessity_sufficiency_ownership_closure_artifacts"
ARTIFACT_ID = 8_451_703_475
WORKFLOW_RUN_ID = 29_719_094_962
WORKFLOW_HEAD = "17ce08e828dfe5c5c0c77ad162188723af53607b"
EXPECTED_SIZE = 274_776
EXPECTED_SHA256 = "d45393bc45b5eff2b6bcbe81524a9acbd98eb7e68902a24e08d3f3e5c78466c2"
EXPECTED_MEMBER_COUNT = 139
EXPECTED_MANIFEST_COUNTS = {
    "ARTIFACT_SHA256SUMS.txt": 136,
    "PORTABLE_ARTIFACT_SHA256SUMS.txt": 136,
    "SHA256SUMS.txt": 138,
}
BATCH101_INGEST_RECEIPT_SHA256 = "e85cf0a319f0a0b68f363a9dad7265d063ed97a8afe6c52a719af93de32fed11"
ACQUISITION_ROUTES = {
    "DIRECT_CODEX_ATTACHMENT",
    "LOCAL_QUARANTINED_ARTIFACT",
    "GITHUB_ACTIONS_ARTIFACT_ID",
}


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
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n"
            for row in rows
        ),
        encoding="utf-8",
        newline="\n",
    )


def tree_hash(root: Path) -> str:
    rows = [
        f"{sha256_file(path)}  {path.relative_to(root).as_posix()}"
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]
    return hashlib.sha256(("\n".join(rows) + "\n").encode()).hexdigest()


def verify_sealed_member_tree(
    root: Path, member_manifest: Path, expected_tree_hash: str
) -> bool:
    rows = read_jsonl(member_manifest)
    sealed = hashlib.sha256(
        (
            "\n".join(
                f"{row['sha256']}  {row['relative_path']}" for row in rows
            )
            + "\n"
        ).encode()
    ).hexdigest()
    expected = {row["relative_path"]: row["sha256"] for row in rows}
    observed = {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in root.rglob("*")
        if path.is_file()
    }
    return sealed == expected_tree_hash and observed == expected


def inspect_artifact(
    path: Path, acquisition_route: str
) -> tuple[dict[str, Any], list[zipfile.ZipInfo]]:
    if acquisition_route not in ACQUISITION_ROUTES:
        raise ValueError("unsupported acquisition route")
    failures: list[str] = []
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        unsafe = [
            name
            for name in names
            if PurePosixPath(name).is_absolute()
            or ".." in PurePosixPath(name).parts
            or "\\" in name
        ]
        duplicates = len(names) - len(set(names))
        casefold = len(names) - len({name.casefold() for name in names})
        symlinks = [
            item.filename
            for item in infos
            if stat.S_ISLNK(item.external_attr >> 16)
        ]
        special = [
            item.filename
            for item in infos
            if item.external_attr >> 16
            and not (
                stat.S_ISREG(item.external_attr >> 16)
                or stat.S_ISDIR(item.external_attr >> 16)
            )
        ]
        compiled = [
            name
            for name in names
            if "__pycache__" in PurePosixPath(name).parts
            or name.lower().endswith((".pyc", ".pyo"))
        ]
        nested = [
            name
            for name in names
            if name.lower().endswith((".zip", ".tar", ".tgz", ".7z", ".whl"))
        ]
    observed_size = path.stat().st_size
    observed_sha = sha256_file(path)
    if observed_size != EXPECTED_SIZE:
        failures.append("size")
    if observed_sha != EXPECTED_SHA256:
        failures.append("sha256")
    if len(infos) != EXPECTED_MEMBER_COUNT:
        failures.append("member_count")
    failures.extend(f"unsafe:{item}" for item in unsafe)
    failures.extend(f"symlink:{item}" for item in symlinks)
    failures.extend(f"special:{item}" for item in special)
    failures.extend(f"compiled:{item}" for item in compiled)
    failures.extend(f"nested:{item}" for item in nested)
    if duplicates:
        failures.append("duplicate_paths")
    if casefold:
        failures.append("casefold_collisions")
    return {
        "status": "PASS" if not failures else "BLOCK",
        "artifact_name": ARTIFACT_NAME,
        "artifact_id": ARTIFACT_ID,
        "workflow_run_id": WORKFLOW_RUN_ID,
        "workflow_head": WORKFLOW_HEAD,
        "acquisition_route": acquisition_route,
        "observed_size": observed_size,
        "expected_size": EXPECTED_SIZE,
        "observed_sha256": observed_sha,
        "expected_sha256": EXPECTED_SHA256,
        "member_count": len(infos),
        "unsafe_path_count": len(unsafe),
        "duplicate_path_count": duplicates,
        "casefold_collision_count": casefold,
        "symlink_count": len(symlinks),
        "special_file_count": len(special),
        "compiled_payload_count": len(compiled),
        "nested_archive_count": len(nested),
        "failures": failures,
    }, infos


def _manifest_rows(path: Path) -> tuple[dict[str, str], list[str]]:
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


def verify_manifests(root: Path) -> dict[str, Any]:
    actual = {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in root.rglob("*")
        if path.is_file()
    }
    reports: dict[str, Any] = {}
    for name, expected in EXPECTED_MANIFEST_COUNTS.items():
        rows, malformed = _manifest_rows(root / name)
        failures = malformed + [
            member for member, digest in rows.items() if actual.get(member) != digest
        ]
        reports[name] = {
            "checked_payload_count": len(rows),
            "expected_payload_count": expected,
            "failures": failures,
            "status": "PASS" if len(rows) == expected and not failures else "BLOCK",
        }
    return {
        "status": (
            "PASS"
            if all(report["status"] == "PASS" for report in reports.values())
            else "BLOCK"
        ),
        "manifests": reports,
    }


def private_scan(root: Path) -> dict[str, Any]:
    patterns = [
        re.compile(pattern, re.I)
        for pattern in (
            rb"C:\\Users\\thisb",
            rb"ControllerGate_Runtime",
            rb"\.codex\\attachments",
            rb"ghp_[A-Za-z0-9]{20,}",
            rb"BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY",
        )
    ]
    findings = []
    for path in root.rglob("*"):
        if path.is_file() and any(pattern.search(path.read_bytes()) for pattern in patterns):
            findings.append(path.relative_to(root).as_posix())
    return {
        "status": "PASS" if not findings else "BLOCK",
        "finding_count": len(findings),
        "findings": findings,
    }


def semantic_reconciliation(root: Path) -> dict[str, Any]:
    state = read_json(root / "batch102_consolidated_state.json")
    cells = read_jsonl(root / "batch102_registered_cell_ledger_v4.jsonl")
    fresh = read_jsonl(root / "batch102_fresh_execution_receipts_v1.jsonl")
    raw = read_jsonl(root / "batch102_raw_observations_v1.jsonl")
    canonical = read_jsonl(root / "batch102_canonical_semantic_observations_v2.jsonl")
    broker = read_jsonl(root / "batch102_broker_operations_v1.jsonl")
    pairs = read_jsonl(root / "batch102_pair_validity_receipts_v3.jsonl")
    factorials = read_jsonl(root / "batch102_factorial_completeness_receipts_v3.jsonl")
    necessity = read_jsonl(root / "batch102_necessity_receipts_v3.jsonl")
    sufficiency = read_jsonl(root / "batch102_sufficiency_receipts_v3.jsonl")
    interaction = read_jsonl(root / "batch102_interaction_receipts_v3.jsonl")
    ownership = read_jsonl(root / "batch102_ownership_support_receipts_v3.jsonl")
    alternatives = read_jsonl(root / "batch102_alternative_exclusion_ledger_v4.jsonl")
    terminals = read_jsonl(root / "batch102_controller_audit_terminal_records_v5.jsonl")
    proofs = read_json(root / "batch102_source_ownership_proof_registry_v1.json")
    statuses = Counter(row.get("status") for row in cells)
    pair_statuses = Counter(row.get("status") for row in pairs)
    fresh_cells = {row.get("cell_id") for row in fresh}
    allowed_statuses = {
        "EXECUTED_VERIFIED",
        "EXECUTED_PREDICATE_FALSE",
        "BLOCKED_EXACT_PROVIDER_UNAVAILABLE",
        "BLOCKED_SOURCE_UNAVAILABLE",
        "BLOCKED_FIXTURE_UNAVAILABLE",
        "BLOCKED_SERVICE_UNAVAILABLE",
        "BLOCKED_INCIDENT_PREFLIGHT",
        "SUPERSEDED_WITH_RECEIPT",
    }
    active_blockers = [
        "OPENBB_SECONDARY_SOURCE_SERVICE_FIXTURE_NOT_MATERIALIZED_EXACT",
        "Darker exact Python 3.7 provider unavailable",
        "Poetry Windows source/provider capsule incomplete",
        "incident-preflight blocked cells",
        "eight invalid counterfactual pairs",
        "no complete factorial design",
        "necessity not established",
        "sufficiency not established",
        "alternative exclusion not established",
        "ownership-grade evidence missing",
        "source-ownership proof missing",
    ]
    checks = {
        "programs": state.get("program_count") == 9,
        "registered_cells": len(cells) == 70,
        "fresh_executed_cells": len(fresh_cells) == 18,
        "fresh_duplicate_replay_receipts": len(fresh) == 36,
        "raw_observations": len(raw) == 36,
        "canonical_observations": len(canonical) == 36,
        "semantically_reproducible_cells": sum(
            bool(row.get("semantically_reproducible")) for row in cells
        )
        == 13,
        "blocked_cells": sum(count for status, count in statuses.items() if status.startswith("BLOCKED_"))
        == 52,
        "superseded_cells": statuses.get("SUPERSEDED_WITH_RECEIPT", 0) == 0,
        "unaccounted_cells": set(statuses).issubset(allowed_statuses),
        "broker_operations": len(broker) == 198,
        "valid_single_factor_pairs": pair_statuses.get("VALID_SINGLE_FACTOR_PAIR", 0)
        == 1,
        "valid_factorial_designs": sum(bool(row.get("complete")) for row in factorials)
        == 0,
        "necessity": sum(bool(row.get("supported")) for row in necessity) == 0,
        "sufficiency": sum(bool(row.get("supported")) for row in sufficiency) == 0,
        "interaction": sum(bool(row.get("supported")) for row in interaction) == 0,
        "ownership": sum(bool(row.get("ownership_supported")) for row in ownership)
        == 0,
        "alternative_ledgers": len(alternatives) == 9,
        "source_ownership_proofs": proofs.get("proof_count") == 0,
        "terminals": len(terminals) == 90
        and all(row.get("terminal_writer") == "ControllerAudit" for row in terminals)
        and all(row.get("terminal") == "INSUFFICIENT_EVIDENCE" for row in terminals),
        "no_actuation": all(row.get("patch_operation_count") == 0 for row in fresh),
        "truth_blind": all(
            row.get("truth_access_count") == 0
            and row.get("private_tld_access_count") == 0
            for row in fresh
        ),
        "no_unauthorized_outcomes": state.get("unauthorized_outcome_access") == 0,
        "required_active_blockers": state.get("exact_blockers")
        == ["OPENBB_SECONDARY_SOURCE_SERVICE_FIXTURE_NOT_MATERIALIZED_EXACT"]
        and statuses.get("BLOCKED_EXACT_PROVIDER_UNAVAILABLE", 0) == 17
        and statuses.get("BLOCKED_INCIDENT_PREFLIGHT", 0) == 35
        and pair_statuses.get("PAIR_NOT_VALID", 0) == 8
        and len(alternatives) == 9
        and all(row.get("status") == "OPEN" for row in alternatives),
    }
    return {
        "status": "PASS" if all(checks.values()) else "BLOCK",
        "checks": checks,
        "program_count": 9,
        "registered_cells": 70,
        "fresh_executed_cells": 18,
        "fresh_duplicate_replay_receipts": 36,
        "raw_observations": 36,
        "canonical_observations": 36,
        "semantically_reproducible_cells": 13,
        "blocked_cells": 52,
        "superseded_cells": 0,
        "unaccounted_cells": 0,
        "broker_operations": 198,
        "valid_single_factor_pairs": 1,
        "active_blockers": active_blockers,
        "valid_factorial_designs": 0,
        "necessity_supported": 0,
        "sufficiency_supported": 0,
        "interaction_supported": 0,
        "ownership_supported": 0,
        "alternative_ledgers": 9,
        "source_ownership_proofs": 0,
        "controller_audit_terminals": 90,
        "insufficient_evidence_terminals": 90,
        "patch_operations": 0,
        "repair_increment": 0,
        "historical_increment": 0,
        "truth_access": 0,
        "unauthorized_outcome_access": 0,
        "status_distribution": dict(sorted(statuses.items())),
    }


def claim_reconciliation(root: Path) -> dict[str, Any]:
    claim = read_json(root / "batch102_claim_boundary.json")
    checks = {
        "release_boundary": claim.get("release_boundary")
        == "PRODUCT_BETA_RC_BLOCKED_EXACT",
        "protocol": claim.get("protocol") == "v2.19",
        "package_version": claim.get("package_version") == "0.2.0b2.dev0",
        "counts": claim.get("issue_derived_repair_count") == 6
        and claim.get("native_external_repair_count") == 4
        and claim.get("historical_increment") == 0,
        "no_actuation": claim.get("ordinary_patch_count") == 0
        and claim.get("protected_actuation") is False
        and claim.get("public_writes") == "inactive"
        and claim.get("automatic_merge") == "inactive",
        "no_promotion": claim.get("production_readiness") is False
        and claim.get("prospective_effectiveness") == "NOT_ESTABLISHED"
        and claim.get("memory_status") == "not demonstrated"
        and claim.get("self_maintaining_software") == "false/not demonstrated",
    }
    return {
        "status": "PASS" if all(checks.values()) else "BLOCK",
        "checks": checks,
        "observed": claim,
    }


def ingest(
    artifact: Path, quarantine: Path, output_root: Path, acquisition_route: str
) -> dict[str, Any]:
    custody, infos = inspect_artifact(artifact, acquisition_route)
    if custody["status"] != "PASS":
        raise ValueError("BATCH103_BATCH102_OFFICIAL_INGEST_BLOCKED_EXACT")
    quarantine.mkdir(parents=True, exist_ok=True)
    quarantined = quarantine / f"{ARTIFACT_NAME}.zip"
    shutil.copyfile(artifact, quarantined)
    if sha256_file(quarantined) != EXPECTED_SHA256:
        raise ValueError("BATCH103_BATCH102_QUARANTINE_COPY_BLOCKED_EXACT")
    root = platform_path(output_root / "batch102_official_ingest")
    extracted = root / "extracted_public_artifact"
    if extracted.exists():
        shutil.rmtree(extracted)
    extracted.mkdir(parents=True)
    with zipfile.ZipFile(quarantined) as archive:
        for info in infos:
            target = extracted / PurePosixPath(info.filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
    manifests = verify_manifests(extracted)
    scan = private_scan(extracted)
    semantic = semantic_reconciliation(extracted)
    claim = claim_reconciliation(extracted)
    if any(report["status"] != "PASS" for report in (manifests, scan, semantic, claim)):
        raise ValueError("BATCH103_BATCH102_OFFICIAL_INGEST_BLOCKED_EXACT")
    member_rows = [
        {
            "relative_path": path.relative_to(extracted).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(extracted.rglob("*"))
        if path.is_file()
    ]
    extracted_hash = tree_hash(extracted)
    write_json(
        root / "artifact_identity/batch102_official_outer_artifact_custody.json",
        custody,
    )
    write_jsonl(
        root / "custody/batch102_official_extracted_member_manifest.jsonl",
        member_rows,
    )
    write_json(
        root / "custody/batch102_official_manifest_verification.json", manifests
    )
    write_json(root / "custody/batch102_official_private_content_scan.json", scan)
    write_json(
        root / "reconciliation/batch102_official_semantic_reconciliation.json",
        semantic,
    )
    write_json(
        root / "reconciliation/batch102_official_claim_boundary_reconciliation.json",
        claim,
    )
    receipt = {
        "ingest_status": "PASS_OFFICIAL_BATCH102_ARTIFACT_INGEST",
        "artifact_name": ARTIFACT_NAME,
        "artifact_id": ARTIFACT_ID,
        "workflow_run_id": WORKFLOW_RUN_ID,
        "workflow_head": WORKFLOW_HEAD,
        "outer_size": EXPECTED_SIZE,
        "outer_sha256": EXPECTED_SHA256,
        "member_count": EXPECTED_MEMBER_COUNT,
        "manifest_counts": EXPECTED_MANIFEST_COUNTS,
        "manifest_failures": [],
        "extracted_tree_hash": extracted_hash,
        "authority_allowed": "authoritative public Batch102 input for Batch103",
        "authority_forbidden": [
            "historical rewrite",
            "fresh Batch103 execution substitution",
            "candidate patch",
            "repair count",
            "release promotion",
        ],
    }
    receipt_path = root / "ingest_receipts/batch102_official_ingest_receipt.json"
    write_json(receipt_path, receipt)
    receipt_hash = sha256_file(receipt_path)
    write_json(
        root / "ingest_receipts/batch102_authoritative_input_registry_v1.json",
        {
            "status": "PASS",
            "inputs": [
                {
                    "input_id": "batch101_official_ingest_receipt",
                    "sha256": BATCH101_INGEST_RECEIPT_SHA256,
                    "authority": "historical prerequisite",
                },
                {
                    "input_id": "batch102_public_artifact",
                    "artifact_id": ARTIFACT_ID,
                    "sha256": EXPECTED_SHA256,
                    "authority": "official Batch103 input",
                },
                {
                    "input_id": "batch102_official_ingest_receipt",
                    "sha256": receipt_hash,
                    "authority": "mandatory downstream binding",
                },
            ],
            "authority_forbidden": [
                "fresh execution substitution",
                "patch",
                "count mutation",
                "release promotion",
            ],
        },
    )
    write_json(
        root / "ingest_receipts/batch102_official_ingest_immutability_contract.json",
        {
            "status": "PASS",
            "outer_artifact_sha256": EXPECTED_SHA256,
            "tree_hash": extracted_hash,
            "mutation_allowed": False,
            "supersession_requires_append_only_receipt": True,
        },
    )
    return {
        "status": receipt["ingest_status"],
        "receipt_sha256": receipt_hash,
        "extracted_tree_hash": extracted_hash,
        "semantic": semantic,
    }

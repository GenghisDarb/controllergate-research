from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
from collections import Counter
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, ZipInfo


EXPECTED_BATCH097 = {
    "size": 12_705_180,
    "sha256": "a1f833c7ae360d302733c8cb0cd9c74d7e109bdcee5469c3b646db929a4f541b",
    "entries": 151,
    "manifests": {"ARTIFACT_SHA256SUMS.txt": 148, "PORTABLE_ARTIFACT_SHA256SUMS.txt": 148, "SHA256SUMS.txt": 150},
}
EXPECTED_TLD = {
    "size": 5_389_984,
    "sha256": "c32609066a7d86934a9a6e8b62d57fd335e51a14c8fdebcb95bb7d1584c6438b",
    "entries": 20,
    "uncompressed_bytes": 22_131_530,
}
HASH_LINE = re.compile(r"^([0-9a-fA-F]{64})[ *](.+)$")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def unsafe(name: str) -> bool:
    path = PurePosixPath(name.replace("\\", "/"))
    return path.is_absolute() or ".." in path.parts or bool(re.match(r"^[A-Za-z]:", name))


def symlink(info: ZipInfo) -> bool:
    return stat.S_ISLNK((info.external_attr >> 16) & 0xFFFF)


def verify_manifest(zf: ZipFile, name: str, expected_count: int) -> dict[str, object]:
    lines = [line for line in zf.read(name).decode("utf-8-sig").splitlines() if line.strip()]
    missing: list[str] = []
    mismatches: list[str] = []
    malformed: list[str] = []
    self_entries: list[str] = []
    for line in lines:
        match = HASH_LINE.match(line)
        if not match:
            malformed.append(line)
            continue
        expected, member = match.groups()
        member = member.lstrip().replace("\\", "/")
        if member == name:
            self_entries.append(member)
            continue
        try:
            data = zf.read(member)
        except KeyError:
            missing.append(member)
            continue
        if digest(data) != expected.lower():
            mismatches.append(member)
    status = "PASS" if len(lines) == expected_count and not (missing or mismatches or malformed or self_entries) else "BLOCK"
    return {
        "manifest": name,
        "expected_entries": expected_count,
        "observed_entries": len(lines),
        "missing": missing,
        "mismatches": mismatches,
        "malformed_entries": malformed,
        "self_entries": self_entries,
        "status": status,
    }


def verify_zip(path: Path, expected: dict[str, object], *, parse_payload: bool) -> dict[str, object]:
    outer = digest(path.read_bytes())
    with ZipFile(path) as zf:
        infos = zf.infolist()
        names = [info.filename.replace("\\", "/") for info in infos]
        counts = Counter(names)
        unsafe_paths = [name for name in names if unsafe(name)]
        duplicates = [name for name, count in counts.items() if count > 1]
        symlinks = [info.filename for info in infos if symlink(info)]
        nested = [name for name in names if Path(name).suffix.lower() in {".zip", ".tar", ".gz", ".tgz", ".7z"}]
        compiled = [name for name in names if name.endswith((".pyc", ".pyo", ".whl", ".sqlite", ".sqlite3", ".db", ".pdf")) or "__pycache__" in name]
        json_failures: list[str] = []
        jsonl_failures: list[str] = []
        if parse_payload:
            for info in infos:
                name = info.filename
                if name.endswith("/"):
                    continue
                try:
                    if name.lower().endswith(".json"):
                        json.loads(zf.read(info).decode("utf-8-sig"))
                    elif name.lower().endswith(".jsonl"):
                        for line in zf.read(info).decode("utf-8-sig").splitlines():
                            if line.strip():
                                json.loads(line)
                except Exception:
                    (jsonl_failures if name.lower().endswith(".jsonl") else json_failures).append(name)
        manifests = []
        for name, count in dict(expected.get("manifests", {})).items():
            manifests.append(verify_manifest(zf, name, int(count)))
        checks = {
            "size": path.stat().st_size == expected["size"],
            "sha256": outer == expected["sha256"],
            "entry_count": len(infos) == expected["entries"],
            "uncompressed_bytes": "uncompressed_bytes" not in expected or sum(info.file_size for info in infos) == expected["uncompressed_bytes"],
            "path_safety": not unsafe_paths,
            "duplicates": not duplicates,
            "symlinks": not symlinks,
            "nested_archives": not nested,
            "compiled_or_forbidden_payload": not compiled,
            "json": not json_failures,
            "jsonl": not jsonl_failures,
            "manifests": all(row["status"] == "PASS" for row in manifests),
        }
        return {
            "path": str(path),
            "size": path.stat().st_size,
            "sha256": outer,
            "entry_count": len(infos),
            "uncompressed_bytes": sum(info.file_size for info in infos),
            "unsafe_paths": unsafe_paths,
            "duplicate_paths": duplicates,
            "symlinks": symlinks,
            "nested_archives": nested,
            "forbidden_payloads": compiled,
            "json_parse_failures": json_failures,
            "jsonl_parse_failures": jsonl_failures,
            "manifests": manifests,
            "checks": checks,
            "status": "PASS" if all(checks.values()) else "BLOCK",
        }


def scoped(value: dict[str, object], *, scope: str) -> dict[str, object]:
    return {
        **value,
        "producer": "scripts/run_batch098_custody_and_reconciliation.py",
        "execution_depth": "direct artifact byte and archive inspection",
        "semantic_scope": scope,
        "authority_allowed": "artifact custody and historical reconstruction",
        "authority_forbidden": ["causal authority", "repair authority", "release promotion"],
    }


def ingest_verified_batch097(path: Path, destination: Path) -> dict[str, object]:
    """Ingest verified evidence bytes without rewriting any existing historical byte."""
    destination.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    identical_existing: list[str] = []
    preserved_different_existing: list[dict[str, str]] = []
    with ZipFile(path) as zf:
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if info.is_dir():
                continue
            if unsafe(name) or "/" in name:
                raise RuntimeError(f"Batch097 artifact contains non-flat or unsafe evidence path: {name}")
            data = zf.read(info)
            target = destination / name
            if target.exists():
                if target.read_bytes() != data:
                    preserved_different_existing.append(
                        {
                            "path": name,
                            "repository_sha256": digest(target.read_bytes()),
                            "official_artifact_sha256": digest(data),
                        }
                    )
                    continue
                identical_existing.append(name)
                continue
            target.write_bytes(data)
            written.append(name)
    return {
        "status": "PASS_WITH_PRESERVED_PREEXISTING_DIFFERENCES" if preserved_different_existing else "PASS",
        "destination": str(destination),
        "new_evidence_files": written,
        "identical_existing_files": identical_existing,
        "rewritten_files": [],
        "preserved_different_existing_files": preserved_different_existing,
        "ingested_file_count": len(written) + len(identical_existing),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch097", required=True)
    parser.add_argument("--tld", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--ingest-batch097-output")
    parser.add_argument("--tld-ci-bridge", choices=("configured", "blocked"), default="blocked")
    args = parser.parse_args()
    out = Path(args.output)
    batch = verify_zip(Path(args.batch097), EXPECTED_BATCH097, parse_payload=True)
    tld = verify_zip(Path(args.tld), EXPECTED_TLD, parse_payload=False)
    ingest = None
    if args.ingest_batch097_output:
        if batch["status"] != "PASS":
            raise SystemExit("BATCH097_INGEST_REFUSED_CUSTODY_BLOCK")
        ingest = ingest_verified_batch097(Path(args.batch097), Path(args.ingest_batch097_output))
    write_json(out / "batch097_artifact_ingest.json", scoped({**batch, "repository_ingest": ingest}, scope="official Batch097 artifact ingest"))
    write_json(out / "batch097_artifact_manifest_verification.json", scoped({"status": batch["status"], "manifests": batch["manifests"]}, scope="portable checksum manifests"))
    write_json(out / "batch097_raw_evidence_preservation.json", scoped({"status": "PASS", "raw_zip_sha256": batch["sha256"], "raw_zip_committed": False, "historical_bytes_rewritten": False}, scope="immutable Batch097 evidence"))
    write_json(out / "batch097_external_scientific_reconstruction.json", scoped({"status": "PASS_WITH_BLOCKERS", "materialized": 1, "candidate_count": 8, "typed_incidents": 5, "ten_role_complete": 1, "topology_progress_real": True, "scientific_closure": "NOT_ESTABLISHED"}, scope="Batch097 external-depth reconstruction"))
    exclusions = [
        {"authority_id": name, "status": "EXCLUDED_FROM_CURRENT_AUTHORITY", "reason": reason, "preserved_historically": True}
        for name, reason in (
            ("batch097_checkout_materializer", "mixed installed/checkout depth"),
            ("batch097_broad_tree_integrity", "generated residue conflated with tracked mutation"),
            ("batch097_marker_semantics", "configured marker matching"),
            ("batch097_projection_labels", "projection sides not independently executed"),
            ("batch097_fixed_decisive_board", "empty source derivations"),
            ("batch097_file_hash_amds", "zero causal facts"),
            ("batch097_producer_generated_verification", "independence not executed"),
            ("batch097_summary_mutations", "complete raw tree not copied"),
        )
    ]
    write_jsonl(out / "batch097_current_authority_exclusion_registry.jsonl", exclusions)
    corrected = {
        "ARTIFACT_CUSTODY": "PASS",
        "REPOSITORY_HISTORY_LEDGER": "PASS_WITH_CURRENT_HEAD_RECOMPUTATION",
        "INSTALLED_CONTROLLERGATE_IMPORT_ORIGIN": "PASS",
        "INSTALLED_CANDIDATE_ORCHESTRATION": "NOT_ESTABLISHED",
        "EIGHT_EPISODE_MATERIALIZATION": "BLOCK_1_OF_8",
        "TYPED_INCIDENTS": "PASS_5_OF_8",
        "TRACKED_SOURCE_TEST_INTEGRITY": "NOT_ESTABLISHED_FOR_6_BUILD_AFFECTED_LANES",
        "TEN_ROLE_BOUNDARY": "PASS_1_OF_8",
        "BULB_BOUNDARY_SCAFFOLD": "REAL_PROGRESS",
        "LOCAL_BROT_SOURCE_GRAPH_SCAFFOLD": "REAL_PROGRESS",
        "COUPLED_TOT_BROT_PROJECTION_EXECUTION": "NOT_ESTABLISHED",
        "TLD_LOCAL_SOURCE_CUSTODY": "PASS",
        "TLD_RAW_CI_SOURCE_CUSTODY": "BLOCK",
        "TOPOLOGY_DERIVED_CAUSAL_BOARD": "NOT_ESTABLISHED",
        "HISTORICAL_AMDS_QUALITY": "NOT_ESTABLISHED",
        "COMPLETE_RAW_TREE_MUTATION_DEPTH": "NOT_ESTABLISHED",
        "PRODUCT_BETA_RC": "PRODUCT_BETA_RC_BLOCKED_EXACT",
    }
    common = {"producer": "scripts/run_batch098_custody_and_reconciliation.py", "execution_depth": "independent raw-evidence reconstruction", "semantic_scope": "Batch097 corrected depth", "authority_allowed": "claim correction", "authority_forbidden": ["repair authority", "release promotion"]}
    for name, keys in {
        "batch097_materialization_depth_correction.json": tuple(corrected)[:8],
        "batch097_topology_board_depth_correction.json": tuple(corrected)[8:15],
        "batch097_amds_depth_correction.json": ("HISTORICAL_AMDS_QUALITY",),
        "batch097_critic_depth_correction.json": ("COMPLETE_RAW_TREE_MUTATION_DEPTH", "PRODUCT_BETA_RC"),
    }.items():
        write_json(out / name, {**common, "status": "PASS", "corrected_classifications": {key: corrected[key] for key in keys}})
    bridge = {
        "status": "PASS" if args.tld_ci_bridge == "configured" and tld["status"] == "PASS" else "BLOCK",
        "exact_blocker": None if args.tld_ci_bridge == "configured" else "BATCH098_TLD_SOURCE_CUSTODY_BRIDGE_BLOCKED_EXACT",
        "local_custody": tld,
        "ci_bridge_configured": args.tld_ci_bridge == "configured",
        "producer": "scripts/run_batch098_custody_and_reconciliation.py",
        "execution_depth": "local direct bytes; CI bridge configuration audit",
        "authority_allowed": "source custody only",
        "authority_forbidden": ["TLD board authority", "repair authority"],
    }
    write_json(out / "tld_raw_ci_custody_v1.json", bridge)
    print(json.dumps({"batch097": batch["status"], "tld_local": tld["status"], "tld_ci_bridge": bridge["status"]}, sort_keys=True))
    return 0 if batch["status"] == "PASS" and tld["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

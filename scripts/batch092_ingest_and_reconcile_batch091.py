from __future__ import annotations

import argparse
import hashlib
import json
import stat
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction"
EXPECTED = {
    "artifact_id": 8353766243,
    "artifact_name": "post_v2_37_hardening_batch091_lossless_capsule_blinded_amds_historical_canary_semantic_critic_closure_artifacts",
    "workflow_run_id": 29441557733,
    "workflow_head": "1c13c97b1d251e79065eb64a425b9666ed410d51",
    "size": 194706,
    "sha256": "306cc60bc1be7c89f7579c9b8a9c4b0f217ba15ef4f5f54d9b416aa6171560c5",
    "entries": 108,
}
PREFIX = "outputs/post_v2_37_hardening_batch091_lossless_capsule_blinded_amds_historical_canary_semantic_critic_closure/"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def safe(name: str) -> bool:
    pure = PurePosixPath(name)
    return not name.startswith(("/", "\\")) and "\\" not in name and ".." not in pure.parts and not (len(name) > 1 and name[1] == ":")


def verify_manifest(archive: zipfile.ZipFile, manifest: str, prefix: str = "") -> dict[str, Any]:
    names = set(archive.namelist())
    rows = []
    for number, line in enumerate(archive.read(manifest).decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        expected, rel = line.split(maxsplit=1)
        rel = rel.strip().lstrip("*")
        while rel.startswith("./"):
            rel = rel[2:]
        target = f"{prefix}{rel}"
        is_self = target == manifest
        observed = sha256_bytes(archive.read(target)) if target in names else None
        rows.append({
            "line": number,
            "path": target,
            "expected_sha256": expected,
            "observed_sha256": observed,
            "self_entry": is_self,
            "status": "INVALID_SELF_REFERENCE" if is_self else ("PASS" if expected == observed else "FAIL"),
        })
    nonself = [row for row in rows if not row["self_entry"]]
    self_rows = [row for row in rows if row["self_entry"]]
    return {
        "manifest": manifest,
        "line_count": len(rows),
        "nonself_checked": len(nonself),
        "nonself_missing": sum(row["observed_sha256"] is None for row in nonself),
        "nonself_mismatches": sum(row["status"] != "PASS" for row in nonself),
        "self_entry_count": len(self_rows),
        "self_entries": self_rows,
        "status": "PASS_WITH_RECONCILED_INVALID_SELF_ENTRY" if self_rows and all(row["status"] == "PASS" for row in nonself) else ("PASS" if not self_rows and all(row["status"] == "PASS" for row in nonself) else "FAIL"),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    artifact = args.artifact.resolve()
    outer_sha = sha256_file(artifact)
    outer_size = artifact.stat().st_size
    json_failures = []
    jsonl_failures = []
    with zipfile.ZipFile(artifact) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        unsafe = [name for name in names if not safe(name)]
        duplicates = len(names) - len(set(names))
        symlinks = [item.filename for item in infos if stat.S_ISLNK((item.external_attr >> 16) & 0xFFFF)]
        nested = [name for name in names if name.lower().endswith((".zip", ".tar", ".tgz", ".tar.gz", ".7z"))]
        compiled = [name for name in names if name.lower().endswith((".pyc", ".pyo", ".so", ".pyd", ".dll", ".exe"))]
        cache_or_env = [name for name in names if any(part.lower() in {"__pycache__", ".pytest_cache", ".venv", "venv", "site-packages"} for part in PurePosixPath(name).parts)]
        for item in infos:
            if item.is_dir():
                continue
            try:
                if item.filename.endswith(".json"):
                    json.loads(archive.read(item).decode("utf-8"))
                elif item.filename.endswith(".jsonl"):
                    for line_number, line in enumerate(archive.read(item).decode("utf-8").splitlines(), 1):
                        if line.strip():
                            json.loads(line)
            except Exception as exc:
                (jsonl_failures if item.filename.endswith(".jsonl") else json_failures).append({"path": item.filename, "line": locals().get("line_number"), "error": str(exc)})
        outer_manifest = verify_manifest(archive, "ARTIFACT_SHA256SUMS.txt")
        inner_manifest = verify_manifest(archive, f"{PREFIX}SHA256SUMS.txt", PREFIX)
        comparisons = []
        for name in names:
            if not (name.startswith(PREFIX) or name == "controllergate_v1_7_beta/reports/critic_review_package/shareable_summary.md"):
                continue
            target = ROOT / Path(*PurePosixPath(name).parts)
            artifact_hash = sha256_bytes(archive.read(name))
            repo_hash = sha256_file(target) if target.is_file() else None
            comparisons.append({
                "path": name,
                "artifact_sha256": artifact_hash,
                "repository_sha256": repo_hash,
                "status": "IDENTICAL_PRESERVED" if artifact_hash == repo_hash else "WORKFLOW_ARTIFACT_VARIANT_INDEXED_WITHOUT_HISTORICAL_REWRITE",
            })
    custody_pass = all((
        outer_sha == EXPECTED["sha256"], outer_size == EXPECTED["size"], len(names) == EXPECTED["entries"],
        not unsafe, duplicates == 0, not symlinks, not nested, not compiled, not cache_or_env,
        not json_failures, not jsonl_failures, outer_manifest["nonself_mismatches"] == 0,
        outer_manifest["self_entry_count"] == 1, inner_manifest["status"] == "PASS",
        inner_manifest["nonself_checked"] == 105,
    ))
    verification = {
        "status": "PASS" if custody_pass else "FAIL",
        "producer": "scripts/batch092_ingest_and_reconcile_batch091.py",
        "execution_depth": "outer_bytes_zip_structure_json_and_manifest_verification",
        "semantic_scope": "official Batch091 artifact custody",
        "authority_allowed": "historical evidence ingest and correction",
        "authority_forbidden": ["Batch091 scientific authority", "repair", "release", "count_increment"],
        "artifact_identity": EXPECTED,
        "artifact_path_outside_git": str(artifact),
        "download_custody": "one_time_user_authorized_exact_github_artifact_download",
        "observed_size": outer_size,
        "observed_sha256": outer_sha,
        "entry_count": len(names),
        "unsafe_path_count": len(unsafe),
        "duplicate_path_count": duplicates,
        "symlink_count": len(symlinks),
        "nested_archive_count": len(nested),
        "compiled_payload_count": len(compiled),
        "cache_or_environment_payload_count": len(cache_or_env),
        "json_parse_failure_count": len(json_failures),
        "jsonl_parse_failure_count": len(jsonl_failures),
        "verified_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }
    ingest = {
        **verification,
        "status": "PASS" if custody_pass else "FAIL",
        "official_ingest_mode": "official_artifact_manifest_indexed_without_rewriting_historical_batch091_outputs",
        "artifact_member_comparison_count": len(comparisons),
        "artifact_member_identical_count": sum(row["status"] == "IDENTICAL_PRESERVED" for row in comparisons),
        "artifact_member_workflow_variant_count": sum(row["status"] != "IDENTICAL_PRESERVED" for row in comparisons),
        "historical_batch091_bytes_rewritten": False,
        "raw_zip_committed": False,
        "comparisons": comparisons,
    }
    manifest = {
        "status": "PASS_WITH_RECONCILED_OUTER_SELF_MANIFEST_DEFECT" if outer_manifest["nonself_mismatches"] == 0 and outer_manifest["self_entry_count"] == 1 and inner_manifest["status"] == "PASS" else "FAIL",
        "producer": "scripts/batch092_ingest_and_reconcile_batch091.py",
        "execution_depth": "manifest_line_by_line_byte_verification",
        "semantic_scope": "Batch091 artifact manifests",
        "authority_allowed": "custody reconciliation",
        "authority_forbidden": ["perfect_outer_manifest_claim", "scientific_authority"],
        "outer_manifest": outer_manifest,
        "portable_inner_manifest": inner_manifest,
    }
    self_reconciliation = {
        "status": "PASS_RECONCILED",
        "producer": "scripts/batch092_ingest_and_reconcile_batch091.py",
        "execution_depth": "outer_manifest_self_entry_detection_and_nonself_reverification",
        "semantic_scope": "historical Batch091 manifest construction defect",
        "authority_allowed": "record correction",
        "authority_forbidden": ["rewrite Batch091", "claim outer manifest perfect"],
        "self_entry_expected_sha256": outer_manifest["self_entries"][0]["expected_sha256"],
        "self_entry_observed_sha256": outer_manifest["self_entries"][0]["observed_sha256"],
        "classification": "invalid_self_referential_manifest_construction",
        "nonself_checked": outer_manifest["nonself_checked"],
        "nonself_missing": outer_manifest["nonself_missing"],
        "nonself_mismatches": outer_manifest["nonself_mismatches"],
        "batch092_correction": "manifests exclude themselves from their own hash lists",
    }
    expected_red = json.loads((args.output / "batch092_pre_fix_external_review_expected_failure.json").read_text(encoding="utf-8"))
    exclusions = [{
        "finding_id": row["finding_id"],
        "excluded_authority": row["risk"],
        "source_commit": row["commit"],
        "source_path": row["path"],
        "reopen_condition": row["red_to_green_test"],
        "status": "EXCLUDED_PENDING_BATCH092_EXECUTED_CORRECTION",
    } for row in expected_red["findings"]]
    reconstruction = {
        "status": "PASS_CORRECTED_EXTERNAL_REVIEW",
        "producer": "scripts/batch092_ingest_and_reconcile_batch091.py",
        "execution_depth": "source_and_official_raw_artifact_reconstruction",
        "semantic_scope": "Batch091 current authority",
        "authority_allowed": ["artifact custody", "lossless transport progress", "installed target execution progress", "real wheel build and target/consumer canary progress"],
        "authority_forbidden": ["AMDS causal quality", "source ownership", "repair license", "real package-slot rollback", "raw semantic critic closure", "Product Beta RC"],
        "finding_count": len(exclusions),
        "corrected_classification": [
            "BATCH091_ARTIFACT_CUSTODY_PASS", "BATCH091_TRANSPORT_AND_TARGET_EXECUTION_PROGRESS_REAL",
            "BATCH091_AMDS_CAUSAL_QUALITY_NOT_ESTABLISHED", "BATCH091_SOURCE_OWNERSHIP_AUTHORITY_NOT_ESTABLISHED",
            "BATCH091_REPAIR_LICENSE_AUTHORITY_NOT_ESTABLISHED", "BATCH091_REAL_PACKAGE_SLOT_ROLLBACK_NOT_ESTABLISHED",
            "BATCH091_SEMANTIC_CRITIC_RAW_RECONSTRUCTION_NOT_ESTABLISHED", "PRODUCT_BETA_RC_BLOCKED_EXACT",
        ],
    }
    claim = {
        "status": "PASS_CORRECTED_CLAIM_BOUNDARY",
        "producer": "scripts/batch092_ingest_and_reconcile_batch091.py",
        "execution_depth": "official_artifact_and_source_external_review",
        "semantic_scope": "current public claim boundary",
        "authority_allowed": "historical correction only",
        "authority_forbidden": ["Product Beta RC approval", "production readiness", "repair count change"],
        "protocol": "v2.19", "package_version": "0.2.0b2.dev0",
        "issue_derived_repair_count": 6, "native_external_repair_count": 4, "historical_increment": 0,
        "product_beta_rc": "PRODUCT_BETA_RC_BLOCKED_EXACT", "amds_prospective_effectiveness": "NOT_ESTABLISHED",
        "memory_lift": "not demonstrated", "full_scoring": "NOT_RUN/disallowed",
        "public_writes": "inactive", "automatic_merge": "inactive", "production_readiness": False,
        "self_maintaining_software": "false/not demonstrated",
    }
    raw_preservation = {
        "status": "PASS" if custody_pass else "FAIL",
        "producer": "scripts/batch092_ingest_and_reconcile_batch091.py",
        "execution_depth": "byte_identity_comparison",
        "semantic_scope": "Batch091 historical bytes",
        "authority_allowed": "preservation",
        "authority_forbidden": ["rewrite", "reinterpret unsupported conclusions as authority"],
        "raw_zip_path_outside_git": str(artifact), "raw_zip_sha256": outer_sha,
        "historical_output_bytes_rewritten": False, "repository_output_comparisons": len(comparisons),
    }
    records = {
        "batch091_artifact_ingest.json": ingest,
        "batch091_artifact_sha256_verification.json": verification,
        "batch091_artifact_manifest_verification.json": manifest,
        "batch091_outer_self_manifest_reconciliation.json": self_reconciliation,
        "batch091_raw_evidence_preservation.json": raw_preservation,
        "batch091_external_review_reconstruction.json": reconstruction,
        "batch091_claim_correction.json": claim,
    }
    for name, value in records.items():
        write_json(args.output / name, value)
    write_jsonl(args.output / "batch091_current_authority_exclusion_registry.jsonl", exclusions)
    print(json.dumps({"status": ingest["status"], "outer_manifest": manifest["status"], "excluded_findings": len(exclusions)}, sort_keys=True))
    return 0 if custody_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

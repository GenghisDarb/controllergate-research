from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


OUTPUT = Path("outputs/post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure")
MAIN_EXPECTED = {
    "artifact_id": 8332964416,
    "name": "post_v2_37_hardening_batch089_full_isomorphism_reaction_complete_vertical_closure_artifacts",
    "workflow_run_id": 29390235692,
    "workflow_head": "85721a7a8a93a9b973abe3dcb90633edbbf63c2d",
    "size_bytes": 1083512,
    "sha256": "738b3184ef27f27e98c254295928b15fd6e86b6ecf2ad9446685b1fcce8cb007",
    "zip_entries": 578,
}
SHORT_EXPECTED = {
    "artifact_id": 8332946868,
    "name": "batch089_short_lived_historical_capsule_consumer_evidence",
    "size_bytes": 2652,
    "sha256": "ddc7ee7756a096db745e153eed60660e0513117e0faf42b569d3f85d0a6ae2ff",
    "zip_entries": 6,
}
UNSUPPORTED = {
    "canonical_capsule_injection_audit.json": "no_capsule_injection_execution",
    "amds_quality_gate.json": "no_blinded_historical_amds_campaign",
    "canary_exact_rollback.json": "canary_and_rollback_remained_blocked",
}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def read_zip(path: Path) -> tuple[dict[str, bytes], dict[str, object]]:
    raw = path.read_bytes()
    payload: dict[str, bytes] = {}
    counts = {key: 0 for key in ("unsafe_paths", "duplicate_paths", "symlinks", "nested_archives", "compiled_payloads", "cache_environment_payloads", "json_parse_errors", "jsonl_parse_errors")}
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        for info in infos:
            name = info.filename.replace("\\", "/")
            pure = PurePosixPath(name)
            lower = name.lower()
            if name.startswith("/") or re.match(r"^[A-Za-z]:", name) or ".." in pure.parts:
                counts["unsafe_paths"] += 1
            if name in payload:
                counts["duplicate_paths"] += 1
            if stat.S_IFMT(info.external_attr >> 16) == stat.S_IFLNK:
                counts["symlinks"] += 1
            if lower.endswith((".zip", ".tar", ".tar.gz", ".tgz", ".7z")):
                counts["nested_archives"] += 1
            if lower.endswith((".whl", ".pyc", ".pyo", ".dll", ".so", ".dylib", ".exe")):
                counts["compiled_payloads"] += 1
            if any(part.lower() in {"__pycache__", ".venv", "venv", ".git", ".tox", ".nox"} for part in pure.parts):
                counts["cache_environment_payloads"] += 1
            content = archive.read(info)
            payload[name] = content
            try:
                if lower.endswith(".json"):
                    json.loads(content.decode("utf-8-sig"))
                elif lower.endswith(".jsonl"):
                    for line in content.decode("utf-8-sig").splitlines():
                        if line.strip():
                            json.loads(line)
            except (UnicodeDecodeError, json.JSONDecodeError):
                counts["json_parse_errors" if lower.endswith(".json") else "jsonl_parse_errors"] += 1
    return payload, {"size_bytes": len(raw), "sha256": sha(raw), "zip_entries": len(infos), "custody_counts": counts}


def verify_manifest(payload: dict[str, bytes], name: str) -> dict[str, object]:
    base = name.rsplit("/", 1)[0] + "/" if "/" in name else ""
    checked = missing = mismatches = 0
    for line in payload[name].decode("utf-8-sig").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split("  ", 1)
        relative = relative.replace("\\", "/")
        while relative.startswith("./"):
            relative = relative[2:]
        target = base + relative
        checked += 1
        if target not in payload:
            missing += 1
        elif sha(payload[target]) != expected:
            mismatches += 1
    return {"path": name, "checked": checked, "missing": missing, "mismatches": mismatches, "status": "PASS" if not missing and not mismatches else "FAIL"}


def json_value(raw: bytes) -> object | None:
    try:
        return json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def classification(name: str, value: object | None) -> str:
    short = name.rsplit("/", 1)[-1]
    if short.endswith("SHA256SUMS.txt"):
        return "PORTABLE_MANIFEST"
    if short in UNSUPPORTED:
        return "UNSUPPORTED_CLAIM"
    if short == "batch089_state.sqlite3":
        return "RAW_MECHANISM_OUTPUT"
    if short in {"prompt2_vertical_scenario_results.json", "prompt3_vertical_scenario_results.json", "batch089_consolidated_state.json", "batch089_final_consolidated_state.json"}:
        return "IN_PROCESS_INTEGRATION_FIXTURE"
    if "pre_fix_expected_failure" in short or "negative_control" in short:
        return "TEST_ASSERTION_RESULT"
    if short in {"cloudpickle_canonical_historical_lifecycle.json", "freezegun_canonical_historical_lifecycle.json"}:
        return "BLOCKER_RECORD"
    if isinstance(value, dict) and isinstance(value.get("execution_receipts"), list):
        return "EVIDENCE_ALIAS"
    if name.endswith(".jsonl"):
        return "EVIDENCE_ALIAS"
    if short in {"mempalace_fork_upstream_comparison.json", "mempalace_license_and_sbom_audit.json", "batch089_secret_scan.json", "batch089_sbom_audit.json"}:
        return "RAW_MECHANISM_OUTPUT"
    if "audit" in short or "summary" in short or "decision" in short or "report" in short:
        return "GENERATED_VIEW"
    return "GENERATED_VIEW"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-artifact", type=Path, required=True)
    parser.add_argument("--short-artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    main_payload, main_observed = read_zip(args.main_artifact)
    short_payload, short_observed = read_zip(args.short_artifact)
    main_failures = [key for key in ("size_bytes", "sha256", "zip_entries") if main_observed[key] != MAIN_EXPECTED[key]]
    short_failures = [key for key in ("size_bytes", "sha256", "zip_entries") if short_observed[key] != SHORT_EXPECTED[key]]
    main_failures += [key for key, count in main_observed["custody_counts"].items() if count]
    short_failures += [key for key, count in short_observed["custody_counts"].items() if count]
    manifests = [verify_manifest(main_payload, name) for name in sorted(main_payload) if name.endswith("SHA256SUMS.txt")]
    required = {row["path"]: row for row in manifests if row["path"] in {"ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt"}}
    expected_manifest_counts = {"ARTIFACT_SHA256SUMS.txt": 577, "PORTABLE_ARTIFACT_SHA256SUMS.txt": 572, "SHA256SUMS.txt": 576}
    for name, expected_count in expected_manifest_counts.items():
        row = required.get(name)
        if not row or row["checked"] != expected_count or row["status"] != "PASS":
            main_failures.append(f"manifest:{name}")
    receipt_rows: list[tuple[str, tuple[str, ...]]] = []
    alias_rows: list[dict[str, object]] = []
    reconciled: list[dict[str, object]] = []
    for name, raw in sorted(main_payload.items()):
        value = json_value(raw) if name.endswith(".json") else None
        evidence_class = classification(name, value)
        receipts: tuple[str, ...] = ()
        observed_status = assertion_status = None
        if isinstance(value, dict):
            observed_status = value.get("mechanism_observed_status")
            assertion_status = value.get("test_assertion_status")
            if isinstance(value.get("execution_receipts"), list):
                receipts = tuple(value["execution_receipts"])
                receipt_rows.append((name, receipts))
        if evidence_class == "EVIDENCE_ALIAS":
            alias_rows.append({"path": name, "receipt_identities": list(receipts), "current_authority": False, "reason": "mechanically_generated_alias_or_unscoped_receipt_view"})
        reconciled.append({
            "path": name,
            "sha256": sha(raw),
            "evidence_class": evidence_class,
            "mechanism_observed_status": observed_status,
            "test_assertion_status": assertion_status,
            "execution_depth": "IN_PROCESS_MECHANISM_FIXTURE" if evidence_class in {"UNIT_MECHANISM_FIXTURE", "IN_PROCESS_INTEGRATION_FIXTURE", "TEST_ASSERTION_RESULT", "EVIDENCE_ALIAS"} else "GENERATED_VIEW" if evidence_class in {"GENERATED_VIEW", "UNSUPPORTED_CLAIM", "BLOCKER_RECORD"} else "RAW_OUTPUT",
            "producer_identity": "batch089_in_process_composite" if evidence_class in {"IN_PROCESS_INTEGRATION_FIXTURE", "TEST_ASSERTION_RESULT", "EVIDENCE_ALIAS"} else "artifact_packager",
            "semantic_scope": "batch089_unit_or_fixture_only" if evidence_class in {"IN_PROCESS_INTEGRATION_FIXTURE", "TEST_ASSERTION_RESULT", "EVIDENCE_ALIAS"} else "custody_or_view",
            "receipt_identities": list(receipts),
            "candidate_run_frame": None,
            "may_support_release": False,
            "may_support_unit_claim": evidence_class in {"UNIT_MECHANISM_FIXTURE", "IN_PROCESS_INTEGRATION_FIXTURE", "TEST_ASSERTION_RESULT", "RAW_MECHANISM_OUTPUT"},
        })
    reuse = Counter(receipts for _, receipts in receipt_rows)
    reuse_graph = {
        "receipt_bearing_json_count": len(receipt_rows),
        "unique_receipt_set_count": len(reuse),
        "maximum_receipt_set_reuse": max(reuse.values()),
        "receipt_sets": [{"receipt_ids": list(receipts), "reuse_count": count, "paths": [name for name, row in receipt_rows if row == receipts]} for receipts, count in reuse.most_common()],
        "release_authority": False,
        "status": "PASS_RECONCILED",
    }
    short_records = {name: json_value(raw) for name, raw in sorted(short_payload.items())}
    lifecycle_rows = [value for name, value in short_records.items() if name.endswith("canonical_historical_lifecycle.json") and isinstance(value, dict)]
    short_lifecycle_valid = len(lifecycle_rows) == 2 and all(row.get("status") == "BLOCK" and row.get("complete") is False and row.get("exact_blocker") == "canonical_installed_lifecycle_capsule_injection_not_completed" and row.get("repair_count_increment") == 0 for row in lifecycle_rows)
    if not short_lifecycle_valid:
        short_failures.append("short_lifecycle_boundary")
    now = datetime.now(timezone.utc).isoformat()
    write_json(args.output / "batch089_main_artifact_ingest.json", {"expected": MAIN_EXPECTED, "observed": main_observed, "artifact_path_outside_git": str(args.main_artifact.resolve()), "raw_zip_committed": False, "failures": sorted(set(main_failures)), "verified_at": now, "status": "PASS" if not main_failures else "FAIL"})
    write_json(args.output / "batch089_short_lived_artifact_ingest.json", {"expected": SHORT_EXPECTED, "observed": short_observed, "artifact_path_outside_git": str(args.short_artifact.resolve()), "records": {name: {"sha256": sha(short_payload[name]), "status": value.get("status") if isinstance(value, dict) else None} for name, value in short_records.items()}, "lifecycle_boundary_preserved": short_lifecycle_valid, "raw_zip_committed": False, "failures": sorted(set(short_failures)), "verified_at": now, "status": "PASS" if not short_failures else "FAIL"})
    write_json(args.output / "batch089_manifest_verification.json", {"manifests": manifests, "required_manifest_expectations": expected_manifest_counts, "status": "PASS" if all(row["status"] == "PASS" for row in manifests) else "FAIL"})
    write_json(args.output / "batch089_raw_evidence_preservation.json", {"main_artifact_sha256": MAIN_EXPECTED["sha256"], "short_lived_artifact_sha256": SHORT_EXPECTED["sha256"], "raw_zips_outside_git": True, "historical_batch089_outputs_rewritten": False, "ingest_mode": "byte_verified_reconciliation_records_only", "status": "PASS"})
    write_json(args.output / "batch089_evidence_depth_reconciliation.json", {"classification_count": len(reconciled), "class_counts": dict(sorted(Counter(row["evidence_class"] for row in reconciled).items())), "batch089_scenario_count": 60, "batch089_scenario_corrected_classification": "IN_PROCESS_INTEGRATION_FIXTURE", "installed_vertical_execution_count": 0, "records": reconciled, "status": "PASS"})
    write_json(args.output / "batch089_receipt_reuse_graph.json", reuse_graph)
    write_jsonl(args.output / "batch089_alias_fanout_registry.jsonl", alias_rows)
    write_json(args.output / "batch089_claim_correction.json", {"valid_progress": ["artifact_custody", "sqlite_schema_v5", "typed_mechanism_library", "54_focused_tests", "full_regression", "linux_windows_wheel_installation", "60_in_process_fixture_assertions"], "corrected_claims": {"batch089_60_scenarios": "IN_PROCESS_INTEGRATION_FIXTURE", "installed_product_vertical_execution_count": 0, "canonical_capsule_injection_audit": "UNSUPPORTED_CLAIM", "amds_quality_gate": "UNSUPPORTED_CLAIM", "canary_exact_rollback": "UNSUPPORTED_CLAIM"}, "product_beta_rc": "PRODUCT_BETA_RC_BLOCKED_EXACT", "status": "PASS"})
    exclusions = [
        {"authority_item": "configs/batch089_output_catalog.json", "reason": "filename_driven_report_fanout", "current_authority": False},
        {"authority_item": "scripts/run_batch089_composite.py::evidence_for", "reason": "filename_derived_binding_and_receipt_fallback", "current_authority": False},
        {"authority_item": "scripts/run_batch089_composite.py::write_catalog", "reason": "evidence_alias_fanout", "current_authority": False},
        *({"authority_item": name, "reason": reason, "current_authority": False} for name, reason in sorted(UNSUPPORTED.items())),
        {"authority_item": "batch089_generic_json_jsonl_aliases", "reason": f"{len(alias_rows)}_unscoped_alias_views", "current_authority": False},
    ]
    write_jsonl(args.output / "batch089_current_authority_exclusion_registry.jsonl", exclusions)
    summary = {"main_artifact": "PASS" if not main_failures else "FAIL", "short_lived_artifact": "PASS" if not short_failures else "FAIL", "manifests": "PASS" if all(row["status"] == "PASS" for row in manifests) else "FAIL", "receipt_bearing_json_count": len(receipt_rows), "unique_receipt_set_count": len(reuse), "alias_count": len(alias_rows), "status": "PASS" if not main_failures and not short_failures and all(row["status"] == "PASS" for row in manifests) else "FAIL"}
    print(json.dumps(summary, sort_keys=True))
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

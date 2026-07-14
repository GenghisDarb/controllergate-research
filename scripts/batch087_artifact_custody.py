from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath


EXPECTED = {
    "name": "post_v2_37_hardening_batch086_historical_lifecycle_dpp14_product_beta_rc_artifacts",
    "artifact_id": 8322892892,
    "workflow_run_id": 29362678414,
    "workflow_head": "ae0410fa1fcabbcf1653e5e73f003f397398a1ca",
    "size_bytes": 47029,
    "sha256": "7e080cbf744962862fe547216fdb403d94e5a238982d19e440e4bea6c3fd018a",
    "zip_entries": 32,
    "internal_manifest_records": 27,
    "outer_manifest_records": 31,
}
RUNNER_PREFIX = "/home/runner/work/_temp/batch086-artifact/"
BATCH086_OUTPUT = "outputs/post_v2_37_hardening_batch086_historical_lifecycle_dpp14_product_beta_rc/"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def verify(zip_path: Path) -> tuple[dict[str, object], dict[str, bytes], str, str]:
    raw = zip_path.read_bytes()
    failures: list[str] = []
    if len(raw) != EXPECTED["size_bytes"]:
        failures.append("outer_size_mismatch")
    if _sha(raw) != EXPECTED["sha256"]:
        failures.append("outer_sha256_mismatch")
    payload: dict[str, bytes] = {}
    unsafe: list[str] = []
    duplicates: list[str] = []
    forbidden: list[str] = []
    symlinks: list[str] = []
    seen: set[str] = set()
    with zipfile.ZipFile(zip_path) as archive:
        infos = archive.infolist()
        if len(infos) != EXPECTED["zip_entries"]:
            failures.append("zip_entry_count_mismatch")
        for info in infos:
            name = info.filename.replace("\\", "/")
            pure = PurePosixPath(name)
            if name.startswith("/") or re.match(r"^[A-Za-z]:", name) or ".." in pure.parts:
                unsafe.append(name)
            if name in seen:
                duplicates.append(name)
            seen.add(name)
            if ((info.external_attr >> 16) & 0o170000) == 0o120000:
                symlinks.append(name)
            lower = name.lower()
            if lower.endswith((".zip", ".tar", ".tar.gz", ".tgz", ".whl", ".pyc", ".pyo", ".dll", ".so", ".exe")):
                forbidden.append(name)
            if any(part in {"__pycache__", ".venv", "venv", ".git"} for part in pure.parts):
                forbidden.append(name)
            if any(marker in lower for marker in ("credential", "secret", "token.txt", "/.env")):
                forbidden.append(name)
            payload[name] = archive.read(info)
    if unsafe:
        failures.append("unsafe_archive_paths")
    if duplicates:
        failures.append("duplicate_archive_paths")
    if symlinks:
        failures.append("symlink_payload")
    if forbidden:
        failures.append("forbidden_archive_payload")

    internal_name = BATCH086_OUTPUT + "SHA256SUMS.txt"
    internal_checked = internal_missing = internal_failed = 0
    for line in payload[internal_name].decode("utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split("  ", 1)
        member = str(PurePosixPath(internal_name).parent / relative)
        internal_checked += 1
        if member not in payload:
            internal_missing += 1
        elif _sha(payload[member]) != expected:
            internal_failed += 1
    if (internal_checked, internal_missing, internal_failed) != (27, 0, 0):
        failures.append("internal_manifest_invalid")

    raw_outer = payload["ARTIFACT_SHA256SUMS.txt"].decode("utf-8")
    outer_rows: list[tuple[str, str, str]] = []
    absolute_count = outer_missing = outer_failed = 0
    for line in raw_outer.splitlines():
        if not line.strip():
            continue
        expected, raw_path = line.split("  ", 1)
        absolute_count += int(raw_path.startswith(RUNNER_PREFIX))
        relative = raw_path[len(RUNNER_PREFIX) :] if raw_path.startswith(RUNNER_PREFIX) else raw_path.lstrip("./")
        outer_rows.append((expected, raw_path, relative))
        if relative not in payload:
            outer_missing += 1
        elif _sha(payload[relative]) != expected:
            outer_failed += 1
    if (len(outer_rows), absolute_count, outer_missing, outer_failed) != (31, 31, 0, 0):
        failures.append("normalized_outer_manifest_invalid")
    portable_outer = "".join(f"{digest}  {relative}\n" for digest, _, relative in sorted(outer_rows, key=lambda row: row[2]))

    result: dict[str, object] = {
        "status": "PASS" if not failures else "FAIL",
        "artifact_identity": EXPECTED,
        "observed_size_bytes": len(raw),
        "observed_sha256": _sha(raw),
        "zip_entry_count": len(payload),
        "unsafe_path_count": len(unsafe),
        "duplicate_path_count": len(duplicates),
        "symlink_count": len(symlinks),
        "forbidden_payload_count": len(forbidden),
        "internal_manifest": {"checked": internal_checked, "missing": internal_missing, "failures": internal_failed},
        "outer_manifest": {
            "checked": len(outer_rows),
            "runner_absolute_path_records": absolute_count,
            "normalized_missing": outer_missing,
            "normalized_failures": outer_failed,
            "raw_sha256": _sha(raw_outer.encode("utf-8")),
            "portable_sha256": _sha(portable_outer.encode("utf-8")),
        },
        "failures": failures,
        "raw_zip_committed": False,
    }
    return result, payload, raw_outer, portable_outer


def ingest(payload: dict[str, bytes], repo_root: Path) -> dict[str, object]:
    copied: list[dict[str, object]] = []
    for name, data in sorted(payload.items()):
        if name == "ARTIFACT_SHA256SUMS.txt":
            continue
        if not (name.startswith(BATCH086_OUTPUT) or name.startswith("experiments/tld_shadow/")):
            continue
        target = repo_root / Path(*PurePosixPath(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        copied.append({"path": name, "sha256": _sha(data), "size_bytes": len(data)})
    return {"status": "PASS", "copied_file_count": len(copied), "files": copied, "non_evidence_payload_ingested": False}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path)
    args = parser.parse_args()
    verification, payload, raw_outer, portable_outer = verify(args.artifact)
    args.output.mkdir(parents=True, exist_ok=True)
    _write_json(args.output / "batch086_artifact_ingest.json", verification)
    (args.output / "batch086_original_outer_ARTIFACT_SHA256SUMS.txt").write_text(raw_outer, encoding="utf-8", newline="\n")
    (args.output / "batch086_portable_ARTIFACT_SHA256SUMS.txt").write_text(portable_outer, encoding="utf-8", newline="\n")
    portability = {
        "status": "PASS" if verification["status"] == "PASS" else "FAIL",
        "known_defect": "outer_manifest_runner_absolute_paths",
        "runner_prefix": RUNNER_PREFIX,
        "original_manifest_preserved_unchanged": True,
        "original_manifest_sha256": verification["outer_manifest"]["raw_sha256"],
        "normalized_records_checked": verification["outer_manifest"]["checked"],
        "normalized_failures": verification["outer_manifest"]["normalized_failures"],
        "portable_manifest_sha256": verification["outer_manifest"]["portable_sha256"],
        "future_machine_specific_rewriting_required": False,
    }
    _write_json(args.output / "batch086_outer_manifest_portability_reconciliation.json", portability)
    if verification["status"] != "PASS":
        print(json.dumps(verification, sort_keys=True))
        return 1
    ingestion = ingest(payload, args.repo_root.resolve()) if args.repo_root else {"status": "NOT_RUN"}
    _write_json(args.output / "batch086_raw_evidence_preservation.json", {
        "status": ingestion["status"],
        "official_artifact_sha256": EXPECTED["sha256"],
        "raw_outer_manifest_preserved": True,
        "ingestion": ingestion,
        "historical_records_rewritten": False,
    })
    reconciliations = {
        "batch086_historical_execution_depth_reconciliation.json": {
            "status": "PASS", "genuine_gains_preserved": ["two reconstructed-equivalent historical providers", "two twice-reproduced prepatch failures", "canonical Cloudpickle and Freezegun patch identities", "target validation and duplicate patched replay", "exact source-tree rollback", "zero historical count increment", "package workflow results", "no public writes", "failed branches and raw records"],
        },
        "batch086_canonical_path_reconciliation.json": {"status": "BLOCK", "blockers": ["canonical_installed_execution_graph_not_converged", "SQLite_not_sole_runtime_state_authority", "legacy_fixture_path_reachable_from_product_cli", "historical_lifecycle_bypasses_execution_broker_and_dispatcher"]},
        "batch086_dpp14_blinding_reconciliation.json": {"status": "BLOCK", "blocker": "DPP14_quality_label_fed_not_blind", "Batch086_metrics_classification": "label_fed_replay_agreement_not_diagnostic_accuracy"},
        "batch086_interlock_elbow_projection_reconciliation.json": {"status": "BLOCK", "blockers": ["interlocks_not_bound_to_executed_typed_evidence", "causal_elbow_not_derived_from_execution_events", "three_projection_shadow_not_empirically_executed"]},
        "batch086_non_source_terminal_reconciliation.json": {"status": "BLOCK", "blocker": "non_source_historical_terminal_depth_insufficient"},
        "batch086_canary_depth_reconciliation.json": {"status": "BLOCK", "blocker": "deployed_repaired_package_canary_not_established"},
        "batch086_critic_independence_reconciliation.json": {"status": "BLOCK", "blocker": "independent_critic_not_independent"},
        "batch086_public_state_drift_reconciliation.json": {"status": "BLOCK", "blocker": "public_state_and_release_version_drift"},
    }
    for name, value in reconciliations.items():
        _write_json(args.output / name, value)
    _write_json(args.output / "batch086_product_beta_rc_reclassification.json", {
        "status": "PRODUCT_BETA_RC_BLOCKED_EXACT",
        "workflow_classification": "BATCH086_WORKFLOW_PASS_WITH_SUBSTANTIAL_HISTORICAL_EXECUTION_EVIDENCE_AND_PRODUCT_BETA_RC_REVALIDATION_REQUIRED",
        "reclassification_reason": "independent Batch087 pre-fix audit discovered release-truth defects",
        "historical_replay_count_increment": 0,
    })
    print(json.dumps({"verification": verification["status"], "ingestion": ingestion["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

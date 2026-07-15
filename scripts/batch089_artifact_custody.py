from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath

from batch089_common import OUTPUT, write_json


EXPECTED = {
    "artifact_id": 8328997599,
    "artifact_name": "post_v2_37_hardening_batch088_causal_amds_historical_capsule_product_beta_closure_artifacts",
    "workflow_run_id": 29379128114,
    "workflow_head": "e02fb4d3a899dd0a6ccc9eb8fc0e38ab0e4e4e94",
    "size_bytes": 116600,
    "sha256": "6e04eeb145d851556ba66defd1fe842a5230ee9fcdd4e50755e0bb7e039bc72b",
    "zip_entries": 69,
}
PREFIX = "post_v2_37_hardening_batch088_causal_amds_historical_capsule_product_beta_closure/"


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _manifest(payload: dict[str, bytes], name: str, prefix: str = "") -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for line in payload[name].decode("utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split("  ", 1)
        relative = relative.replace("\\", "/")
        while relative.startswith("./"):
            relative = relative[2:]
        target = prefix + relative
        observed = _sha(payload[target]) if target in payload else None
        rows.append({"path": target, "expected_sha256": expected, "observed_sha256": observed, "status": "PASS" if observed == expected else "FAIL"})
    missing = sum(row["observed_sha256"] is None for row in rows)
    failures = sum(row["observed_sha256"] is not None and row["status"] != "PASS" for row in rows)
    return {"checked": len(rows), "missing": missing, "failures": failures, "manifest_sha256": _sha(payload[name]), "records": rows, "status": "PASS" if not missing and not failures else "FAIL"}


def verify(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    payload: dict[str, bytes] = {}
    categories: dict[str, list[str]] = {key: [] for key in ("unsafe_paths", "duplicate_paths", "symlinks", "nested_archives", "compiled_payloads", "cache_environment_payloads")}
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            name = info.filename.replace("\\", "/")
            pure = PurePosixPath(name)
            if name.startswith("/") or re.match(r"^[A-Za-z]:", name) or ".." in pure.parts:
                categories["unsafe_paths"].append(name)
            if name in payload:
                categories["duplicate_paths"].append(name)
            if ((info.external_attr >> 16) & 0o170000) == 0o120000:
                categories["symlinks"].append(name)
            lower = name.lower()
            if lower.endswith((".zip", ".tar", ".tar.gz", ".tgz", ".7z")):
                categories["nested_archives"].append(name)
            if lower.endswith((".whl", ".pyc", ".pyo", ".dll", ".so", ".dylib", ".exe")):
                categories["compiled_payloads"].append(name)
            if any(part.lower() in {"__pycache__", ".venv", "venv", ".git", ".tox", ".nox"} for part in pure.parts):
                categories["cache_environment_payloads"].append(name)
            payload[name] = archive.read(info)
    observed = {"sha256": _sha(raw), "size_bytes": len(raw), "zip_entries": len(payload)}
    manifests = {
        "artifact_level": _manifest(payload, "ARTIFACT_SHA256SUMS.txt"),
        "portable_output": _manifest(payload, PREFIX + "PORTABLE_ARTIFACT_SHA256SUMS.txt", PREFIX),
        "internal_output": _manifest(payload, PREFIX + "SHA256SUMS.txt", PREFIX),
    }
    failures: list[str] = []
    for key in observed:
        if observed[key] != EXPECTED[key]:
            failures.append(f"outer_{key}_mismatch")
    expected_counts = {"artifact_level": 68, "portable_output": 66, "internal_output": 67}
    for key, count in expected_counts.items():
        row = manifests[key]
        if (row["checked"], row["missing"], row["failures"]) != (count, 0, 0):
            failures.append(f"{key}_manifest_invalid")
    for key, rows in categories.items():
        if rows:
            failures.append(key)
    return {
        "artifact_identity": EXPECTED,
        "observed": observed,
        "manifests": manifests,
        "custody": {f"{key}_count": len(rows) for key, rows in categories.items()},
        "failures": failures,
        "source_path_outside_git": str(path.resolve()),
        "raw_zip_committed": False,
        "prior_batch_raw_evidence_rewritten": False,
        "status": "PASS" if not failures else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    result = verify(args.artifact)
    write_json(args.output / "batch088_artifact_ingest.json", {key: value for key, value in result.items() if key != "manifests"})
    write_json(args.output / "batch088_artifact_sha256_verification.json", {"expected": EXPECTED, "observed": result["observed"], "status": "PASS" if result["observed"] == {key: EXPECTED[key] for key in ("sha256", "size_bytes", "zip_entries")} else "FAIL"})
    write_json(args.output / "batch088_artifact_manifest_verification.json", {"manifests": result["manifests"], "status": result["status"]})
    write_json(args.output / "batch088_raw_evidence_preservation.json", {"artifact_sha256": EXPECTED["sha256"], "artifact_path_outside_git": str(args.artifact.resolve()), "ingest_mode": "verified_companion_records_only", "prior_output_rewritten": False, "raw_zip_committed": False, "status": result["status"]})
    print(json.dumps({"status": result["status"], "observed": result["observed"]}, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath


EXPECTED = {
    "artifact_id": 8325603205,
    "name": "post_v2_37_hardening_batch087_canonical_execution_blind_dpp14_product_beta_revalidation_artifacts",
    "sha256": "7da52e33c7fd2f512e03a2858aefea95042b6aa1ad943b702a080b0a136ccbe2",
    "size_bytes": 97024,
    "workflow_head": "f00bdc4a54786e20ac9cb6f82ed061b9af3cb2ec",
    "workflow_run_id": 29369758780,
    "zip_entries": 86,
}
BATCH087_OUTPUT = (
    "outputs/post_v2_37_hardening_batch087_canonical_execution_blind_dpp14_"
    "product_beta_revalidation/"
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def parse_manifest(
    payload: dict[str, bytes], manifest_name: str, base: PurePosixPath | None = None
) -> dict[str, object]:
    checked = missing = failures = 0
    records: list[dict[str, object]] = []
    for line in payload[manifest_name].decode("utf-8").splitlines():
        if not line.strip():
            continue
        expected, relative = line.split("  ", 1)
        member = str((base / relative) if base else PurePosixPath(relative))
        checked += 1
        observed = sha256(payload[member]) if member in payload else None
        missing += int(observed is None)
        failures += int(observed is not None and observed != expected)
        records.append(
            {
                "expected_sha256": expected,
                "observed_sha256": observed,
                "path": member,
                "status": "PASS" if observed == expected else "FAIL",
            }
        )
    return {
        "checked": checked,
        "failures": failures,
        "manifest_sha256": sha256(payload[manifest_name]),
        "missing": missing,
        "records": records,
        "status": "PASS" if not missing and not failures else "FAIL",
    }


def verify(artifact: Path) -> tuple[dict[str, object], dict[str, bytes]]:
    raw = artifact.read_bytes()
    payload: dict[str, bytes] = {}
    unsafe: list[str] = []
    duplicates: list[str] = []
    symlinks: list[str] = []
    nested_archives: list[str] = []
    compiled: list[str] = []
    cache_environment: list[str] = []
    seen: set[str] = set()
    with zipfile.ZipFile(artifact) as archive:
        infos = archive.infolist()
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
            if lower.endswith((".zip", ".tar", ".tar.gz", ".tgz", ".7z")):
                nested_archives.append(name)
            if lower.endswith((".whl", ".pyc", ".pyo", ".dll", ".so", ".dylib", ".exe")):
                compiled.append(name)
            if any(part.lower() in {"__pycache__", ".venv", "venv", ".git", ".tox", ".nox"} for part in pure.parts):
                cache_environment.append(name)
            payload[name] = archive.read(info)

    output_base = PurePosixPath(BATCH087_OUTPUT)
    artifact_manifest = parse_manifest(payload, "ARTIFACT_SHA256SUMS.txt")
    portable_manifest = parse_manifest(
        payload,
        BATCH087_OUTPUT + "PORTABLE_ARTIFACT_SHA256SUMS.txt",
        output_base,
    )
    internal_manifest = parse_manifest(
        payload,
        BATCH087_OUTPUT + "SHA256SUMS.txt",
        output_base,
    )
    failures: list[str] = []
    observed = {
        "sha256": sha256(raw),
        "size_bytes": len(raw),
        "zip_entries": len(payload),
    }
    for key in ("sha256", "size_bytes", "zip_entries"):
        if observed[key] != EXPECTED[key]:
            failures.append(f"outer_{key}_mismatch")
    expected_manifests = {
        "artifact": (85, 0, 0),
        "portable": (66, 0, 0),
        "internal": (67, 0, 0),
    }
    for name, result in (
        ("artifact", artifact_manifest),
        ("portable", portable_manifest),
        ("internal", internal_manifest),
    ):
        actual = (result["checked"], result["missing"], result["failures"])
        if actual != expected_manifests[name]:
            failures.append(f"{name}_manifest_invalid")
    for name, values in (
        ("unsafe_paths", unsafe),
        ("duplicate_paths", duplicates),
        ("symlinks", symlinks),
        ("nested_archives", nested_archives),
        ("wheels_or_compiled_payloads", compiled),
        ("cache_or_environment_payloads", cache_environment),
    ):
        if values:
            failures.append(name)
    result: dict[str, object] = {
        "artifact_identity": EXPECTED,
        "artifact_manifest": artifact_manifest,
        "cache_or_environment_payload_count": len(cache_environment),
        "duplicate_path_count": len(duplicates),
        "failures": failures,
        "internal_output_manifest": internal_manifest,
        "nested_archive_count": len(nested_archives),
        "observed": observed,
        "portable_output_manifest": portable_manifest,
        "raw_zip_committed": False,
        "source_path_outside_git": str(artifact.resolve()),
        "status": "PASS" if not failures else "FAIL",
        "symlink_count": len(symlinks),
        "unsafe_path_count": len(unsafe),
        "wheels_or_compiled_payload_count": len(compiled),
    }
    return result, payload


def ingest(payload: dict[str, bytes], repo_root: Path) -> dict[str, object]:
    copied: list[dict[str, object]] = []
    for name, data in sorted(payload.items()):
        if not name.startswith(BATCH087_OUTPUT):
            continue
        target = repo_root / Path(*PurePosixPath(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        copied.append({"path": name, "sha256": sha256(data), "size_bytes": len(data)})
    return {
        "copied_file_count": len(copied),
        "files": copied,
        "non_output_payload_ingested": False,
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path)
    args = parser.parse_args()
    verification, payload = verify(args.artifact)
    args.output.mkdir(parents=True, exist_ok=True)
    summary = {
        key: value
        for key, value in verification.items()
        if key not in {"artifact_manifest", "portable_output_manifest", "internal_output_manifest"}
    }
    write_json(args.output / "batch087_artifact_ingest.json", summary)
    write_json(
        args.output / "batch087_artifact_sha256_verification.json",
        {
            "expected_sha256": EXPECTED["sha256"],
            "expected_size_bytes": EXPECTED["size_bytes"],
            "observed_sha256": verification["observed"]["sha256"],
            "observed_size_bytes": verification["observed"]["size_bytes"],
            "status": "PASS" if not any(x.startswith("outer_") for x in verification["failures"]) else "FAIL",
        },
    )
    write_json(
        args.output / "batch087_artifact_manifest_verification.json",
        {
            "artifact_level": verification["artifact_manifest"],
            "internal_output": verification["internal_output_manifest"],
            "portable_output": verification["portable_output_manifest"],
            "status": verification["status"],
        },
    )
    if verification["status"] != "PASS":
        print(json.dumps(summary, sort_keys=True))
        return 1
    ingestion = ingest(payload, args.repo_root.resolve()) if args.repo_root else {"status": "NOT_RUN"}
    write_json(
        args.output / "batch087_raw_evidence_preservation.json",
        {
            "artifact_sha256": EXPECTED["sha256"],
            "ingestion": ingestion,
            "raw_evidence_rewritten": False,
            "raw_zip_committed": False,
            "raw_zip_location": str(args.artifact.resolve()),
            "status": ingestion["status"],
        },
    )
    print(json.dumps({"ingestion": ingestion["status"], "verification": verification["status"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

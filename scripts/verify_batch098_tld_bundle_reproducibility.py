from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def run_builder(source: Path, target: Path, label: str) -> tuple[Path, Path, Path, int]:
    target.mkdir(parents=True, exist_ok=True)
    bundle = target / "bundle.zip"
    manifest = target / "manifest.json"
    report = target / "report.json"
    command = [
        sys.executable,
        str(Path(__file__).with_name("build_batch098_tld_bundle_from_direct_sources.py")),
        "--source-root",
        str(source),
        "--output-bundle",
        str(bundle),
        "--output-manifest",
        str(manifest),
        "--output-report",
        str(report),
    ]
    environment = dict(os.environ)
    environment["PYTHONHASHSEED"] = "0" if label == "A" else "937"
    completed = subprocess.run(command, check=False, capture_output=True, text=True, env=environment)
    if completed.returncode != 0:
        raise RuntimeError(f"builder {label} failed: {completed.stdout[-2000:]} {completed.stderr[-2000:]}")
    return bundle, manifest, report, completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-bundle", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--requirement-registry")
    parser.add_argument("--inventory-output-dir")
    args = parser.parse_args()
    source = Path(args.source_root).resolve()
    output = Path(args.output_dir)
    runtime_parent = Path(r"C:\Dev\ControllerGate_Runtime") if os.name == "nt" else Path(tempfile.gettempdir())
    runtime_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="batch098-tld-rebuild-a-", dir=runtime_parent) as first_dir, tempfile.TemporaryDirectory(prefix="batch098-tld-rebuild-b-", dir=runtime_parent) as second_dir:
        try:
            first = run_builder(source, Path(first_dir), "A")
            second = run_builder(source, Path(second_dir), "B")
        except RuntimeError as exc:
            print(json.dumps({"status": "BLOCK", "error": str(exc)}, sort_keys=True))
            return 1
        zip_equal = first[0].read_bytes() == second[0].read_bytes()
        manifest_equal = first[1].read_bytes() == second[1].read_bytes()
        report_equal = first[2].read_bytes() == second[2].read_bytes()
        with zipfile.ZipFile(first[0]) as left, zipfile.ZipFile(second[0]) as right:
            left_names = left.namelist()
            right_names = right.namelist()
            member_order_equal = left_names == right_names
            member_rows = [{"path": info.filename, "size": info.file_size, "sha256": hashlib.sha256(left.read(info)).hexdigest()} for info in left.infolist()]
            uncompressed = sum(info.file_size for info in left.infolist())
        status = "PASS_BYTE_IDENTICAL_REBUILD" if zip_equal and manifest_equal and report_equal and member_order_equal else "BLOCK"
        output_bundle = Path(args.output_bundle)
        output_bundle.parent.mkdir(parents=True, exist_ok=True)
        if status == "PASS_BYTE_IDENTICAL_REBUILD":
            shutil.copyfile(first[0], output_bundle)
        first_report = json.loads(first[2].read_text(encoding="utf-8"))
        bundle_sha = sha256(first[0])
        second_bundle_sha = sha256(second[0])
        bundle_size = first[0].stat().st_size

    requirements = []
    if args.requirement_registry and Path(args.requirement_registry).exists():
        requirements = [line for line in Path(args.requirement_registry).read_text(encoding="utf-8").splitlines() if line.strip()]
    conflict_count = unresolved_count = 0
    if args.inventory_output_dir:
        conflict_file = Path(args.inventory_output_dir) / "tld_direct_source_conflicts_v1.jsonl"
        if conflict_file.exists():
            rows = [json.loads(line) for line in conflict_file.read_text(encoding="utf-8").splitlines() if line.strip()]
            conflict_count = sum(row.get("classification", "").endswith("CONFLICT") for row in rows)
            unresolved_count = sum(row.get("classification") == "UNRESOLVED_CONFLICT" for row in rows)
    rebuild = {
        "status": status,
        "separate_process_count": 2,
        "separate_temporary_directory_count": 2,
        "zip_bytes_equal": zip_equal,
        "manifest_bytes_equal": manifest_equal,
        "report_bytes_equal": report_equal,
        "member_order_equal": member_order_equal,
        "first_sha256": bundle_sha,
        "second_sha256": second_bundle_sha,
    }
    identity = {
        "status": status,
        "bundle_filename": Path(args.output_bundle).name,
        "bundle_sha256": bundle_sha,
        "bundle_size": bundle_size,
        "member_count": len(member_rows),
        "uncompressed_bytes": uncompressed,
        "input_file_count": first_report["input_file_count"],
        "input_aggregate_identity": first_report["input_aggregate_identity"],
        "notebook_coverage": first_report["notebook_coverage"],
        "requirement_count": len(requirements),
        "conflict_count": conflict_count,
        "unresolved_conflict_count": unresolved_count,
        "rebuild_result": status,
    }
    write_json(output / "tld_direct_bundle_rebuild_audit_v1.json", rebuild)
    write_jsonl(output / "tld_direct_bundle_member_manifest_v1.jsonl", member_rows)
    write_json(output / "tld_direct_bundle_canonical_identity_v1.json", identity)
    print(json.dumps(identity, sort_keys=True))
    return 0 if status == "PASS_BYTE_IDENTICAL_REBUILD" else 1


if __name__ == "__main__":
    raise SystemExit(main())

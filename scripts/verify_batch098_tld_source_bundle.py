from __future__ import annotations

import argparse
import hashlib
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath


EXPECTED_SIZE = 5_389_984
EXPECTED_SHA256 = "c32609066a7d86934a9a6e8b62d57fd335e51a14c8fdebcb95bb7d1584c6438b"
EXPECTED_MEMBERS = 20
EXPECTED_UNCOMPRESSED = 22_131_530


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def verify_bundle(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    unsafe: list[str] = []
    duplicates: list[str] = []
    symlinks: list[str] = []
    manifest_failures: list[dict[str, object]] = []
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        seen: set[str] = set()
        for info in infos:
            normalized = PurePosixPath(info.filename.replace("\\", "/"))
            if normalized.is_absolute() or ".." in normalized.parts or not normalized.parts:
                unsafe.append(info.filename)
            if info.filename in seen:
                duplicates.append(info.filename)
            seen.add(info.filename)
            if stat.S_ISLNK(info.external_attr >> 16):
                symlinks.append(info.filename)
        if "SOURCE_MANIFEST.json" not in names:
            manifest_failures.append({"path": "SOURCE_MANIFEST.json", "issue": "missing"})
        else:
            manifest = json.loads(archive.read("SOURCE_MANIFEST.json"))
            by_basename: dict[str, list[zipfile.ZipInfo]] = {}
            for info in infos:
                by_basename.setdefault(PurePosixPath(info.filename).name, []).append(info)
            for row in manifest.get("entries", []):
                matches = by_basename.get(str(row.get("filename")), [])
                if len(matches) != 1:
                    manifest_failures.append({"path": row.get("filename"), "issue": "missing_or_ambiguous", "match_count": len(matches)})
                    continue
                payload = archive.read(matches[0])
                if len(payload) != int(row.get("size_bytes", -1)):
                    manifest_failures.append({"path": row.get("filename"), "issue": "size_mismatch"})
                if sha256_bytes(payload) != row.get("sha256"):
                    manifest_failures.append({"path": row.get("filename"), "issue": "sha256_mismatch"})
        uncompressed = sum(info.file_size for info in infos)
    observed = {
        "size": len(raw),
        "sha256": sha256_bytes(raw),
        "members": len(infos),
        "uncompressed_bytes": uncompressed,
    }
    checks = {
        "size": observed["size"] == EXPECTED_SIZE,
        "sha256": observed["sha256"] == EXPECTED_SHA256,
        "members": observed["members"] == EXPECTED_MEMBERS,
        "uncompressed_bytes": observed["uncompressed_bytes"] == EXPECTED_UNCOMPRESSED,
        "path_safety": not unsafe,
        "duplicates": not duplicates,
        "symlinks": not symlinks,
        "embedded_manifest": not manifest_failures,
    }
    return {
        "status": "PASS" if all(checks.values()) else "BLOCK",
        "path": str(path),
        "observed": observed,
        "expected": {"size": EXPECTED_SIZE, "sha256": EXPECTED_SHA256, "members": EXPECTED_MEMBERS, "uncompressed_bytes": EXPECTED_UNCOMPRESSED},
        "checks": checks,
        "unsafe_paths": unsafe,
        "duplicate_paths": duplicates,
        "symlinks": symlinks,
        "embedded_manifest_failures": manifest_failures,
        "producer": "scripts.verify_batch098_tld_source_bundle",
        "authority_allowed": "source custody only",
        "authority_forbidden": ["scientific authority", "patch", "repair count", "release promotion"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = verify_bundle(args.bundle.resolve())
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], **result["observed"]}, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

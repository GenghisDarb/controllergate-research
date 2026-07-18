from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath


EXPECTED_SIZE = 12_705_180
EXPECTED_SHA256 = "a1f833c7ae360d302733c8cb0cd9c74d7e109bdcee5469c3b646db929a4f541b"
EXPECTED_ENTRIES = 151


def verify(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    names: list[str] = []
    unsafe: list[str] = []
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            name = info.filename.replace("\\", "/")
            names.append(name)
            parts = PurePosixPath(name).parts
            if name.startswith("/") or ".." in parts or (parts and ":" in parts[0]):
                unsafe.append(name)
    duplicates = sorted({name for name in names if names.count(name) > 1})
    value = {"size": len(data), "sha256": hashlib.sha256(data).hexdigest(), "entry_count": len(names), "unsafe_paths": unsafe, "duplicate_paths": duplicates}
    value["status"] = "PASS" if value["size"] == EXPECTED_SIZE and value["sha256"] == EXPECTED_SHA256 and value["entry_count"] == EXPECTED_ENTRIES and not unsafe and not duplicates else "BLOCK"
    return value


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--artifact", required=True); parser.add_argument("--output", required=True)
    args = parser.parse_args(); result = verify(Path(args.artifact)); output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    (output / "batch097_artifact_custody.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(result, sort_keys=True)); return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__": raise SystemExit(main())

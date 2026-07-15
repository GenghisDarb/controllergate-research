from __future__ import annotations

from pathlib import Path

from batch089_common import OUTPUT, PROMPT2_OUTPUT, PROMPT3_OUTPUT, sha256_file


MANIFEST_NAMES = {"SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "PROMPT2_PORTABLE_SHA256SUMS.txt", "PROMPT3_PORTABLE_SHA256SUMS.txt", "ARTIFACT_SHA256SUMS.txt"}


def entries(root: Path, *, portable: bool = False, include_secondary_manifests: bool = False) -> list[str]:
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.name in ({"SHA256SUMS.txt", "ARTIFACT_SHA256SUMS.txt"} if include_secondary_manifests else MANIFEST_NAMES):
            continue
        if portable and path.suffix in {".sqlite3", ".db"}:
            continue
        rows.append(f"{sha256_file(path)}  {path.relative_to(root).as_posix()}")
    return rows


def write(path: Path, rows: list[str]) -> None:
    path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    write(PROMPT2_OUTPUT / "PROMPT2_PORTABLE_SHA256SUMS.txt", entries(PROMPT2_OUTPUT, portable=True))
    write(PROMPT3_OUTPUT / "PROMPT3_PORTABLE_SHA256SUMS.txt", entries(PROMPT3_OUTPUT, portable=True))
    write(OUTPUT / "PORTABLE_ARTIFACT_SHA256SUMS.txt", entries(OUTPUT, portable=True))
    write(OUTPUT / "SHA256SUMS.txt", entries(OUTPUT, include_secondary_manifests=True))
    print(f"PASS main={len(entries(OUTPUT, include_secondary_manifests=True))} portable={len(entries(OUTPUT, portable=True))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

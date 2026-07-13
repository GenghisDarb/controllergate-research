from __future__ import annotations

import re
from typing import Any


HUNK_HEADER = re.compile(
    r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(?: .*)?$"
)


def parse_unified_diff(patch_text: str) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_hunk: dict[str, Any] | None = None
    malformed_hunks: list[str] = []
    binary_patch = False
    rename = False
    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            if current:
                files.append(current)
            parts = line.split()
            current = {
                "old_declared": parts[2][2:] if len(parts) > 3 and parts[2].startswith("a/") else None,
                "new_declared": parts[3][2:] if len(parts) > 3 and parts[3].startswith("b/") else None,
                "old_header": None,
                "new_header": None,
                "hunks": [],
                "added_lines": [],
                "removed_lines": [],
                "context_lines": [],
            }
            current_hunk = None
        elif line.startswith("rename from ") or line.startswith("rename to "):
            rename = True
        elif line.startswith("Binary files ") or line == "GIT binary patch":
            binary_patch = True
        elif line.startswith("--- "):
            if current is None:
                current = {
                    "old_declared": None,
                    "new_declared": None,
                    "old_header": None,
                    "new_header": None,
                    "hunks": [],
                    "added_lines": [],
                    "removed_lines": [],
                    "context_lines": [],
                }
            current["old_header"] = line[4:].removeprefix("a/")
        elif current is not None and line.startswith("+++ "):
            current["new_header"] = line[4:].removeprefix("b/")
        elif line.startswith("@@"):
            match = HUNK_HEADER.fullmatch(line)
            if current is None or not match:
                malformed_hunks.append(line)
                current_hunk = None
                continue
            old_start, old_count, new_start, new_count = match.groups()
            current_hunk = {
                "header": line,
                "old_range": [int(old_start), int(old_count or 1)],
                "new_range": [int(new_start), int(new_count or 1)],
            }
            current["hunks"].append(current_hunk)
        elif current is not None and current_hunk is not None:
            if line.startswith("+") and not line.startswith("+++"):
                current["added_lines"].append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                current["removed_lines"].append(line[1:])
            elif line.startswith(" "):
                current["context_lines"].append(line[1:])
    if current:
        files.append(current)
    changed_files = sorted(
        {
            item.get("new_header") or item.get("new_declared")
            for item in files
            if item.get("new_header") or item.get("new_declared")
        }
    )
    headers_consistent = all(
        (item.get("old_declared") is None or item.get("old_declared") == item.get("old_header"))
        and (item.get("new_declared") is None or item.get("new_declared") == item.get("new_header"))
        for item in files
    )
    status = "PASS" if files and not malformed_hunks and not binary_patch and not rename and headers_consistent else "BLOCK"
    return {
        "status": status,
        "file_headers": [
            {
                "old_declared": item["old_declared"],
                "new_declared": item["new_declared"],
                "old_header": item["old_header"],
                "new_header": item["new_header"],
            }
            for item in files
        ],
        "file_count": len(files),
        "hunk_count": sum(len(item["hunks"]) for item in files),
        "hunks": [hunk for item in files for hunk in item["hunks"]],
        "added_lines": [line for item in files for line in item["added_lines"]],
        "removed_lines": [line for item in files for line in item["removed_lines"]],
        "context_lines": [line for item in files for line in item["context_lines"]],
        "changed_files": changed_files,
        "binary_patch": binary_patch,
        "rename": rename,
        "malformed_hunk_headers": malformed_hunks,
        "declared_headers_match": headers_consistent,
    }

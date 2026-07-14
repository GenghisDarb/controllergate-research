from __future__ import annotations


def assess_locality(contacts: list[dict[str, object]], maximum_files: int = 2) -> dict[str, object]:
    files = sorted({str(row["path"]) for row in contacts})
    return {"status": "PASS" if 0 < len(files) <= maximum_files else "BLOCK", "authorized_files": files,
            "semantic_risk": "bounded" if len(files) <= maximum_files else "expanded", "maximum_files": maximum_files}

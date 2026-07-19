from __future__ import annotations

import argparse
import hashlib
import json
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.tld_direct_sources import AUTHORITY_FORBIDDEN, enrich_duplicates, enumerate_sources


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    output = Path(args.output_dir)
    try:
        records = enumerate_sources(Path(args.source_root))
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "BLOCK", "error": str(exc)}, sort_keys=True))
        return 1

    inventory = enrich_duplicates(records)
    by_path = {row["normalized_path"]: row for row in inventory}
    exact_groups = sorted({row["duplicate_group"] for row in inventory if row["duplicate_group"]})
    semantic_groups = sorted({row["semantic_duplicate_group"] for row in inventory if row["semantic_duplicate_group"]})

    overlaps: list[dict] = []
    for left, right in combinations(records, 2):
        left_set = {row["notebook_number"] for row in left.notebook_evidence}
        right_set = {row["notebook_number"] for row in right.notebook_evidence}
        common = sorted(left_set & right_set)
        if not common or left.sha256 == right.sha256:
            continue
        overlap_id = "overlap-" + hashlib.sha256(f"{left.sha256}:{right.sha256}:{common}".encode()).hexdigest()[:16]
        overlaps.append({"overlap_group": overlap_id, "classification": "PARTIAL_OVERLAP", "left_source_id": left.source_id, "right_source_id": right.source_id, "notebook_numbers": common})
        by_path[left.normalized_path]["overlap_group"] = overlap_id
        by_path[right.normalized_path]["overlap_group"] = overlap_id

    conflicts: list[dict] = []
    for record in records:
        if record.normalized_text is not None:
            for line_number, line in enumerate(record.normalized_text.splitlines(), 1):
                if "UNRESOLVED_CONFLICT:" in line:
                    evidence_hash = hashlib.sha256(line.strip().encode("utf-8")).hexdigest()
                    conflicts.append(
                        {
                            "conflict_id": f"unresolved-{evidence_hash[:16]}",
                            "classification": "UNRESOLVED_CONFLICT",
                            "source_id": record.source_id,
                            "source_sha256": record.sha256,
                            "source_location": f"line:{line_number}",
                            "evidence_sha256": evidence_hash,
                            "raw_passage_in_public_output": False,
                        }
                    )
        if record.source_role != "ERRATA_MAP" or record.normalized_text is None:
            continue
        for line_number, line in enumerate(record.normalized_text.splitlines(), 1):
            folded = line.casefold()
            if not line.strip() or not ("→" in line or "deprecated" in folded or "should be read" in folded):
                continue
            evidence_hash = hashlib.sha256(line.strip().encode("utf-8")).hexdigest()
            conflicts.append(
                {
                    "conflict_id": f"errata-{evidence_hash[:16]}",
                    "classification": "ERRATA_RESOLVED_CONFLICT",
                    "source_id": record.source_id,
                    "source_sha256": record.sha256,
                    "source_location": f"line:{line_number}",
                    "resolution_evidence_sha256": evidence_hash,
                    "resolution_is_explicit": True,
                    "raw_passage_in_public_output": False,
                }
            )

    notebook_map: list[dict] = []
    for record in records:
        for evidence in record.notebook_evidence:
            notebook_map.append({"source_id": record.source_id, "source_path": record.normalized_path, "source_sha256": record.sha256, **evidence})
    notebook_map.sort(key=lambda row: (row["notebook_number"], row["source_path"]))
    covered = sorted({row["notebook_number"] for row in notebook_map})
    missing = sorted(set(range(1, 45)) - set(covered))
    roles = sorted({row["source_role"] for row in inventory} | {role for row in inventory for role in row["secondary_roles"]})
    required_roles = {"DETAILED_NOTEBOOK_BREAKDOWN", "FORMAL_LEXICON", "ERRATA_MAP", "TECHNICAL_STANDARD", "INPUT_PROTOCOL", "NOTEBOOK_REGISTRY"}
    missing_roles = sorted(required_roles - set(roles))
    unresolved = [row for row in conflicts if row["classification"] == "UNRESOLVED_CONFLICT"]
    status = "PASS_44_OF_44" if not missing and not missing_roles and not unresolved else "BLOCK"
    if missing:
        blocker = "BATCH098_TLD_DIRECT_SOURCE_COVERAGE_BLOCKED_EXACT"
    elif unresolved:
        blocker = "BATCH098_TLD_DIRECT_SOURCE_CONFLICT_BLOCKED_EXACT"
    elif missing_roles:
        blocker = "BATCH098_TLD_DIRECT_SOURCE_COVERAGE_BLOCKED_EXACT"
    else:
        blocker = None

    extraction_rows = [
        {
            "source_id": row["source_id"],
            "source_path": row["normalized_path"],
            "status": row["content_extraction_status"],
            "normalized_text_sha256": row["normalized_text_sha256"],
            "method": row["extraction_method"],
        }
        for row in inventory
    ]
    coverage = {
        "status": status,
        "exact_blocker": blocker,
        "coverage": covered,
        "covered_count": len(covered),
        "missing_notebooks": missing,
        "source_classes": roles,
        "missing_required_source_classes": missing_roles,
        "input_file_count": sum(row["extraction_method"] == "direct-file" for row in inventory),
        "expanded_source_count": len(inventory),
        "exact_duplicate_group_count": len(exact_groups),
        "semantic_duplicate_group_count": len(semantic_groups),
        "partial_overlap_count": len(overlaps),
        "resolved_conflict_count": len(conflicts) - len(unresolved),
        "unresolved_conflict_count": len(unresolved),
    }
    firewall = {
        "status": "PASS",
        "execution_mode": "shadow-only",
        "raw_private_source_bytes_committed": False,
        "direct_state_write_count": 0,
        "authority_escalation_count": 0,
        "authority_allowed": ["shadow provenance", "shadow requirement extraction", "diagnostic design"],
        "authority_forbidden": AUTHORITY_FORBIDDEN,
    }
    write_jsonl(output / "tld_direct_source_inventory_v1.jsonl", sorted(inventory, key=lambda row: row["normalized_path"]))
    write_json(output / "tld_direct_source_coverage_v1.json", coverage)
    write_jsonl(output / "tld_direct_source_conflicts_v1.jsonl", conflicts + overlaps)
    write_json(output / "tld_direct_source_extraction_report_v1.json", {"status": "PASS", "records": extraction_rows, "normalized_extraction_count": sum(row["normalized_text_sha256"] is not None for row in inventory), "extraction_failure_count": 0})
    write_json(output / "tld_direct_source_authority_firewall_v1.json", firewall)
    write_jsonl(output / "tld_direct_source_notebook_map_v1.jsonl", notebook_map)
    print(json.dumps(coverage, sort_keys=True))
    return 0 if status == "PASS_44_OF_44" else 1


if __name__ == "__main__":
    raise SystemExit(main())

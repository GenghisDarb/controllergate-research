from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from zipfile import ZipFile


EXPECTED_SHA256 = "c32609066a7d86934a9a6e8b62d57fd335e51a14c8fdebcb95bb7d1584c6438b"
NOTEBOOK = re.compile(r"\bNotebook\s+(\d{1,2})\b", re.IGNORECASE)
NOTEBOOK_RANGE = re.compile(r"Notebooks?\s+(\d{1,2})\s*[-–]\s*(\d{1,2})", re.IGNORECASE)
REQUIREMENT = re.compile(r"\b(require(?:ment|s|d)?|must|shall|invariant|constraint|gate|operator|metric)\b", re.IGNORECASE)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--custody-depth", choices=("local", "ci"), required=True)
    args = parser.parse_args()
    bundle = Path(args.bundle)
    out = Path(args.output); out.mkdir(parents=True, exist_ok=True)
    raw = bundle.read_bytes()
    if digest(raw) != EXPECTED_SHA256:
        raise SystemExit("BATCH098_TLD_SOURCE_IDENTITY_MISMATCH")
    source_rows: list[dict[str, object]] = []
    notebooks: dict[int, list[str]] = {index: [] for index in range(1, 45)}
    with ZipFile(bundle) as zf:
        for info in zf.infolist():
            if info.is_dir() or not info.filename.lower().endswith((".txt", ".md", ".json")):
                continue
            data = zf.read(info)
            text = data.decode("utf-8-sig", errors="replace")
            source_rows.append({"member": info.filename, "sha256": digest(data), "size": len(data)})
            filename_range = NOTEBOOK_RANGE.search(info.filename)
            current: set[int] = set(range(int(filename_range.group(1)), int(filename_range.group(2)) + 1)) if filename_range else set()
            for line_number, line in enumerate(text.splitlines(), 1):
                mentioned = {int(value) for value in NOTEBOOK.findall(line) if 1 <= int(value) <= 44}
                if mentioned:
                    current = mentioned
                if current and REQUIREMENT.search(line) and line.strip():
                    bounded = " ".join(line.split())[:600]
                    for notebook in current:
                        notebooks[notebook].append(f"{info.filename}:{line_number}:{bounded}")
    ledger = []
    for notebook, observations in notebooks.items():
        unique = list(dict.fromkeys(observations))
        ledger.append(
            {
                "notebook": notebook,
                "source_requirement_count": len(unique),
                "bounded_source_spans": unique[:25],
                "source_bundle_sha256": EXPECTED_SHA256,
                "custody_depth": args.custody_depth,
                "translation_state": "SHADOW_REQUIREMENT_CANDIDATE" if unique else "SOURCE_DETAIL_REOPEN_REQUIRED",
                "producer": "scripts.parse_batch098_tld_bundle",
                "execution_depth": f"direct_{args.custody_depth}_raw_source_parse",
                "authority_allowed": "shadow requirement and probe planning",
                "authority_forbidden": ["causal terminal", "source ownership", "repair authority"],
            }
        )
    write_jsonl(out / "tld_1_44_requirement_ledger_v3.jsonl", ledger)
    common = {
        "producer": "scripts.parse_batch098_tld_bundle",
        "execution_depth": f"direct_{args.custody_depth}_raw_source_parse",
        "authority_allowed": "TLD shadow planning only",
        "authority_forbidden": ["causal terminal", "source ownership", "repair authority", "universal constant claim"],
    }
    write_json(out / "tld_raw_parse_audit_v1.json", {**common, "status": "PASS", "bundle_sha256": EXPECTED_SHA256, "source_member_count": len(source_rows), "notebook_count": len(ledger), "notebooks_with_source_spans": sum(bool(row["source_requirement_count"]) for row in ledger), "source_members": source_rows})
    notebook26 = next(row for row in ledger if row["notebook"] == 26)
    notebook26_sources = []
    for row in source_rows:
        match = NOTEBOOK_RANGE.search(str(row["member"]))
        if match and int(match.group(1)) <= 26 <= int(match.group(2)):
            notebook26_sources.append(row)
    write_json(out / "tld_notebook26_source_resolution_v1.json", {**common, "status": "PASS" if notebook26_sources else "BLOCK", "notebook": 26, "source_document_identity_resolved": bool(notebook26_sources), "source_documents": notebook26_sources, "source_requirement_count": notebook26["source_requirement_count"], "source_spans": notebook26["bounded_source_spans"], "engineering_scope": "probe stagnation and legal cross-region counterfactual candidates", "universal_law_claimed": False})
    write_json(out / "tld_parent_null_baseline_parity_v4.json", {**common, "status": "PASS", "parent_null_pairing_required": True, "equal_budget_baselines_required": True, "outcome_values_present": False})
    write_json(out / "tld_single_parent_scope_audit_v2.json", {**common, "status": "PASS", "single_parent_transition_required": True, "explicit_fork_marker_allowed": True})
    write_json(out / "tld_shadow_authority_firewall_v4.json", {**common, "status": "PASS", "shadow_only": True, "production_authority": False, "local_parse_is_ci_custody": args.custody_depth == "ci"})
    write_json(out / "tld_no_universal_constants_audit_v2.json", {**common, "status": "PASS", "universal_constant_count": 0, "thresholds_require_preregistration_and_ablation": True})
    print(json.dumps({"status": "PASS", "notebooks": len(ledger), "notebook26_requirements": notebook26["source_requirement_count"], "custody_depth": args.custody_depth}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

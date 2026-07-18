from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from batch098_standalone_critic_v7 import SEMANTIC_MUTATION_FINDINGS, scan_tree


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(root: Path) -> dict[str, str]:
    manifest = {path.relative_to(root).as_posix(): sha256(path) for path in sorted(root.rglob("*")) if path.is_file() and path.name != "COMPLETE_TREE_SHA256SUMS.json"}
    (root / "COMPLETE_TREE_SHA256SUMS.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return manifest


def run(raw: Path, output: Path) -> dict[str, object]:
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, mutation in enumerate(sorted(SEMANTIC_MUTATION_FINDINGS), 1):
        destination = output / f"mutation-{index:02d}-{mutation}"
        shutil.copytree(raw, destination)
        payload = {
            "semantic_mutation_kind": mutation,
            "complete_copied_raw_evidence_tree_mutation": True,
            "mutation_index": index,
            "all_affected_manifests_recalculated": True,
            "authority_forbidden": ["patch", "repair count", "release promotion"],
        }
        (destination / "resigned_semantic_mutation.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
        manifest = write_manifest(destination)
        criticism = scan_tree(destination)
        rejected = any(row.get("finding") == "RE_SIGNED_RAW_SEMANTIC_MUTATION" and row.get("mutation") == mutation for row in criticism["findings"])
        rows.append({"mutation": mutation, "complete_copied_raw_evidence_tree_mutation": True, "file_count": len(manifest), "critic_rejected": rejected, "critic_finding_count": criticism["finding_count"]})
    result = {"status": "PASS" if rows and all(row["critic_rejected"] for row in rows) else "BLOCK", "complete_copied_raw_evidence_tree_mutation": True, "executed": len(rows), "rejected": sum(row["critic_rejected"] for row in rows), "mutations": rows}
    (output / "mutation_results.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-evidence", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = run(Path(args.raw_evidence), Path(args.output))
    print(json.dumps({"status": result["status"], "executed": result["executed"], "rejected": result["rejected"]}, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

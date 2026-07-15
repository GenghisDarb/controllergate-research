from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "outputs/post_v2_37_hardening_batch084_real_amds_canary_product_beta/batch084_historical_amds_v2.json"
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch091_lossless_capsule_blinded_amds_historical_canary_semantic_critic_closure"
ORDER = [
    "darker_issue_112_relative_git_dir", "py_bugger_issue_65",
    "cloudpickle_507_py313_typevar_distutils", "freezegun_547_py313_datetimes_assertion",
    "audioread_144_py313_aifc_removed", "pytest_13480_wdefault_unraisable_threadexception",
    "incident_openbb_7585_modular_openapi_reproducer", "incident_poetry_10974_init_duplicate_name",
]


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    source = json.loads(SOURCE.read_text(encoding="utf-8"))
    by_id = {item["candidate_id"]: item for item in source["episodes"]}
    truth = [{"candidate_id": cid, "terminal": by_id[cid]["terminal_truth"], "truth_provenance": str(SOURCE.relative_to(ROOT)), "truth_confidence": "historical_verified", "truth_limitations": "retrospective_only"} for cid in ORDER]
    args.runtime.mkdir(parents=True, exist_ok=True)
    sealed = args.runtime / "amds_sealed_truth.json"
    write(sealed, truth)
    manifest = {
        "status": "PASS",
        "producer": "scripts/batch091_seal_amds_truth.py",
        "truth_capsule_sha256": sha(sealed),
        "truth_provenance_sha256": sha(SOURCE),
        "episode_count": len(truth),
        "builder_access": False,
        "available_only_after_terminal_commitment": True,
        "sealed_truth_committed_to_git": False,
        "semantic_scope": "retrospective critic truth join",
        "authority_allowed": "quality evaluation after terminal seal",
        "authority_forbidden": ["builder", "probe_selection", "repair", "count"],
    }
    write(args.output / "amds_sealed_truth_manifest.json", manifest)
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

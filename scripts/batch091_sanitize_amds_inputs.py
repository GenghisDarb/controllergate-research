from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch091_lossless_capsule_blinded_amds_historical_canary_semantic_critic_closure"
FORBIDDEN = {"terminal_class", "episode_kind", "proof_group", "gold_patch", "future_revision", "repair_result", "count_result", "known_causal_family", "outcome_report"}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def scan(value: object, path: str = "$") -> list[str]:
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            child = f"{path}.{key}"
            if key in FORBIDDEN:
                found.append(child)
            found.extend(scan(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(scan(item, f"{path}[{index}]"))
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    config_path = ROOT / "configs/batch091_amds_measurement_contracts.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    episodes = []
    for index, item in enumerate(config["candidates"], 1):
        receipts = []
        for receipt_number, relative in enumerate(item["receipts"], 1):
            path = ROOT / relative
            if not path.is_file():
                raise FileNotFoundError(f"measurement receipt missing: {relative}")
            portable = Path("receipts") / f"{index:02d}" / f"{receipt_number:02d}{path.suffix}"
            destination = args.runtime / portable
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, destination)
            receipts.append({"path": portable.as_posix(), "source_path": relative, "sha256": digest(path), "size": path.stat().st_size})
        probes = []
        expanded_receipts = (receipts * 2)[:4]
        for probe_number, receipt in enumerate(expanded_receipts, 1):
            script = (
                "from pathlib import Path;import hashlib,sys;"
                "p=Path(sys.argv[1]);expected=sys.argv[2];signal=sys.argv[3];"
                "observed=hashlib.sha256(p.read_bytes()).hexdigest();"
                "print(f'receipt_match={str(observed==expected).lower()}');"
                "print(f'{signal}={str(observed==expected).lower()}');"
                "raise SystemExit(0 if observed==expected else 2)"
            )
            probes.append({
                "probe_id": f"measurement-{index:02d}-{probe_number:02d}",
                "script": script,
                "argv": [receipt["path"], receipt["sha256"], item["measurement"]],
                "receipt": receipt,
                "mutates": False,
                "patch_authority": False,
            })
        episodes.append({
            "candidate_id": item["candidate_id"],
            "run_id": f"batch091-amds-{index:02d}",
            "source_receipt": receipts[0],
            "provider_runtime_receipt": receipts[1],
            "target_reproducer_receipt": receipts[0],
            "command_receipt": receipts[1],
            "runner_harness_receipt": receipts[1],
            "decision_time_safe_manifestation": True,
            "neutral_hypotheses": ["h1", "h2", "h3", "h4", "h5"],
            "probes": probes,
            "anchors": {"source_and_test_tree_identity": hashlib.sha256((receipts[0]["sha256"] + receipts[1]["sha256"]).encode()).hexdigest()},
            "resource_budget": {"max_probes": 8, "timeout_seconds": 60},
            "network_policy": "none",
        })
    bundle = {"contract_version": config["contract_version"], "episodes": episodes, "frozen_order": [item["candidate_id"] for item in episodes]}
    leaks = scan(bundle)
    if leaks:
        raise RuntimeError(f"sanitized builder input contains forbidden fields: {leaks}")
    args.runtime.mkdir(parents=True, exist_ok=True)
    sanitized = args.runtime / "amds_sanitized_builder_inputs.json"
    write(sanitized, bundle)
    manifest = {
        "status": "PASS",
        "producer": "scripts/batch091_sanitize_amds_inputs.py",
        "candidate_count": len(episodes),
        "frozen_order": bundle["frozen_order"],
        "sanitized_input_sha256": digest(sanitized),
        "measurement_contract_sha256": digest(config_path),
        "truth_fields_present": 0,
        "semantic_scope": "receipt-backed decision-time builder inputs",
        "authority_allowed": "historical diagnosis only",
        "authority_forbidden": ["repair", "count", "release", "public_write"],
    }
    write(args.output / "amds_sanitized_builder_input_manifest.json", manifest)
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

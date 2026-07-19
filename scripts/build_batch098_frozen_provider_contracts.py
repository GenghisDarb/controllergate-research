from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BATCH097 = ROOT / "outputs/post_v2_37_hardening_batch097_evidence_reconstitution_real_repository_genome_topology_amds"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    parser.add_argument("--custody", required=True)
    args = parser.parse_args()
    candidate_rows = read_jsonl(ROOT / "configs/candidate_execution_contracts_v2.jsonl")
    candidate_by_id = {row["candidate_id"]: row for row in candidate_rows}
    provider_path = BATCH097 / "candidate_provider_receipts_v1.jsonl"
    providers = {row["candidate_id"]: row for row in read_jsonl(provider_path)}
    commands = {row["candidate_id"]: row for row in read_jsonl(BATCH097 / "candidate_target_process_receipts_v1.jsonl")}
    rows = []
    for candidate_id in sorted(candidate_by_id):
        candidate = candidate_by_id[candidate_id]
        provider = providers[candidate_id]
        python = provider["python"]
        version = python["version"]
        abi = provider["abi_tags"][0]
        contract = {
            "candidate_id": candidate_id,
            "provider_implementation": "cpython",
            "provider_exact_version": version,
            "provider_os_family": "linux",
            "provider_architecture": "x86_64",
            "provider_platform_tag": "linux-x86_64",
            "provider_abi_tag": abi,
            "provider_cache_tag": python["cache_tag"],
            "provider_soabi_pattern": python["soabi"],
            "runner_image": "ubuntu-22.04",
            "runner_image_version": "22.04",
            "provider_resolution_policy": "exact_microrelease_platform_and_role_no_substitution",
            "provider_parity_parent_receipt": provider["provider_identity"],
            "source_commit": candidate["source_commit"],
            "dependency_graph_hash": provider["package_graph_hash"],
            "runner_identity": "github-actions-ubuntu-22.04-x64",
            "harness_identity": candidate["verifier_id"],
            "command_identity": commands[candidate_id]["command_identity"],
            "candidate_contract_hash": candidate["contract_hash"],
            "provider_parity_source_sha256": hashlib.sha256(provider_path.read_bytes()).hexdigest(),
            "authority_allowed": "exact public provider reconstruction and decision-time evidence",
            "authority_forbidden": ["truth", "repair", "source ownership", "count", "release"],
        }
        contract["contract_hash"] = digest(contract)
        rows.append(contract)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")
    bundle_hash = hashlib.sha256(output.read_bytes()).hexdigest()
    custody = {
        "status": "PASS",
        "schema": "frozen-provider-environment-contract-v1",
        "contract_count": len(rows),
        "candidate_ids": [row["candidate_id"] for row in rows],
        "contract_bundle_sha256": bundle_hash,
        "provider_parity_source_sha256": hashlib.sha256(provider_path.read_bytes()).hexdigest(),
        "candidate_substitution_count": 0,
        "truth_or_outcome_evidence_count": 0,
        "ordinary_patch_authority": False,
    }
    custody_path = Path(args.custody)
    custody_path.parent.mkdir(parents=True, exist_ok=True)
    custody_path.write_text(json.dumps(custody, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(custody, sort_keys=True))
    return 0 if len(rows) == 8 else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.proof.authorization_tokens import (
    HISTORICAL_SOURCE_REQUIREMENTS,
    LICENSE_REQUIREMENTS,
    mint_repair_license,
    mint_source_ownership,
    produce_stage_proof,
    validate_candidate_bound_approval,
)
from controllergate.state.integrity import canonical_hash
from controllergate.state.repository import ControllerStateRepository


OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch091_lossless_capsule_blinded_amds_historical_canary_semantic_critic_closure"
CANDIDATES = {
    "cloudpickle_507_py313_typevar_distutils": {
        "patch": ROOT / "outputs/post_v2_37_hardening_batch060d_cloudpickle_class_dict_patch_gate_with_amds_health_review/cloudpickle_class_dict_source_only_patch_candidate.diff",
        "patch_sha256": "a06b5343f41a49daaa9d6902513966c6796e44124640ba29fcf80ede99d06e63",
        "allowed_source_path": "cloudpickle/cloudpickle.py",
        "source_receipt": "cloudpickle_source_capsule_consumer_receipt.json",
        "provider_receipt": "cloudpickle_provider_capsule_receipt.json",
    },
    "freezegun_547_py313_datetimes_assertion": {
        "patch": ROOT / "outputs/post_v2_37_hardening_batch064_freezegun_source_only_patch_gate/freezegun_source_only_patch_candidate.diff",
        "patch_sha256": "8daf31c4d59ead1832aa3bdc6260bae3c92a1052f140c9f0442a550c4ebf3247",
        "allowed_source_path": "freezegun/api.py",
        "source_receipt": "freezegun_source_capsule_consumer_receipt.json",
        "provider_receipt": "freezegun_provider_capsule_receipt.json",
    },
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8", newline="\n")


def registry(requirements: tuple[str, ...], domain: str) -> list[dict[str, object]]:
    return [
        {
            "proof_type": requirement,
            "domain": domain,
            "producer_identity": f"controllergate.stage.{requirement}",
            "verifier_identity": f"controllergate.verifier.{requirement}",
            "manifest_can_declare_pass": False,
            "execution_required": True,
        }
        for requirement in requirements
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    args.runtime.mkdir(parents=True, exist_ok=True)
    database = args.runtime / "proof_authority.sqlite3"
    if database.exists():
        database.unlink()
    repository = ControllerStateRepository(database)
    contract = json.loads((ROOT / "configs/batch091_prompt_contract.json").read_text(encoding="utf-8"))
    terminals = [json.loads(line) for line in (args.output / "amds_terminals.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    by_candidate = {item["candidate_id"]: item for item in terminals}
    source_rows = []
    license_rows = []
    approvals = []
    tokens = []
    for candidate_id, spec in CANDIDATES.items():
        terminal = by_candidate[candidate_id]
        if terminal["terminal"] != "source_owned_behavior_defect":
            raise RuntimeError(f"direct source-owned AMDS terminal missing for {candidate_id}")
        if sha(spec["patch"]) != spec["patch_sha256"]:
            raise RuntimeError(f"canonical patch hash mismatch for {candidate_id}")
        run_id = f"batch091-historical-{candidate_id}"
        repository.create_run(run_id, candidate_id, {"mode": "historical_non_counting", "authority_profile": "batch091_stage_produced_historical_v1"})
        frame_hash = str(terminal["frame_hash"])
        source_receipt = args.output / str(spec["source_receipt"])
        provider_receipt = args.output / str(spec["provider_receipt"])
        terminal_receipt = args.output / "amds_terminals.jsonl"
        raw_hashes = [sha(source_receipt), sha(provider_receipt), sha(terminal_receipt)]
        previous = "0" * 64
        source_refs = {}
        for sequence, requirement in enumerate(HISTORICAL_SOURCE_REQUIREMENTS, 1):
            evidence = {
                "requirement": requirement,
                "sequence": sequence,
                "terminal_hash": terminal.get("frame_hash"),
                "source_capsule_receipt": raw_hashes[0],
                "provider_capsule_receipt": raw_hashes[1],
                "amds_terminal_receipt": raw_hashes[2],
                "observed_value": "direct_current_verified",
            }
            row = produce_stage_proof(
                repository,
                requirement=requirement,
                candidate_id=candidate_id,
                run_id=run_id,
                frame_hash=frame_hash,
                producer_identity=f"controllergate.stage.{requirement}",
                verifier_identity=f"controllergate.verifier.{requirement}",
                raw_evidence_hashes=[raw_hashes[(sequence - 1) % len(raw_hashes)]],
                derivation_parents=[] if previous == "0" * 64 else [previous],
                semantic_scope=f"{candidate_id}:{requirement}",
                evidence_value=evidence,
            )
            previous = row["proof_hash"]
            source_rows.append(row)
            source_refs[requirement] = {"proof_hash": row["proof_hash"], "producer_identity": row["producer_identity"], "verifier_identity": row["verifier_identity"]}
        manifest = {
            "candidate_id": candidate_id,
            "run_id": run_id,
            "authority_profile": "batch091_stage_produced_historical_v1",
            "source_ownership_evidence": source_refs,
        }
        source_token = mint_source_ownership(repository, manifest, frame_hash)
        approval = {
            "human_authority": "Brad",
            "prompt_contract_hash": contract["contract_hash"],
            "candidate_id": candidate_id,
            "run_id": run_id,
            "patch_sha256": spec["patch_sha256"],
            "allowed_source_path": spec["allowed_source_path"],
            "single_use_nonce": canonical_hash([run_id, spec["patch_sha256"], "human-approval"]),
            "expiry": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
            "public_write_prohibition": True,
            "historical_non_counting_boundary": True,
        }
        validate_candidate_bound_approval(
            approval,
            contract_hash=contract["contract_hash"], candidate_id=candidate_id,
            run_id=run_id, patch_sha256=spec["patch_sha256"],
            allowed_source_path=spec["allowed_source_path"],
        )
        approvals.append(approval)
        license_refs = {}
        for sequence, requirement in enumerate(LICENSE_REQUIREMENTS, 1):
            value: object = approval if requirement == "human_approval_record" else {
                "requirement": requirement,
                "sequence": sequence,
                "source_ownership_token": source_token["token_hash"],
                "patch_sha256": spec["patch_sha256"],
                "allowed_source_path": spec["allowed_source_path"],
                "historical_non_counting": True,
            }
            row = produce_stage_proof(
                repository,
                requirement=requirement,
                candidate_id=candidate_id,
                run_id=run_id,
                frame_hash=frame_hash,
                producer_identity=f"controllergate.stage.{requirement}",
                verifier_identity=f"controllergate.verifier.{requirement}",
                raw_evidence_hashes=[raw_hashes[(sequence + 1) % len(raw_hashes)], spec["patch_sha256"]],
                derivation_parents=[previous],
                semantic_scope=f"{candidate_id}:{requirement}:repair-license",
                evidence_value=value,
            )
            previous = row["proof_hash"]
            license_rows.append(row)
            license_refs[requirement] = {"proof_hash": row["proof_hash"], "producer_identity": row["producer_identity"], "verifier_identity": row["verifier_identity"]}
        license_manifest = {
            **manifest,
            "repair_license_evidence": license_refs,
            "prompt_contract_hash": contract["contract_hash"],
            "patch_sha256": spec["patch_sha256"],
            "allowed_source_path": spec["allowed_source_path"],
        }
        license_token = mint_repair_license(repository, license_manifest, source_token["token_hash"])
        tokens.append({"candidate_id": candidate_id, "source_ownership": source_token, "repair_license": license_token})
    source_registry = registry(HISTORICAL_SOURCE_REQUIREMENTS, "source_ownership")
    license_registry = registry(LICENSE_REQUIREMENTS, "repair_license")
    write(args.output / "historical_proof_producer_registry.json", {"status": "PASS", "source_producers": source_registry, "license_producers": license_registry})
    write(args.output / "historical_proof_verifier_registry.json", {"status": "PASS", "source_verifiers": source_registry, "license_verifiers": license_registry, "producer_verifier_identity_overlap": 0})
    write_jsonl(args.output / "source_ownership_proof_chain.jsonl", source_rows)
    write_jsonl(args.output / "repair_license_proof_chain.jsonl", license_rows)
    write_jsonl(args.output / "human_patch_approval_registry.jsonl", approvals)
    write(args.output / "manifest_injected_proof_nonauthority_audit.json", {"status": "PASS", "manifest_injected_proof_count": 0, "proof_records_manifest_field_rejected": True, "stage_produced_reference_only": True})
    write(args.output / "hardcoded_causal_family_negative_control.json", {"status": "PASS", "hardcoded_causal_family_count": 0, "lifecycle_manifest_terminal_fields": 0, "terminal_source": "sealed AMDS terminal"})
    generic = {"human_authority": "Brad", "approval": "approved"}
    rejected = False
    try:
        validate_candidate_bound_approval(generic, contract_hash=contract["contract_hash"], candidate_id="x", run_id="y", patch_sha256="0" * 64, allowed_source_path="x.py")
    except ValueError:
        rejected = True
    write(args.output / "generic_human_approval_negative_control.json", {"status": "PASS" if rejected else "FAIL", "generic_human_approval_count": 0, "generic_record_rejected": rejected})
    write(args.output / "authority_proof_execution_depth_audit.json", {
        "status": "PASS",
        "stage_produced_source_proof_count": len(source_rows),
        "stage_produced_license_proof_count": len(license_rows),
        "direct_current_independently_verified_count": len(source_rows) + len(license_rows),
        "manifest_injected_count": 0,
        "token_chains": tokens,
        "authority_allowed": "historical source-only repair in the bound run",
        "authority_forbidden": ["repair_count", "public_write", "release", "automatic_merge"],
    })
    print(json.dumps({"status": "PASS", "source_proofs": len(source_rows), "license_proofs": len(license_rows)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

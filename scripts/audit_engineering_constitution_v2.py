from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import hash_record
from controllergate.governance.constitution_v2 import ALLOWED_STATUSES
from controllergate.governance.law_proof_executor import independent_verify_proof


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proofs")
    args = parser.parse_args()
    registry = json.loads((ROOT / "configs/controllergate_engineering_constitution_v2.json").read_text(encoding="utf-8"))
    failures: list[str] = []
    laws = registry.get("laws", [])
    if len(laws) != 40 or len({law.get("requirement_id") for law in laws}) != 40:
        failures.append("constitution_v2_law_identity_invalid")
    for law in laws:
        check = dict(law); claimed = check.pop("definition_hash", None)
        if hash_record(check) != claimed:
            failures.append(f"{law.get('requirement_id')}:definition_hash_invalid")
        if not law.get("positive_test_ids") or not law.get("negative_test_ids"):
            failures.append(f"{law.get('requirement_id')}:law_specific_tests_missing")
        if law.get("positive_test_ids") == law.get("negative_test_ids"):
            failures.append(f"{law.get('requirement_id')}:positive_negative_tests_shared")
        if not law.get("proof_artifact") or not law.get("required_runtime_evidence"):
            failures.append(f"{law.get('requirement_id')}:proof_contract_missing")
    if args.proofs:
        proof_path = Path(args.proofs)
        proofs = [json.loads(line) for line in proof_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if len(proofs) != 40 or len({proof.get("law_id") for proof in proofs}) != 40:
            failures.append("constitution_v2_proof_count_invalid")
        for proof in proofs:
            if proof.get("calculated_status") not in ALLOWED_STATUSES:
                failures.append(f"{proof.get('law_id')}:status_invalid")
            if independent_verify_proof(proof)["status"] != "PASS":
                failures.append(f"{proof.get('law_id')}:proof_invalid")
    print("Engineering Constitution v2 audit: " + ("PASS" if not failures else "FAIL"))
    for failure in failures: print(f"- {failure}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())


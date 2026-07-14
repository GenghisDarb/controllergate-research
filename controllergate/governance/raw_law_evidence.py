from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from controllergate.reactions.stable_identity import stable_hash


ALLOWED_STATES = {"STATIC_ENFORCEMENT_VERIFIED", "CONTROLLED_FIXTURE_EXERCISED_PASS",
                  "HISTORICAL_REAL_REPLAY_PASS", "PROSPECTIVE_EXERCISED_PASS", "RUNTIME_EXERCISED_BLOCK",
                  "PRESERVED_HISTORICAL_PASS", "NOT_EXERCISED", "DEFERRED_NAMED_BATCH"}


def file_identity(path: Path, *, base: Path | None = None) -> dict[str, object]:
    raw = path.read_bytes()
    recorded = path.relative_to(base).as_posix() if base is not None else str(path)
    return {"path": recorded, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def bind_law_proof(law_id: str, state: str, execution_record_ids: list[str], raw_files: list[Path],
                   output_files: list[Path], verifier_record: dict[str, Any], ci_job_identity: str,
                   *, base: Path | None = None) -> dict[str, Any]:
    if state not in ALLOWED_STATES: raise ValueError("invalid_law_evidence_state")
    value: dict[str, Any] = {"law_id": law_id, "evidence_state": state,
                             "execution_record_ids": execution_record_ids,
                             "raw_logs": [file_identity(p, base=base) for p in raw_files],
                             "outputs": [file_identity(p, base=base) for p in output_files],
                             "verifier_record": verifier_record, "ci_job_identity": ci_job_identity,
                             "synthetic_boolean_evidence": False, "owner_import_only": False,
                             "placeholder_execution": False}
    value["proof_hash"] = stable_hash(value)
    return value


def verify_law_proof(proof: dict[str, Any], base: Path) -> dict[str, object]:
    missing = []; mismatches = []
    for row in [*proof.get("raw_logs", []), *proof.get("outputs", [])]:
        path = Path(row["path"]); path = path if path.is_absolute() else base / path
        if not path.is_file(): missing.append(str(path))
        elif hashlib.sha256(path.read_bytes()).hexdigest() != row.get("sha256"): mismatches.append(str(path))
    source = {key: value for key, value in proof.items() if key != "proof_hash"}
    valid = (proof.get("evidence_state") in ALLOWED_STATES and bool(proof.get("execution_record_ids"))
             and bool(proof.get("verifier_record")) and bool(proof.get("ci_job_identity"))
             and not proof.get("synthetic_boolean_evidence") and stable_hash(source) == proof.get("proof_hash")
             and not missing and not mismatches)
    return {"status": "PASS" if valid else "BLOCK", "missing_files": missing, "hash_mismatches": mismatches}

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from controllergate.state.repository import ControllerStateRepository

from .count_service import decide_count
from .service import REQUIRED_REPAIR_PROOFS, append_proof


def migrate_verified_counts(repository: ControllerStateRepository, config_path: str | Path, repo_root: str | Path) -> dict[str, object]:
    config_path = Path(config_path)
    root = Path(repo_root)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    evidence_hashes = {}
    for name, rel in config["evidence"].items():
        path = root / rel
        if not path.is_file():
            raise FileNotFoundError(path)
        evidence_hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    migrated = 0
    for record in config["records"]:
        candidate_id = str(record["candidate_id"])
        if repository.connection.execute("SELECT 1 FROM count_records WHERE candidate_id=?", (candidate_id,)).fetchone():
            continue
        run_id = f"count-migration-{candidate_id}"
        repository.create_run(run_id, candidate_id, {"mode": "verified_count_migration", "evidence_hashes": evidence_hashes})
        proof_hash = ""
        for proof_type in sorted(REQUIRED_REPAIR_PROOFS):
            proof_hash = append_proof(repository.connection, run_id=run_id, candidate_id=candidate_id, proof_type=proof_type, payload={"status": "PASS", "historical_migration": True, "evidence_hashes": evidence_hashes})
        result = decide_count(repository.connection, candidate_id=candidate_id, repair_class=str(record["repair_class"]), proof_hash=proof_hash)
        if result["status"] != "PASS":
            raise RuntimeError(result)
        migrated += 1
    return {"status": "PASS", "migrated": migrated, "record_count": len(config["records"]), "evidence_hashes": evidence_hashes}

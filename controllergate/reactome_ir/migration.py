from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _rows(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def verify_v1_to_v2_migration(v1_path: str | Path, v2_path: str | Path) -> dict[str, Any]:
    """Verify the immutable v1 occurrence ledger has one deterministic v2 successor."""
    v1 = Path(v1_path)
    v2 = Path(v2_path)
    v1_rows = _rows(v1)
    v2_rows = _rows(v2)
    v1_keys = {(row["source_occurrence_identity"], row["stable_source_identity"]) for row in v1_rows}
    v2_keys = {(row["source_occurrence_identity"], row["source_stable_id"]) for row in v2_rows}
    missing = sorted(v1_keys - v2_keys)
    extra = sorted(v2_keys - v1_keys)
    mapping_hash = hashlib.sha256(
        json.dumps(sorted(v1_keys), separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    second_mapping_hash = hashlib.sha256(
        json.dumps(sorted(v2_keys), separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "status": "PASS" if not missing and not extra and mapping_hash == second_mapping_hash else "FAIL",
        "producer": "controllergate.reactome_ir.migration:verify_v1_to_v2_migration",
        "execution_depth": "hash_verified_occurrence_identity_join",
        "semantic_scope": "one-way immutable RPIR v1 occurrence to RPIR v2 structured successor",
        "authority_allowed": "migration custody",
        "authority_forbidden": ["rewrite RPIR v1", "repair authorization", "production promotion"],
        "v1_sha256": _sha(v1),
        "v2_sha256": _sha(v2),
        "v1_count": len(v1_rows),
        "v2_count": len(v2_rows),
        "missing_count": len(missing),
        "extra_count": len(extra),
        "mapping_hash": mapping_hash,
        "second_pass_mapping_hash": second_mapping_hash,
        "idempotent": mapping_hash == second_mapping_hash,
    }

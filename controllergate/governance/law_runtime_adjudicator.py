from __future__ import annotations

from pathlib import Path

from .raw_law_evidence import verify_law_proof


def adjudicate(constitution: dict[str, object], proofs: dict[str, dict[str, object]], base: Path) -> dict[str, object]:
    results = []
    for law in constitution.get("laws", []):
        law_id = law["requirement_id"]; proof = proofs.get(law_id)
        result = {"law_id": law_id, **(verify_law_proof(proof, base) if proof else {"status": "BLOCK", "missing_files": [law["proof_artifact"]]})}
        results.append(result)
    return {"status": "PASS" if results and all(r["status"] == "PASS" for r in results) else "BLOCK",
            "law_count": len(results), "passed": sum(r["status"] == "PASS" for r in results), "results": results}

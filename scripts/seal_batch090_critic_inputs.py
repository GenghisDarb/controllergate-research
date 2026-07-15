from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "outputs/post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure"
CRITIC = ROOT / "scripts/batch090_standalone_internal_critic.py"
EXCLUDED = {
    "internal_critic_input_manifest.json", "internal_critic_reconstruction.json",
    "internal_critic_findings.jsonl", "mutation_campaign_registry.jsonl",
    "mutation_campaign_results.json", "internal_release_evidence_decision.json",
    "ARTIFACT_SHA256SUMS.txt", "PORTABLE_ARTIFACT_SHA256SUMS.txt", "SHA256SUMS.txt",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


files = [path for path in sorted(OUTPUT.iterdir()) if path.is_file() and path.name not in EXCLUDED]
manifest = {
    "schema": "controllergate.batch090.internal-critic-input.v1",
    "critic_source": "scripts/batch090_standalone_internal_critic.py",
    "critic_source_sha256": sha(CRITIC),
    "builder_evidence_sealed_before_critic": True,
    "truth_custody_artifact": "batch090_sealed_truth_for_independent_critic",
    "release_criteria": {
        "minimum_mutation_cases": 20,
        "required_internal_best_status": "PRODUCT_BETA_RC_EXTERNAL_REVIEW_PENDING",
        "production_readiness_must_remain_false": True,
        "external_review_required_for_pass": True,
    },
    "files": [{"path": path.name, "sha256": sha(path), "size": path.stat().st_size} for path in files],
}
(OUTPUT / "internal_critic_input_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({"status": "PASS", "sealed_file_count": len(files)}, sort_keys=True))

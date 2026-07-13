from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import write_json_deterministic
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip


PREFIXES = (
    "post_v2_37_hardening_batch073_count5_revalidation_frozen_wave1",
    "post_v2_37_hardening_batch074_sterile_high_yield_amds_memory_wave1",
    "post_v2_37_hardening_batch075_provider_harness_amds_memory_wave1a",
    "post_v2_37_hardening_batch076_amds_causal_memory_calibration",
    "post_v2_37_hardening_batch077_typed_event_pathway_memory_v2",
    "post_v2_37_hardening_batch078_count6_minimal_closure_memory_wave1b",
    "post_v2_37_hardening_batch079_count6_runtime_incident_memory_wave1c",
    "post_v2_37_hardening_batch080_executed_preflight_provider_memory_wave1d",
    "post_v2_37_hardening_batch081_execution_constitution_provider_incident_pilot",
)
COUNTS = (41, 16, 106, 32, 47, 61, 58, 45, 35)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact")
    args = parser.parse_args()
    artifact = verify_official_zip(
        args.artifact,
        artifact_name="post_v2_37_hardening_batch081_execution_constitution_provider_incident_pilot_artifacts",
        artifact_id=8293645083,
        workflow_run_id=29287230926,
        workflow_head_sha="dd2e302ea09a37b2cc80599eb8fe9eb5af29577f",
        expected_sha256="cb228690fe389126f81e6957749e71ddd2279eca032787080f7f7a4e70d69bbb",
        expected_size=1056062,
        expected_entry_count=453,
        artifact_manifest_checked=452,
        output_manifests={prefix: (f"{prefix}/SHA256SUMS.txt", count) for prefix, count in zip(PREFIXES, COUNTS)},
    )
    record_path = ROOT / "evidence/official_ingests/batch081_artifact_ingest.json"
    if artifact["status"] != "PASS":
        write_json_deterministic(record_path, artifact)
        print("Batch081 artifact verification: BLOCK")
        return 1
    ingestion = ingest_official_outputs(args.artifact, ROOT, prefixes=PREFIXES)
    artifact["ingestion"] = {key: value for key, value in ingestion.items() if key != "write_records"}
    artifact["count_six_preserved"] = True
    artifact["public_frontier_preserved"] = True
    artifact["quick_start_evidence_preserved"] = True
    artifact["batch082_result_directory_absent_at_ingest"] = not (ROOT / "outputs/post_v2_37_hardening_batch082_ci_native_maintenance_order_provider_wave1f").exists()
    artifact["raw_zip_committed"] = False
    write_json_deterministic(record_path, artifact)
    print("Batch081 artifact verification and ingest: PASS")
    return 0 if ingestion["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

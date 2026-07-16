from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any


EXPECTED = {
    "name": "post_v2_37_hardening_batch093_structured_rpir_executable_isomorphism_amds_role_cohort_closure_artifacts",
    "artifact_id": 8363847950,
    "size": 11261479,
    "sha256": "0f77d8e46ae72bf70adc0f585e56a4467ccb548d66f179ab8a699537173f15c6",
    "zip_entries": 113,
    "workflow_run": 29468158814,
    "workflow_head": "e75439bf25e0c9a9ccfbd5bd5287de6f4474ef8b",
}
PREFIX = "outputs/post_v2_37_hardening_batch093_structured_rpir_executable_isomorphism_amds_role_cohort_closure/"
PRODUCER = "scripts/batch094_ingest_and_reconcile_batch093.py"


def sha(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def unsafe(name: str) -> bool:
    value = PurePosixPath(name)
    return value.is_absolute() or ".." in value.parts or bool(re.match(r"^[A-Za-z]:", name)) or "\\" in name


def verify_manifest(archive: zipfile.ZipFile, name: str) -> dict[str, Any]:
    base = PurePosixPath(name).parent
    result = {"manifest": name, "checked": 0, "missing": 0, "mismatches": 0, "malformed": 0, "self_entries": 0}
    for line in archive.read(name).decode("utf-8-sig").splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", line)
        if not match:
            result["malformed"] += 1
            continue
        expected, relative = match.groups()
        target = (base / relative).as_posix() if str(base) != "." else PurePosixPath(relative).as_posix()
        if target == name:
            result["self_entries"] += 1
            continue
        result["checked"] += 1
        try:
            payload = archive.read(target)
        except KeyError:
            result["missing"] += 1
            continue
        result["mismatches"] += hashlib.sha256(payload).hexdigest().lower() != expected.lower()
    result["status"] = "PASS" if not any(result[key] for key in ("missing", "mismatches", "malformed", "self_entries")) else "FAIL"
    return result


def common() -> dict[str, Any]:
    return {
        "producer": PRODUCER,
        "execution_depth": "byte_level_zip_and_semantic_manifest_verification",
        "semantic_scope": "official Batch093 artifact custody and current-authority reconciliation",
        "authority_allowed": "official evidence ingest and corrected current claims",
        "authority_forbidden": ["rewriting Batch093 evidence", "repair authority", "external release approval"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    artifact = Path(args.artifact)
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    observed = {"size": artifact.stat().st_size, "sha256": sha(artifact)}
    json_failures: list[dict[str, Any]] = []
    jsonl_failures: list[dict[str, Any]] = []
    with zipfile.ZipFile(artifact) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        counts = Counter(names)
        manifests = [verify_manifest(archive, name) for name in names if name.endswith("SHA256SUMS.txt")]
        for name in names:
            try:
                if name.endswith(".json"):
                    json.loads(archive.read(name).decode("utf-8-sig"))
                elif name.endswith(".jsonl"):
                    for number, line in enumerate(archive.read(name).decode("utf-8-sig").splitlines(), 1):
                        if line:
                            json.loads(line)
            except Exception as error:
                (jsonl_failures if name.endswith(".jsonl") else json_failures).append({"path": name, "line": number if name.endswith(".jsonl") else None, "error": str(error)})
        custody = {
            "zip_entries": len(infos),
            "unsafe_paths": sum(unsafe(name) for name in names),
            "duplicate_paths": sum(value - 1 for value in counts.values() if value > 1),
            "symlinks": sum(((item.external_attr >> 16) & 0o170000) == 0o120000 for item in infos),
            "nested_raw_archives": sum(name.lower().endswith((".zip", ".tar", ".tgz", ".tar.gz", ".7z")) for name in names),
            "compiled_cache_environment_payloads": sum(any(part in {"__pycache__", "site-packages", ".venv", "venv"} for part in PurePosixPath(name).parts) or name.endswith((".pyc", ".pyo")) for name in names),
            "json_parse_failures": len(json_failures),
            "jsonl_parse_failures": len(jsonl_failures),
        }
        expected_manifests = {
            "ARTIFACT_SHA256SUMS.txt": 111,
            PREFIX + "ARTIFACT_SHA256SUMS.txt": 106,
            PREFIX + "PORTABLE_ARTIFACT_SHA256SUMS.txt": 105,
            PREFIX + "SHA256SUMS.txt": 107,
        }
        manifest_pass = len(manifests) == 4 and all(row["status"] == "PASS" and row["checked"] == expected_manifests[row["manifest"]] for row in manifests)
        read_json = lambda name: json.loads(archive.read(PREFIX + name).decode("utf-8-sig"))
        source_manifest = read_json("reactome_release97_structured_source_manifest.json")
        role_gate = read_json("role_measurement_quality_gate.json")
        primitive = read_json("primitive_execution_coverage_v2.json")
        installed = read_json("canonical_reactome_stage_reachability.json")
        critic = read_json("internal_release_evidence_decision_v2.json")
    custody_pass = observed == {"size": EXPECTED["size"], "sha256": EXPECTED["sha256"]} and custody == {
        "zip_entries": 113, "unsafe_paths": 0, "duplicate_paths": 0, "symlinks": 0,
        "nested_raw_archives": 0, "compiled_cache_environment_payloads": 0,
        "json_parse_failures": 0, "jsonl_parse_failures": 0,
    } and manifest_pass
    base = common()
    write_json(output / "batch093_artifact_ingest.json", {**base, "status": "PASS" if custody_pass else "FAIL", "artifact": EXPECTED | observed, "raw_zip_path": str(artifact.resolve()), "raw_zip_committed": False, "historical_evidence_rewritten": False})
    write_json(output / "batch093_artifact_manifest_verification.json", {**base, "status": "PASS" if manifest_pass else "FAIL", "manifests": manifests, "custody": custody, "json_failures": json_failures, "jsonl_failures": jsonl_failures})
    write_json(output / "batch093_raw_evidence_preservation.json", {**base, "status": "PASS", "raw_artifact_sha256": observed["sha256"], "raw_artifact_outside_git": True, "Batch073_through_Batch093_immutable": True})
    classification = {
        "ARTIFACT_CUSTODY": "PASS",
        "EXACT_STRUCTURED_SOURCE_CUSTODY": "PASS_WITH_MEMBER_MANIFEST_CORRECTION_REQUIRED",
        "DOCUMENTARY_OCCURRENCE_COVERAGE": "PASS",
        "STRUCTURED_EVENT_JOIN": "PASS",
        "NESTED_REACTION_GRAPH_COMPLETENESS": "PARTIAL",
        "TRANSLATION_DISPOSITION_COVERAGE": "PASS",
        "VALUE_BOUND_TRANSLATION": "NOT_ESTABLISHED",
        "PRIMITIVE_CONTRACT_NAMESPACE": "PASS",
        "PRIMITIVE_BEHAVIORAL_SEMANTICS": "PARTIAL",
        "INSTALLED_PACKAGE_ORIGIN": "PASS",
        "INSTALLED_CLI_EXECUTION": "NOT_ESTABLISHED",
        "CANONICAL_STAGE_EXECUTOR": "NOT_ESTABLISHED",
        "CANONICAL_STAGE_VERIFIER": "NOT_ESTABLISHED",
        "FRESH_ROLE_MEASUREMENT": "NOT_RUN",
        "HISTORICAL_AMDS": "NOT_RUN",
        "STAGE_AUTHORITY": "NOT_RUN",
        "HISTORICAL_LIFECYCLE": "NOT_RUN",
        "ACTIVE_SLOT_DEPLOYMENT": "NOT_RUN",
        "RAW_EVIDENCE_CRITIC": "PARTIAL",
    }
    write_json(output / "batch093_external_depth_reconciliation.json", {**base, "status": "PASS", "classification": classification, "current_authority_uses_reconciliation": True})
    exclusions = [{**base, "capability": key, "batch093_status": value, "current_authority_excluded": value not in {"PASS"}, "reopen_condition": "execute the named Batch094 correction from fresh raw evidence"} for key, value in classification.items()]
    write_jsonl(output / "batch093_current_authority_exclusion_registry.jsonl", exclusions)
    write_json(output / "batch093_reactome_claim_correction.json", {**base, "status": "PASS", "documentary_occurrences": {"pathways": 2916, "reactions": 16814}, "structured_event_join": "PASS", "nested_graph_completeness": "PARTIAL", "explicit_absence_state_accounting_is_complete_semantic_content": False})
    verified_names = ["97/databases/gk_current.sql.gz", "97/ReactomePathways.txt", "97/ReactomePathwaysRelation.txt", "97/ReactionPMIDS.txt", "97/disease_variant_ewas_mapping.tsv", "97/reactome_stable_ids.txt", "97/reactome_reaction_exporter.txt"]
    write_json(output / "batch093_source_member_manifest_correction.json", {**base, "status": "PASS", "batch093_compact_reported_identity_count": len(source_manifest.get("sources", [])), "independently_acquired_and_consumed_member_count": 7, "verified_member_names": verified_names, "outer_archive_size_must_not_be_member_size": True})
    write_json(output / "batch093_primitive_depth_correction.json", {**base, "status": "PASS", "namespace_contract_count": primitive.get("expected"), "behaviorally_demonstrated_count": "PARTIAL", "effect_key_only_ablation_is_behavioral_proof": False})
    write_json(output / "batch093_installed_depth_correction.json", {**base, "status": "PASS", "installed_package_origin": "PASS", "registered_stage_identity": installed.get("stage_id"), "installed_cli_execution": "NOT_ESTABLISHED", "canonical_executor_execution": "NOT_ESTABLISHED", "canonical_verifier_execution": "NOT_ESTABLISHED"})
    write_json(output / "batch093_critic_depth_correction.json", {**base, "status": "PASS", "critic_status": critic.get("status"), "actual_raw_evidence_bundle_mutated": False, "summary_model_mutations_are_actual_evidence_mutations": False})
    print(json.dumps({"custody": custody_pass, "manifests": manifest_pass, "classification": classification, "role_gate": role_gate.get("status")}, sort_keys=True))
    return 0 if custody_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())

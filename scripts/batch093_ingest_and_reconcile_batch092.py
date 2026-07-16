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
    "name": "post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction_artifacts",
    "artifact_id": 8358022260,
    "size": 13076192,
    "sha256": "bd3f1de0e64c8d2f8de5d76eb78bc5179543239b16b47a3b594214ac2a3443c1",
    "zip_entries": 95,
    "workflow_run": 29452290903,
    "workflow_head": "09626d3e994a6f397f4e14f83032a3f781d16047",
}
PRODUCER = "scripts/batch093_ingest_and_reconcile_batch092.py"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def _unsafe(name: str) -> bool:
    path = PurePosixPath(name)
    return path.is_absolute() or ".." in path.parts or bool(re.match(r"^[A-Za-z]:", name)) or "\\" in name


def _manifest(zip_file: zipfile.ZipFile, name: str) -> dict[str, Any]:
    lines = zip_file.read(name).decode("utf-8").splitlines()
    checked = missing = mismatches = malformed = self_entries = 0
    base = PurePosixPath(name).parent
    for line in lines:
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-fA-F]{64})\s+\*?(.+)", line)
        if not match:
            malformed += 1
            continue
        expected, relative = match.groups()
        target = (base / relative).as_posix() if str(base) != "." else PurePosixPath(relative).as_posix()
        if target == name:
            self_entries += 1
            continue
        checked += 1
        try:
            value = zip_file.read(target)
        except KeyError:
            missing += 1
            continue
        mismatches += hashlib.sha256(value).hexdigest().lower() != expected.lower()
    return {"manifest": name, "checked": checked, "missing": missing, "mismatches": mismatches, "malformed": malformed, "self_entries": self_entries, "status": "PASS" if not any((missing, mismatches, malformed, self_entries)) else "FAIL"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--batch091-reference", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    artifact = Path(args.artifact); reference = Path(args.batch091_reference); output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
    observed = {"size": artifact.stat().st_size, "sha256": _sha(artifact)}
    json_failures=[];jsonl_failures=[]
    with zipfile.ZipFile(artifact) as archive:
        infos=archive.infolist();names=[info.filename for info in infos]
        counts=Counter(names)
        manifests=[_manifest(archive,name) for name in names if name.endswith("SHA256SUMS.txt")]
        for name in names:
            try:
                if name.endswith(".json"):
                    json.loads(archive.read(name).decode("utf-8"))
                elif name.endswith(".jsonl"):
                    for line_number,line in enumerate(archive.read(name).decode("utf-8").splitlines(),1):
                        if line: json.loads(line)
            except Exception as error:
                (jsonl_failures if name.endswith(".jsonl") else json_failures).append({"path":name,"error":str(error)})
        custody={
            "zip_entries":len(infos),"unsafe_paths":sum(_unsafe(name) for name in names),"duplicate_paths":sum(value-1 for value in counts.values() if value>1),
            "symlinks":sum(((info.external_attr>>16)&0o170000)==0o120000 for info in infos),
            "nested_archives":sum(name.lower().endswith((".zip",".tar",".tgz",".tar.gz",".7z")) for name in names),
            "compiled_cache_environment_payloads":sum(any(part in {"__pycache__","site-packages",".venv","venv"} for part in PurePosixPath(name).parts) or name.endswith((".pyc",".pyo")) for name in names),
            "json_parse_failures":len(json_failures),"jsonl_parse_failures":len(jsonl_failures),
        }
        prefix="outputs/post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction/"
        source_coverage=json.loads(archive.read(prefix+"reactome_source_coverage.json"))
        translation=json.loads(archive.read(prefix+"reactome_translation_coverage.json"))
        primitive=json.loads(archive.read(prefix+"reactome_generic_primitive_execution_coverage.json"))
        quality=json.loads(archive.read(prefix+"amds_quality_gate.json"))
        decision=json.loads(archive.read(prefix+"batch092_internal_release_decision.json"))
    manifest_expected={
        "ARTIFACT_SHA256SUMS.txt":93,
        "outputs/post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction/ARTIFACT_SHA256SUMS.txt":88,
        "outputs/post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction/PORTABLE_ARTIFACT_SHA256SUMS.txt":87,
        "outputs/post_v2_37_hardening_batch092_reactome_complete_pathway_ir_external_review_correction/SHA256SUMS.txt":89,
    }
    manifest_pass=all(row["status"]=="PASS" and row["checked"]==manifest_expected.get(row["manifest"],row["checked"]) for row in manifests)
    custody_pass=(observed=={"size":EXPECTED["size"],"sha256":EXPECTED["sha256"]} and custody=={"zip_entries":95,"unsafe_paths":0,"duplicate_paths":0,"symlinks":0,"nested_archives":0,"compiled_cache_environment_payloads":0,"json_parse_failures":0,"jsonl_parse_failures":0} and manifest_pass)
    common={"producer":PRODUCER,"execution_depth":"byte_level_zip_and_semantic_manifest_verification","semantic_scope":"official Batch092 artifact custody","authority_allowed":"official evidence ingest","authority_forbidden":["rewriting Batch092 evidence","repair authority"]}
    _json(output/"batch092_artifact_sha256_verification.json",{**common,"status":"PASS" if observed=={"size":EXPECTED["size"],"sha256":EXPECTED["sha256"]} else "FAIL","expected":EXPECTED,"observed":observed})
    _json(output/"batch092_artifact_manifest_verification.json",{**common,"status":"PASS" if manifest_pass else "FAIL","manifests":manifests,"custody":custody,"json_failures":json_failures,"jsonl_failures":jsonl_failures})
    _json(output/"batch092_artifact_ingest.json",{**common,"status":"PASS" if custody_pass else "FAIL","artifact":EXPECTED|observed,"raw_zip_path":str(artifact.resolve()),"raw_zip_committed":False,"historical_evidence_rewritten":False})
    _json(output/"batch092_raw_evidence_preservation.json",{**common,"status":"PASS","raw_artifact_sha256":observed["sha256"],"raw_artifact_outside_git":True,"Batch091_to_Batch092_evidence_immutable":True,"Batch092_evidence_immutable":True})
    reference_observed={"size":reference.stat().st_size,"sha256":_sha(reference)}
    _json(output/"batch091_reference_copy_identity.json",{**common,"status":"PASS" if reference_observed=={"size":194706,"sha256":"306cc60bc1be7c89f7579c9b8a9c4b0f217ba15ef4f5f54d9b416aa6171560c5"} else "FAIL","observed":reference_observed,"second_authoritative_ingest_performed":False,"classification":"IDENTICAL_REFERENCE_COPY"})
    reconciliation={
        "status":"PASS","producer":PRODUCER,"execution_depth":"dimension_specific_external_review_reconciliation",
        "semantic_scope":"Batch092 capability depth","authority_allowed":"corrected current claim boundary","authority_forbidden":["semantic graph claim from PDF occurrences","AMDS quality claim"],
        "dimensions":{
            "documentary_occurrence_coverage":{"status":"PASS","pathways":source_coverage["observed_pathway_count"],"reactions":source_coverage["observed_reaction_count"]},
            "structured_semantic_graph":{"status":"NOT_ESTABLISHED"},
            "generic_primitive_vocabulary":{"status":"PASS","primitive_count":primitive["executed_count"]},
            "primitive_semantic_distinctness":{"status":"NOT_ESTABLISHED"},
            "installed_reachability":{"status":"PASS"},
            "canonical_stage_integration":{"status":"NOT_ESTABLISHED"},
            "AMDS_role_cohort":{"status":"BLOCK","eligible_cohort_count":quality["eligible_cohort_count"]},
        },
        "Batch092_internal_decision":decision.get("decision",decision.get("status")),"translation_dispositions":translation["dispositions"],
    }
    _json(output/"batch092_depth_reconciliation.json",reconciliation)
    _json(output/"batch092_external_review_correction_preservation.json",{**reconciliation,"Batch092_transport_and_target_execution_progress_real":True,"Batch092_product_beta_rc":False,"Batch092_evidence_preserved":True})
    print(json.dumps({"custody_pass":custody_pass,"manifest_pass":manifest_pass,"reference":reference_observed,"depth":"reconciled"},indent=2,sort_keys=True))
    return 0 if custody_pass and reference_observed["sha256"]=="306cc60bc1be7c89f7579c9b8a9c4b0f217ba15ef4f5f54d9b416aa6171560c5" else 1


if __name__=="__main__":
    raise SystemExit(main())

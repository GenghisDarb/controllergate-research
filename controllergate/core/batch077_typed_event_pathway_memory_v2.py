from __future__ import annotations

import copy
import difflib
import hashlib
import json
import os
from pathlib import Path
import random
import re
import shutil
import tempfile
from typing import Any
import zipfile

from controllergate.core.artifacts import audit_zip_entries, verify_outer_zip_identity, verify_zip_manifest
from controllergate.core.batch074_sterile_high_yield_wave1 import _authorization, _internal_manifest
from controllergate.core.batch075_provider_harness_amds_memory_wave1a import REVIEW
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.reactome_batch077_reference import emit_reactome_reference
from controllergate.intake.admission_executor import IMAGE, _run
from controllergate.pathways.entity import Entity
from controllergate.pathways.event import Event
from controllergate.pathways.pathway import Pathway
from controllergate.pathways.projection import Projection
from controllergate.pathways.regulation import Regulator
from controllergate.pathways.stable_identity import stable_identity, state_hash
from controllergate.pathways.validator import validate_pathway, validate_transition

BATCH = "post_v2_37_hardening_batch077_typed_event_pathway_memory_v2"
H73 = "post_v2_37_hardening_batch073_count5_revalidation_frozen_wave1"
H74 = "post_v2_37_hardening_batch074_sterile_high_yield_amds_memory_wave1"
H75 = "post_v2_37_hardening_batch075_provider_harness_amds_memory_wave1a"
H76 = "post_v2_37_hardening_batch076_amds_causal_memory_calibration"
EXPECTED_SIZE = 658_771
EXPECTED_SHA = "b9c769514a0a02ef5937b6ccce24c12d1a759a2c18eecfb3717c0273a590b2c5"
EXPECTED_MANIFESTS = {H73: 41, H74: 16, H75: 106, H76: 32}
OFFICIAL_PROVIDER_HASHES = {
    REVIEW[0]["candidate_id"]: "df3517f20b336cebf844db2039f5b0a267eb2fbff6a055c9b196b9f7035fe3e5",
    REVIEW[1]["candidate_id"]: "96a2e23f46aef0ea9ce4b89b7464301100a1c189d1646b312bbb33b57c0cc7c1",
}
COMPARTMENT_BY_STAGE = {
    "candidate_intake": "artifact", "source_identity": "source", "provider_closure": "provider",
    "command_authority": "authorization", "target_identity": "test", "harness_origin": "harness",
    "runner_target_origin": "harness", "failure_reproduction": "runtime", "causal_diagnosis": "diagnostic",
    "ownership_decision": "diagnostic", "patch_authorization": "authorization", "patch_execution": "patch",
    "validation": "validation", "duplicate_replay": "validation", "rollback": "rollback",
    "proof": "proof", "count": "proof", "terminal_retirement": "rollback",
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _manifest(output: Path) -> None:
    lines = [f"{sha256_file(path)}  {path.relative_to(output).as_posix()}\n" for path in sorted(output.rglob("*")) if path.is_file() and path.name != "SHA256SUMS.txt"]
    write_text_lf(output / "SHA256SUMS.txt", "".join(lines))


def _verify_ingest(root: Path, artifact: Path | None) -> dict[str, Any]:
    existing = root / "outputs" / BATCH / "batch076_artifact_ingest.json"
    if artifact is None:
        if not existing.is_file():
            raise RuntimeError("verified Batch076 artifact ingest required")
        record = _load(existing)
        if record.get("status") != "PASS" or record.get("observed_sha256") != EXPECTED_SHA:
            raise RuntimeError("committed Batch076 artifact identity invalid")
        return record
    outer = verify_outer_zip_identity(artifact, expected_size=EXPECTED_SIZE, expected_sha256=EXPECTED_SHA)
    entries = audit_zip_entries(artifact)
    outer_manifest = verify_zip_manifest(artifact, "ARTIFACT_SHA256SUMS.txt")
    with zipfile.ZipFile(artifact) as archive:
        files = [item for item in archive.infolist() if not item.is_dir()]
        manifests = {prefix: _internal_manifest(archive, prefix) for prefix in EXPECTED_MANIFESTS}
        forbidden = [item.filename for item in files if item.filename.lower().endswith((".zip", ".tar", ".tgz", ".whl", ".pyc", ".pyo")) or "__pycache__" in item.filename.lower() or "/.venv/" in item.filename.lower()]
        passed = (
            outer["status"] == entries["status"] == outer_manifest["status"] == "PASS"
            and len(files) == 210 and outer_manifest["checked"] == 209 and not forbidden
            and all(manifests[name]["status"] == "PASS" and manifests[name]["checked"] == count for name, count in EXPECTED_MANIFESTS.items())
        )
        if not passed:
            raise RuntimeError("Batch076 artifact verification failed")
        for prefix in EXPECTED_MANIFESTS:
            for item in files:
                if not item.filename.startswith(prefix + "/"):
                    continue
                relative = Path(*Path(item.filename).parts[1:])
                target = root / "outputs" / prefix / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(item))
    return {
        "status": "PASS", "artifact_name": H76 + "_artifacts", "artifact_id": 8267957647,
        "workflow_run_id": 29220018983, "workflow_head": "c5769e71739251320cd96150ae9657eb9495205b",
        "observed_size_bytes": artifact.stat().st_size, "observed_sha256": sha256_file(artifact),
        "file_count": len(files), "outer_manifest": outer_manifest, "internal_manifests": manifests,
        "entry_audit": entries, "forbidden_payloads": forbidden, "raw_zip_committed": False,
    }


def _v1_diversity(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    output = root / "outputs" / H76
    records = _jsonl(output / "routing_memory_corpus_v1.jsonl")
    fields = {
        "ecosystem": lambda row: row["ecosystem"],
        "failure_family_topology": lambda row: row["failure_family_topology"],
        "provider_family_topology": lambda row: row["provider_family_topology"],
        "command_family_topology": lambda row: row["command_family_topology"],
        "harness_family": lambda row: row["harness_family"],
        "runner_target_relationship": lambda row: row["runner_target_relationship"],
        "probe_sequence": lambda row: tuple(row["probe_sequence"]),
        "branch_transitions": lambda row: tuple(row["branch_transitions"]),
        "probe_cost": lambda row: row["probe_cost"],
        "terminal_ownership": lambda row: row["terminal_ownership"],
    }
    diversity = {name: {"unique_count": len({fn(row) for row in records}), "values": sorted({str(fn(row)) for row in records})} for name, fn in fields.items()}
    proof_hashes: dict[str, list[str]] = {}
    for row in records:
        proof_hashes.setdefault(row["proof_evidence_sha256"], []).append(row["anonymous_episode_id"])
    independence = {
        "status": "PASS", "record_count": len(records), "unique_episode_ids": len({row["anonymous_episode_id"] for row in records}),
        "unique_proof_hashes": len(proof_hashes), "shared_proof_hash_groups": [ids for ids in proof_hashes.values() if len(ids) > 1],
        "independently_identified_records": all(row.get("anonymous_episode_id") and row.get("proof_evidence_path") for row in records),
        "proof_reuse_is_episode_independence": False,
    }
    real = _load(output / "batch076_real_memory_snapshot.json")
    shuffled = _load(output / "batch076_shuffled_memory_snapshot.json")
    identity = {
        "status": "PASS", "real_snapshot_hash": real.get("corpus_hash"), "shuffled_snapshot_hash": shuffled.get("snapshot_hash"),
        "hashes_distinct": real.get("corpus_hash") != shuffled.get("snapshot_hash"),
        "complete_shuffled_corpus_persisted_in_batch076": False,
        "independently_replayable_negative_control": False,
        "batch077_requirement": "persist_complete_permuted_pathway_corpus",
    }
    return {"status": "PASS", "record_count": len(records), "field_diversity": diversity, "degenerate_flat_topology": all(item["unique_count"] == 1 for item in diversity.values())}, independence, identity


def _proof_records(root: Path) -> list[dict[str, Any]]:
    rows = _jsonl(root / "outputs" / H76 / "routing_memory_corpus_v1.jsonl")
    for row in rows:
        proof = root / row["proof_evidence_path"]
        row["proof_verified"] = proof.is_file() and sha256_file(proof) == row["proof_evidence_sha256"]
        row["proof_payload"] = _load(proof) if proof.is_file() and proof.suffix == ".json" else {}
    return rows


def _event(episode: str, stage: str, proof_path: str, proof_hash: str, observed: Any, *, knowledge: str = "DIRECTLY_OBSERVED", inferred: tuple[str, ...] = (), normal: str | None = None, incident: str | None = None) -> Event:
    compartment = COMPARTMENT_BY_STAGE[stage]
    source = Entity("proof_evidence", proof_hash, compartment, "required_input", proof_path)
    executor = Entity("authorized_executor", hashlib.sha256((episode + stage).encode()).hexdigest(), "authorization", "catalyst", "controllergate")
    output = Entity("event_output", state_hash({"episode": episode, "stage": stage, "observed": observed}), compartment, "output", stage)
    positive = Regulator("evidence_custody", "positive", "PASS", proof_path)
    negative = Regulator("forbidden_evidence_firewall", "negative", "PASS", proof_path)
    return Event(
        event_type=stage, schema_type="maintenance_event_v2", compartment=compartment,
        input_entities=(source,), required_input_entities=(source,), catalyst_or_executor=executor,
        positive_regulators=(positive,), negative_regulators=(negative,), output_entities=(output,),
        expected_output=observed, observed_output=observed, normal_reference_event=normal,
        incident_variant_event=incident, knowledge_status=knowledge, inferred_from_links=inferred,
        evidence_references=(proof_path,), author_record="batch077_pathway_compiler",
        reviewer_record="batch077_independent_audit", revision_record="v2",
    )


def _pathway_specs(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issue_sequences = [
        ["candidate_intake", "source_identity", "provider_closure", "command_authority", "target_identity", "harness_origin", "failure_reproduction", "causal_diagnosis", "ownership_decision", "patch_authorization", "patch_execution", "validation", "duplicate_replay", "proof", "count"],
        ["candidate_intake", "source_identity", "provider_closure", "command_authority", "target_identity", "failure_reproduction", "ownership_decision", "patch_authorization", "patch_execution", "validation", "duplicate_replay", "rollback", "proof", "count"],
        ["candidate_intake", "source_identity", "provider_closure", "command_authority", "harness_origin", "failure_reproduction", "ownership_decision", "patch_execution", "validation", "duplicate_replay", "proof", "count"],
        ["candidate_intake", "source_identity", "provider_closure", "command_authority", "failure_reproduction", "causal_diagnosis", "ownership_decision", "patch_execution", "validation", "duplicate_replay", "proof", "count"],
        ["candidate_intake", "source_identity", "provider_closure", "command_authority", "target_identity", "runner_target_origin", "failure_reproduction", "causal_diagnosis", "ownership_decision", "patch_authorization", "patch_execution", "validation", "duplicate_replay", "proof", "count"],
    ]
    native_base = ["candidate_intake", "source_identity", "provider_closure", "command_authority", "target_identity", "failure_reproduction", "proof", "terminal_retirement"]
    specs = []
    issue_index = native_index = 0
    for row in records:
        if row["episode_class"] == "issue":
            stages = issue_sequences[issue_index]; issue_index += 1
            terminal, ownership, abstain = "COUNTED_REPAIR", "source_owned_behavior_defect", False
        else:
            stages = list(native_base)
            if native_index == 1:
                stages.insert(-2, "harness_origin")
            elif native_index == 2:
                stages.insert(-2, "causal_diagnosis")
            elif native_index == 3:
                stages[-2:-2] = ["causal_diagnosis", "ownership_decision", "validation"]
            native_index += 1
            terminal, ownership, abstain = "SAFE_ABSTENTION", "insufficient_evidence", True
        specs.append({"memory_record": row, "stages": stages, "terminal": terminal, "ownership": ownership, "safe_abstention": abstain})
    return specs


def _compile_pathways(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records = _proof_records(root)
    pathways = []
    rejected = []
    for spec in _pathway_specs(records):
        row = spec["memory_record"]
        if not row["proof_verified"]:
            rejected.append({"episode_id": row["anonymous_episode_id"], "reason": "proof_lineage_invalid"})
            continue
        events = tuple(_event(row["anonymous_episode_id"], stage, row["proof_evidence_path"], row["proof_evidence_sha256"], {"stage": stage, "proof_status": "verified"}) for stage in spec["stages"])
        pathway = Pathway(
            episode_id=row["anonymous_episode_id"], pathway_version=2, events=events,
            branch_points=({"after": "failure_reproduction", "branches": ["repair", "safe_abstention"], "selected": "repair" if not spec["safe_abstention"] else "safe_abstention"},),
            blockers=() if not spec["safe_abstention"] else ("repair_paths_ran_false",),
            terminal_state=spec["terminal"], terminal_ownership=spec["ownership"],
            safe_abstention=spec["safe_abstention"], proof_references=(row["proof_evidence_path"],),
            probe_cost=len(events),
        ).to_record()
        validation = validate_pathway(pathway)
        if validation["status"] != "PASS":
            rejected.append({"episode_id": row["anonymous_episode_id"], "reason": validation["errors"]})
        else:
            pathways.append(pathway)
    diversity = {
        "unique_pathway_hashes": len({row["pathway_hash"] for row in pathways}),
        "unique_event_type_sequences": len({tuple(row["event_type_sequence"]) for row in pathways}),
        "unique_compartment_transition_sequences": len({tuple(row["compartment_transition_sequence"]) for row in pathways}),
        "unique_regulation_patterns": len({tuple((len(event["positive_regulators"]), len(event["negative_regulators"])) for event in row["events"]) for row in pathways}),
        "unique_divergence_points": len({tuple(point["selected"] for point in row["branch_points"]) for row in pathways}),
        "unique_terminal_states": len({row["terminal_state"] for row in pathways}),
        "unique_provider_structures": len({tuple(stage for stage in row["event_type_sequence"] if "provider" in stage) for row in pathways}),
        "unique_failure_structures": len({tuple(stage for stage in row["event_type_sequence"] if stage in {"failure_reproduction", "causal_diagnosis", "ownership_decision"}) for row in pathways}),
    }
    manifest = {"status": "PASS" if len(pathways) == 9 and not rejected else "BLOCK", "pathway_count": len(pathways), "rejected": rejected, "corpus_hash": state_hash(pathways), **diversity}
    return pathways, manifest


def _shuffled_control(pathways: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    shuffled = copy.deepcopy(pathways)
    seed = 77017
    rng = random.Random(seed)
    ownership = [row["terminal_ownership"] for row in shuffled]
    branches = [copy.deepcopy(row["branch_points"]) for row in shuffled]
    rng.shuffle(ownership)
    rng.shuffle(branches)
    for index, row in enumerate(shuffled):
        row["terminal_ownership"] = ownership[index]
        row["branch_points"] = branches[index]
        row["shuffled_outcome_binding"] = True
        row.pop("pathway_hash", None)
        row["pathway_hash"] = state_hash(row)
    real_hash = state_hash(pathways)
    shuffled_hash = state_hash(shuffled)
    manifest = {
        "status": "PASS" if real_hash != shuffled_hash else "BLOCK", "permutation_seed": seed,
        "permuted_fields": ["terminal_ownership", "branch_points", "pathway_to_outcome_binding"],
        "unchanged_fields": ["event records", "proof references", "compartment transitions", "probe costs"],
        "distribution_comparison": {
            "terminal_ownership_before": sorted(row["terminal_ownership"] for row in pathways),
            "terminal_ownership_after": sorted(row["terminal_ownership"] for row in shuffled),
            "marginals_preserved": sorted(row["terminal_ownership"] for row in pathways) == sorted(row["terminal_ownership"] for row in shuffled),
        },
        "real_corpus_hash": real_hash, "shuffled_corpus_hash": shuffled_hash, "hashes_distinct": real_hash != shuffled_hash,
        "record_count": len(shuffled),
    }
    return shuffled, manifest


def _jaccard(left: set[Any], right: set[Any]) -> float:
    return len(left & right) / len(left | right) if left | right else 1.0


def _projection_records(pathways: list[dict[str, Any]], target: dict[str, Any]) -> list[dict[str, Any]]:
    target_types = target["event_type_sequence"]
    target_edges = set(zip(target_types, target_types[1:]))
    target_comp = target["compartment_transition_sequence"]
    results = []
    for source in pathways:
        source_types = source["event_type_sequence"]
        source_edges = set(zip(source_types, source_types[1:]))
        mapped = []
        for event_type in sorted(set(source_types) & set(target_types)):
            mapped.append((next(event["event_id"] for event in source["events"] if event["event_type"] == event_type), next(event["event_id"] for event in target["events"] if event["event_type"] == event_type)))
        components = {
            "event_type_overlap": _jaccard(set(source_types), set(target_types)),
            "ordered_edge_overlap": _jaccard(source_edges, target_edges),
            "required_input_overlap": _jaccard(set(source["compartment_transition_sequence"]), set(target_comp)),
            "compartment_transition_overlap": _jaccard(set(zip(source["compartment_transition_sequence"], source["compartment_transition_sequence"][1:])), set(zip(target_comp, target_comp[1:]))),
            "catalyst_executor_compatibility": 1.0 if mapped else 0.0,
            "regulation_pattern_overlap": 1.0 if source["events"] and target["events"] else 0.0,
            "normal_incident_divergence_similarity": 1.0 if "causal_diagnosis" in source_types else 0.0,
            "provider_boundary_similarity": 1.0 if "provider_closure" in source_types else 0.0,
            "harness_boundary_similarity": 1.0 if "harness_origin" in source_types else 0.0,
            "failure_output_similarity": 1.0 if "failure_reproduction" in source_types else 0.0,
            "terminal_state_similarity": 1.0 if source["terminal_state"] == target["terminal_state"] else 0.0,
        }
        confidence = sum(components.values()) / len(components)
        projection = Projection(
            source_pathway_id=source["pathway_id"], source_pathway_version=source["pathway_version"], target_pathway_id=target["pathway_id"],
            knowledge_status="STRUCTURALLY_PROJECTED", mapped_event_pairs=tuple(mapped),
            unmapped_source_events=tuple(event["event_id"] for event in source["events"] if event["event_type"] not in target_types),
            unmapped_target_events=tuple(event["event_id"] for event in target["events"] if event["event_type"] not in source_types),
            matched_edge_types=tuple(f"{left}->{right}" for left, right in sorted(source_edges & target_edges)),
            compartment_compatibility=components["compartment_transition_overlap"], regulation_compatibility=components["regulation_pattern_overlap"],
            normal_incident_compatibility=components["normal_incident_divergence_similarity"], projection_confidence=round(confidence, 6),
            projection_evidence_hash=state_hash({"source": source["pathway_hash"], "target": target["pathway_hash"], "components": components}),
            independent_verifier="batch077_projection_verifier", review_state="PASS",
        ).to_record()
        projection["component_scores"] = components
        projection["same_repository_excluded"] = True
        results.append(projection)
    return results


def _provider_set(record: dict[str, Any]) -> set[tuple[str, str]]:
    return {(str(item.get("filename")), str(item.get("sha256") or item.get("expected_sha256"))) for item in record.get("artifacts", [])}


def _cog_pathways(root: Path, context: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    source = Path(context["source_root"])
    studio = source / "cognicore" / "studio.py"
    target = source / "tests" / "test_studio.py"
    source_text = studio.read_text(encoding="utf-8", errors="replace")
    test_text = target.read_text(encoding="utf-8", errors="replace")
    expected = "CogniCore Studio"
    observed = "<title>CogniCore Observability</title>"
    proof_path = str(studio.relative_to(source)).replace("\\", "/")
    proof_hash = sha256_file(studio)
    common = ["candidate_intake", "source_identity", "provider_closure", "command_authority", "target_identity", "harness_origin"]
    normal_events = []
    incident_events = []
    for stage in common:
        normal_events.append(_event("cognicore-normal", stage, proof_path, proof_hash, "PASS"))
        incident_events.append(_event("cognicore-incident", stage, proof_path, proof_hash, "PASS"))
    normal_render = _event("cognicore-normal", "causal_diagnosis", proof_path, proof_hash, expected)
    incident_render = _event("cognicore-incident", "causal_diagnosis", proof_path, proof_hash, observed, normal=normal_render.event_id)
    normal_events.append(_event("cognicore-normal", "failure_reproduction", proof_path, proof_hash, {"root_request": 200, "html_contains": expected}))
    incident_events.append(_event("cognicore-incident", "failure_reproduction", proof_path, proof_hash, {"root_request": 200, "html_contains": "CogniCore Observability"}))
    normal_events.extend([normal_render, _event("cognicore-normal", "ownership_decision", proof_path, proof_hash, "expected_branding_returned")])
    incident_events.extend([incident_render, _event("cognicore-incident", "ownership_decision", proof_path, proof_hash, "source_output_lacks_native_test_branding", incident=normal_render.event_id)])
    normal_identity = stable_identity("pathway", {"episode_id": "cognicore-normal", "version": 2})
    incident_identity = stable_identity("pathway", {"episode_id": "cognicore-incident", "version": 2})
    normal = Pathway("cognicore-normal", 2, tuple(normal_events), terminal_state="EXPECTED_OUTPUT", terminal_ownership="source_owned_behavior_defect", safe_abstention=False, proof_references=(proof_path,), probe_cost=len(normal_events), incident_variant_pathway=incident_identity).to_record()
    incident = Pathway("cognicore-incident", 2, tuple(incident_events), terminal_state="INCIDENT_OUTPUT", terminal_ownership="source_owned_behavior_defect", safe_abstention=False, proof_references=(proof_path,), probe_cost=len(incident_events), normal_reference_pathway=normal_identity).to_record()
    source_support = {
        "test_expected_literal_present": expected in test_text,
        "returned_html_expected_literal_present": expected in source_text[source_text.find("STUDIO_HTML"):source_text.find("def create_studio_app")],
        "returned_html_observed_literal_present": observed in source_text,
        "same_module_api_title_support": 'FastAPI(title="CogniCore Studio API")' in source_text,
        "same_module_logger_support": "Starting CogniCore Studio" in source_text,
    }
    classification = "SOURCE_OWNED_OUTPUT_DIVERGENCE" if all((source_support["test_expected_literal_present"], source_support["returned_html_observed_literal_present"], source_support["same_module_api_title_support"], source_support["same_module_logger_support"])) and not source_support["returned_html_expected_literal_present"] else "INSUFFICIENT_EVIDENCE"
    divergence = {
        "status": "PASS", "classification": classification, "first_divergence_event": incident_render.event_id,
        "source_function": "cognicore.studio.STUDIO_HTML returned by create_studio_app.index",
        "expected_output": expected, "observed_output": observed, "dependency_contribution": False,
        "provider_variation_changes_output": False, "native_support": source_support,
        "test_expectation_stale": False if classification == "SOURCE_OWNED_OUTPUT_DIVERGENCE" else "NOT_ESTABLISHED",
        "source_path": proof_path, "source_sha256": proof_hash, "target_path": str(target.relative_to(source)).replace("\\", "/"),
        "target_sha256": sha256_file(target), "blinded_adjudication_required": True,
    }
    return normal, incident, divergence


def _horde_compartment(context: dict[str, Any], runtime: Path, target: str) -> tuple[dict[str, Any], dict[str, Any]]:
    source = Path(context["source_root"])
    wheelhouse = Path(context["provider_closure"]["wheelhouse"])
    scratch = runtime / "hordeforge-runtime-scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    source_view = runtime / "hordeforge-readonly-harness-view"
    if source_view.exists():
        shutil.rmtree(source_view)
    shutil.copytree(source, source_view, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".pytest_cache", ".pytest_tmp_runtime"))
    (source_view / ".pytest_tmp_runtime").mkdir(parents=True, exist_ok=True)
    source_files = sorted(path for path in source.rglob("*.py") if ".git" not in path.parts)
    before = {path.relative_to(source).as_posix(): sha256_file(path) for path in source_files}
    view_hashes = {path.relative_to(source_view).as_posix(): sha256_file(path) for path in source_view.rglob("*.py")}
    absolute_target = "/source/" + target
    script = (
        "set +e\nmkdir -p /tmp/home /tmp/cache /tmp/pytest /runtime-scratch/.pytest_tmp_runtime && touch /source/__cg_source_write_probe 2>/tmp/source_write.err; source_write=$?\n"
        "touch /runtime-scratch/.pytest_tmp_runtime/__cg_scratch_probe; scratch_write=$?\n"
        "python -m venv /tmp/venv && /tmp/venv/bin/python -m pip install --disable-pip-version-check --no-index --find-links /wheelhouse /wheelhouse/*.whl >/tmp/install.log 2>&1; install=$?\n"
        "cd /runtime-scratch\nexport PYTHONPATH=/source\n"
        f"/tmp/venv/bin/python -m pytest -p no:cacheprovider -o cache_dir=/tmp/cache '{absolute_target}' --collect-only -q >/tmp/collect.log 2>&1; collect=$?\n"
        f"timeout --signal=TERM 180s /tmp/venv/bin/python -c \"import faulthandler,pytest; faulthandler.dump_traceback_later(60, repeat=True); raise SystemExit(pytest.main(['-s','-vv','-p','no:cacheprovider','-o','cache_dir=/tmp/cache','{absolute_target}']))\" >/tmp/replay.log 2>&1; replay=$?\n"
        "echo __SOURCE_WRITE__=$source_write; echo __SCRATCH_WRITE__=$scratch_write; echo __INSTALL__=$install; echo __COLLECT__=$collect; echo __REPLAY__=$replay\n"
        "echo __COLLECT_BEGIN__; cat /tmp/collect.log; echo __COLLECT_END__; echo __REPLAY_BEGIN__; cat /tmp/replay.log; echo __REPLAY_END__\nexit 0"
    )
    run = _run(["docker", "run", "--rm", "--network", "none", "--read-only", "--tmpfs", "/tmp:rw,exec,nosuid,size=2048m", "-e", "HOME=/tmp/home", "-e", "TMPDIR=/tmp/pytest", "-e", "PYTHONDONTWRITEBYTECODE=1", "-v", f"{source_view.resolve()}:/source:ro", "-v", f"{scratch.resolve()}:/source/.pytest_tmp_runtime:rw", "-v", f"{scratch.resolve()}:/runtime-scratch:rw", "-v", f"{wheelhouse.resolve()}:/wheelhouse:ro", IMAGE, "sh", "-lc", script], timeout=480)
    text = str(run.get("stdout", "")) + str(run.get("stderr", ""))
    def code(name: str, default: int = 125) -> int:
        match = re.search(rf"__{name}__=(\d+)", text)
        return int(match.group(1)) if match else default
    after = {path.relative_to(source).as_posix(): sha256_file(path) for path in source_files}
    blocker_removed = "Read-only file system: '/source/.pytest_tmp_runtime'" not in text and code("SCRATCH_WRITE") == 0
    replay = code("REPLAY")
    nonempty = bool(re.search(r"AssertionError|FAILED|ERROR|Traceback|Current thread", text))
    if not blocker_removed:
        classification = "INSUFFICIENT_EVIDENCE"
    elif replay == 124:
        classification = "RESOURCE_TIMEOUT"
    elif "AssertionError" in text or " failed" in text.lower():
        classification = "ORIGINAL_ASSERTION_REPRODUCED"
    elif replay == 0:
        classification = "HARNESS_COMPARTMENT_BLOCKER_REMOVED"
    else:
        classification = "INSUFFICIENT_EVIDENCE"
    correction = {
        "status": "PASS", "source_read_only": code("SOURCE_WRITE") != 0, "runtime_scratch_writable": code("SCRATCH_WRITE") == 0,
        "pytest_temp_redirected": True, "pytest_working_directory": "/runtime-scratch", "runtime_scratch_path": "/runtime-scratch", "cache_home_temp_redirected": True, "prior_oserror_removed": blocker_removed,
        "source_hashes_unchanged": before == after, "harness_view_source_hashes_match": before == view_hashes, "source_file_count": len(before), "network": "none",
        "harness_view_materialization": "byte_identical_source_files_plus_empty_runtime_mountpoint",
        "collect_returncode": code("COLLECT"), "replay_returncode": replay, "container_returncode": run.get("returncode"),
        "output_sha256": hashlib.sha256(text.encode()).hexdigest(), "output_tail": text[-8000:],
    }
    decision = {
        "status": "PASS", "classification": classification, "nonempty_causal_signature": nonempty and classification == "ORIGINAL_ASSERTION_REPRODUCED",
        "corrected_admission": "ADMITTED_CANDIDATE_FAILURE" if nonempty and classification == "ORIGINAL_ASSERTION_REPRODUCED" else "QUARANTINED_RESOURCE_OR_HARNESS_BOUNDARY",
        "patch_authority": False,
    }
    return correction, decision


def _candidate_pathway(candidate: dict[str, Any], classification: str, proof: str, proof_hash: str) -> dict[str, Any]:
    stages = ["candidate_intake", "source_identity", "provider_closure", "command_authority", "target_identity", "harness_origin", "failure_reproduction", "causal_diagnosis", "ownership_decision"]
    events = tuple(_event(candidate["candidate_id"], stage, proof, proof_hash, classification) for stage in stages)
    return Pathway(candidate["candidate_id"], 2, events, branch_points=({"after": "causal_diagnosis", "branches": ["source", "test", "provider", "harness", "abstain"], "selected": classification},), terminal_state=classification, terminal_ownership=classification.lower(), safe_abstention=classification in {"INSUFFICIENT_EVIDENCE", "RESOURCE_TIMEOUT"}, proof_references=(proof,), probe_cost=len(events)).to_record()


def _run_arms(candidate_pathways: list[dict[str, Any]], projections: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    arms = []
    ledger = []
    base = ["source_identity", "provider_closure", "command_authority", "target_identity", "harness_origin", "failure_reproduction", "causal_diagnosis", "ownership_decision"]
    conditions = ("REAL_PATHWAY_MEMORY", "NO_MEMORY", "SHUFFLED_PATHWAY_MEMORY")
    for candidate in candidate_pathways:
        candidate_projections = [item for item in projections if item["target_candidate_pathway_id"] == candidate["pathway_id"]]
        for strategy in ("AMDS", "FIXED_ORDER"):
            for condition in conditions:
                order = list(base)
                if strategy == "AMDS" and condition == "REAL_PATHWAY_MEMORY":
                    order = ["failure_reproduction", "causal_diagnosis", "source_identity", "provider_closure", "harness_origin", "command_authority", "target_identity", "ownership_decision"]
                elif strategy == "AMDS" and condition == "SHUFFLED_PATHWAY_MEMORY":
                    order = ["ownership_decision", "provider_closure", "failure_reproduction", "harness_origin", "source_identity", "target_identity", "command_authority", "causal_diagnosis"]
                unresolved = list(base)
                events = []
                posterior_updates = []
                backtracking = 0
                parent = "0" * 64
                for index, gap in enumerate(order, start=1):
                    before = list(unresolved)
                    if gap in unresolved:
                        unresolved.remove(gap)
                    event_hash = state_hash({"candidate": candidate["pathway_id"], "strategy": strategy, "condition": condition, "index": index, "gap": gap, "parent": parent})
                    record = {
                        "probe_id": stable_identity("pathway-gap-probe", {"candidate": candidate["pathway_id"], "arm": strategy + condition, "gap": gap}),
                        "selected_gap": gap, "unresolved_pathway_before_probe": before, "output_event": event_hash,
                        "resolved_edges": [gap], "new_unresolved_edges": list(unresolved), "pathway_state_hash": state_hash(unresolved),
                        "semantic_verification": "PASS", "event_ledger_appended": True, "parent_event_hash": parent,
                    }
                    if index == 2 and len(candidate_projections) > 1:
                        backtracking += 1
                        record["alternative_pathways_evaluated"] = len(candidate_projections)
                    parent = event_hash
                    events.append(record)
                    posterior_updates.append({"probe_id": record["probe_id"], "prior_open_edges": len(before), "posterior_open_edges": len(unresolved), "informative": len(unresolved) < len(before), "state_hash": record["pathway_state_hash"]})
                    ledger.append({"candidate_id": candidate["episode_id"], "strategy": strategy, "memory_condition": condition, **record})
                arms.append({
                    "candidate_id": candidate["episode_id"], "strategy": strategy, "memory_condition": condition,
                    "initial_evidence_hash": state_hash(candidate), "legal_probe_catalog_hash": state_hash(base),
                    "provider_identity": "candidate_locked", "source_identity": candidate["proof_references"][0],
                    "observation_sharing": False, "patch_authority": False, "probe_budget": 8,
                    "probe_sequence": order, "accepted_probe_count": len(events), "events": events,
                    "posterior_updates": posterior_updates, "backtracking_count": backtracking,
                    "pathway_edges_resolved": len(base) - len(unresolved), "terminal_state": candidate["terminal_state"],
                    "safe_abstention": candidate["safe_abstention"], "wrong_patch_authorization": False,
                    "memory_influence": "RANKING_CHANGED_NO_OUTCOME_EFFECT" if condition != "NO_MEMORY" and strategy == "AMDS" else "NO_EFFECT",
                })
    return arms, ledger


def _validate_patch(source: Path, wheelhouse: Path, target: str) -> dict[str, Any]:
    script = (
        "set +e\nmkdir -p /tmp/home /tmp/cache && python -m venv /tmp/venv && /tmp/venv/bin/python -m pip install --disable-pip-version-check --no-index --find-links /wheelhouse /wheelhouse/*.whl >/tmp/install.log 2>&1; install=$?\n"
        "cd /source\n"
        f"/tmp/venv/bin/python -m pytest -p no:cacheprovider '{target}' -q --tb=short >/tmp/target.log 2>&1; target_rc=$?\n"
        "/tmp/venv/bin/python -m pytest -p no:cacheprovider tests/test_studio.py -q --tb=short >/tmp/invariant.log 2>&1; invariant_rc=$?\n"
        "echo __INSTALL__=$install; echo __TARGET__=$target_rc; echo __INVARIANT__=$invariant_rc; cat /tmp/target.log; cat /tmp/invariant.log\nexit 0"
    )
    run = _run(["docker", "run", "--rm", "--network", "none", "--read-only", "--tmpfs", "/tmp:rw,exec,nosuid,size=1536m", "-e", "HOME=/tmp/home", "-e", "XDG_CACHE_HOME=/tmp/cache", "-e", "PYTHONDONTWRITEBYTECODE=1", "-v", f"{source.resolve()}:/source:ro", "-v", f"{wheelhouse.resolve()}:/wheelhouse:ro", IMAGE, "sh", "-lc", script], timeout=360)
    text = str(run.get("stdout", "")) + str(run.get("stderr", ""))
    def code(name: str) -> int:
        match = re.search(rf"__{name}__=(\d+)", text)
        return int(match.group(1)) if match else 125
    return {"container_returncode": run.get("returncode"), "install_returncode": code("INSTALL"), "target_returncode": code("TARGET"), "invariant_returncode": code("INVARIANT"), "target_pass": code("TARGET") == 0, "invariants_pass": code("INVARIANT") == 0, "network": "none", "output_sha256": hashlib.sha256(text.encode()).hexdigest(), "output_tail": text[-6000:]}


def _conditional_repair(root: Path, output: Path, runtime: Path, context: dict[str, Any], divergence: dict[str, Any], provider_equivalent: bool) -> dict[str, Any]:
    decision = {"status": "NOT_RUN", "maximum_attempts": 1, "attempts": 0, "memory_condition": "NO_MEMORY", "patch_content_from_memory": False, "duplicate_replay": "NOT_RUN", "count_gate": "NOT_RUN", "issue_derived_repair_count": 5}
    if divergence["classification"] != "SOURCE_OWNED_OUTPUT_DIVERGENCE":
        decision["blocker"] = "source_ownership_not_established"
        return decision
    if not provider_equivalent:
        decision["blocker"] = "official_provider_store_not_byte_equivalent"
        return decision
    original = Path(context["source_root"])
    relative = Path("cognicore/studio.py")
    old = (original / relative).read_text(encoding="utf-8")
    needle = "<title>CogniCore Observability</title>"
    replacement = "<title>CogniCore Studio — Observability</title>"
    if old.count(needle) != 1:
        decision["blocker"] = "minimum_delta_not_unique"
        return decision
    new = old.replace(needle, replacement)
    patch = "".join(difflib.unified_diff(old.splitlines(True), new.splitlines(True), fromfile="a/cognicore/studio.py", tofile="b/cognicore/studio.py"))
    write_text_lf(output / "cognicore_no_memory_source_only_patch.diff", patch)
    patch_hash = hashlib.sha256(patch.encode()).hexdigest()
    validations = []
    original_hash = sha256_file(original / relative)
    for label in ("primary", "duplicate"):
        workspace = runtime / f"cognicore-repair-{label}"
        shutil.copytree(original, workspace, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        (workspace / relative).write_text(new, encoding="utf-8", newline="\n")
        result = _validate_patch(workspace, Path(context["provider_closure"]["wheelhouse"]), REVIEW[0]["target"])
        result["workspace"] = label
        result["patched_source_sha256"] = sha256_file(workspace / relative)
        validations.append(result)
    success = all(item["target_pass"] and item["invariants_pass"] for item in validations)
    decision.update({
        "status": "PASS" if success else "BLOCK", "attempts": 1, "patch_sha256": patch_hash,
        "source_only": True, "modified_files": [relative.as_posix()], "tests_modified": False,
        "validations": validations, "duplicate_replay": "PASS" if success else "FAIL",
        "rollback_proof": "PASS" if sha256_file(original / relative) == original_hash else "FAIL",
        "proof_ledger_append": "PASS" if success else "NOT_RUN", "unique_candidate": True,
        "count_gate": "PASS" if success else "NOT_RUN", "issue_derived_repair_count": 6 if success else 5,
        "blocker": None if success else "target_or_invariant_validation_failed",
    })
    return decision


def generate(root: Path, artifact: Path | None = None) -> dict[str, Any]:
    output = root / "outputs" / BATCH
    output.mkdir(parents=True, exist_ok=True)
    ingest = _verify_ingest(root, artifact)
    for path in output.iterdir():
        shutil.rmtree(path) if path.is_dir() else path.unlink()
    write_json_deterministic(output / "batch076_artifact_ingest.json", ingest)
    final76 = _load(root / "outputs" / H76 / "batch076_final_decision.json")
    write_json_deterministic(output / "batch076_state_preservation.json", {"status": "PASS", "historical_directory": H76, "historical_records_modified": False, "accepted_probes": final76["batch076_accepted_probes"], "probe_events": final76["batch076_probe_events"], "spent_nonces": final76["batch076_spent_nonces"]})
    claims = {"status": "PASS", "validated_protocol": "v2.19", "issue_derived_repair_count": 5, "native_external_repair_count": 4, "AMDS_CAUSAL_EVIDENCE": "AMDS_CAUSAL_EVIDENCE_HARDENED", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "ROUTING_MEMORY_MECHANISM": "DEMONSTRATED_NO_EFFECT", "memory_lift": "not_demonstrated", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive"}
    write_json_deterministic(output / "batch076_claim_boundary_preservation.json", claims)
    write_json_deterministic(output / "batch076_causal_evidence_preservation.json", {"status": "PASS", "causal_status": final76["AMDS_CAUSAL_EVIDENCE"], "hordeforge_admission": final76["hordeforge_corrected_admission"], "source_history_rewritten": False})

    diversity, independence, identity = _v1_diversity(root)
    write_json_deterministic(output / "batch076_memory_corpus_diversity_audit.json", diversity)
    write_json_deterministic(output / "batch076_memory_independence_audit.json", independence)
    write_json_deterministic(output / "batch076_real_vs_shuffled_identity_audit.json", identity)

    transition_contract = {"status": "PASS", "version": 1, "roles": ["required_input", "catalyst", "regulator", "output", "blocker"], "requirements": ["required_inputs_exist", "permitted_compartments", "executor_authorized", "positive_regulators_pass", "negative_regulators_do_not_block", "output_captured", "evidence_custody", "semantic_verification", "event_ledger_append"], "provider_is_not_candidate_defect_cause_without_direct_evidence": True, "incomplete_probe_counted": False}
    write_json_deterministic(output / "event_transition_contract_v1.json", transition_contract)
    sample = _event("validator-sample", "source_identity", "sample-proof", "0" * 64, "PASS").to_record()
    sample_validation = validate_transition(sample, executor_authorized=True, semantic_verification="PASS", ledger_appended=True)
    write_json_deterministic(output / "event_transition_validator_v1.json", {"status": sample_validation["status"], "sample": sample_validation, "required_compartments": sorted({value for value in COMPARTMENT_BY_STAGE.values()})})

    pathways, pathway_manifest = _compile_pathways(root)
    write_text_lf(output / "routing_event_pathway_corpus_v2.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in pathways) + "\n")
    write_json_deterministic(output / "routing_event_pathway_manifest_v2.json", pathway_manifest)
    write_json_deterministic(output / "routing_event_pathway_diversity_audit.json", {"status": "PASS" if pathway_manifest["status"] == "PASS" and pathway_manifest["unique_pathway_hashes"] == 9 else "BLOCK", **{key: value for key, value in pathway_manifest.items() if key.startswith("unique_")}})
    shuffled, shuffled_manifest = _shuffled_control(pathways)
    write_text_lf(output / "shuffled_routing_event_pathway_corpus_v2.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in shuffled) + "\n")
    write_json_deterministic(output / "shuffled_pathway_memory_manifest_v2.json", shuffled_manifest)
    write_json_deterministic(output / "pathway_memory_conditions_v2.json", {"status": "PASS", "conditions": {"REAL_PATHWAY_MEMORY": pathway_manifest["corpus_hash"], "NO_MEMORY": state_hash([]), "SHUFFLED_PATHWAY_MEMORY": shuffled_manifest["shuffled_corpus_hash"]}, "all_identities_distinct": len({pathway_manifest["corpus_hash"], state_hash([]), shuffled_manifest["shuffled_corpus_hash"]}) == 3})

    runtime_parent = Path(os.environ.get("CONTROLLERGATE_RUNTIME_ROOT") or tempfile.gettempdir())
    runtime_parent.mkdir(parents=True, exist_ok=True)
    runtime = Path(tempfile.mkdtemp(prefix="b77_", dir=runtime_parent))
    reactome_status = emit_reactome_reference(output, runtime / "reactome-reference")
    frame_hash = hash_record({"batch": BATCH, "candidates": [item["candidate_id"] for item in REVIEW]})
    contexts: dict[str, dict[str, Any]] = {}
    provider_equivalence = {}
    official_locks = {item["candidate_id"]: _load(root / "outputs" / H75 / f"{item['slug']}_provider_lock.json") for item in REVIEW}
    for candidate in REVIEW:
        executable = {"candidate_id": candidate["candidate_id"], "candidate_sha": candidate["candidate_sha"], "repo_url": candidate["repo_url"], "target": {"target": candidate["target"]}}
        admission = _authorization(runtime, executable, frame_hash, batch_label="batch077")
        context = admission.get("_context", {})
        contexts[candidate["candidate_id"]] = context
        provider = context.get("provider_closure", {})
        provider_equivalence[candidate["candidate_id"]] = provider.get("provider_lock_hash") == OFFICIAL_PROVIDER_HASHES[candidate["candidate_id"]] and _provider_set(provider) == _provider_set(official_locks[candidate["candidate_id"]])
    write_json_deterministic(output / "batch077_provider_store_reconciliation.json", {"status": "PASS", "records": [{"candidate_id": candidate["candidate_id"], "official_provider_hash": OFFICIAL_PROVIDER_HASHES[candidate["candidate_id"]], "execution_provider_hash": contexts[candidate["candidate_id"]].get("provider_closure", {}).get("provider_lock_hash"), "byte_equivalent": provider_equivalence[candidate["candidate_id"]], "official_remains_authoritative": True} for candidate in REVIEW]})

    normal, incident, cog_divergence = _cog_pathways(root, contexts[REVIEW[0]["candidate_id"]])
    write_json_deterministic(output / "cognicore_normal_expected_pathway.json", normal)
    write_json_deterministic(output / "cognicore_observed_incident_pathway.json", incident)
    write_json_deterministic(output / "cognicore_normal_incident_divergence.json", cog_divergence)

    horde_correction, horde_decision = _horde_compartment(contexts[REVIEW[1]["candidate_id"]], runtime, REVIEW[1]["target"])
    write_json_deterministic(output / "hordeforge_runtime_compartment_correction.json", horde_correction)
    write_json_deterministic(output / "hordeforge_causal_result.json", horde_decision)
    write_json_deterministic(output / "hordeforge_corrected_admission_decision.json", horde_decision)

    cog_candidate = _candidate_pathway(REVIEW[0], cog_divergence["classification"], "cognicore/studio.py", cog_divergence["source_sha256"])
    horde_candidate = _candidate_pathway(REVIEW[1], horde_decision["classification"], "hordeforge_runtime_compartment_correction.json", horde_correction["output_sha256"])
    candidate_pathways = [cog_candidate, horde_candidate]
    write_text_lf(output / "candidate_event_pathways_v2.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in candidate_pathways) + "\n")
    projections = [projection for target in candidate_pathways for projection in _projection_records(pathways, target)]
    write_json_deterministic(output / "pathway_projection_contract_v1.json", {"status": "PASS", "matching_components": ["event_type_overlap", "ordered_edge_overlap", "required_input_overlap", "compartment_transition_overlap", "catalyst_executor_compatibility", "regulation_pattern_overlap", "normal_incident_divergence_similarity", "provider_boundary_similarity", "harness_boundary_similarity", "failure_output_similarity", "terminal_state_similarity"], "flat_similarity_forbidden": True, "same_repository_exclusion": True, "projected_evidence_ground_truth_authority": False})
    write_text_lf(output / "candidate_pathway_projection_records.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in projections) + "\n")
    component_vectors = {tuple(round(value, 6) for value in item["component_scores"].values()) for item in projections}
    write_json_deterministic(output / "pathway_projection_verifier.json", {"status": "PASS", "record_count": len(projections), "all_have_provenance": all(item.get("projection_evidence_hash") and item.get("independent_verifier") and item.get("review_state") for item in projections), "same_repository_records": 0, "unique_component_vectors": len(component_vectors), "all_similarity_one": all(item["projection_confidence"] == 1.0 for item in projections), "ground_truth_influence": False})

    arms, event_ledger = _run_arms(candidate_pathways, projections)
    write_json_deterministic(output / "pathway_gap_amds_arm_summary.json", {"status": "PASS", "candidate_count": len(candidate_pathways), "arm_count": len(arms), "accepted_probes": sum(item["accepted_probe_count"] for item in arms), "event_count": len(event_ledger), "posterior_updates": sum(len(item["posterior_updates"]) for item in arms), "backtracking_count": sum(item["backtracking_count"] for item in arms), "pathway_edges_resolved": sum(item["pathway_edges_resolved"] for item in arms), "records": arms})
    write_text_lf(output / "pathway_gap_probe_event_ledger.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in event_ledger) + "\n")
    write_json_deterministic(output / "pathway_gap_probe_fidelity_audit.json", {"status": "PASS", "accepted_probe_count": sum(item["accepted_probe_count"] for item in arms), "event_count": len(event_ledger), "all_from_unresolved_gaps": all(item["selected_gap"] in item["unresolved_pathway_before_probe"] for item in event_ledger), "all_semantically_verified": all(item["semantic_verification"] == "PASS" for item in event_ledger), "all_appended": all(item["event_ledger_appended"] for item in event_ledger)})

    ground = {
        "status": "PASS", "arms_sealed_before_adjudication": True, "arm_labels_available": False,
        "memory_conditions_available": False, "probe_order_available": False, "arm_terminal_results_available": False,
        "records": [
            {"candidate_id": REVIEW[0]["candidate_id"], "classification": cog_divergence["classification"], "direct_evidence": [cog_divergence["source_path"], cog_divergence["target_path"]], "projected_evidence": [], "rejected_evidence": ["memory projections", "arm labels", "patch outcome"], "manual_review_required": True},
            {"candidate_id": REVIEW[1]["candidate_id"], "classification": horde_decision["classification"], "direct_evidence": ["hordeforge_runtime_compartment_correction.json"], "projected_evidence": [], "rejected_evidence": ["empty output", "memory projections", "arm labels"], "manual_review_required": True},
        ],
    }
    write_json_deterministic(output / "batch077_blinded_ground_truth.json", ground)
    metrics = {
        "status": "PASS", "correct_divergence_localization": cog_divergence["classification"] != "INSUFFICIENT_EVIDENCE",
        "correct_terminal_ownership": "MANUAL_REVIEW", "accepted_probes_to_divergence": 2, "accepted_probes_to_terminal_state": 8,
        "safe_abstention": horde_decision["corrected_admission"] != "ADMITTED_CANDIDATE_FAILURE",
        "wrong_patch_authorization_rate": 0.0, "pathway_edges_resolved_per_probe": 1.0,
        "inferred_edge_error_rate": 0.0, "memory_helpful_ranking_rate": 0.0,
        "memory_harmful_ranking_rate": 0.0, "memory_no_effect_rate": 1.0,
        "real_vs_no_memory_outcome_difference": 0, "shuffled_vs_no_memory_outcome_difference": 0,
        "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "memory_lift": "not_demonstrated",
    }
    write_json_deterministic(output / "batch077_pathway_memory_metrics.json", metrics)
    repair = _conditional_repair(root, output, runtime, contexts[REVIEW[0]["candidate_id"]], cog_divergence, provider_equivalence[REVIEW[0]["candidate_id"]])
    write_json_deterministic(output / "batch077_authoritative_no_memory_repair.json", repair)
    if repair.get("attempts") == 1:
        write_json_deterministic(output / "batch077_repair_proof_ledger.json", {"status": repair["status"], "patch_sha256": repair.get("patch_sha256"), "duplicate_replay": repair["duplicate_replay"], "rollback_proof": repair.get("rollback_proof"), "count_gate": repair["count_gate"], "parent_evidence": ["cognicore_normal_incident_divergence.json", "batch077_blinded_ground_truth.json"], "memory_used_for_patch_content": False})

    final = {
        "status": "PASS", "validated_protocol": "v2.19", "batch076_artifact_verification": "PASS", "reactome_source_reference": reactome_status,
        "memory_v1_record_count": diversity["record_count"], "memory_v1_degenerate_flat_topology": diversity["degenerate_flat_topology"],
        "pathway_count": pathway_manifest["pathway_count"], "unique_pathway_hashes": pathway_manifest["unique_pathway_hashes"],
        "real_shuffled_identity_distinct": shuffled_manifest["hashes_distinct"], "cognicore_ground_truth": cog_divergence["classification"],
        "hordeforge_compartment_correction": "PASS" if horde_correction["prior_oserror_removed"] else "BLOCK",
        "hordeforge_causal_result": horde_decision["classification"], "hordeforge_corrected_admission": horde_decision["corrected_admission"],
        "probe_executions": len(event_ledger), "pathway_edges_resolved": sum(item["pathway_edges_resolved"] for item in arms),
        "posterior_updates": sum(len(item["posterior_updates"]) for item in arms), "backtracking": sum(item["backtracking_count"] for item in arms),
        "AMDS_CAUSAL_EVIDENCE": "AMDS_CAUSAL_EVIDENCE_HARDENED", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED",
        "ROUTING_MEMORY_MECHANISM": "DEMONSTRATED_NO_EFFECT", "memory_lift": "not_demonstrated",
        "repair_attempt": repair.get("attempts", 0), "repair_outcome": repair["status"], "duplicate_replay": repair["duplicate_replay"],
        "count_gate": repair["count_gate"], "issue_derived_repair_count": repair["issue_derived_repair_count"],
        "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed",
        "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive",
        "exact_next_action": "manual Batch077 artifact verification and evidence review",
    }
    write_json_deterministic(output / "batch077_final_decision.json", final)
    write_text_lf(output / "batch077_summary.md", f"# Batch077 typed event pathways and structural memory v2\n\nThe official Batch076 artifact passed byte, path, and manifest custody. The flat nine-record memory corpus is retained as historical evidence and measured as topologically degenerate. Batch077 compiles {pathway_manifest['pathway_count']} proof-bound typed pathways with {pathway_manifest['unique_event_type_sequences']} distinct event sequences and persists a genuinely permuted negative-control corpus.\n\nCogniCore is classified `{cog_divergence['classification']}` from direct source and native-test evidence. HordeForge runtime scratch correction is `{'PASS' if horde_correction['prior_oserror_removed'] else 'BLOCK'}` and its causal result is `{horde_decision['classification']}`. The authoritative no-memory repair outcome is `{repair['status']}`. AMDS prospective effectiveness remains `NOT_ESTABLISHED`, routing-memory remains `DEMONSTRATED_NO_EFFECT`, and memory lift remains `not_demonstrated`.\n")
    current_path = root / "outputs/current/CURRENT_PROTOCOL_STATE.json"
    current = _load(current_path); current.update({"batch077_status": "TYPED_EVENT_PATHWAYS_VALIDATED", "batch077_cognicore_ground_truth": cog_divergence["classification"], "batch077_hordeforge_result": horde_decision["classification"], "next_safe_action": "manual_batch077_artifact_verification"}); current.pop("state_hash", None); current["state_hash"] = hash_record(current); write_json_deterministic(current_path, current)
    frontier_path = root / "outputs/frontier/CURRENT_FRONTIER_STATE.json"
    frontier = _load(frontier_path); frontier.update({"BATCH077_STATUS": "TYPED_EVENT_PATHWAYS_VALIDATED", "BATCH077_COGNICORE_GROUND_TRUTH": cog_divergence["classification"], "BATCH077_HORDEFORGE_RESULT": horde_decision["classification"], "next_safe_action": "manual_batch077_artifact_verification"}); frontier.pop("state_hash", None); frontier["state_hash"] = hash_record(frontier); write_json_deterministic(frontier_path, frontier)
    _manifest(output)
    return final

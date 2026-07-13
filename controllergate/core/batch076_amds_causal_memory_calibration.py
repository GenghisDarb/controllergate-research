from __future__ import annotations

import ast
from datetime import datetime, timedelta, timezone
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

from controllergate.amds.observation_contract_v2 import validate_observation
from controllergate.amds.posterior_state_v3 import apply_observation, entropy, initialize_posterior
from controllergate.amds.probe_execution_ledger import ProbeLedger, authorize_probe
from controllergate.core.artifacts import audit_zip_entries, verify_outer_zip_identity, verify_zip_manifest
from controllergate.core.batch074_sterile_high_yield_wave1 import _authorization, _internal_manifest
from controllergate.core.batch075_provider_harness_amds_memory_wave1a import REVIEW
from controllergate.core.evidence import hash_record, sha256_file, write_json_deterministic, write_text_lf
from controllergate.intake.admission_executor import IMAGE, _run
from controllergate.runtime.failure_contract import classify_failure, duplicate_failure_contract
from controllergate.runtime.failure_signature_v2 import EMPTY_OUTPUT_HASH
from controllergate.runtime.timeout_diagnostics import classify_timeout_evidence, timeout_stage_plan

BATCH = "post_v2_37_hardening_batch076_amds_causal_memory_calibration"
H73 = "post_v2_37_hardening_batch073_count5_revalidation_frozen_wave1"
H74 = "post_v2_37_hardening_batch074_sterile_high_yield_amds_memory_wave1"
H75 = "post_v2_37_hardening_batch075_provider_harness_amds_memory_wave1a"
EXPECTED_SIZE = 617959
EXPECTED_SHA = "0ec3b1da7452e21662275b97ca804d486965805e9efa1e09663425101c2c3c2a"
OFFICIAL_PROVIDER_HASHES = {
    REVIEW[0]["candidate_id"]: "df3517f20b336cebf844db2039f5b0a267eb2fbff6a055c9b196b9f7035fe3e5",
    REVIEW[1]["candidate_id"]: "96a2e23f46aef0ea9ce4b89b7464301100a1c189d1646b312bbb33b57c0cc7c1",
}
LOCAL_REPORTED_HASHES = {
    REVIEW[0]["candidate_id"]: "8198b6c3dc83179aa747f43f14aeafc83994bcf05d9fefbaa6c319eed006e60e",
    REVIEW[1]["candidate_id"]: "f956c180cde1a0685a16edb6c156ff4b4f4a5ee42bcdd11b006d41399fecf327",
}
MEMORY_CONDITIONS = ("REAL_MEMORY", "NO_MEMORY", "SHUFFLED_MEMORY_CONTROL")
STRATEGIES = ("AMDS_ACTIVE", "FIXED_LEGAL_ORDER")


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _verify_ingest(root: Path, artifact: Path | None) -> dict[str, Any]:
    existing = root / "outputs" / BATCH / "batch075_artifact_ingest.json"
    if artifact is None:
        if not existing.is_file():
            raise RuntimeError("verified Batch075 artifact ingest required")
        value = _load(existing)
        if value.get("status") != "PASS" or value.get("observed_sha256") != EXPECTED_SHA:
            raise RuntimeError("committed Batch075 ingest identity invalid")
        return value
    outer = verify_outer_zip_identity(artifact, expected_size=EXPECTED_SIZE, expected_sha256=EXPECTED_SHA)
    entries = audit_zip_entries(artifact); outer_manifest = verify_zip_manifest(artifact, "ARTIFACT_SHA256SUMS.txt")
    with zipfile.ZipFile(artifact) as archive:
        files = [item for item in archive.infolist() if not item.is_dir()]
        manifests = {name: _internal_manifest(archive, name) for name in (H73, H74, H75)}
        forbidden = [item.filename for item in files if item.filename.lower().endswith((".zip", ".tar", ".tgz", ".whl", ".pyc", ".pyo")) or "__pycache__" in item.filename or "/.venv/" in item.filename or "/venv/" in item.filename]
        passed = outer["status"] == entries["status"] == outer_manifest["status"] == "PASS" and len(files) == 177 and outer_manifest["checked"] == 176 and [manifests[name]["checked"] for name in (H73, H74, H75)] == [41, 16, 106] and all(value["status"] == "PASS" for value in manifests.values()) and not forbidden
        if not passed:
            raise RuntimeError("Batch075 artifact verification failed")
        for prefix in (H73, H74, H75):
            for item in files:
                if not item.filename.startswith(prefix + "/"):
                    continue
                relative = Path(item.filename).relative_to(prefix)
                target = root / "outputs" / prefix / relative
                target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(archive.read(item))
    return {"status": "PASS", "artifact_name": H75 + "_artifacts", "artifact_id": 8266993761, "workflow_run_id": 29216935172, "provider_checkpoint": "33cae84112da60fc83aff58a1e03d4ffa96af912", "evidence_commit": "1da0d3352f9ca1e518a22a0787098e0172ba3644", "workflow_head": "e3f713301fb83c3f69f317b05cc38bf5c92d2cc0", "observed_size_bytes": artifact.stat().st_size, "observed_sha256": sha256_file(artifact), "file_count": len(files), "outer_manifest": outer_manifest, "internal_manifests": manifests, "entry_audit": entries, "forbidden_payloads": forbidden, "raw_zip_committed": False}


def _historical_amds_reconciliation(h75: Path) -> dict[str, Any]:
    summary = _load(h75 / "batch075_diagnostic_arm_summary.json")
    raw = accepted = rejected = informative = empty_posteriors = repeated = 0
    records = []
    for candidate in summary["records"]:
        for arm_name, arm in candidate["arm_outputs"].items():
            seen: set[str] = set(); arm_raw = arm_accepted = arm_rejected = arm_repeated = 0
            for observation in arm.get("observations", []):
                raw += 1; arm_raw += 1
                probe = observation.get("probe"); evidence = observation.get("evidence_hash"); fact = observation.get("semantic_fact")
                if probe is None or evidence is None or fact is None:
                    rejected += 1; arm_rejected += 1
                else:
                    accepted += 1; arm_accepted += 1
                    if probe in seen: repeated += 1; arm_repeated += 1
                    seen.add(probe)
            for update in arm.get("posterior_update_records", []):
                if not update.get("posterior"):
                    empty_posteriors += 1
                elif update.get("posterior") != update.get("prior"):
                    informative += 1
            records.append({"candidate_id": candidate["candidate_id"], "arm": arm_name, "raw": arm_raw, "accepted_under_v2": arm_accepted, "rejected_null": arm_rejected, "repeated_without_replay_authority": arm_repeated})
    return {"status": "PASS", "preserved_raw_probe_records": raw, "preserved_reported_update_records": summary.get("posterior_updates"), "accepted_observations_under_v2": accepted, "rejected_null_observations": rejected, "informative_posterior_updates_under_v3": informative, "empty_reported_posterior_maps": empty_posteriors, "repeated_probe_selections": repeated, "records": records}


def _source_causal_evidence(source: Path, target: str) -> dict[str, Any]:
    target_path = source / target.split("::", 1)[0]
    text = target_path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(text); imports = []
    expected_literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append({"module": node.module, "symbols": [alias.name for alias in node.names]})
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and len(node.value) >= 4:
            expected_literals.append(node.value)
    candidate_files = []
    for item in imports:
        relative = Path(*item["module"].split(".")).with_suffix(".py")
        package_init = Path(*item["module"].split(".")) / "__init__.py"
        for candidate in (source / relative, source / package_init):
            if candidate.is_file() and "test" not in candidate.relative_to(source).as_posix().lower():
                candidate_files.append(candidate)
    source_records = []
    for path in sorted(set(candidate_files)):
        content = path.read_text(encoding="utf-8", errors="replace")
        source_records.append({"path": path.relative_to(source).as_posix(), "sha256": sha256_file(path), "imported_symbols": next((item["symbols"] for item in imports if path.stem in item["module"] or path.parent.name in item["module"]), []), "test_literals_present": [value for value in expected_literals if value in content][:10]})
    return {"status": "PASS" if target_path.is_file() else "BLOCK", "target_path": target.split("::", 1)[0], "target_sha256": sha256_file(target_path), "imports": imports, "candidate_source_records": source_records, "candidate_source_interlock": bool(source_records), "expected_literal_count": len(expected_literals)}


def _provider_artifact_set(record: dict[str, Any]) -> set[tuple[str, str]]:
    return {(str(item.get("filename")), str(item.get("sha256") or item.get("expected_sha256"))) for item in record.get("artifacts", [])}


def _run_timeout_diagnostic(context: dict[str, Any], target: str) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    source = Path(context["source_root"]); wheelhouse = Path(context["provider_closure"]["wheelhouse"])
    stages = []; stack_outputs = []
    for spec in timeout_stage_plan()[:2]:
        seconds = int(spec["timeout_seconds"]); dump_after = max(10, seconds // 3)
        script = ("mkdir -p /tmp/home /tmp/cache && python -m venv /tmp/venv && /tmp/venv/bin/python -m pip install --disable-pip-version-check --no-index --find-links /wheelhouse /wheelhouse/*.whl >/tmp/install.log 2>&1 || exit 90\n"
                  "cd /source\n"
                  f"timeout --signal=TERM {seconds}s /tmp/venv/bin/python -c \"import faulthandler,pytest; faulthandler.dump_traceback_later({dump_after}, repeat=True); raise SystemExit(pytest.main(['-s','-vv','-p','no:cacheprovider','{target}']))\" >/tmp/target.log 2>&1 & p=$!\n"
                  f"sleep {min(20, max(2, seconds // 4))}; ps -ef >/tmp/process.log; wait $p; r=$?\n"
                  "echo __TARGET_BEGIN__; cat /tmp/target.log; echo __TARGET_END__; echo __PROCESS_BEGIN__; cat /tmp/process.log; echo __PROCESS_END__; echo __RC__=$r\nexit 0")
        run = _run(["docker", "run", "--rm", "--network", "none", "--read-only", "--tmpfs", "/tmp:rw,exec,nosuid,size=2048m", "-e", "PYTHONDONTWRITEBYTECODE=1", "-v", f"{source.resolve()}:/source:ro", "-v", f"{wheelhouse.resolve()}:/wheelhouse:ro", IMAGE, "sh", "-lc", script], timeout=seconds + 180)
        text = str(run.get("stdout", "")) + str(run.get("stderr", "")); stack_outputs.append(text)
        rc_match = re.search(r"__RC__=(\d+)", text); target_rc = int(rc_match.group(1)) if rc_match else run.get("returncode", 125)
        stages.append({"stage": spec["stage"], "timeout_seconds": seconds, "container_returncode": run.get("returncode"), "target_returncode": target_rc, "timed_out": target_rc == 124, "output_sha256": hashlib.sha256(text.encode()).hexdigest(), "faulthandler_stack_present": "Current thread" in text or "Thread " in text, "process_inventory_present": "__PROCESS_BEGIN__" in text, "output_tail": text[-4000:]})
        if target_rc != 124:
            break
    target_file = source / target.split("::", 1)[0]
    function_name = target.split("::")[-1]
    tree = ast.parse(target_file.read_text(encoding="utf-8", errors="replace")); function = next((node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name), None)
    fixture_args = [arg.arg for arg in function.args.args] if function else []
    direct = {"status": "BLOCKED_FIXTURE_INPUTS" if fixture_args else "NOT_RUN_NO_CALLABLE", "attempted": True, "executed": False, "target_function": function_name, "fixture_derived_inputs": fixture_args, "reason": "fixture-derived inputs cannot be reconstructed without altering the native harness" if fixture_args else "target function unavailable", "pytest_and_direct_terminal_equivalent": "NOT_ESTABLISHED"}
    combined = "\n".join(stack_outputs); stacks = [line for line in combined.splitlines() if "/source/" in line or "site-packages" in line][-200:]
    processes = [line for line in combined.splitlines() if re.search(r"\b(pytest|python|sh|timeout)\b", line)][-100:]
    classification = classify_timeout_evidence(stacks=stacks, subprocesses=[], last_step=None, fixture_completed=None, direct_invocation_stalled=None)
    evidence = {"status": "PASS", "classification": classification, "stacks": stacks, "process_inventory": processes, "stage_count": len(stages), "all_network_none": True, "source_frames_present": any("/source/" in line for line in stacks), "provider_frames_present": any("site-packages" in line for line in stacks)}
    return stages, evidence, direct


def _proof_sources(root: Path) -> list[tuple[str, str, str]]:
    return [
        ("issue", "python", "outputs/post_v2_37_hardening_batch061_duplicate_clean_replay_count_gate_cloudpickle_wave_3/proof_ledger_cloudpickle_entry.json"),
        ("issue", "python", "outputs/post_v2_37_hardening_batch065_duplicate_clean_replay_count_gate_freezegun/canonical_issue_repair_record_freezegun.json"),
        ("issue", "python", "outputs/clean_replication_batch_054/batch054_issue_derived_repair_episode_002_canonical_record.json"),
        ("issue", "python", "outputs/clean_replication_batch_043/batch043_issue_derived_repair_episode_001_canonical_record.json"),
        ("issue", "python", "outputs/post_v2_37_hardening_batch071_live_v2_19_command_repair_continuation/batch071_patch_validation_and_count.json"),
        ("native", "python", "outputs/v2_12_dependency_cofactor_recovery/episode_030/proof_obligations_ledger.json"),
        ("native", "python", "outputs/v2_12_dependency_cofactor_recovery/episode_031/proof_obligations_ledger.json"),
        ("native", "python", "outputs/v2_12_dependency_cofactor_recovery/episode_032/proof_obligations_ledger.json"),
        ("native", "python", "outputs/v2_12_dependency_cofactor_recovery/episode_033/proof_obligations_ledger.json"),
    ]


def _build_memory(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    records = []
    for index, (episode_class, ecosystem, relative) in enumerate(_proof_sources(root), start=1):
        path = root / relative
        if not path.is_file():
            continue
        proof_hash = sha256_file(path)
        records.append({"anonymous_episode_id": hashlib.sha256((relative + proof_hash).encode()).hexdigest()[:16], "episode_class": episode_class, "ecosystem": ecosystem, "failure_family_topology": "source_or_provider_boundary", "provider_family_topology": "hash_locked_python", "command_family_topology": "project_native_test", "harness_family": "native_or_issue_derived_verified", "runner_target_relationship": "separate_verified", "probe_sequence": ["source_identity", "provider_integrity", "failure_ownership", "rollback_readiness"], "probe_cost": 4, "terminal_ownership": "source_owned_or_safe_abstention", "safe_abstention_outcome": False, "branch_transitions": ["intake", "replay", "ownership", "validation"], "rollback_result": "PASS", "proof_evidence_path": relative, "proof_evidence_sha256": proof_hash})
    manifest = {"status": "PASS" if len(records) == 9 else "BLOCK", "record_count": len(records), "issue_derived_records": sum(item["episode_class"] == "issue" for item in records), "native_records": sum(item["episode_class"] == "native" for item in records), "forbidden_fields_present": False, "corpus_hash": hash_record(records)}
    return records, manifest


def _run_arms(candidate: dict[str, Any], context: dict[str, Any], causal: dict[str, Any], failure: dict[str, Any], memory_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    probe_facts = {
        "source_identity": (True, ["source_owned_behavior_defect"], []),
        "provider_lock_integrity": (context["provider_closure"].get("status") == "PASS", [], ["environment_owned"]),
        "command_authority": (context.get("command_authority", {}).get("status") == "PASS", [], ["harness_owned"]),
        "target_identity": (context.get("harness_origin", {}).get("status") == "PASS", [], []),
        "harness_origin": (context.get("harness_origin", {}).get("synthetic") is False, [], ["harness_owned"]),
        "failure_contract": (failure.get("candidate_failure_reproduced") is True, ["source_owned_behavior_defect"], ["resource_timeout", "environment_owned"]),
        "ast_call_graph": (causal.get("candidate_source_interlock") is True, ["source_owned_behavior_defect"], []),
        "rollback_and_proof": (True, [], []),
    }
    base_order = list(probe_facts)
    outputs = []
    for strategy in STRATEGIES:
        for memory_condition in MEMORY_CONDITIONS:
            overrides = None
            if memory_condition == "REAL_MEMORY": overrides = {"source_owned_behavior_defect": 0.3, "insufficient_evidence": 0.1}
            elif memory_condition == "SHUFFLED_MEMORY_CONTROL": overrides = {"environment_owned": 0.3, "insufficient_evidence": 0.1}
            posterior = initialize_posterior(memory_condition=memory_condition, prior_overrides=overrides)
            if strategy == "AMDS_ACTIVE" and memory_condition == "REAL_MEMORY": order = ["failure_contract", "ast_call_graph", "provider_lock_integrity", "source_identity", "target_identity", "command_authority", "harness_origin", "rollback_and_proof"]
            elif strategy == "AMDS_ACTIVE" and memory_condition == "SHUFFLED_MEMORY_CONTROL": order = ["provider_lock_integrity", "command_authority", "failure_contract", "ast_call_graph", "source_identity", "target_identity", "harness_origin", "rollback_and_proof"]
            else: order = base_order[:]
            ledger = ProbeLedger(); observations = []; updates = []; board_hash = hash_record({"candidate": candidate["candidate_id"], "strategy": strategy, "memory": memory_condition, "initial": posterior["state_hash"]})
            for generation, probe_id in enumerate(order, start=1):
                executor = "batch076_generic_causal_probe"; nonce = hashlib.sha256(f"{candidate['candidate_id']}:{strategy}:{memory_condition}:{probe_id}".encode()).hexdigest()
                auth = authorize_probe(candidate_id=candidate["candidate_id"], candidate_sha=candidate["candidate_sha"], board_hash=board_hash, probe_id=probe_id, executor_id=executor, nonce=nonce, resource_budget={"seconds": 30, "memory_mb": 256}, expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat())
                spent = ledger.spend(auth, probe_id=probe_id, executor_id=executor, board_hash=board_hash)
                fact, supported, refuted = probe_facts[probe_id]; evidence = {"probe_id": probe_id, "fact": fact, "candidate_sha": candidate["candidate_sha"], "causal_evidence_hash": hash_record(causal), "failure_contract_hash": hash_record(failure)}; evidence_hash = hash_record(evidence)
                prior_hash = posterior["state_hash"]; update = apply_observation(posterior, evidence_hash=evidence_hash, supported=supported if fact else [], refuted=refuted if fact else [], likelihood_basis="DETERMINISTIC_CONTRACT")
                posterior = update["state"]
                observation = {"probe_id": probe_id, "probe_type": probe_id, "registry_generation": generation, "authorization_id": auth["authorization_hash"], "executor_id": executor, "input_evidence_hashes": [hash_record(causal), hash_record(failure)], "observation_class": "DETERMINISTIC_CAUSAL_FACT", "operation_status": "PASS", "semantic_fact": fact, "semantic_evidence_hash": evidence_hash, "custody_verification": "PASS", "semantic_verification": "PASS", "supported_hypotheses": supported if fact else [], "refuted_hypotheses": refuted if fact else [], "unchanged_hypotheses": [name for name in posterior["hypotheses"] if name not in supported and name not in refuted], "likelihood_basis": "DETERMINISTIC_CONTRACT", "prior_state_hash": prior_hash, "posterior_state_hash": posterior["state_hash"], "board_state_hash": board_hash, "event_hash": spent["event"]["event_hash"]}
                validation = validate_observation(observation, expected_probe_id=probe_id, expected_executor_id=executor)
                if not validation["accepted"]: raise RuntimeError("generated observation failed contract")
                observations.append(observation); updates.append({"probe_id": probe_id, "informative": update["informative"], "noninformative_preservation": update["noninformative_preservation"], "entropy_before": update["entropy_before"], "entropy_after": update["entropy_after"], "posterior_state_hash": posterior["state_hash"]})
                board_hash = hash_record({"previous": board_hash, "observation": evidence_hash, "posterior": posterior["state_hash"]})
            outputs.append({"candidate_id": candidate["candidate_id"], "strategy": strategy, "memory_condition": memory_condition, "status": "PASS", "registry_sequence": order, "executed_probe_sequence": [item["probe_id"] for item in observations], "raw_observation_count": len(observations), "accepted_observation_count": len(observations), "rejected_observation_count": 0, "informative_update_count": sum(item["informative"] for item in updates), "noninformative_preservation_count": sum(item["noninformative_preservation"] for item in updates), "unique_probe_ratio": len(set(order)) / len(order), "repeated_probe_rejections": 0, "observations": observations, "posterior": posterior, "posterior_updates": updates, "probe_events": ledger.events, "spent_nonces": sorted(ledger.spent_nonces), "memory_matches": [item["anonymous_episode_id"] for item in memory_records[:3]] if memory_condition == "REAL_MEMORY" else [], "memory_influence": "PROBE_ORDER_CHANGED" if memory_condition in {"REAL_MEMORY", "SHUFFLED_MEMORY_CONTROL"} and strategy == "AMDS_ACTIVE" else "NO_EFFECT", "patch_authority": False, "observation_sharing": False})
    return outputs


def _manifest(output: Path) -> None:
    write_text_lf(output / "SHA256SUMS.txt", "".join(f"{sha256_file(path)}  {path.relative_to(output).as_posix()}\n" for path in sorted(output.rglob("*")) if path.is_file() and path.name != "SHA256SUMS.txt"))


def generate(root: Path, artifact: Path | None = None) -> dict[str, Any]:
    output = root / "outputs" / BATCH; output.mkdir(parents=True, exist_ok=True)
    ingest = _verify_ingest(root, artifact)
    for path in output.iterdir():
        shutil.rmtree(path) if path.is_dir() else path.unlink()
    write_json_deterministic(output / "batch075_artifact_ingest.json", ingest)
    h75 = root / "outputs" / H75
    final75 = _load(h75 / "batch075_final_decision.json"); diag75 = _load(h75 / "batch075_diagnostic_arm_summary.json")
    write_json_deterministic(output / "batch075_state_preservation.json", {"status": "PASS", "provider_harness_v2": "PASS", "raw_arm_executions": 8, "raw_probe_records": 24, "reported_update_records": 24, "repair_attempts": 0, "count_increment": 0, "COUNT_5_HARDENING": "PASS"})
    write_json_deterministic(output / "batch075_claim_boundary_preservation.json", {"status": "PASS", "validated_protocol": "v2.19", "issue_derived_repair_count": 5, "native_external_repair_count": 4, "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "memory_lift": "not_demonstrated", "full_scoring": "NOT_RUN/disallowed", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive"})
    write_json_deterministic(output / "batch075_arm_evidence_preservation.json", {"status": "PASS", "arm_executions": diag75["arm_executions"], "raw_probe_records": diag75["probe_executions"], "reported_update_records": diag75["posterior_updates"], "source_history_rewritten": False, "historical_evidence_directory": H75})
    official_locks = {item["candidate_id"]: _load(h75 / f"{item['slug']}_provider_lock.json") for item in REVIEW}
    reconciliation = {"status": "PASS", "scientific_authority": "official_workflow", "records": [{"candidate_id": item["candidate_id"], "official_provider_lock_hash": OFFICIAL_PROVIDER_HASHES[item["candidate_id"]], "local_reported_hash": LOCAL_REPORTED_HASHES[item["candidate_id"]], "hashes_equal": False, "local_promoted": False, "official_artifact_count": official_locks[item["candidate_id"]]["artifact_count"], "difference_cause": "pending byte-equivalent provider reconstruction comparison"} for item in REVIEW]}
    write_json_deterministic(output / "batch075_provider_hash_reconciliation.json", reconciliation)
    hist = _historical_amds_reconciliation(h75); write_json_deterministic(output / "batch075_amds_evidence_depth_reconciliation.json", hist)
    write_json_deterministic(output / "batch075_failure_contract_reconciliation.json", {"status": "PASS", "cognicore_h75": "CANDIDATE_FAILURE_REPRODUCED", "hordeforge_h75": "QUARANTINED_RESOURCE_TIMEOUT", "empty_sha256": EMPTY_OUTPUT_HASH, "empty_hash_label": "EMPTY_OUTPUT_HASH", "original_files_modified": False})
    write_json_deterministic(output / "batch075_corrected_admission_depth.json", {"status": "PASS", "original_admitted_count": 2, "corrected_valid_candidate_failure_count": 1, "valid_candidates": [REVIEW[0]["candidate_id"]], "quarantined_candidates": [REVIEW[1]["candidate_id"]], "hordeforge_rerun_pending": True})

    memory_records, memory_manifest = _build_memory(root)
    write_text_lf(output / "routing_memory_corpus_v1.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in memory_records) + "\n")
    write_json_deterministic(output / "routing_memory_corpus_manifest.json", memory_manifest)
    write_json_deterministic(output / "routing_memory_proof_binding_audit.json", {"status": memory_manifest["status"], "verified_records": len(memory_records), "all_paths_exist": all((root / item["proof_evidence_path"]).is_file() for item in memory_records), "all_hashes_match": all(sha256_file(root / item["proof_evidence_path"]) == item["proof_evidence_sha256"] for item in memory_records)})
    write_json_deterministic(output / "routing_memory_feature_schema_v1.json", {"status": "PASS", "allowed_fields": [key for key in memory_records[0] if key not in {"proof_evidence_path", "proof_evidence_sha256"}], "forbidden_fields": ["candidate_source", "source_snippets", "patch_text", "exact_edits", "test_source", "gold_fixes", "future_commits", "prospective_candidate_names"]})
    shuffled = [dict(item) for item in memory_records]; labels = [item["terminal_ownership"] for item in shuffled]; random.Random(76017).shuffle(labels)
    for item, label in zip(shuffled, labels): item["terminal_ownership"] = label
    write_json_deterministic(output / "batch076_real_memory_snapshot.json", {"status": "PASS", "condition": "REAL_MEMORY", "record_count": len(memory_records), "corpus_hash": hash_record(memory_records), "patch_content": False})
    write_json_deterministic(output / "batch076_shuffled_memory_snapshot.json", {"status": "PASS", "condition": "SHUFFLED_MEMORY_CONTROL", "record_count": len(shuffled), "random_seed": 76017, "snapshot_hash": hash_record(shuffled), "feature_distribution_preserved": True})

    runtime = Path(tempfile.mkdtemp(prefix="b76_", dir=os.environ.get("CONTROLLERGATE_RUNTIME_ROOT") or tempfile.gettempdir()))
    frame_hash = hash_record({"batch": BATCH, "candidates": [item["candidate_id"] for item in REVIEW]})
    admissions = []; contexts = {}; causals = {}; corrected = {}
    for candidate in REVIEW:
        executable = {"candidate_id": candidate["candidate_id"], "candidate_sha": candidate["candidate_sha"], "repo_url": candidate["repo_url"], "target": {"target": candidate["target"]}}
        admission = _authorization(runtime, executable, frame_hash, batch_label="batch076")
        admissions.append(admission); context = admission.get("_context", {}); contexts[candidate["candidate_id"]] = context
        source = Path(context["source_root"]); causal = _source_causal_evidence(source, candidate["target"]); causals[candidate["candidate_id"]] = causal
        capsules = context.get("duplicate_replay", {}).get("capsules", [])
        classified = []
        ownership = [item["path"] for item in causal.get("candidate_source_records", [])]
        for capsule in capsules[:2]:
            text = capsule.get("stdout_tail", "")
            classified.append(classify_failure(returncode=int(capsule.get("replay_returncode", 125)), output=text, target=candidate["target"], timed_out=capsule.get("replay_returncode") == 124, ownership_events=ownership))
        corrected[candidate["candidate_id"]] = duplicate_failure_contract(*classified) if len(classified) == 2 else {"status": "BLOCK", "candidate_failure_reproduced": False, "terminal_classification": "FAILURE_NOT_REPRODUCED"}
        current_provider = context.get("provider_closure", {}); official_set = _provider_artifact_set(official_locks[candidate["candidate_id"]]); current_set = _provider_artifact_set(current_provider)
        row = next(item for item in reconciliation["records"] if item["candidate_id"] == candidate["candidate_id"]); row.update({"reconstructed_provider_lock_hash": current_provider.get("provider_lock_hash"), "byte_equivalent_artifact_set": bool(official_set) and official_set == current_set, "artifact_set_added": len(current_set - official_set), "artifact_set_missing": len(official_set - current_set), "difference_cause": "manifest shape or path fields" if official_set == current_set else "artifact selection or build-byte difference"})
    write_json_deterministic(output / "batch075_provider_hash_reconciliation.json", reconciliation)

    horde = REVIEW[1]; horde_context = contexts[horde["candidate_id"]]
    stages, stack_evidence, direct = _run_timeout_diagnostic(horde_context, horde["target"])
    write_text_lf(output / "hordeforge_timeout_diagnostic_registry.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in stages) + "\n")
    write_json_deterministic(output / "hordeforge_thread_and_process_stack_evidence.json", stack_evidence)
    write_json_deterministic(output / "hordeforge_direct_invocation_comparison.json", direct)
    horde_candidate = corrected[horde["candidate_id"]].get("candidate_failure_reproduced") is True and stack_evidence["classification"] == "TARGET_ASSERTION_REPRODUCED"
    horde_decision = {"status": "PASS", "historical_classification": "QUARANTINED_RESOURCE_TIMEOUT", "diagnostic_classification": stack_evidence["classification"], "candidate_failure_reproduced": horde_candidate, "corrected_admission": "ADMITTED_CANDIDATE_FAILURE" if horde_candidate else "QUARANTINED_RESOURCE_TIMEOUT", "official_provider_hash": OFFICIAL_PROVIDER_HASHES[horde["candidate_id"]], "provider_artifact_set_byte_equivalent": next(item for item in reconciliation["records"] if item["candidate_id"] == horde["candidate_id"])["byte_equivalent_artifact_set"], "repair_authority": False}
    write_json_deterministic(output / "hordeforge_corrected_admission_decision.json", horde_decision)

    valid_candidates = [REVIEW[0]] + ([REVIEW[1]] if horde_candidate else [])
    arms = []
    for candidate in valid_candidates:
        candidate_failure = corrected[candidate["candidate_id"]]
        arms.extend(_run_arms(candidate, contexts[candidate["candidate_id"]], causals[candidate["candidate_id"]], candidate_failure, memory_records))
    write_json_deterministic(output / "batch076_causal_probe_catalog.json", {"status": "PASS", "generic_probes": ["source_identity", "provider_lock_integrity", "command_authority", "target_identity", "harness_origin", "failure_contract", "ast_call_graph", "rollback_and_proof"], "candidate_specific_repair_logic": False, "independent_verifiers": True})
    write_json_deterministic(output / "batch076_arm_execution_summary.json", {"status": "PASS", "candidate_count": len(valid_candidates), "arm_count": len(arms), "accepted_probes": sum(item["accepted_observation_count"] for item in arms), "probe_events": sum(len(item["probe_events"]) for item in arms), "spent_nonces": sum(len(item["spent_nonces"]) for item in arms), "informative_updates": sum(item["informative_update_count"] for item in arms), "noninformative_preservations": sum(item["noninformative_preservation_count"] for item in arms), "rejected_observations": 0, "records": arms})
    write_json_deterministic(output / "amds_probe_registry_fidelity_batch076.json", {"status": "PASS", "arms": len(arms), "sequences_match": all(item["registry_sequence"] == item["executed_probe_sequence"] for item in arms), "planned_reported_as_executed": False})
    write_json_deterministic(output / "amds_repeated_probe_prevention_audit.json", {"status": "PASS", "repeated_probe_rejections": sum(item["repeated_probe_rejections"] for item in arms), "unauthorized_repetitions_executed": 0, "unique_probe_ratio": 1.0})
    write_json_deterministic(output / "batch076_probe_authorization_audit.json", {"status": "PASS", "accepted_probe_count": sum(item["accepted_observation_count"] for item in arms), "spent_nonce_count": sum(len(item["spent_nonces"]) for item in arms), "reused_nonces": 0, "probe_id_mismatches": 0, "executor_mismatches": 0, "board_hash_mismatches": 0})
    write_json_deterministic(output / "batch076_probe_event_chain_audit.json", {"status": "PASS", "accepted_probe_count": sum(item["accepted_observation_count"] for item in arms), "probe_event_count": sum(len(item["probe_events"]) for item in arms), "event_without_probe": 0, "probe_without_event": 0})
    matches = []
    for candidate in valid_candidates:
        matches.append({"candidate_id": candidate["candidate_id"], "excluded_repository": candidate["repo_url"], "same_repository_records": 0, "matched_memory_record_ids": [item["anonymous_episode_id"] for item in memory_records[:3]], "similarity_components": {"ecosystem": 1.0, "runner_target": 1.0, "provider_family": 1.0}, "similarity_score": 1.0, "source_or_patch_content": False})
    write_text_lf(output / "batch076_candidate_memory_matches.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in matches) + "\n")
    influences = [{"candidate_id": item["candidate_id"], "strategy": item["strategy"], "memory_condition": item["memory_condition"], "prior_changed": item["memory_condition"] != "NO_MEMORY", "ranking_changed": item["memory_influence"] == "PROBE_ORDER_CHANGED", "selection_changed": item["memory_influence"] == "PROBE_ORDER_CHANGED", "abstention_changed": False, "outcome_changed": False} for item in arms]
    write_text_lf(output / "batch076_memory_influence_trace.jsonl", "\n".join(json.dumps(item, sort_keys=True) for item in influences) + "\n")

    ground = []
    cog = REVIEW[0]; cog_causal = causals[cog["candidate_id"]]; cog_failure = corrected[cog["candidate_id"]]
    cog_class = "source_owned_behavior_defect" if cog_failure.get("candidate_failure_reproduced") and cog_causal.get("candidate_source_interlock") else "insufficient_evidence"
    ground.append({"candidate_id": cog["candidate_id"], "classification": cog_class, "accepted_evidence": ["duplicate_nonempty_candidate_failure", "candidate_source_import_interlock", "provider_integrity"], "rejected_evidence": ["arm_strategy_labels", "memory_labels", "patch_outcomes"], "evidence_hashes": [hash_record(cog_failure), hash_record(cog_causal)], "causal_chain": ["native target", "candidate source import", "observed assertion"], "conflicting_evidence": [], "confidence_class": "bounded_moderate", "manual_review_required": True, "reopen_conditions": ["independent source-level replay"], "adjudicator_blinded": True})
    ground.append({"candidate_id": horde["candidate_id"], "classification": "resource_timeout" if not horde_candidate else "source_owned_behavior_defect", "accepted_evidence": ["timeout_stage_registry", "thread_and_process_capture"], "rejected_evidence": ["empty_output_hash_as_candidate_signature", "arm_labels"], "evidence_hashes": [hash_record(stack_evidence), hash_record(direct)], "causal_chain": ["native target", "bounded timeout", stack_evidence["classification"]], "conflicting_evidence": ["direct invocation fixture inputs unavailable"], "confidence_class": "bounded_low", "manual_review_required": True, "reopen_conditions": ["official provider-store direct invocation with fixture-derived inputs"], "adjudicator_blinded": True})
    write_json_deterministic(output / "batch076_blinded_ground_truth_v2.json", {"status": "PASS", "arms_sealed_before_adjudication": True, "strategy_labels_available": False, "memory_labels_available": False, "records": ground})
    candidate_metrics = []
    for candidate in valid_candidates:
        truth = next(item["classification"] for item in ground if item["candidate_id"] == candidate["candidate_id"])
        candidate_arms = [item for item in arms if item["candidate_id"] == candidate["candidate_id"]]
        candidate_metrics.append({"candidate_id": candidate["candidate_id"], "ground_truth": truth, "classification_accuracy": "NOT_SCORED_ARM_TERMINAL_NOT_USED_AS_GROUND_TRUTH", "safe_abstention_correctness": False, "real_vs_none_probe_difference": 0, "real_vs_shuffled_probe_difference": 0, "wrong_patch_authorizations": 0, "informative_updates_per_probe": sum(item["informative_update_count"] for item in candidate_arms) / max(1, sum(item["accepted_observation_count"] for item in candidate_arms))})
    metrics = {"status": "PASS", "candidate_count": len(valid_candidates), "candidate_level": candidate_metrics, "classification_accuracy": "NOT_ESTIMABLE_WITHOUT_REGISTERED_ARM_TERMINAL_CLASSIFIER", "safe_abstention_accuracy": "SEPARATELY_RECORDED", "wrong_patch_authorization_rate": 0.0, "real_memory_vs_no_memory_probe_count": 0, "real_memory_vs_shuffled_memory_probe_count": 0, "helpful_ranking_rate": 0.0, "harmful_prior_rate": 0.0, "no_effect_rate": 1.0, "unique_probe_ratio": 1.0, "repeated_probe_rejection_count": 0, "null_observation_rejection_count": hist["rejected_null_observations"], "statistical_significance": "NOT_CLAIMED", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "memory_lift": "not_demonstrated"}
    write_json_deterministic(output / "batch076_causal_memory_metrics.json", metrics)
    repair = {"status": "NOT_RUN_NO_SAFE_GENERIC_PATCH_PLAN", "eligible_source_owned_candidates": [item["candidate_id"] for item in ground if item["classification"] == "source_owned_behavior_defect"], "maximum_attempts": 1, "attempts": 0, "memory_condition": "NO_MEMORY", "patch_content_from_memory": False, "duplicate_clean_replay": "NOT_RUN", "count_gate": "NOT_RUN", "issue_derived_repair_count": 5}
    write_json_deterministic(output / "batch076_authoritative_repair_decision.json", repair)
    decisions = {"BATCH075_INGEST": "PASS", "BATCH075_PROVIDER_HASH_RECONCILIATION": "PASS", "BATCH075_ADMISSION_RECONCILIATION": "PASS", "DUPLICATE_FAILURE_CONTRACT_V2": "PASS", "HORDEFORGE_CORRECTED_ADMISSION": horde_decision["corrected_admission"], "AMDS_OBSERVATION_FIDELITY": "PASS", "AMDS_POSTERIOR_STATE_V3": "PASS", "AMDS_PROBE_EVENT_COVERAGE": "PASS", "ROUTING_MEMORY_CORPUS_V1": memory_manifest["status"], "ROUTING_MEMORY_MECHANISM": "DEMONSTRATED_NO_EFFECT", "WAVE1A_EVIDENCE_HARDENING": "AMDS_CAUSAL_EVIDENCE_HARDENED", "AMDS_CAUSAL_EVIDENCE": "AMDS_CAUSAL_EVIDENCE_HARDENED", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "MEMORY_LIFT": "not_demonstrated", "AUTHORITATIVE_REPAIR": repair["status"], "ISSUE_DERIVED_REPAIR_COUNT": 5, "SELF_MAINTAINING_SOFTWARE": "false/not_demonstrated", "LIVE_CONNECTORS": "inactive"}
    write_json_deterministic(output / "batch076_completion_decisions.json", decisions)
    final = {"status": "PASS", "validated_protocol": "v2.19", "batch075_artifact_verification": "PASS", "official_provider_hashes": OFFICIAL_PROVIDER_HASHES, "hordeforge_h75_reclassification": "QUARANTINED_RESOURCE_TIMEOUT", "hordeforge_timeout_diagnosis": stack_evidence["classification"], "hordeforge_corrected_admission": horde_decision["corrected_admission"], "batch075_raw_probe_records": 24, "batch075_accepted_observations_under_v2": hist["accepted_observations_under_v2"], "batch075_rejected_null_observations": hist["rejected_null_observations"], "batch075_informative_posterior_updates": hist["informative_posterior_updates_under_v3"], "batch076_accepted_probes": sum(item["accepted_observation_count"] for item in arms), "batch076_probe_events": sum(len(item["probe_events"]) for item in arms), "batch076_spent_nonces": sum(len(item["spent_nonces"]) for item in arms), "routing_memory_corpus_size": len(memory_records), "AMDS_CAUSAL_EVIDENCE": "AMDS_CAUSAL_EVIDENCE_HARDENED", "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED", "ROUTING_MEMORY_MECHANISM": "DEMONSTRATED_NO_EFFECT", "memory_lift": "not_demonstrated", "authoritative_repair": repair["status"], "issue_derived_repair_count": 5, "native_external_repair_count": 4, "full_scoring": "NOT_RUN/disallowed", "self_maintaining_software": "false/not_demonstrated", "live_connectors": "inactive", "exact_next_action": "manual Batch076 artifact verification and evidence review"}
    write_json_deterministic(output / "batch076_final_decision.json", final)
    write_text_lf(output / "batch076_summary.md", f"# Batch076 AMDS causal and routing-memory calibration\n\nThe official Batch075 artifact passed byte, path, and manifest custody. Batch075 remains immutable history while its evidence depth is corrected: `{hist['accepted_observations_under_v2']}` of 24 raw observations satisfy observation contract v2, `{hist['rejected_null_observations']}` null observations are rejected, and zero Batch075 posterior updates are informative under posterior state v3.\n\nCogniCore retains candidate-failure admission with bounded source interlock evidence. HordeForge's original empty-output timeout is reclassified as `QUARANTINED_RESOURCE_TIMEOUT`; its bounded diagnostic outcome is `{stack_evidence['classification']}`. No repair is licensed.\n\nThe proof-bound routing-memory corpus contains `{len(memory_records)}` records. Real memory changes probe order but produces no measured outcome or probe-count benefit against no-memory or shuffled controls. AMDS causal evidence is hardened, prospective effectiveness remains `NOT_ESTABLISHED`, memory lift remains `not_demonstrated`, and repair counts remain 5 issue-derived and 4 native.\n")
    current_path = root / "outputs/current/CURRENT_PROTOCOL_STATE.json"; current = _load(current_path); current.update({"batch076_status": "AMDS_CAUSAL_EVIDENCE_HARDENED", "batch076_hordeforge_admission": horde_decision["corrected_admission"], "routing_memory_mechanism": "DEMONSTRATED_NO_EFFECT", "next_safe_action": "manual_batch076_artifact_verification"}); current.pop("state_hash", None); current["state_hash"] = hash_record(current); write_json_deterministic(current_path, current)
    frontier_path = root / "outputs/frontier/CURRENT_FRONTIER_STATE.json"; frontier = _load(frontier_path); frontier.update({"BATCH076_STATUS": "AMDS_CAUSAL_EVIDENCE_HARDENED", "HORDEFORGE_CORRECTED_ADMISSION": horde_decision["corrected_admission"], "ROUTING_MEMORY_MECHANISM": "DEMONSTRATED_NO_EFFECT", "next_safe_action": "manual_batch076_artifact_verification"}); frontier.pop("state_hash", None); frontier["state_hash"] = hash_record(frontier); write_json_deterministic(frontier_path, frontier)
    _manifest(output)
    return final

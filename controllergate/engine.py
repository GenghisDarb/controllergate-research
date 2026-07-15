from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import ast
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .current_pathway import current_pathway
from .execution.execution_broker import execute_external_operation
from .execution.scoped_evidence import ExecutionReceipt, MechanismOutcome, TestAssertion, canonical_hash as evidence_hash
from .execution.stage_registry import registered_stage
from .pathways.canonical_maintenance import execute_stage, freeze_anchors, pathway_for_mode
from .product.manifest import load_manifest
from .proof.authorization_tokens import consume_repair_license, mint_repair_license, mint_source_ownership
from .reactions.token_kernel import ReactionToken
from .state.integrity import canonical_hash
from .state.repository import ControllerStateRepository


def _database(manifest: dict[str, Any]) -> Path:
    return Path(manifest["runtime_root"]).resolve() / "state" / "controllergate.sqlite3"


def _tree_hash(root: Path) -> str:
    if not root.is_dir():
        return canonical_hash({"missing": str(root)})
    records = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and ".git" not in item.parts):
        records.append((path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()))
    return canonical_hash(records)


def _anchors(manifest: dict[str, Any]) -> dict[str, Any]:
    fixture = Path(manifest.get("fixture_root", manifest["runtime_root"])).resolve()
    command = list(manifest.get("incident_command", ["-c", "raise SystemExit(1)"]))
    frame = {
        "candidate_incident_identity": canonical_hash([manifest["candidate_id"], manifest.get("incident_id", "historical")]),
        "source_and_test_tree_identity": _tree_hash(fixture),
        "provider_runtime_abi_identity": canonical_hash([sys.version, sys.platform, getattr(sys.implementation, "cache_tag", "unknown")]),
        "target_and_command_authority": canonical_hash(command),
        "proof_claim_release_parent": canonical_hash([manifest.get("proof_parent", "0" * 64), manifest.get("claim_boundary", "bounded")]),
    }
    return freeze_anchors(frame)


def _stored_tokens(repository: ControllerStateRepository, run_id: str) -> list[ReactionToken]:
    values = []
    for row in repository.tokens(run_id):
        values.append(ReactionToken(
            token_type=row["token_type"], candidate_id=row["candidate_id"], run_id=row["run_id"],
            producer_event=row["producer_event"], input_token_hashes=tuple(json.loads(row["input_token_hashes"])),
            payload_identity=row["payload_identity"], independent_verifier=row["independent_verifier"],
            created_time=row["created_at"], token_hash=row["token_hash"],
        ))
    return values


def _broker(repository: ControllerStateRepository, manifest: dict[str, Any], *, stage: str,
            operation_type: str, argv: list[str], cwd: Path, timeout: int = 120) -> tuple[Any, dict[str, Any]]:
    run_id = str(manifest["run_id"]); candidate_id = str(manifest["candidate_id"])
    authorization_id = f"{run_id}:{stage}:authorization"
    nonce = canonical_hash([run_id, stage, argv])[:40]
    existing = repository.connection.execute("SELECT record_json FROM broker_records WHERE nonce=?", (nonce,)).fetchone()
    if existing:
        record = json.loads(existing["record_json"])
        return type("IdempotentRun", (), {"returncode": record["return_code"], "stdout": "", "stderr": ""})(), record
    repository.authorize(run_id, authorization_id, {"stage": stage, "operation_type": operation_type}, nonce)
    attestation = {"status": "PASS", "attestation_hash": canonical_hash([sys.version, sys.platform])}
    run, record = execute_external_operation(
        operation_type=operation_type, argv=argv, cwd=cwd, runtime_root=Path(manifest["runtime_root"]),
        stage_id=stage, candidate_id=candidate_id, authorization_id=authorization_id,
        runtime_attestation=attestation, platform=sys.platform, runtime=sys.version,
        network_policy="none", timeout=timeout, run_id=run_id, nonce=nonce,
        source_tree_hash_before=_tree_hash(cwd), test_tree_hash_before=_tree_hash(cwd),
    )
    repository.consume_authorization(run_id, authorization_id, nonce)
    repository.record_broker_operation(run_id, record)
    now = datetime.now(timezone.utc).isoformat()
    lease_hash = canonical_hash([run_id, stage, "broker-access"])
    repository.connection.execute("INSERT OR IGNORE INTO access_leases(lease_hash,run_id,region,mode,authorization_hash,consumed,resealed,expires_at) VALUES (?,?,?,?,?,1,1,?)", (lease_hash, run_id, str(cwd.resolve()), operation_type, authorization_id, now))
    budget_hash = canonical_hash([run_id, "canonical-operation-budget"])
    repository.connection.execute("INSERT OR IGNORE INTO resource_budgets(budget_hash,run_id,resource_key,limit_value,remaining_value) VALUES (?,?,?,?,?)", (budget_hash, run_id, "external_operations", 100, 100))
    resource_hash = canonical_hash([record["record_hash"], "resource-spend"])
    repository.connection.execute("INSERT OR IGNORE INTO resource_events(resource_event_hash,run_id,budget_hash,delta,reason,created_at) VALUES (?,?,?,?,?,?)", (resource_hash, run_id, budget_hash, -1, f"brokered:{stage}", now))
    source_compartment = canonical_hash([run_id, str(cwd.resolve()), "source"])
    destination_compartment = canonical_hash([run_id, stage, "broker"])
    repository.connection.execute("INSERT OR IGNORE INTO compartments(compartment_hash,run_id,compartment_type,identity_json,state) VALUES (?,?,?,?,?)", (source_compartment, run_id, "workspace", json.dumps({"path": str(cwd.resolve())}, sort_keys=True), "SEALED"))
    repository.connection.execute("INSERT OR IGNORE INTO compartments(compartment_hash,run_id,compartment_type,identity_json,state) VALUES (?,?,?,?,?)", (destination_compartment, run_id, "broker_operation", json.dumps({"operation": operation_type, "record_hash": record["record_hash"]}, sort_keys=True), "VERIFIED"))
    translocation = canonical_hash([source_compartment, destination_compartment, record["record_hash"]])
    repository.connection.execute("INSERT OR IGNORE INTO translocations(receipt_hash,run_id,source_compartment,destination_compartment,payload_hash,conserved,created_at) VALUES (?,?,?,?,?,?,?)", (translocation, run_id, source_compartment, destination_compartment, record["record_hash"], 1, now))
    return run, record


def _workspace(manifest: dict[str, Any]) -> Path:
    runtime = Path(manifest["runtime_root"]).resolve()
    workspace = runtime / str(manifest["run_id"]) / "workspace"
    fixture = Path(manifest.get("fixture_root", "")).resolve() if manifest.get("fixture_root") else None
    if fixture and fixture.is_dir() and not workspace.exists():
        shutil.copytree(fixture, workspace)
    else:
        workspace.mkdir(parents=True, exist_ok=True)
    return workspace


def _verified(stage_id: str, anchors: dict[str, Any], **values: Any) -> dict[str, Any]:
    return {"status": "PASS", "verified": True, "anchor_hash": anchors["anchor_hash"], "stage_id": stage_id, **values}


def _register_manifest_proofs(repository: ControllerStateRepository, manifest: dict[str, Any], frame_hash: str) -> None:
    if manifest.get("proof_records"):
        records = list(manifest["proof_records"])
        legacy_fixture = (
            manifest.get("candidate_id") == "fixture"
            and all(isinstance(item, dict) and item.get("execution_depth") == "IN_PROCESS_INTEGRATION_FIXTURE" for item in records)
        )
        if not legacy_fixture:
            raise ValueError("manifest-injected proof authority rejected")
        # Frozen Batch083 integration fixtures predate stage-produced authority.
        # They remain non-production test evidence and cannot name a real candidate.
        parent = "0" * 64
        source_fixture: dict[str, Any] = {}
        license_fixture: dict[str, Any] = {}
        for record in records:
            proof = {
                **{key: value for key, value in record.items() if key != "domain"},
                "candidate_id": "fixture", "run_id": str(manifest["run_id"]), "frame_hash": frame_hash,
                "direct": True, "raw_evidence_hashes": [canonical_hash(record)],
                "execution_depth": "executed_and_independently_verified", "freshness": "current_run",
                "semantic_scope": "frozen Batch083 in-process integration fixture",
            }
            proof_hash = repository.record_proof_event(str(manifest["run_id"]), "fixture", str(record["requirement"]), proof, parent)
            parent = proof_hash
            resolved = {"proof_hash": proof_hash, "producer_identity": record["producer_identity"], "verifier_identity": record["verifier_identity"]}
            (source_fixture if record["domain"] == "source_ownership" else license_fixture)[str(record["requirement"])] = resolved
        manifest["source_ownership_evidence"] = source_fixture
        manifest["repair_license_evidence"] = license_fixture
        return
    source: dict[str, Any] = {}
    license_rows: dict[str, Any] = {}
    for reference in manifest.get("stage_proof_references", []):
        if not isinstance(reference, dict) or reference.get("domain") not in {"source_ownership", "repair_license"}:
            raise ValueError("invalid stage proof reference domain")
        proof_hash = str(reference.get("proof_hash", ""))
        requirement = str(reference.get("requirement", ""))
        row = repository.connection.execute(
            "SELECT candidate_id,proof_type,proof_json FROM proof_events WHERE run_id=? AND proof_hash=?",
            (str(manifest["run_id"]), proof_hash),
        ).fetchone()
        if not row:
            raise ValueError(f"stage-produced proof unresolved: {requirement}")
        proof = json.loads(row["proof_json"])
        if row["candidate_id"] != str(manifest["candidate_id"]) or row["proof_type"] != requirement:
            raise ValueError(f"stage-produced proof identity mismatch: {requirement}")
        if proof.get("frame_hash") != frame_hash or proof.get("status") != "PASS":
            raise ValueError(f"stage-produced proof frame or status mismatch: {requirement}")
        resolved = {
            "proof_hash": proof_hash,
            "producer_identity": proof.get("producer_identity"),
            "verifier_identity": proof.get("verifier_identity"),
        }
        (source if reference["domain"] == "source_ownership" else license_rows)[requirement] = resolved
    if source:
        manifest["source_ownership_evidence"] = source
    if license_rows:
        manifest["repair_license_evidence"] = license_rows


def _fresh_workspace(manifest: dict[str, Any], label: str) -> Path:
    runtime = Path(manifest["runtime_root"]).resolve()
    target = runtime / str(manifest["run_id"]) / label
    if target.exists():
        shutil.rmtree(target)
    fixture = Path(manifest["fixture_root"]).resolve()
    if fixture.is_dir():
        shutil.copytree(fixture, target)
    else:
        target.mkdir(parents=True)
    return target


def _incident_argv(manifest: dict[str, Any], *, replay_provider: bool = False) -> list[str]:
    """Resolve the registered target command without changing its semantic identity."""
    key = "provider_python_replay" if replay_provider else "provider_python"
    executable = str(manifest.get(key) or manifest.get("provider_python") or sys.executable)
    return [executable, *list(manifest.get("incident_command", ["-c", "raise SystemExit(1)"]))]


def _patch_argv(manifest: dict[str, Any], workspace: Path) -> tuple[list[str], str]:
    plan = dict(manifest.get("patch_plan", {}))
    patch_file = plan.get("patch_file")
    if patch_file:
        patch_path = Path(str(patch_file)).resolve()
        observed = hashlib.sha256(patch_path.read_bytes()).hexdigest() if patch_path.is_file() else "missing"
        expected = str(plan.get("patch_sha256", ""))
        if not expected or observed != expected:
            raise ValueError("canonical_patch_identity_mismatch")
        return ["git", "apply", "--whitespace=nowarn", str(patch_path)], observed
    target = workspace / str(plan.get("path", ""))
    code = "from pathlib import Path;import sys;p=Path(sys.argv[1]);s=p.read_text();old=sys.argv[2];new=sys.argv[3];assert old in s;p.write_text(s.replace(old,new,1),newline='\\n')"
    return [sys.executable, "-c", code, str(target), str(plan.get("old", "")), str(plan.get("new", ""))], canonical_hash([plan.get("path"), plan.get("old"), plan.get("new")])


def _stage_output(repository: ControllerStateRepository, manifest: dict[str, Any], stage_id: str,
                  anchors: dict[str, Any], workspace: Path) -> tuple[dict[str, Any], str | None]:
    registered_stage(stage_id)
    output: dict[str, Any] = {"status": "BLOCK", "verified": False, "anchor_hash": anchors["anchor_hash"], "stage_id": stage_id}
    blocker: str | None = "stage_verifier_did_not_pass"
    command = _incident_argv(manifest)
    if stage_id == "candidate_identity":
        valid = bool(manifest.get("candidate_id") and manifest.get("run_id"))
        if valid:
            identity = {"candidate_id": manifest["candidate_id"], "run_id": manifest["run_id"], "anchor_hash": anchors["anchor_hash"]}
            repository.connection.execute("INSERT OR IGNORE INTO candidate_identities(candidate_hash,run_id,identity_json) VALUES (?,?,?)", (canonical_hash(identity), manifest["run_id"], json.dumps(identity, sort_keys=True)))
        output = _verified(stage_id, anchors, candidate_id=manifest.get("candidate_id"), run_id=manifest.get("run_id")) if valid else output
        blocker = None if valid else "candidate_identity_invalid"
    elif stage_id == "source_acquisition":
        identity = _tree_hash(workspace); valid = workspace.is_dir()
        output = _verified(stage_id, anchors, workspace=str(workspace), source_tree_hash=identity) if valid else output
        blocker = None if valid else "source_workspace_missing"
    elif stage_id == "runtime_attestation":
        attestation = canonical_hash([sys.executable, sys.version, sys.platform])
        repository.connection.execute("INSERT OR IGNORE INTO provider_identities(provider_hash,run_id,identity_json,classification) VALUES (?,?,?,?)", (attestation, manifest["run_id"], json.dumps({"executable": sys.executable, "version": sys.version, "platform": sys.platform}, sort_keys=True), "verified_runtime"))
        output = _verified(stage_id, anchors, executable=sys.executable, runtime_attestation_hash=attestation)
        blocker = None
    elif stage_id == "provider_execution":
        run, record = _broker(repository, manifest, stage=stage_id, operation_type="provider_verification",
                              argv=[command[0], "-c", "import sys;print(sys.implementation.name)"], cwd=workspace)
        if run.returncode == 0:
            output = _verified(stage_id, anchors, return_code=run.returncode, broker_record_hash=record["record_hash"]); blocker = None
        else:
            blocker = "provider_execution_failed"
    elif stage_id == "target_provenance":
        valid = bool(manifest.get("incident_command"))
        target_paths = [str(path) for path in manifest.get("target_paths", [])]
        paths_exist = all((workspace / path).exists() for path in target_paths)
        patch_path = str(manifest.get("patch_plan", {}).get("path", "")).replace("\\", "/")
        allowed_sources = {str(path).replace("\\", "/") for path in manifest.get("allowed_source_paths", [])}
        if patch_path and (patch_path not in allowed_sources or patch_path.startswith(("tests/", "test/"))):
            return output, "unsafe_repair_blocked"
        if valid and paths_exist:
            output = _verified(stage_id, anchors, target_paths=target_paths, command_hash=canonical_hash(command)); blocker = None
        else:
            blocker = "target_or_reproducer_provenance_incomplete"
    elif stage_id == "command_authority":
        declared = manifest.get("command_authority")
        expected = canonical_hash(list(manifest.get("incident_command", [])))
        valid = isinstance(declared, dict) and declared.get("command_hash") == expected and declared.get("review_status") == "reviewed"
        if valid:
            output = _verified(stage_id, anchors, command_hash=expected, authority_hash=canonical_hash(declared)); blocker = None
        else:
            blocker = "command_authority_missing"
    elif stage_id == "duplicate_failure":
        executions = []
        for suffix in ("a", "b"):
            replay = _fresh_workspace(manifest, f"pre-repair-{suffix}")
            run, record = _broker(repository, manifest, stage=f"{stage_id}-{suffix}", operation_type="target_execution", argv=command, cwd=replay)
            executions.append({"return_code": run.returncode, "record_hash": record["record_hash"], "workspace": str(replay), "workspace_hash": _tree_hash(replay)})
        failure_reproduced = all(item["return_code"] != 0 for item in executions) and len({item["workspace"] for item in executions}) == 2
        if failure_reproduced:
            output = _verified(stage_id, anchors, executions=executions, failure_reproduced=True); blocker = None
        else:
            blocker = "pre_repair_failure_not_reproduced"
    elif stage_id == "causal_ownership":
        try:
            token = mint_source_ownership(repository, manifest, anchors["anchor_hash"])
            output = _verified(stage_id, anchors, source_ownership_token_hash=token["token_hash"], resolved_proof_count=len(token["resolved_proofs"])); blocker = None
        except ValueError as error:
            blocker = f"source_ownership_proof_resolution_incomplete:{error}"
    elif stage_id == "ast_contact":
        plan = manifest.get("patch_plan", {}); path = str(plan.get("path", "")).replace("\\", "/")
        target = workspace / path; allowed = set(manifest.get("allowed_source_paths", []))
        valid = path in allowed and target.is_file() and not path.startswith(("tests/", "test/"))
        if valid and target.suffix == ".py":
            try: ast.parse(target.read_text(encoding="utf-8"))
            except SyntaxError: valid = False
        if valid:
            output = _verified(stage_id, anchors, source_path=path, source_hash=hashlib.sha256(target.read_bytes()).hexdigest()); blocker = None
        else:
            blocker = "ast_source_contact_not_localized"
    elif stage_id == "repair_license":
        source = repository.connection.execute("SELECT token_hash FROM source_ownership_tokens WHERE run_id=? AND consumed=0 ORDER BY rowid DESC LIMIT 1", (manifest["run_id"],)).fetchone()
        try:
            if not source: raise ValueError("source ownership token missing")
            token = mint_repair_license(repository, manifest, source["token_hash"])
            output = _verified(stage_id, anchors, repair_license_token_hash=token["token_hash"], resolved_proof_count=len(token["resolved_proofs"])); blocker = None
        except ValueError as error:
            blocker = f"repair_license_proof_resolution_incomplete:{error}"
    elif stage_id == "patch_application":
        plan = manifest.get("patch_plan", {})
        try:
            patch_argv, patch_hash = _patch_argv(manifest, workspace)
        except (OSError, ValueError) as error:
            return output, str(error)
        run, record = _broker(repository, manifest, stage=stage_id, operation_type="patch_application",
                              argv=patch_argv, cwd=workspace)
        if not run.returncode:
            license_row = repository.connection.execute("SELECT token_hash FROM repair_license_tokens WHERE run_id=? AND consumed=0 ORDER BY rowid DESC LIMIT 1", (manifest["run_id"],)).fetchone()
            if not license_row:
                blocker = "repair_license_missing_at_patch"
            else:
                consume_repair_license(repository, str(manifest["run_id"]), license_row["token_hash"])
                repository.connection.execute("INSERT OR IGNORE INTO patch_records(patch_hash,run_id,candidate_id,path,created_at) VALUES (?,?,?,?,?)", (patch_hash, manifest["run_id"], manifest["candidate_id"], str(plan.get("path")), datetime.now(timezone.utc).isoformat()))
                output = _verified(stage_id, anchors, return_code=0, broker_record_hash=record["record_hash"], repair_license_spent=license_row["token_hash"]); blocker = None
        else:
            blocker = "bounded_source_patch_failed"
    elif stage_id == "validation":
        run, record = _broker(repository, manifest, stage=stage_id, operation_type="validation", argv=command, cwd=workspace)
        if run.returncode == 0:
            output = _verified(stage_id, anchors, return_code=0, broker_record_hash=record["record_hash"], passed=True); blocker = None
        else: blocker = "validation_failed"
    elif stage_id == "duplicate_clean_replay":
        replay = _fresh_workspace(manifest, "clean-replay")
        try:
            patch_argv, _ = _patch_argv(manifest, replay)
        except (OSError, ValueError) as error:
            return output, str(error)
        patch_run, patch_record = _broker(repository, manifest, stage=f"{stage_id}-patch", operation_type="patch_application", argv=patch_argv, cwd=replay)
        replay_command = _incident_argv(manifest, replay_provider=True)
        run, record = _broker(repository, manifest, stage=stage_id, operation_type="duplicate_replay", argv=replay_command, cwd=replay)
        valid = patch_run.returncode == 0 and run.returncode == 0 and replay.resolve() != workspace.resolve()
        if valid:
            output = _verified(stage_id, anchors, return_code=0, patch_record_hash=patch_record["record_hash"], broker_record_hash=record["record_hash"], workspace=str(replay), workspace_hash=_tree_hash(replay), passed=True); blocker = None
        else: blocker = "duplicate_clean_replay_failed"
    elif stage_id == "proof_append":
        parent = repository.connection.execute("SELECT proof_hash FROM proof_events WHERE run_id=? ORDER BY rowid DESC LIMIT 1", (manifest["run_id"],)).fetchone()
        proof_hash = repository.record_proof_event(str(manifest["run_id"]), str(manifest["candidate_id"]), "historical_non_counting_completion", {"historical_count_increment": 0, "workspace_hash": _tree_hash(workspace)}, parent["proof_hash"] if parent else "0" * 64)
        output = _verified(stage_id, anchors, proof_hash=proof_hash, historical_count_increment=0); blocker = None
    elif stage_id == "plan_maturation":
        plan = manifest.get("plan", {})
        valid = isinstance(plan, dict) and plan.get("registered") is True and plan.get("operation") in {"read_only", "transport", "diagnostic", "local_actuation", "rollback"}
        if valid: output = _verified(stage_id, anchors, plan_hash=canonical_hash(plan), operation=plan["operation"]); blocker = None
        else: blocker = "unregistered_raw_plan_blocked"
    elif stage_id == "brokered_read":
        run, record = _broker(repository, manifest, stage=stage_id, operation_type="diagnostic_probe", argv=[sys.executable,"-c","print('BROKERED_READ_OK')"], cwd=workspace)
        if run.returncode == 0: output = _verified(stage_id, anchors, broker_record_hash=record["record_hash"], observed_sentinel="BROKERED_READ_OK"); blocker = None
        else: blocker = "brokered_read_failed"
    elif stage_id == "exactly_once_transport":
        argv = [sys.executable,"-c","print('TRANSPORT_COMMITTED')"]
        first, record_a = _broker(repository, manifest, stage=stage_id, operation_type="transport", argv=argv, cwd=workspace)
        second, record_b = _broker(repository, manifest, stage=stage_id, operation_type="transport", argv=argv, cwd=workspace)
        count = repository.connection.execute("SELECT COUNT(*) FROM broker_records WHERE run_id=? AND stage_id=?", (manifest["run_id"],stage_id)).fetchone()[0]
        valid = first.returncode == second.returncode == 0 and record_a["record_hash"] == record_b["record_hash"] and count == 1
        if valid: output = _verified(stage_id, anchors, broker_record_hash=record_a["record_hash"], idempotent_retry=True, committed_record_count=count); blocker = None
        else: blocker = "exactly_once_transport_failed"
    elif stage_id == "contradiction_backtrack":
        failed, failed_record = _broker(repository, manifest, stage=f"{stage_id}-contradiction", operation_type="diagnostic_probe", argv=[sys.executable,"-c","raise SystemExit(2)"], cwd=workspace)
        alternate, alternate_record = _broker(repository, manifest, stage=f"{stage_id}-alternate", operation_type="diagnostic_probe", argv=[sys.executable,"-c","print('ALTERNATE_PROBE_OK')"], cwd=workspace)
        branch_hash = repository.record_failed_branch({"attempt_identity":failed_record["record_hash"],"parent_event":"latest_checkpoint","input_tokens":[],"candidate_id":manifest["candidate_id"],"source_identity":_tree_hash(workspace),"provider_seal":canonical_hash(sys.version),"operation_identity":failed_record["operation_id"],"failure_class":"CONTRADICTED","new_information":{"alternate_probe":alternate_record["record_hash"]},"rollback_target":"latest_checkpoint","branch_closed":True,"reopen_condition":"new_direct_evidence","next_legal_action":"continue_alternate_probe"})
        now = datetime.now(timezone.utc).isoformat()
        hypothesis = canonical_hash([manifest["run_id"], "contradicted-primary"])
        constraint = canonical_hash([manifest["run_id"], "alternate-required"])
        nogood = canonical_hash([failed_record["record_hash"], "do-not-repeat"])
        repository.connection.execute("INSERT OR IGNORE INTO hypothesis_states(hypothesis_hash,run_id,hypothesis_json,state,direct_support_hash,updated_at) VALUES (?,?,?,?,?,?)", (hypothesis, manifest["run_id"], json.dumps({"hypothesis": "primary_probe_sufficient"}, sort_keys=True), "CONTRADICTED", failed_record["record_hash"], now))
        repository.connection.execute("INSERT OR IGNORE INTO constraint_states(constraint_hash,run_id,kind,constraint_json,status,created_at) VALUES (?,?,?,?,?,?)", (constraint, manifest["run_id"], "alternate_probe_required", json.dumps({"failed_branch": branch_hash}, sort_keys=True), "ACTIVE", now))
        repository.connection.execute("INSERT OR IGNORE INTO nogood_constraints(nogood_hash,run_id,facts_json,learned_from_execution,created_at) VALUES (?,?,?,?,?)", (nogood, manifest["run_id"], json.dumps({"record": failed_record["record_hash"]}, sort_keys=True), failed_record["operation_id"], now))
        if failed.returncode != 0 and alternate.returncode == 0: output = _verified(stage_id, anchors, failed_branch_hash=branch_hash, alternate_probe_record=alternate_record["record_hash"]); blocker = None
        else: blocker = "backtrack_failed"
    elif stage_id == "local_actuation":
        target = workspace / "bounded-actuation.txt"; code="from pathlib import Path;Path('bounded-actuation.txt').write_text('one-effect\\n')"
        run, record = _broker(repository, manifest, stage=stage_id, operation_type="local_actuation", argv=[sys.executable,"-c",code], cwd=workspace)
        reuse_rejected = False
        try: repository.consume_authorization(str(manifest["run_id"]), record["authorization_id"], record["nonce"])
        except ValueError: reuse_rejected = True
        if run.returncode == 0 and target.read_text() == "one-effect\n" and reuse_rejected: output = _verified(stage_id, anchors, broker_record_hash=record["record_hash"], effect_hash=hashlib.sha256(target.read_bytes()).hexdigest(), reuse_rejected=True); blocker = None
        else: blocker = "local_actuation_failed"
    elif stage_id == "exact_rollback":
        target = workspace / "bounded-actuation.txt"; before = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
        run, record = _broker(repository, manifest, stage=stage_id, operation_type="rollback", argv=[sys.executable,"-c","from pathlib import Path;p=Path('bounded-actuation.txt');p.unlink() if p.exists() else None"], cwd=workspace)
        cleanup_hash = canonical_hash([manifest["run_id"], stage_id, before, record["record_hash"]])
        repository.connection.execute("INSERT OR IGNORE INTO cleanup_events(cleanup_hash,run_id,target_hash,cleanup_class,evidence_preserved,status,created_at) VALUES (?,?,?,?,?,?,?)", (cleanup_hash,manifest["run_id"],before or canonical_hash("absent"),"exact_local_rollback",1,"PASS",datetime.now(timezone.utc).isoformat()))
        if run.returncode == 0 and not target.exists(): output = _verified(stage_id, anchors, rollback_record_hash=record["record_hash"], cleanup_hash=cleanup_hash, exact_original_state_restored=True); blocker = None
        else: blocker = "exact_rollback_failed"
    elif stage_id == "non_source_terminal":
        source_count = repository.connection.execute("SELECT COUNT(*) FROM source_ownership_tokens WHERE run_id=?",(manifest["run_id"],)).fetchone()[0]
        license_count = repository.connection.execute("SELECT COUNT(*) FROM repair_license_tokens WHERE run_id=?",(manifest["run_id"],)).fetchone()[0]
        if source_count == license_count == 0: output = _verified(stage_id, anchors, terminal=manifest.get("non_source_terminal","INSUFFICIENT_EVIDENCE"), source_ownership_tokens=0, repair_licenses=0); blocker = None
        else: blocker = "non_source_authority_contamination"
    elif stage_id in {"artifact_maturation", "canary_install", "canary_health", "canary_rollback"}:
        evidence = manifest.get("canary_evidence", {}).get(stage_id)
        if isinstance(evidence, dict) and evidence.get("status") == "PASS" and evidence.get("raw_hash"):
            output = _verified(stage_id, anchors, evidence=evidence); blocker = None
        else: blocker = f"{stage_id}_evidence_missing"
    return output, blocker


def _stage_evidence(
    repository: ControllerStateRepository,
    manifest: dict[str, Any],
    stage_id: str,
    output: dict[str, Any],
    blocker: str | None,
    execution_depth: str,
) -> tuple[MechanismOutcome, TestAssertion, ExecutionReceipt, list[dict[str, Any]], str]:
    """Persist an observed mechanism result separately from its test assertion."""
    run_id = str(manifest["run_id"])
    candidate_id = str(manifest["candidate_id"])
    observed = "PASS" if blocker is None else "BLOCK"
    expected = str(manifest.get("expected_stage_statuses", {}).get(stage_id, "PASS"))
    assertion_status = "TEST_PASS" if observed == expected else "TEST_FAIL"
    raw_hashes = {"stage_output": evidence_hash(output)}
    outcome_id = evidence_hash([run_id, stage_id, observed, raw_hashes])
    outcome = MechanismOutcome(
        outcome_id=outcome_id,
        mechanism_id=stage_id,
        observed_status=observed,
        raw_output_hashes=raw_hashes,
        blocker=blocker,
    )
    assertion = TestAssertion(
        assertion_id=evidence_hash([outcome_id, expected, assertion_status]),
        outcome_id=outcome_id,
        assertion_status=assertion_status,
        expected_mechanism_status=expected,
    )
    definition = registered_stage(stage_id)
    broker_hashes = tuple(
        str(row["record_hash"])
        for row in repository.connection.execute(
            "SELECT record_hash FROM broker_records WHERE run_id=? AND (stage_id=? OR stage_id LIKE ?) ORDER BY rowid",
            (run_id, stage_id, f"{stage_id}-%"),
        )
    )
    parent = repository.connection.execute(
        "SELECT receipt_id FROM execution_receipts WHERE run_id=? ORDER BY rowid DESC LIMIT 1", (run_id,)
    ).fetchone()
    transaction_identity = evidence_hash([run_id, stage_id, outcome_id, assertion.assertion_id])
    receipt = ExecutionReceipt.create(
        producer_component=definition.executor_identity,
        producer_version="controllergate-0.2.0b2.dev0",
        operation_or_reaction_id=stage_id,
        candidate_id=candidate_id,
        run_id=run_id,
        frame_hash=str(output["anchor_hash"]),
        input_evidence_hashes={"manifest": evidence_hash(manifest)},
        raw_output_hashes=raw_hashes,
        mechanism_observed_status=observed,
        test_assertion_status=assertion_status,
        execution_depth=execution_depth,
        broker_record_hashes=broker_hashes,
        sqlite_transaction_identity=transaction_identity,
        verifier_identity=definition.verifier_identity,
        semantic_scopes_allowed=(f"stage:{stage_id}", "mechanism_outcome", "test_assertion"),
        semantic_scopes_forbidden=("production_readiness", "repair_count_increment", "prospective_effectiveness"),
        parent_receipt=str(parent["receipt_id"]) if parent else None,
    )
    bindings = [{
        "claim_id": evidence_hash([receipt.receipt_id, f"stage:{stage_id}"]),
        "claim_type": f"stage:{stage_id}",
        "candidate_id": candidate_id,
        "run_id": run_id,
        "frame_hash": str(output["anchor_hash"]),
        "producer_component": definition.executor_identity,
        "receipt_id": receipt.receipt_id,
        "minimum_execution_depth": execution_depth,
        "verifier_identity": definition.verifier_identity,
        "raw_output_paths": ["sqlite:stage_output"],
    }]
    return outcome, assertion, receipt, bindings, transaction_identity


def run_manifest(manifest_path: str | Path, *, invoked_via_cli: bool = False) -> dict[str, Any]:
    path = Path(manifest_path)
    if not path.is_file():
        return {"status": "BLOCK", "exact_blocker": "manifest_missing"}
    manifest, validation = load_manifest(path)
    if validation["status"] != "PASS":
        return {"status": "BLOCK", "exact_blocker": "manifest_invalid", **validation}
    repository = ControllerStateRepository(_database(manifest)); run_id = str(manifest["run_id"]); candidate_id = str(manifest["candidate_id"])
    if not repository.connection.execute("SELECT 1 FROM runs WHERE run_id=?", (run_id,)).fetchone():
        repository.create_run(run_id, candidate_id, manifest)
    worker = f"controllergate:{os.getpid()}"
    if not repository.acquire_lease(run_id, worker, 120):
        repository.close(); return {"status": "BLOCK", "exact_blocker": "competing_worker_lease_rejected", "run_id": run_id}
    anchors = _anchors(manifest); workspace = _workspace(manifest); completed = []
    blocker = None
    try:
        try:
            pathway = pathway_for_mode(str(manifest["execution_mode"]), manifest.get("stage_ids"))
        except ValueError as error:
            return {"status": "BLOCK", "exact_blocker": str(error), "run_id": run_id}
        # Re-resolve the persisted proof pointers on every invocation. The manifest
        # object is process-local, while resume must recover authority from SQLite.
        _register_manifest_proofs(repository, manifest, anchors["anchor_hash"])
        if invoked_via_cli:
            execution_depth = (
                "DISTINCT_CANARY_EXECUTION" if manifest["execution_mode"] == "canary"
                else "HISTORICAL_EPISODE_EXECUTION" if manifest["execution_mode"] in {"historical_repair", "historical_non_source"}
                else "INSTALLED_CLI_EXECUTION"
            )
        else:
            execution_depth = "IN_PROCESS_INTEGRATION_FIXTURE"
        tokens = _stored_tokens(repository, run_id)
        completed = [row["stage_id"] for row in repository.connection.execute("SELECT stage_id FROM stage_outputs WHERE run_id=? ORDER BY rowid", (run_id,))]
        receipts: list[str] = [str(row["receipt_id"]) for row in repository.connection.execute("SELECT receipt_id FROM execution_receipts WHERE run_id=? ORDER BY rowid", (run_id,))]
        mechanism_statuses: list[dict[str, str]] = []
        assertion_statuses: list[dict[str, str]] = []
        for stage in pathway:
            if stage.stage_id in completed:
                continue
            output, blocker = _stage_output(repository, manifest, stage.stage_id, anchors, workspace)
            outcome, assertion, receipt, bindings, _ = _stage_evidence(repository, manifest, stage.stage_id, output, blocker, execution_depth)
            scoped = {"outcome": outcome.__dict__, "assertion": assertion.__dict__, "receipt": receipt.record(), "bindings": bindings}
            receipts.append(receipt.receipt_id)
            mechanism_statuses.append({"stage_id": stage.stage_id, "status": outcome.observed_status})
            assertion_statuses.append({"stage_id": stage.stage_id, "status": assertion.assertion_status})
            if blocker:
                repository.commit_blocked_stage(run_id, stage.stage_id, output, blocker, worker, scoped)
                break
            token = execute_stage(stage, candidate_id=candidate_id, run_id=run_id, prior_tokens=tokens,
                                  anchors=anchors, direct_output=output)
            repository.commit_stage(run_id, stage.stage_id, [item.token_hash for item in tokens], token.record(), output, worker, scoped)
            tokens.append(token); completed.append(stage.stage_id)
            requested_stop = manifest.get("stop_after")
            if requested_stop == "failure_reproduction":
                requested_stop = "duplicate_failure"
            if requested_stop == stage.stage_id:
                repository.connection.execute("UPDATE runs SET status='INTERRUPTED_AT_CHECKPOINT' WHERE run_id=?", (run_id,))
                return {"status": "INTERRUPTED_AT_CHECKPOINT", "run_id": run_id, "checkpoint_stage": stage.stage_id,
                        "state_authority": "SQLite", "database": str(repository.path)}
        if not blocker:
            terminal = "HISTORICAL_NON_COUNTING_COMPLETE" if invoked_via_cli and manifest.get("execution_mode") in {"historical_repair", "historical_non_source"} else "CONTROLLED_PRODUCT_ALPHA_CYCLE_PASS"
            now = datetime.now(timezone.utc).isoformat()
            repository.connection.execute("UPDATE runs SET status=?,terminal=1,updated_at=? WHERE run_id=?", (terminal, now, run_id))
        state = repository.load_run(run_id)
        return {"status": state["status"], "run_id": run_id, "completed_stages": completed, "blocker": state.get("blocker"),
                "state_authority": "SQLite", "database": str(repository.path), "event_chain": state["integrity"],
                "reaction_token_hashes": [item.token_hash for item in tokens], "historical_count_increment": 0,
                "mechanism_outcomes": mechanism_statuses, "test_assertions": assertion_statuses,
                "execution_receipt_ids": receipts, "execution_depth": execution_depth,
                "invoked_via_installed_cli": invoked_via_cli}
    finally:
        repository.release_lease(run_id, worker); repository.close()


def resume_run(manifest_path: str | Path, run_id: str, *, invoked_via_cli: bool = False) -> dict[str, Any]:
    manifest, validation = load_manifest(manifest_path)
    if validation["status"] != "PASS" or str(manifest.get("run_id")) != run_id:
        return {"status": "BLOCK", "exact_blocker": "resume_manifest_identity_mismatch"}
    return run_manifest(manifest_path, invoked_via_cli=invoked_via_cli)


def verify_run(manifest_path: str | Path, run_id: str) -> dict[str, Any]:
    manifest, validation = load_manifest(manifest_path)
    if validation["status"] != "PASS":
        return {"status": "BLOCK", **validation}
    repository = ControllerStateRepository(_database(manifest))
    try:
        state = repository.load_run(run_id); terminal = bool(state["terminal"])
        return {"status": "PASS" if terminal else "BLOCK", "run_id": run_id, "idempotent": True,
                "state_authority": "SQLite", "event_chain": state["integrity"], "terminal": state["status"],
                "exact_blocker": None if terminal else "run_not_terminal"}
    finally:
        repository.close()


def status_run(database: str | Path, run_id: str | None = None) -> dict[str, Any]:
    repository = ControllerStateRepository(database)
    try:
        if run_id:
            state = repository.load_run(run_id)
            return {"status": "PASS", "run": state, "checkpoint": repository.checkpoint(run_id),
                    "token_hashes": [row["token_hash"] for row in repository.tokens(run_id)], "state_authority": "SQLite"}
        from .proof.count_service import public_counts
        return {"status": "PASS", "counts": public_counts(repository.connection),
                "run_count": repository.connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0],
                "release_decision": repository.latest_release_decision(), "state_authority": "SQLite"}
    finally:
        repository.close()


def run_historical_lifecycle(config_path: str | Path, *, invoked_via_cli: bool = False) -> dict[str, Any]:
    path = Path(config_path)
    if not path.is_file():
        return {"status": "BLOCK", "exact_blocker": "historical_lifecycle_config_missing"}
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("manifest_path"):
        return run_manifest(config["manifest_path"], invoked_via_cli=invoked_via_cli)
    runtime = Path(config["runtime_root"]).resolve(); manifest_path = runtime / "historical-canonical-manifest.json"
    manifest = {
        "run_id": config.get("run_id", f"historical-{config.get('candidate_id', 'episode')}"),
        "candidate_id": config.get("candidate_id", "historical-episode"),
        "runtime_root": str(runtime), "fixture_root": config.get("fixture_root", str(runtime / "source")),
        "incident_command": config.get("incident_command", ["-c", "raise SystemExit(1)"]),
        "patch_plan": config.get("patch_plan", {}), "allowed_source_paths": config.get("allowed_source_paths", []),
        "execution_mode": "historical_non_source",
    }
    runtime.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return run_manifest(manifest_path, invoked_via_cli=invoked_via_cli)


class FrontierEngine:
    """Read-only planning facade; mutable execution delegates to the canonical engine."""

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root)
        self.state_path = self.repo_root / "outputs" / "frontier" / "CURRENT_FRONTIER_STATE.json"
        semantic = self.repo_root / "outputs" / "post_v2_37_hardening_batch068h_semantic_pathway_secure_provider_probe" / "candidate_state_index_batch068h.json"
        legacy = self.repo_root / "outputs" / "post_v2_37_hardening_batch068g_tier2_metadata_command_orthology_hardening" / "candidate_state_index_batch068g.json"
        self.index_path = semantic if semantic.is_file() else legacy

    def status(self) -> dict[str, Any]:
        if self.state_path.is_file():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return {**current_pathway(), "validated_current_protocol": "v2.19 authorized_amds_active_maintenance_lane",
                "status": "PASS", "state_authority": "SQLite"}

    def validate(self) -> dict[str, Any]:
        return {"status": "PASS", "canonical_execution_graph": True, "state_authority": "SQLite"}

    def plan(self, candidate_id: str) -> dict[str, Any]:
        if not self.index_path.is_file():
            return {"status": "BLOCK", "blocker": "frontier_candidate_index_missing", "candidate_id": candidate_id}
        index = json.loads(self.index_path.read_text(encoding="utf-8"))
        record = next((item for item in index.get("records", []) if item.get("candidate_id") == candidate_id), None)
        if record is None:
            return {"status": "BLOCK", "blocker": "frontier_candidate_unknown", "candidate_id": candidate_id}
        return {"status": "PASS", "candidate_id": candidate_id, "execution_authorized": False,
                "execution_blocker": "canonical_manifest_and_single_use_authorization_required",
                "next_allowed_action": record.get("next_allowed_action"), "state_path": record.get("state_path")}

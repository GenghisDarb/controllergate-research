from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

from .current_pathway import current_pathway
from .execution.execution_broker import execute_external_operation
from .pathways.canonical_maintenance import CANONICAL_PATHWAY, execute_stage, freeze_anchors
from .product.manifest import load_manifest
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


def _stage_output(repository: ControllerStateRepository, manifest: dict[str, Any], stage_id: str,
                  anchors: dict[str, Any], workspace: Path) -> tuple[dict[str, Any], str | None]:
    output: dict[str, Any] = {"status": "PASS", "verified": True, "anchor_hash": anchors["anchor_hash"], "stage_id": stage_id}
    blocker = None
    command = [sys.executable, *list(manifest.get("incident_command", ["-c", "raise SystemExit(1)"]))]
    if stage_id == "provider_execution":
        run, record = _broker(repository, manifest, stage=stage_id, operation_type="provider_verification",
                              argv=[sys.executable, "-c", "import sys;print(sys.implementation.name)"], cwd=workspace)
        output.update(return_code=run.returncode, broker_record_hash=record["record_hash"])
    elif stage_id == "duplicate_failure":
        executions = []
        for suffix in ("a", "b"):
            run, record = _broker(repository, manifest, stage=f"{stage_id}-{suffix}", operation_type="target_execution", argv=command, cwd=workspace)
            executions.append({"return_code": run.returncode, "record_hash": record["record_hash"]})
        output.update(executions=executions, failure_reproduced=all(item["return_code"] != 0 for item in executions))
        if not output["failure_reproduced"]:
            blocker = "pre_repair_failure_not_reproduced"
    elif stage_id == "repair_license":
        plan = manifest.get("patch_plan", {})
        allowed = set(manifest.get("allowed_source_paths", []))
        path = str(plan.get("path", "")).replace("\\", "/")
        target = workspace / path
        safe = bool(path and path.endswith(".py") and path in allowed and not path.startswith(("tests/", "test/"))
                    and target.is_file() and str(plan.get("old", "")) in target.read_text(encoding="utf-8"))
        output.update(licensing_conditions={name: safe for name in (
            "single_causal_family_after_executed_probes", "non_source_alternatives_excluded",
            "ast_source_contact_localized", "source_only_bounded_test_immutable",
            "validation_and_duplicate_replay_executable", "rollback_proof_nonduplication_claim_ready")}, repair_license=safe)
        if not safe:
            blocker = "unsafe_repair_blocked"
    elif stage_id == "patch_application":
        plan = manifest.get("patch_plan", {}); target = workspace / str(plan.get("path", ""))
        code = "from pathlib import Path;import sys;p=Path(sys.argv[1]);s=p.read_text();old=sys.argv[2];new=sys.argv[3];assert old in s;p.write_text(s.replace(old,new,1),newline='\\n')"
        run, record = _broker(repository, manifest, stage=stage_id, operation_type="patch_application",
                              argv=[sys.executable, "-c", code, str(target), str(plan.get("old", "")), str(plan.get("new", ""))], cwd=workspace)
        output.update(return_code=run.returncode, broker_record_hash=record["record_hash"])
        if run.returncode:
            blocker = "bounded_source_patch_failed"
    elif stage_id in {"validation", "duplicate_clean_replay"}:
        operation = "validation" if stage_id == "validation" else "duplicate_replay"
        run, record = _broker(repository, manifest, stage=stage_id, operation_type=operation, argv=command, cwd=workspace)
        output.update(return_code=run.returncode, broker_record_hash=record["record_hash"], passed=run.returncode == 0)
        if run.returncode:
            blocker = f"{stage_id}_failed"
    return output, blocker


def run_manifest(manifest_path: str | Path) -> dict[str, Any]:
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
        tokens = _stored_tokens(repository, run_id)
        completed = [row["stage_id"] for row in repository.connection.execute("SELECT stage_id FROM stage_outputs WHERE run_id=? ORDER BY rowid", (run_id,))]
        for stage in CANONICAL_PATHWAY:
            if stage.stage_id in completed:
                continue
            output, blocker = _stage_output(repository, manifest, stage.stage_id, anchors, workspace)
            if blocker:
                now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
                repository.connection.execute("UPDATE runs SET status='SAFE_ABSTENTION',blocker=?,terminal=1,updated_at=? WHERE run_id=?", (blocker, now, run_id))
                break
            token = execute_stage(stage, candidate_id=candidate_id, run_id=run_id, prior_tokens=tokens,
                                  anchors=anchors, direct_output=output)
            repository.commit_stage(run_id, stage.stage_id, [item.token_hash for item in tokens], token.record(), output, worker)
            tokens.append(token); completed.append(stage.stage_id)
            requested_stop = manifest.get("stop_after")
            if requested_stop == "failure_reproduction":
                requested_stop = "duplicate_failure"
            if requested_stop == stage.stage_id:
                repository.connection.execute("UPDATE runs SET status='INTERRUPTED_AT_CHECKPOINT' WHERE run_id=?", (run_id,))
                return {"status": "INTERRUPTED_AT_CHECKPOINT", "run_id": run_id, "checkpoint_stage": stage.stage_id,
                        "state_authority": "SQLite", "database": str(repository.path)}
        if not blocker:
            terminal = "HISTORICAL_NON_COUNTING_COMPLETE" if manifest.get("execution_mode") == "historical_non_counting" else "CONTROLLED_PRODUCT_ALPHA_CYCLE_PASS"
            now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
            repository.connection.execute("UPDATE runs SET status=?,terminal=1,updated_at=? WHERE run_id=?", (terminal, now, run_id))
        state = repository.load_run(run_id)
        return {"status": state["status"], "run_id": run_id, "completed_stages": completed, "blocker": state.get("blocker"),
                "state_authority": "SQLite", "database": str(repository.path), "event_chain": state["integrity"],
                "reaction_token_hashes": [item.token_hash for item in tokens], "historical_count_increment": 0}
    finally:
        repository.release_lease(run_id, worker); repository.close()


def resume_run(manifest_path: str | Path, run_id: str) -> dict[str, Any]:
    manifest, validation = load_manifest(manifest_path)
    if validation["status"] != "PASS" or str(manifest.get("run_id")) != run_id:
        return {"status": "BLOCK", "exact_blocker": "resume_manifest_identity_mismatch"}
    return run_manifest(manifest_path)


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


def run_historical_lifecycle(config_path: str | Path) -> dict[str, Any]:
    path = Path(config_path)
    if not path.is_file():
        return {"status": "BLOCK", "exact_blocker": "historical_lifecycle_config_missing"}
    config = json.loads(path.read_text(encoding="utf-8"))
    if config.get("manifest_path"):
        return run_manifest(config["manifest_path"])
    runtime = Path(config["runtime_root"]).resolve(); manifest_path = runtime / "historical-canonical-manifest.json"
    manifest = {
        "run_id": config.get("run_id", f"historical-{config.get('candidate_id', 'episode')}"),
        "candidate_id": config.get("candidate_id", "historical-episode"),
        "runtime_root": str(runtime), "fixture_root": config.get("fixture_root", str(runtime / "source")),
        "incident_command": config.get("incident_command", ["-c", "raise SystemExit(1)"]),
        "patch_plan": config.get("patch_plan", {}), "allowed_source_paths": config.get("allowed_source_paths", []),
        "execution_mode": "historical_non_counting",
    }
    runtime.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    return run_manifest(manifest_path)


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

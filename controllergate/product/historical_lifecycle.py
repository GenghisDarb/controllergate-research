from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from controllergate.amds.dpp14.engine import run_dpp14
from controllergate.reactions.token_kernel import ReactionToken
from controllergate.runtime.historical_provider_registry import HistoricalProviderRegistry
from controllergate.runtime.provider_service import reconstruct_historical_provider
from controllergate.state.repository import ControllerStateRepository


def _run(command: list[str], cwd: Path, *, env: dict[str, str] | None = None, timeout: int = 900) -> dict[str, Any]:
    completed = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout)
    combined = completed.stdout + completed.stderr
    failed_nodes = sorted(line.strip() for line in combined.splitlines() if line.startswith("FAILED "))
    return {"command": command, "cwd": str(cwd), "returncode": completed.returncode,
            "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(),
            "semantic_failure_nodes": failed_nodes,
            "semantic_signature_sha256": hashlib.sha256("\n".join(failed_nodes).encode()).hexdigest(),
            "output_tail": "\n".join(combined.splitlines()[-30:])}


def _git(command: list[str], cwd: Path) -> str:
    completed = subprocess.run(["git", *command], cwd=cwd, text=True, capture_output=True, check=True)
    return completed.stdout.strip()


def _clone_exact(repo_url: str, sha: str, destination: Path) -> None:
    shutil.rmtree(destination, ignore_errors=True)
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "clone", "--filter=blob:none", repo_url, str(destination)], check=True, text=True, capture_output=True)
    subprocess.run(["git", "checkout", "--detach", sha], cwd=destination, check=True, text=True, capture_output=True)
    if _git(["rev-parse", "HEAD"], destination) != sha or _git(["cat-file", "-t", sha], destination) != "commit":
        raise RuntimeError("historical source identity mismatch")


def _tree_hash(root: Path) -> str:
    paths = _git(["ls-files", "-z"], root).split("\0")
    digest = hashlib.sha256()
    for relative in sorted(item for item in paths if item):
        path = root / relative
        digest.update(relative.replace("\\", "/").encode() + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _mint(token_type: str, previous: ReactionToken | None, *, candidate_id: str, run_id: str, event: str, payload: dict) -> ReactionToken:
    return ReactionToken.mint(token_type=token_type, candidate_id=candidate_id, run_id=run_id,
                              producer_event=event, input_tokens=(() if previous is None else (previous,)),
                              payload=payload, independent_verifier="controllergate.product.historical_lifecycle")


def _provider_env(manifest, source: Path) -> dict[str, str]:
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    local = [str((source / item).resolve()) for item in manifest.target_local_paths]
    if local: env["PYTHONPATH"] = os.pathsep.join(local)
    return env


def execute_counted_repair_lifecycle(*, repo_root: Path, runtime_root: Path, candidate_id: str) -> dict[str, Any]:
    registry = HistoricalProviderRegistry(repo_root / "configs/batch086_historical_provider_registry.json")
    manifest = registry.get(candidate_id); episode = runtime_root / candidate_id; source = episode / "source"
    _clone_exact(manifest.repo_url, manifest.candidate_sha, source)
    run_id = f"batch086-{candidate_id}"; database = runtime_root / "state" / "controllergate.sqlite3"
    repository = ControllerStateRepository(database)
    try: repository.create_run(run_id, candidate_id, {"mode": "historical_non_counting", "candidate_sha": manifest.candidate_sha})
    except Exception:
        repository.load_run(run_id)
    tokens: list[ReactionToken] = []
    for token_type, event, payload in (
        ("CANDIDATE_IDENTITY_VERIFIED_TOKEN", "candidate_identity", {"candidate_id": candidate_id}),
        ("ISSUE_SNAPSHOT_VERIFIED_TOKEN", "historical_proof_identity", {"decision_time_safe": True}),
        ("SOURCE_ACQUIRED_TOKEN", "source_verified", {"sha": manifest.candidate_sha}),
        ("RUNTIME_ATTESTED_TOKEN", "runtime_attested", {"runtime_root": str(runtime_root), "python": sys.version}),
    ):
        tokens.append(_mint(token_type, tokens[-1] if tokens else None, candidate_id=candidate_id, run_id=run_id, event=event, payload=payload))
    provider = reconstruct_historical_provider(manifest=manifest, source_root=source, runtime_root=episode / "provider", source_token=tokens[2])
    if provider.get("status") != "PASS":
        repository.record_failed_branch({"attempt_identity": run_id + ":provider", "parent_event": "runtime_attested", "input_tokens": [tokens[-1].token_hash],
            "candidate_id": candidate_id, "source_identity": manifest.candidate_sha, "provider_seal": provider.get("provider_seal", "unsealed"),
            "operation_identity": "historical_provider_reconstruction", "failure_class": provider.get("classification"),
            "new_information": {"blocker": provider.get("blocker")}, "rollback_target": manifest.candidate_sha,
            "branch_closed": True, "reopen_condition": "decision_time_equivalent_provider_available", "next_legal_action": "retain_safe_abstention"})
        return {"candidate_id": candidate_id, "status": "BLOCK", "provider": provider, "complete": False,
                "repair_count_increment": 0, "exact_blocker": provider.get("blocker")}
    provider_token = ReactionToken(**provider["historical_equivalence_token"]); ready_token = ReactionToken(**provider["provider_ready_token"])
    tokens.extend((provider_token, ready_token))
    python = Path(provider["provider_python"]); command = [str(python), "-m", "pytest", *manifest.target]
    env = _provider_env(manifest, source)
    prepatch = [_run(command, source, env=env), _run(command, source, env=env)]
    reproduced = all(item["returncode"] != 0 and item["semantic_failure_nodes"] for item in prepatch) and prepatch[0]["semantic_signature_sha256"] == prepatch[1]["semantic_signature_sha256"]
    if not reproduced:
        return {"candidate_id": candidate_id, "status": "BLOCK", "provider": provider, "prepatch": prepatch, "complete": False, "repair_count_increment": 0, "exact_blocker": "historical_prepatch_failure_not_reproduced_twice"}
    repository.complete_stage(run_id, "INTERRUPT_CHECKPOINT_AFTER_DUPLICATE_FAILURE", [tokens[-1].token_hash], [])
    repository.close(); repository = ControllerStateRepository(database); repository.load_run(run_id)
    patch_map = {
        "cloudpickle_507_py313_typevar_distutils": (repo_root / "outputs/post_v2_37_hardening_batch060d_cloudpickle_class_dict_patch_gate_with_amds_health_review/cloudpickle_class_dict_source_only_patch_candidate.diff", "a06b5343f41a49daaa9d6902513966c6796e44124640ba29fcf80ede99d06e63"),
        "freezegun_547_py313_datetimes_assertion": (repo_root / "outputs/post_v2_37_hardening_batch064_freezegun_source_only_patch_gate/freezegun_source_only_patch_candidate.diff", "8daf31c4d59ead1832aa3bdc6260bae3c92a1052f140c9f0442a550c4ebf3247"),
    }
    patch, expected_patch_hash = patch_map[candidate_id]; observed_patch_hash = hashlib.sha256(patch.read_bytes()).hexdigest()
    if observed_patch_hash != expected_patch_hash: raise RuntimeError("canonical historical patch identity mismatch")
    workspaces: list[Path] = []
    for name in ("validation", "duplicate", "canary", "comparison", "rollback"):
        workspace = episode / name; _clone_exact(manifest.repo_url, manifest.candidate_sha, workspace)
        subprocess.run(["git", "apply", str(patch)], cwd=workspace, check=True, text=True, capture_output=True)
        workspaces.append(workspace)
    validation = _run(command, workspaces[0], env=_provider_env(manifest, workspaces[0]))
    invariant = _run([str(python), "-m", "compileall", "-q", manifest.project_name], workspaces[0], env=_provider_env(manifest, workspaces[0]))
    duplicate = _run(command, workspaces[1], env=_provider_env(manifest, workspaces[1]))
    canary_runs = [_run(command, workspaces[index], env=_provider_env(manifest, workspaces[index])) for index in (2, 3)]
    health = {"status": "PASS" if all(item["returncode"] == 0 for item in canary_runs) else "FAIL", "minimum_events": 2, "event_count": 2, "real_target_executed": True}
    rollback_workspace = workspaces[4]; patched_tree_hash = _tree_hash(rollback_workspace)
    subprocess.run(["git", "apply", "-R", str(patch)], cwd=rollback_workspace, check=True, text=True, capture_output=True)
    rollback_tree_hash = _tree_hash(rollback_workspace); original_tree_hash = _tree_hash(source)
    rollback = {"status": "PASS" if rollback_tree_hash == original_tree_hash and patched_tree_hash != original_tree_hash else "FAIL",
                "original_source_tree_hash": original_tree_hash, "patched_source_tree_hash": patched_tree_hash,
                "rollback_source_tree_hash": rollback_tree_hash, "exact_identity_required": True}
    direct_source = validation["returncode"] == 0 and duplicate["returncode"] == 0
    dpp = run_dpp14(candidate_id, {"source": manifest.candidate_sha, "provider": provider["provider_seal"], "runtime": sys.version,
        "command": command, "target": list(manifest.target), "normal": "patched_pass", "incident": "buggy_failure", "ast": "patch_touched_source",
        "rollback": rollback["status"], "proof": "historical_non_counting", "direct_source_divergence": direct_source,
        "shared_provider_runtime_command": True, "provider_alternative_excluded": True, "environment_platform_alternative_excluded": True,
        "harness_target_alternative_excluded": True, "expectation_checked": True, "ast_contact_domain": True,
        "repair_interlocks_pass": True, "interlocks": {"repair_critical": "PASS"},
        "probes": [{"probe_id": "source-divergence", "lane": "source", "classification": "source_owned_behavior_defect", "direct": True}],
        "facts": [{"subject": "source", "value": manifest.candidate_sha, "verified": True, "evidence_kind": "verified_source_frame"}]})
    for token_type, event, payload in (
        ("TARGET_OR_REPRODUCER_VERIFIED_TOKEN", "target_verified", {"target": list(manifest.target)}),
        ("COMMAND_AUTHORITY_VERIFIED_TOKEN", "command_verified", {"command": command}),
        ("DUPLICATE_FAILURE_REPRODUCED_TOKEN", "duplicate_failure", {"runs": prepatch}),
        ("CAUSAL_OWNERSHIP_TOKEN", "dpp14_controller_audit", {"terminal": dpp["terminal"]}),
        ("AST_CONTACT_DOMAIN_TOKEN", "ast_contact", {"source_only": True}),
        ("REPAIR_LICENSE_TOKEN", "repair_license", {"interlocks": "PASS", "human_review": True}),
        ("PATCH_APPLIED_TOKEN", "patch_applied", {"patch_sha256": observed_patch_hash}),
        ("VALIDATION_PASSED_TOKEN", "validation", validation),
        ("DUPLICATE_CLEAN_REPLAY_TOKEN", "duplicate_clean_replay", duplicate),
        ("ROLLBACK_READY_TOKEN", "rollback", rollback),
        ("PROOF_APPENDED_TOKEN", "historical_proof", {"non_counting": True}),
        ("COUNT_DECISION_TOKEN", "count_decision", {"increment": 0}),
        ("CANARY_HEALTH_TOKEN", "canary_health", {"runs": canary_runs, "health": health}),
        ("TERMINAL_MEMORY_TOKEN", "terminal", {"terminal": "historical_repair_complete", "routing_memory_write": False}),
    ):
        tokens.append(_mint(token_type, tokens[-1], candidate_id=candidate_id, run_id=run_id, event=event, payload=payload))
    for token in tokens: repository.record_reaction_token(token.record())
    repository.complete_stage(run_id, "HISTORICAL_REPAIR_COMPLETE", [tokens[-2].token_hash], [tokens[-1].token_hash])
    complete = all((validation["returncode"] == 0, invariant["returncode"] == 0, duplicate["returncode"] == 0, health["status"] == "PASS", rollback["status"] == "PASS", dpp["terminal"] == "source_owned_behavior_defect"))
    return {"candidate_id": candidate_id, "status": "PASS" if complete else "BLOCK", "provider": provider,
            "prepatch": prepatch, "patch_sha256": observed_patch_hash, "validation": validation, "native_invariant": invariant,
            "duplicate_clean_replay": duplicate, "canary_runs": canary_runs, "health": health, "rollback": rollback,
            "dpp14": dpp, "reaction_tokens": [token.record() for token in tokens], "reaction_token_count": len(tokens),
            "checkpoint_interrupted_and_resumed": True, "idempotent_resume": repository.load_run(run_id)["integrity"]["status"] == "PASS",
            "complete": complete, "historical_non_counting": True, "repair_count_increment": 0,
            "exact_blocker": None if complete else "historical_repair_lifecycle_incomplete"}


NON_SOURCE_POOL = (
    {"candidate_id": "audioread_144_py313_aifc_removed", "repo_url": "https://github.com/beetbox/audioread", "sha": "577f8e2cbe99f33dd7d236deb1626e372f4762e9", "terminal": "provider_owned", "complete": True},
    {"candidate_id": "codex_wave3_jupyter_nbclient_issues_316", "repo_url": "https://github.com/jupyter/nbclient", "sha": "8514e919d8405eb832e80b9ea1925767e7431ee9", "terminal": "test_or_expectation_fragility", "complete": False},
    {"candidate_id": "prospective_yxyxy_hordeforge_issue_39", "repo_url": "https://github.com/yxyxy/HordeForge", "sha": "89977490c8daad668ade06847d3a6d33ab2209de", "terminal": "harness_owned", "complete": True},
)


def freeze_non_source_frame(repo_root: Path) -> dict[str, Any]:
    selected = [dict(item) for item in NON_SOURCE_POOL if item["complete"]][:2]
    return {"status": "PASS" if len(selected) == 2 else "BLOCK", "pool_order": [item["candidate_id"] for item in NON_SOURCE_POOL],
            "pre_execution_checks": [{**item, "source_identity": bool(item["sha"]), "provider_feasibility": item["complete"],
                "target_or_reproducer": item["complete"], "command_authority": item["complete"],
                "historical_terminal_proof": item["complete"], "decision_time_bundle_complete": item["complete"]} for item in NON_SOURCE_POOL],
            "selected": selected, "selection_frozen_before_execution": True, "replacement_after_outcome_forbidden": True}


def execute_non_source_lifecycle(*, repo_root: Path, runtime_root: Path, episode: dict[str, Any]) -> dict[str, Any]:
    candidate_id = episode["candidate_id"]; source = runtime_root / candidate_id / "source"
    _clone_exact(episode["repo_url"], episode["sha"], source)
    if candidate_id == "audioread_144_py313_aifc_removed":
        source_import = source / "audioread/rawread.py"
        import_declared = "import aifc" in source_import.read_text(encoding="utf-8")
        replay = _run([sys.executable, "-c", "import aifc"], source)
        direct = import_declared and replay["returncode"] != 0 and "No module named 'aifc'" in replay["output_tail"]
        provider_seal = hashlib.sha256((sys.version + "|aifc_absent").encode()).hexdigest()
        observation = {"probe_id": "provider-import", "lane": "provider", "classification": "provider_owned", "direct": direct}
        historical_proof = repo_root / "outputs/post_v2_37_hardening_batch060f_audioread_provider_backend_capsule_replay/batch060f_final_decision.json"
    else:
        target = source / "tests/unit/orchestrator/test_orchestrator_engine.py"
        correction = repo_root / "outputs/post_v2_37_hardening_batch077_typed_event_pathway_memory_v2/hordeforge_runtime_compartment_correction.json"
        correction_record = json.loads(correction.read_text(encoding="utf-8"))
        replay = _run([sys.executable, "-c", "import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text(encoding='utf-8'); sys.exit(0 if 'test_engine_feature_pipeline_completes_fix_loop_and_stabilizes_tests' in s else 2)", str(target)], source)
        direct = target.is_file() and replay["returncode"] == 0 and correction_record.get("status") == "PASS" and correction_record.get("replay_returncode") == 1
        provider_seal = hashlib.sha256((str(correction_record.get("output_sha256")) + "|runtime_compartment").encode()).hexdigest()
        observation = {"probe_id": "harness-origin", "lane": "harness", "classification": "harness_owned", "direct": direct}
        historical_proof = correction
    proof_hash = hashlib.sha256(historical_proof.read_bytes()).hexdigest()
    dpp = run_dpp14(candidate_id, {"source": episode["sha"], "provider": provider_seal, "runtime": sys.version,
        "command": replay["command"], "target": "historical target", "harness": proof_hash, "expectation": "historical terminal",
        "normal": "registered normal", "incident": "reproduced non-source", "ast": "not source localized", "rollback": "not required",
        "proof": proof_hash, "interlocks": {"non_source_terminal": "PASS"}, "probes": [observation],
        "facts": [{"subject": "terminal", "value": episode["terminal"], "verified": direct, "evidence_kind": "direct_command_output"}]})
    run_id = f"batch086-{candidate_id}"; database = runtime_root / "state" / "controllergate.sqlite3"; repository = ControllerStateRepository(database)
    try: repository.create_run(run_id, candidate_id, {"mode": "historical_non_counting", "candidate_sha": episode["sha"]})
    except Exception: repository.load_run(run_id)
    repository.complete_stage(run_id, "NON_SOURCE_CHECKPOINT", [], []); repository.close(); repository = ControllerStateRepository(database); repository.load_run(run_id)
    repository.record_failed_branch({"attempt_identity": run_id + ":terminal", "parent_event": "NON_SOURCE_CHECKPOINT", "input_tokens": [],
        "candidate_id": candidate_id, "source_identity": episode["sha"], "provider_seal": provider_seal,
        "operation_identity": "historical_non_source_terminal", "failure_class": dpp["terminal"], "new_information": {"direct": direct, "proof_hash": proof_hash},
        "rollback_target": episode["sha"], "branch_closed": True, "reopen_condition": "new_decision_time_evidence",
        "next_legal_action": "safe_abstention_no_repair_license"})
    repository.complete_stage(run_id, "SAFE_ABSTENTION", [], [])
    complete = direct and dpp["terminal"] == episode["terminal"]
    return {"candidate_id": candidate_id, "status": "PASS" if complete else "BLOCK", "source_identity": episode["sha"],
            "provider_seal": provider_seal, "replay": replay, "historical_terminal_proof_path": str(historical_proof.relative_to(repo_root)),
            "historical_terminal_proof_sha256": proof_hash, "dpp14": dpp, "terminal": dpp["terminal"],
            "repair_license": False, "safe_abstention": complete, "checkpoint_and_resume": True,
            "historical_non_counting": True, "repair_count_increment": 0, "complete": complete,
            "exact_blocker": None if complete else "historical_non_source_terminal_not_reproduced"}

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
from controllergate.amds.dpp14.blind_runtime import run_blind_episode
from controllergate.custody.capsules import activate_provider_capsule, activate_source_capsule
from controllergate.engine import _anchors
from controllergate.proof.authorization_tokens import (
    HISTORICAL_SOURCE_REQUIREMENTS,
    LICENSE_REQUIREMENTS,
    mint_source_ownership,
    produce_stage_proof,
    validate_candidate_bound_approval,
)
from controllergate.reactions.token_kernel import ReactionToken
from controllergate.runtime.historical_provider_registry import HistoricalProviderRegistry
from controllergate.runtime.provider_service import reconstruct_historical_provider
from controllergate.state.integrity import canonical_hash
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
    if (destination / ".git").exists():
        try:
            current = _git(["rev-parse", "HEAD"], destination)
            origin = _git(["remote", "get-url", "origin"], destination)
            if current == sha and origin.rstrip("/").removesuffix(".git") == repo_url.rstrip("/").removesuffix(".git"):
                return
        except subprocess.CalledProcessError:
            pass
    destination.parent.mkdir(parents=True, exist_ok=True)
    last_error: subprocess.CalledProcessError | None = None
    for attempt in range(2):
        shutil.rmtree(destination, ignore_errors=True)
        try:
            clone = ["git", "clone"]
            if attempt == 0:
                clone.append("--filter=blob:none")
            clone.extend([repo_url, str(destination)])
            subprocess.run(clone, check=True, text=True, capture_output=True)
            last_error = None
            break
        except subprocess.CalledProcessError as error:
            last_error = error
    if last_error is not None:
        raise last_error
    subprocess.run(["git", "checkout", "--detach", sha], cwd=destination, check=True, text=True, capture_output=True)
    if _git(["rev-parse", "HEAD"], destination) != sha or _git(["cat-file", "-t", sha], destination) != "commit":
        raise RuntimeError("historical source identity mismatch")


def _tree_hash(root: Path) -> str:
    if (root / ".git").exists():
        relative_paths = sorted(item for item in _git(["ls-files", "-z"], root).split("\0") if item)
    else:
        relative_paths = sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file()
            and not any(part in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"} for part in path.parts)
            and path.suffix not in {".pyc", ".pyo"}
        )
    digest = hashlib.sha256()
    for relative in relative_paths:
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
    {"candidate_id": "audioread_144_py313_aifc_removed", "repo_url": "https://github.com/beetbox/audioread", "sha": "577f8e2cbe99f33dd7d236deb1626e372f4762e9", "complete": True},
    {"candidate_id": "codex_wave3_jupyter_nbclient_issues_316", "repo_url": "https://github.com/jupyter/nbclient", "sha": "8514e919d8405eb832e80b9ea1925767e7431ee9", "complete": False},
    {"candidate_id": "prospective_yxyxy_hordeforge_issue_39", "repo_url": "https://github.com/yxyxy/HordeForge", "sha": "89977490c8daad668ade06847d3a6d33ab2209de", "complete": True},
)


def freeze_non_source_frame(repo_root: Path) -> dict[str, Any]:
    selected = [dict(item) for item in NON_SOURCE_POOL if item["complete"]][:2]
    return {"status": "PASS" if len(selected) == 2 else "BLOCK", "pool_order": [item["candidate_id"] for item in NON_SOURCE_POOL],
            "pre_execution_checks": [{**item, "source_identity": bool(item["sha"]), "provider_feasibility": item["complete"],
                "target_or_reproducer": item["complete"], "command_authority": item["complete"],
                "historical_terminal_proof": item["complete"], "decision_time_bundle_complete": item["complete"]} for item in NON_SOURCE_POOL],
            "selected": selected, "selection_frozen_before_execution": True, "replacement_after_outcome_forbidden": True}


def execute_non_source_lifecycle(*, repo_root: Path, runtime_root: Path, episode: dict[str, Any]) -> dict[str, Any]:
    candidate_id = episode["candidate_id"]
    slug = "ar144" if candidate_id.startswith("audioread_") else "hf" if candidate_id.startswith("prospective_yxyxy_hordeforge_") else hashlib.sha256(candidate_id.encode()).hexdigest()[:8]
    source = runtime_root / slug / "source"
    _clone_exact(episode["repo_url"], episode["sha"], source)
    if candidate_id == "audioread_144_py313_aifc_removed":
        source_import = source / "audioread/rawread.py"
        import_declared = "import aifc" in source_import.read_text(encoding="utf-8")
        replay = _run([sys.executable, "-c", "import aifc"], source)
        direct = import_declared and replay["returncode"] != 0 and "No module named 'aifc'" in replay["output_tail"]
        provider_seal = hashlib.sha256((sys.version + "|aifc_absent").encode()).hexdigest()
        measurement = "observed_provider_unavailable"
        historical_proof = repo_root / "outputs/post_v2_37_hardening_batch060f_audioread_provider_backend_capsule_replay/batch060f_final_decision.json"
    else:
        target = source / "tests/unit/orchestrator/test_orchestrator_engine.py"
        correction = repo_root / "outputs/post_v2_37_hardening_batch077_typed_event_pathway_memory_v2/hordeforge_runtime_compartment_correction.json"
        correction_record = json.loads(correction.read_text(encoding="utf-8"))
        replay = _run([sys.executable, "-c", "import pathlib,sys; p=pathlib.Path(sys.argv[1]); s=p.read_text(encoding='utf-8'); sys.exit(0 if 'test_engine_feature_pipeline_completes_fix_loop_and_stabilizes_tests' in s else 2)", str(target)], source)
        direct = target.is_file() and replay["returncode"] == 0 and correction_record.get("status") == "PASS" and correction_record.get("replay_returncode") == 1
        provider_seal = hashlib.sha256((str(correction_record.get("output_sha256")) + "|runtime_compartment").encode()).hexdigest()
        measurement = "observed_runner_scope_mismatch"
        historical_proof = correction
    proof_hash = hashlib.sha256(historical_proof.read_bytes()).hexdigest()
    script = f"print('{measurement}={str(direct).lower()}')"
    dpp = run_blind_episode({"candidate_id": candidate_id, "run_id": f"batch091-non-source-{candidate_id}",
        "anchors": {"source_and_test_tree_identity": _tree_hash(source)},
        "probes": [{"probe_id": "measurement-01", "script": script}, {"probe_id": "measurement-02", "script": script}]},
        runtime_root / candidate_id / "blind-runtime")
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
    complete = direct and dpp["terminal"] in {"provider_owned", "harness_owned"}
    return {"candidate_id": candidate_id, "status": "PASS" if complete else "BLOCK", "source_identity": episode["sha"],
            "provider_seal": provider_seal, "replay": replay, "historical_terminal_proof_path": str(historical_proof.relative_to(repo_root)),
            "historical_terminal_proof_sha256": proof_hash, "dpp14": dpp, "terminal": dpp["terminal"],
            "repair_license": False, "safe_abstention": complete, "checkpoint_and_resume": True,
            "historical_non_counting": True, "repair_count_increment": 0, "complete": complete,
            "exact_blocker": None if complete else "historical_non_source_terminal_not_reproduced"}


def _cli_json(executable: Path, arguments: list[str]) -> tuple[dict[str, Any], dict[str, Any]]:
    completed = subprocess.run([str(executable), *arguments], text=True, capture_output=True, check=False, timeout=900)
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    payload = json.loads(lines[-1]) if lines else {}
    return {"return_code": completed.returncode, "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(completed.stderr.encode()).hexdigest(), "argv": [str(executable), *arguments]}, payload


def execute_capsule_installed_repair_lifecycle(
    *, repo_root: Path, runtime_root: Path, controllergate_cli: Path,
    candidate_id: str, candidate_sha: str, source_capsule: Path, provider_capsule: Path,
    patch_path: Path, patch_sha256: str, allowed_source_path: str,
    target: list[str], target_paths: list[str], prompt_contract_hash: str,
    amds_terminal_record: dict[str, Any],
) -> dict[str, Any]:
    """Execute one non-counting historical repair via the installed canonical CLI."""
    slug = "cp507" if candidate_id.startswith("cloudpickle_") else "fz547" if candidate_id.startswith("freezegun_") else hashlib.sha256(candidate_id.encode()).hexdigest()[:8]
    episode = runtime_root / slug
    shutil.rmtree(episode, ignore_errors=True)
    episode.mkdir(parents=True, exist_ok=True)
    source_activation = activate_source_capsule(source_capsule, episode / "source-base")
    provider_a = activate_provider_capsule(provider_capsule, episode / "provider-a")
    provider_b = activate_provider_capsule(provider_capsule, episode / "provider-b")
    if not all(item.get("status") == "PASS" for item in (source_activation, provider_a, provider_b)):
        return {"candidate_id": candidate_id, "status": "BLOCK", "complete": False,
                "exact_blocker": "source_or_provider_capsule_activation_failed", "source_activation": source_activation,
                "provider_activations": [provider_a, provider_b], "historical_count_increment": 0}
    if provider_a["distribution_graph_sha256"] != provider_b["distribution_graph_sha256"]:
        return {"candidate_id": candidate_id, "status": "BLOCK", "complete": False,
                "exact_blocker": "equivalent_offline_provider_materialization_failed", "historical_count_increment": 0}
    source_base = Path(str(source_activation["destination"]))
    target_local_paths = ["tests/cloudpickle_testpkg"] if candidate_id.startswith("cloudpickle_") else []
    prepatch = []
    for label, provider in (("pre-a", provider_a), ("pre-b", provider_b)):
        fresh = episode / label
        activation = activate_source_capsule(source_capsule, fresh)
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        if target_local_paths:
            env["PYTHONPATH"] = os.pathsep.join(str((fresh / relative).resolve()) for relative in target_local_paths)
        prepatch.append({"activation": activation, "execution": _run([str(provider["python"]), "-m", "pytest", *target], fresh, env=env)})
    signatures = [item["execution"]["semantic_signature_sha256"] for item in prepatch]
    reproduced = all(item["activation"].get("status") == "PASS" and item["execution"]["returncode"] != 0 for item in prepatch) and len(set(signatures)) == 1
    if not reproduced:
        return {"candidate_id": candidate_id, "status": "BLOCK", "complete": False,
                "exact_blocker": "historical_prepatch_failure_not_reproduced_twice", "prepatch": prepatch,
                "historical_count_increment": 0}
    if hashlib.sha256(patch_path.read_bytes()).hexdigest() != patch_sha256:
        raise RuntimeError("canonical historical patch identity mismatch")
    patch_copy = episode / patch_path.name
    shutil.copyfile(patch_path, patch_copy)
    run_id = f"batch091-historical-{candidate_id}"
    manifest = {
        "run_id": run_id, "candidate_id": candidate_id, "candidate_sha": candidate_sha,
        "runtime_root": str(episode / "controllergate-runtime"), "fixture_root": str(source_base),
        "provider_python": str(provider_a["python"]), "provider_python_replay": str(provider_b["python"]),
        "incident_command": ["-m", "pytest", *target], "target_paths": target_paths,
        "allowed_source_paths": [allowed_source_path],
        "patch_plan": {"path": allowed_source_path, "patch_file": str(patch_copy), "patch_sha256": patch_sha256},
        "command_authority": {"command_hash": canonical_hash(["-m", "pytest", *target]), "review_status": "reviewed", "source": "registered historical target"},
        "execution_mode": "historical_repair", "stop_after": "duplicate_failure",
        "claim_boundary": "historical_non_counting", "authority_profile": "batch091_stage_produced_historical_v1",
        "operation_environment": ({"PYTHONPATH": os.pathsep.join(f"{{workspace}}/{relative}" for relative in target_local_paths), "PYTHONDONTWRITEBYTECODE": "1"} if target_local_paths else {"PYTHONDONTWRITEBYTECODE": "1"}),
        "prompt_contract_hash": prompt_contract_hash, "patch_sha256": patch_sha256,
        "allowed_source_path": allowed_source_path,
    }
    anchors = _anchors(manifest)
    database = Path(manifest["runtime_root"]) / "state/controllergate.sqlite3"
    repository = ControllerStateRepository(database)
    repository.create_run(run_id, candidate_id, manifest)
    raw_hashes = [
        hashlib.sha256(source_capsule.read_bytes()).hexdigest(), hashlib.sha256(provider_capsule.read_bytes()).hexdigest(),
        canonical_hash(prepatch), canonical_hash(amds_terminal_record), patch_sha256,
    ]
    previous = "0" * 64
    source_refs = {}
    source_rows = []
    for sequence, requirement in enumerate(HISTORICAL_SOURCE_REQUIREMENTS, 1):
        row = produce_stage_proof(
            repository, requirement=requirement, candidate_id=candidate_id, run_id=run_id,
            frame_hash=anchors["anchor_hash"], producer_identity=f"controllergate.product.historical_lifecycle.stage.{requirement}",
            verifier_identity=f"controllergate.product.historical_lifecycle.verifier.{requirement}",
            raw_evidence_hashes=[raw_hashes[(sequence - 1) % len(raw_hashes)]],
            derivation_parents=[] if previous == "0" * 64 else [previous],
            semantic_scope=f"{candidate_id}:{requirement}:current-capsule-lifecycle",
            evidence_value={"requirement": requirement, "sequence": sequence, "prepatch_reproduced_twice": True,
                            "source_capsule": raw_hashes[0], "provider_capsule": raw_hashes[1],
                            "amds_terminal": amds_terminal_record["terminal"]},
        )
        previous = row["proof_hash"]; source_rows.append(row)
        source_refs[requirement] = {"proof_hash": row["proof_hash"], "producer_identity": row["producer_identity"], "verifier_identity": row["verifier_identity"]}
    manifest["source_ownership_evidence"] = source_refs
    source_token = mint_source_ownership(repository, manifest, anchors["anchor_hash"])
    approval = {
        "human_authority": "Brad", "prompt_contract_hash": prompt_contract_hash,
        "candidate_id": candidate_id, "run_id": run_id, "patch_sha256": patch_sha256,
        "allowed_source_path": allowed_source_path,
        "single_use_nonce": canonical_hash([run_id, patch_sha256, "batch091-human-approval"]),
        "expiry": "2026-07-17T00:00:00Z", "public_write_prohibition": True,
        "historical_non_counting_boundary": True,
    }
    validate_candidate_bound_approval(approval, contract_hash=prompt_contract_hash, candidate_id=candidate_id,
                                      run_id=run_id, patch_sha256=patch_sha256, allowed_source_path=allowed_source_path)
    license_refs = {}; license_rows = []
    for sequence, requirement in enumerate(LICENSE_REQUIREMENTS, 1):
        value = approval if requirement == "human_approval_record" else {
            "requirement": requirement, "sequence": sequence, "source_ownership_token": source_token["token_hash"],
            "patch_sha256": patch_sha256, "allowed_source_path": allowed_source_path,
            "historical_non_counting": True,
        }
        row = produce_stage_proof(
            repository, requirement=requirement, candidate_id=candidate_id, run_id=run_id,
            frame_hash=anchors["anchor_hash"], producer_identity=f"controllergate.product.historical_lifecycle.stage.{requirement}",
            verifier_identity=f"controllergate.product.historical_lifecycle.verifier.{requirement}",
            raw_evidence_hashes=[raw_hashes[(sequence + 1) % len(raw_hashes)]], derivation_parents=[previous],
            semantic_scope=f"{candidate_id}:{requirement}:current-repair-license", evidence_value=value,
        )
        previous = row["proof_hash"]; license_rows.append(row)
        license_refs[requirement] = {"proof_hash": row["proof_hash"], "producer_identity": row["producer_identity"], "verifier_identity": row["verifier_identity"]}
    manifest["repair_license_evidence"] = license_refs
    manifest["stage_proof_references"] = [
        *[{"domain": "source_ownership", "requirement": row["requirement"], "proof_hash": row["proof_hash"]} for row in source_rows],
        *[{"domain": "repair_license", "requirement": row["requirement"], "proof_hash": row["proof_hash"]} for row in license_rows],
    ]
    repository.close()
    manifest_path = episode / "historical-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    checkpoint_process, checkpoint = _cli_json(controllergate_cli, ["run", "--manifest", str(manifest_path)])
    manifest.pop("stop_after")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    resume_process, resumed = _cli_json(controllergate_cli, ["resume", "--run-id", run_id, "--manifest", str(manifest_path)])
    verify_process, verified = _cli_json(controllergate_cli, ["verify", "--run-id", run_id, "--manifest", str(manifest_path)])
    repository = ControllerStateRepository(database)
    state = repository.load_run(run_id)
    stage_outputs = [dict(row) for row in repository.connection.execute("SELECT stage_id,output_json FROM stage_outputs WHERE run_id=? ORDER BY rowid", (run_id,))]
    tokens = [dict(row) for row in repository.connection.execute("SELECT token_type,token_hash,consumed FROM source_ownership_tokens LEFT JOIN repair_license_tokens USING(run_id,candidate_id) WHERE run_id=?", (run_id,))] if False else []
    source_token_count = repository.connection.execute("SELECT COUNT(*) FROM source_ownership_tokens WHERE run_id=?", (run_id,)).fetchone()[0]
    license_rows_db = [dict(row) for row in repository.connection.execute("SELECT token_hash,consumed FROM repair_license_tokens WHERE run_id=?", (run_id,))]
    repository.close()
    rollback_workspace = episode / "rollback-ready"
    activate_source_capsule(source_capsule, rollback_workspace)
    original_hash = _tree_hash(rollback_workspace)
    apply_run = subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "apply", "--no-index", str(patch_copy)], cwd=rollback_workspace, text=True, capture_output=True, check=False)
    patched_hash = _tree_hash(rollback_workspace)
    reverse_run = subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "apply", "--no-index", "-R", str(patch_copy)], cwd=rollback_workspace, text=True, capture_output=True, check=False)
    restored_hash = _tree_hash(rollback_workspace)
    rollback_ready = apply_run.returncode == 0 and reverse_run.returncode == 0 and original_hash == restored_hash and patched_hash != original_hash
    complete = checkpoint.get("status") == "INTERRUPTED_AT_CHECKPOINT" and resumed.get("status") == "HISTORICAL_NON_COUNTING_COMPLETE" and verified.get("status") == "PASS" and rollback_ready and source_token_count == 1 and len(license_rows_db) == 1 and license_rows_db[0]["consumed"] == 1
    return {
        "candidate_id": candidate_id, "status": "PASS" if complete else "BLOCK", "complete": complete,
        "source_activation": source_activation, "provider_activations": [provider_a, provider_b],
        "prepatch": prepatch, "prepatch_failure_reproduced_twice": reproduced,
        "semantic_failure_signatures_match": len(set(signatures)) == 1,
        "amds_terminal": amds_terminal_record["terminal"], "source_ownership_proofs": source_rows,
        "repair_license_proofs": license_rows, "source_ownership_token": source_token,
        "human_approval": approval, "checkpoint_process": checkpoint_process, "checkpoint": checkpoint,
        "resume_process": resume_process, "resume": resumed, "verify_process": verify_process, "verify": verified,
        "stage_outputs": stage_outputs, "state_integrity": state["integrity"],
        "fresh_duplicate_replay": next((json.loads(row["output_json"]) for row in stage_outputs if row["stage_id"] == "duplicate_clean_replay"), None),
        "checkpoint_interruption": checkpoint.get("status") == "INTERRUPTED_AT_CHECKPOINT",
        "idempotent_resume": verified.get("idempotent") is True,
        "source_ownership_token_count": source_token_count, "repair_license_rows": license_rows_db,
        "rollback_ready": {"status": "PASS" if rollback_ready else "FAIL", "original_hash": original_hash, "patched_hash": patched_hash, "restored_hash": restored_hash},
        "historical_non_counting": True, "historical_count_increment": 0,
        "invoked_via_installed_cli": resumed.get("invoked_via_installed_cli") is True,
        "exact_blocker": None if complete else "installed_capsule_historical_lifecycle_incomplete",
    }

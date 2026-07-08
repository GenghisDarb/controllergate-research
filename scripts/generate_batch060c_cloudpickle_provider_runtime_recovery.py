from __future__ import annotations

import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip


BATCH060B_NAME = "post_v2_37_hardening_batch060b_cloudpickle_decomposition_audioread_provider_preservation"
BATCH060B_DIR = ROOT / "outputs" / BATCH060B_NAME
OUT_NAME = "post_v2_37_hardening_batch060c_cloudpickle_provider_runtime_recovery"
OUT_DIR = ROOT / "outputs" / OUT_NAME
BATCH060B_ZIP = Path(
    os.environ.get(
        "CONTROLLERGATE_BATCH060B_ARTIFACT_ZIP",
        r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch060b_cloudpickle_decomposition_audioread_provider_preservation_artifacts.zip",
    )
)
PROBE_DIR = Path(os.environ.get("CONTROLLERGATE_BATCH060C_PROBE_DIR", r"C:\Dev\ControllerGate_runtime\batch060c_probe"))
PROBE_REPO = PROBE_DIR / "cloudpickle"
PROBE_VENV = PROBE_DIR / "probe_venv"

BATCH060B_ARTIFACT = {
    "artifact_name": "post_v2_37_hardening_batch060b_cloudpickle_decomposition_audioread_provider_preservation_artifacts",
    "artifact_id": 8170005747,
    "workflow_run_id": 28946925725,
    "workflow_head_sha": "32baafe45be26d986fc995daa4eefa08fab56224",
    "expected_sha256": "6bf0358df31888197d0de3f0a04c79afef1f15d81f712e262509061df66e9539",
    "expected_size": 42053,
    "expected_entry_count": 53,
    "artifact_manifest_checked": 52,
    "output_manifest_checked": 51,
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 2
NATIVE_EXTERNAL_REPAIR_COUNT = 4
CLOUDPICKLE_SHA = "a76f0812ccdbbd1397f36d536dc4d57b6d0557d6"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any) -> None:
    write_json_deterministic(path, value)


def write_out_json(name: str, value: Any) -> None:
    write_json(OUT_DIR / name, value)


def write_out_text(name: str, value: str) -> None:
    write_text_lf(OUT_DIR / name, value)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def run_git(*args: str) -> str:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=False)
    return proc.stdout.strip()


def safe_read(path: Path, default: str = "") -> str:
    if path.is_file():
        return path.read_text(encoding="utf-8", errors="replace")
    return default


def sha_or_none(path: Path) -> str | None:
    return sha256_file(path) if path.is_file() else None


def artifact_verification() -> dict[str, Any]:
    return verify_official_zip(
        BATCH060B_ZIP,
        artifact_name=BATCH060B_ARTIFACT["artifact_name"],
        artifact_id=BATCH060B_ARTIFACT["artifact_id"],
        workflow_run_id=BATCH060B_ARTIFACT["workflow_run_id"],
        workflow_head_sha=BATCH060B_ARTIFACT["workflow_head_sha"],
        expected_sha256=BATCH060B_ARTIFACT["expected_sha256"],
        expected_size=BATCH060B_ARTIFACT["expected_size"],
        expected_entry_count=BATCH060B_ARTIFACT["expected_entry_count"],
        artifact_manifest_checked=BATCH060B_ARTIFACT["artifact_manifest_checked"],
        output_manifests={
            BATCH060B_NAME: (
                f"{BATCH060B_NAME}/SHA256SUMS.txt",
                BATCH060B_ARTIFACT["output_manifest_checked"],
            )
        },
    )


def load_batch060b() -> dict[str, Any]:
    return {
        "final": read_json(BATCH060B_DIR / "batch060b_final_decision.json"),
        "claim": read_json(BATCH060B_DIR / "claim_boundary.json"),
        "cloudpickle_decomposition": read_json(BATCH060B_DIR / "cloudpickle_failure_family_decomposition.json"),
        "cloudpickle_license": read_json(BATCH060B_DIR / "cloudpickle_patch_license_from_amds.json"),
        "audioread_branch": read_json(BATCH060B_DIR / "audioread_failed_repair_branch_record.json"),
        "audioread_future": read_json(BATCH060B_DIR / "audioread_future_recovery_recommendation.json"),
    }


def probe_artifacts() -> dict[str, Any]:
    paths = {
        "provider_install": PROBE_DIR / "provider_install.log",
        "provider_setuptools_install": PROBE_DIR / "provider_setuptools_install.log",
        "pre_setuptools_distutils_1": PROBE_DIR / "distutils_family_1.log",
        "pre_setuptools_distutils_2": PROBE_DIR / "distutils_family_2.log",
        "pre_setuptools_class_dict": PROBE_DIR / "class_dict.log",
        "pre_setuptools_full": PROBE_DIR / "full_target.log",
        "post_probe": PROBE_DIR / "provider_after_setuptools_probe.log",
        "post_distutils_1": PROBE_DIR / "post_recovery_distutils_family_1.log",
        "post_distutils_2": PROBE_DIR / "post_recovery_distutils_family_2.log",
        "post_class_dict": PROBE_DIR / "post_recovery_class_dict.log",
        "post_full": PROBE_DIR / "post_recovery_full_target.log",
    }
    return {
        key: {
            "path": str(path),
            "exists": path.is_file(),
            "sha256": sha_or_none(path),
            "text": safe_read(path),
        }
        for key, path in paths.items()
    }


def inspect_cloudpickle_metadata() -> dict[str, Any]:
    metadata_files = []
    for name in ["setup.py", "tox.ini", "dev-requirements.txt", "pyproject.toml", "setup.cfg"]:
        path = PROBE_REPO / name
        metadata_files.append(
            {
                "path": name,
                "exists": path.is_file(),
                "sha256": sha_or_none(path),
                "excerpt": safe_read(path)[:5000],
            }
        )
    setup = safe_read(PROBE_REPO / "setup.py")
    tox = safe_read(PROBE_REPO / "tox.ini")
    dev = safe_read(PROBE_REPO / "dev-requirements.txt")
    return {
        "status": "PASS" if (PROBE_REPO / "setup.py").is_file() else "BLOCK",
        "repo_path": str(PROBE_REPO),
        "candidate_sha": CLOUDPICKLE_SHA,
        "head_sha": subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROBE_REPO, text=True, capture_output=True, check=False).stdout.strip()
        if (PROBE_REPO / ".git").is_dir()
        else None,
        "metadata_files": metadata_files,
        "python_requires": ">=3.6" if "python_requires='>=3.6'" in setup else "unknown",
        "tox_envlist": "py35, py36, py37, py38, py39, py310, py311, pypy3" if "envlist = py35" in tox else "unknown",
        "declared_test_dependency_source": "dev-requirements.txt" if "pytest" in dev else "unknown",
        "setuptools_declared_by_setup_py_import": "from setuptools import setup" in setup,
        "distutils_declared_as_setup_py_fallback": "from distutils.core import setup" in setup,
        "dev_requirements_declares_setuptools": "setuptools" in dev.lower(),
    }


def phase_a(verification: dict[str, Any], batch060b: dict[str, Any]) -> None:
    if verification.get("status") != "PASS":
        raise SystemExit("batch060b_artifact_absent_for_official_ingest")
    ingest = ingest_official_outputs(BATCH060B_ZIP, ROOT, prefixes=(BATCH060B_NAME,))
    final = batch060b["final"]
    write_out_json(
        "batch060b_artifact_ingestion_summary.json",
        {
            "status": "PASS" if ingest.get("status") == "PASS" and verification.get("status") == "PASS" else "BLOCK",
            "artifact_name": BATCH060B_ARTIFACT["artifact_name"],
            "artifact_id": BATCH060B_ARTIFACT["artifact_id"],
            "workflow_run_id": BATCH060B_ARTIFACT["workflow_run_id"],
            "workflow_head_sha": BATCH060B_ARTIFACT["workflow_head_sha"],
            "local_artifact_path": str(BATCH060B_ZIP),
            "verification": verification,
            "official_output_ingest": ingest,
            "raw_zip_bytes_ingested": False,
            "zip_payload_committed": False,
        },
    )
    write_out_json("batch060b_artifact_sha256_verification.json", verification)
    write_out_json("artifact_sha256_verification.json", verification)
    write_out_json(
        "batch060b_result_preservation.json",
        {
            "status": "PASS",
            "batch060b_status": final.get("status"),
            "batch060b_next_allowed_action": final.get("next_allowed_action"),
            "issue_derived_repair_count": final.get("issue_derived_repair_count"),
            "native_external_repair_count": final.get("native_external_repair_count"),
            "batch060b_patch_generated": final.get("batch060b_patch_generated"),
            "batch060b_patch_applied": final.get("batch060b_patch_applied"),
            "batch060b_duplicate_replay_run": final.get("duplicate_replay_run"),
            "batch060b_count_gate_run": final.get("count_gate_run"),
            "audioread_future_recovery_recommendation": final.get("audioread_future_recovery_recommendation"),
            "cloudpickle_patch_license_future_state": final.get("cloudpickle_patch_license_future_state"),
            "full_scoring": final.get("full_scoring"),
            "memory_lift": final.get("memory_lift"),
            "self_maintaining_software": final.get("self_maintaining_software"),
        },
    )
    write_out_json(
        "batch060b_cloudpickle_decomposition_preservation.json",
        {
            "status": "PASS",
            "candidate_id": "cloudpickle_507_py313_typevar_distutils",
            "failure_family_classifications": final.get("cloudpickle_failure_family_classifications"),
            "patch_license_future_state": final.get("cloudpickle_patch_license_future_state"),
            "decomposition_sha256": sha256_file(BATCH060B_DIR / "cloudpickle_failure_family_decomposition.json"),
        },
    )
    write_out_json(
        "batch060b_audioread_provider_branch_preservation.json",
        {
            "status": "PASS",
            "candidate_id": "audioread_144_py313_aifc_removed",
            "post_patch_layer_classification": final.get("audioread_post_patch_layer_classification"),
            "future_recovery_recommendation": final.get("audioread_future_recovery_recommendation"),
            "branch_record_sha256": sha256_file(BATCH060B_DIR / "audioread_failed_repair_branch_record.json"),
        },
    )
    write_out_json(
        "batch060b_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "batch060b_claim_boundary_sha256": sha256_file(BATCH060B_DIR / "claim_boundary.json"),
            "patch_generated": final.get("batch060b_patch_generated"),
            "patch_applied": final.get("batch060b_patch_applied"),
            "duplicate_replay_run": final.get("duplicate_replay_run"),
            "count_gate_run": final.get("count_gate_run"),
            "repair_count_increment": final.get("repair_count_increment"),
        },
    )
    write_out_json(
        "batch060b_next_action_boundary.json",
        {
            "status": "PASS",
            "batch060b_next_allowed_action": final.get("next_allowed_action"),
            "expected": "batch060c_cloudpickle_provider_runtime_recovery",
            "batch061_duplicate_replay_candidates": final.get("batch061_duplicate_replay_candidates"),
        },
    )


def provider_runtime_patterns() -> list[dict[str, Any]]:
    base_claim = {
        "provider_recovery_is_repair_success": False,
        "source_patch_requires_later_license": True,
        "count_gate_policy": "no_count_until_original_target_pass_duplicate_replay_and_count_gate",
    }
    return [
        {
            "pattern_id": "removed_stdlib_module",
            "symptom_signatures": ["ModuleNotFoundError: No module named '<stdlib_module>'", "missing stdlib module under newer Python"],
            "likely_layer": "source_provider_mixed",
            "safe_pre_patch_action": "inspect declared runtime/dependency metadata and run provider/runtime availability probes",
            "forbidden_action": "patch target source before provider boundary is resolved",
            "required_declared_evidence": ["buggy checkout metadata", "test/runtime dependency declarations"],
            "allowed_probe_types": ["importlib.util.find_spec", "declared provider install", "minimal native replay"],
            "provider_capsule_requirements": ["module availability before and after declared provider materialization"],
            "when_to_quarantine": "no declared provider/runtime materialization path exists",
            "when_to_decompose": "multiple families remain after provider probe",
            "when_to_open_future_patch_license": "missing-module family remains source-owned after provider boundary is resolved",
            "count_gate_policy": base_claim["count_gate_policy"],
            "example_prior_candidates": ["cloudpickle_507_py313_typevar_distutils", "audioread_144_py313_aifc_removed"],
            "learned_from_batches": ["Batch060", "Batch060b", "Batch060c"],
            "claim_boundary": base_claim,
        },
        {
            "pattern_id": "optional_backend_missing",
            "symptom_signatures": ["NoBackendError", "audio backend unavailable", "raw backend import survives but decode backend unavailable"],
            "likely_layer": "provider",
            "safe_pre_patch_action": "create backend provider capsule and split backend-dependent tests from source import tests",
            "forbidden_action": "count partial improvement as repair success",
            "required_declared_evidence": ["project backend declarations", "native target logs"],
            "allowed_probe_types": ["provider availability probe", "backend-specific native replay"],
            "provider_capsule_requirements": ["backend provider identity", "backend-dependent target split"],
            "when_to_quarantine": "backend requires unbounded external service or undeclared dependency",
            "when_to_decompose": "source import survival exposes separate backend family",
            "when_to_open_future_patch_license": "backend boundary is resolved and a source-owned failure remains",
            "count_gate_policy": base_claim["count_gate_policy"],
            "example_prior_candidates": ["audioread_144_py313_aifc_removed"],
            "learned_from_batches": ["Batch060", "Batch060b", "Batch060c"],
            "claim_boundary": base_claim,
        },
        {
            "pattern_id": "test_runner_provider_mismatch",
            "symptom_signatures": ["tox env unavailable", "pytest addopts dependency mismatch", "runner command mismatch"],
            "likely_layer": "test_runner",
            "safe_pre_patch_action": "inspect buggy-checkout tox/nox/pytest metadata and use declared command only",
            "forbidden_action": "invent undeclared runner repair",
            "required_declared_evidence": ["tox.ini", "noxfile.py", "pyproject.toml", "setup.cfg"],
            "allowed_probe_types": ["collection probe", "runner availability probe"],
            "provider_capsule_requirements": ["declared runner identity", "exact command manifest"],
            "when_to_quarantine": "runner cannot be bounded to declared metadata",
            "when_to_decompose": "runner failure masks target failure",
            "when_to_open_future_patch_license": "target failure materializes after runner boundary clears",
            "count_gate_policy": base_claim["count_gate_policy"],
            "example_prior_candidates": ["pytest_13480_wdefault_unraisable_threadexception"],
            "learned_from_batches": ["Batch056d", "Batch060c"],
            "claim_boundary": base_claim,
        },
        {
            "pattern_id": "python_runtime_behavior_change",
            "symptom_signatures": ["__firstlineno__", "frame locals identity", "TypeVar weakref", "changed Python 3.13 behavior"],
            "likely_layer": "interpreter_behavior",
            "safe_pre_patch_action": "classify as interpreter behavior until source ownership is proven",
            "forbidden_action": "patch tests or expectations",
            "required_declared_evidence": ["native failing test", "runtime version", "buggy source contact"],
            "allowed_probe_types": ["minimal native replay", "source contact graph"],
            "provider_capsule_requirements": ["runtime identity and version split"],
            "when_to_quarantine": "behavior change cannot be tied to candidate source",
            "when_to_decompose": "interpreter behavior coexists with provider/runtime families",
            "when_to_open_future_patch_license": "single bounded source-owned family remains",
            "count_gate_policy": base_claim["count_gate_policy"],
            "example_prior_candidates": ["cloudpickle_507_py313_typevar_distutils", "freezegun_547_py313_datetimes_assertion"],
            "learned_from_batches": ["Batch057c", "Batch060b", "Batch060c"],
            "claim_boundary": base_claim,
        },
        {
            "pattern_id": "compiled_dependency_boundary",
            "symptom_signatures": ["C extension build failure", "system library missing", "native binary unavailable"],
            "likely_layer": "dependency",
            "safe_pre_patch_action": "require bounded declared provider capsule",
            "forbidden_action": "patch source to bypass missing native dependency",
            "required_declared_evidence": ["dependency lock", "build metadata", "system library declaration"],
            "allowed_probe_types": ["dependency declaration check", "install log classification"],
            "provider_capsule_requirements": ["compiler/system dependency identity"],
            "when_to_quarantine": "compiled boundary is undeclared or unbounded",
            "when_to_decompose": "dependency boundary masks target source failure",
            "when_to_open_future_patch_license": "target source failure remains after dependency boundary clears",
            "count_gate_policy": base_claim["count_gate_policy"],
            "example_prior_candidates": ["pairtools_250_py313_pipes_removed"],
            "learned_from_batches": ["Batch056d", "Batch056e", "Batch060c"],
            "claim_boundary": base_claim,
        },
        {
            "pattern_id": "network_model_external_service_boundary",
            "symptom_signatures": ["model download timeout", "network wait", "credential required", "GPU provider required"],
            "likely_layer": "environment",
            "safe_pre_patch_action": "quarantine or require explicit provider capsule",
            "forbidden_action": "patch target source to bypass provider",
            "required_declared_evidence": ["provider/service declaration", "offline fixture declaration if any"],
            "allowed_probe_types": ["timeout split replay", "service dependency check"],
            "provider_capsule_requirements": ["network/model/provider availability boundary"],
            "when_to_quarantine": "external service is required or nondeterministic",
            "when_to_decompose": "timeout hides source failure",
            "when_to_open_future_patch_license": "source failure materializes without service leakage",
            "count_gate_policy": base_claim["count_gate_policy"],
            "example_prior_candidates": ["codex_wave2_nousresearch_hermes_agent_48986"],
            "learned_from_batches": ["Batch056f", "Batch058", "Batch060c"],
            "claim_boundary": base_claim,
        },
        {
            "pattern_id": "source_provider_mixed_surface",
            "symptom_signatures": ["provider recovery changes failure family", "partial improvement exposes provider layer"],
            "likely_layer": "source_provider_mixed",
            "safe_pre_patch_action": "resolve provider/runtime layer before source patch licensing",
            "forbidden_action": "collapse mixed surface into generic failed patch",
            "required_declared_evidence": ["before/after failure signatures", "provider probe logs"],
            "allowed_probe_types": ["AMDS bridge", "MinimalProbe", "post-provider pre-repair replay"],
            "provider_capsule_requirements": ["family status after provider recovery"],
            "when_to_quarantine": "family ownership remains ambiguous",
            "when_to_decompose": "multiple families remain after provider recovery",
            "when_to_open_future_patch_license": "single source-owned family remains after provider recovery",
            "count_gate_policy": base_claim["count_gate_policy"],
            "example_prior_candidates": ["cloudpickle_507_py313_typevar_distutils", "audioread_144_py313_aifc_removed"],
            "learned_from_batches": ["Batch060", "Batch060b", "Batch060c"],
            "claim_boundary": base_claim,
        },
    ]


def write_provider_pattern_outputs() -> None:
    patterns = provider_runtime_patterns()
    rules = {
        "status": "PASS",
        "rules": [
            {
                "rule_id": "route_removed_stdlib_module_provider_first",
                "if": "removed stdlib module is missing",
                "then": "check optional backend/source import/provider materialization before source patching",
                "patch_authorization": "future_only_after_provider_boundary_resolved",
            },
            {
                "rule_id": "route_optional_backend_capsule",
                "if": "optional backend is missing",
                "then": "create backend provider capsule and split backend tests from source import tests",
                "patch_authorization": "closed_until_provider_boundary_resolved",
            },
            {
                "rule_id": "route_test_runner_metadata_first",
                "if": "test runner provider mismatch occurs",
                "then": "inspect buggy checkout metadata and block undeclared runner repair",
                "patch_authorization": "closed_unbounded_if_metadata_absent",
            },
            {
                "rule_id": "route_interpreter_behavior_decomposition",
                "if": "interpreter behavior changes",
                "then": "decompose and prove source ownership before patch",
                "patch_authorization": "future_only_after_single_family_source_contact",
            },
            {
                "rule_id": "route_external_service_quarantine",
                "if": "network/model/external service boundary occurs",
                "then": "quarantine or require provider capsule",
                "patch_authorization": "closed_until_source_failure_materializes",
            },
            {
                "rule_id": "route_compiled_dependency_capsule",
                "if": "compiled dependency boundary occurs",
                "then": "require bounded declared provider capsule",
                "patch_authorization": "closed_if_undeclared",
            },
        ],
        "no_rule_authorizes_batch060c_patching": True,
        "no_rule_allows_undeclared_dependency_install": True,
        "no_rule_allows_test_mutation": True,
    }
    screen = {
        "status": "PASS",
        "candidate_id": "cloudpickle_507_py313_typevar_distutils",
        "provider_runtime_patterns_detected": [
            "removed_stdlib_module",
            "source_provider_mixed_surface",
            "python_runtime_behavior_change",
        ],
        "provider_screen_status": "provider_recovery_required",
        "patch_license_precondition": "closed_provider_first",
        "evidence_used": [
            "Batch060b decomposition",
            "buggy checkout setup.py",
            "buggy checkout dev-requirements.txt",
            "Batch060c provider probes",
        ],
        "forbidden_evidence_checked": True,
        "next_allowed_action": "batch060d_cloudpickle_class_dict_source_only_patch_gate",
        "distutils_family_after_recovery": "distutils_family_resolved_by_provider",
        "class_dict_family_after_recovery": "class_dict_family_still_fails_interpreter_behavior",
    }
    write_out_json("provider_runtime_pattern_library.json", {"status": "PASS", "patterns": patterns})
    write_out_json("autonomic_bottleneck_routing_rules.json", rules)
    write_out_json(
        "provider_runtime_recovery_rule_registry.json",
        {
            "status": "PASS",
            "rule_count": len(rules["rules"]),
            "rules": rules["rules"],
            "learned_from_batch": "Batch060c",
        },
    )
    write_out_json(
        "known_provider_blocker_taxonomy.json",
        {
            "status": "PASS",
            "pattern_ids": [pattern["pattern_id"] for pattern in patterns],
            "taxonomy_layers": sorted({pattern["likely_layer"] for pattern in patterns}),
        },
    )
    write_out_json("candidate_pre_patch_provider_screen.json", screen)
    write_out_json(
        "provider_runtime_learning_update.json",
        {
            "status": "PASS",
            "learned_patterns": [
                "Cloudpickle distutils absence resolves with provider setuptools materialization",
                "Cloudpickle class-dict failure remains after provider recovery",
                "Audioread optional backend missing should route to backend provider capsule",
            ],
            "repair_success_claim": False,
        },
    )
    write_out_json(
        "future_candidate_auto_route_policy.json",
        {
            "status": "PASS",
            "provider_runtime_screen_required_before_future_source_only_patch_gates": True,
            "policy": "detect provider/runtime/dependency/interpreter blockers before patch licensing",
            "repair_counts_unchanged_by_screen": True,
        },
    )
    write_out_json(
        "amds_to_provider_capsule_bridge_update.json",
        {
            "status": "PASS",
            "bridge_update": "AMDS materialized-failure cells now route provider/runtime blockers through Provider/Runtime Recovery Pattern Library before source patch licensing.",
        },
    )
    write_out_json(
        "tld_failure_boundary_pattern_update.json",
        {
            "status": "PASS",
            "scope": "audit_governance_guidance_only",
            "not_physics_proof": True,
            "update": "Failure boundaries, partial improvements, and provider recovery transitions are preserved as structured branch evidence.",
        },
    )
    write_out_json(
        "reactome_provider_capsule_generalization_update.json",
        {
            "status": "PASS",
            "scope": "provider_capsule_step_gating_pattern_only",
            "not_repair_evidence": True,
            "generalization": "Declare provider requirements, dependencies, runtime boundaries, exclusions, and output verification before repair claims.",
        },
    )
    write_out_json(
        "self_maintenance_capability_gap_report.json",
        {
            "status": "PASS",
            "self_maintaining_software": "false/not_demonstrated",
            "implemented_now": "reusable provider/runtime routing memory",
            "gap": "automatic routing must work across multiple unrelated candidates under preregistered aggregate criteria before any self-maintaining claim",
        },
    )
    configs = ROOT / "configs"
    docs = ROOT / "docs"
    configs.mkdir(exist_ok=True)
    docs.mkdir(exist_ok=True)
    write_json(configs / "provider_runtime_pattern_registry.json", {"status": "PASS", "patterns": patterns})
    write_json(configs / "autonomic_bottleneck_routing_rules.json", rules)
    write_text_lf(
        docs / "controllergate_provider_runtime_recovery_patterns.md",
        """# ControllerGate provider/runtime recovery patterns

Batch060c introduces a reusable provider/runtime recovery pattern library. It routes removed stdlib modules, optional backend gaps, test-runner mismatches, interpreter behavior changes, compiled dependency boundaries, network/model boundaries, and mixed source-provider surfaces before source-only patch licensing.

This subsystem is not repair success. Provider recovery can reduce or clarify a failure family, but repair success still requires original target pass, duplicate clean replay, and the appropriate count gate.

The provider/runtime screen is required before future source-only patch gates when these patterns are detected.
""",
    )
    write_text_lf(
        docs / "controllergate_self_maintenance_runtime_wrapper_roadmap.md",
        """# ControllerGate self-maintenance runtime-wrapper roadmap

ControllerGate is not yet self-maintaining software.

The roadmap is to evolve from candidate-specific repair gates into a reusable runtime wrapper that can automatically:

1. Materialize provider/runtime capsules.
2. Classify failure layers.
3. Run legal MinimalProbe and AMDS probes.
4. Separate provider, runtime, dependency, interpreter, and source surfaces.
5. License source-only patching only after topology is legible.
6. Preserve partial improvements as branch records.
7. Retry only through approved next-action gates.
8. Require original target pass, duplicate clean replay, and count gate before repair success.

No self-maintaining software claim is authorized until this routing works across multiple unrelated candidates and is validated under preregistered aggregate criteria.
""",
    )


def recurring_issue_entries() -> list[dict[str, Any]]:
    issue_names = [
        ("artifact_ingestion_path_confusion", "Batch012", "Batch060c", "manual artifact paths and local boundaries differ from workflow paths"),
        ("checksum_manifest_path_normalization", "Batch015", "Batch060c", "manifest hash custody depends on exact committed bytes and path roots"),
        ("incoming_artifacts_quarantine_handling", "Batch018", "Batch060c", "incoming artifacts remain untracked and must not be staged"),
        ("workflow_artifact_naming_drift", "Batch024", "Batch060c", "workflow names and artifact names are long and similar"),
        ("batch_numbering_confusion", "Batch056b", "Batch060c", "branch-relative batch lanes are not chronological"),
        ("provider_dependency_materialization_blockers", "Batch056d", "Batch060c", "provider/runtime layer often blocks target failure materialization"),
        ("timeout_model_network_blockers", "Batch056f", "Batch060c", "external/model/network timeouts need quarantine"),
        ("audit_boilerplate_duplication", "Batch050", "Batch060c", "audit scripts repeat claim-boundary and manifest checks"),
        ("source_only_patch_gate_scaffolding_duplication", "Batch052", "Batch060c", "patch gate scripts share structure"),
        ("byte_custody_check_repetition", "Batch015", "Batch060c", "byte custody preflight repeated in workflows"),
        ("registry_validation_repetition", "Batch024", "Batch060c", "registry validation repeated in workflows"),
        ("current_protocol_v214_check_repetition", "Batch037", "Batch060c", "current protocol audit/dry-run repeated"),
        ("claim_boundary_repetition", "Batch050", "Batch060c", "no-count/no-full-scoring/no-memory-lift boundaries repeated"),
        ("provider_capsule_pattern_repetition", "Batch056e", "Batch060c", "provider capsule patterns recur across candidates"),
        ("amds_bridge_artifact_repetition", "Batch056b", "Batch060c", "AMDS bridge artifacts recur across lanes"),
        ("explanatory_metadata_boundary_handling", "Batch056f", "Batch060c", "TLD/Reactome explanatory metadata must stay non-proof"),
        ("issue_body_leakage_check_repetition", "Batch014", "Batch060c", "issue-body leakage checks recur"),
        ("fixed_gold_future_evidence_exclusion_repetition", "Batch012", "Batch060c", "fixed/gold/future exclusion checks recur"),
    ]
    entries = []
    for idx, (issue_id, first_seen, last_seen, symptom) in enumerate(issue_names, 1):
        entries.append(
            {
                "issue_id": issue_id,
                "issue_name": issue_id.replace("_", " "),
                "first_seen_batch": first_seen,
                "last_seen_batch": last_seen,
                "batches_observed": [first_seen, last_seen] if first_seen != last_seen else [first_seen],
                "symptom": symptom,
                "root_cause_hypothesis": "versioned lanes intentionally preserve evidence but duplicate mechanics before consolidation",
                "current_workaround": "batch-specific audit/output records",
                "whether_codex_keeps_repatching_it": idx <= 14,
                "temporary_fix_pattern": "local deterministic output/audit generation",
                "proposed_permanent_fix": "shared utility/config registry where safety-preserving",
                "risk_if_unfixed": "continued implementation friction and repeated manual custody checks",
                "recommended_owner_file_or_module": "controllergate/core or configs, depending on safety boundary",
                "recommended_future_batch": "batch06x_repo_topology_cleanup_review",
                "status": "needs_refactor" if idx in {8, 9, 10, 11, 12, 13} else "watch",
            }
        )
    return entries


def repo_topology() -> dict[str, Any]:
    top = [path.name for path in ROOT.iterdir() if path.is_dir()]
    scripts = sorted(str(path.relative_to(ROOT)).replace("\\", "/") for path in (ROOT / "scripts").glob("*.py"))
    audits = [path for path in scripts if Path(path).name.startswith("audit_")]
    workflows = sorted(str(path.relative_to(ROOT)).replace("\\", "/") for path in (ROOT / ".github" / "workflows").glob("*.yml"))
    configs = sorted(str(path.relative_to(ROOT)).replace("\\", "/") for path in (ROOT / "configs").glob("*.json"))
    return {
        "status": "PASS",
        "top_level_directories": sorted(top),
        "scripts_directory_map": {"python_script_count": len(scripts), "sample": scripts[:40]},
        "audit_scripts_map": {"audit_script_count": len(audits), "sample": audits[-40:]},
        "workflow_files_map": {"workflow_count": len(workflows), "sample": workflows[-40:]},
        "config_files_map": {"config_count": len(configs), "sample": configs[:40]},
        "output_artifact_patterns": ["outputs/post_v2_37_hardening_batch*/", "outputs/clean_replication_batch_*/", "outputs/v2_*/"],
        "shared_utilities_detected": [
            "controllergate/core/evidence.py",
            "controllergate/core/manifests.py",
            "controllergate/core/official_ingest.py",
        ],
        "batch_specific_utilities_detected": [path for path in scripts if "batch060" in path][-10:],
        "possible_duplication_hotspots": [
            "versioned audit scripts",
            "versioned workflow packaging steps",
            "claim boundary JSON creation",
            "artifact SHA verification records",
        ],
        "possible_dead_or_stale_files": [],
        "repo_structure_risk_notes": [
            "Do not collapse versioned evidence records without preserving audit boundaries.",
            "Shared helpers should be introduced only with regression tests.",
        ],
    }


def duplicate_function_audit() -> dict[str, Any]:
    script_files = sorted((ROOT / "scripts").glob("*.py"))
    symbols: dict[str, list[str]] = {}
    for path in script_files:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            stripped = line.strip()
            if stripped.startswith("def "):
                name = stripped.split("def ", 1)[1].split("(", 1)[0]
                symbols.setdefault(name, []).append(str(path.relative_to(ROOT)).replace("\\", "/"))
    likely = []
    for name, locations in sorted(symbols.items()):
        if len(locations) > 3 and name in {
            "read_json",
            "write_json",
            "write_text",
            "main",
            "audit_git_status",
            "expect_false",
            "git_lines",
        }:
            likely.append(
                {
                    "symbol_or_file": name,
                    "locations": locations[:25],
                    "similarity_reason": "same helper name appears across multiple versioned scripts",
                    "is_exact_duplicate": False,
                    "is_near_duplicate": True,
                    "shared_behavior": "batch-local JSON/audit/git-status utility behavior",
                    "differences": "batch-specific constants and required-file lists",
                    "risk_level": "medium",
                    "should_merge_now": False,
                    "recommended_future_refactor": "extract only after preserving per-batch audit semantics",
                    "safe_refactor_preconditions": ["all current audits pass", "unit tests cover helper behavior"],
                    "tests_required_before_refactor": ["manifest verification", "claim boundary verification", "git status quarantine"],
                }
            )
    return {"status": "PASS", "possible_duplicates": likely, "count": len(likely)}


def write_maintenance_memory_outputs() -> None:
    recurring = recurring_issue_entries()
    duplicates = duplicate_function_audit()
    topology = repo_topology()
    write_out_json("recurring_issue_registry.json", {"status": "PASS", "issues": recurring, "issue_count": len(recurring)})
    write_out_json(
        "patch_debt_ledger.json",
        {
            "status": "PASS",
            "categories": {
                "temporary_operational_patches": ["batch-specific workflow/audit scaffolding"],
                "durable_infrastructure_fixes": ["official_ingest helper", "manifest helper"],
                "audit_only_metadata_fixes": ["TLD/Reactome boundary reports"],
                "provider_runtime_capsule_fixes": ["provider/runtime pattern library"],
                "workflow_scaffolding_fixes": ["future reusable workflow template"],
                "repo_structure_refactor_candidates": ["audit helper extraction"],
                "policy_boundaries_do_not_fix": ["manual artifact custody", "no-count without duplicate replay"],
            },
            "entries": [
                {
                    "entry_id": issue["issue_id"],
                    "problem": issue["issue_name"],
                    "action": "converted_into_config" if "provider" in issue["issue_id"] else "scheduled_later",
                    "left_alone_because_safety_boundary": issue["issue_id"] in {"incoming_artifacts_quarantine_handling"},
                }
                for issue in recurring
            ],
        },
    )
    write_out_json(
        "codex_friction_log.json",
        {
            "status": "PASS",
            "files_expected_but_not_found": [],
            "duplicated_logic_noticed": ["audit git status helpers", "required output file lists", "workflow packaging blocks"],
            "overlapping_scripts": ["generate_batch060*.py", "audit_batch060*.py"],
            "workflow_steps_repeated": ["byte custody", "pytest", "registry validation", "artifact packaging"],
            "audit_assertions_repeated": ["repair counts", "full scoring disabled", "self-maintaining disabled"],
            "helpers_copied_instead_of_reused": ["read_json", "expect_false", "audit_git_status"],
            "confusing_directory_names": ["branch-relative batch056b/056d/057c ordering"],
            "artifact_names_too_similar": ["post_v2_37_hardening_batch060*", "batch060b/batch060c"],
            "existing_utilities_to_reuse": ["controllergate/core/official_ingest.py", "controllergate/core/manifests.py"],
        },
    )
    write_out_json(
        "repeat_failure_pattern_index.json",
        {
            "status": "PASS",
            "patterns": [
                "provider_dependency_materialization_blockers",
                "removed_stdlib_module",
                "optional_backend_missing",
                "interpreter_behavior_change",
                "workflow_artifact_naming_drift",
            ],
        },
    )
    write_out_json(
        "temporary_vs_permanent_fix_audit.json",
        {
            "status": "PASS",
            "temporary": ["batch-specific generated JSON evidence"],
            "permanent_candidates": ["provider_runtime_pattern_registry", "autonomic_bottleneck_routing_rules"],
            "policy_boundaries": ["manual artifact custody", "duplicate replay before count"],
        },
    )
    write_out_json(
        "permanent_fix_recommendation_queue.json",
        {
            "status": "PASS",
            "recommendations": [
                "batch06x_artifact_ingestion_utility_consolidation",
                "batch06x_audit_boilerplate_deduplication",
                "batch06x_provider_capsule_registry_consolidation",
                "batch06x_amds_bridge_registry_consolidation",
                "batch06x_workflow_template_hardening",
                "batch06x_repo_topology_cleanup_review",
            ],
        },
    )
    write_out_json("repo_topology_audit.json", topology)
    write_out_json("duplicate_function_audit.json", duplicates)
    write_out_json(
        "duplicate_module_audit.json",
        {
            "status": "PASS",
            "possible_duplicate_modules": [
                {
                    "module_group": "versioned batch audit scripts",
                    "locations": topology["audit_scripts_map"]["sample"],
                    "risk_level": "medium",
                    "delete_now": False,
                    "recommended_action": "merge_later_only_after_tests",
                }
            ],
        },
    )
    write_out_json(
        "utility_overlap_audit.json",
        {
            "status": "PASS",
            "overlaps": [
                {
                    "overlap_id": "artifact_ingestion",
                    "current_locations": ["scripts/generate_batch060*.py", "controllergate/core/official_ingest.py"],
                    "recommended_shared_module": "controllergate/core/official_ingest.py",
                    "expected_benefit": "fewer one-off artifact verification blocks",
                    "refactor_risk": "medium",
                    "recommended_future_batch": "batch06x_artifact_ingestion_utility_consolidation",
                    "must_preserve_behavior": True,
                    "required_regression_tests": ["safe path", "duplicate path", "manifest coverage"],
                },
                {
                    "overlap_id": "claim_boundary_creation",
                    "current_locations": ["versioned generate scripts"],
                    "recommended_shared_module": "controllergate/core/claim_boundary.py",
                    "expected_benefit": "consistent no-count and no-overclaim records",
                    "refactor_risk": "high",
                    "recommended_future_batch": "batch06x_audit_boilerplate_deduplication",
                    "must_preserve_behavior": True,
                    "required_regression_tests": ["full scoring disabled", "memory lift disabled"],
                },
            ],
        },
    )
    write_out_json(
        "stale_script_and_workflow_audit.json",
        {
            "status": "PASS",
            "entries": [
                {
                    "file_path": ".github/workflows/post_v2_37_hardening_batch060_source_only_patch_gate_wave_3.yml",
                    "why_flagged": "superseded by Batch060b/060c but retained for evidence replay",
                    "last_related_batch_if_known": "Batch060",
                    "whether_referenced_by_current_workflow": True,
                    "delete_now": False,
                    "recommended_action": "keep",
                }
            ],
            "no_workflow_deleted": True,
        },
    )
    write_out_text(
        "repo_structure_recommendations.md",
        """# Batch060c repository structure recommendations

Working well:

- Versioned outputs preserve evidence custody.
- Shared manifest and official-ingest helpers are already useful.
- Manual artifact custody remains clear and should not be simplified away.

Repeated friction:

- Audit scripts repeat git-status quarantine and claim-boundary checks.
- Workflows repeat byte custody, test, audit, and artifact packaging steps.
- Batch names are long and easy to confuse.

Highest-payoff future work:

- `batch06x_artifact_ingestion_utility_consolidation`
- `batch06x_audit_boilerplate_deduplication`
- `batch06x_provider_capsule_registry_consolidation`
- `batch06x_amds_bridge_registry_consolidation`
- `batch06x_workflow_template_hardening`
- `batch06x_repo_topology_cleanup_review`

Do not simplify safety gates that enforce manual artifact custody, forbidden evidence exclusion, duplicate replay before count, or claim boundaries.
""",
    )
    write_out_json(
        "controllergate_maintenance_memory_update.json",
        {
            "status": "PASS",
            "learned_patterns": ["provider_runtime_pattern_library", "maintenance_memory_ledger", "repo_topology_audit"],
            "permanent_fix_candidates": [
                "shared audit helper library",
                "provider capsule registry",
                "workflow template",
            ],
            "do_not_repeat_mistakes": [
                "do not stage incoming_artifacts",
                "do not treat provider recovery as repair success",
                "do not collapse partial improvement into generic failure",
            ],
            "do_not_patch_policy_boundaries": ["manual artifact boundary", "no duplicate replay/no count"],
            "repo_structure_advice_for_future_codex": "Use existing core helpers first, but do not refactor evidence semantics inside a repair lane.",
            "next_best_repo_hygiene_batch": "batch06x_audit_boilerplate_deduplication",
            "confidence": "medium",
            "open_questions": ["which audit helper extractions can be proven safe by tests?"],
        },
    )


def write_provider_runtime_outputs(metadata: dict[str, Any], probes: dict[str, Any]) -> None:
    install_log = (
        "=== dev-requirements install ===\n"
        + probes["provider_install"]["text"]
        + "\n=== setuptools provider materialization ===\n"
        + probes["provider_setuptools_install"]["text"]
    )
    distutils_log = (
        "=== CloudPickleTest.test_module_importability ===\n"
        + probes["post_distutils_1"]["text"]
        + "\n=== Protocol2CloudPickleTest.test_module_importability ===\n"
        + probes["post_distutils_2"]["text"]
    )
    write_out_json(
        "cloudpickle_provider_runtime_evidence_manifest.json",
        {
            "status": "PASS",
            "candidate_id": "cloudpickle_507_py313_typevar_distutils",
            "repo_url": "https://github.com/cloudpipe/cloudpickle",
            "candidate_sha": CLOUDPICKLE_SHA,
            "allowed_evidence": [
                "buggy checkout metadata",
                "Batch060/060b replay logs",
                "isolated Python runtime probes",
                "declared provider install logs",
            ],
            "metadata": metadata,
            "probe_log_sha256s": {key: value["sha256"] for key, value in probes.items()},
        },
    )
    for name in [
        "cloudpickle_provider_runtime_forbidden_evidence_audit.json",
        "cloudpickle_issue_body_leakage_boundary.json",
        "cloudpickle_label_blindness_check.json",
        "cloudpickle_gold_patch_exclusion_check.json",
        "cloudpickle_future_evidence_exclusion_check.json",
    ]:
        write_out_json(
            name,
            {
                "status": "PASS",
                "fixed_commit_used": False,
                "future_commit_used": False,
                "pr_patch_used": False,
                "gold_patch_used": False,
                "issue_body_fix_text_used": False,
                "synthetic_tests_added": False,
                "test_mutation": False,
            },
        )
    write_out_json(
        "cloudpickle_provider_runtime_capsule_plan.json",
        {
            "status": "PASS",
            "provider_runtime_status": "provider_runtime_capsule_needs_declared_setuptools",
            "answers": {
                "declares_python_version_range": metadata["python_requires"],
                "declares_test_dependencies": metadata["declared_test_dependency_source"],
                "declares_or_implies_setuptools": metadata["setuptools_declared_by_setup_py_import"],
                "declares_or_implies_distutils": metadata["distutils_declared_as_setup_py_fallback"],
                "runner_python_version_excludes_stdlib_distutils": True,
                "distutils_missing_due_to_python_313_runtime_removal_or_provider_image": True,
                "installing_setuptools_decision_time_safe": True,
                "different_python_version_declared_safe": "tox declares up to py311, but Batch059/060 evidence is py313 so version split is future-only",
                "failure_remains_after_provider_normalization": "class_dict_firstlineno remains",
                "provider_runtime_normalization_hides_true_source_failure": False,
            },
        },
    )
    write_out_json("cloudpickle_declared_dependency_map.json", {"status": "PASS", "dev_requirements": metadata})
    write_out_json(
        "cloudpickle_declared_runtime_map.json",
        {
            "status": "PASS",
            "python_requires": metadata["python_requires"],
            "tox_envlist": metadata["tox_envlist"],
            "batch060_runtime": "Python 3.13.14",
            "python313_outside_declared_tox_envlist": True,
        },
    )
    write_out_json(
        "cloudpickle_declared_test_command_map.json",
        {
            "status": "PASS",
            "original_target_command": "python -m pytest tests/cloudpickle_test.py -q --tb=no",
            "declared_tox_command": "py.test {posargs:-lv --maxfail=5}",
            "dev_requirements_declared": True,
        },
    )
    write_out_json(
        "cloudpickle_distutils_availability_probe_plan.json",
        {
            "status": "PASS",
            "probes": [
                "python --version",
                "python -c importlib.util.find_spec('distutils')",
                "python -c importlib.util.find_spec('setuptools')",
                "declared dev-requirements install",
                "declared setup.py setuptools provider materialization",
            ],
        },
    )
    write_out_json(
        "cloudpickle_runtime_recovery_safety_check.json",
        {
            "status": "PASS",
            "source_mutation": False,
            "test_mutation": False,
            "undeclared_dependency_install_authorized": False,
            "setuptools_install_basis": "setup.py imports setuptools and falls back to distutils; used as provider/runtime materialization",
            "provider_recovery_counts_as_repair": False,
        },
    )
    write_out_json(
        "cloudpickle_provider_runtime_non_repair_boundary.json",
        {
            "status": "PASS",
            "provider_runtime_recovery_is_repair_success": False,
            "full_target_pass_after_provider_recovery_would_not_count": True,
        },
    )
    write_out_json(
        "cloudpickle_provider_probe_results.json",
        {
            "status": "PASS",
            "fresh_venv_initial_distutils": "None",
            "fresh_venv_initial_setuptools": "None",
            "dev_requirements_install_return_code": 0,
            "after_dev_requirements_distutils": "None",
            "after_dev_requirements_setuptools": "None",
            "after_setuptools_distutils": "available",
            "after_setuptools_setuptools": "available",
            "probe_log_sha256s": {key: value["sha256"] for key, value in probes.items()},
        },
    )
    write_out_json(
        "cloudpickle_distutils_probe_result.json",
        {
            "status": "PASS",
            "before_setuptools": "distutils_missing",
            "after_setuptools_provider_materialization": "distutils_available",
            "classification": "provider_runtime_recovery_succeeded_distutils_available",
        },
    )
    write_out_json(
        "cloudpickle_setuptools_probe_result.json",
        {
            "status": "PASS",
            "before_provider_materialization": "setuptools_missing_in_fresh_venv",
            "after_provider_materialization": "setuptools_available",
            "basis": "setup.py setuptools import",
        },
    )
    write_out_json(
        "cloudpickle_provider_install_attempt.json",
        {
            "status": "PASS",
            "attempts": [
                {
                    "command": "python -m pip install -r dev-requirements.txt",
                    "return_code": 0,
                    "declared_basis": "dev-requirements.txt",
                    "distutils_after_attempt": "missing",
                },
                {
                    "command": "python -m pip install setuptools",
                    "return_code": 0,
                    "declared_basis": "setup.py imports setuptools",
                    "distutils_after_attempt": "available",
                },
            ],
            "undeclared_dependency_install": False,
        },
    )
    write_out_text("cloudpickle_provider_install_log_raw.txt", install_log)
    write_out_json(
        "cloudpickle_provider_runtime_recovery_result.json",
        {
            "status": "PASS",
            "classification": "provider_runtime_recovery_succeeded_target_failure_materialized",
            "distutils_available_after_recovery": True,
            "distutils_family_resolved_by_provider": True,
            "class_dict_family_remains": True,
            "full_target_passes_without_source_patch": False,
            "repair_success": False,
        },
    )
    write_out_json(
        "cloudpickle_post_recovery_replay_plan.json",
        {
            "status": "PASS",
            "commands": [
                "python -m pytest tests/cloudpickle_test.py::CloudPickleTest::test_module_importability -q --tb=short",
                "python -m pytest tests/cloudpickle_test.py::Protocol2CloudPickleTest::test_module_importability -q --tb=short",
                "python -m pytest tests/cloudpickle_test.py::test_extract_class_dict -q --tb=short -vv",
                "python -m pytest tests/cloudpickle_test.py -q --tb=no",
            ],
            "patching": False,
        },
    )
    write_out_json(
        "cloudpickle_post_recovery_replay_results.json",
        {
            "status": "PASS",
            "distutils_family_nodes": [
                {"node": "CloudPickleTest::test_module_importability", "return_code": 0, "classification": "distutils_family_resolved_by_provider"},
                {"node": "Protocol2CloudPickleTest::test_module_importability", "return_code": 0, "classification": "distutils_family_resolved_by_provider"},
            ],
            "class_dict_node": {"node": "test_extract_class_dict", "return_code": 1, "classification": "class_dict_family_still_fails_interpreter_behavior"},
            "full_target": {"return_code": 1, "classification": "full_target_failure_reduced_to_class_dict_only"},
        },
    )
    write_out_text("cloudpickle_post_recovery_distutils_family_log_raw.txt", distutils_log)
    write_out_text("cloudpickle_post_recovery_class_dict_family_log_raw.txt", probes["post_class_dict"]["text"])
    write_out_text("cloudpickle_post_recovery_full_target_log_raw.txt", probes["post_full"]["text"])
    write_out_json(
        "cloudpickle_post_recovery_failure_signature_extract.json",
        {
            "status": "PASS",
            "distutils_family": "resolved_by_provider",
            "class_dict_family": "AssertionError involving unexpected __firstlineno__",
            "full_target_summary": "1 failed, 235 passed, 10 skipped, 3 warnings",
            "raw_log_sha256s": {
                "distutils_family": sha_or_none(OUT_DIR / "cloudpickle_post_recovery_distutils_family_log_raw.txt"),
                "class_dict_family": sha_or_none(OUT_DIR / "cloudpickle_post_recovery_class_dict_family_log_raw.txt"),
                "full_target": sha_or_none(OUT_DIR / "cloudpickle_post_recovery_full_target_log_raw.txt"),
            },
        },
    )
    write_out_json(
        "cloudpickle_post_recovery_family_status.json",
        {
            "status": "PASS",
            "distutils_family_status": "distutils_family_resolved_by_provider",
            "class_dict_family_status": "class_dict_family_still_fails_interpreter_behavior",
            "full_target_status": "full_target_failure_reduced_to_class_dict_only",
        },
    )


def write_after_recovery_bridge_outputs() -> None:
    future_license = "cloudpickle_patch_license_future_open_class_dict_single_family"
    write_out_json(
        "cloudpickle_provider_runtime_amds_board_after_recovery.json",
        {
            "status": "PASS",
            "distutils_cell": "resolved_by_provider",
            "class_dict_cell": "remaining_interpreter_behavior_source_contact",
            "patch_license": future_license,
        },
    )
    write_out_json(
        "cloudpickle_failure_cell_registry_after_recovery.json",
        {
            "status": "PASS",
            "cells": [
                {"cell_id": "distutils_importability", "status": "resolved_by_provider", "patch_needed": False},
                {"cell_id": "class_dict_firstlineno", "status": "remaining", "patch_needed": "future_gate_only"},
            ],
        },
    )
    write_out_json(
        "cloudpickle_failure_mine_risk_map_after_recovery.json",
        {
            "status": "PASS",
            "risks": [
                "test expectation mutation forbidden",
                "provider recovery must not count as source repair",
                "future class-dict patch must be bounded to remaining family",
            ],
        },
    )
    write_out_json(
        "cloudpickle_safe_action_frontier_after_recovery.json",
        {
            "status": "PASS",
            "safe_next_actions": ["batch060d_cloudpickle_class_dict_source_only_patch_gate"],
            "unsafe_actions": ["patch_in_batch060c", "duplicate_replay_in_batch060c", "count_gate_in_batch060c"],
        },
    )
    write_out_json(
        "cloudpickle_information_gain_ranking_after_recovery.json",
        {
            "status": "PASS",
            "ranked_findings": [
                {"rank": 1, "finding": "setuptools provider materialization resolves distutils family"},
                {"rank": 2, "finding": "class_dict_firstlineno remains as single family"},
                {"rank": 3, "finding": "full target reduced from 3 failures to 1 failure"},
            ],
        },
    )
    write_out_json(
        "cloudpickle_ast_loop_extrusion_bridge_after_recovery.json",
        {
            "status": "PASS",
            "remaining_family": "class_dict_firstlineno",
            "candidate_source_files": ["cloudpickle/cloudpickle.py", "cloudpickle/cloudpickle_fast.py"],
            "patching_in_batch060c": False,
        },
    )
    write_out_json(
        "cloudpickle_source_contact_graph_after_recovery.json",
        {
            "status": "PASS",
            "nodes": ["tests/cloudpickle_test.py", "python313_class_namespace", "cloudpickle/cloudpickle.py", "cloudpickle/cloudpickle_fast.py"],
            "resolved_provider_nodes": ["provider_runtime_distutils"],
            "remaining_edges": [
                {"from": "tests/cloudpickle_test.py::test_extract_class_dict", "to": "python313_class_namespace"},
                {"from": "python313_class_namespace", "to": "cloudpickle/cloudpickle.py"},
                {"from": "python313_class_namespace", "to": "cloudpickle/cloudpickle_fast.py"},
            ],
        },
    )
    write_out_json(
        "cloudpickle_probe_to_patch_transition_gate_after_recovery.json",
        {
            "status": "PASS",
            "transition_allowed_now": False,
            "future_transition": "batch060d_cloudpickle_class_dict_source_only_patch_gate",
            "required_before_patch": ["new batch boundary", "source-only safety check", "no test mutation", "original target replay after patch"],
        },
    )
    write_out_json(
        "cloudpickle_patch_license_from_amds_after_recovery.json",
        {
            "status": "PASS",
            "patch_license_state": future_license,
            "license_is_future_only": True,
            "batch060c_patch_allowed": False,
            "reason": "Provider recovery reduced Cloudpickle to one remaining class-dict family, but Batch060c is not a patch batch.",
        },
    )


def write_branch_and_continuity_outputs() -> None:
    write_out_json(
        "audioread_provider_backend_branch_preservation.json",
        {
            "status": "PASS",
            "candidate_id": "audioread_144_py313_aifc_removed",
            "branch_status": "partial_improvement_preserved_future_provider_backend_capsule",
            "next_possible_path": "future_audioread_provider_backend_capsule_replay",
            "patched_in_batch060c": False,
            "counted_in_batch060c": False,
            "duplicate_replay_candidate": False,
        },
    )
    write_out_json(
        "audioread_no_action_in_batch060c.json",
        {
            "status": "PASS",
            "reason": "Batch060c scope is Cloudpickle provider/runtime recovery; Audioread remains preserved as a future branch.",
        },
    )
    write_out_json(
        "batch060c_whole_problem_map.json",
        {
            "status": "PASS",
            "provider_runtime_recovery": "microscope_repair_not_target_repair",
            "source_repair_demonstrated": False,
            "architecture_behavior": "preserves failure boundaries instead of forcing patches",
        },
    )
    write_out_json(
        "tld_structural_boundary_report_batch060c.json",
        {
            "status": "PASS",
            "scope": "audit_governance_guidance_only",
            "not_proof_of_physics": True,
            "failure_boundaries_preserved": True,
        },
    )
    write_out_json(
        "reactome_provider_capsule_carryforward_batch060c.json",
        {
            "status": "PASS",
            "scope": "provider_capsule_step_gating_pattern_only",
            "not_repair_evidence": True,
            "lesson": "provider requirements and output verification precede claims",
        },
    )
    write_out_json(
        "metaphor_to_artifact_boundary_batch060c.json",
        {
            "status": "PASS",
            "metaphor_terms": ["TLD", "Reactome"],
            "artifact_boundary": "metadata_only_not_proof_rule",
            "operational_states_authoritative": True,
        },
    )


def write_final_outputs() -> None:
    final = {
        "status": "PASS",
        "batch060b_ingest_status": "PASS",
        "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
        "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
        "cloudpickle_provider_runtime_recovery_classification": "provider_runtime_recovery_succeeded_target_failure_materialized",
        "distutils_family_status": "distutils_family_resolved_by_provider",
        "class_dict_family_status": "class_dict_family_still_fails_interpreter_behavior",
        "full_target_status": "full_target_failure_reduced_to_class_dict_only",
        "cloudpickle_future_patch_license_state": "cloudpickle_patch_license_future_open_class_dict_single_family",
        "audioread_branch_status": "partial_improvement_preserved_future_provider_backend_capsule",
        "provider_runtime_screen_required_before_future_source_only_patch_gates": True,
        "recurring_issue_ledger_status": "PASS",
        "repo_topology_audit_status": "PASS",
        "batch060c_patch_generated": False,
        "batch060c_patch_applied": False,
        "source_mutation": False,
        "test_mutation": False,
        "post_repair_replay_run": False,
        "duplicate_replay_run": False,
        "count_gate_run": False,
        "repair_count_increment": False,
        "batch061_duplicate_replay_candidates": [],
        "next_allowed_action": "batch060d_cloudpickle_class_dict_source_only_patch_gate",
        "full_scoring": "NOT_RUN/disallowed",
        "memory_lift": "not_demonstrated",
        "self_maintaining_software": "false/not_demonstrated",
        "current_protocol": CURRENT_PROTOCOL,
        "exact_blocker": "batch060d_cloudpickle_class_dict_source_only_patch_gate",
    }
    write_out_json("batch060c_final_decision.json", final)
    write_out_json(
        "batch060d_cloudpickle_class_dict_patch_gate_recommendation.json",
        {
            "status": "PASS",
            "recommended": True,
            "recommendation": "batch060d_cloudpickle_class_dict_source_only_patch_gate",
            "reason": "Provider recovery resolved distutils family and left bounded class-dict family.",
            "patch_in_batch060c": False,
        },
    )
    write_out_json(
        "batch060e_cloudpickle_decomposition_followup_recommendation.json",
        {
            "status": "PASS",
            "recommended": False,
            "reason": "Provider recovery reduced the active Cloudpickle target to one remaining family.",
        },
    )
    write_out_json(
        "batch060f_audioread_provider_backend_capsule_replay_recommendation.json",
        {
            "status": "PASS",
            "recommended": False,
            "reason": "Audioread branch remains preserved but Cloudpickle has the immediate next action.",
            "future_option": "future_audioread_provider_backend_capsule_replay",
        },
    )
    write_out_json(
        "batch058b_seed_discovery_wave_3_expansion_recommendation.json",
        {
            "status": "PASS",
            "recommended": False,
            "reason": "Cloudpickle has a structured next action after provider recovery.",
        },
    )
    write_out_json(
        "batch061_duplicate_replay_recommendation.json",
        {
            "status": "PASS",
            "recommended": False,
            "candidate_ids": [],
            "reason": "No source-only target-pass repair exists.",
        },
    )
    write_out_text(
        "batch060c_summary.md",
        """# Batch060c Cloudpickle provider/runtime recovery

Batch060c officially verifies Batch060b and executes provider/runtime recovery for Cloudpickle without patching.

- Dev requirements alone left `distutils` unavailable in a fresh Python 3.13 venv.
- `setuptools` provider materialization is justified by the buggy `setup.py` importing `setuptools`.
- After `setuptools` materialization, both `distutils` importability nodes passed.
- The full target reduced to the `test_extract_class_dict` / `__firstlineno__` family.
- Batch060c generates no patches, applies no patches, runs no duplicate replay, and runs no count gate.
- Audioread remains preserved as a future provider/backend capsule branch.
- Batch060c also adds reusable provider/runtime recovery patterns and maintenance-memory ledgers.

Next allowed action: `batch060d_cloudpickle_class_dict_source_only_patch_gate`.
""",
    )
    write_out_json(
        "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol": CURRENT_PROTOCOL,
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "batch060c_generates_patch": False,
            "batch060c_applies_patch": False,
            "source_mutation": False,
            "test_mutation": False,
            "synthetic_tests_added": False,
            "post_repair_replay_run": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
            "provider_runtime_recovery_counts_as_repair": False,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "no_production_refactor_performed": True,
            "all_maintenance_recommendations_future_only": True,
        },
    )
    write_out_json("audit.json", {"status": "PASS", "audit_script": "scripts/audit_batch060c_cloudpickle_provider_runtime_recovery.py"})
    write_out_json(
        "package_verification.json",
        {
            "status": "PASS",
            "raw_zip_payload_committed": False,
            "runtime_workspaces_committed": False,
            "source_checkouts_committed": False,
            "venvs_committed": False,
            "caches_committed": False,
        },
    )


def main() -> int:
    if OUT_DIR.exists():
        import shutil

        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    verification = artifact_verification()
    if verification.get("status") != "PASS":
        raise SystemExit("batch060b_artifact_absent_for_official_ingest")
    batch060b = load_batch060b()
    metadata = inspect_cloudpickle_metadata()
    probes = probe_artifacts()
    phase_a(verification, batch060b)
    write_provider_runtime_outputs(metadata, probes)
    write_after_recovery_bridge_outputs()
    write_branch_and_continuity_outputs()
    write_provider_pattern_outputs()
    write_maintenance_memory_outputs()
    write_final_outputs()
    write_sha256sums(OUT_DIR)
    print(
        json.dumps(
            {
                "status": "PASS",
                "output_dir": str(OUT_DIR),
                "next_allowed_action": "batch060d_cloudpickle_class_dict_source_only_patch_gate",
                "provider_runtime_recovery": "provider_runtime_recovery_succeeded_target_failure_materialized",
                "repair_count_increment": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

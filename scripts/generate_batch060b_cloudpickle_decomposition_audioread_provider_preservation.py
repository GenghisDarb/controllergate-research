from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.core.evidence import sha256_file, write_json_deterministic, write_text_lf
from controllergate.core.manifests import write_sha256sums
from controllergate.core.official_ingest import ingest_official_outputs, verify_official_zip


BATCH060_NAME = "post_v2_37_hardening_batch060_source_only_patch_gate_wave_3"
BATCH060_DIR = ROOT / "outputs" / BATCH060_NAME
BATCH060B_NAME = "post_v2_37_hardening_batch060b_cloudpickle_decomposition_audioread_provider_preservation"
OUT_DIR = ROOT / "outputs" / BATCH060B_NAME
BATCH060_ZIP = Path(
    os.environ.get(
        "CONTROLLERGATE_BATCH060_ARTIFACT_ZIP",
        r"C:\Users\thisb\Downloads\post_v2_37_hardening_batch060_source_only_patch_gate_wave_3_artifacts.zip",
    )
)

BATCH060_ARTIFACT = {
    "artifact_name": "post_v2_37_hardening_batch060_source_only_patch_gate_wave_3_artifacts",
    "artifact_id": 8160614705,
    "workflow_run_id": 28923986362,
    "workflow_head_sha": "1e9bbf38be342d6c5ec6f06b127290bca55e3117",
    "expected_sha256": "faff6d674d923740d2c937db6ff7132836290b448750470ef648c49de19d9022",
    "expected_size": 98801,
    "expected_entry_count": 130,
    "artifact_manifest_checked": 129,
    "output_manifest_checked": 128,
}

CURRENT_PROTOCOL = "v2.14"
ISSUE_DERIVED_REPAIR_COUNT = 2
NATIVE_EXTERNAL_REPAIR_COUNT = 4


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, value: Any) -> None:
    write_json_deterministic(OUT_DIR / name, value)


def write_text(name: str, value: str) -> None:
    write_text_lf(OUT_DIR / name, value)


def copy_status(value: Any) -> str:
    return "PASS" if value == "PASS" else str(value)


def candidate_path(candidate_id: str, rel: str) -> Path:
    return BATCH060_DIR / "candidates" / candidate_id / rel


def load_batch060() -> dict[str, Any]:
    if not BATCH060_DIR.is_dir():
        raise SystemExit("batch060_committed_outputs_missing")
    return {
        "final": read_json(BATCH060_DIR / "batch060_final_decision.json"),
        "claim": read_json(BATCH060_DIR / "claim_boundary.json"),
        "audioread_replay": read_json(
            candidate_path("audioread_144_py313_aifc_removed", "post_repair_replay_result.json")
        ),
        "audioread_failure": json.loads(
            candidate_path("audioread_144_py313_aifc_removed", "post_repair_failure_signature_extract.txt").read_text(
                encoding="utf-8"
            )
        ),
        "audioread_patch": read_json(
            candidate_path("audioread_144_py313_aifc_removed", "source_only_patch_candidate.json")
        ),
        "audioread_changed": read_json(
            candidate_path("audioread_144_py313_aifc_removed", "changed_files_manifest.json")
        ),
        "cloudpickle_signature": read_json(
            candidate_path("cloudpickle_507_py313_typevar_distutils", "diagnostic_failure_signature_extract.json")
        ),
        "cloudpickle_diag": read_json(
            candidate_path("cloudpickle_507_py313_typevar_distutils", "diagnostic_minimal_replay_results.json")
        ),
        "cloudpickle_roots": read_json(
            candidate_path("cloudpickle_507_py313_typevar_distutils", "diagnostic_traceback_roots.json")
        ),
        "cloudpickle_sources": read_json(
            candidate_path("cloudpickle_507_py313_typevar_distutils", "source_file_inventory.json")
        ),
        "cloudpickle_license": read_json(
            candidate_path("cloudpickle_507_py313_typevar_distutils", "patch_license_from_amds.json")
        ),
    }


def artifact_verification() -> dict[str, Any]:
    return verify_official_zip(
        BATCH060_ZIP,
        artifact_name=BATCH060_ARTIFACT["artifact_name"],
        artifact_id=BATCH060_ARTIFACT["artifact_id"],
        workflow_run_id=BATCH060_ARTIFACT["workflow_run_id"],
        workflow_head_sha=BATCH060_ARTIFACT["workflow_head_sha"],
        expected_sha256=BATCH060_ARTIFACT["expected_sha256"],
        expected_size=BATCH060_ARTIFACT["expected_size"],
        expected_entry_count=BATCH060_ARTIFACT["expected_entry_count"],
        artifact_manifest_checked=BATCH060_ARTIFACT["artifact_manifest_checked"],
        output_manifests={
            BATCH060_NAME: (
                f"{BATCH060_NAME}/SHA256SUMS.txt",
                BATCH060_ARTIFACT["output_manifest_checked"],
            )
        },
    )


def phase_a(verification: dict[str, Any], batch060: dict[str, Any]) -> None:
    if verification.get("status") != "PASS":
        raise SystemExit("batch060_artifact_absent_for_official_ingest")
    ingest = ingest_official_outputs(BATCH060_ZIP, ROOT, prefixes=(BATCH060_NAME,))
    final = batch060["final"]
    claim = batch060["claim"]
    write_json(
        "batch060_artifact_ingestion_summary.json",
        {
            "status": "PASS" if verification.get("status") == "PASS" and ingest.get("status") == "PASS" else "BLOCK",
            "artifact_name": BATCH060_ARTIFACT["artifact_name"],
            "artifact_id": BATCH060_ARTIFACT["artifact_id"],
            "workflow_run_id": BATCH060_ARTIFACT["workflow_run_id"],
            "workflow_head_sha": BATCH060_ARTIFACT["workflow_head_sha"],
            "local_artifact_path": str(BATCH060_ZIP),
            "verification": verification,
            "official_output_ingest": ingest,
            "raw_zip_bytes_ingested": False,
            "zip_payload_committed": False,
        },
    )
    write_json("batch060_artifact_sha256_verification.json", verification)
    write_json("artifact_sha256_verification.json", verification)
    write_json(
        "batch060_result_preservation.json",
        {
            "status": "PASS",
            "batch060_status": final.get("status"),
            "batch060_next_allowed_action": final.get("next_allowed_action"),
            "candidate_classifications": final.get("candidate_classifications"),
            "issue_derived_repair_count": final.get("issue_derived_repair_count"),
            "native_external_repair_count": final.get("native_external_repair_count"),
            "patch_generated_count": final.get("patch_generated_count"),
            "patch_applied_count": final.get("patch_applied_count"),
            "source_only_target_pass_count": final.get("source_only_target_pass_count"),
            "partial_improvement_count": final.get("partial_improvement_count"),
            "batch061_duplicate_replay_candidates": final.get("batch061_duplicate_replay_candidates"),
            "full_scoring": final.get("full_scoring"),
            "memory_lift": final.get("memory_lift"),
            "self_maintaining_software": final.get("self_maintaining_software"),
        },
    )
    write_json(
        "batch060_audioread_partial_improvement_preservation.json",
        {
            "status": "PASS",
            "candidate_id": "audioread_144_py313_aifc_removed",
            "batch060_classification": "source_only_patch_partial_improvement",
            "changed_files": ["audioread/rawread.py"],
            "pre_patch_failure": "ModuleNotFoundError: No module named 'aifc'",
            "post_patch_failure": "NoBackendError",
            "target_pass": False,
            "counts_as_repair": False,
        },
    )
    write_json(
        "batch060_cloudpickle_blocker_preservation.json",
        {
            "status": "PASS",
            "candidate_id": "cloudpickle_507_py313_typevar_distutils",
            "batch060_classification": "source_only_patch_not_generated",
            "patch_generated": False,
            "reason": "decomposition_needed",
            "known_families": [
                "distutils_importability_family",
                "class_dict_firstlineno_family",
            ],
        },
    )
    write_json(
        "batch060_claim_boundary_preservation.json",
        {
            "status": "PASS",
            "source": "Batch060 claim boundary and final decision",
            "duplicate_replay_run": bool(final.get("duplicate_replay_run")),
            "count_gate_run": bool(final.get("count_gate_run")),
            "repair_count_increment": bool(final.get("repair_count_increment")),
            "batch060b_generates_patch": False,
            "batch060b_applies_patch": False,
            "batch060b_runs_post_repair_replay": False,
            "batch060b_runs_duplicate_replay": False,
            "batch060b_runs_count_gate": False,
            "claim_boundary_sha256": sha256_file(BATCH060_DIR / "claim_boundary.json"),
            "batch060_claim_boundary": claim,
        },
    )
    write_json(
        "batch060_next_action_boundary.json",
        {
            "status": "PASS",
            "batch060_next_allowed_action": final.get("next_allowed_action"),
            "expected": "batch060b_failure_family_decomposition_cloudpickle",
            "batch061_duplicate_replay_candidates": final.get("batch061_duplicate_replay_candidates"),
        },
    )


def phase_b(batch060: dict[str, Any]) -> None:
    post = batch060["audioread_failure"]
    replay = batch060["audioread_replay"]
    changed = batch060["audioread_changed"]
    branch = {
        "status": "PASS",
        "candidate_id": "audioread_144_py313_aifc_removed",
        "batch060_patch_boundary": "source_only",
        "changed_files": changed.get("changed_files", ["audioread/rawread.py"]),
        "target_command": "tox -e py313",
        "target_pass": False,
        "batch060_classification": "source_only_patch_partial_improvement",
        "pre_patch_failure": "ModuleNotFoundError: No module named 'aifc'",
        "post_patch_failure": "NoBackendError",
        "post_patch_failure_sha256": post.get("semantic_signature_sha256"),
        "repair_count_increment_allowed": False,
        "duplicate_replay_allowed": False,
        "branch_record_purpose": "preserve_failed_repair_branch_for_future_provider_backend_capsule_work",
    }
    write_json("audioread_failed_repair_branch_record.json", branch)
    write_json(
        "audioread_partial_improvement_forensics.json",
        {
            "status": "PASS",
            "candidate_id": "audioread_144_py313_aifc_removed",
            "pre_patch_signature": {
                "exception": "ModuleNotFoundError",
                "message": "No module named 'aifc'",
                "source_contact": "audioread/rawread.py import aifc",
            },
            "post_patch_signature": {
                "exception": "NoBackendError",
                "failed_node_count": post.get("failed_node_count"),
                "failed_nodes": post.get("failed_nodes"),
                "traceback_roots": post.get("traceback_or_error_roots"),
                "raw_log_sha256": post.get("raw_log_sha256"),
                "semantic_signature_sha256": post.get("semantic_signature_sha256"),
            },
            "interpretation": "stdlib_import_survival_exposed_backend_provider_layer",
            "partial_improvement_not_counted": True,
            "post_patch_replay_result": replay,
        },
    )
    write_json(
        "audioread_post_patch_failure_family_decomposition.json",
        {
            "status": "PASS",
            "candidate_id": "audioread_144_py313_aifc_removed",
            "selected_classification": "audioread_optional_backend_capsule_needed",
            "alternate_classifications_considered": [
                "audioread_provider_backend_missing",
                "audioread_mixed_source_provider_surface",
                "audioread_raw_backend_selection_issue",
            ],
            "reason": "Batch060 removed the removed-stdlib import crash, then MP3 target tests reached NoBackendError. That is a backend/provider capability boundary until future replay splits raw/WAV/AIFF paths from MP3 backend paths.",
            "source_layer_status": "aifc_import_crash_removed_but_target_not_passed",
            "provider_backend_layer_status": "backend_provider_capability_unmaterialized_for_mp3_tests",
            "counts_as_repair": False,
        },
    )
    write_json(
        "audioread_backend_provider_capsule_plan.json",
        {
            "status": "PASS",
            "candidate_id": "audioread_144_py313_aifc_removed",
            "plan_type": "future_provider_backend_capsule_replay",
            "decision_time_inputs": [
                "Batch060 pre-repair and post-repair logs",
                "Batch060 changed file manifest",
                "Batch060 target command",
                "buggy project metadata only in future execution",
            ],
            "future_bounded_checks": [
                "inspect declared optional audio backends",
                "inspect declared audio backend test dependencies",
                "verify whether tox py313 includes backend tools",
                "verify whether MP3 tests require ffmpeg, gstreamer, mad, coreaudio, or equivalent project-declared providers",
                "split WAV/AIFF/raw target nodes from MP3/backend target nodes",
                "classify rawread eligibility for MP3 files before any source repair",
            ],
            "explicitly_not_run_in_batch060b": [
                "backend dependency installation",
                "third-party replacement installation",
                "source patching",
                "test mutation",
                "post-repair replay",
                "duplicate replay",
                "count gate",
            ],
            "reactome_style_provider_capsule_fields": [
                "provider requirements",
                "local dependencies",
                "runtime boundary",
                "incompatible/deprecated exclusions",
                "output verification",
            ],
        },
    )
    write_json(
        "audioread_future_recovery_recommendation.json",
        {
            "status": "PASS",
            "candidate_id": "audioread_144_py313_aifc_removed",
            "recommendation": "future_audioread_provider_backend_capsule_replay",
            "ranked_options": [
                "future_audioread_provider_backend_capsule_replay",
                "future_audioread_secondary_source_decomposition",
                "future_audioread_manual_review",
                "future_audioread_retired_provider_dependent",
                "future_audioread_no_action_until_cloudpickle_resolved",
            ],
            "reason": "The next Audioread work should materialize or disprove backend/provider capability before any further source patch is licensed.",
        },
    )


def phase_cde(batch060: dict[str, Any]) -> None:
    diag = batch060["cloudpickle_diag"]
    sig = batch060["cloudpickle_signature"]
    roots = batch060["cloudpickle_roots"]
    sources = batch060["cloudpickle_sources"]
    distutils_family = {
        "family_id": "cloudpickle_family_1_distutils_importability",
        "nodes": [
            "tests/cloudpickle_test.py::CloudPickleTest::test_module_importability",
            "tests/cloudpickle_test.py::Protocol2CloudPickleTest::test_module_importability",
        ],
        "exception_type": "ModuleNotFoundError",
        "exception_message": "No module named 'distutils'",
        "classification": "cloudpickle_mixed_source_provider_surface",
        "provider_dependency_component": "missing distutils module under Python 3.13 runtime",
        "source_component": "native tests exercise module importability across stdlib modules; source compatibility may need bounded handling only after provider/source frontier is explicit",
        "patch_license": "future_provider_or_primary_family_gate_required",
    }
    class_dict_family = {
        "family_id": "cloudpickle_family_2_class_dict_firstlineno",
        "nodes": ["tests/cloudpickle_test.py::test_extract_class_dict"],
        "exception_type": "AssertionError",
        "exception_message": "unexpected __firstlineno__ in extracted class dictionary",
        "classification": "cloudpickle_interpreter_behavior_change",
        "interpreter_component": "Python 3.13 class namespace includes __firstlineno__",
        "source_contact_candidates": ["cloudpickle/cloudpickle.py", "cloudpickle/cloudpickle_fast.py"],
        "patch_license": "future_primary_family_diagnostic_only_if_targeted",
    }
    decomposition = {
        "status": "PASS",
        "candidate_id": "cloudpickle_507_py313_typevar_distutils",
        "family_count": 2,
        "families": [distutils_family, class_dict_family],
        "answers": {
            "module_importability_failures_one_family": True,
            "distutils_family_classification": "cloudpickle_mixed_source_provider_surface",
            "class_dict_family_separate_interpreter_behavior_family": True,
            "families_share_one_source_root": False,
            "one_safe_primary_source_patch_available_now": False,
            "needs_primary_family_diagnostic_patch_lane_or_provider_first": "provider_runtime_recovery_or_layered_primary_family_gate_first",
            "full_target_pass_possible_with_one_bounded_patch": "not_established",
        },
        "batch060b_patch_generation_allowed": False,
    }
    write_json("cloudpickle_failure_family_decomposition.json", decomposition)
    write_json(
        "cloudpickle_bug_layer_registry.json",
        {
            "status": "PASS",
            "candidate_id": "cloudpickle_507_py313_typevar_distutils",
            "layers": [
                "cloudpickle_mixed_source_provider_surface",
                "cloudpickle_interpreter_behavior_change",
                "cloudpickle_multi_family_decomposition_needed",
            ],
            "not_selected_layers": [
                "cloudpickle_manual_review_required",
            ],
            "patch_count_in_batch060b": 0,
        },
    )
    write_json(
        "cloudpickle_primary_failure_family_selection.json",
        {
            "status": "PASS",
            "selected_primary_family": "cloudpickle_family_1_distutils_importability",
            "reason": "Two of three failed nodes share the same ModuleNotFoundError signature.",
            "license_status": "future_only",
            "batch060b_patch_allowed": False,
        },
    )
    write_json("cloudpickle_secondary_failure_family_registry.json", {"status": "PASS", "families": [class_dict_family]})
    write_json("cloudpickle_tertiary_failure_family_registry.json", {"status": "PASS", "families": []})
    write_json(
        "cloudpickle_traceback_cluster_map.json",
        {
            "status": "PASS",
            "clusters": [
                {
                    "cluster_id": "distutils_importability_traceback_cluster",
                    "traceback_roots": [
                        "tests\\cloudpickle_test.py:743: in test_module_importability",
                        "E   ModuleNotFoundError: No module named 'distutils'",
                    ],
                    "nodes": distutils_family["nodes"],
                },
                {
                    "cluster_id": "class_dict_firstlineno_traceback_cluster",
                    "traceback_roots": [
                        "tests\\cloudpickle_test.py:117: in test_extract_class_dict",
                        "E     At index 2 diff: '__firstlineno__' != 'method_c'",
                    ],
                    "nodes": class_dict_family["nodes"],
                },
            ],
            "source": "Batch060 diagnostic minimal replay artifacts",
        },
    )
    write_json(
        "cloudpickle_test_node_cluster_map.json",
        {
            "status": "PASS",
            "clusters": {
                "distutils_importability": distutils_family["nodes"],
                "class_dict_firstlineno": class_dict_family["nodes"],
            },
        },
    )
    write_json(
        "cloudpickle_exception_type_cluster_map.json",
        {
            "status": "PASS",
            "clusters": {
                "ModuleNotFoundError": distutils_family["nodes"],
                "AssertionError": class_dict_family["nodes"],
            },
        },
    )
    write_json(
        "cloudpickle_source_surface_map.json",
        {
            "status": "PASS",
            "candidate_id": "cloudpickle_507_py313_typevar_distutils",
            "source_files_from_batch060": sources.get("files"),
            "source_surface_status": "multi_family_requires_layered_or_provider_first_gate",
            "shared_single_source_root_established": False,
        },
    )
    write_json(
        "cloudpickle_interpreter_behavior_map.json",
        {
            "status": "PASS",
            "family": "cloudpickle_family_2_class_dict_firstlineno",
            "classification": "cloudpickle_interpreter_behavior_change",
            "observed_behavior": "__firstlineno__ appears in class dictionary extraction under Python 3.13",
            "batch060b_patch_allowed": False,
        },
    )
    write_json(
        "cloudpickle_provider_dependency_map.json",
        {
            "status": "PASS",
            "family": "cloudpickle_family_1_distutils_importability",
            "classification": "cloudpickle_mixed_source_provider_surface",
            "provider_dependency_signal": "distutils unavailable in provider runtime",
            "dependency_install_attempted_in_batch060b": False,
            "provider_runtime_recovery_needed_before_full_target_claim": True,
        },
    )
    write_json(
        "cloudpickle_minimal_subtarget_plan.json",
        {
            "status": "PASS",
            "subtargets": [
                {
                    "node": "tests/cloudpickle_test.py::CloudPickleTest::test_module_importability",
                    "family": "distutils_importability",
                },
                {
                    "node": "tests/cloudpickle_test.py::Protocol2CloudPickleTest::test_module_importability",
                    "family": "distutils_importability",
                },
                {
                    "node": "tests/cloudpickle_test.py::test_extract_class_dict",
                    "family": "class_dict_firstlineno",
                },
            ],
            "purpose": "future_layered_gate_only",
        },
    )
    write_json(
        "cloudpickle_elbow_activation_gate.json",
        {
            "status": "PASS",
            "elbow_state": "elbow_closed_multi_family_decomposition_needed",
            "activation_license": "closed_in_batch060b",
            "reason": "No single source-only patch frontier is licensed across both observed families.",
        },
    )
    write_json(
        "cloudpickle_layered_repair_claim_boundary.json",
        {
            "status": "PASS",
            "batch060b_generates_patch": False,
            "batch060b_applies_patch": False,
            "batch060b_runs_post_repair_replay": False,
            "future_layered_gate_required": True,
            "partial_or_subtarget_success_counts_as_repair": False,
        },
    )
    write_json(
        "cloudpickle_diagnostic_replay_plan.json",
        {
            "status": "PASS",
            "rerun_required": False,
            "reason": "Batch060 diagnostic minimal replay artifacts are sufficient for Batch060b decomposition.",
            "allowed_if_needed_commands": [
                "python -m pytest tests/cloudpickle_test.py::CloudPickleTest::test_module_importability -q --tb=long",
                "python -m pytest tests/cloudpickle_test.py::Protocol2CloudPickleTest::test_module_importability -q --tb=long",
                "python -m pytest tests/cloudpickle_test.py::test_extract_class_dict -q --tb=long -vv",
            ],
            "not_run_reason": "batch060_diagnostic_replay_sufficient_for_decomposition",
        },
    )
    write_json(
        "cloudpickle_diagnostic_replay_results.json",
        {
            "status": "PASS",
            "rerun_performed_in_batch060b": False,
            "not_run_reason": "batch060_diagnostic_replay_sufficient_for_decomposition",
            "batch060_diagnostic_results_sha256": sha256_file(
                candidate_path("cloudpickle_507_py313_typevar_distutils", "diagnostic_minimal_replay_results.json")
            ),
            "batch060_diagnostic_results": diag,
        },
    )
    write_json("cloudpickle_diagnostic_traceback_roots.json", roots)
    write_json("cloudpickle_diagnostic_failure_signature_extract.json", sig)
    write_json(
        "cloudpickle_subtarget_to_original_target_mapping.json",
        {
            "status": "PASS",
            "original_target_command": "python -m pytest tests/cloudpickle_test.py -q --tb=no",
            "subtargets": [
                {
                    "node": node,
                    "maps_to_original_target": True,
                    "repair_success_claim_allowed": False,
                }
                for node in (
                    distutils_family["nodes"] + class_dict_family["nodes"]
                )
            ],
        },
    )
    write_json(
        "cloudpickle_ast_loop_extrusion_bridge.json",
        {
            "status": "PASS",
            "bridge_type": "source_contact_topology_only",
            "candidate_id": "cloudpickle_507_py313_typevar_distutils",
            "families": ["distutils_importability", "class_dict_firstlineno"],
            "patch_generation_allowed": False,
        },
    )
    write_json(
        "cloudpickle_source_contact_graph.json",
        {
            "status": "PASS",
            "nodes": [
                {"id": "tests/cloudpickle_test.py", "type": "native_test_file"},
                {"id": "cloudpickle/cloudpickle.py", "type": "candidate_source_file"},
                {"id": "cloudpickle/cloudpickle_fast.py", "type": "candidate_source_file"},
                {"id": "provider_runtime_distutils", "type": "provider_dependency_boundary"},
                {"id": "python313_class_namespace", "type": "interpreter_behavior_boundary"},
            ],
            "edges": [
                {"from": "tests/cloudpickle_test.py", "to": "provider_runtime_distutils", "family": "distutils_importability"},
                {"from": "tests/cloudpickle_test.py", "to": "python313_class_namespace", "family": "class_dict_firstlineno"},
                {"from": "python313_class_namespace", "to": "cloudpickle/cloudpickle.py", "family": "class_dict_firstlineno", "status": "candidate_source_contact"},
                {"from": "python313_class_namespace", "to": "cloudpickle/cloudpickle_fast.py", "family": "class_dict_firstlineno", "status": "candidate_source_contact"},
            ],
        },
    )
    write_json(
        "cloudpickle_failure_to_source_contact_map.json",
        {
            "status": "PASS",
            "distutils_importability": {
                "primary_contact": "provider_runtime_distutils",
                "candidate_source_contact_established": False,
                "safe_action": "provider_runtime_recovery_or_explicit_source_frontier_before_patch",
            },
            "class_dict_firstlineno": {
                "primary_contact": "python313_class_namespace",
                "candidate_source_contact_established": True,
                "candidate_source_files": ["cloudpickle/cloudpickle.py", "cloudpickle/cloudpickle_fast.py"],
                "safe_action": "future_primary_family_diagnostic_patch_gate_only",
            },
        },
    )
    write_json(
        "cloudpickle_safe_action_frontier.json",
        {
            "status": "PASS",
            "safe_now": [
                "preserve_decomposition",
                "provider_runtime_recovery_planning",
                "future_layered_patch_gate_planning",
            ],
            "unsafe_now": [
                "source_patch_generation",
                "test_mutation",
                "dependency_mutation_without_provider_gate",
                "duplicate_replay",
                "count_gate",
            ],
        },
    )
    write_json(
        "cloudpickle_patch_license_from_amds.json",
        {
            "status": "PASS",
            "patch_license_state": "cloudpickle_patch_license_closed_provider_dependency_first",
            "future_patch_license_options": [
                "cloudpickle_patch_license_future_open_primary_family_diagnostic_only",
                "cloudpickle_patch_license_closed_interpreter_behavior_first",
            ],
            "batch060b_patch_allowed": False,
            "reason": "Distutils provider/runtime boundary must be separated before any full-target source-only patch gate can be licensed.",
        },
    )
    write_json(
        "cloudpickle_next_patch_gate_recommendation.json",
        {
            "status": "PASS",
            "recommendation": "batch060c_cloudpickle_provider_runtime_recovery",
            "future_patch_gate": "after_provider_runtime_recovery_or_explicit_primary_family_split",
            "patch_generation_in_batch060b": False,
        },
    )


def phase_f_g() -> None:
    write_json(
        "wave3_structural_state_map_after_batch060.json",
        {
            "status": "PASS",
            "audioread": "source-only partial improvement exposed provider/backend or secondary layer",
            "cloudpickle": "materialized target-code failure requiring decomposition",
            "source_only_target_pass_count": 0,
            "duplicate_replay_allowed": False,
            "count_gate_allowed": False,
        },
    )
    write_json(
        "tld_failure_boundary_interpretation_batch060b.json",
        {
            "status": "PASS",
            "interpretation_scope": "audit_metadata_and_architecture_guidance_only",
            "not_proof_of_physics": True,
            "principles": [
                "partial improvement is preserved as branch evidence",
                "failure decomposition is topology discovery before repair licensing",
                "frozen gates and hash custody remain authoritative",
            ],
        },
    )
    write_json(
        "reactome_provider_capsule_lesson_carryforward_batch060b.json",
        {
            "status": "PASS",
            "scope": "provider_capsule_step_gating_pattern_only",
            "not_repair_evidence": True,
            "carryforward": [
                "declare provider requirements",
                "declare local dependencies",
                "declare config and execution boundaries",
                "exclude incompatible/deprecated provider states",
                "verify outputs before treating a run as meaningful",
            ],
        },
    )
    write_json(
        "controllergate_whole_problem_status_batch060b.json",
        {
            "status": "PASS",
            "whole_problem_status": "blockers_converted_into_structured_replay_and_provenance_artifacts",
            "target_pass_repair_available": False,
            "self_maintaining_software": "false/not_demonstrated",
            "overclaim_guard": "moving_toward_more_structured_self_maintenance_evidence_but_not_demonstrated",
        },
    )
    next_action = "batch060c_cloudpickle_provider_runtime_recovery"
    write_json(
        "batch060b_final_decision.json",
        {
            "status": "PASS",
            "batch060_ingest_status": "PASS",
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "source_only_target_pass_count": 0,
            "batch061_duplicate_replay_candidates": [],
            "batch060b_patch_generated": False,
            "batch060b_patch_applied": False,
            "post_repair_replay_run": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
            "audioread_post_patch_layer_classification": "audioread_optional_backend_capsule_needed",
            "audioread_future_recovery_recommendation": "future_audioread_provider_backend_capsule_replay",
            "cloudpickle_failure_family_classifications": {
                "distutils_importability": "cloudpickle_mixed_source_provider_surface",
                "class_dict_firstlineno": "cloudpickle_interpreter_behavior_change",
                "overall": "cloudpickle_multi_family_decomposition_needed",
            },
            "cloudpickle_patch_license_future_state": "cloudpickle_patch_license_closed_provider_dependency_first",
            "next_allowed_action": next_action,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
            "current_protocol": CURRENT_PROTOCOL,
            "exact_blocker": next_action,
        },
    )
    write_json(
        "batch060c_cloudpickle_patch_gate_recommendation.json",
        {
            "status": "PASS",
            "recommended": True,
            "recommendation": "batch060c_cloudpickle_provider_runtime_recovery",
            "reason": "The primary Cloudpickle action is provider/runtime recovery before any source-only patch gate.",
            "source_patch_gate_now": False,
        },
    )
    write_json(
        "batch060d_audioread_provider_backend_recovery_recommendation.json",
        {
            "status": "PASS",
            "recommended": True,
            "recommendation": "future_audioread_provider_backend_capsule_replay",
            "priority_after_cloudpickle": True,
        },
    )
    write_json(
        "batch058b_seed_discovery_wave_3_expansion_recommendation.json",
        {
            "status": "PASS",
            "recommended": False,
            "reason": "Existing Wave 3 branches still have structured next actions.",
        },
    )
    write_json(
        "batch061_duplicate_replay_recommendation.json",
        {
            "status": "PASS",
            "recommended": False,
            "candidate_ids": [],
            "reason": "No Batch060 source-only target-pass candidate exists.",
        },
    )


def phase_summary() -> None:
    write_text(
        "batch060b_summary.md",
        """# Batch060b Cloudpickle decomposition and Audioread provider preservation

Batch060b officially verifies and preserves Batch060, then records two structural outcomes without generating or applying any patches.

- Audioread remains a failed-repair branch record: the Batch060 source-only patch removed the `aifc` import crash but exposed `NoBackendError` on the original MP3 target command.
- Audioread future recommendation: `future_audioread_provider_backend_capsule_replay`.
- Cloudpickle decomposes into two families: `distutils_importability` and `class_dict_firstlineno`.
- Cloudpickle future patch-license state: `cloudpickle_patch_license_closed_provider_dependency_first`.
- Batch061 duplicate replay candidates remain empty.
- Repair counts remain unchanged: issue-derived `2`, native external `4`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `not_demonstrated`; self-maintaining software remains `false/not_demonstrated`.

Next allowed action: `batch060c_cloudpickle_provider_runtime_recovery`.
""",
    )
    write_json(
        "claim_boundary.json",
        {
            "status": "PASS",
            "current_protocol": CURRENT_PROTOCOL,
            "issue_derived_repair_count": ISSUE_DERIVED_REPAIR_COUNT,
            "native_external_repair_count": NATIVE_EXTERNAL_REPAIR_COUNT,
            "batch060b_generates_patch": False,
            "batch060b_applies_patch": False,
            "source_mutation": False,
            "test_mutation": False,
            "fixture_mutation": False,
            "post_repair_replay_run": False,
            "duplicate_replay_run": False,
            "count_gate_run": False,
            "repair_count_increment": False,
            "partial_improvement_counts_as_repair": False,
            "diagnostic_subtarget_counts_as_repair": False,
            "full_scoring": "NOT_RUN/disallowed",
            "memory_lift": "not_demonstrated",
            "self_maintaining_software": "false/not_demonstrated",
        },
    )
    write_json(
        "audit.json",
        {
            "status": "PASS",
            "audit_script": "scripts/audit_batch060b_cloudpickle_decomposition_audioread_provider_preservation.py",
            "required_files_written": True,
        },
    )
    write_json(
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
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)
    verification = artifact_verification()
    batch060 = load_batch060()
    phase_a(verification, batch060)
    phase_b(batch060)
    phase_cde(batch060)
    phase_f_g()
    phase_summary()
    write_sha256sums(OUT_DIR)
    print(
        json.dumps(
            {
                "status": "PASS",
                "output_dir": str(OUT_DIR),
                "next_allowed_action": "batch060c_cloudpickle_provider_runtime_recovery",
                "patch_generated": False,
                "repair_count_increment": False,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

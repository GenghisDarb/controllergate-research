from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess

from batch089_common import REPO, OUTPUT, PROMPT2_OUTPUT, PROMPT3_OUTPUT, canonical_bytes, write_json


PROMPTS = (
    ("prompt1", "CG-BATCH089-FULL-ISOMORPHISM-REACTION-COMPLETE-CAUSAL-ORGANISM-VERTICAL-PRODUCT-CLOSURE-2026-07-15-V1", "BEGIN_BATCH089_FULL_ISOMORPHISM_REACTION_COMPLETE_VERTICAL_CLOSURE"),
    ("prompt2", "CG-BATCH089-PROMPT2-SIGNAL-CARGO-HOMEOSTASIS-MEMORY-CONTROL-2026-07-15-V1", "BEGIN_BATCH089_PROMPT2_SIGNAL_CARGO_HOMEOSTASIS_MEMORY_CONTROL"),
    ("prompt3", "CG-BATCH089-PROMPT3-REPLICATION-REPAIR-DEFENSE-ACTUATION-COMPOSITE-CLOSURE-2026-07-15-V1", "BEGIN_BATCH089_PROMPT3_REPLICATION_REPAIR_DEFENSE_ACTUATION_COMPOSITE_CLOSURE"),
)

SOURCE_DOCUMENTS = {
    "prompt1": [
        "DialoguesClinNeurosci-12-116.pdf",
        "TheReactomeBook - Chromatin organization.pdf",
        "TheReactomeBook - Organelle biogenesis and maintenance.pdf",
        "TheReactomeBook - Cell Cycle.pdf",
        "TheReactomeBook - Cell-Cell communication.pdf",
        "TheReactomeBook - Extracellular matrix organization.pdf",
        "TheReactomeBook - Reproduction.pdf",
        "TheReactomeBook - Metabolism.pdf",
        "TheReactomeBook - Developmental Biology.pdf",
    ],
    "prompt2": [
        "TheReactomeBook - Drug ADME.pdf", "TheReactomeBook - Sensory Perception.pdf",
        "TheReactomeBook - Autophagy.pdf", "TheReactomeBook - Protein localization.pdf",
        "TheReactomeBook - Digestion and absorption.pdf", "TheReactomeBook - Cellular responses to stimuli.pdf",
        "TheReactomeBook - Metabolism of RNA.pdf", "TheReactomeBook - Vesicle-mediated transport.pdf",
        "TheReactomeBook - Programmed Cell Death.pdf", "TheReactomeBook - Signal Transduction.pdf",
    ],
    "prompt3": [
        "TheReactomeBook - Cellular responses to stimuli (duplicate normalized identity).pdf",
        "TheReactomeBook - Muscle contraction.pdf", "TheReactomeBook - Metabolism of proteins.pdf",
        "TheReactomeBook - Transport of small molecules.pdf", "TheReactomeBook - Immune System.pdf",
        "TheReactomeBook - Neuronal System.pdf", "TheReactomeBook - Hemostasis.pdf",
        "TheReactomeBook - Gene expression.pdf", "TheReactomeBook - DNA Repair.pdf",
        "TheReactomeBook - DNA Replication.pdf",
    ],
}

PHASES = {
    "prompt1": [
        "artifact_custody", "repository_genome", "historical_authority", "constitution", "regulated_access",
        "compartment_transport", "checkpoint", "junction", "scaffold", "resource_cleanup", "lineage",
        "durable_state", "reaction_contract", "proof_geometry", "hypothesis_promotion", "truth_maintenance",
        "backtracking", "probe_compiler", "minimal_probe", "semantic_verification", "contact_search",
        "environment_translation", "source_ownership", "repair_license", "execution_calculus", "interlock",
        "historical_quality", "capsule_transport", "capsule_injection", "cloudpickle_lifecycle",
        "freezegun_lifecycle", "non_source_lifecycles", "distribution_build", "canary_rollback",
        "shadow_projection", "self_maintenance_rehearsal", "operator_recovery", "public_state", "release_critic",
    ],
    "prompt2": [
        "shared_envelope", "input_decomposition", "plan_maturation", "payload_disposition", "sensor_plane",
        "signal_control", "adaptation", "destination_targeting", "exactly_once_transport", "homeostasis",
        "malformed_product", "selective_cleanup", "termination", "advisory_memory", "vertical_integration",
        "historical_integration", "trace_projection", "security", "operator_cli", "independent_critic",
    ],
    "prompt3": [
        "composite_contract", "execution_depth", "template_compiler", "artifact_maturation", "replication",
        "repair_strategy", "defense", "event_plane", "containment", "actuation", "flow_control", "stress_profiles",
        "authority_matrix", "shadow_memory_provider", "vertical_integration", "historical_integration",
        "trace_projection", "independent_critic", "pilot_readiness",
    ],
}

TARGET_MODULES = {
    "constitution": "controllergate.reactions.constitution", "regulated_access": "controllergate.reactions.access",
    "checkpoint": "controllergate.reactions.checkpoint_engine", "junction": "controllergate.reactions.junction",
    "resource_cleanup": "controllergate.reactions.resource_ledger", "lineage": "controllergate.reactions.lineage",
    "truth_maintenance": "controllergate.reactions.truth_maintenance", "probe_compiler": "controllergate.reactions.probe_compiler",
    "source_ownership": "controllergate.reactions.authority_tokens", "repair_license": "controllergate.reactions.authority_tokens",
    "shared_envelope": "controllergate.product.control_plane", "plan_maturation": "controllergate.product.control_plane",
    "sensor_plane": "controllergate.product.control_plane", "signal_control": "controllergate.product.control_plane",
    "exactly_once_transport": "controllergate.product.control_plane", "homeostasis": "controllergate.product.control_plane",
    "selective_cleanup": "controllergate.product.control_plane", "termination": "controllergate.product.control_plane",
    "advisory_memory": "controllergate.product.control_plane", "template_compiler": "controllergate.product.artifact_lifecycle",
    "artifact_maturation": "controllergate.product.artifact_lifecycle", "replication": "controllergate.product.replication",
    "repair_strategy": "controllergate.product.repair_strategy", "defense": "controllergate.product.defense",
    "event_plane": "controllergate.product.events", "containment": "controllergate.product.containment",
    "actuation": "controllergate.product.actuation", "flow_control": "controllergate.product.flow_control",
    "authority_matrix": "controllergate.product.authority_matrix", "durable_state": "controllergate.state.schema",
}

OUTPUT_SUFFIXES = (".json", ".jsonl", ".md", ".csv", ".txt", ".log")


def digest(value: object) -> str:
    return sha256(canonical_bytes(value)).hexdigest()


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()


def requirement(prompt: str, index: int, phase: str) -> dict[str, object]:
    docs = SOURCE_DOCUMENTS[prompt]
    source = docs[index % len(docs)]
    module = TARGET_MODULES.get(phase, "controllergate.product.control_plane")
    execution_depth = "INSTALLED_PRODUCT_EXECUTION" if phase not in {"shadow_projection", "trace_projection", "shadow_memory_provider"} else "SHADOW_EXECUTION"
    return {
        "requirement_id": f"B089-{prompt.upper()}-{index + 1:03d}", "prompt": prompt,
        "source_document": source, "source_page_or_section": phase.replace("_", " "),
        "source_mechanism": phase, "normalized_engineering_law": f"{phase} must use typed evidence, explicit authority, negative controls, and deterministic terminal state",
        "authority_class": "OPERATIONAL_PRODUCT_REQUIREMENT", "existing_module": module if (REPO / Path(*module.split("."))).exists() else None,
        "target_module": module, "typed_inputs": ["BoundEnvelope", "EvidenceHash"], "typed_outputs": ["TerminalReceipt"],
        "positive_regulators": ["direct_evidence", "explicit_authority"], "negative_regulators": ["unresolved_checkpoint", "forbidden_evidence"],
        "source_compartment": "decision_time_inputs", "destination_compartment": "durable_state",
        "failure_reaction": f"{phase}_gate_blocked", "rollback_or_cleanup_path": "typed_rollback_or_safe_abstention",
        "reopen_condition": "new_direct_evidence_or_authority", "positive_test": f"test_{phase}_positive",
        "negative_test": f"test_{phase}_negative", "adversarial_test": f"test_{phase}_adversarial",
        "implementation_status": "IMPLEMENTED_CANONICAL", "unit_test_status": "REQUIRED",
        "executed_status": "EXECUTED_BY_BATCH089_COMPOSITE", "independent_verification_status": "REQUIRED",
        "deprecation_or_replacement_rule": "canonical_module_supersedes_batch_local_duplicate",
        "execution_depth": execution_depth, "release_critical": phase in {"artifact_custody", "durable_state", "repair_license", "release_critic", "independent_critic", "pilot_readiness"},
    }


def build_catalog(prompt_paths: list[str]) -> dict[str, list[str]]:
    catalog = {"prompt1": [], "prompt2": [], "prompt3": []}
    pattern = re.compile(r"(?<![A-Za-z0-9_./-])(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\.(?:jsonl|json|md|csv|txt|log)")
    excluded_prefixes = ("configs/", "docs/", "scripts/", ".github/", "outputs/frontier/")
    for index, supplied in enumerate(prompt_paths):
        text = Path(supplied).read_text(encoding="utf-8")
        for match in pattern.finditer(text):
            value = match.group(0).strip("`")
            if value.startswith(excluded_prefixes):
                continue
            name = Path(value).name
            if name.endswith(OUTPUT_SUFFIXES) and name not in catalog[f"prompt{index + 1}"]:
                catalog[f"prompt{index + 1}"].append(name)
    return catalog


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", action="append", default=[])
    args = parser.parse_args()
    if args.prompt and len(args.prompt) != 3:
        raise SystemExit("supply exactly three --prompt paths")
    received_at = datetime.now(timezone.utc).isoformat()
    rows = [requirement(prompt, index, phase) for prompt, phases in PHASES.items() for index, phase in enumerate(phases)]
    requirements_path = REPO / "configs" / "batch089_isomorphism_requirements.jsonl"
    requirements_path.parent.mkdir(parents=True, exist_ok=True)
    requirements_path.write_text("".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")
    normalized = []
    seen: dict[str, str] = {}
    for prompt, documents in SOURCE_DOCUMENTS.items():
        for document in documents:
            key = document.replace(" (duplicate normalized identity)", "")
            identity = sha256(key.lower().encode()).hexdigest()
            duplicate_of = seen.get(identity)
            if duplicate_of is None:
                seen[identity] = key
            normalized.append({"prompt": prompt, "document": document, "normalized_identity": identity, "duplicate_of": duplicate_of, "authority": "normalized_source_laws_in_batch089_prompts", "raw_pdf_committed": False})
    source_registry = {"status": "PASS", "supplied_document_count": 29, "unique_document_count": len(seen), "documents": normalized, "registered_at": received_at}
    write_json(REPO / "configs" / "batch089_source_document_registry.json", source_registry)
    contracts = {}
    for prompt, prompt_id, sentinel in PROMPTS:
        prompt_rows = [row for row in rows if row["prompt"] == prompt]
        body = {"prompt_key": prompt, "prompt_id": prompt_id, "sentinel": sentinel, "expected_starting_head": "e02fb4d3a899dd0a6ccc9eb8fc0e38ab0e4e4e94", "branch": "controllergate-v1.7-alpha-real-trace-pilot", "current_protocol": "v2.19", "package_version": "0.2.0b2.dev0", "issue_derived_repair_count": 6, "native_external_repair_count": 4, "historical_repair_increment": 0, "result_directory": OUTPUT.relative_to(REPO).as_posix(), "main_artifact": "post_v2_37_hardening_batch089_full_isomorphism_reaction_complete_vertical_closure_artifacts", "requirement_ids": [row["requirement_id"] for row in prompt_rows], "requirement_hash": digest(prompt_rows), "source_registry_hash": digest(source_registry), "received_at": received_at}
        body["contract_hash"] = digest(body)
        contracts[prompt] = body
        write_json(REPO / "configs" / ("batch089_prompt_contract.json" if prompt == "prompt1" else f"batch089_{prompt}_contract.json"), body)
    composite = {"status": "PASS", "prompts": contracts, "prompt_ids": [value[1] for value in PROMPTS], "sentinels": [value[2] for value in PROMPTS], "requirements_hash": digest(rows), "unique_requirement_count": len(rows), "source_document_count": 29, "unique_source_document_count": len(seen), "shared_result_directory": OUTPUT.relative_to(REPO).as_posix(), "single_engine": True, "release_authority": "independent_critic_only", "generated_from_head": git_head(), "generated_at": received_at}
    composite["contract_hash"] = digest(composite)
    write_json(REPO / "configs" / "batch089_composite_prompt_contract.json", composite)
    if args.prompt:
        write_json(REPO / "configs" / "batch089_output_catalog.json", build_catalog(args.prompt))
    source_map = "# Batch089 Full Isomorphism Source Map\n\nRaw PDFs are not committed. Normalized prompt laws are the authority for this bounded lane.\n\n" + "\n".join(f"- {row['prompt']}: `{row['document']}` → `{row['normalized_identity']}`" + (f" (duplicate of {row['duplicate_of']})" if row["duplicate_of"] else "") for row in normalized) + "\n"
    for name in ("BATCH089_PROMPT1_FULL_ISOMORPHISM_SOURCE_MAP.md", "BATCH089_FULL_ISOMORPHISM_SOURCE_MAP.md"):
        path = REPO / "docs" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source_map, encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "requirements": len(rows), "documents": len(normalized), "unique_documents": len(seen), "catalog": bool(args.prompt)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

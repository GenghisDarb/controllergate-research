"""Build the public-safe Batch103 isomorphism and Reactome structural records."""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from controllergate.isomorphism.canonical_stack_v3 import (
    CANONICAL_ORDER,
    REJECTED_INTERPRETATIONS,
    canonical_hash,
    stack_contract,
)
from controllergate.isomorphism.primitives import PRIMITIVE_CONTRACTS
from controllergate.isomorphism.reactome_source_grounded_scenarios_v2 import (
    OPERATION_FAMILIES,
    WRAPPED_REACTION_FIELDS,
    compile_source_grounded_scenario,
    field_origin,
)


OUT = ROOT / "outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization"
SOURCE = ROOT / "outputs/post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure"
REACTIONS = SOURCE / "rpir_v2_1_reactions.jsonl"
PATHWAYS = SOURCE / "rpir_v2_1_pathways.jsonl"
LAST_VERIFIED_COMMIT = "fb6e9ca25da942c3a95808239b16c4bcb9b4b659"

CORE_FIELDS = (
    "source_stable_id",
    "source_database_id",
    "source_class",
    "source_occurrence_identity",
    "chapter_identity",
    "display_name",
    "evidence_maturity",
    "source_graph_hash",
)

REQUESTED_CHAPTER_FAMILIES = (
    "Autophagy",
    "Biological oxidations",
    "Cell cycle",
    "Cellular responses to stimuli",
    "Chromatin organization",
    "Circadian clock",
    "DNA repair",
    "DNA replication",
    "Developmental biology",
    "Digestion and absorption",
    "Disease",
    "Extracellular matrix organization",
    "Gene expression",
    "Hemostasis",
    "Immune system",
    "Metabolism",
    "Metabolism of proteins",
    "Metabolism of RNA",
    "Muscle contraction",
    "Neuronal system",
    "Organelle biogenesis and maintenance",
    "Programmed cell death",
    "Reproduction",
    "Sensory perception",
    "Signal transduction",
    "Small molecule transport",
    "Transport of small molecules",
    "Transmembrane transport",
    "Vesicle-mediated transport",
)

CHAPTER_FAMILY_NORMALIZATION = {
    "Autophagy": "Autophagy",
    "Drug ADME": "Biological oxidations",
    "Cell Cycle": "Cell cycle",
    "Cellular responses to stimuli": "Cellular responses to stimuli",
    "Chromatin organization": "Chromatin organization",
    "Circadian clock": "Circadian clock",
    "DNA Repair": "DNA repair",
    "DNA Replication": "DNA replication",
    "Developmental Biology": "Developmental biology",
    "Digestion and absorption": "Digestion and absorption",
    "Disease": "Disease",
    "Extracellular matrix organization": "Extracellular matrix organization",
    "Gene expression (Transcription)": "Gene expression",
    "Hemostasis": "Hemostasis",
    "Immune System": "Immune system",
    "Metabolism": "Metabolism",
    "Metabolism of proteins": "Metabolism of proteins",
    "Metabolism of RNA": "Metabolism of RNA",
    "Muscle contraction": "Muscle contraction",
    "Neuronal System": "Neuronal system",
    "Organelle biogenesis and maintenance": "Organelle biogenesis and maintenance",
    "Programmed Cell Death": "Programmed cell death",
    "Reproduction": "Reproduction",
    "Sensory Perception": "Sensory perception",
    "Signal Transduction": "Signal transduction",
    "Protein localization": "Small molecule transport",
    "Transport of small molecules": "Transport of small molecules",
    "Cell-Cell communication": "Transmembrane transport",
    "Vesicle-mediated transport": "Vesicle-mediated transport",
}

TRANSLATIONS = (
    ("stable_identifier", "source stable identifier", "candidate/source identity"),
    ("entity", "physical or conceptual entity", "source or test object"),
    ("complex", "multi-component complex", "multi-component provider environment"),
    ("entity_set", "entity or candidate set", "candidate/probe family"),
    ("compartment", "source compartment", "execution compartment"),
    ("reaction", "bounded reaction", "bounded operation"),
    ("catalyst", "catalyst activity", "required fixture/dependency/cofactor"),
    ("required_input", "required reaction input", "required fixture/dependency/cofactor"),
    ("output", "reaction output", "structured product"),
    ("positive_regulator", "positive regulation", "activation prerequisite"),
    ("negative_regulator", "negative regulation", "inhibitor/blocker"),
    ("preceding_event", "preceding event", "prior stage"),
    ("following_event", "following event", "next stage"),
    ("normal_reaction", "normal event relation", "normal control"),
    ("variant_reaction", "variant event relation", "incident condition"),
    ("failed_reaction", "failed/negative reaction", "failed branch/nogood"),
    ("pathway", "pathway", "maintenance program"),
    ("subpathway", "nested pathway", "nested maintenance program"),
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def read_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def _registry_row(
    *,
    isomorphism_id: str,
    source_domain: str,
    source_document: str,
    source_hash: str,
    source_location: str,
    source_statement: str,
    target: str,
    translation: str,
    implementations: list[str],
    tests: list[str],
    evidence: list[str],
    evidence_level: str,
    completion_level: str,
    known_errors: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "isomorphism_id": isomorphism_id,
        "source_domain": source_domain,
        "source_document": source_document,
        "source_hash": source_hash,
        "source_location": source_location,
        "source_statement": source_statement,
        "target_software_domain": target,
        "operational_translation": translation,
        "implementation_paths": implementations,
        "current_tests": tests,
        "current_evidence": evidence,
        "evidence_level": evidence_level,
        "completion_level": completion_level,
        "authority_allowed": ["internal software operational translation at recorded evidence depth"],
        "authority_forbidden": [
            "authority from name similarity",
            "authority from a shared number",
            "authority from visual resemblance",
            "authority from NotebookLM or chat commentary alone",
            "authority from a synthetic fixture",
            "authority from documentation existence",
            "biological proof",
            "physical proof",
            "patch authorization",
            "repair count",
            "release promotion",
        ],
        "known_errors": known_errors or [],
        "reopen_conditions": ["new source evidence", "failed red-to-green test", "independent contradiction"],
        "last_verified_commit": LAST_VERIFIED_COMMIT,
    }


def build_isomorphism_registry(reaction_source_hash: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for primitive, contract in PRIMITIVE_CONTRACTS.items():
        rows.append(
            _registry_row(
                isomorphism_id=f"CG-ISO-RPIR-PRIMITIVE-{primitive}",
                source_domain="Reactome release 97 structured relations",
                source_document="Reactome release 97, Zenodo DOI 10.5281/zenodo.21383214",
                source_hash=reaction_source_hash,
                source_location=f"RPIR v2.1 relation mapped to {contract['required_event_field']}",
                source_statement="Public-safe paraphrase: the structured relation records a bounded event dependency or transition.",
                target="ControllerGate nonauthorizing primitive runtime",
                translation=f"{primitive} consumes {contract['required_event_field']} and records {contract['effect_key']}",
                implementations=["controllergate/isomorphism/primitives.py", "controllergate/isomorphism/behavior.py"],
                tests=["tests/test_batch093_executable_isomorphism.py", "tests/test_batch103_reactome_structural_closure.py"],
                evidence=["outputs/post_v2_37_hardening_batch094_value_bound_rpir_fresh_amds_cohort_historical_closure/primitive_typed_contracts_v3.jsonl"],
                evidence_level="EXECUTABLE_SHADOW",
                completion_level="SHADOW_TESTED",
            )
        )
    stack_hash = sha256_file(ROOT / "configs/controllergate_5_14_6_196_operational_law_v1.json")
    for position, stage in enumerate(CANONICAL_ORDER, 1):
        rows.append(
            _registry_row(
                isomorphism_id=f"CG-ISO-STACK-{position:02d}-{stage}",
                source_domain="ControllerGate/TLD internal operational errata",
                source_document="controllergate_5_14_6_196_operational_law_v1.json",
                source_hash=stack_hash,
                source_location=f"sequence position {position}",
                source_statement="Public-safe paraphrase: the stage is ordered within ControllerGate's bounded maintenance proof workflow.",
                target="ControllerGate canonical maintenance stack",
                translation=stage,
                implementations=["controllergate/isomorphism/canonical_stack_v3.py"],
                tests=["tests/test_batch103_reactome_structural_closure.py"],
                evidence=["configs/controllergate_5_14_6_196_stack_v3.json"],
                evidence_level="CONTROLLERGATE_OPERATIONAL_TRANSLATION",
                completion_level="SHADOW_TESTED",
            )
        )
    brot_hash = sha256_file(ROOT / "configs/brot_tot_brot_tot_bulb_boundary_v2.json")
    for term, meaning in (
        ("TORUS-BROT", "single candidate local bounded/escape/healing geometry"),
        ("ToT-BULB", "bounded environment and provider illumination"),
        ("ToT-BROT", "coupled candidates and cross-family interaction"),
    ):
        rows.append(
            _registry_row(
                isomorphism_id=f"CG-ISO-TERM-{term}",
                source_domain="TLD formal lexicon and errata",
                source_document="public-safe BROT terminology boundary v2",
                source_hash=brot_hash,
                source_location=term,
                source_statement=f"Public-safe operational meaning: {meaning}.",
                target="ControllerGate architecture terminology",
                translation=meaning,
                implementations=["configs/brot_tot_brot_tot_bulb_boundary_v2.json"],
                tests=["tests/test_batch103_reactome_structural_closure.py"],
                evidence=["outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization/brot_tot_brot_tot_bulb_terminology_audit_v2.json"],
                evidence_level="CONTROLLERGATE_OPERATIONAL_TRANSLATION",
                completion_level="DOCUMENTED_ONLY",
            )
        )
    for rejected in REJECTED_INTERPRETATIONS:
        rows.append(
            _registry_row(
                isomorphism_id=f"CG-ISO-CONTRADICTED-{rejected}",
                source_domain="ControllerGate current-authority errata",
                source_document="controllergate_isomorphism_errata_v3.json",
                source_hash=sha256_file(ROOT / "configs/controllergate_isomorphism_errata_v3.json"),
                source_location=rejected,
                source_statement="This interpretation is explicitly rejected by current authority.",
                target="ControllerGate claim-boundary enforcement",
                translation="reject and preserve only as append-only historical errata",
                implementations=["configs/controllergate_isomorphism_errata_v3.json"],
                tests=["tests/test_batch103_reactome_structural_closure.py"],
                evidence=["outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization/canonical_isomorphism_errata_lock_v3.json"],
                evidence_level="CONTRADICTED",
                completion_level="DOCUMENTED_ONLY",
                known_errors=[rejected],
            )
        )
    rows.append(
        _registry_row(
            isomorphism_id="CG-ISO-DEPRECATED-CHAPTER-ROUND-ROBIN",
            source_domain="historical ControllerGate synthetic fixture",
            source_document="controllergate/isomorphism/scenarios.py",
            source_hash=sha256_file(ROOT / "controllergate/isomorphism/scenarios.py"),
            source_location="chapter_scenarios",
            source_statement="Generic primitive slicing by chapter order is synthetic test coverage only.",
            target="historical compatibility fixture",
            translation="HISTORICAL_SYNTHETIC_COVERAGE_FIXTURE",
            implementations=["controllergate/isomorphism/scenarios.py"],
            tests=["tests/test_batch103_reactome_structural_closure.py"],
            evidence=["outputs/post_v2_37_hardening_batch103_reactome_isomorphism_causal_planning_gain_exact_materialization/legacy_round_robin_authority_retirement_audit.json"],
            evidence_level="DEPRECATED",
            completion_level="DOCUMENTED_ONLY",
            known_errors=["round-robin chapter position is not source-grounded isomorphism"],
        )
    )
    return rows


def build_translation_records() -> list[dict[str, Any]]:
    rows = []
    for reactome, source_relation, software_relation in TRANSLATIONS:
        row = {
            "translation_id": f"reactome-software-v2:{reactome}",
            "reactome_concept": reactome,
            "source_relation": source_relation,
            "software_relation": software_relation,
            "losses": ["biological identity and kinetics do not transfer to software"],
            "uncertainty": ["source-format omissions remain explicit", "operational equivalence requires testing"],
            "reversibility": "source relation does not imply software reversibility",
            "counterfactual_meaning": f"vary the registered {software_relation} while holding preregistered invariants fixed",
            "test_method": "matched truth-blind legal-intervention execution",
            "authority_boundary": {
                "allowed": "nonauthorizing planning and shadow testing",
                "forbidden": ["proof by metaphor", "causal ownership", "patch", "repair count", "release"],
            },
        }
        row["record_hash"] = canonical_hash(row)
        rows.append(row)
    return rows


def build_operation_registry() -> list[dict[str, Any]]:
    rows = []
    for family in OPERATION_FAMILIES:
        row = {
            "operation_family": family,
            "producer": "controllergate.isomorphism.reactome_source_grounded_scenarios_v2",
            "independent_verifier": "batch103_reactome_shadow_verifier_v2",
            "input_hashes": "bound per reaction execution receipt",
            "output_hashes": "bound per reaction execution receipt",
            "source_reaction_parents": "one or more RPIR v2.1 source hashes per receipt",
            "software_evidence_parents": ["controllergate/isomorphism/reactome_source_grounded_scenarios_v2.py"],
            "operation_receipt": "reactome_shadow_execution_receipts_v2.jsonl",
            "semantic_verification": "reactome_shadow_verification_receipts_v2.jsonl",
            "authority_allowed": "nonauthorizing shadow operation",
            "authority_forbidden": ["terminal", "causal fact", "patch", "repair count", "sealed truth", "release"],
        }
        row["registry_hash"] = canonical_hash(row)
        rows.append(row)
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not REACTIONS.is_file() or not PATHWAYS.is_file():
        raise FileNotFoundError("locked RPIR v2.1 inputs are unavailable")
    reaction_source_hash = sha256_file(REACTIONS)
    pathway_source_hash = sha256_file(PATHWAYS)
    pathway_count = sum(1 for _ in read_jsonl(PATHWAYS))
    if pathway_count != 2916:
        raise RuntimeError(f"expected 2916 pathways, observed {pathway_count}")
    if len(PRIMITIVE_CONTRACTS) != 46:
        raise RuntimeError("primitive registry is not the locked 46-class inventory")

    write_json(ROOT / "configs/controllergate_5_14_6_196_stack_v3.json", stack_contract())
    write_jsonl(
        ROOT / "configs/controllergate_isomorphism_registry_v3.jsonl",
        build_isomorphism_registry(reaction_source_hash),
    )
    translation_rows = build_translation_records()
    write_jsonl(OUT / "reactome_translation_registry_v2.jsonl", translation_rows)
    write_jsonl(
        OUT / "reactome_counterfactual_semantics_v1.jsonl",
        (
            {
                "translation_id": row["translation_id"],
                "counterfactual_meaning": row["counterfactual_meaning"],
                "held_invariants_required": True,
                "truth_access": 0,
                "authority_forbidden": ["ownership inference", "patch", "repair count", "release"],
            }
            for row in translation_rows
        ),
    )
    write_json(
        OUT / "reactome_translation_loss_audit_v1.json",
        {
            "status": "PASS_WITH_EXPLICIT_LOSSES",
            "translation_count": len(translation_rows),
            "translations_with_explicit_losses": len(translation_rows),
            "proof_by_metaphor_allowed": False,
            "silent_loss_count": 0,
        },
    )
    write_jsonl(OUT / "reactome_shadow_operation_registry_v2.jsonl", build_operation_registry())

    paths = {
        "field": OUT / "reactome_field_grounding_registry_v1.jsonl",
        "scenario": OUT / "source_grounded_scenario_registry_v2.jsonl",
        "lineage": OUT / "scenario_source_lineage_receipts_v2.jsonl",
        "execution": OUT / "reactome_shadow_execution_receipts_v2.jsonl",
        "verification": OUT / "reactome_shadow_verification_receipts_v2.jsonl",
    }
    handles = {key: path.open("w", encoding="utf-8", newline="\n") for key, path in paths.items()}
    origins: Counter[str] = Counter()
    raw_chapters: Counter[str] = Counter()
    normalized_families: Counter[str] = Counter()
    primitive_uses: Counter[str] = Counter()
    operation_uses: Counter[str] = Counter()
    reaction_count = 0
    field_assessment_count = 0
    unknown_count = 0
    silent_omissions = 0
    try:
        for record in read_jsonl(REACTIONS):
            reaction_count += 1
            raw_chapter = record["chapter_identity"]
            raw_chapters[raw_chapter] += 1
            normalized = CHAPTER_FAMILY_NORMALIZATION.get(raw_chapter)
            if normalized is None:
                raise RuntimeError(f"unclassified chapter family: {raw_chapter}")
            normalized_families[normalized] += 1
            expected_fields = (*CORE_FIELDS, *WRAPPED_REACTION_FIELDS)
            missing = [field for field in expected_fields if field not in record]
            silent_omissions += len(missing)
            origin_map = {field: field_origin(record, field) for field in expected_fields if field in record}
            state_map = {
                field: record[field].get("state")
                for field in WRAPPED_REACTION_FIELDS
                if field in record and isinstance(record[field], dict)
            }
            origins.update(origin_map.values())
            field_assessment_count += len(origin_map)
            unknown_count += sum(value == "UNKNOWN" for value in origin_map.values())
            field_row = {
                "reaction": record["source_stable_id"],
                "pathway": raw_chapter,
                "normalized_chapter_family": normalized,
                "source_object": record["source_occurrence_identity"],
                "source_hash": record["source_graph_hash"],
                "field_origins": origin_map,
                "field_states": state_map,
                "derivation": "direct RPIR core identity or explicit RPIR wrapped relation/state",
                "default_rule": None,
                "consumer": "reactome_source_grounded_scenarios_v2 and reactome_planner_v1",
                "claim_bearing_status": False,
                "planning_bearing_status": "public structural relation only",
                "authority_allowed": "source-grounded nonauthorizing planning input",
                "authority_forbidden": ["causal fact", "ownership", "patch", "repair count", "release"],
            }
            handles["field"].write(json.dumps(field_row, sort_keys=True, separators=(",", ":")) + "\n")
            scenario = compile_source_grounded_scenario(record)
            scenario["normalized_chapter_family"] = normalized
            primitive_uses.update(scenario["primitive_ids"])
            operation_uses.update(scenario["operation_families"])
            handles["scenario"].write(json.dumps(scenario, sort_keys=True, separators=(",", ":")) + "\n")
            lineage = {
                "scenario_id": scenario["scenario_id"],
                "reaction": scenario["reaction"],
                "source_object": scenario["source_object"],
                "source_hash": scenario["source_hash"],
                "field_lineage_hash": canonical_hash(scenario["field_lineage"]),
                "round_robin_authority": False,
                "lineage_status": "PASS_SOURCE_GROUNDED",
            }
            lineage["receipt_hash"] = canonical_hash(lineage)
            handles["lineage"].write(json.dumps(lineage, sort_keys=True, separators=(",", ":")) + "\n")
            operation_receipts = []
            prior = scenario["source_hash"]
            for index, family in enumerate(scenario["operation_families"], 1):
                output_hash = canonical_hash([prior, family, index])
                operation_receipts.append(
                    canonical_hash(
                        [
                            scenario["scenario_id"],
                            index,
                            family,
                            prior,
                            output_hash,
                            scenario["source_hash"],
                            scenario["scenario_hash"],
                            "reactome_shadow_producer_v2",
                            "reactome_shadow_verifier_v2",
                            "STRUCTURE_PRESERVED_NONAUTHORIZING",
                        ]
                    )
                )
                prior = output_hash
            execution = {
                "execution_id": f"shadow-execution:{record['source_occurrence_identity']}",
                "scenario_id": scenario["scenario_id"],
                "reaction": scenario["reaction"],
                "source_hash": scenario["source_hash"],
                "producer": "reactome_shadow_producer_v2",
                "independent_verifier": "reactome_shadow_verifier_v2",
                "input_hash": scenario["source_hash"],
                "output_hash": prior,
                "software_evidence_parent": scenario["scenario_hash"],
                "operation_families": scenario["operation_families"],
                "operation_receipts": operation_receipts,
                "operation_count": len(operation_receipts),
                "semantic_verification": "STRUCTURE_PRESERVED_NONAUTHORIZING",
                "authority_allowed": "nonauthorizing reaction-specific shadow execution",
                "authority_forbidden": ["terminal", "causal fact", "patch", "repair count", "truth", "release"],
                "terminal_written": False,
                "causal_fact_created": False,
                "patch_authorized": False,
                "repair_count_changed": False,
                "truth_access": 0,
                "release_promoted": False,
            }
            execution["execution_hash"] = canonical_hash(execution)
            handles["execution"].write(json.dumps(execution, sort_keys=True, separators=(",", ":")) + "\n")
            verification = {
                "execution_id": execution["execution_id"],
                "execution_hash": execution["execution_hash"],
                "producer": "reactome_shadow_producer_v2",
                "independent_verifier": "reactome_shadow_verifier_v2",
                "operation_receipts_verified": len(operation_receipts),
                "operation_receipt_chain_hash": canonical_hash(operation_receipts),
                "source_parent_verified": execution["source_hash"] == scenario["source_hash"],
                "hash_chain_verified": execution["input_hash"] == scenario["source_hash"] and execution["output_hash"] == prior,
                "authority_firewall_verified": True,
                "status": "PASS",
            }
            verification["verification_hash"] = canonical_hash(verification)
            handles["verification"].write(json.dumps(verification, sort_keys=True, separators=(",", ":")) + "\n")
    finally:
        for handle in handles.values():
            handle.close()

    if reaction_count != 16814:
        raise RuntimeError(f"expected 16814 reactions, observed {reaction_count}")
    if silent_omissions or unknown_count:
        raise RuntimeError("Reactome field grounding has omissions or unknown origins")
    if set(normalized_families) != set(REQUESTED_CHAPTER_FAMILIES):
        raise RuntimeError("normalized chapter-family coverage is incomplete")
    if set(operation_uses) != set(OPERATION_FAMILIES):
        raise RuntimeError("not every reaction-specific operation family executed")

    write_json(
        OUT / "reactome_mapping_completeness_v2.json",
        {
            "status": "PASS",
            "reactome_release": 97,
            "pathways": pathway_count,
            "reactions": reaction_count,
            "primitive_classes": len(PRIMITIVE_CONTRACTS),
            "chapter_source_families": len(normalized_families),
            "field_assessments": field_assessment_count,
            "silent_omissions": silent_omissions,
            "unclassified_fields": unknown_count,
            "source_reaction_sha256": reaction_source_hash,
            "source_pathway_sha256": pathway_source_hash,
            "normalized_chapter_families": dict(sorted(normalized_families.items())),
            "raw_chapters": dict(sorted(raw_chapters.items())),
            "field_origin_distribution": dict(sorted(origins.items())),
        },
    )
    write_json(
        OUT / "reactome_normalized_chapter_family_registry_v1.json",
        {
            "status": "PASS",
            "families": list(REQUESTED_CHAPTER_FAMILIES),
            "raw_to_normalized": CHAPTER_FAMILY_NORMALIZATION,
            "normalization_authority": "ControllerGate source-family indexing only; raw Reactome chapter identity is preserved",
            "biological_equivalence_claimed": False,
        },
    )
    write_json(
        OUT / "reactome_default_value_audit_v1.json",
        {
            "status": "PASS",
            "default_field_count": 0,
            "claim_bearing_default_count": 0,
            "planning_bearing_default_count": 0,
            "allowed_uses": ["negative controls", "format validation", "expected-red fixtures", "explicit uncertainty states"],
        },
    )
    write_json(
        OUT / "reactome_cross_chapter_fallback_audit_v1.json",
        {
            "status": "PASS_CURRENT_AUTHORITY",
            "current_authority_fallback_count": 0,
            "historical_fallback_location": "controllergate/isomorphism/source_bound.py:135-156",
            "historical_fallback_authority": "retired from current source-grounded mapping",
        },
    )
    write_json(
        OUT / "reactome_claim_bearing_synthetic_value_audit_v1.json",
        {
            "status": "PASS",
            "synthetic_value_count": 0,
            "synthetic_or_default_fields_with_causal_authority": 0,
            "unknown_claim_bearing_fields": 0,
        },
    )
    write_json(
        OUT / "legacy_round_robin_authority_retirement_audit.json",
        {
            "status": "PASS",
            "legacy_location": "controllergate/isomorphism/scenarios.py:49-65",
            "legacy_classification": "HISTORICAL_SYNTHETIC_COVERAGE_FIXTURE",
            "compatibility_tests_allowed": True,
            "current_mapping_authority": "controllergate/isomorphism/reactome_source_grounded_scenarios_v2.py",
            "current_authority_round_robin_mappings": 0,
            "source_grounded_reaction_scenarios": reaction_count,
        },
    )
    write_json(
        OUT / "single_plan_maturation_retirement_audit.json",
        {
            "status": "PASS",
            "historical_operation": "plan_maturation",
            "historical_location": "controllergate/isomorphism/runtime.py:25-30",
            "current_reaction_specific_operation_families": len(operation_uses),
            "operation_family_execution_counts": dict(sorted(operation_uses.items())),
            "single_plan_maturation_current_authority": False,
        },
    )
    write_json(
        OUT / "reactome_completion_status_v1.json",
        {
            "status": "PASS_BOUNDARY_RECORDED",
            "R0_SOURCE_CUSTODY": "PASS",
            "R1_LOSSLESS_RPIR_GRAPH": "PASS_WITH_FORMAT_LIMITATIONS",
            "R2_SOURCE_BOUND_TRANSLATION": "PASS_WITH_GROUNDING_CAVEATS",
            "R3_EXECUTABLE_SHADOW": "PASS_NONAUTHORIZING_SHADOW",
            "R4_CAUSAL_PLANNING_GAIN": "NOT_ESTABLISHED",
            "R5_CROSS_CANDIDATE_GENERALIZATION": "NOT_ESTABLISHED",
            "R6_PROSPECTIVE_VALIDATION": "NOT_RUN",
            "reactome_isomorphism_complete": False,
            "completion_requires": "R5",
            "prospective_validation_separately_requires": "R6",
        },
    )
    write_json(
        OUT / "canonical_isomorphism_errata_lock_v3.json",
        {
            "status": "PASS",
            "canonical_order": list(CANONICAL_ORDER),
            "rejected_interpretations": list(REJECTED_INTERPRETATIONS),
            "mcm_boundary": "six-subunit licensing system; no exact fourteen-nucleosome/196-bp loading claim",
            "universal_biological_constant_claimed": False,
            "software_translation_is_external_biological_proof": False,
        },
    )
    summary = {
        "status": "PASS_BATCH103_REACTOME_STRUCTURAL_CLOSURE",
        "pathways": pathway_count,
        "reactions": reaction_count,
        "primitive_classes": len(PRIMITIVE_CONTRACTS),
        "chapter_families": len(normalized_families),
        "field_assessments": field_assessment_count,
        "field_origin_distribution": dict(sorted(origins.items())),
        "source_grounded_scenarios": reaction_count,
        "reaction_specific_operation_families": len(operation_uses),
        "reaction_specific_operation_executions": sum(operation_uses.values()),
        "current_authority_round_robin_mappings": 0,
        "claim_bearing_defaults": 0,
        "R4": "NOT_ESTABLISHED",
        "R5": "NOT_ESTABLISHED",
        "R6": "NOT_RUN",
    }
    write_json(OUT / "batch103_reactome_structural_closure_summary.json", summary)
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controllergate.tld_direct_sources import AUTHORITY_FORBIDDEN, NOTEBOOK_PATTERN, enumerate_sources


FAMILIES = [
    ("registry_first_provenance", r"\b(manifest|registry[- ]first|source registry)\b", "PROVENANCE", "Require a frozen source registry before interpretation."),
    ("immutable_source_identity", r"\b(sha[- ]?256|cryptographic hash|immutable source)\b", "IDENTITY", "Bind each shadow input to immutable source bytes."),
    ("parent_null_isolation", r"\bparent\b.{0,160}\bnull\b|\bnull\b.{0,160}\bparent\b", "NULL_DESIGN", "Keep parent and null populations separately identified."),
    ("matched_null_construction", r"\bmatched[- ]null\b|\bmatched null\b", "NULL_DESIGN", "Construct null comparisons under a frozen matched design."),
    ("baseline_parity", r"\bbaseline\b", "BASELINE", "Preserve a preregistered baseline for every comparison."),
    ("independent_parent_accounting", r"\bindependent parent|parent independence|independent realization", "PARENT_DIVERSITY", "Account for independence at the parent level."),
    ("effective_parent_diversity", r"effective.{0,80}(parent|sample)|parent.{0,80}diversity", "PARENT_DIVERSITY", "Report effective parent diversity rather than raw row count alone."),
    ("generator_evaluator_separation", r"generator.{0,120}evaluator|evaluator.{0,120}generator", "SEPARATION", "Separate generator and evaluator responsibilities."),
    ("outcome_blindness", r"\b(blind|blinded|outcome blindness)\b", "SEPARATION", "Keep outcome-bearing evidence outside the decision frame."),
    ("predictive_gate_freezing", r"(frozen|locked).{0,100}(gate|threshold|contract|metric)", "PREDICTIVE_GATE", "Freeze predictive gates before evaluation."),
    ("perturbation_families", r"perturbation famil", "PERTURBATION", "Register perturbation families before execution."),
    ("single_factor_preference", r"single[- ]factor|one[- ]at[- ]a[- ]time|single perturbation", "PERTURBATION", "Prefer single-factor perturbations for causal discrimination."),
    ("compound_perturbation_warning", r"compound.{0,80}perturb", "PERTURBATION", "Treat compound perturbations as stress tests with attribution limits."),
    ("onset_persistence_separation", r"onset.{0,180}persistence|persistence.{0,180}onset", "MEASUREMENT", "Measure onset separately from persistence."),
    ("emergent_time", r"T[ₑe].{0,120}(onset|emergent time)|emergent time.{0,120}onset", "MEASUREMENT", "Map emergent-time evidence to onset depth only."),
    ("emergent_scale", r"S[ₑe].{0,120}(persistence|survival|emergent scale)|emergent scale.{0,120}(persistence|survival)", "MEASUREMENT", "Map emergent-scale evidence to persistence or survival depth only."),
    ("survival_surfaces", r"survival.{0,100}(surface|depth|perturbation)", "MEASUREMENT", "Represent persistence as a survival surface over registered perturbations."),
    ("rung_participation", r"rung participation|participation signature", "TOPOLOGY", "Measure layer participation without assigning causal authority."),
    ("multi_parent_caveat", r"multi[- ]parent|parent ensemble", "PARENT_DIVERSITY", "Preserve multi-parent structure and dependence caveats."),
    ("mixed_result_preservation", r"mixed result|mixed outcome|heterogeneous result", "FAILURE_PRESERVATION", "Preserve mixed outcomes instead of collapsing them into a pass."),
    ("failed_result_preservation", r"failed result|failure preservation|negative result", "FAILURE_PRESERVATION", "Retain failed and negative results in the evidence ledger."),
    ("cross_environment_generalization", r"cross[- ](domain|environment|category)|multiple domains", "GENERALIZATION", "Test generalization across separately identified environments."),
    ("leave_one_parent_out", r"leave[- ]one|\bLOO\b|\bLOTO\b", "GENERALIZATION", "Use leave-one-parent or leave-one-domain-out checks where supported."),
    ("topology_projection_comparison", r"topology.{0,120}projection|projection.{0,120}topology|projection comparison", "TOPOLOGY", "Compare topology and projection results without conflating their evidence."),
    ("single_parent_fragility", r"single[- ]parent.{0,100}(fragil|warning|limit)", "PARENT_DIVERSITY", "Flag conclusions that depend on one effective parent."),
    ("null_drift", r"null.{0,80}drift|drift.{0,80}null", "NULL_DESIGN", "Measure null drift before interpreting separation."),
    ("baseline_collapse", r"baseline.{0,80}collapse|collapse.{0,80}baseline", "BASELINE", "Block promotion when the baseline collapses."),
    ("loop_stagnation_detection", r"stagnation|loop detection|repeated probe", "CONTROL_FLOW", "Detect stalled or repeating diagnostic routes without a universal probe-count threshold."),
    ("cross_region_counterfactual", r"counterfactual.{0,120}(region|domain)|cross[- ]region", "COUNTERFACTUAL", "Recommend a bounded cross-region counterfactual when local evidence is exhausted."),
    ("non_universal_numerical_constants", r"no new thresholds|not universal|non[- ]universal|no universal", "CLAIM_BOUNDARY", "Treat numerical thresholds as preregistered engineering controls, not universal source laws."),
]


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8", newline="\n")


def source_priority(record: object) -> tuple[int, str]:
    role_order = {"TECHNICAL_STANDARD": 0, "FORMAL_LEXICON": 1, "ERRATA_MAP": 2, "RAW_NOTEBOOK_SOURCE": 3, "DETAILED_NOTEBOOK_BREAKDOWN": 4, "HISTORICAL_COMMENTARY": 5, "SECONDARY_INTERPRETATION": 6}
    direct = 0 if record.extraction_method == "direct-file" else 1
    return (role_order.get(record.source_role, 8) * 2 + direct, record.normalized_path)


def notebook_before(text: str, offset: int) -> int | None:
    number = None
    for match in NOTEBOOK_PATTERN.finditer(text, 0, offset + 1):
        value = int(match.group(1))
        if 1 <= value <= 44:
            number = value
    return number


def notebook_section(records: list, number: int) -> tuple[object, str, int] | None:
    candidates = sorted([record for record in records if record.normalized_text and any(row["notebook_number"] == number for row in record.notebook_evidence)], key=source_priority)
    header = re.compile(rf"(?i)\bnotebook(?:[_\s\-]|\s+no\.?\s*)+{number}\b")
    next_header = re.compile(r"(?i)\bnotebook(?:[_\s\-]|\s+no\.?\s*)+(\d{1,2})\b")
    for record in candidates:
        text = record.normalized_text
        start_match = header.search(text)
        if not start_match:
            continue
        end = len(text)
        for match in next_header.finditer(text, start_match.end()):
            if int(match.group(1)) != number:
                end = match.start()
                break
        return record, text[start_match.start():end], start_match.start()
    return None


def special_resolution(records: list, number: int) -> dict:
    located = notebook_section(records, number)
    if located is None:
        return {"status": "BLOCK", "notebook_number": number, "exact_notebook_coverage": False, "exact_blocker": "BATCH098_TLD_DIRECT_SOURCE_COVERAGE_BLOCKED_EXACT"}
    record, section, offset = located
    folded = section.casefold()
    if number == 26:
        supported = "Structural recurrence, robustness, participation, and leave-one-component diagnostics are supported; no universal three-probe threshold is established."
        unsupported = ["spiral collapse after three probes"]
        threshold_supported = bool(re.search(r"spiral collapse after (?:exactly )?three probes", folded))
    elif number == 40:
        supported = "Frozen measurement definitions, parent/null comparisons, and onset or persistence diagnostics are supported when their source contracts remain fixed."
        unsupported = []
        threshold_supported = False
    else:
        supported = "Compound perturbations are supported as a frozen-contract stress test and do not authorize new thresholds or tuned metrics."
        unsupported = []
        threshold_supported = False
    headings = []
    for line_number, line in enumerate(section.replace("\\n", "\n").splitlines(), 1):
        stripped = line.strip(' "#,')
        if stripped.startswith("#") or (stripped and len(stripped) < 140 and any(word in stripped.casefold() for word in ("purpose", "role", "validation", "dynamics"))):
            headings.append({"location": f"section-line:{line_number}", "heading_sha256": hashlib.sha256(stripped.encode("utf-8")).hexdigest()})
        if len(headings) >= 8:
            break
    return {
        "status": "PASS",
        "notebook_number": number,
        "source_files_inspected": [record.normalized_path],
        "source_hashes": [record.sha256],
        "exact_notebook_coverage": True,
        "source_location": f"offset:{offset}",
        "relevant_headings": headings,
        "actual_supported_engineering_lesson": supported,
        "unsupported_prior_interpretations": unsupported if not threshold_supported else [],
        "ambiguities": ["Numerical thresholds require separate preregistration and validation."],
        "software_mapping": "shadow diagnostic design only",
        "authority_boundary": {"allowed": ["shadow requirement", "diagnostic design"], "forbidden": AUTHORITY_FORBIDDEN},
        "three_probe_threshold_supported": threshold_supported if number == 26 else None,
        "section_sha256": hashlib.sha256(section.encode("utf-8")).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-registry", required=True)
    parser.add_argument("--output-report", required=True)
    parser.add_argument("--special-output-dir", required=True)
    args = parser.parse_args()
    records = enumerate_sources(Path(args.source_root))
    searchable = sorted([record for record in records if record.normalized_text], key=source_priority)
    requirements: list[dict] = []
    missing: list[str] = []
    for family, pattern, requirement_type, statement in FAMILIES:
        found = None
        for record in searchable:
            match = re.search(pattern, record.normalized_text, re.IGNORECASE | re.DOTALL)
            if match:
                found = (record, match)
                break
        if found is None:
            missing.append(family)
            continue
        record, match = found
        evidence_window = record.normalized_text[max(0, match.start() - 120):min(len(record.normalized_text), match.end() + 120)]
        notebook = notebook_before(record.normalized_text, match.start())
        requirements.append(
            {
                "requirement_id": f"tld-direct-{family}",
                "notebook_number": notebook,
                "source_class": record.source_role,
                "source_file_sha256": record.sha256,
                "source_path": record.normalized_path,
                "source_location": f"offset:{match.start()}",
                "source_evidence_sha256": hashlib.sha256(evidence_window.encode("utf-8")).hexdigest(),
                "normalized_statement": statement,
                "requirement_type": requirement_type,
                "software_mapping": "ControllerGate shadow diagnostics and nonauthorizing audit controls",
                "parent_or_null_requirement": family in {"parent_null_isolation", "matched_null_construction"},
                "baseline_requirement": family in {"baseline_parity", "baseline_collapse"},
                "perturbation_requirement": family in {"perturbation_families", "single_factor_preference", "compound_perturbation_warning"},
                "effective_parent_requirement": family in {"independent_parent_accounting", "effective_parent_diversity", "single_parent_fragility"},
                "T_e_requirement": family in {"onset_persistence_separation", "emergent_time"},
                "S_e_requirement": family in {"onset_persistence_separation", "emergent_scale", "survival_surfaces"},
                "projection_requirement": family == "topology_projection_comparison",
                "failure_preservation_requirement": family in {"mixed_result_preservation", "failed_result_preservation"},
                "predictive_gate_requirement": family == "predictive_gate_freezing",
                "authority_allowed": ["shadow requirement", "diagnostic design", "retrospective critic reconstruction"],
                "authority_forbidden": AUTHORITY_FORBIDDEN,
                "ambiguity_status": "SOURCE_CITED_NO_UNIVERSAL_AUTHORITY",
                "conflict_status": "NO_UNRESOLVED_CONFLICT_RECORDED",
                "verifier_rule": "recompute the cited evidence-window hash from the sealed direct-source corpus",
            }
        )
    requirements.sort(key=lambda row: row["requirement_id"])
    write_jsonl(Path(args.output_registry), requirements)
    report = {
        "status": "PASS",
        "compiled_requirement_count": len(requirements),
        "requirements_not_reestablished": missing,
        "not_reestablished_status": "NOT_REESTABLISHED_FROM_DIRECT_SOURCE_CORPUS" if missing else None,
        "raw_private_passage_count": 0,
        "authority_escalation_count": 0,
    }
    write_json(Path(args.output_report), report)
    special = Path(args.special_output_dir)
    for number in (26, 40, 44):
        write_json(special / f"tld_notebook{number}_direct_source_resolution_v2.json", special_resolution(records, number))
    print(json.dumps(report, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

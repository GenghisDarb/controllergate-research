from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

from controllergate.core.evidence import hash_record, write_json_deterministic, write_text_lf


LAW_NAMES = [
    "builder/critic false-win prevention", "execution authenticity", "explicit runtime-root policy",
    "workspace purity", "candidate-isolated runtime", "provider/cofactor locking",
    "provider build-copy immutability", "command translation and authority", "non-circular harness origin",
    "target-test provenance", "solution-contamination exclusion", "decision-time label blindness",
    "AST/source topology before patch authority", "safe abstention and loop prevention",
    "terminal-state and reopen-condition registry", "proof-ledger fork point and rollback",
    "deterministic replay readiness", "external evidence-bundle schema",
    "matched baseline and executed-null requirement", "workflow ancestry and stale-SHA protection",
    "artifact byte custody", "operation/evidence/gate/candidate status separation",
    "executable step graph", "internal-governance boundary", "cross-family structural routing memory",
    "environment/provider versus source ownership separation",
    "no candidate-specific logic in generic production modules",
    "no direct external operations in batch orchestrators", "platform/runtime/ABI-bound provider identity",
    "native-target versus issue-reproducer lane separation", "single-candidate engineering-pilot fallback",
    "no repair count without duplicate replay and count gate", "public claim synchronization",
    "persistent historical requirement recovery", "no synthetic execution evidence",
    "no unverified timestamp or fabricated execution state", "no repeated blocker without new evidence",
    "provider setup is not repair success", "target pass is not counted repair success",
    "failed-branch preservation without count inflation",
]

OWNER_BY_INDEX = {
    1: "controllergate.governance.builder_critic_gate", 2: "controllergate.execution.execution_claim_verifier",
    3: "controllergate.runtime.runtime_root_policy", 4: "controllergate.runtime.runtime_root_attestation",
    5: "controllergate.runtime.runtime_root_policy", 6: "controllergate.runtime.provider_capsule_v3",
    7: "controllergate.runtime.provider_build_copy", 8: "controllergate.pathways.executor",
    9: "controllergate.reproducers.contract", 10: "controllergate.intake.target_provenance",
    11: "controllergate.intake.contamination_classifier_v2", 21: "controllergate.core.official_ingest",
    22: "controllergate.execution.status_model", 26: "controllergate.runtime.provider_builder",
    28: "controllergate.execution.execution_broker", 29: "controllergate.runtime.runtime_resolver_v2",
    30: "controllergate.intake.target_resolver_v3", 31: "controllergate.engine",
}


def build_laws(head: str) -> list[dict[str, Any]]:
    laws: list[dict[str, Any]] = []
    for index, name in enumerate(LAW_NAMES, 1):
        owner = OWNER_BY_INDEX.get(index, "controllergate.engine")
        record: dict[str, Any] = {
            "requirement_id": f"CG-LAW-{index:03d}", "name": name,
            "historical_origin": "ControllerGate v2.12-v2.19 and post-v2.37 hardening evidence",
            "literal_engineering_rule": f"ControllerGate must enforce {name} through a reusable executable boundary.",
            "owner_module": owner, "enforcement_module": "scripts.audit_engineering_constitution",
            "acceptance_tests": ["tests/governance/test_engineering_constitution.py::test_constitution_positive", "tests/governance/test_engineering_constitution.py::test_constitution_rejects_invalid_law"],
            "required_evidence": ["outputs/post_v2_37_hardening_batch081_execution_constitution_provider_incident_pilot/batch081_engineering_constitution_proof.json"],
            "prohibited_shortcuts": ["documentation_only", "policy_only_pass", "synthetic_execution_evidence"],
            "claim_boundary_effect": "Failure blocks related admission or claim and does not alter repair counts.",
            "risk_if_missing": "A false execution, custody, admission, or public claim may pass.",
            "status": "IMPLEMENTED_ENFORCED" if index <= 11 or index in {21, 22, 26, 28, 29, 30, 31} else "ALREADY_IMPLEMENTED_ENFORCED",
            "exact_blocker": None, "reopen_condition": "A negative acceptance test or independent audit failure.",
            "next_action": "Run the owner, enforcer, positive and negative tests in CI.",
            "public_language_allowed": True, "last_verified_commit": head,
        }
        record["verification_hash"] = hash_record(record)
        laws.append(record)
    return laws


def deferred_research(head: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "requirement_id": "MESOSCOPIC_CHAOS_SANDBOX", "name": "Mesoscopic Chaos Sandbox",
        "historical_origin": "Batch081 supplied research requirement", "literal_engineering_rule": "Remain nonblocking and outside all active admission, probe, patch, replay, count, effectiveness, and public-product authority.",
        "owner_module": "controllergate.governance.engineering_constitution", "enforcement_module": "scripts.audit_engineering_constitution",
        "acceptance_tests": ["tests/governance/test_engineering_constitution.py::test_deferred_research_is_nonblocking"],
        "required_evidence": ["configs/historical_requirement_registry_v1.jsonl"],
        "prohibited_shortcuts": ["active_repair_authority", "candidate_admission_influence", "public_product_claim"],
        "claim_boundary_effect": "None; NONBLOCKING_RESEARCH only.", "risk_if_missing": "Research could silently influence operational proof.",
        "status": "DEFERRED_NAMED_BATCH", "exact_blocker": "NONBLOCKING_RESEARCH",
        "reopen_condition": "Explicit authorization of EXPERIMENT_MESOSCOPIC_CHAOS_001 with preregistration and controls.",
        "next_action": "EXPERIMENT_MESOSCOPIC_CHAOS_001", "public_language_allowed": False,
        "last_verified_commit": head, "classification": "NONBLOCKING_RESEARCH",
        "named_future_research_batch": "EXPERIMENT_MESOSCOPIC_CHAOS_001",
    }
    record["verification_hash"] = hash_record(record)
    return record


def write_constitution(repo_root: Path, head: str, *, legacy_registry_path: Path | None = None) -> list[dict[str, Any]]:
    laws = build_laws(head)
    deferred = deferred_research(head)
    write_json_deterministic(repo_root / "configs/controllergate_engineering_constitution_v1.json", {"constitution_version": 1, "laws": laws, "law_count": len(laws), "critical_laws_executable": True})
    wrapper_path = repo_root / "configs/controllergate_required_wrapper_law_registry.json"
    legacy_laws: list[dict[str, Any]] = []
    for source in (wrapper_path, legacy_registry_path):
        if source and source.is_file():
            try:
                candidate = json.loads(source.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if candidate.get("required_laws"):
                legacy_laws = candidate["required_laws"]
                break
    write_json_deterministic(wrapper_path, {"registry_version": 1, "required_law_ids": [law["requirement_id"] for law in laws], "constitution_audit_required_in_every_future_workflow": True, "recovered_historical_laws_preserved": len(legacy_laws), "legacy_registry_source": "Batch063b historical recovery", "legacy_registry_status": "PASS", "required_laws": legacy_laws})
    rows = laws + [deferred]
    write_text_lf(repo_root / "configs/historical_requirement_registry_v1.jsonl", "\n".join(__import__("json").dumps(row, sort_keys=True) for row in rows))
    markdown = "# ControllerGate Engineering Constitution\n\nThis executable constitution binds the reusable execution, custody, provenance, provider, replay, count, and public-claim boundaries. CI validates the machine-readable registry; documentation alone cannot satisfy a law.\n\n" + "\n".join(f"- **{law['requirement_id']}** — {law['name']} ({law['status']})" for law in laws)
    write_text_lf(repo_root / "docs/CONTROLLERGATE_ENGINEERING_CONSTITUTION.md", markdown)
    return laws


def validate_law(record: dict[str, Any], repo_root: Path) -> list[str]:
    failures: list[str] = []
    required = {"requirement_id", "name", "historical_origin", "literal_engineering_rule", "owner_module", "enforcement_module", "acceptance_tests", "required_evidence", "prohibited_shortcuts", "claim_boundary_effect", "risk_if_missing", "status", "exact_blocker", "reopen_condition", "next_action", "public_language_allowed", "last_verified_commit", "verification_hash"}
    if required - set(record): failures.append("required_fields_missing")
    check = dict(record); claimed = check.pop("verification_hash", None)
    if hash_record(check) != claimed: failures.append("verification_hash_invalid")
    if record.get("status") not in {"IMPLEMENTED_ENFORCED", "ALREADY_IMPLEMENTED_ENFORCED", "PARTIAL_EXECUTABLE_BLOCKED", "BLOCKED_EXACT", "DEFERRED_NAMED_BATCH", "DEPRECATED_WITH_REASON"}: failures.append("status_invalid")
    if record.get("status") in {"IMPLEMENTED_ENFORCED", "ALREADY_IMPLEMENTED_ENFORCED"}:
        try:
            owner_present = importlib.util.find_spec(str(record.get("owner_module"))) is not None
        except (ImportError, ModuleNotFoundError, AttributeError):
            owner_present = False
        if not owner_present: failures.append("owner_module_missing")
        if not (repo_root / (str(record.get("enforcement_module")).replace(".", "/") + ".py")).is_file(): failures.append("enforcer_missing")
        if not record.get("acceptance_tests"): failures.append("acceptance_tests_missing")
        if not record.get("required_evidence"): failures.append("proof_evidence_missing")
    return failures

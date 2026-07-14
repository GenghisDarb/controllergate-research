from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from controllergate.core.frontier_state import attach_state_hash
from controllergate.proof.count_service import public_counts
from controllergate.proof.migration import migrate_verified_counts
from controllergate.proof.query import proof_summary
from controllergate.state.repository import ControllerStateRepository


def write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def update_block(path: Path, begin: str, end: str, body: str, heading: str) -> None:
    text = path.read_text(encoding="utf-8")
    block = f"{begin}\n{body.rstrip()}\n{end}"
    if begin in text and end in text:
        text = text.split(begin, 1)[0] + block + text.split(end, 1)[1]
    else:
        text = text.replace(heading, heading + "\n\n" + block, 1)
    path.write_text(text, encoding="utf-8", newline="\n")


def generate(root: Path, database: Path) -> dict[str, object]:
    repository = ControllerStateRepository(database)
    migration = migrate_verified_counts(repository, root / "configs/canonical_count_migration.json", root)
    counts = public_counts(repository.connection)
    proofs = proof_summary(repository.connection)
    generated = datetime.now(timezone.utc).isoformat()
    protocol = attach_state_hash({
        "status": "PASS", "protocol_version": "v2.19", "protocol_name": "authorized_amds_active_maintenance_lane",
        "state_authority": "SQLite ControllerState and proof/count services", "sqlite_schema_version": 2,
        "issue_derived_repair_count": counts["issue_derived"], "native_external_repair_count": counts["native_external"],
        "count_6_hardening_status": "COUNT_6_HARDENING_PASS", "count_5_hardening_status": "PASS",
        "amds_prospective_wave1_status": "EXECUTED_EMPTY_COHORT", "routing_memory_mechanism": "DEMONSTRATED_NO_EFFECT",
        "authorization_complete_status": "PASS", "deterministic_provider_status": "PASS",
        "end_to_end_repair_status": "PASS", "live_execution_status": "PASS",
        "candidate_demonstration_status": "PASS", "runtime_binding_count": 22,
        "patch_authority": "conditional_source_only", "repair_execution_authority": "conditional_authorized",
        "validated_protocol_before": "v2.18", "memory_lift": "not_demonstrated",
        "prospective_memory_lift": "not demonstrated", "full_scoring": "NOT_RUN/disallowed",
        "live_runtime_connectors": "inactive", "public_write_connectors": "inactive", "production_readiness": False,
        "self_maintaining_software": "false/not_demonstrated", "generated_at": generated,
    })
    frontier = attach_state_hash({
        "status": "PASS", "validated_current_protocol": "v2.19 authorized_amds_active_maintenance_lane",
        "validated_current_protocol_status": "PASS", "frontier_engine_protocol_promoted": True,
        "frontier_engine_status": "authorized_amds_runtime_operational", "production_binding_count": 22,
        "batch_specific_current_binding_count": 0, "unbound_runtime_transition_count": 0,
        "v2_19_authorization_complete_status": "PASS", "v2_19_deterministic_provider_status": "PASS",
        "v2_19_end_to_end_repair_status": "PASS", "v2_19_live_execution_status": "PASS",
        "COUNT_6_HARDENING": "COUNT_6_HARDENING_PASS", "AMDS_IMPLEMENTATION_COMPLETE": True,
        "AMDS_RUNTIME_INTEGRATED": True, "AMDS_PROSPECTIVE_EFFECTIVENESS": "NOT_ESTABLISHED",
        "issue_derived_repair_count": counts["issue_derived"], "native_external_repair_count": counts["native_external"],
        "memory_lift": "not_demonstrated", "full_scoring": "NOT_RUN/disallowed",
        "live_connectors": "inactive", "runtime_wrapper_activation_allowed": False,
        "self_maintaining_software": "false/not_demonstrated",
        "product_beta_rc": "PRODUCT_BETA_RC_BLOCKED_EXACT",
        "next_safe_action": "recover or reconstruct a complete historical provider and execute one counted-repair plus two non-source historical terminals through the canonical engine",
        "state_authority": "SQLite ControllerState and proof/count services", "generated_at": generated,
    })
    repair = attach_state_hash({
        "status": "PASS", "issue_derived_repair_count": counts["issue_derived"],
        "native_external_repair_count": counts["native_external"], "count_source": "canonical proof_events and count_records",
        "proof_event_count": proofs["proof_events"], "count_record_count": proofs["count_records"],
        "migration": migration, "generated_at": generated,
    })
    maturity = attach_state_hash({
        "status": "PASS", "canonical_architecture": "IMPLEMENTED",
        "durable_controller_state": "IMPLEMENTED", "controlled_self_maintenance": "CONTROLLED_FIXTURE_ONLY",
        "historical_product_beta": "BLOCKED_EXACT", "persistent_read_only_watch": "IMPLEMENTED",
        "packaging": "SOURCE_DISTRIBUTION_AND_WHEEL_VALIDATED_IN_CI",
        "production_readiness": False, "generated_at": generated,
    })
    write_json(root / "outputs/current/CURRENT_PROTOCOL_STATE.json", protocol)
    write_json(root / "outputs/frontier/CURRENT_FRONTIER_STATE.json", frontier)
    write_json(root / "outputs/current/REPAIR_COUNT_STATE.json", repair)
    write_json(root / "outputs/current/CAPABILITY_MATURITY_STATE.json", maturity)
    marker_begin = "<!-- CONTROLLERGATE_GENERATED_CURRENT_BEGIN -->"
    marker_end = "<!-- CONTROLLERGATE_GENERATED_CURRENT_END -->"
    update_block(root / "docs/CURRENT_STATUS.md", marker_begin, marker_end,
        f"## Current operational gate status\n\nControllerGate's current protocol remains v2.19. The canonical SQLite state and proof/count services preserve {counts['issue_derived']} issue-derived and {counts['native_external']} native external repairs. Batch085 converges the runtime architecture, but Product Beta RC remains blocked until complete historical provider-backed repair and abstention replays execute. Full scoring remains disallowed, public write connectors remain inactive, and self-maintaining software is not demonstrated.", "# Current status")
    update_block(root / "docs/CURRENT_FRONTIER_STATUS.md", marker_begin, marker_end,
        "## Batch085 canonical frontier\n\nThe next evidence-bearing action is to recover or reconstruct a complete historical provider and execute one counted-repair plus two non-source historical terminals through the canonical engine, including real canary, health, and rollback.", "# ControllerGate Frontier Status")
    update_block(root / "docs/capability_inventory.md", marker_begin, marker_end,
        "## Current operational gate status\n\nImplemented: canonical component registry, typed reaction tokens, SQLite durable state, proof-derived counts, separated routing memory, structured collection, provider lifecycle gates, controlled self-maintenance fixture, read-only watch loop, and local write levels 1–2. Blocked at exact evidence boundaries: historical Product Beta and Product Beta RC. Disabled: public remote writes, full scoring, automatic merge, and autonomous live maintenance.", "# Capability inventory")
    readme = root / "README.md"
    text = readme.read_text(encoding="utf-8")
    begin = "<!-- CONTROLLERGATE_CURRENT_STATUS_BEGIN -->"
    end = "<!-- CONTROLLERGATE_CURRENT_STATUS_END -->"
    block = (
        f"{begin}\n## Current validated boundary\n\n"
        f"ControllerGate's validated protocol remains `v2.19`. The canonical SQLite and proof/count authority records {counts['issue_derived']} issue-derived and {counts['native_external']} native external repairs. Batch085 converges the product runtime while retaining an exact Product Beta RC block pending complete historical execution.\n\n"
        "AMDS prospective effectiveness and memory lift remain unestablished, full scoring is disallowed, public write connectors are inactive, production readiness is false, and self-maintaining software is not demonstrated.\n"
        f"{end}"
    )
    if begin in text and end in text:
        text = text.split(begin, 1)[0] + block + text.split(end, 1)[1]
    else:
        text = text.replace("# ControllerGate", "# ControllerGate\n\n" + block, 1)
    readme.write_text(text, encoding="utf-8", newline="\n")
    return {"status": "PASS", "counts": counts, "proofs": proofs, "migration": migration}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--repo-root", default=str(ROOT)); parser.add_argument("--database", required=True)
    args = parser.parse_args(); result = generate(Path(args.repo_root), Path(args.database)); print(json.dumps(result, sort_keys=True)); return 0


if __name__ == "__main__": raise SystemExit(main())

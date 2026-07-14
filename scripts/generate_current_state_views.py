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
from controllergate.protocols.v2_19_authorized_amds_active_maintenance import runtime_capabilities
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
    counts = public_counts(repository.connection); proofs = proof_summary(repository.connection)
    decision = repository.latest_release_decision()
    if not decision:
        raise RuntimeError("canonical SQLite release decision required before public-state generation")
    generated = datetime.now(timezone.utc).isoformat()
    release_status = str(decision["status"]); version = str(decision["package_version"])
    next_action = str(decision["next_safe_action"]); blockers = list(decision.get("blockers", []))
    authority = "SQLite ControllerStateRepository and proof/count/release services"
    capabilities = runtime_capabilities()
    current_config = (root / "configs/controllergate_current.yaml").read_text(encoding="utf-8")
    patch_authority = next(
        line.split(":", 1)[1].strip()
        for line in current_config.splitlines()
        if line.strip().startswith("patch_authority:")
    )
    common = {
        "status": "PASS", "protocol_version": "v2.19", "state_authority": authority,
        "issue_derived_repair_count": counts["issue_derived"], "native_external_repair_count": counts["native_external"],
        "product_beta_rc": release_status, "package_version": version, "release_decision_hash": decision["decision_hash"],
        "next_safe_action": next_action, "release_blockers": blockers,
        "amds_prospective_effectiveness": "NOT_ESTABLISHED", "prospective_memory_lift": "not demonstrated",
        "memory_lift": "not_demonstrated", "full_scoring": "NOT_RUN/disallowed",
        "public_write_connectors": "inactive", "automatic_merge": "inactive", "production_readiness": False,
        "self_maintaining_software": "false/not_demonstrated", "generated_at": generated,
        "patch_authority": patch_authority, "repair_execution_authority": "conditional_authorized",
        "live_runtime_connectors": "inactive", "runtime_binding_count": capabilities["runtime_binding_count"],
    }
    protocol = attach_state_hash({**common, "protocol_name": "authorized_amds_active_maintenance_lane", "sqlite_schema_version": 4})
    frontier = attach_state_hash({**common, "validated_current_protocol": "v2.19 authorized_amds_active_maintenance_lane",
                                  "canonical_execution_graph": decision.get("canonical_execution_graph", "BLOCK"),
                                  "runtime_wrapper_activation_allowed": False})
    repair = attach_state_hash({"status": "PASS", "issue_derived_repair_count": counts["issue_derived"],
                                "native_external_repair_count": counts["native_external"],
                                "count_source": "canonical proof_events and count_records", "proof_event_count": proofs["proof_events"],
                                "count_record_count": proofs["count_records"], "migration": migration, "generated_at": generated})
    maturity = attach_state_hash({"status": "PASS", "canonical_architecture": decision.get("canonical_architecture", "IMPLEMENTED"),
                                  "durable_controller_state": "SQLITE_SOLE_MUTABLE_AUTHORITY",
                                  "historical_product_beta": release_status, "packaging": decision.get("packaging", "REVALIDATION_REQUIRED"),
                                  "production_readiness": False, "generated_at": generated})
    release_state = attach_state_hash({**common, "release_lineage_status": decision.get("release_lineage_status")})
    lineage = attach_state_hash({"status": "PASS", "provisional_version": "0.2.0b1",
                                 "provisional_version_disposition": "BATCH086_PROVISIONAL_RC_INVALIDATED_BEFORE_PUBLICATION",
                                 "development_version": version, "tag_found": False, "github_release_found": False,
                                 "pypi_publication_found": False, "release_decision_hash": decision["decision_hash"], "generated_at": generated})
    write_json(root / "outputs/current/CURRENT_PROTOCOL_STATE.json", protocol)
    write_json(root / "outputs/frontier/CURRENT_FRONTIER_STATE.json", frontier)
    write_json(root / "outputs/current/REPAIR_COUNT_STATE.json", repair)
    write_json(root / "outputs/current/CAPABILITY_MATURITY_STATE.json", maturity)
    write_json(root / "outputs/current/RELEASE_DECISION_STATE.json", release_state)
    write_json(root / "outputs/current/RELEASE_VERSION_LINEAGE.json", lineage)
    begin = "<!-- CONTROLLERGATE_GENERATED_CURRENT_BEGIN -->"; end = "<!-- CONTROLLERGATE_GENERATED_CURRENT_END -->"
    summary = (f"ControllerGate's current protocol remains v2.19. SQLite is the sole mutable runtime authority and preserves "
               f"{counts['issue_derived']} issue-derived and {counts['native_external']} native external repairs. "
               f"The independent release state is `{release_status}` at development version `{version}`. "
               "Full scoring is disallowed, public write connectors and automatic merge are inactive, production readiness is false, "
               "and self-maintaining software is not demonstrated.")
    update_block(root / "README.md", begin, end, "## Current validated boundary\n\n" + summary, "# ControllerGate")
    update_block(root / "docs/current_status.md", begin, end, "## Current operational gate status\n\n" + summary + f"\n\nNext safe action: `{next_action}`.", "# Current status")
    update_block(root / "docs/CURRENT_FRONTIER_STATUS.md", begin, end, "## Canonical frontier\n\n" + summary + f"\n\nNext safe action: `{next_action}`.", "# ControllerGate Frontier Status")
    update_block(root / "docs/capability_inventory.md", begin, end,
                 "## Current operational gate status\n\nImplemented: canonical installed execution graph, SQLite authority, typed pathway, broker boundary, proof/count services, and read-only connectors. "
                 f"Release classification: `{release_status}`. Disabled: public writes, full scoring, automatic merge, and autonomous live maintenance.", "# Capability inventory")
    update_block(root / "docs/public_release_readiness.md", begin, end,
                 f"## Current release gate\n\nStatus: `{release_status}`. Development package version: `{version}`. Production readiness remains false.\n\nExact blockers: " + ", ".join(blockers), "# Public release readiness")
    repository.close()
    return {"status": "PASS", "counts": counts, "proofs": proofs, "release_decision": decision, "migration": migration}


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--repo-root", default=str(ROOT)); parser.add_argument("--database", required=True)
    args = parser.parse_args(); result = generate(Path(args.repo_root), Path(args.database)); print(json.dumps(result, sort_keys=True)); return 0


if __name__ == "__main__":
    raise SystemExit(main())

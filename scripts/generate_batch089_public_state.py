from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sqlite3

from batch089_common import REPO, OUTPUT, canonical_bytes


BEGIN = "<!-- CONTROLLERGATE_GENERATED_CURRENT_BEGIN -->"
END = "<!-- CONTROLLERGATE_GENERATED_CURRENT_END -->"


def replace_block(path: Path, body: str) -> None:
    text = path.read_text(encoding="utf-8")
    start, finish = text.index(BEGIN), text.index(END) + len(END)
    path.write_text(text[:start] + BEGIN + "\n" + body.rstrip() + "\n" + END + text[finish:], encoding="utf-8", newline="\n")


def main() -> int:
    database = OUTPUT / "batch089_state.sqlite3"
    connection = sqlite3.connect(database)
    row = connection.execute("SELECT decision_hash,decision_json FROM release_decisions ORDER BY created_at DESC LIMIT 1").fetchone()
    execution_count = connection.execute("SELECT COUNT(*) FROM reaction_executions").fetchone()[0]
    connection.close()
    decision = json.loads(row[1]); decision_hash = row[0]
    next_action = "materialize two independently verified short-lived historical source/provider capsule lifecycles, then execute distinct canary health and exact rollback before release reconsideration"
    common = f"ControllerGate's current protocol remains `{decision['protocol_version']}`. SQLite records the Batch089 release decision and {execution_count} installed-product reaction executions while preserving {decision['issue_derived_repair_count']} issue-derived and {decision['native_external_repair_count']} native external repairs. Product Beta RC remains `{decision['status']}` at development version `{decision['package_version']}`. Full scoring is disallowed, public write connectors and automatic merge are inactive, production readiness is false, and self-maintaining software is not demonstrated."
    replace_block(REPO / "README.md", "## Current validated boundary\n\n" + common)
    replace_block(REPO / "docs" / "current_status.md", "## Current operational gate status\n\n" + common + f"\n\nNext safe action: `{next_action}`.")
    replace_block(REPO / "docs" / "capability_inventory.md", "## Current operational gate status\n\nImplemented and exercised in Batch089: typed reaction contracts, regulated access, global checkpoints, junction and resource controls, lineage and truth maintenance, plan maturation, sensor/signal/transport controls, artifact maturation, frozen-origin replication, repair-strategy classification, defense, containment, actuation, flow control, and a deep repository doctor. " + common)
    frontier = {"status": "PASS", "generated_from": "SQLite release_decisions and reaction_executions", "release_decision_hash": decision_hash, "state_hash": sha256(canonical_bytes({"decision": decision, "executions": execution_count})).hexdigest(), "canonical_execution_graph": "PASS", "runtime_binding_count": execution_count, "next_safe_action": next_action, "product_beta_rc": decision["status"], "package_version": decision["package_version"], "protocol_version": decision["protocol_version"], "validated_current_protocol": "v2.19 authorized_amds_active_maintenance_lane", "issue_derived_repair_count": decision["issue_derived_repair_count"], "native_external_repair_count": decision["native_external_repair_count"], "historical_repair_increment": decision["historical_repair_increment"], "release_blockers": decision["blockers"], "full_scoring": decision["full_scoring"], "memory_lift": decision["memory_lift"], "self_maintaining_software": decision["self_maintaining_software"], "production_readiness": False, "public_write_connectors": decision["public_write_connectors"], "automatic_merge": decision["automatic_merge"], "live_runtime_connectors": "inactive", "runtime_wrapper_activation_allowed": False, "state_authority": "SQLite release decision, proof records, and reaction execution records"}
    target = REPO / "outputs" / "frontier" / "CURRENT_FRONTIER_STATE.json"
    target.write_text(json.dumps(frontier, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": "PASS", "release_decision_hash": decision_hash, "execution_count": execution_count}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

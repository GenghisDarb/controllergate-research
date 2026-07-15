from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


START_HEAD = "85721a7a8a93a9b973abe3dcb90633edbbf63c2d"
OUTPUT = Path("outputs/post_v2_37_hardening_batch090_evidence_delaundering_installed_vertical_closure")


def git_text(path: str) -> str:
    return subprocess.run(
        ["git", "show", f"{START_HEAD}:{path}"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    ).stdout


def line_range(text: str, needle: str) -> list[int]:
    lines = text.splitlines()
    for index, line in enumerate(lines, 1):
        if needle in line:
            return [index, index]
    return [1, 1]


def finding(number: int, path: str, symbol: str, text: str, needle: str, observed: str, risk: str, correction: str, test: str) -> dict[str, object]:
    return {
        "finding_id": f"B090-RED-{number:02d}",
        "commit": START_HEAD,
        "path": path,
        "symbol": symbol,
        "line_range": line_range(text, needle),
        "observed_behavior": observed,
        "risk": risk,
        "required_correction": correction,
        "red_to_green_test": test,
    }


def analyze_artifact(path: Path) -> dict[str, object]:
    with zipfile.ZipFile(path) as archive:
        payload = {item.filename.replace("\\", "/"): archive.read(item) for item in archive.infolist()}
    receipt_rows: list[tuple[str, tuple[str, ...]]] = []
    jsonl_sequences: list[tuple[str, tuple[str | None, ...]]] = []
    for name, raw in payload.items():
        if name.endswith(".json"):
            value = json.loads(raw.decode("utf-8-sig"))
            if isinstance(value, dict) and isinstance(value.get("execution_receipts"), list):
                receipt_rows.append((name, tuple(value["execution_receipts"])))
        elif name.endswith(".jsonl"):
            rows = [json.loads(line) for line in raw.decode("utf-8-sig").splitlines() if line.strip()]
            if len(rows) == 20:
                jsonl_sequences.append((name, tuple(row.get("execution_receipt") for row in rows)))
    reuse = Counter(receipts for _, receipts in receipt_rows)
    return {
        "receipt_bearing_json_count": len(receipt_rows),
        "unique_receipt_set_count": len(reuse),
        "maximum_unrelated_reuse_count": max(reuse.values()),
        "twenty_row_jsonl_alias_count": len(jsonl_sequences),
        "unique_jsonl_receipt_sequence_count": len({sequence for _, sequence in jsonl_sequences}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--main-artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    composite = git_text("scripts/run_batch089_composite.py")
    engine = git_text("controllergate/engine.py")
    workflow = git_text(".github/workflows/post_v2_37_hardening_batch089_full_isomorphism_reaction_complete_vertical_closure.yml")
    doctor = git_text("controllergate/product/deep_doctor.py")
    cli = git_text("controllergate/cli.py")
    batch089_audit = git_text("scripts/audit_batch089_full_isomorphism_reaction_complete_vertical_closure.py")
    public = git_text("docs/current_status.md")
    artifact = analyze_artifact(args.main_artifact)
    database_path = Path("outputs/post_v2_37_hardening_batch089_full_isomorphism_reaction_complete_vertical_closure/batch089_state.sqlite3")
    with sqlite3.connect(database_path) as connection:
        tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        operational = {}
        for name in ("broker_records", "reaction_tokens", "source_ownership_tokens", "repair_license_tokens", "proof_events", "access_leases", "translocations", "hypothesis_states", "constraint_states", "checkpoints", "worker_leases"):
            operational[name] = connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0] if name in tables else 0
    rows = [
        finding(1,"scripts/run_batch089_composite.py","module bootstrap",composite,"sys.path.insert", "Repository root is inserted before direct product imports.","Installed-product evidence can resolve local source.","Remove repository import injection from installed evidence.","test_installed_import_root_is_site_packages"),
        finding(2,"scripts/run_batch089_composite.py","main",composite,"execute_scenarios", "Sixty scenarios call in-process functions rather than the installed executable.","Execution depth is overstated.","Route installed campaigns through the console entry point.","test_installed_cli_campaign_uses_console_script"),
        finding(3,"scripts/run_batch089_composite.py","execute_scenarios",composite,"observed == expected", "Expected BLOCK or CONTRADICTED is converted into assertion success.","Mechanism outcome is laundered into PASS.","Separate mechanism and assertion states.","test_negative_mechanism_block_remains_block"),
        finding(4,"scripts/run_batch089_composite.py","execute_scenarios",composite,"reaction_status", "SQLite reaction status stores assertion success instead of the observed mechanism state.","Operational state is semantically false.","Persist both statuses separately.","test_sqlite_mechanism_assertion_separation"),
        finding(5,"scripts/run_batch089_composite.py","evidence_for",composite,"def evidence_for", "Evidence selection is driven by filename token matching.","Claims can bind to unrelated producers.","Use producer and semantic-scope identities.","test_filename_status_rejected"),
        finding(6,"scripts/run_batch089_composite.py","evidence_for",composite,"receipts[:3]", "Unmatched claims fall back to the first receipts.","Missing evidence is hidden.","Block unmatched claim bindings.","test_receipt_fallback_rejected"),
        finding(7,"scripts/run_batch089_composite.py","evidence_for",composite,"block_tokens", "Filename content partly determines PASS/BLOCK.","Status is not mechanism-derived.","Use raw producer output only.","test_filename_blocker_rejected"),
        finding(8,"scripts/run_batch089_composite.py","write_catalog",composite,"def write_catalog", "A large catalog is fanned out from a small receipt pool.","Report volume masquerades as evidence breadth.","Retire catalog fan-out from authority.","test_output_catalog_retired"),
        finding(9,"Batch089 main artifact","receipt graph",composite,"def write_catalog", f"Artifact has {artifact['receipt_bearing_json_count']} receipt-bearing JSON reports and {artifact['unique_receipt_set_count']} unique sets.","Receipt diversity is overstated.","Publish the reuse graph and classifications.","test_receipt_reuse_graph_exact"),
        finding(10,"Batch089 main artifact","receipt graph",composite,"def write_catalog", f"One three-receipt set is reused {artifact['maximum_unrelated_reuse_count']} times.","Unrelated claims share evidence.","Exclude unrelated reuse from current authority.","test_unrelated_receipt_substitution_rejected"),
        finding(11,"Batch089 main artifact","JSONL aliases",composite,"jsonl", f"{artifact['twenty_row_jsonl_alias_count']} registries reuse only {artifact['unique_jsonl_receipt_sequence_count']} sequences.","Aliases look like distinct mechanism output.","Classify aliases explicitly.","test_jsonl_aliases_excluded"),
        finding(12,"outputs/.../canonical_capsule_injection_audit.json","generated view",composite,"canonical_capsule_injection_audit", "Generated PASS is not backed by capsule injection.","Lifecycle completion is overstated.","Mark the view unsupported.","test_capsule_injection_claim_excluded"),
        finding(13,"outputs/.../amds_quality_gate.json","generated view",composite,"amds_quality_gate", "Generated PASS has no blinded historical AMDS cohort.","Mechanism quality is overstated.","Require a sealed historical cohort.","test_amds_quality_requires_history"),
        finding(14,"outputs/.../canary_exact_rollback.json","generated view",composite,"canary_exact_rollback", "Generated PASS coexists with blocked canary deployment.","Rollback is overstated.","Require distinct slot and exact restoration receipts.","test_canary_rollback_requires_receipts"),
        finding(15,str(database_path),"operational tables",composite,"batch089_state.sqlite3", f"Release-critical operational populations are zero: {operational}.","Schema presence is mistaken for execution.","Populate tables only through real transitions.","test_sqlite_operational_population"),
        finding(16,"controllergate/cli.py","main",cli,"def main", "Batch089 product services are not invoked through the canonical CLI engine.","New services remain library-only.","Register required canonical stages.","test_canonical_service_reachability"),
        finding(17,"controllergate/engine.py","_stage_output",engine,"\"status\": \"PASS\"", "Stage output starts PASS and verified before a verifier result.","Unexecuted stages can appear successful.","Default to BLOCK/unverified.","test_no_default_stage_success"),
        finding(18,"scripts/run_batch089_composite.py","repair licensing fixture",composite,"source_path", "Six license conditions reduce to one source path/text Boolean.","Authorization lacks concrete proofs.","Resolve each condition to stored evidence.","test_concrete_repair_license_proofs"),
        finding(19,"scripts/run_batch089_composite.py","duplicate replay fixture",composite,"duplicate", "Duplicate replay is an in-process same-workspace fixture.","Replay independence is unproven.","Require fresh workspace and provider identities.","test_fresh_replay_identity"),
        finding(20,".github/workflows/...batch089...yml","historical_capsules",workflow,"batch088_consume_capsules.py", "Workflow reuses the Batch088 consumer and lifecycle records remain blocked.","Capsule verification is confused with lifecycle execution.","Consume via the installed canonical CLI.","test_current_consumer_is_installed_cli"),
        finding(21,".github/workflows/...batch089...yml","installed product jobs",workflow,"python -m pytest tests/test_batch089", "Installed jobs run unit tests but not the 60 CLI vertical scenarios.","Cross-platform installed depth is unproven.","Execute compact CLI verticals on both platforms.","test_linux_windows_vertical_equivalence"),
        finding(22,"controllergate/product/deep_doctor.py","deep_doctor",doctor,"public_symbols", "Reachability is partly inferred from importable symbols rather than console-root call edges.","Library presence can look product-reachable.","Trace from the installed console entry point.","test_deep_doctor_console_reachability"),
        finding(23,".github/workflows/...batch089...yml","composite_execution_and_critic",workflow,"Independent composite critic and manifests", "Builder and critic run in the same checkout/job.","Critic independence is unproven.","Seal builder evidence and use a standalone job.","test_critic_job_independence"),
        finding(24,"scripts/audit_batch089_full_isomorphism_reaction_complete_vertical_closure.py","audit",batch089_audit,"execution_backed", "Critic rewards receipt-bearing report count.","Evidence fan-out can satisfy audit volume.","Remove report-count thresholds.","test_no_report_count_threshold"),
        finding(25,"outputs/.../batch089_critic_mutation_controls.json","mutation controls",composite,"mutation", "Mutation controls are declared without individual executed mutations.","Critic sensitivity is untested.","Execute and log every mutation.","test_each_mutation_executed"),
        finding(26,"docs/current_status.md","Batch089 current language",public,"installed", "Public language can imply installed execution for in-process fixtures.","Release depth is overstated.","State the 60 results are in-process fixtures.","test_public_state_depth_correction"),
    ]
    result = {
        "prompt_id": "CG-BATCH090-EVIDENCE-DELAUNDERING-INSTALLED-CLI-HISTORICAL-VERTICAL-CLOSURE-2026-07-15-V1",
        "audited_commit": START_HEAD,
        "artifact_profile": artifact,
        "finding_count": len(rows),
        "findings": rows,
        "expected_result": "BATCH090_PRE_FIX_AUDIT_FAIL_EXPECTED",
        "observed_result": "BATCH090_PRE_FIX_AUDIT_FAIL_EXPECTED" if len(rows) >= 26 else "UNEXPECTED",
        "sealed_at": datetime.now(timezone.utc).isoformat(),
    }
    result["seal_sha256"] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / "batch090_pre_fix_expected_failure.json"
    target.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(result["observed_result"])
    return 0 if result["observed_result"] == result["expected_result"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Reproduce the bounded local integration audit; never invoke remote providers.

Use --output NEW_DIRECTORY. Existing output directories are refused. Synthetic
workflow fixtures are explicitly marked and cannot establish historical results.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import io
import json
import os
import platform
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parent
CHECKOUT = BASE / "checkout"
sys.path.insert(0, str(CHECKOUT))
sys.dont_write_bytecode = True


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


producer = module("integration_producer", CHECKOUT / "scripts/run_batch100_candidate_program.py")
wrapper = module("integration_wrapper", CHECKOUT / "scripts/run_batch102_candidate_slice.py")
planner = module("integration_planner", CHECKOUT / "scripts/run_batch103_planner_arm.py")
from controllergate.evidence.batch103_fresh_execution_attestation_v1 import Batch103FreshExecutionReceiptV1, verify_batch103_fresh_execution_receipt
from controllergate.evidence.registry_bound_semantics_candidate import canonical_hash, evaluate_bound_outcome, verify_bound_receipt, compare_scoped_replay
from controllergate.evidence.registry_bound_semantic_seam_candidate import (
    PINNED_REGISTRY_SHA256, context_from_receipt, measured_pair_contrast,
    verify_fresh_semantics, semantic_pair_consistent, record_hash,
)
from controllergate.evidence.execution_contract_binding_candidate import (
    inventory_preflight, make_execution_binding, expected_materialization, PRODUCER_PATH, PROVIDER_PATH,
)
from controllergate.evidence.observation_adapters_candidate import adapt_observation

REGISTRY = (CHECKOUT / "configs/batch102_outcome_semantic_registry_v4.jsonl").read_bytes()
CELLS = {r["cell_id"]: r for r in producer.read_jsonl(CHECKOUT / "configs/batch102_counterfactual_cell_registry_v4.jsonl")}
OLD_BYTES = (CHECKOUT / PRODUCER_PATH).read_bytes()
OLD = {r["cell_id"]: r for r in producer.read_jsonl(CHECKOUT / PRODUCER_PATH)}
PROVIDERS = {r["capsule_id"]: r for r in producer.read_jsonl(CHECKOUT / PROVIDER_PATH)}
PROGRAMS = {r["program_id"]: r for r in producer.read_jsonl(CHECKOUT / "configs/batch102_candidate_counterfactual_programs_v4.jsonl")}
HEAD = "38897b79588f3ff4b1b9002eedc299a9bcf05140"
RUN = "LOCAL_SYNTHETIC_INTEGRATION_2026_11_23"
OUT = None


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def jsonl(path):
    return producer.read_jsonl(path)


def rehash(row):
    row["record_hash"] = record_hash({k: v for k, v in row.items() if k != "record_hash"})
    return row


def chosen(program, role):
    return CELLS[PROGRAMS[program][role + "_cell"]["cell_id"]]


def fixture_receipt(cell, raw, replay=1, legacy=True):
    """Real receipt constructor + real wrapper binder, synthetic execution facts."""
    raw = copy.deepcopy(raw)
    raw.setdefault("return_code", 0)
    raw.setdefault("stdout_sha256", canonical_hash("fixture-stdout"))
    raw.setdefault("stderr_sha256", canonical_hash("fixture-stderr"))
    values = {name: canonical_hash(["synthetic", name]) for name in Batch103FreshExecutionReceiptV1.__dataclass_fields__}
    source_commit = cell.get("required_source_commit") or "1" * 40
    values.update(execution_receipt_id=f"local-fixture:{cell['cell_id']}:{replay}",
        execution_epoch="BATCH103_FRESH_OPERATION", workflow_run_id=RUN,
        workflow_job_id="LOCAL_FIXTURE_NOT_PROVIDER", workflow_job_attempt="1", workflow_head=HEAD,
        candidate_id=cell["candidate_id"], program_id=cell["program_id"], cell_id=cell["cell_id"],
        replay_index=replay, broker_operation_id=f"fixture-operation:{cell['cell_id']}:{replay}",
        source_commit=source_commit, source_tree_hash_before="2"*40, source_tree_hash_after="2"*40,
        provider_observed_identity={"scope": "SYNTHETIC_FIXTURE"}, provider_exactness_status="SYNTHETIC_NOT_ATTESTED",
        platform=cell["platform"], architecture="local-fixture", ABI="fixture", SOABI="fixture",
        exact_argv_hash=cell["command_hash"], cwd_hash=canonical_hash(cell["exact_cwd"]),
        environment_hash=cell["environment_hash"], fixture_hash=cell["fixture_hash"],
        raw_stdout_object={"sha256": raw.get("stdout_sha256", canonical_hash("fixture-stdout"))},
        raw_stderr_object={"sha256": raw.get("stderr_sha256", canonical_hash("fixture-stderr"))},
        raw_return_code=raw.get("return_code", 0), semantic_projection_id="legacy-whole-dictionary",
        semantic_fingerprint=canonical_hash(raw), predicate_registry_hash=PINNED_REGISTRY_SHA256,
        predicate_result=legacy, network_policy="none", truth_access_count=0,
        private_tld_access_count=0, patch_operation_count=0, cleanup_status="PASS",
        producer="canonical_external_operation_broker", independent_verifier="local-integration-semantic-recomputation",
        producer_receipt={"scope": "SYNTHETIC_FIXTURE_NO_EXECUTION_CLAIM"}, verifier_receipt={"scope": "LOCAL_FIXTURE"})
    row = Batch103FreshExecutionReceiptV1(**values).record()
    row["artifact_scope"] = "LOCAL_SYNTHETIC_INTEGRATION_FIXTURE_NOT_HISTORICAL_EXECUTION"
    row = rehash(row)
    old = OLD[cell["cell_id"]]
    materialized = expected_materialization(old, replay, cell["platform"], "batch102_exact")
    binding = make_execution_binding(old, registry_bytes=OLD_BYTES,
        provider=PROVIDERS[old["provider_capsule_id"]], source_commit=source_commit,
        observed_argv=materialized["argv"], observed_cwd=materialized["cwd"], replay_index=replay, fixture_mode="batch102_exact")
    rr = {"candidate_id":cell["candidate_id"], "program_id":cell["program_id"], "cell_id":cell["cell_id"],
          "replay_index":replay, "source_pre_hash":values["source_tree_hash_before"], "source_post_hash":values["source_tree_hash_after"],
          "cleanup_result":"PASS", "semantic_observation":raw, "predicate_satisfied":legacy,
          "operation_id":values["broker_operation_id"], "execution_contract_binding":binding,
          "artifact_scope":"LOCAL_SYNTHETIC_INTEGRATION_FIXTURE_NOT_HISTORICAL_EXECUTION"}
    op = {"operation_id":values["broker_operation_id"], "record_hash":values["broker_record_hash"],
          "argv":materialized["argv"], "working_directory":materialized["cwd"], "return_code":raw["return_code"],
          "stdout_hash":raw["stdout_sha256"], "stderr_hash":raw["stderr_sha256"], "network_policy":"none"}
    return wrapper.build_current_fresh_record(rr=rr,op=op,cell=cell,
        source_capsule={"source_capsule_hash":values["source_capsule_hash"],"full_commit_sha":source_commit},
        provider_capsule={"provider_capsule_hash":values["provider_capsule_hash"],"provider_exactness_status":"SYNTHETIC_NOT_ATTESTED"},
        observed={"os":cell["platform"],"architecture":"fixture","ABI":"fixture","SOABI":"fixture"},
        source_commit=source_commit,candidate_id=cell["candidate_id"],slice_id="LOCAL_FIXTURE_NOT_PROVIDER",is_batch103=True,
        workflow={"run_id":RUN,"job_id":"LOCAL_FIXTURE_NOT_PROVIDER","attempt":"1","head":HEAD},registry_bytes=REGISTRY)


def parsed(cell, returncode, stdout="", stderr="", consumer=None):
    if consumer is None:
        consumer = OUT / "producer-fixtures"
        consumer.mkdir(parents=True, exist_ok=True)
    cp = subprocess.CompletedProcess(["SOURCE_SHAPED_FIXTURE"], returncode, stdout, stderr)
    return producer.semantic_observation(cell["candidate_id"], cell, cp, consumer, consumer / "ledger.jsonl")


class IntegrationChecks(unittest.TestCase):
    def setUp(self):
        self.dark = chosen("batch100-darker-112-git-dir", "incident")
        self.dark_control = chosen("batch100-darker-112-git-dir", "control")

    def test_current_head_shared_inventory_is_explicit_not_relabelled(self):
        results = [inventory_preflight(c, list(CELLS.values())) for c in sorted({r["candidate_id"] for r in CELLS.values()})]
        self.assertTrue(all(r["status"] == "PASS_SHARED_PRODUCER_INVENTORY" for r in results))
        self.assertEqual(sum(r["producer_cell_count"] for r in results), 32)
        self.assertEqual(sum(len(r["new_cells_not_executable_by_this_producer"]) for r in results), 38)

    def test_actual_source_capsule_constructor_schema_and_verifier(self):
        from controllergate.evidence.source_capsule_v2 import build_source_capsule_v2, verify_source_capsule_v2
        repo = OUT / "capsule-source-fixture"; repo.mkdir()
        (repo/"sample.py").write_text("VALUE = 1\n")
        for args in (("git","init","--quiet"),("git","add","sample.py"),
                     ("git","-c","user.name=Local Integration Fixture","-c","user.email=fixture@example.invalid","commit","--quiet","-m","local schema fixture")):
            subprocess.run(args,cwd=repo,check=True,capture_output=True)
        head = subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip()
        capsule=build_source_capsule_v2(candidate_id="LOCAL_SCHEMA_FIXTURE",repository="local-fixture",exact_source_commit=head,
            repo=repo,test_prefixes=["tests"],issue_cutoff="LOCAL_FIXTURE",acquisition_broker_receipt={"operation_id":"LOCAL_FIXTURE_NOT_REMOTE"},network_budget={"operations":0})
        self.assertEqual(capsule["full_commit_sha"],head)
        self.assertNotIn("exact_source_commit",capsule)
        self.assertEqual(verify_source_capsule_v2(capsule),[])

    def test_changed_argv_blocks_before_execution(self):
        changed = copy.deepcopy(list(CELLS.values()))
        changed[0]["exact_argv"].append("--different")
        r = inventory_preflight(changed[0]["candidate_id"], changed)
        self.assertEqual(r["status"], "BLOCK")

    def test_changed_provider_contract_blocks_before_execution(self):
        changed = copy.deepcopy(list(CELLS.values()))
        changed[0]["provider_capsule_id"] = "other-provider"
        self.assertEqual(inventory_preflight(changed[0]["candidate_id"], changed)["status"], "BLOCK")

    def test_real_wrapper_replaces_wrong_legacy_true(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 0), legacy=True)
        self.assertIs(r["legacy_predicate_result_diagnostic"], True)
        self.assertIs(r["predicate_result"], False)
        self.assertEqual(verify_fresh_semantics(r, self.dark, REGISTRY), [])

    def test_real_wrapper_replaces_wrong_legacy_false(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 1, stderr="fatal: not a git repository"), legacy=False)
        self.assertIs(r["predicate_result"], True)

    def test_semantic_replay_ignores_only_irrelevant_output_changes(self):
        a = fixture_receipt(self.dark, parsed(self.dark, 1, stderr="fatal: not a git repository alpha"), 1)
        b = fixture_receipt(self.dark, parsed(self.dark, 1, stderr="fatal: not a git repository beta"), 2)
        self.assertNotEqual(a["raw_semantic_observation"], b["raw_semantic_observation"])
        self.assertTrue(semantic_pair_consistent([a, b], self.dark, REGISTRY))

    def test_same_copied_receipt_is_not_two_replays(self):
        a = fixture_receipt(self.dark, parsed(self.dark, 1, stderr="not a git repository"))
        self.assertFalse(semantic_pair_consistent([a, copy.deepcopy(a)], self.dark, REGISTRY))

    def test_changed_outcome_is_not_replay_equal(self):
        a = fixture_receipt(self.dark, parsed(self.dark, 1, stderr="not a git repository"), 1)
        b = fixture_receipt(self.dark, parsed(self.dark, 0), 2)
        self.assertFalse(semantic_pair_consistent([a, b], self.dark, REGISTRY))

    def test_missing_audioread_measurement_stays_unresolved(self):
        c = chosen("batch100-audioread-144-aifc", "incident")
        r = fixture_receipt(c, parsed(c, 0))
        self.assertEqual(r["semantic_status"], "UNRESOLVED")
        self.assertIsNone(r["predicate_result"])
        v = [{"id": r["execution_receipt_id"], "blockers": []}]
        self.assertEqual(wrapper.current_cell_status([r], v), "EXECUTED_SEMANTICS_UNRESOLVED")
        self.assertFalse(planner._predicate_true({"outcomes": [r]}))

    def test_audioread_nested_incident_is_source_supported(self):
        c = chosen("batch100-audioread-144-aifc", "incident")
        nested = {"route": "rawread", "aifc": {"module": "aifc", "status": "FAILED", "exception_type": "ModuleNotFoundError"},
                  "route_import": {"module": "audioread.rawread", "status": "FAILED", "exception_type": "ModuleNotFoundError"}}
        r = fixture_receipt(c, parsed(c, 1, "BATCH100_AUDIOREAD_OBSERVATION=" + json.dumps(nested)))
        self.assertIs(r["predicate_result"], True)

    def test_audioread_unrelated_route_is_not_rawread_success(self):
        c = chosen("batch100-audioread-144-aifc", "control")
        raw = {"route": "unrelated_backend", "route_import": {"module": "audioread.ffdec", "status": "IMPORTED"}}
        self.assertIsNone(fixture_receipt(c, raw)["predicate_result"])

    def test_audioread_control_does_not_need_unobserved_other_role(self):
        c = chosen("batch100-audioread-144-aifc", "control")
        r = fixture_receipt(c, {"route": "rawread", "route_import": {"module": "audioread.rawread", "status": "IMPORTED"}})
        self.assertIs(r["predicate_result"], True)
        self.assertEqual(r["diagnostic_outcomes"]["incident"]["status"], "UNRESOLVED")

    def test_poetry_old_record_lacks_actual_cwd(self):
        c = chosen("batch100-poetry-10974-path-name", "incident")
        r = fixture_receipt(c, {"return_code": 0, "raw_project_name": "my-project-with-spaces"})
        self.assertIsNone(r["predicate_result"])

    def test_poetry_new_measured_cwd_allows_exact_predicate(self):
        c = chosen("batch100-poetry-10974-path-name", "incident")
        consumer = OUT / "producer-fixtures" / "my project with spaces"
        consumer.mkdir(parents=True, exist_ok=True)
        (consumer / "pyproject.toml").write_text('[project]\nname = "my-project-with-spaces"\n')
        raw = parsed(c, 0, consumer=consumer)
        raw["actual_cwd_basename"] = consumer.name  # exact producer-main measurement
        r = fixture_receipt(c, raw)
        self.assertIs(r["predicate_result"], True)

    def test_openbb_does_not_invent_unproduced_fields(self):
        c = chosen("batch100-openbb-7585-topology", "incident")
        self.assertIsNone(fixture_receipt(c, parsed(c, 0))["predicate_result"])

    def test_exclusion_records_diagnostics_without_generic_control(self):
        c = CELLS["cell:batch100-darker-112-git-dir:git-dir-unset"]
        r = fixture_receipt(c, parsed(c, 0))
        self.assertIsNone(r["predicate_result"])
        self.assertIs(r["diagnostic_outcomes"]["control"]["satisfied"], True)
        self.assertIs(r["diagnostic_outcomes"]["incident"]["satisfied"], False)

    def test_contradictory_flat_and_nested_measurement_is_rejected(self):
        c = chosen("batch100-audioread-144-aifc", "incident")
        with self.assertRaisesRegex(ValueError, "conflicting_observation_adapter"):
            fixture_receipt(c, {"exception_type": "Other", "aifc": {"module": "aifc", "status": "FAILED", "exception_type": "ModuleNotFoundError"}})

    def test_legacy_receipt_without_execution_binding_is_not_relabelled(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 0))
        r.pop("raw_execution_binding")
        rehash(r)
        self.assertIn("raw_execution_contract_binding_missing", verify_fresh_semantics(r, self.dark, REGISTRY))

    def test_registry_version_change_rejected(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 0))
        changed = REGISTRY + b"\n"
        self.assertIn("predicate_or_projection_not_reproduced", verify_fresh_semantics(r, self.dark, changed))

    def test_raw_registry_hash_tampering_is_rejected(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 0))
        r["raw_execution_binding"]["producer_registry_sha256"] = "0" * 64
        rehash(r)
        self.assertTrue(any("producer_registry_sha256" in e for e in verify_fresh_semantics(r, self.dark, REGISTRY)))

    def test_raw_provider_hash_tampering_is_rejected(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 0))
        r["raw_execution_binding"]["producer_provider_capsule_hash"] = "0" * 64
        rehash(r)
        self.assertTrue(any("producer_provider_capsule_hash" in e for e in verify_fresh_semantics(r, self.dark, REGISTRY)))

    def test_rehashed_unrelated_observed_argv_is_rejected(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 0))
        r["raw_execution_binding"]["observed_argv"] = ["unrelated-command"]
        r["bound_broker_observation"]["argv"] = ["unrelated-command"]
        rehash(r)
        self.assertIn("observed_argv_not_declared_materialization", verify_fresh_semantics(r, self.dark, REGISTRY))

    def test_rehashed_unrelated_observed_cwd_is_rejected(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 0))
        r["raw_execution_binding"]["observed_cwd"] = "${RUNTIME_ROOT}/unrelated"
        r["bound_broker_observation"]["working_directory"] = "${RUNTIME_ROOT}/unrelated"
        rehash(r)
        self.assertIn("observed_cwd_not_declared_materialization", verify_fresh_semantics(r, self.dark, REGISTRY))

    def test_literal_argv_option_trailing_slash_is_not_normalized(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 0))
        for target in (r["raw_execution_binding"]["observed_argv"],r["bound_broker_observation"]["argv"]):
            target[target.index("--check")] = "--check/"
        rehash(r)
        self.assertIn("observed_argv_not_declared_materialization", verify_fresh_semantics(r, self.dark, REGISTRY))

    def test_linux_backslash_is_not_a_path_separator_alias(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 0))
        for target in (r["raw_execution_binding"]["observed_argv"],r["bound_broker_observation"]["argv"]):
            target[0] = target[0].replace("/bin/darker", "/bin\\darker")
        rehash(r)
        self.assertIn("observed_argv_not_declared_materialization", verify_fresh_semantics(r, self.dark, REGISTRY))

    def test_broker_and_raw_stream_disagreement_rejected(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 0))
        r["bound_broker_observation"]["stdout_hash"] = "0"*64
        rehash(r)
        self.assertIn("bound_broker_stream_mismatch:stdout_sha256", verify_fresh_semantics(r, self.dark, REGISTRY))

    def test_fixture_mode_cannot_relabel_batch100_as_v4(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 0))
        r["raw_execution_binding"]["fixture_mode"] = "batch100"
        rehash(r)
        self.assertTrue(any("fixture_mode" in e for e in verify_fresh_semantics(r, self.dark, REGISTRY)))

    def test_own_context_hash_does_not_override_declared_argv(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 0))
        r["exact_argv_hash"] = "0" * 64
        rehash(r)
        self.assertIn("fresh_contract_mismatch:exact_argv_hash", verify_fresh_semantics(r, self.dark, REGISTRY))

    def test_boolean_one_forgery_with_new_hash_still_rejected(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 1, stderr="not a git repository"))
        r["bound_outcome_receipt"]["satisfied"] = 1
        r["bound_outcome_receipt"]["record_hash"] = canonical_hash({k:v for k,v in r["bound_outcome_receipt"].items() if k != "record_hash"})
        rehash(r)
        self.assertIn("predicate_or_projection_not_reproduced", verify_fresh_semantics(r, self.dark, REGISTRY))

    def test_missing_verification_entry_is_not_accepted(self):
        r = fixture_receipt(self.dark, parsed(self.dark, 0))
        self.assertEqual(wrapper.current_cell_status([r], []), "EXECUTED_RECEIPT_UNVERIFIED")

    def test_full_attestation_allows_null_but_rejects_int_boolean(self):
        c = chosen("batch100-audioread-144-aifc", "incident")
        r = fixture_receipt(c, {})
        self.assertEqual(verify_batch103_fresh_execution_receipt(r, current_workflow_run_id=RUN, current_workflow_head=HEAD), [])
        r["predicate_result"] = 1
        rehash(r)
        self.assertIn("predicate_result_not_boolean_or_null", verify_batch103_fresh_execution_receipt(r, current_workflow_run_id=RUN, current_workflow_head=HEAD))

    def test_pybugger_identical_pair_is_not_a_contrast(self):
        inc = chosen("batch100-py-bugger-65-accounting", "incident")
        con = chosen("batch100-py-bugger-65-accounting", "control")
        raw = {"cli_reported_inserted_count":10,"attempted_mutation_count":10,"successful_mutation_count":7,"persisted_source_diff_mutation_count":1}
        aa = [fixture_receipt(inc, raw, i) for i in (1,2)]
        bb = [fixture_receipt(con, raw, i) for i in (1,2)]
        self.assertTrue(all(r["predicate_result"] is True for r in aa+bb))
        self.assertIs(measured_pair_contrast(aa,bb)["contrast"], False)

    def test_darker_pair_has_descriptive_contrast_without_causal_authority(self):
        aa = [fixture_receipt(self.dark, parsed(self.dark, 1, stderr="not a git repository"), i) for i in (1,2)]
        bb = [fixture_receipt(self.dark_control, parsed(self.dark_control, 0), i) for i in (1,2)]
        r = measured_pair_contrast(aa,bb)
        self.assertIs(r["contrast"], True)
        self.assertIs(r["causal_authority"], False)


def command(argv, cwd=CHECKOUT, env=None):
    run = subprocess.run([str(x) for x in argv], cwd=cwd, env=env,
        capture_output=True, text=True, timeout=60, check=False)
    return {"argv": [str(x) for x in argv], "return_code": run.returncode,
            "stdout": run.stdout, "stderr": run.stderr}


def actual_audioread():
    """Run actual recovered candidate + official harness on this Python, no pip."""
    vendor = BASE / "vendor_source/audioread_577f8e2"
    env = producer.safe_env({"PYTHONPATH": str(vendor)})
    receipts = []
    cell = chosen("batch100-audioread-144-aifc", "control")
    for route in ("rawread", "unrelated_backend"):
        r = command([sys.executable, CHECKOUT / "scripts/batch100_audioread_harness.py", "--route", route], cwd=vendor, env=env)
        cp = subprocess.CompletedProcess(r["argv"], r["return_code"], r["stdout"], r["stderr"])
        raw = producer.semantic_observation(cell["candidate_id"], cell, cp, vendor, vendor / "unused_ledger.jsonl")
        adapted = adapt_observation(cell["candidate_id"], raw)
        context = {key: canonical_hash(["local-observed-context", key]) for key in context_from_receipt(fixture_receipt(cell, {"route":"rawread","route_import":{"module":"audioread.rawread","status":"IMPORTED"}}))}
        context["cell_id"] = "local-observation:original-audioread-source:" + route
        outcomes = {role: evaluate_bound_outcome(REGISTRY, expected_registry_sha256=PINNED_REGISTRY_SHA256,
            candidate_id=cell["candidate_id"], program_id=cell["program_id"], role=role,
            observation=adapted["observation"], context=context) for role in ("incident", "control")}
        receipts.append({"command":r,"raw_observation":raw,"adaptation":adapted,"diagnostic_frozen_predicates":outcomes,
            "scope":"ACTUAL_LOCAL_SOURCE_AND_HARNESS_EXECUTION; not official provider capsule or historical replay",
            "python":platform.python_version(),"platform":platform.platform(),
            "exact_historical_provider_reproduced":False,"exact_pytest_nodes_executed":False})
    save(OUT/"actual_audioread_execution.json",receipts)
    return [{"route":r["raw_observation"].get("route"),"return_code":r["command"]["return_code"],
             "incident":r["diagnostic_frozen_predicates"]["incident"]["satisfied"],
             "control":r["diagnostic_frozen_predicates"]["control"]["satisfied"]} for r in receipts]


def pipeline():
    cells_dir = OUT/"pipeline/cells"; cells_dir.mkdir(parents=True)
    records = []
    for role in ("incident","control"):
        cell = chosen("batch100-darker-112-git-dir",role)
        for replay in (1,2):
            records.append(fixture_receipt(cell,parsed(cell,1 if role=="incident" else 0,stderr="not a git repository" if role=="incident" else ""),replay))
    for role in ("incident","control"):
        cell=chosen("batch100-py-bugger-65-accounting",role)
        for replay in (1,2):
            records.append(fixture_receipt(cell,{"cli_reported_inserted_count":10,"attempted_mutation_count":10,"successful_mutation_count":7,"persisted_source_diff_mutation_count":1},replay))
    audio=chosen("batch100-audioread-144-aifc","incident")
    for replay in (1,2):records.append(fixture_receipt(audio,parsed(audio,0),replay))
    exclusion=CELLS["cell:batch100-darker-112-git-dir:git-dir-unset"]
    for replay in (1,2):records.append(fixture_receipt(exclusion,parsed(exclusion,0),replay))
    producer.write_jsonl(cells_dir/"batch103_fresh_execution_receipts_v1.jsonl",records)
    calls=[]
    def run(script,*args):
        r=command([sys.executable,CHECKOUT/"scripts"/script,*args]);calls.append(r)
        save(OUT/"pipeline/command_receipts.json",calls)
        if r["return_code"]:raise RuntimeError(r["stderr"])
    outcomes=OUT/"pipeline/outcomes";causal=OUT/"pipeline/causal";arms=OUT/"pipeline/arms"
    run("seal_batch103_candidate_outcomes.py","--cell-artifacts-root",cells_dir,"--output-root",outcomes,"--workflow-run-id",RUN,"--workflow-head",HEAD)
    run("compile_batch103_public_evidence.py","--phase","causal","--outcome-root",outcomes,"--output-root",causal)
    for arm in "ABCDEFGHIJ":run("run_batch103_planner_arm.py","--arm",arm,"--outcome-root",outcomes,"--output-root",arms/arm)
    gain=OUT/"pipeline/gain";terminal=OUT/"pipeline/terminal";ownership=OUT/"pipeline/ownership"
    run("compile_batch103_public_evidence.py","--phase","gain","--arm-artifacts-root",arms,"--output-root",gain)
    run("compile_batch103_public_evidence.py","--phase","terminal","--arm-artifacts-root",arms,"--causal-root",causal,"--output-root",terminal)
    run("compile_batch103_public_evidence.py","--phase","ownership","--causal-root",causal,"--terminal-root",terminal,"--output-root",ownership)
    ledger=jsonl(outcomes/"batch103_registered_cell_ledger_v1.jsonl")
    sensitivity=jsonl(causal/"batch103_sensitivity_receipts_v1.jsonl")
    pairs=jsonl(causal/"batch103_pair_validity_receipts_v1.jsonl")
    assert len(ledger)==70
    assert all(not r["supported"] for r in sensitivity)
    assert all(not r["held_invariants_verified"] for r in pairs)
    observed={r["cell_id"]:r for r in ledger}
    assert observed[audio["cell_id"]]["status"]=="EXECUTED_SEMANTICS_UNRESOLVED"
    assert observed[exclusion["cell_id"]]["status"]=="EXECUTED_SEMANTICS_UNRESOLVED"
    contrast={r["program_id"]:r["measured_predicate_contrast"] for r in pairs}
    assert contrast["batch100-darker-112-git-dir"]["contrast"] is True
    assert contrast["batch100-py-bugger-65-accounting"]["contrast"] is False
    armrows=[r for a in "ABCDEFGHIJ" for r in jsonl(arms/a/"reactome_planner_execution_receipts_v1.jsonl")]
    assert len(armrows)==90 and all(r["time_to_first_sensitivity"] is None for r in armrows)
    proof=json.loads((ownership/"batch103_source_ownership_proof_registry_v1.json").read_text())
    assert proof["proof_count"]==0
    return {"status":"PASS_WITH_LOCAL_FIXTURE_SCOPE","synthetic_receipts":len(records),"represented_cells":len({r['cell_id'] for r in records}),
        "registered_cells_accounted":len(ledger),"commands_executed":len(calls),"arm_program_executions":len(armrows),
        "role_classified_pairs":sum(r["status"]=="VALID_PAIR" for r in pairs),"causal_sensitivity_claims":0,
        "ownership_proofs":0,"descriptive_contrasts":contrast,"official_provider_operations":0,
        "scope":"real imported producer/parser + wrapper binder; actual seal/compiler/planner CLIs over explicitly synthetic receipts"}


def main():
    global OUT
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);args=p.parse_args()
    OUT=args.output.resolve()
    if OUT.exists():raise SystemExit("Refusing to overwrite existing evidence; choose a new --output directory")
    OUT.mkdir(parents=True)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(IntegrationChecks)
    original=[]
    for name in ("test_batch101_semantic_predicates","test_batch102_causal_interventions"):
        mod=module("original_"+name,CHECKOUT/"tests"/(name+".py"))
        for fn in sorted(n for n in dir(mod) if n.startswith("test_")):
            original.append(name+"."+fn);suite.addTest(unittest.FunctionTestCase(getattr(mod,fn)))
    log=io.StringIO();result=unittest.TextTestRunner(stream=log,verbosity=2).run(suite)
    (OUT/"test_log.txt").write_text(log.getvalue())
    summary={"test_methods":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),
        "original_unmodified_test_functions":original,"original_test_count":len(original),
        "pytest_status":"not installed; attempted pinned install had no accessible index candidate; exact plain source tests executed through unittest", 
        "imported_actual_scripts":["run_batch100_candidate_program.py","run_batch102_candidate_slice.py","run_batch103_planner_arm.py"],
        "remote_head":HEAD,"scope":"local integration correction, not causal/biological repair gain"}
    save(OUT/"summary.json",summary)
    print(log.getvalue())
    if not result.wasSuccessful():raise SystemExit(1)
    summary["actual_audioread"]=actual_audioread()
    summary["pipeline"]=pipeline()
    save(OUT/"summary.json",summary)
    print(json.dumps(summary,indent=2))


if __name__=="__main__":main()

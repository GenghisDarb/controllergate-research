# Non-Ansible Capability Roadmap

This roadmap is a planning/control document. It is not evidence that any capability has been proven, and it does not weaken the versioned audits. Every future non-Ansible lane must continue to use decision-time-safe evidence, preserve the current claim boundaries, and stop with an exact blocker when a required capability is missing.

## Current boundary

- Current protocol remains `v2.13`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software remains `false` / not demonstrated.
- Memory lift remains `undemonstrated` unless the aggregate criteria are met.
- Non-Ansible generalization remains unproven.
- PySnooper:2 remains blocked unless decision-time-safe provenance for `tests/mini_toolbox.py` is proven.

## Required capability checklist

### 1. Source acquisition / origin licensing

- Status: implemented in v2.18, incomplete because the public PySnooper checkout lacks the BugsInPy materialized target test.
- Target version: v2.19.
- Required files: `source_acquisition_audit.json`, `workspace_provenance.json`, `materialized_test_provenance.json`.
- Audit checks: public buggy source commit acquired; benchmark target test acquired/materialized only from decision-time-safe sources; no fixed revision, gold patch, future evidence, or hidden-label evidence.
- Stop condition: `blocked_materialized_target_test_provenance_missing`.

### 2. Environment lock

- Status: required for all future non-Ansible lanes.
- Target version: v2.18+ and v2.19.
- Required files: `environment_lock_summary.json`, and `requirements-lock.txt` or equivalent if generated.
- Audit checks: dependency metadata hashes, Python version, declared dependencies, `python-toolbox` declaration if used, no undeclared dependency install, and no global environment mutation.
- Stop condition: `pre_repair_environment_lock_missing`.

### 3. Command manifest / BugsInPy translation bridge

- Status: required.
- Target version: v2.18+ and v2.19.
- Required file: `bugsinpy_command_map_v1.json`.
- Audit checks: candidate ID, raw executable target command, working directory, `PYTHONPATH` additions, command manifest SHA256, and decision-time-safe basis.
- Stop condition: `blocked_command_manifest_missing_or_unsafe`.

### 4. Fresh workspace / stale artifact resistance

- Status: required.
- Target version: v2.18+ and v2.19.
- Required files: `workspace_purity_report.json`, `workspace_equivalence_summary.json`.
- Audit checks: fresh ephemeral workspace outside the live repo and outside OneDrive; stale cache count is zero; no `__pycache__`, `.pytest_cache`, old virtualenv, or previous runtime artifact contamination; workspace tree/file manifest hash recorded.
- Stop condition: `blocked_workspace_purity_failure`.

### 5. Baseline registry precheck

- Status: required before every new non-Ansible acquisition or repair lane.
- Target version: v2.18+ and v2.19.
- Required file: `baseline_registry_snapshot_v2_19.json`.
- Audit checks: five scoreable baseline candidates preserved; `ansible:2` and `ansible:5` previous positive-memory statuses preserved; scoreable count remains 5 unless later verified evidence changes it; positive-memory count remains 2 unless later verified evidence changes it.
- Stop condition: `baseline_drift_blocking_acquisition`.

### 6. Cryptographic rollback markers

- Status: required for failed acquisition, failed workspace materialization, failed patch application, or failed validation.
- Target version: v2.19 and all future lanes.
- Required file: `proof_obligations_ledger.json`.
- Audit checks: failed attempt entry, rollback target entry index, rollback cleanup entry, valid hash chain, and no ghost state after rollback.
- Stop conditions: `blocked_ledger_rollback_missing`, `blocked_ghost_state_detected`.

### 7. Repair state snapshot

- Status: missing before v2.19; must be implemented in v2.19.
- Target version: v2.19.
- Required file: `s_engine_cognitive_state_snapshot.json`.
- Audit checks: candidate, prompt hash if available, context sources, AST/context hashes, MinimalProbe outputs used, previous failure classifications, decision-time evidence hash, generated patch hash if any, final state hash, and no fixed/gold/future evidence.
- Stop condition: `blocked_cognitive_state_snapshot_missing`.

### 8. Bounded diagnostic reward signal

- Status: missing before v2.19; must be implemented in v2.19 if validation or bounded target-test runs occur.
- Target version: v2.19.
- Required file: `retrocausal_reward_signal.json`.
- Audit checks: target command only, pass/fail/skip counts if parseable, failure signature, graded diagnostic signal if parseable, comparison only to prior known attempt hashes/signatures, no full scoring, and no broad benchmark claim.
- Stop condition: `blocked_reward_signal_missing_after_test_run`.

### 9. Test-run structural signature

- Status: missing before v2.19; must be implemented in v2.19 if any test run occurs.
- Target version: v2.19.
- Required file: `test_suite_structural_signature.json`.
- Audit checks: import errors, assertion errors, fixture errors, timeout errors, syntax errors, collection errors, failure locations if parseable, and structural signature hash.
- Stop condition: `blocked_structural_signature_missing_after_test_run`.

### 10. Patch size cap / locality limit

- Status: missing before v2.19; must be implemented in v2.19 if a patch exists.
- Target version: v2.19.
- Required file: `patch_size_cap.json`.
- Audit checks: max files touched 3, max lines changed 50, max functions modified 2, actual files/lines/functions changed, status `PASS` or `BLOCK`.
- Stop condition: `blocked_patch_size_cap_exceeded`.

### 11. Real-time patch safety

- Status: misapplied previously; corrected in v2.19 as construction-time safety checking.
- Target version: v2.19.
- Required file: `realtime_patch_safety_trace.json`.
- Audit checks: each file modification checked before proceeding, source-only status per file, AST/function locality check if parseable, forbidden-path check per file, and generation stops immediately on a failed check.
- Stop condition: `blocked_realtime_patch_safety_failed`.

### 12. Patch application step

- Status: misapplied previously; corrected in v2.19 as application after pre-application verification.
- Target version: v2.19.
- Required file: `patch_application_step.json`.
- Audit checks: pre-application source hash, patch hash, apply status, post-application source hash, and verification happened before application.
- Stop condition: `blocked_patch_application_failed`.

### 13. Workspace protection

- Status: misapplied previously; corrected in v2.19 as protected fresh workspace handling.
- Target version: v2.19.
- Required file: `telomere_workspace_protection_status.json`.
- Audit checks: fresh workspace path, attempt number, previous workspace archived or deleted before new attempt, protected workspace true/false, stale cache count, and status `PASS` or `BLOCK`.
- Stop condition: `blocked_workspace_protection_failed`.

### 14. Post-validation workspace analysis

- Status: missing before v2.19; must be implemented in v2.19 if validation runs.
- Target version: v2.19.
- Required file: `post_validation_workspace_analysis.json`.
- Audit checks: patch hash if any, validation result, modified files after validation, new/deleted files, cache files present, pytest cache present, virtualenv state, and duplicate replay workspace equivalence if applicable.
- Stop condition: `blocked_post_validation_analysis_missing`.

### 15. Materialized target-test provenance bridge

- Status: immediate v2.19 blocker.
- Target version: v2.19.
- Required files: `materialized_test_provenance.json`, `materialized_test_equivalence_summary.json`.
- Audit checks: target test came from a decision-time-safe BugsInPy/public benchmark source; target test did not come from fixed revision, gold patch, hidden labels, future logs, or hallucinated content; materialization is benchmark harness setup, not repair mutation; patch never modifies materialized test/harness files.
- Stop condition: `blocked_materialized_target_test_provenance_missing`.

### 16. PySnooper:2 policy

- Status: blocked.
- Target version: future only if provenance appears.
- Required files: future candidate-specific provenance record for `tests/mini_toolbox.py`.
- Audit checks: no compute spent on PySnooper:2 unless decision-time-safe fixture provenance is proven.
- Stop condition: keep PySnooper:2 blocked when provenance is absent.

### 17. Claims boundary

- Status: always active.
- Target version: every future version.
- Required files: `claim_boundary_v*_*.json` or version-equivalent claim record.
- Audit checks: full scoring remains `NOT_RUN` / disallowed; self-maintaining software remains false / not demonstrated; memory lift remains undemonstrated unless aggregate criteria are met; non-Ansible generalization is not claimed from one candidate; family generalization requires multiple verified scoreable non-Ansible episodes.
- Stop condition: any claim-boundary violation.

### 18. Future version sequencing

- v2.19: ingest v2.18; solve/block BugsInPy materialized target-test provenance; add repair state snapshot, diagnostic reward signal, structural signature, patch size cap, real-time patch safety, corrected patch application semantics, workspace protection, and post-validation analysis; attempt PySnooper:1 only if all gates pass.
- v2.20: if v2.19 blocks on target-test provenance, implement a stricter BugsInPy benchmark-source acquisition bridge or manual verified source-bundle protocol; if v2.19 reaches validation but fails, use reward/signature/post-validation evidence to improve repair strategy without broad scoring.
- v2.20 updated scope: couple source acquisition, BugsInPy harness-origin authority, target-test provenance, harness topology, redundancy-cache verification, recursive provenance, transport integrity, prompt/context custody, and precision-resolution diagnostics into one PySnooper:1 lane. If no non-circular authoritative BugsInPy harness-origin pin exists, block with `bugsinpy_harness_origin_bootstrap_missing` and write a proposal-only harness-origin candidate for review.
- v2.21: promote a non-circular BugsInPy harness-origin pin from an immutable public source already tied to ingested decision-time metadata, verify that pin before any repair work, then attempt PySnooper:1 only if target-test provenance, topology, replay, and proof-ledger gates pass. If the pinned harness source still lacks `tests/test_chinese.py`, block before dependency recovery and patch generation.
- v2.22: run the pinned official BugsInPy framework checkout/materialization path for PySnooper:1 before any terminal target-test decision. Absence from the framework repository metadata tree alone is not terminal; only absence after official materialization plus buggy-source search, or unsafe fixed/future/gold/synthetic provenance, can terminally block PySnooper:1 under current safety rules.
- v2.23: only after multiple non-Ansible positives, consider current-protocol promotion beyond v2.13.

## Origin notes

Some output filenames preserve earlier project terminology for continuity with existing prompts and artifacts. The implementation meaning is ordinary engineering: source provenance, dependency locking, command translation, workspace hygiene, proof-ledger rollback, repair state capture, bounded diagnostics, patch locality, patch safety, patch application, and post-validation analysis.

## v2.20 coupled provenance and precision-resolution controls

v2.20 adds planning and audit controls for:

- BugsInPy harness-origin acquisition with non-circular authority.
- Source-test coupling so target tests cannot be paired with unrelated source revisions.
- Harness topology/configuration mapping before dependency recovery or patch generation.
- Recursive provenance-depth checks for any prior artifact content.
- Redundancy-cache lookup with expected-vs-actual SHA256 verification before any local file is trusted.
- Cross-boundary transport hash logging for files written from workspace/runtime context into committed evidence.
- Pre-generation prompt/context hash locking before any repair patch bytes may be generated.
- Zero-lift reward signals for true precondition failures and graded diagnostic reward for executed target commands or patch-size/locality cap failures.
- Patch-size overshoot grading to distinguish near-cap patches from divergent patches.
- Resolution-depth diagnostics using TLD framing as a planning heuristic only, not as a proof claim.

The v2.20 lane remains PySnooper:1-only. PySnooper:2 remains blocked unless decision-time-safe fixture provenance for `tests/mini_toolbox.py` is proven. Full scoring, self-maintaining software, memory lift, broad non-Ansible generalization, and TORUS/TLD proof claims remain forbidden.

## v2.21 harness-origin pin and first eligible repair-attempt controls

v2.21 adds planning and audit controls for:

- A committed non-circular BugsInPy harness-origin pin for `PySnooper:1`.
- Pin authority derived from an immutable public BugsInPy commit already referenced by ingested decision-time evidence, not from workflow-runtime discovery.
- Verification of the pinned BugsInPy topology files before target-test provenance, dependency recovery, replay, patch generation, or validation.
- Explicit target-test provenance blocking when the pinned harness source does not contain `tests/test_chinese.py`.
- Preservation of the v2.20 source-acquisition and provenance boundaries while allowing at most one PySnooper:1 patch attempt only after all provenance/replay gates pass.
- A zero-lift diagnostic reward when the blocker is a missing target-test precondition rather than a failed repair attempt.

The v2.21 lane remains PySnooper:1-only. PySnooper:2 remains blocked unless decision-time-safe fixture provenance for `tests/mini_toolbox.py` is proven. Full scoring, self-maintaining software, memory lift, broad non-Ansible generalization, and TORUS/TLD proof claims remain forbidden.

## v2.22 BugsInPy official target-test materialization controls

v2.22 adds planning and audit controls for:

- Treating the pinned BugsInPy repository as the official framework/metadata source, not as the expected materialized project filesystem.
- Running official `bugsinpy-checkout` materialization into a fresh outside-repo workspace before any terminal PySnooper:1 target-test absence decision.
- Searching the materialized workspace and buggy source tree for `tests/test_chinese.py`, `test_chinese.py`, and `*chinese*.py` only after official materialization is attempted.
- Recording whether the official materialization path requires fixed/future source content for the target test.
- Terminally blocking PySnooper:1 under current safety rules when the target test is absent after materialization/buggy-source search, or when the only available target-test content requires fixed/future/gold/hidden/synthetic provenance.
- Recommending selection of a different non-Ansible candidate next if PySnooper:1 is terminally provenance-blocked, unless externally provided decision-time-safe target-test provenance is later supplied.

The v2.22 lane remains PySnooper:1-only. PySnooper:2 remains blocked unless decision-time-safe fixture provenance for `tests/mini_toolbox.py` is proven. Full scoring, self-maintaining software, memory lift, broad non-Ansible generalization, and TORUS/TLD proof claims remain forbidden.
## v2.23 Source Acquisition Method Boundary

v2.23 stops before new candidate selection because the pinned BugsInPy checkout method is blocked under the current provenance rules.

- Method ID: `bugsinpy_checkout_fixed_copy`.
- Method signature: `git_checkout_fixed_commit_then_copy_test_then_git_checkout_buggy_commit`.
- Decision: `globally_blocked_under_current_provenance_rules`.
- Scope: all candidates that require fixed-commit-derived test copying through this BugsInPy method.
- Candidate selection: `not_run_global_method_block`.
- Patch generation, dependency recovery, pre-repair replay, validation, and scoring: not run.
- v2.24 priority: External Safe-Source Candidate Acquisition Lane using direct immutable project history, exact buggy commits, and tests physically present in the buggy commit tree or otherwise proven decision-time-safe.
- Future safety enhancements are recorded as planning items, not prerequisites for the v2.24 source-acquisition pivot: Executed Scope Manifest, Compound Provenance Combination Gate, Candidate Environment Resolution Preflight, Pre-Generation Structural Failure Signature, Co-Change Impact Map, Stochastic Replay Reliability, Environmental Pass Guard, Conditional Path Fork Guard, Bounded Patch Variant Queue, and Dependency Impact Map.
- Research-level items such as Conditional Path Fork Guard and advanced Dependency Impact Map are v2.26+ investigations and must not delay v2.24 external source acquisition.

Claim boundaries remain unchanged: current protocol `v2.13`, full scoring `NOT_RUN` / disallowed, memory lift undemonstrated, and self-maintaining software false / not demonstrated.
## v2.24 External Candidate Registry Precheck

v2.24 requires a committed reviewed External Candidate Registry entry before any external repository can be cloned or selected for repair.

- Required config: `configs/external_candidate_registry.json`.
- Current registry status: empty, with no reviewed entries.
- Blocker: `blocked_external_candidate_registry_missing_or_invalid`.
- Smallest next step: `create_reviewed_external_candidate_registry_entry`.
- Recommended follow-up: `v2.25 External Candidate Registry Construction Lane`.
- Candidate recommendations from issues or maintainer discussion remain source material for registry construction only; they are not executable candidates until the registry pins repository URL, exact buggy commit, exact command, target-test file hashes, and expected normalized failure-log hash.

No candidate selection, environment setup, failure capture, executed-scope tracing, patch generation, or scoring is authorized until the registry precheck passes.
## v2.25 External Candidate Registry Construction

v2.25 turns the v2.24 registry precheck into committed registry infrastructure.

- The registry schema and validator are now tracked.
- A future candidate may enter only through a reviewed registry seed with exact repository URL, exact buggy commit, exact target command, target-test hashes from the buggy tree, and expected normalized failure-log hash.
- No seed is present in this run, so no external repository is cloned and no candidate is selected.
- Current blocker: `blocked_no_reviewed_external_candidate_seed_provided`.
- Next action: `provide inputs/external_candidate_registry_seed.json with one reviewed candidate, or manually edit configs/external_candidate_registry.json after offline verification`.
- Official artifact status: `verified_official_artifact`; v2.25 audit `PASS`; current protocol remains `v2.13`.
- v2.26 follow-up: External Candidate Seed Capture Lane using `inputs/external_candidate_seed_draft.json` as the manual seed draft handoff.
## v2.26 External Candidate Seed Capture

v2.26 records the manual seed-draft boundary for external candidate intake.

- The lane requires `inputs/external_candidate_seed_draft.json`; the tracked example file is placeholders only.
- No seed draft is present in this run, so no external repository is cloned and no candidate is selected.
- Current blocker: `blocked_no_external_candidate_seed_draft_provided`.
- Next action: provide inputs/external_candidate_seed_draft.json with exactly one manually reviewed seed draft.
## v2.27 External Candidate Seed Draft Verification

v2.27 verifies a manually supplied External Candidate Seed Draft before any registry merge.

- Canonical input: `inputs/external_candidate_seed_draft.json`.
- Seed draft present: `false`.
- Native buggy-test verification is mandatory; generated/manual reproducer files are not accepted as target tests.
- External-network-dependent commands are blocked unless backed by a project-native local fixture in the buggy tree.
- Timeout-based expected failures require an explicit timeout policy.
- Current result: `blocked_no_external_candidate_seed_draft_provided`.
## v2.28 External Candidate Seed Draft Verification

v2.28 tests whether one manually supplied External Candidate Seed Draft can become a reviewed registry entry.

- Candidate: `py_bugger_issue_65`.
- Required proof: direct buggy commit checkout, native target test, project-native support file, declared environment source, and captured pre-repair failure.
- Result: `verified_external_candidate_seed_added`.
- No repair or patch generation is authorized in this lane.
## v2.29 Structural Repair Capability Integration

v2.29 integrates the missing repair-navigation controls for the reviewed external candidate path.

- AST Dependency Closure and executed-scope evidence restrict patchable files.
- Context Pinching Filter creates a hash-anchored repair capsule from allowed buggy-tree evidence.
- Failure Memory Weight Ledger is diagnostic-only.
- Fragmented Patch Assembly Gate still permits only one final patch attempt.
- Pre/Post Handoff Consistency Gate ties patch and validation evidence to the same candidate, commit, command, and failure signature.

The lane selects no additional candidates and does not promote the current protocol.




## v2.30 Failure Signature Canonicalization

v2.30 adds a stronger failure-signature gate for the reviewed external candidate path.

- Existing text-log hashes stay as historical evidence.
- A structured semantic signature becomes the repair gate after three matching clean captures.
- The old full-log hash mismatch remains diagnostic only after registry refresh passes.
- No candidate expansion, full scoring, or protocol promotion occurs.


## v2.31 Scoreable External Repair Episode Consolidation


v2.31 does not repair a new candidate. It registers the first scoreable external non-Ansible repair episode from v2.30 and prepares the next-candidate path.

- Achieved evidence boundary: one scoreable external source-only repair episode.
- Candidate: `py_bugger_issue_65`.
- Carry-forward validation: target validation `PASS`, duplicate clean replay `3 / 3`, replay reliability `1.0`.
- Candidate expansion must continue through the external candidate registry and seed verification pipeline.
- Next lane should either add 2-3 more reviewed external candidates or run a prospective second repair lane only if another reviewed candidate already exists.
- Full scoring, memory lift, broad family generalization, and self-maintaining software remain unclaimed.



## v2.32 Second External Candidate Seed and Matched-Null Protocol Lock


v2.32 locks the future matched-null memory experiment before any second repair is attempted.

- If a manually reviewed second seed is absent, the lane stops with `blocked_no_second_external_candidate_seed_draft_provided`.
- If a seed is later provided, it must verify a native buggy-tree test, support/environment hashes, and pre-repair failure before any registry merge.
- Future v2.33 repair work may compare memory-enabled and memory-disabled matched arms only after candidate #2 is verified.
- v2.32 makes no repair, full-scoring, memory-lift, or self-maintaining claim.




## v2.33 Candidate #2 Seed Intake and Matched-Null Experiment Status


v2.33 could only run the matched-null memory repair experiment if candidate #2 seed verification passed. Because no seed file is present, the lane stops at the no-seed blocker and writes a discovery support packet instead of searching or fabricating a candidate.

- Use the generated helper prompt/checklist/template to obtain a verified seed.
- A valid seed must identify a native buggy-tree test and a full 40-character buggy commit SHA.
- Issue or pull request links are lead evidence only; they are not sufficient registry evidence.
- No repair, patch generation, target validation after patch, memory-lift claim, full-scoring claim, or protocol promotion occurs in v2.33.

## v2.34 Candidate #2 Seed Verification Workbench


v2.34 closes the recurring byte-custody gap and converts candidate #2 discovery into a reusable verification workbench. The lane does not search live issues, select a candidate, repair code, generate patches, or run the matched-null experiment.

- Rejected prior leads are recorded as leads only, not candidates.
- A future seed must provide a full 40-character buggy commit SHA, a native target test path that exists in that commit, an environment source file, and an exact failing command.
- The workbench can verify a seed from the buggy commit only and can merge it into the registry only after the registry validator passes.
- The next repair experiment remains blocked until a valid second reviewed candidate exists.

## v2.35 Automated Candidate #2 Acquisition

v2.35 replaces passive seed waiting with a bounded metadata-probe acquisition sprint. The sprint did not acquire a valid second seed under the direct-verification gates, so no repair or matched-null comparison ran.

- Metadata probes are lead evidence only.
- Any future candidate #2 still needs exact commit identity, native target test presence, environment-file proof, pre-repair failure capture, and registry validation.
- The next safe step is a more focused lead pool or a manually supplied seed that already satisfies the v2.34 workbench requirements.

## v2.36 resolved-commit replay and candidate admission

v2.36 adds resolved-commit replay, active probe routing, structural navigation, coupled dependency projection, and a separately classified issue-derived fallback. The lane keeps candidate #2 admission gated on direct replay or verified issue-derived harness evidence.

- Native replay candidate acquired: `false`.
- Issue-derived fallback attempted: `true`.
- Issue-derived candidate acquired: `false`.
- Exact blocker: `blocked_no_native_or_issue_derived_candidate2_seed_acquired`.
- Structural Navigation Map: `implemented_active_v2_36`.
- Active Probe Router: `implemented_active_v2_36`.
- Coupled Dependency Projection Map: `implemented_active_v2_36`.
- Interlock Invariant Map: `implemented_active_v2_36`.
- Issue-Derived Ephemeral Reproduction Harness: `conditional_fallback_v2_36`.
- Matched-Null Repair Experiment: `conditional_on_candidate2_verification`.
- Full scoring remains `NOT_RUN/disallowed`; memory lift remains `undemonstrated`; self-maintaining software remains `false/not_demonstrated`.

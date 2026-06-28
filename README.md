# ControllerGate

ControllerGate is a research repository for replay-first evidence, memory-lift experiments, and bounded repair-protocol evaluation. The project keeps historical versioned evidence intact while exposing a stable current-protocol interface for day-to-day checks.

Current branch: `controllergate-v1.7-alpha-real-trace-pilot`

## Current protocol

The current protocol is `v2.13` / `minimal_forensic_context_lane`.

- Current config: `configs/controllergate_current.yaml`
- Current summary: `outputs/current/current_protocol_summary.json`
- Verified v2.13 outputs: `outputs/v2_13_minimal_forensic_context_lane`
- Current protocol docs: `docs/current_protocol.md`

Historical versioned runners, workflows, audits, and output directories remain the reproducibility references. The current interface points to the latest verified protocol; it does not rewrite old results.

## Current status

v2.13 is officially ingested and audited.

- Workflow run: `28130741168`
- Artifact: `v2_13_minimal_forensic_context_lane_artifacts`
- Artifact SHA256: `57f87a8e0726f55acf0a01282acf7a649808fc71007cba732b9491cf66567ee1`
- v2.13 audit: `PASS`
- Baseline preservation: `PASS`
- `ansible:2` and `ansible:5` preserved `positive_memory_only` status.
- PySnooper:1 policy classification: `dependency_recovery_allowed_by_policy_not_executed_in_minimal_lane`
- PySnooper:2 final blocker: `blocked_fixture_materialization_incomplete`
- Scoreable episodes: `5`
- Positive-memory-only episodes: `2`
- Non-Ansible positive-memory episodes: `0`

The v2.13 result is a successful deterministic forensic block, not a repair breakthrough.

## Claim boundaries

- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.
- Family generalization remains `not_expanded`.
- Non-Ansible positive-memory count remains `0`.
- v2.14 capability recovery is officially ingested as a preserved artifact result, but it is still separate from the current protocol.
- v2.15 chromosomal maintenance gate-order work is a corrective stack on top of v2.14, not a current-protocol promotion.
- v2.16 PySnooper:1 isolated recovery executor work is an officially ingested bounded executor-contract checkpoint, not a current-protocol promotion or a scoreable repair result.
- v2.17 PySnooper:1 runtime-workspace materialization is an officially ingested bounded workspace-provenance checkpoint, not a current-protocol promotion or a scoreable repair result.
- v2.18 PySnooper:1 origin licensing/source acquisition work is an officially ingested bounded source-acquisition checkpoint, not a current-protocol promotion or a scoreable repair result.
- v2.19 BugsInPy materialized-test provenance is officially ingested as a bounded provenance checkpoint, not a current-protocol promotion or a scoreable repair result.
- v2.20 coupled test-provenance repair work is officially ingested as a bounded harness-origin bootstrap checkpoint; it blocks before repair because no non-circular BugsInPy harness-origin authority is available.
- v2.21 harness-origin verification work is officially ingested as a bounded non-circular BugsInPy harness-origin pin checkpoint; it is not a current-protocol promotion or a scoreable repair result.
- v2.22 BugsInPy target-test materialization work is a bounded implementation lane that must run official pinned BugsInPy materialization before any terminal PySnooper:1 target-test provenance decision; it is not a current-protocol promotion.
- The non-Ansible capability roadmap is tracked in `docs/non_ansible_capability_roadmap.md` and `configs/non_ansible_capability_backlog.json`.

## v2.14 capability recovery lane

v2.14 is a bounded non-Ansible capability recovery lane, not the current protocol.

- Campaign: `v2_14_capability_recovery_lane`
- Scope: `PySnooper:1` first, then `PySnooper:2` only if PySnooper:1 blocks or fails cleanly.
- No broad sweep, full scoring, self-maintaining-software claim, or family-generalization claim is allowed.
- Official artifact digest: `sha256:1a247992b8915f7b5b792df6663e283244d23e6c5ffe2423ca1fc0f83efb4f3f`
- Result: `PASS_WITH_BOUNDED_BLOCKERS`; no new non-Ansible scoreable or positive-memory result.

## v2.15 chromosomal maintenance gate order

v2.15 implements the next corrective stack as machine-checkable maintenance gates: reference core, contact topology, materialization/cofactor recovery, activation/licensing, bounded patch attempt, contact audit, duplicate replay, phase/seed check, and proof-ledger lock.

- Campaign: `v2_15_chromosomal_maintenance_gate_order`
- Patch generation remains blocked unless prior gates explicitly authorize `next_allowed_action: patch`.
- PySnooper:1 remains blocked at dependency/cofactor materialization and activation licensing.
- PySnooper:2 remains blocked at fixture/helper materialization and activation licensing.
- Current protocol remains `v2.13` until a later verified promotion is explicitly made.

## v2.16 PySnooper:1 isolated recovery executor

v2.16 narrows the next non-Ansible step to PySnooper:1 only. It defines and audits the isolated declared-dependency executor contract: create a sandboxed `venv`, install only the buggy-checkout-declared `python-toolbox` dependency, normalize `PYTHONPATH` to the checked-out project root, and forbid fixed revisions, BugsInPy gold patches, future outcomes, hidden labels, test edits, benchmark edits, undeclared installs, and vendored helpers.

- Campaign: `v2_16_pysnooper1_isolated_recovery_executor`
- Status: `verified_official_artifact` / `PASS_WITH_EXECUTOR_CONTRACT_BLOCKED`
- Official artifact digest: `sha256:92cc10c777e0fc56e665a963283bf94daca17a008252210ad6a05242b4f15070`
- Internal manifest: `10` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `11` entries after adding the local official artifact-verification record.
- PySnooper:1 classification: `blocked_no_safe_patch_candidate_generated`
- PySnooper:2 remains blocked unless decision-time-safe provenance for `tests/mini_toolbox.py` can be proven.
- No `.diff` payload is generated or counted because the live isolated BugsInPy PySnooper runtime workspace is not committed in the repo and pre-repair replay preconditions did not pass.
- Scoreable episodes remain `5`; positive-memory-only episodes remain `2`; non-Ansible positive-memory episodes remain `0`.
- Full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
- Current protocol remains `v2.13`.

## v2.17 PySnooper:1 runtime-workspace materialization

v2.17 is a narrow PySnooper:1-only lane that attempts to turn the v2.16 isolated recovery contract into an executable path only if a decision-time-safe buggy runtime workspace can be found or materialized outside the live repository.

- Campaign: `v2_17_pysnooper1_runtime_workspace_materialization`
- Status: `verified_official_artifact` / `PASS_WITH_WORKSPACE_MATERIALIZATION_BLOCKED`.
- Official artifact digest: `sha256:a2606d558d9baf62e301cd74c4e5ef39f577e513f23c7464d3213819cdbd09ce`; byte size: `32097`; ZIP entries: `14`.
- Internal SHA256SUMS: `11` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `12` entries after adding the local official artifact-verification record.
- Workspace materialization classification: `blocked_no_decision_time_safe_workspace_source`.
- Workspace provenance status: `BLOCK`; no outside-repo PySnooper:1 buggy checkout or available BugsInPy checkout executable/source bundle could be tied to the recorded safe metadata.
- Dependency recovery execution status: `not_executed_workspace_blocked`.
- Pre-repair replay status: `not_run_workspace_blocked`.
- Patch generated: `false`; authorized: `false`; attempted: `false`.
- PySnooper:1 scoreable: `false`; positive-memory-only: `false`.
- PySnooper:2 was not pursued.
- Scoreable episodes remain `5`; positive-memory-only episodes remain `2`; non-Ansible positive-memory episodes remain `0`.
- Full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
- Current protocol remains `v2.13`; v2.17 is not promoted to current.

## v2.18 PySnooper:1 origin licensing/source acquisition

v2.18 corrects the missing source-acquisition prerequisite exposed by v2.17. It is a PySnooper:1-only lane that uses decision-time-safe BugsInPy metadata to attempt a stateless public Git checkout of the exact buggy PySnooper revision before any environment recovery, replay, patch generation, or validation can run.

- Campaign: `v2_18_origin_licensing_source_acquisition`
- Status: `verified_official_artifact`; v2.18 audit status: `PASS`.
- Official artifact digest: `sha256:4c91b8e69dd75e1ed49432611f834b73ec700054d6395c99b42c729e9f84eac5`; byte size: `36500`; ZIP entries: `18`.
- Internal SHA256SUMS: `15` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `16` entries after adding the local official artifact-verification record.
- v2.17 source blocker corrected: `true`.
- Source acquisition status: `source_checkout_acquired`.
- Source commit acquired: `e21a31162f4c54be693d8ca8260e42393b39abd3`.
- Workspace purity status: `PASS`; the fresh outside-repo checkout was cleaned and then removed after evidence capture.
- Workspace equivalence status: `BLOCK`; the raw public checkout does not contain the BugsInPy materialized target test `tests/test_chinese.py`.
- Environment lock status: `PASS`; command manifest status: `PASS`.
- Dependency recovery status: `not_executed_workspace_equivalence_blocked`.
- Pre-repair replay status: `not_run_workspace_equivalence_blocked`.
- Patch generated: `false`; authorized: `false`; attempted: `false`.
- PySnooper:1 classification: `blocked_workspace_equivalence_missing_materialized_target_test`.
- PySnooper:1 scoreable: `false`; positive-memory-only: `false`.
- PySnooper:2 was not pursued.
- Scoreable episodes remain `5`; positive-memory-only episodes remain `2`; non-Ansible positive-memory episodes remain `0`.
- Full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
- Current protocol remains `v2.13`; v2.18 is not promoted to current.

## v2.19 BugsInPy materialized-test provenance

v2.19 directly addresses the v2.18 blocker by searching decision-time-safe BugsInPy/materialized-test provenance sources for `tests/test_chinese.py` before any dependency recovery, replay, patch generation, validation, or duplicate replay.

- Campaign: `v2_19_bugsinpy_materialized_test_provenance`
- Status: `verified_official_artifact`; v2.19 audit status: `PASS`.
- Official artifact digest: `sha256:bd7ee23458a60051abe2137266b91d06c72b06449941f2720ddc09b0b6ead695`; byte size: `51116`; ZIP entries: `29`.
- Workflow run: `28187693617`; artifact ID: `7885570481`.
- Internal SHA256SUMS: `24` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `25` entries after adding the local official artifact-verification record.
- v2.18 official ingest verified: `true`.
- Source acquisition status: `source_checkout_acquired`.
- Source commit acquired: `e21a31162f4c54be693d8ca8260e42393b39abd3`.
- Materialized target-test provenance status: `BLOCK`; target-test SHA256: `null`.
- Workspace purity status: `PASS`; workspace equivalence status: `BLOCK`.
- Environment lock status: `PASS`; command manifest status: `PASS`; baseline registry precheck: `PASS`.
- Dependency recovery status: `not_executed_materialized_test_provenance_blocked`.
- Pre-repair replay status: `not_run_materialized_test_provenance_blocked`.
- Repair state snapshot: `PASS`; diagnostic reward signal: `not_run_no_target_command_execution`; test structural signature: `not_run_no_target_command_execution`; patch size cap: `PASS`.
- Patch generated: `false`; authorized: `false`; attempted: `false`.
- PySnooper:1 classification: `blocked_materialized_target_test_provenance_missing`.
- Exact blocker: decision-time-safe BugsInPy target-test content for `tests/test_chinese.py` was not found. Prior logs identify the target path and show fixed-revision test-copy behavior, but no allowed public benchmark source supplied the file content.
- PySnooper:1 scoreable: `false`; positive-memory-only: `false`.
- PySnooper:2 was not pursued.
- Scoreable episodes remain `5`; positive-memory-only episodes remain `2`; non-Ansible positive-memory episodes remain `0`.
- Full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
- Current protocol remains `v2.13`; v2.19 is not promoted to current.

## v2.20 coupled test-provenance repair lane

v2.20 couples the v2.18 source-acquisition result, v2.19 materialized-test blocker, BugsInPy harness-origin bootstrap, harness topology, redundancy-cache trust, workspace transport integrity, pre-generation context custody, and precision-resolution diagnostics into one PySnooper:1-only lane.

- Campaign: `v2_20_test_provenance_repair_lane`
- Status: `verified_official_artifact`; v2.20 audit status: `PASS`.
- Official artifact digest: `sha256:3b6090f33ab4e5bb04ca4f922e51d4688b8d1ef5bc343ab6b26efc40b9e7ca25`; byte size: `64492`; ZIP entries: `43`.
- Workflow run: `28199100858`; artifact ID: `7890304839`.
- Internal SHA256SUMS: `36` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `37` entries after adding the local official artifact-verification record.
- v2.19 official ingest verified: `true`.
- Source acquisition status: `source_checkout_acquired`; source commit: `e21a31162f4c54be693d8ca8260e42393b39abd3`.
- BugsInPy harness origin status: `BLOCK`; bootstrap status: `BLOCK`.
- Authoritative SHA256 source: `none_available_before_v2_20_execution`; self-referential hash detected: `false`.
- Proposed harness-origin candidate is written for future review only and is not authoritative for the current run.
- Target-test provenance status: `BLOCK`; target-test SHA256: `null`.
- Replisome coupling status: `BLOCK`; chaperonin topology status: `BLOCK`.
- Redundancy-cache lookup result: `not_found`; trust result: `not_trusted`.
- Nuclear-pore transport status: `PASS`; workspace purity: `PASS`; workspace equivalence: `BLOCK`.
- Environment lock, command manifest, baseline registry precheck, cognitive state snapshot, pre-generation prompt/context hash, reward signal, test structural signature, and patch size cap all record machine-checkable status.
- Dependency recovery status: `not_executed_harness_origin_blocked`; pre-repair replay: `not_run_harness_origin_blocked`.
- Patch generated: `false`; authorized: `false`; attempted: `false`.
- PySnooper:1 scoreable: `false`; positive-memory-only: `false`; PySnooper:2 was not pursued.
- Current resolution band: `source_acquisition_N6_passed__test_provenance_N7_blocked__harness_topology_N8_blocked`.
- Exact blocker: no non-circular authoritative BugsInPy harness-origin SHA256 pin was available before v2.20 execution, so target-test provenance could not be trusted.
- Scoreable episodes remain `5`; positive-memory-only episodes remain `2`; non-Ansible positive-memory episodes remain `0`.
- Full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
- Current protocol remains `v2.13`; v2.20 is not promoted to current.

## v2.21 harness-origin verification lane

v2.21 promotes a committed, non-circular BugsInPy harness-origin pin for `PySnooper:1` from an immutable public BugsInPy commit already tied to ingested decision-time metadata. The lane may attempt repair only if the pin, target-test provenance, topology, replay, dependency recovery, and proof-ledger gates pass.

- Campaign: `v2_21_harness_origin_verification_lane`
- Status: `verified_official_artifact`; v2.21 audit status: `PASS`.
- Official artifact digest: `sha256:35b22fd48d93ae5c5163ad9ab5d27ac99cfc351bfd2e08b869f38479aebade08`; byte size: `72234`; ZIP entries: `47`.
- Workflow run: `28201995136`; artifact ID: `7891479826`.
- Internal SHA256SUMS: `39` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `40` entries after adding the local official artifact-verification record.
- Scope: `PySnooper:1` only; PySnooper:2 is not pursued.
- Harness-origin pin source: `https://github.com/soarsmu/BugsInPy.git` at `11c5f1eea954a42132cfd06bf257766a7963e0fd`.
- Expected harness manifest SHA256: `3706244b4618612fad4681578dd740d1e54dbe9069303072ab7802f656f0e608`.
- Workflow-runtime generation of authority is forbidden; the workflow must use committed pin config.
- Target-test provenance remains the next hard gate: if the pinned harness source lacks `projects/PySnooper/bugs/1/tests/test_chinese.py`, the lane blocks before dependency recovery, replay, patch generation, validation, or scoring.
- Full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
- Current protocol remains `v2.13`; v2.21 is not promoted to current.

## v2.22 BugsInPy target-test materialization lane

v2.22 corrects the framework-vs-materialized-workspace distinction: the pinned BugsInPy repository is treated as official framework/metadata, not as the expected location of materialized project files. The lane must run official `bugsinpy-checkout` into a fresh outside-repo workspace before deciding whether `tests/test_chinese.py` is safely available for PySnooper:1.

- Campaign: `v2_22_bugsinpy_target_test_materialization_lane`
- Status: `verified_official_artifact`; v2.22 audit status: `PASS`; v2.22 is not promoted to current.
- Official artifact digest: `sha256:32aaad406f10acecb373d3313722c5c7130fd4c4c87ae879e5feb83706cb852a`; byte size: `78669`; ZIP entries: `49`.
- Workflow run: `28204197043`; artifact ID: `7892349852`.
- Internal SHA256SUMS: `42` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `43` entries after adding the local official artifact-verification record.
- Scope: `PySnooper:1` only; PySnooper:2 is not pursued.
- Official framework source: `https://github.com/soarsmu/BugsInPy.git` at `11c5f1eea954a42132cfd06bf257766a7963e0fd`.
- Absence from `projects/PySnooper/bugs/1/tests/test_chinese.py` in the framework checkout alone is not a terminal blocker.
- Official materialization found `PySnooper/tests/test_chinese.py`; artifact-preserved target-test SHA256 is `7a3d64cd702fdfa1eba8c08ac3c8934948a3ef0178f141c1f5599307c1fe59f3`.
- The target-test provenance status is `BLOCK` because the pinned framework materialized the test through fixed-commit-derived content before resetting to the buggy commit.
- PySnooper:1 terminal blocker: `blocked_target_test_requires_fixed_or_future_source`.
- Dependency recovery, pre-repair replay, patch generation, validation, duplicate replay, and scoring were not run after the provenance block.
- Scoreable episodes remain `5`; positive-memory-only episodes remain `2`; non-Ansible positive-memory episodes remain `0`.
- Full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
- Current protocol remains `v2.13`; v2.22 is not promoted to current.

## Non-Ansible capability roadmap

The project now tracks the missing non-Ansible execution and repair-instrumentation work in two planning/control files:

- `docs/non_ansible_capability_roadmap.md`
- `configs/non_ansible_capability_backlog.json`

These files are not evidence of a proven capability. They record required future gates for source acquisition, environment locking, BugsInPy command translation, fresh workspaces, baseline preservation, rollback markers, repair-state capture, bounded diagnostic feedback, structural test signatures, patch locality, real-time patch safety, patch application semantics, workspace protection, post-validation analysis, materialized target-test provenance, PySnooper:2 policy, claims boundaries, and future version sequencing.

## Day-to-day checks

Use the generic current interface:

```powershell
python scripts/controllergate_audit.py --protocol current
python scripts/controllergate_run.py --protocol current --dry-run
```

The same interface can explicitly select v2.13:

```powershell
python scripts/controllergate_audit.py --protocol v2.13
python scripts/controllergate_run.py --protocol v2.13 --dry-run
```

The generic runner is dry-run only for now. Non-dry-run evidence generation must be explicitly authorized and should use the versioned runner or a reviewed future current-protocol mechanism.

## Required regression checks for this boundary

```powershell
python scripts/audit_v2_13_minimal_forensic_context_lane.py
python scripts/audit_v2_12_dependency_cofactor_recovery.py
```

On Windows with `core.autocrlf=true`, sparse-checkout materialization may need byte-exact tracked evidence before running manifest-heavy historical audits. Do not weaken audits to accommodate sparse checkout or line-ending conversion.
## v2.23 source acquisition method boundary

v2.23 adds a method-level provenance preflight before any new non-Ansible candidate selection. It records the BugsInPy checkout method as blocked under the current provenance rules because the pinned framework source and the verified v2.22 trace show fixed-commit target-test copying before reset to the buggy commit.

- Campaign: `v2_23_non_ansible_candidate_transition_lane`
- Status: `verified_official_artifact`; v2.23 audit status: `PASS`; v2.23 is not promoted to current.
- Official artifact digest: `sha256:fbbed9f699822b16733a77a8c4b32c960a5ef3fed527059737b645802b0116ca`; byte size: `64784`; ZIP entries: `28`.
- Workflow run: `28211816313`; artifact ID: `7895186058`.
- Internal SHA256SUMS: `21` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `22` entries after adding the local official artifact-verification record.
- Method decision: `globally_blocked_under_current_provenance_rules`.
- Candidate selection: `not_run_global_method_block`; no new BugsInPy candidate was selected.
- Dependency recovery, pre-repair replay, patch generation, validation, duplicate replay, and scoring were not run.
- v2.24 recommendation: External Safe-Source Candidate Acquisition Lane.
- Current protocol remains `v2.13`; full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
## v2.24 external candidate registry precheck

v2.24 starts the external safe-source pivot with an External Candidate Registry precheck. Because `configs/external_candidate_registry.json` currently contains no reviewed entries, the lane blocks before cloning any repository or selecting any candidate.

- Campaign: `v2_24_external_safe_source_candidate_acquisition_lane`
- Status: `verified_official_artifact`; v2.24 audit status: `PASS`; v2.24 is not promoted to current.
- Official artifact digest: `sha256:1801c197bb032c415dea4a33a9208042b0377d069e95fc4cde1ab4e0f2e7db8d`; byte size: `51049`; ZIP entries: `20`.
- Workflow run: `28212746325`; artifact ID: `7895535773`.
- Internal SHA256SUMS: `12` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `13` entries after adding the local official artifact-verification record.
- Blocker: `blocked_external_candidate_registry_missing_or_invalid`.
- Candidate selection: `not_run_no_valid_registry_entries`.
- External clone, failure capture, dependency setup, executed-scope tracing, patch generation, validation, duplicate replay, and scoring were not run.
- Safest next step: `create_reviewed_external_candidate_registry_entry`.
- Recommended next lane: `v2.25 External Candidate Registry Construction Lane`.
- Current protocol remains `v2.13`; full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
## v2.25 external candidate registry construction

v2.25 creates the strict External Candidate Registry infrastructure needed before any future external safe-source candidate run. No reviewed seed was provided in this run, so the lane writes an empty registry, schema, validator, audit outputs, and stops before any clone, candidate selection, repair, patch, validation, or scoring step.

- Campaign: `v2_25_external_candidate_registry_construction_lane`
- Status: `verified_official_artifact`; v2.25 audit status: `PASS`; v2.25 is not promoted to current.
- Official artifact digest: `sha256:41ac43048ca834c203542b2e0b9c9045c2ceb1be43a963cf2d4c66ca250864b2`; byte size: `61756`; ZIP entries: `27`.
- Workflow run: `28213908809`; artifact ID: `7895944211`.
- Internal SHA256SUMS: `17` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `18` entries after adding the local official artifact-verification record.
- Registry schema: `configs/external_candidate_registry.schema.json`.
- Registry config: `configs/external_candidate_registry.json`.
- Seed file present: `false`.
- Exact blocker: `blocked_no_reviewed_external_candidate_seed_provided`.
- Candidate count: `0`; reviewed valid candidate count: `0`.
- Current protocol remains `v2.13`; full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
- Smallest next step: provide `inputs/external_candidate_seed_draft.json` with one manually reviewed seed draft for v2.26.
## v2.26 external candidate seed capture

v2.26 is the External Candidate Seed Capture Lane. It accepts only a manually provided seed draft and does not search, clone, repair, patch, validate a patch, or score anything unless the seed draft exists and passes the safety gates.

- Campaign: `v2_26_external_candidate_seed_capture_lane`
- Status: `implemented_pending_official_artifact_ingestion`; v2.26 is not promoted to current.
- Required seed draft: `inputs/external_candidate_seed_draft.json`.
- Seed draft present in this run: `false`.
- Exact blocker: `blocked_no_external_candidate_seed_draft_provided`.
- External clone attempted: `false`.
- Registry candidate count remains `0`; reviewed valid candidate count remains `0`.
- Current protocol remains `v2.13`; full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
- Smallest next step: provide inputs/external_candidate_seed_draft.json with exactly one manually reviewed seed draft.
## v2.27 external candidate seed draft verification

v2.27 is the External Candidate Seed Draft Verification Lane. It verifies exactly one manually supplied seed draft and may merge one reviewed registry candidate only after native buggy-test, environment, failure-capture, registry, and audit gates pass.

- Campaign: `v2_27_external_candidate_seed_draft_verification_lane`.
- Status: `blocked_no_seed_draft`; v2.27 is not promoted to current.
- Required seed draft path: `inputs/external_candidate_seed_draft.json`.
- Deprecated seed draft path is not canonical: `configs/candidate_seed_draft.json`.
- Seed draft present in this run: `false`.
- Reviewed valid candidate count after run: `0`.
- Registry candidate count after run: `0`.
- Exact blocker: `blocked_no_external_candidate_seed_draft_provided`.
- Repair and patch generation remain disabled.
- Current protocol remains `v2.13`; full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
- Smallest next step: provide inputs/external_candidate_seed_draft.json with exactly one manually reviewed seed draft.
## v2.28 external candidate seed draft verification

v2.28 verifies the Brad-supplied py-bugger External Candidate Seed Draft and may merge one reviewed registry candidate only after direct checkout, native target-test, support-file, environment, failure-capture, and registry gates pass.

- Campaign: `v2_28_external_candidate_seed_draft_verification_lane`.
- Seed candidate: `py_bugger_issue_65`.
- Current result: `verified_external_candidate_seed_added`.
- Registry candidate count after run: `1`.
- Reviewed valid candidate count after run: `1`.
- Repair and patch generation remain disabled.
- Current protocol remains `v2.13`; full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.
## v2.29 external candidate repair lane

v2.29 adds the Structural Repair Capability Integration Lane and runs at most one bounded source-only repair attempt for the reviewed `py_bugger_issue_65` candidate.

- Candidate scope: exactly `py_bugger_issue_65`.
- Capability controls: AST Dependency Closure, Context Pinching Filter, diagnostic Failure Memory Weight Ledger, Fragmented Patch Assembly Gate, and Pre/Post Handoff Consistency Gate.
- Current protocol remains `v2.13`; full scoring remains `NOT_RUN` / disallowed; memory lift and self-maintaining software remain undemonstrated.




## v2.30 failure signature canonicalization and repair continuation

v2.30 keeps scope on the reviewed `py_bugger_issue_65` candidate and resolves the v2.29 text-hash mismatch only through a versioned semantic failure signature.

- Historical v2.28 and v2.29 normalized text hashes remain preserved.
- Repair can proceed only after three clean pre-repair captures agree on the semantic signature.
- The lane still allows at most one bounded source-only patch and three duplicate clean replays before any scoreable result.
- Current protocol remains `v2.13`; full scoring remains disabled; memory lift and self-maintaining software remain undemonstrated.


## v2.31 scoreable external repair episode consolidation


ControllerGate has now crossed an important evidence boundary: v2.30 produced the first official scoreable external non-Ansible source-only repair episode, and v2.31 consolidates that result without attempting another repair.

- Consolidated episode: `py_bugger_issue_65` from v2.30.
- Patch boundary: source-only, one file, patch SHA256 `02ada076e824bb703bc02d1c33f75f51eb4db4539a5aac8e4f5fa3fedd4972ee`.
- Validation carry-forward: target validation `PASS`, duplicate clean replay `3 / 3`, observed replay reliability `1.0`.
- External repair episode registry: `configs/external_repair_episode_registry.json`.
- Current protocol remains `v2.13`; v2.30 and v2.31 are not promoted to current.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Next engineering target: add 2-3 more reviewed external candidates through the registry/seed pipeline, or run a prospective second external repair lane if a second reviewed candidate is already available.



## v2.32 second external candidate seed and matched-null protocol lock


v2.32 preserves the first scoreable external repair episode and locks the future matched-null memory experiment protocol. No second seed draft is present in this run, so no external repository is cloned and no candidate #2 is selected.

- First scoreable episode remains `py_bugger_issue_65` from v2.30/v2.31.
- Scoreable external repair episode count remains `1`.
- Second seed draft path: `inputs/external_candidate_seed_draft_v2_32.json`.
- Second seed present: `false`.
- Exact blocker: `blocked_no_second_external_candidate_seed_draft_provided`.
- Candidate #2 repair attempted: `false`.
- Patch generated: `false`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.




## v2.33 candidate #2 seed intake and matched-null experiment status


v2.33 ingests the official v2.32 artifact and checks for a manually supplied candidate #2 seed at `inputs/external_candidate_seed_draft_v2_33.json`. No seed is present in this run, so candidate #2 is not selected and the matched-null repair experiment is not attempted.

- Exact blocker: `blocked_no_second_external_candidate_seed_draft_provided`.
- Candidate #2 discovery packet: created under `outputs/v2_33_candidate2_matched_null_memory_repair_lane/`.
- First scoreable external repair episode remains `py_bugger_issue_65`.
- Reviewed valid candidate count remains `1`.
- Candidate #2 repair attempted: `false`.
- Patch generated: `false`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.

## v2.34 candidate #2 seed workbench and byte-custody status


v2.34 ingests the official v2.33 boundary, adds reusable byte-custody preflight tooling, rejects the six currently unverified candidate #2 leads, and installs a seed-verification workbench for a future manually supplied seed.

- Current protocol remains `v2.13`; v2.34 is not promoted.
- Valid candidate #2 seed present: `false`.
- Exact blocker: `blocked_no_valid_second_external_candidate_seed_provided`.
- Prior invalid lead count recorded as rejected: `6`.
- Candidate #2 selected: `false`.
- Repair attempted: `false`; patch generated: `false`.
- Matched-null experiment attempted: `false`.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.
- Next step: place one valid seed at `inputs/external_candidate_seed_draft_v2_34.json` or a future-lane seed path.

## v2.35 automated candidate #2 acquisition status


v2.35 adds an automated candidate #2 acquisition sprint. The lane uses public metadata only as lead evidence and requires direct ControllerGate verification before any candidate can enter the registry.

- Repositories attempted: `5`.
- Candidate commits attempted: `17`.
- Verified second seed acquired: `false`.
- Exact blocker: `blocked_no_verified_candidate2_seed_acquired`.
- Registry reviewed valid candidate count remains `1`.
- Matched-null repair experiment attempted: `false`.
- Patch generated: `false`.
- Current protocol remains `v2.13`; v2.35 is not promoted.
- Full scoring remains `NOT_RUN/disallowed`.
- Memory lift remains `undemonstrated`.
- Self-maintaining software remains `false/not_demonstrated`.

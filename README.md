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

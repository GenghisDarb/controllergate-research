# ControllerGate TLD / Resolution-Depth Map

This document is an architecture note and planning control. It is not empirical proof that TORUS/TLD physics has been validated by ControllerGate, and it does not weaken any ControllerGate evidence gate, audit, provenance rule, or claim boundary.

## Interpretation

ControllerGate treats chaotic-looking blockers as under-resolved metrology states: the system may not yet have enough source, harness, environment, transport, or diagnostic precision to distinguish a real repair opportunity from an unsafe or unproven setup. A blocker is therefore a resolution report, not proof of impossibility.

## Version-to-resolution mapping

- v2.18 corresponds to the approximate `N≈6` emergence/source-acquisition threshold: the public PySnooper buggy source commit became resolvable.
- v2.19 corresponds to the approximate `N≈7` test-provenance threshold: the target test content remained unresolved.
- v2.20 targets the `N≈7–N≈8` region: coupled target-test provenance plus harness topology.
- v2.21 targets the `N≈7.13` harness-origin-pin threshold: non-circular BugsInPy harness authority can be verified independently of workflow-runtime discovery, while target-test content may still remain unresolved.
- v2.22 targets the `N≈7.5` official materialization/source-guard threshold: the BugsInPy framework must materialize the project workspace before target-test absence is terminal, and fixed/future-derived materialization remains unsafe under current rules.
- A future repair/scoreable state corresponds to the `N≈9–N≈10` repair/kernel-lock region.

## Precision instruments

SHA256 hashes, artifact manifests, workspace equivalence checks, command manifests, environment locks, transport hash logs, prompt/context pre-generation hashes, and proof ledgers are ControllerGate's metrological precision instruments. They are analogous to using higher numerical precision to resolve stable structure in a chaotic-looking system.

The 80-digit precision analogy is metrological: it describes observer/instrument precision, not a claim that physical reality requires decimal precision to exist.

## Diagnostic reward interpretation

The graded diagnostic reward signal is the ControllerGate analogue of divergence or near-attractor information. It must distinguish precondition failure, near-cap patch, target failure, and successful validation. A score of `0.0` is reserved for true precondition failures. A patch that exists and is evaluated but fails only by locality/size cap should preserve non-zero diagnostic information below success.

## Patch locality

The patch size cap is a locality/noise-floor protection mechanism. Overshoot metrics must preserve whether a patch was close to the allowed locality threshold or wildly divergent.

## Claim boundaries

A scoreable PySnooper:1 result may be recorded only as one non-Ansible scoreable episode. It must not be reported as full generalization, full scoring, self-maintaining software, broad memory lift, or proof of TORUS/TLD.
## v2.23 Source Acquisition Method Boundary

v2.23 records a method-level provenance boundary rather than a repair attempt.

- Method decision: `globally_blocked_under_current_provenance_rules`.
- Evidence basis: verified v2.22 runtime trace plus pinned BugsInPy source-code lines from `framework/bin/bugsinpy-checkout`.
- Blocker: `blocked_bugsinpy_acquisition_method_fixed_commit_test_copy_global_or_unproven_candidate_specific_safety`.
- Next action: move candidate acquisition to external safe sources where the buggy project tree and test provenance can be verified without fixed/future/gold/synthetic test materialization.
- This is a benchmark/source-provenance boundary finding, not a ControllerGate repair failure.
## v2.24 External Candidate Registry Precheck

v2.24 records an external-candidate intake boundary before any repair attempt.

- Boundary: reviewed registry entries are required before external candidate selection.
- Result: `blocked_external_candidate_registry_missing_or_invalid`.
- No public issue was selected directly.
- No external repository was cloned.
- Next action: `create_reviewed_external_candidate_registry_entry`.
## v2.25 External Candidate Registry Construction

v2.25 records the registry-construction boundary.

- Registry schema: present.
- Validator: present.
- Reviewed seed: absent.
- External clone attempted: `false`.
- Candidate selected: `false`.
- Result: `blocked_no_reviewed_external_candidate_seed_provided`.
## v2.26 External Candidate Seed Capture

v2.26 records the seed-capture boundary.

- Seed draft: absent.
- External clone attempted: `false`.
- Candidate selected: `false`.
- Registry merge: `not_run_seed_draft_absent`.
- Result: `blocked_no_external_candidate_seed_draft_provided`.
## v2.27 External Candidate Seed Draft Verification

v2.27 records the seed-draft verification boundary.

- Seed draft: `false`.
- External clone attempted only when schema and source guards pass.
- Registry merge is permitted only after source/test co-location, environment, and failure capture pass.
- Result: `blocked_no_external_candidate_seed_draft_provided`.
## v2.28 External Candidate Seed Draft Verification

v2.28 records the seed-draft verification boundary for a py-bugger candidate.

- Candidate: `py_bugger_issue_65`.
- Registry merge requires failure capture from the direct checked-out commit.
- Result: `seed_capture_environment_resolution_failed`.
## v2.29 Structural Repair Capability Integration

v2.29 moves the external candidate path from verified seed capture to a bounded repair attempt with source-context narrowing and validation custody.

- Candidate: `py_bugger_issue_65`.
- Scope: one reviewed external candidate and one possible source-only patch.
- Stop condition: any registry, replay, context, patch-safety, validation, or duplicate-replay mismatch blocks before broader claims.


## v2.30 Failure Signature Canonicalization

v2.30 moves the reviewed external candidate from text-hash mismatch to semantic replay agreement before any repair attempt.

- Candidate: `py_bugger_issue_65`.
- Scope: one reviewed external candidate and one final source-only patch maximum.
- Stop condition: any semantic replay, registry refresh, context, patch-safety, validation, or duplicate-replay mismatch blocks broader claims.


## v2.31 consolidation status


v2.31 marks the first consolidated scoreable external repair episode, not a protocol promotion.

- One reviewed external candidate has a scoreable source-only repair episode.
- The result is enough to update planning and readiness, but not enough for full scoring, memory-lift, broad-generalization, or self-maintaining claims.
- The next precision target is multiple reviewed external candidates or a prospective second repair episode under frozen comparison rules.


## v2.32 protocol lock status


v2.32 is a protocol-lock and seed-intake boundary.

- One scoreable external repair episode is preserved.
- Candidate #2 is not selected unless Brad supplies a seed draft.
- Memory lift remains a future prospective comparison question, not a retrospective claim.

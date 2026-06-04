# v1.8 Controlled Repo Replay-First Capture Plan

Status: planning and audit layer only. Do not score.

ControllerGate v1.8 will use a user-owned public repository, initially the TORUS Theory repo, as a controlled replay-first capture target. This is not a performance result and not a self-maintaining software claim. The purpose is to generate fresh deterministic replay-ready episodes from birth, with full artifact custody, rather than trying to rescue expired or incomplete historical evidence.

## Why TatMapper Remains Ineligible

The v1.7-beta TatMapper historical episodes remain `review_required`.

- 11 of 11 TatMapper episodes were reviewed.
- 0 of 11 are deterministic-replay-ready.
- PR #92 and PR #93 have failed Flutter CI run/job metadata, but decoded logs returned GitHub API `410`.
- The other nine TatMapper source SHAs exposed no PR-triggered workflow runs through the connector.
- Current-head evidence remains outcome-only and is not PR-head proof.
- Full scoring remains disallowed.
- Real-repo memory lift is not demonstrated.
- Self-maintaining software is not demonstrated.

TatMapper is useful evidence that the pipeline can ingest and quarantine historical real-repo evidence. It is not yet usable for deterministic replay scoring.

## Why TORUS Theory Is Useful

Brad has authorized the public TORUS Theory repo as a user-owned controlled testbed. Because it can be cloned, branched, instrumented, and rebuilt under controlled conditions, it can generate replay-first episodes with complete logs and hashes from birth.

The TORUS repo may be used for controlled seeded failures, fixtures, check scaffolds, CI configs, repair tasks, and proof-obligation ledgers. All work must remain ethical, reversible through Git history, and fully artifact-preserving.

The repo is useful as an authorized testbed, not as proof by itself.

## Controlled Target Repo Policy

- Target repo class: `user_owned_public_repo`.
- Preferred initial target: `GenghisDarb/TORUS-Theory`.
- Repo may be forked, branched, cloned, instrumented, and seeded with controlled failures.
- Original repo states must be snapshotted and hashed before modification.
- Testbed changes must be made on clearly named branches.
- Generated episodes must include before/after SHAs.
- No claim may depend on uncaptured remote-only logs.
- No useful source material should be destroyed without preserved snapshots and hashes.

## Candidate Target Acceptance Criteria

A repo or branch is acceptable only when:

- It is owned or explicitly authorized by Brad.
- A clean clone can be obtained.
- Baseline SHA is recorded.
- Dependency/install commands are documented or can be created honestly.
- A test/build/lint/check command exists or can be introduced honestly.
- A failure can be generated or discovered reproducibly.
- Failure logs can be captured locally.
- Patch/action trace can be preserved.
- Post-repair validation can be captured locally.
- SHA256 manifest can cover all input/output artifacts.

## Controlled Failure Types

Allowed:

- failing unit test
- lint failure
- formatting failure
- type-check failure
- build failure
- dependency-lock failure
- documentation-link/check failure
- schema/validation failure
- small deterministic bug with test oracle

Disallowed:

- security exploit tasks
- secrets or credential extraction
- destructive data deletion without snapshot
- tasks requiring private third-party services
- network-only proof without local replay
- vague quality improvement tasks without a deterministic validator
- subjective theory-content rewrites as repair targets unless paired with deterministic checks

## Episode Birth-Capture Schema

Every TORUS-repo replay-first episode must capture:

- `episode_id`
- `target_repo_url`
- `target_repo_branch`
- `baseline_sha`
- `task_head_sha` or `failing_sha`
- `post_repair_sha`, if repair is attempted
- `original_repo_snapshot_manifest`
- `changed_files_snapshot`
- `dependency_lock_files`
- `environment_snapshot`
- `setup_command`
- `failing_command`
- `failing_log_raw`
- `failure_signature`
- `pre_repair_replay_transcript`
- `decision_time_inputs`
- `controllergate_action_trace`
- `repair_patch_diff`
- `post_repair_command`
- `post_repair_log_raw`
- `post_repair_outcome`
- `no_memory_baseline_result`, if run
- `always_rebuild_baseline_result`, if run
- `memory_enabled_result`, if run
- `corruption_check_result`
- `human_required_flag`
- `decision_time_outcome_overlap_check`
- `sha256_manifest_path`
- `proof_obligations_ledger_path`
- `allowed_scoring_mode`

## Replay Gate

Discard an episode before scoring if:

- A clean checkout cannot reproduce the pre-repair failure.
- The failing log is missing.
- The failure signature is missing.
- The repair patch/action trace is missing.
- Post-repair validation is missing.
- Decision-time inputs include future outcome evidence.

Additional boundaries:

- If no-memory baseline instrumentation is absent, do not claim memory lift.
- If baseline comparators are absent, do not claim ControllerGate advantage.
- If only a seeded failure is used, label it `seeded_controlled_real_repo_episode`, not external organic evidence.

## Allowed Labels And Scoring Modes

Allowed episode labels:

- `seeded_controlled_real_repo_episode`
- `discovered_user_owned_repo_episode`
- `forked_public_repo_episode`
- `synthetic_realistic_repo_episode`
- `historical_review_required_episode`

Allowed scoring modes:

- `not_scoreable`
- `review_required`
- `deterministic_replay_ready`
- `limited_replay_scoring_only`
- `full_scoring_disallowed`

Full scoring remains disallowed in this pass.

## Initial v1.8 Pilot Design

Start with 1 to 3 replay-first TORUS episodes only.

Prefer deterministic seeded failures first to validate the capture pipeline:

- introduce a failing documentation consistency check
- introduce a broken schema validation fixture
- introduce a failing unit test around glossary/metadata parsing
- introduce a deterministic build/lint failure
- introduce a broken internal link checker

Do not use subjective TORUS theory correctness as the first validator. The first goal is to prove the replay-capture machinery, not to prove repair intelligence.

## Seeded Evidence Boundary

Seeded controlled real-repo episodes are weaker than organic external repo evidence because the failure is deliberately introduced under known conditions. They are stronger than non-replayable historical evidence because they can preserve baseline SHA, failure logs, repair patch, post-repair validation, environment, and hashes from birth.

That means seeded TORUS episodes may validate replay capture, but they do not prove broad real-repo repair ability.

## Before Capability Scoring

Before any capability scoring, ControllerGate needs:

- replay-ready episodes with local pre-repair reproduction
- preserved failure signatures
- preserved action/repair traces
- post-repair validation logs
- baseline comparator conditions
- no-memory baseline instrumentation if memory lift is claimed
- decision-time/outcome separation
- artifact SHA256 manifests

Without those, scoring remains blocked or limited to review-only reporting.

## Falsification and Stop Conditions

- If no replay-ready episodes can be produced even in the user-owned TORUS Theory repo, ControllerGate real-repo capability remains blocked.
- If replay-ready episodes are produced but ControllerGate cannot repair them under preregistered metrics, this ControllerGate version fails the controlled repo capability claim.
- If memory-enabled ControllerGate does not outperform no-memory baselines under replay-ready conditions, real-repo memory lift is not demonstrated.
- If ControllerGate only succeeds on seeded failures but fails on discovered organic failures, claims must remain limited to seeded controlled episodes.
- If repeated replay-ready pilots show no maintainability advantage, freeze or redesign the architecture rather than weakening the evidence standard.
- Failure of this version does not falsify all possible self-maintaining software, but it does falsify the stronger claims of the current version.

## Conservative Boundary

Do say:

- TORUS Theory repo is authorized as a controlled testbed.
- Seeded controlled real-repo episodes may validate replay capture.
- Replay Gate must pass before scoring.
- Self-maintaining software remains undemonstrated.
- Memory lift remains undemonstrated until baselines pass under replay-ready conditions.

Do not say:

- ControllerGate has demonstrated real-repo repair.
- TORUS repo tests prove self-maintaining software.
- Seeded failures equal organic external evidence.
- Memory lift is demonstrated.
- Full scoring is allowed.

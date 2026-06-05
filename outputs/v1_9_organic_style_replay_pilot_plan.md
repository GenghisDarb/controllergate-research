# v1.9 Organic-Style Controlled Discovery / External-Fork Replay Pilot Plan

Status: planning only. Do not execute v1.9 yet. Do not run full scoring.

## Why v1.8 Matters

v1.8 is a real positive milestone because Episodes 004-010 met the preregistered limited seeded controlled memory-lift criteria under replay-ready conditions.

The v1.8 campaign produced:

- 7 executed limited replay-scoring episodes.
- 7 deterministic replay-ready seeded controlled episodes.
- 6 positive seeded memory-lift episodes.
- 1 inconclusive equal-performance episode.
- 0 blocked episodes.
- 0 corruption episodes.
- 0 decision-time/outcome overlap.

Episode 003 remains preserved as negative evidence for memory lift on a simple local seeded `HASH_MISMATCH: README.md` task. That result matters because it shows memory is not being credited on every task by default.

## Why v1.8 Is Still Limited

The v1.8 positive result is limited to seeded controlled replay tasks. It does not demonstrate organic external repo memory lift, full scoring, or self-maintaining software.

Seeded controlled tasks are useful because they test specific memory-relevant pathologies under clean custody. They are weaker than discovered or organic-style software-maintenance evidence because the failure families were intentionally designed.

## Why v1.9 Is Needed

v1.9 should test whether the v1.8 memory advantage survives on less scripted, more organic software-maintenance failures while preserving replay-first custody.

Allowed target classes:

- `user_owned_repo_discovered_failure`
- `user_owned_repo_semi_organic_failure`
- `forked_public_repo_discovered_failure`
- `forked_public_repo_issue_replay`
- `archived_public_repo_dependency_drift`
- `synthetic_seeded_fallback_only_if_no_discovered_failure`

The preferred pilot size is 3 to 5 episodes. At least one user-owned discovered failure and one forked public repo replay should be attempted if feasible. If public repo discovery is too costly, v1.9 should start with user-owned discovered or semi-organic failures. The pilot should avoid overfitting to the seeded manifest tasks from v1.8.

## Acceptance Criteria

A candidate can be accepted only if:

- The repo is user-owned, forked, or locally cloned ethically.
- The license permits local testing/forking, or Brad owns it.
- The failure can be reproduced from clean checkout.
- The failure is discovered or semi-organic where possible.
- No private secrets or credentials are required.
- A deterministic validator command exists.
- No-memory and memory-enabled paths can run under identical replay conditions.
- Corruption or downstream checks can be defined.
- All logs and artifacts can be captured and hashed.
- Decision-time/outcome separation can be enforced.

## Rejection Criteria

Reject a candidate if:

- The failure depends only on expired CI logs.
- Local replay cannot reproduce it.
- Setup requires private services or secrets.
- The validator is subjective.
- The task is security exploit focused.
- The task requires broad theory-content judgment.
- Artifact custody cannot be preserved.
- Baseline comparison cannot be run.

## Required Episode Artifacts

Every v1.9 episode must capture:

- `episode_metadata.json`
- `target_repo_snapshot.json`
- `candidate_selection_record.json`
- `environment_snapshot.txt`
- `failing_command.txt`
- `failing_log_raw.txt`
- `failure_signature.txt`
- `pre_repair_replay_transcript.txt`
- `no_memory_decision_time_inputs.json`
- `no_memory_action_trace.json`
- `no_memory_repair_patch.diff`
- `no_memory_post_repair_log_raw.txt`
- `no_memory_outcome.json`
- `memory_enabled_decision_time_inputs.json`
- `memory_enabled_action_trace.json`
- `memory_evidence_used.json`
- `memory_enabled_repair_patch.diff`
- `memory_enabled_post_repair_log_raw.txt`
- `memory_enabled_outcome.json`
- `post_repair_comparison.json`
- `corruption_check_result.json`
- `decision_time_outcome_overlap_check.json`
- `limited_scoring_result.json`
- `proof_obligations_ledger.json`
- `SHA256SUMS.txt`

## Evidence Classifications

Each episode must be classified as exactly one:

- `positive_evidence_memory_lift_organic_style_episode`
- `negative_evidence_no_memory_lift_organic_style_episode`
- `negative_evidence_memory_harm_or_corruption_organic_style_episode`
- `blocked_replay_gate_failed`
- `blocked_missing_baseline`
- `blocked_artifact_custody_failure`
- `blocked_decision_time_outcome_overlap`
- `inconclusive_equal_performance`
- `not_executed_resource_limit`

## Aggregate Rule

Organic-style memory lift remains undemonstrated unless:

- At least 3 v1.9 episodes become deterministic replay-ready limited scoring episodes.
- Memory-enabled outperforms no-memory in at least 2 episodes.
- No positive memory episode has corruption.
- Decision-time/outcome overlap remains 0.
- Replay/custody passes for all positive episodes.

If fewer than 3 scoreable v1.9 episodes complete, classify the result as `insufficient_episode_count_for_organic_style_memory_lift`.

If memory never outperforms no-memory, classify the result as `negative_evidence_no_organic_style_memory_lift`.

If all candidates are blocked by replay/custody, classify the result as `blocked_candidate_acquisition_failure`, not negative capability evidence.

## Evidence Interpretation

Positive evidence would be a replay-ready episode where memory-enabled ControllerGate outperforms no-memory under identical replay conditions without corruption.

Negative evidence would be a replay-ready episode where memory-enabled ControllerGate does not outperform no-memory or causes harm/corruption.

Blocked evidence would be missing replay, missing baseline, artifact-custody failure, decision-time/outcome overlap, or environment setup failure. Blocked evidence is not negative capability evidence.

Inconclusive evidence would be equal comparable performance without a clear memory advantage.

## Claim Boundaries

Full scoring remains `NOT_RUN`.

Self-maintaining software remains undemonstrated.

Organic external memory lift remains undemonstrated.

v1.8 seeded controlled memory lift does not imply organic external memory lift.

v1.9 organic-style success would still be limited replay evidence, not full self-maintenance.

External public repo results must be labeled separately from user-owned repo results.

## Stop Conditions

Stop v1.9 execution if:

- Replay gate repeatedly fails.
- Artifact custody fails.
- Decision-time/outcome leakage appears.
- Memory-enabled causes repeated corruption.
- Candidate acquisition consumes too much resource without replayable tasks.

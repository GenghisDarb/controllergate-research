# Shareable v1.7-beta Limited TatMapper Pilot Summary

ControllerGate v1.7-beta limited TatMapper scoring was run on 11 normalized TatMapper external real repo episodes. This is tiny second-repo exploratory evidence only, not proof of self-maintaining software.

## Result

`COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`

## What Passed

- The run used only the 11 v1.7-beta TatMapper `external_real_repo_episode` entries.
- v1.7-alpha TORUS episodes, v1.6 controlled benchmark evidence, and correction-review episodes were excluded.
- Scoring mode stayed `limited_pilot_only`.
- Full scoring stayed disallowed.
- All weak, ambiguous, warning-only, closed-unmerged, unavailable-CI, and `review_required` episodes stayed visible.
- Decision-time and outcome-only evidence stayed separated.
- `decision_time_outcome_overlap_episode_count: 0`.

## What Did Not Pass As A Strong Claim

- Passed episodes: 0.
- Failed episodes: 0.
- Review-required episodes: 11.
- Deterministic pass/fail performance evidence: 0.
- Memory baselines: unavailable.
- Real-repo memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

## Main Caveats

- Full GitHub Actions logs were unavailable for selected TatMapper PRs and commits.
- Fresh local reruns were current-head-only, timed out, unavailable, or blocked by Java, Flutter, OpenCV, or tooling gaps.
- Original agent/tool transcripts were unavailable.
- All 11 episodes remained `review_required`.

## Recommendation

Do not expand scoring yet. Strengthen TatMapper evidence with full CI logs, PR-head reruns, deterministic Flutter or Android build checks, original agent traces, and memory-baseline instrumentation before any full-scoring or memory-lift claim.

## Evidence Strengthening Pass 1

TatMapper deterministic replay readiness audit is complete.

- Deterministic replay-ready episodes: 0.
- PR #92 and PR #93 now have failed Flutter CI run/job metadata.
- PR #92 run: `17984606083`, failed jobs `test` (`51159403854`) and `android-build` (`51159403859`).
- PR #93 run: `17986583215`, failed jobs `test` (`51166385920`) and `android-build` (`51166385937`).
- Decoded job logs for those runs returned GitHub API `410`, so full logs remain unavailable.
- The other nine TatMapper source SHAs exposed no PR-triggered workflow runs through the connector.
- Current-head strengthening SHA: `8f49190a6e9ae29c8c49301a7736e0f838dfd369`.
- Current-head strengthening remains outcome-only, not PR-head proof.
- Flutter version/analyze/test timed out, Java was not found, Gradle was blocked by missing Java/JAVA_HOME, guard calibration passed, and OpenCV discovery failed because `OpenCVConfig.cmake` was missing.

Correct interpretation remains unchanged: the limited pilot is `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`; real-repo memory lift is not demonstrated; self-maintaining software is not demonstrated; full scoring remains blocked.

## Evidence Strengthening Pass 2

Replay-eligibility pathway is now complete.

- 11 of 11 TatMapper episodes were reviewed for replay eligibility.
- 0 of 11 TatMapper episodes are deterministic-replay-ready.
- 11 of 11 remain review-required.
- Full scoring remains disallowed.
- ControllerGate full scoring remains NOT RUN.
- Current-head evidence is still outcome-only and is not PR-head proof.

Pass 2 defines the missing evidence needed to convert an episode from `review_required` to `deterministic_replay_ready`: base SHA, full changed-files snapshot, full failing job log, failure signature, pre-repair command, repair patch, post-repair validation command, outcome evidence tied to PR/merge/commit head, toolchain versions, original agent trace, and memory-baseline instrumentation where memory-lift scoring is intended.

The current TatMapper set is not deterministic-replay-ready. v1.7-beta now includes a replay-eligibility pathway, but scoring must not be expanded.

## v1.8 controlled repo replay-first path

ControllerGate v1.8 adds a planning/audit layer for controlled replay-first evidence capture.

- TORUS Theory repo is authorized as a controlled testbed.
- The target role is user-owned public repo replay capture, not proof.
- Seeded controlled real-repo episodes may validate replay capture.
- Seeded controlled episodes are weaker than organic external repo evidence.
- Seeded controlled episodes are stronger than non-replayable historical evidence when they preserve SHAs, logs, commands, patches, transcripts, and SHA256 manifests from birth.
- Replay Gate must pass before scoring.
- Full scoring remains disallowed.
- Self-maintaining software remains undemonstrated.
- Memory lift remains undemonstrated until baselines pass under replay-ready conditions.

The initial v1.8 TORUS pilot should use only 1 to 3 small replay-first episodes, preferably deterministic seeded failures such as a documentation consistency check, schema validation fixture, glossary/metadata parsing unit test, deterministic lint/build failure, or internal link checker. Do not use subjective TORUS theory correctness as the first validator.

If no replay-ready episodes can be produced even in the user-owned TORUS Theory repo, ControllerGate real-repo capability remains blocked. If replay-ready episodes are produced but ControllerGate cannot repair them under preregistered metrics, this ControllerGate version fails the controlled repo capability claim.

## v1.8 Episode 001 dry-run capture plan

Episode 001 is a dry-run capture plan.

- The TORUS repo is a controlled testbed.
- Episode label: `seeded_controlled_real_repo_episode`.
- Allowed scoring mode: `not_scoreable`.
- The purpose is to validate replay capture, not repair capability.
- Proposed validator: metadata manifest validation.
- Proposed command: `python tools/validate_metadata_manifest.py metadata_manifest.json`.
- Required artifacts include clean clone transcript, baseline SHA, original snapshot manifest, raw failing log, failure signature, decision-time inputs, repair patch/action trace if repair is attempted, post-repair validation log, SHA256 manifest, and proof obligations ledger.
- No scoring is allowed yet.
- ControllerGate has not repaired TORUS.
- Self-maintaining software is not demonstrated.
- Memory lift is not demonstrated.
- Seeded controlled evidence does not equal organic external repo evidence.

Episode 002 may only advance toward limited replay scoring after Episode 001 proves the capture harness: clean checkout reproduces the failure, post-repair validation is replayable if repair is attempted, SHA256 manifests validate, proof obligations are complete, and decision-time/outcome overlap remains zero.

## v1.8 Episode 001 artifact dry-run result

Episode 001 validates replay-capture artifact generation.

- The TORUS repo was used as a controlled user-owned testbed.
- Episode label: `seeded_controlled_real_repo_episode`.
- Allowed scoring mode: `not_scoreable`.
- Replay gate status: `capture_complete_not_scoreable`.
- Failure type: deterministic metadata manifest validation failure.
- Failure signature: `MISSING_REQUIRED_FIELD: version`.
- Failing SHA: `1757e666f5477b7e0d9bfc4a734298efc667eb54`.
- Post-repair SHA: `0b95051230961b5be30f2c91679417162b9e5ceb`.
- Clean checkout replay reproduced the failure at the failing SHA and the pass at the post-repair SHA.
- SHA256SUMS and proof obligations ledger are present for the artifact bundle.
- Decision-time/outcome overlap remains zero.
- Episode 001 remains `not_scoreable`.
- This is seeded controlled evidence, not organic external evidence.
- ControllerGate has not repaired TORUS.
- Memory lift is not demonstrated.
- Self-maintaining software is not demonstrated.
- Full scoring is not allowed.

This result moves v1.8 from plan-only to replay-capture artifact generation for one controlled seeded episode. It still does not permit ControllerGate scoring, memory-lift claims, or self-maintaining-software claims.

## v1.8 Episode 002 dry-run capture plan

Episode 002 is a dry-run capture plan.

- The TORUS repo remains a controlled testbed.
- Episode label: `seeded_controlled_real_repo_episode`.
- Allowed scoring mode: `not_scoreable`.
- Execution status: `not_executed`.
- The purpose is to validate replay capture for a second failure class, not repair capability.
- Proposed validator: metadata manifest validation.
- Proposed command: `python tools/validate_metadata_manifest.py metadata_manifest.json`.
- Proposed seeded failure: `version` has the wrong JSON type.
- Expected failure signature: `TYPE_MISMATCH: version`.
- Episode 001 remains `capture_complete_not_scoreable`.
- Episode 002 remains `not_scoreable`.
- No scoring is allowed yet.
- ControllerGate has not repaired TORUS.
- Self-maintaining software is not demonstrated.
- Memory lift is not demonstrated.
- Seeded controlled evidence does not equal organic external repo evidence.

Episode 002 artifact execution must be explicitly approved separately. The plan only expands the replay-capture ladder from a missing-field failure class to a type-mismatch failure class.

## v1.8 Episode 002 artifact dry-run result

Episode 002 validates replay-capture artifact generation for a second deterministic failure class.

- The TORUS repo was used as a controlled user-owned testbed.
- Episode label: `seeded_controlled_real_repo_episode`.
- Allowed scoring mode: `not_scoreable`.
- Replay gate status: `capture_complete_not_scoreable`.
- Failure type: deterministic metadata manifest version type mismatch.
- Failure signature: `TYPE_MISMATCH: version`.
- Failing SHA: `b885768acfa60fc434c79baf51a3b7b05c1e7ae8`.
- Post-repair SHA: `9868c7e76b4675939d56195427ed49faa2816ed9`.
- Clean checkout replay reproduced the failure at the failing SHA and the pass at the post-repair SHA.
- SHA256SUMS and proof obligations ledger are present for the artifact bundle.
- Decision-time/outcome overlap remains zero.
- Episode 001 remains `capture_complete_not_scoreable`.
- Episode 002 remains `not_scoreable`.
- This is seeded controlled evidence, not organic external evidence.
- ControllerGate has not repaired TORUS.
- Memory lift is not demonstrated.
- Self-maintaining software is not demonstrated.
- Full scoring is not allowed.

This result gives v1.8 two controlled replay-capture bundles across two deterministic failure classes: missing required field and type mismatch. It still does not permit ControllerGate scoring, memory-lift claims, or self-maintaining-software claims.

## v1.8 Episode 003 limited replay-scoring candidate design

Episode 003 is a preregistered limited replay-scoring candidate design.

- Episode 003 is not executed yet.
- Target: TORUS Theory as a controlled user-owned testbed.
- Episode label: `seeded_controlled_real_repo_episode`.
- Allowed scoring mode: `limited_replay_scoring_candidate_not_executed`.
- Proposed failure type: metadata manifest hash mismatch.
- Expected failure signature: `HASH_MISMATCH: README.md`.
- Baselines are mandatory before memory lift can be evaluated.
- Required baseline: no-memory baseline.
- Preferred optional baselines: always-rebuild baseline and simple-rule baseline.
- A memory-enabled ControllerGate path is required before any memory-lift claim can be considered.
- Baseline and memory-enabled paths must use identical replay conditions.
- Replay Gate must pass before any limited scoring.
- Decision-time and outcome-only evidence must remain separated.
- Corruption/downstream checks are required.
- ControllerGate has not demonstrated memory lift.
- ControllerGate has not demonstrated self-maintaining software.
- Full scoring is not allowed.
- Seeded controlled evidence does not equal organic external evidence.
- Episodes 001/002 were capture evidence, not repair-performance evidence.

Positive evidence would require the Replay Gate to pass, baseline and memory-enabled runs to be captured under identical conditions, and the memory-enabled result to outperform no-memory without corruption. Negative evidence would be a replay-ready run where memory-enabled ControllerGate fails to outperform baselines or causes corruption. Blocked evidence would be a failed Replay Gate, missing artifacts, decision-time/outcome overlap, or absent baselines.

## v1.8 Episode 003 limited replay-scoring execution result

Episode 003 is the first controlled limited replay-scoring attempt.

- Target: TORUS Theory as a controlled user-owned testbed.
- Episode label: `seeded_controlled_real_repo_episode`.
- Allowed scoring mode: `limited_replay_scoring_only`.
- Replay gate status: `deterministic_replay_ready_limited_scoring`.
- Failure type: metadata manifest README hash mismatch.
- Failure signature: `HASH_MISMATCH: README.md`.
- Baseline SHA: `6b715d7b81a956ab6d902f818e24a06bcabcdff8`.
- Failing SHA: `a366eb472996b9e057531487b01cdb2a21707d4c`.
- No-memory post-repair SHA: `7116db41452f966d0ed97bff6d95544ebcff754b`.
- Memory-enabled post-repair SHA: `72b2d86b3395d97e309c100df667356bcbc3b2bc`.
- No-memory baseline result: `passed`.
- Memory-enabled path result: `passed`.
- Memory-enabled outperformed no-memory: `false`.
- Result classification: `negative_evidence_no_memory_lift_on_seeded_controlled_episode`.
- Corruption detected: `false`.
- Decision-time/outcome overlap detected: `false`.
- SHA256SUMS and proof obligations ledger are present for the artifact bundle.
- Memory lift is only evaluated against no-memory baseline.
- Memory lift is not demonstrated.
- Full scoring remains disallowed.
- ControllerGate full scoring remains `NOT_RUN`.
- Self-maintaining software remains undemonstrated.
- This is seeded controlled evidence, not organic external evidence.

Positive evidence would have required the memory-enabled path to outperform the no-memory baseline under identical replay conditions without corruption. Episode 003 did not meet that condition because both paths repaired the seeded hash mismatch. This is useful limited negative evidence for memory lift on one seeded controlled episode, not a broad failure of self-maintaining software and not a claim of organic real-repo performance.

## v1.8 Episodes 004-010 memory-relevance campaign

This campaign tests whether memory helps under replay-ready seeded controlled conditions.

- Target: TORUS Theory as a controlled user-owned testbed.
- Episode label: `seeded_controlled_real_repo_episode`.
- Executed episodes: 7.
- Deterministic replay-ready limited scoring episodes: 7.
- Positive seeded memory-lift episodes: 6.
- Negative episodes: 0.
- Inconclusive episodes: 1.
- Blocked episodes: 0.
- Decision-time/outcome overlap count: 0.
- Corruption episode count: 0.
- Aggregate memory-lift assessment: `limited_seeded_controlled_memory_lift_criteria_met`.
- Memory lift scope: seeded controlled replay campaign only.
- Organic external memory lift remains undemonstrated.
- Real-repo memory lift is not generalized.
- Full scoring remains disallowed.
- ControllerGate full scoring remains `NOT_RUN`.
- Self-maintaining software remains undemonstrated.

Positive evidence means replay gate passed, both paths were captured under identical replay conditions, memory-enabled outperformed no-memory on a preregistered dimension, and no corruption occurred. Negative results are valid evidence against this memory design for these task classes. Blocked results reflect missing artifacts or replay failure, not capability failure. Inconclusive evidence means the paths were comparable but memory did not show a distinct advantage.

Validator-level hash mismatch is a valid deterministic target when replay/custody passes. Artifact-custody hash mismatch blocks scoring. Any future claim beyond seeded controlled replay must require organic or externally sourced replay-ready evidence, not this campaign alone.

## v1.9 Organic-Style Replay Pilot Plan

v1.8 met limited seeded controlled memory-lift criteria.

v1.9 is designed to test organic-style replay evidence.

- Plan status: planning only, not executed.
- Target pilot size: 3 to 5 episodes.
- Allowed target classes include user-owned discovered failures, user-owned semi-organic failures, forked public repo discovered failures, forked public repo issue replay, archived public repo dependency drift, and synthetic seeded fallback only if no discovered failure can be obtained safely.
- Every accepted v1.9 candidate must have clean-checkout replay, deterministic validator command, no-memory baseline, memory-enabled path, identical replay conditions, corruption/downstream check, decision-time/outcome separation, and SHA256 artifact custody.
- v1.8 seeded controlled memory lift does not imply organic external memory lift.
- Organic external memory lift remains undemonstrated.
- Self-maintaining software remains undemonstrated.
- Full scoring remains disallowed.
- ControllerGate full scoring remains `NOT_RUN`.

Positive organic-style evidence would require at least 3 deterministic replay-ready v1.9 episodes, with memory-enabled outperforming no-memory in at least 2, no corruption in positive episodes, decision-time/outcome overlap remaining 0, and replay/custody passing for all positive episodes.

Blocked v1.9 candidates are not negative capability evidence if replay, custody, baseline, or environment requirements cannot be satisfied.

## v1.9 Episodes 011-013 organic-style replay pilot

v1.9 tests generalization beyond seeded controlled memory-relevance tasks.

- Episode 011: user-owned semi-organic TORUS data README consistency failure; classification `positive_evidence_memory_lift_organic_style_episode`.
- Episode 012: forked/public candidate acquisition was unavailable under the current restricted local evidence conditions; classification `not_executed_candidate_acquisition_failed`.
- Episode 013: user-owned semi-organic TORUS MkDocs navigation target consistency failure; classification `positive_evidence_memory_lift_organic_style_episode`.
- Scoreable episodes: 2.
- Positive organic-style episodes: 2.
- Not-executed candidate-acquisition episodes: 1.
- Blocked episodes: 0.
- Decision-time/outcome overlap count: 0.
- Corruption episode count: 0.
- Aggregate assessment: `insufficient_episode_count_for_organic_style_memory_lift`.

Episode 011 and Episode 013 are useful positive limited replay signals in a user-owned semi-organic repo setting, but the preregistered v1.9 aggregate requires at least 3 scoreable episodes. Organic-style memory lift remains undemonstrated. Organic external memory lift remains undemonstrated. Self-maintaining software remains undemonstrated. Full scoring remains disallowed.

Blocked acquisition is not negative capability evidence. Negative results under replay-ready conditions would be valid negative evidence for those task classes, but Episode 012 did not reach replay execution.

## v1.9 Organic-Style Replay Pilot Completion Pass

v1.9 was previously positive but underpowered.

- Completion pass attempts to reach the minimum scoreable episode count.
- Episode 014: user-owned semi-organic TORUS README local target consistency failure; classification `positive_evidence_memory_lift_user_owned_organic_style_episode`.
- New scoreable episodes: 1.
- New positive episodes: 1.
- Total v1.9 scoreable episodes: 3.
- Total v1.9 positive memory-outperformance episodes: 3.
- Total v1.9 candidate-acquisition misses preserved: 1.
- Decision-time/outcome overlap count: 0.
- Corruption episode count: 0.
- Aggregate assessment: `limited_user_owned_organic_style_memory_lift_criteria_met`.

Organic-style memory lift is now supported only within the limited user-owned replay scope. Organic external memory lift remains undemonstrated. Semi-organic user-owned evidence does not equal organic external evidence. Self-maintaining software remains undemonstrated. Full scoring remains disallowed.

Blocked acquisition is not negative capability evidence. Organic-style memory lift is only claimed because the preregistered aggregate criteria are met in the limited user-owned replay scope.

## v2.0 External-Fork Replay Pilot Plan

v1.9 met limited user-owned organic-style memory-lift criteria.

- v2.0 is designed to test external/fork replay evidence.
- Target classes include forked public repo discovered failures, forked public issue replay, archived public dependency drift, public benchmark realistic failures, and user-owned fallback only if external acquisition fails.
- External candidates must be public and ethically forkable or locally cloneable.
- Replay must use clean checkout reproduction, local logs, no-memory baseline, memory-enabled path, identical replay conditions, corruption checks, decision-time/outcome separation, and SHA256 artifact custody.
- Organic external memory lift remains undemonstrated.
- Self-maintaining software remains undemonstrated.
- Full scoring remains disallowed.

User-owned results do not prove external public repo performance. A future v2.0 success may support only limited external-fork memory lift, and only if at least three scoreable external/fork episodes complete, at least two show memory outperformance, corruption remains zero, decision-time/outcome overlap remains zero, and replay/custody passes for all positive episodes.

## v2.0 External-Fork Replay Pilot Result

v2.0 tests forked/public replay evidence.

- Candidate attempts: 5
- Scoreable external/fork episodes: 0
- Rejected candidates: 5
- Blocked candidates: 0
- Aggregate assessment: `blocked_external_candidate_acquisition_failure`
- External memory lift remains undemonstrated.
- Full scoring remains disallowed.
- ControllerGate full scoring remains `NOT_RUN`.
- Self-maintaining software remains undemonstrated.

The bounded public-repo candidate scan found no deterministic, non-subjective local replay failure suitable for no-memory and memory-enabled comparison. Blocked candidate acquisition is not negative capability evidence. User-owned v1.9 results do not prove external repo performance.

## v2.1 External Candidate Acquisition Harness Plan

v2.0 blocked at candidate acquisition.

This is not negative capability evidence.

v2.1 designs systematic preflight candidate mining.

- Source tiers prioritize curated bug benchmarks, small public repos with simple tests, archived dependency-drift repos, forked issue replay candidates, and user-owned fallback only as non-external harness validation.
- Candidate preflight checks include clone/fork availability, license/ethics screen, ecosystem detection, install/test command detection, clean checkout baseline, deterministic failure presence, runtime budget, baseline feasibility, corruption-check feasibility, and artifact custody.
- Candidate readiness is scored from 0 to 100, with candidates below threshold barred from v2.2 execution.
- Candidate acquisition success is not repair success.
- Candidate pool creation is not external memory lift.
- Blocked candidates are not negative capability evidence.
- External memory lift remains undemonstrated.
- Self-maintaining software remains undemonstrated.
- Full scoring remains disallowed.

## v2.1 External Candidate Acquisition Harness Result

v2.1 implements candidate acquisition/preflight.

- Harness implemented: true
- Candidate pool produced: true
- Candidate descriptors evaluated: 5
- Ready candidates count: 0
- Manual-review candidates count: 0
- Rejected/blocked candidates count: 5
- v2.2 handoff recommendation: `continue_candidate_acquisition`
- Candidate acquisition is not repair success.
- Ready candidates only authorize future v2.2 replay attempts.
- Blocked candidate acquisition is not negative capability evidence.
- External memory lift remains undemonstrated.
- Self-maintaining software remains undemonstrated.
- Full scoring remains disallowed.

The harness ranks public/fork candidates by replay feasibility and uses controlled rejection reasons before any repair attempt. This result means no candidate is ready for v2.2 execution yet; it does not mean ControllerGate failed on external repos.

Future developer-framework note: a reusable ControllerGate integration should separate `controllergate.toml` or YAML configuration, adapter interfaces, a generic shell adapter, a pytest adapter first, later npm/cargo/go test/Flutter-Dart adapters, proof ledger generation, and replay-engine execution.

## v2.1b Curated External Candidate Sourcing Result

v2.1b improves candidate sourcing quality.

- Candidate pool produced: true
- Candidates evaluated: 10
- Ready candidates count: 0
- Manual-review candidates count: 5
- Rejected/blocked candidates count: 5
- Best source families: small public Python repos with simple tests and curated bug benchmark descriptors
- Source gap analysis: curated benchmark datasets/checkouts are unavailable locally; local public Python repos have clone, license, and command feasibility but still lack known deterministic failing issue branches.
- v2.2 handoff recommendation: `manual_candidate_triage_before_v2_2`
- Candidate readiness is not repair success.
- Ready candidates only authorize future v2.2 replay attempts.
- Blocked acquisition is not negative capability evidence.
- External memory lift remains undemonstrated.
- Self-maintaining software remains undemonstrated.
- Full scoring remains disallowed.

The next acquisition step should supply local benchmark datasets or known issue-branch descriptors with exact failing commands. Candidate readiness does not prove repair capability, and no external memory-lift claim is allowed from v2.1b.

## v2.1c/v2.2 External-Fork Controlled Fixture Campaign

External-fork controlled fixtures test portability of replay/memory machinery.

- v2.1c triaged candidates: 5
- Promoted candidates count: 3
- Known external bug candidates: 0
- Controlled fixture candidates: 3
- v2.2 executed: true
- Executed episodes count: 3
- Scoreable episodes count: 3
- Positive memory episodes: 3
- Inconclusive/negative/blocked episodes: 0
- Aggregate result: `limited_external_fork_controlled_fixture_memory_lift_criteria_met`
- Claim boundary: limited external-fork controlled fixture evidence only.

Injected fixture failures are not organic external bugs. Known external bug replay is stronger evidence. Candidate promotion is not repair success. Controlled fixture memory lift, if met, is limited-scope evidence. Organic external memory lift remains undemonstrated unless known external bug criteria are met. Self-maintaining software remains undemonstrated. Full scoring remains disallowed.

## v2.3 Known External Bug Replay Campaign

Known external bug replay is stronger than injected fixture evidence. Benchmark bugs must be labeled as benchmark evidence.

- Promoted candidates count: 3
- Known external bug candidates: 0
- Benchmark bug candidates: 3
- Fallback controlled fixture candidates: 3, not counted
- Executed episodes count: 3
- Scoreable episodes count: 3
- Positive memory episodes: 3
- Inconclusive/negative/blocked episodes: 0
- Aggregate result: `limited_known_external_or_benchmark_memory_lift_criteria_met`
- Claim boundary: limited QuixBugs benchmark replay evidence only.

Fallback controlled fixtures do not count as known external bug evidence. Benchmark success does not prove arbitrary public repo performance. External memory lift remains limited unless aggregate criteria are met in the named evidence class. Broad organic external memory lift remains undemonstrated. Self-maintaining software remains undemonstrated. Full scoring remains disallowed.

## v2.4 SWE-bench/BugsInPy Real External Bug Replay Campaign

SWE-bench-style tasks are real GitHub issue tasks when reproduced safely. BugsInPy-style entries are real Python bug benchmark entries.

- Source families acquired/preflighted: SWE-bench Verified/Lite repository metadata and BugsInPy repository metadata.
- Promoted candidates count: 0.
- Executed episodes count: 0.
- Scoreable episodes count: 0.
- Positive memory episodes: 0.
- Inconclusive/negative episodes: 0.
- Blocked candidates: 4 real-bug source descriptors plus QuixBugs preserved as non-organic benchmark evidence.
- Aggregate result: `blocked_real_external_bug_candidate_acquisition_failure`.
- Claim boundary: real external bug memory lift remains untested in v2.4.

Gold/corrected patches are outcome-only and excluded from decision-time inputs. Benchmark evidence must be labeled as benchmark evidence. QuixBugs remains algorithmic benchmark evidence only and does not prove organic external bug repair.

The current blockers are execution-environment and task-instantiation blockers, not negative capability evidence: SWE-bench requires a concrete bounded task plus Docker-based evaluation resources, and BugsInPy requires a Unix-style framework or Docker plus project-specific Python runtimes. The next required dataset/source action is to provide or enable a bounded SWE-bench Lite/Verified task workspace or a runnable BugsInPy container/shell environment with exact failing commands.

Self-maintaining software remains undemonstrated. Full scoring remains disallowed. Broad organic external memory lift remains undemonstrated.

## v2.4b BugsInPy/SWE-bench Runtime Unblock

The blocker is benchmark runtime acquisition.

- BugsInPy/SWE-bench candidates require local benchmark harness execution.
- BugsInPy concrete candidates probed: `black:2`, `youtube-dl:1`, `black:8`.
- SWE-bench smoke test status: blocked before task instantiation.
- Promoted real-bug candidates: 0.
- Executed real-bug replay episodes: 0.
- Scoreable real-bug replay episodes: 0.
- Aggregate result: `blocked_real_bug_runtime_unavailable`.

Blocked runtime is not negative ControllerGate capability evidence. Candidate metadata alone does not prove replay readiness. Gold/corrected patches are outcome-only and barred from decision-time inputs.

The practical next action is to run the benchmark harness in an environment that supports it: BugsInPy through a Unix shell or Docker with project-specific Python runtimes, or SWE-bench through a bounded Docker-capable Lite/Verified task runner.

Self-maintaining software remains undemonstrated. Full scoring remains disallowed. Broad organic external memory lift remains undemonstrated.

## v2.5 BugsInPy Linux Runtime Runner

The current blocker is benchmark runtime acquisition.

- The workflow creates a Linux runtime path for BugsInPy replay.
- Candidate replay readiness requires fresh checkout/compile/test logs.
- BugsInPy candidates targeted: `black:2`, `youtube-dl:1`, and `black:8`.
- Workflow trigger: manual `workflow_dispatch`.
- Expected artifact: `v2_5_bugsinpy_runtime_probe_artifacts`.
- Current local status: workflow ready, runtime artifact pending.
- Repair scoring: not run.

Blocked runtime is not negative ControllerGate capability evidence. Gold/fixed patches are outcome-only. Candidate metadata alone does not prove replay readiness.

After the GitHub Actions artifact is produced, parse it with `scripts/v2_5_parse_bugsinpy_runtime_artifacts.py`. If three candidates promote, the next gated step is `v2_5_bugsinpy_real_bug_limited_replay_execution`; if one or two promote, run a small probe; if none promote, fix the runner environment.

Self-maintaining software remains undemonstrated. Full scoring remains disallowed. Broad organic external memory lift remains undemonstrated.

## v2.5 BugsInPy Runtime Artifact Ingestion Result

The v2.5 GitHub Actions BugsInPy runtime probe artifact was ingested.

- Candidate count: 3.
- Promoted real-bug candidates: 1.
- Handoff recommendation: `v2_5_small_bugsinpy_probe_execution`.
- Repair scoring: not run.
- Full scoring: disallowed.
- Self-maintaining software: not demonstrated.
- Broad organic external memory lift: not demonstrated.

Candidate classifications:

- `black:2`: `blocked_bugsinpy_test_not_reproducible`
- `youtube-dl:1`: `promoted_ready_for_v2_5_bugsinpy_real_bug`
- `black:8`: `blocked_bugsinpy_test_not_reproducible`

Fresh checkout/compile/test logs now exist in the ingested GitHub Actions artifact. Gold/fixed patches remain outcome-only and were not used as decision-time inputs. If three candidates promote, the next gated step is real BugsInPy limited replay execution, not a self-maintaining-software claim.

Target-failure matching is enforced at parser/audit time. A dependency/import/runtime failure is not enough to promote a BugsInPy candidate unless the expected BugsInPy target failure is also matched.

## v2.6 BugsInPy Real-Bug Limited Replay Execution

BugsInPy real-bug replay is stronger than QuixBugs and controlled fixture evidence, but target-failure matching is now a hard gate.

- Candidates reviewed: `black:2`, `youtube-dl:1`, `black:8`.
- Target-failure-matched promoted candidates: 1.
- Blocked by target-failure guard: 2.
- Executed episodes: 0.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Decision-time/outcome overlap count: 0.
- Corruption count: 0.
- Aggregate result: `insufficient_episode_count_for_bugsinpy_real_bug_memory_lift`.

The two Black candidates were not accepted as target BugsInPy replay evidence because the ingested logs show dependency/import failures rather than the expected target BugsInPy failure. `youtube-dl:1` remains promoted and can support a future small real-bug probe.

Gold/fixed patches are outcome-only and excluded from decision-time inputs. Limited BugsInPy memory lift is still not self-maintaining software. Full scoring remains disallowed. Blocked runtime or target-failure mismatch is not negative capability evidence.

## v2.7/v2.8 BugsInPy Target-Replay Recovery and Limited Replay Campaign

Dependency repair is runtime setup, not code repair. Target-failure matching remains mandatory. Dependency/import failures do not count as target bug replay.

- Previous target-matched count: 1 (`youtube-dl:1`).
- `black:2` recovery status: blocked pending v2.7 Linux GitHub Actions dependency rerun for `regex`.
- `black:8` recovery status: blocked pending v2.7 Linux GitHub Actions dependency rerun for `click`.
- Additional candidates attempted locally: 0; local Windows runtime cannot perform BugsInPy expansion.
- Final target-matched count: 1.
- v2.8 executed: false.
- Aggregate/gate result: `insufficient_target_matched_bugsinpy_candidates_for_v2_8`.

Candidate promotion is not repair success. Limited BugsInPy memory lift is not demonstrated. Full scoring remains disallowed. Self-maintaining software remains undemonstrated.

Next required runtime action: run the `v2_7_bugsinpy_target_replay_recovery` GitHub Actions workflow, download `v2_7_bugsinpy_target_replay_recovery_artifacts`, and ingest it before any v2.8 repair scoring.

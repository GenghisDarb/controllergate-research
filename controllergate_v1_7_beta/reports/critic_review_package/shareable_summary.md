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

## v2.7 BugsInPy Recovery Artifact Ingestion

The v2.7 GitHub Actions recovery artifact was ingested.

- Previous target-matched count: 1 (`youtube-dl:1`).
- Phase A Black rerun results:
- `black:2`: `blocked_runtime_environment_failure`; target matched: `false`; reason: dependency/import/runtime failure marker was present
- `black:8`: `blocked_runtime_environment_failure`; target matched: `false`; reason: dependency/import/runtime failure marker was present
- Additional BugsInPy candidates attempted by the runner: 8.
- Final target-matched BugsInPy candidate count: 1.
- v2.8 executed: false.
- Repair scoring: NOT RUN.
- Full scoring: disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

Dependency repair is runtime setup, not code repair. Target-failure matching remains mandatory. Dependency/import/runtime failures do not count as target bug replay. Candidate promotion is not repair success.

Next required action: fix the BugsInPy runner command/runtime path so target tests execute without wrapper contamination, or run a broader BugsInPy expansion that yields at least three target-matched candidates.

## v2.7b/v2.8 BugsInPy Direct Target Runner Fix and Conditional Replay

v2.7b fixes the runner by bypassing the broken BugsInPy wrapper path. `black:8` had target-failure signal but required clean direct rerun. Dependency/runtime setup is not code repair.

- `black:8` direct rerun result: pending fresh v2.7b GitHub Actions artifact.
- `black:2` direct rerun result: pending fresh v2.7b GitHub Actions artifact.
- Additional candidates attempted locally: 0.
- Final clean target-matched count: 1.
- v2.8 executed: false.
- Gate result: `insufficient_target_matched_candidates_for_v2_8`.

Target-failure matching remains mandatory. Dependency/import/wrapper failures do not count as target bug replay. Candidate promotion is not repair success. Limited BugsInPy memory lift is not demonstrated. Full scoring remains disallowed. Self-maintaining software remains undemonstrated.

Next required source/runtime action: run the `v2_7b_bugsinpy_direct_target_runner_fix` GitHub Actions workflow and ingest its artifact before any v2.8 repair scoring.

## v2.7c/v2.8 BugsInPy Direct Runner Artifact Ingestion, Third-Candidate Recovery, and Conditional Replay

v2.7c promotes black:8 from clean direct target replay. black:8 had clean direct target failure with wrapper contamination cleared. black:2 remains blocked by runtime/environment failure.

- Artifact ingestion result: PASS; artifact SHA256 verification had 0 hash failures.
- `black:8` promotion result: `promoted_ready_for_v2_8_bugsinpy_real_bug`.
- `black:2` blocked result: `blocked_runtime_environment_failure`.
- Additional candidates attempted through the direct-runner artifact: 8.
- Final clean target-matched count: 2.
- v2.8 executed: false.
- Gate result: `insufficient_target_matched_candidates_for_v2_8`.

Dependency/runtime setup is not code repair. Target-failure matching remains mandatory. Dependency/import/wrapper failures do not count as target bug replay. Candidate promotion is not repair success. Limited BugsInPy memory lift is not demonstrated. Full scoring remains disallowed. Self-maintaining software remains undemonstrated.

Next required source/runtime action: run a focused direct-runner expansion that yields one additional clean target-matched BugsInPy candidate before any v2.8 repair scoring.

## v2.7d/v2.8 BugsInPy Third-Candidate Direct Runner Expansion

v2.7d adds a focused Linux/GitHub Actions direct-runner expansion to acquire the one missing clean target-matched BugsInPy candidate. It does not run repair scoring locally.

- Starting clean target-matched count from v2.7c: 2.
- Runner artifact ingested: false.
- v2.8 executed: false.
- Gate result: `blocked_pending_v2_7d_runner_artifact`.

The runner excludes already promoted or blocked candidates, derives direct commands from BugsInPy metadata, rejects dependency/import/runtime/wrapper failures, and stops after one clean new target-matched candidate. Candidate promotion is not repair success. Full scoring remains disallowed. Memory lift and self-maintaining software remain undemonstrated.

Next required action: run the `v2_7d_bugsinpy_third_candidate_direct_runner_expansion` GitHub Actions workflow and ingest the artifact.

## v2.7e/v2.8 BugsInPy Third-Candidate Ingestion and Limited Replay Execution

v2.7e promotes black:4 from clean direct target replay. The clean BugsInPy target-matched pool reached 3 candidates, and v2.8 limited replay opened only after the target-matched gate passed.

- Artifact ingestion result: PASS; artifact SHA256 verification had 0 hash failures.
- Promoted candidates: `youtube-dl:1`, `black:8`, `black:4`.
- Blocked candidates: `black:1`, `black:3`.
- Final clean target-matched candidate count: 3.
- v2.8 execution status: gate opened; repair comparison blocked pending post-repair BugsInPy validation runtime artifacts.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Blocked episodes: 3.
- Decision-time/outcome overlap count: 0.
- Label-leakage count: 0.
- Apoptosis watchdog count: 0.
- Corruption count: 0.
- Aggregate result: `blocked_bugsinpy_real_bug_replay_runtime_failure`.

Candidate promotion is not repair success. Limited BugsInPy memory lift is not demonstrated. Full scoring remains disallowed. Self-maintaining software remains undemonstrated.

## v2.8b BugsInPy Linux Repair-Comparison Runner

v2.8b runs repair comparison; candidate promotion alone was not repair success. No-memory and memory-enabled paths are compared under identical BugsInPy replay conditions once the Linux workflow artifact is available.

- Candidate pool: `youtube-dl:1`, `black:8`, `black:4`.
- Linux workflow executed: false.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Blocked episodes: 0.
- Decision-time/outcome overlap count: 0.
- Label-leakage count: 0.
- Apoptosis watchdog count: 0.
- Corruption count: 0.
- Aggregate result: `blocked_bugsinpy_real_bug_replay_runtime_failure`.

Limited BugsInPy memory lift is not demonstrated unless the aggregate criteria are met. Full scoring remains disallowed. Self-maintaining software remains undemonstrated. Blocked runtime/log capture is not negative ControllerGate capability evidence.

## v2.8c BugsInPy Repair-Comparison Checkout Fix

v2.8b reached the workflow but blocked before repair because checkout failed. Checkout/runtime failure is blocked evidence, not negative ControllerGate repair evidence.

- v2.8b artifact ingestion result: SHA256 verification clean; 3 episodes executed by the workflow, 0 scoreable repair episodes.
- Root cause diagnosis: relative checkout/workspace path handling caused BugsInPy checkout failures before replay/repair.
- v2.8c checkout fix status: workflow and runner are ready; the runner uses absolute workspace paths and pre-repair replay gates.
- v2.8c repair comparison executed: false in this local checkpoint; GitHub Actions artifact is required.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Aggregate result: `blocked_bugsinpy_real_bug_replay_runtime_failure`.

Apoptosis should not count infrastructure checkout failure as repair flatline. Full scoring remains disallowed. Self-maintaining software remains undemonstrated.

## v2.8d BugsInPy Git-Workspace Repair Comparison

v2.8d fixed the runner infrastructure path. The workflow executed with Git-based repair workspaces instead of fragile file-tree copying.

- Workflow executed: true.
- Executed episodes: 3.
- Pre-repair replay gates: passed for all three promoted BugsInPy candidates.
- Repair workspace strategy: `git_clone_no_local`.
- Scoreable episodes: 0.
- Blocked episodes: 3.
- Apoptosis watchdog triggers: 3.
- Positive memory episodes: 0.
- Decision-time/outcome overlap count: 0.
- Label-leakage count: 0.
- Corruption count: 0.
- Aggregate result: `blocked_apoptosis_watchdog_triggered`.

This is no longer a checkout/runtime acquisition failure. It is blocked because the bounded repair runner produced no source-changing repair actions, and no-op/flatline behavior is correctly quarantined rather than scored. Full scoring remains disallowed. Memory lift and self-maintaining software remain undemonstrated.

## v2.8e BugsInPy Repair Workspace Preservation

v2.8e ingested the Linux workflow artifact and confirmed the workspace-preservation fix worked. The validated BugsInPy workspace is archived and restored into both no-memory and memory-enabled repair workspaces, and both repair workspaces reproduce the target failure before repair.

- Workflow executed: true.
- Executed episodes: 3.
- Workspace equivalence: passed for all three episodes.
- Repair-workspace pre-repair replay: target failure matched for no-memory and memory-enabled paths in all three episodes.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Aggregate result: `blocked_no_repair_candidate_generated`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

This is a narrower implementation blocker, not negative ControllerGate capability evidence: no safe repair candidate was generated from allowed decision-time inputs, so the episodes remain blocked instead of scored.

## v2.8f BugsInPy Bounded Repair Proposer

v2.8f ingested the Linux workflow artifact and confirmed the bounded proposer ran under valid replay/workspace gates. Candidate promotion, checkout/runtime, target replay, exact workspace preservation, no-memory prerepair replay, and memory-enabled prerepair replay were preserved.

- Workflow executed: true.
- Executed episodes: 3.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Aggregate result: `insufficient_episode_count_for_bugsinpy_real_bug_memory_lift`.
- Episode classifications: `blocked_no_safe_patch_candidate_generated`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

v2.8f isolated the next blocker: source-discovery and repair-heuristic coverage. No-patch/no-action outcomes are not scoreable repair evidence.

## v2.8g BugsInPy Source-Discovery Repair Proposer

v2.8g ingested the Linux workflow artifact and preserved the source-discovery repair proposer result. Candidate promotion, checkout/runtime, target replay, exact workspace preservation, no-memory prerepair replay, memory-enabled prerepair replay, bounded proposer execution, and source discovery all ran under the replay gates.

- Workflow executed: true.
- Executed episodes: 3.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Aggregate result: `blocked_no_safe_patch_candidate_generated`.
- Episode classifications: `blocked_no_safe_patch_candidate_generated`.
- `youtube-dl:1` source discovery: `match_str` found in `youtube_dl/utils.py`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

v2.8g found the relevant `match_str` source for youtube-dl:1, but it did not demonstrate repair success or memory lift. It isolated the next blocker: the boolean false-handling heuristic was not implemented. No-patch/no-action outcomes are not scoreable repair evidence.

## v2.8h BugsInPy Targeted Boolean Patch Heuristic

v2.8h ingested the Linux workflow artifact. The workflow executed the three promoted BugsInPy candidates and registered the targeted non-gold boolean false-handling heuristic for `youtube-dl:1`.

- Workflow executed: true.
- Executed episodes: 3.
- Scoreable episodes: 0.
- Positive memory episodes: 0.
- Aggregate result: `blocked_no_safe_patch_candidate_generated`.
- Boolean heuristic registered: true.
- `youtube-dl:1` unary operator block detected: true.
- Patch construction result: blocked because candidate generation failed to locate the same unary block.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

v2.8h registered the boolean heuristic but failed patch construction despite detecting the unary operator block. This is a narrow implementation blocker, not negative ControllerGate repair evidence.


## vHW0 ControllerGate Telemetry Maintenance Validation Plan

vHW0 is a planning-only replay protocol for future telemetry maintenance validation. It does not run physical hardware repair, does not perform actuation, and does not claim hardware self-maintenance.

- Status: planning only.
- Scope: diagnosis, recommendation, and replay evaluation over captured telemetry logs.
- Physical actuation: not allowed.
- Autonomous hardware repair: not allowed.
- Safety-critical deployment: not allowed.
- Self-maintenance claim: not made.
- Required future evidence: replay datasets, no-memory versus memory-enabled comparison, artifact custody, decision-time/outcome separation, and corruption/safety checks.

Full scoring remains disallowed. Self-maintaining software remains undemonstrated unless separately proven.

No hardware self-maintenance claim is made. No physical actuation is performed.

## v2.8i BugsInPy Boolean Patch Construction Fix

v2.8h registered the boolean heuristic but failed patch construction despite detecting the unary operator block. v2.8i fixes the boolean patch construction path. The Linux workflow artifact was ingested and verified cleanly.

- v2.8h artifact ingestion: preserved.
- v2.8i workflow executed: true.
- Executed episodes: 3.
- Scoreable episodes: 1.
- Positive memory episodes: 0.
- `youtube-dl:1` patch construction: generated non-gold full-source boolean patch in both no-memory and memory-enabled paths.
- `youtube-dl:1` classification: `inconclusive_equal_performance`.
- Black episodes: remain `blocked_no_safe_patch_candidate_generated`.
- Aggregate result: `insufficient_episode_count_for_bugsinpy_real_bug_memory_lift`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

A no-memory and memory-enabled tie is inconclusive, not memory lift. This is the first scoreable BugsInPy repair episode in this ladder, but the aggregate remains below the three-episode threshold.

## v2.8j BugsInPy Scoreable Episode Expansion

v2.8j Linux runner artifact was ingested and verified from GitHub Actions run `27428293349`. The artifact SHA256 is `363a3a4bfc3ddac3f95bb0f09ac4fe7b632acf84d6747a25f91f5c8414e30ed1` and the internal SHA256 manifest verified with 0 missing entries and 0 hash failures.

- Workflow executed: true.
- Executed episodes: 3.
- Scoreable episodes: 2.
- Positive memory episodes: 0.
- Inconclusive equal-performance episodes: 2.
- Blocked episodes: 1.
- Aggregate result: `insufficient_episode_count_for_bugsinpy_real_bug_memory_lift`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

Official v2.8j Linux result: two scoreable BugsInPy episodes were captured, both inconclusive equal-performance, with zero positive memory-only episodes. The aggregate remains below the three-scoreable-episode threshold. Candidate promotion and artifact capture are not repair success, and missing or blocked post-repair evidence is not counted as a pass.

## v2.8k BugsInPy Third Scoreable Episode Recovery

v2.8k is a bounded Linux runner continuation after the official v2.8j result reached two scoreable BugsInPy episodes but remained below the aggregate threshold. The runner targets the missing third scoreable episode by refining the `black:8` source-only comma relocation patch construction path.

- v2.8j official executed episodes: 3.
- v2.8j official scoreable episodes: 2.
- v2.8j official positive memory episodes: 0.
- v2.8k local workflow status: pending GitHub Actions artifact.
- Targeted recovery candidate: `black:8`.
- Candidate set remains: `youtube-dl:1`, `black:8`, `black:4`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

v2.8k does not treat candidate promotion, patch construction, or missing logs as repair success. Scoreable evidence still requires Linux post-repair target validation logs under the same anti-leakage rules.

## v2.8l BugsInPy Third Scoreable Episode Recovery

v2.8l follows the official v2.8k Linux result, where `black:8` remained blocked because the source-only candidate exceeded the repair budget. v2.8l keeps `black:8` as the target and replaces the oversized generator with a compact source-only comment/comma relocation guard.

- v2.8k official scoreable episodes: 2.
- v2.8k official positive memory episodes: 0.
- v2.8k black:8 result: `blocked_no_safe_patch_candidate_generated`.
- v2.8l local workflow status: pending GitHub Actions artifact.
- Candidate set remains: `youtube-dl:1`, `black:8`, `black:4`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

v2.8l does not count candidate construction as repair success. Scoreable evidence still requires post-repair target validation logs under the same anti-leakage rules.

## v2.8m BugsInPy Replacement Third Scoreable Episode

v2.8m preserves the official v2.8l Linux result and moves to an outcome-blind replacement candidate instead of repeatedly tuning `black:8`.

- v2.8l official result: 3 executed, 2 scoreable, 0 positive memory episodes.
- `black:8`: frozen as `failed_both`.
- Preserved scoreable episodes: `youtube-dl:1`, `black:4`.
- v2.8m replacement candidate: `black:6`.
- v2.8m local status: `blocked_pending_v2_8m_replacement_artifact`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

Candidate promotion or candidate selection is not repair success. v2.8m requires a fresh Linux artifact before any scoreable-count or memory-lift update.

## v2.8n BugsInPy Replacement Preflight Third Scoreable

v2.8n ingests the official v2.8m Linux artifact, normalizes `blocked_runtime_replay_failure` to `blocked_replay_or_materialization_failure`, and adds a preflight gate before any replacement candidate can enter repair generation.

- v2.8m official result: 4 executed, 2 scoreable, 0 positive memory episodes.
- Preserved scoreable references: `youtube-dl:1`, `black:4`.
- `black:8`: frozen as `failed_both`.
- `black:6`: diagnosed as materialization/preflight blocked in v2.8m; v2.8n retries only after target-file-list preflight.
- v2.8n local status: `blocked_pending_v2_8n_replacement_preflight_artifact`.
- Full scoring: NOT_RUN / disallowed.
- Memory lift: not demonstrated.
- Self-maintaining software: not demonstrated.

Candidate preflight is not repair success. A replacement episode becomes scoreable only with source-only repair generation, patch application, post-repair target validation logs, and clean anti-leakage checks.

## v2.8o BugsInPy Broad Preflight Harvest

- Status: `blocked_pending_v2_8o_broad_preflight_harvest_artifact`.
- v2.8n artifact ingested and verified: `31ef78b0f9ea422ac56338dd4369966874b89d9f5fe85d7ad63ea922d9280ca6`.
- v2.8n official result remains: 5 executed, 2 scoreable, 0 positive memory episodes.
- v2.8o broadens candidate discovery beyond Black formatter bugs before repair attempts.
- Candidate promotion, source discovery, and patch construction are not repair success.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift is not demonstrated.
- Self-maintaining software is not demonstrated.

## v2.8p BugsInPy Harness Repair Broad Harvest

- Status: official GitHub Actions artifact ingested and audited.
- Workflow run: `27469062985`.
- Artifact SHA256: `6f227ab2c12c15c173420663055ec55d3c01f2fc3d666c7a74d1fcfd25b59a06`.
- Internal SHA256SUMS verification: 1009 checked, 0 missing, 0 hash failures.
- v2.8o artifact verified: `4ae274921bb0ea3a25a3443daaa77056c028d12be0b7910065a39623baea0a9e`.
- v2.8o official regression: 0 scoreable episodes, 0 preflight-passing broad candidates.
- Preserved-reference gate: PASS.
- Restored scoreable references: `youtube-dl:1`, `black:4`.
- Harness sanity: PASS.
- Broad candidates preflighted: 28; preflight-passing candidates: 19.
- Returncode 127 failures after normalization: 0.
- Repair-attempted replacements: 3; third scoreable replacement: not found.
- Executed episodes: 5; scoreable episodes: 2; positive memory episodes: 0.
- Aggregate result: `insufficient_episode_count_for_bugsinpy_real_bug_memory_lift`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift is not demonstrated.
- Self-maintaining software is not demonstrated.

## v2.8q BugsInPy Preflight-Guided Third Scoreable Recovery

- Status: `blocked_pending_v2_8q_preflight_guided_third_scoreable_artifact`.
- v2.8p official evidence is preserved: restored `youtube-dl:1` and `black:4`, 19 preflight-passing replacement candidates, 0 returncode-127 normalization failures.
- v2.8q starts with the preserved-reference gate and stops as `runner_regression_preserved_reference_failure` if either reference regresses.
- Candidate triage ranks all v2.8p preflight-passing candidates using decision-time-safe failure/source evidence.
- Initial bounded repair targets: `fastapi:1`, `ansible:2`, `ansible:5`, `ansible:8`, `ansible:4`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift is not demonstrated.
- Self-maintaining software is not demonstrated.

## v2.8r Closure-Guided Third Scoreable Recovery

- Status: `verified_official_artifact`.
- Workflow run: `27730642452`.
- Artifact SHA256: `437b398edf63824cd87c6b193d0e300d53373ec56a02454fbc1b5afba0b4beeb`.
- Internal SHA256SUMS: `1691` checked across `32` manifests, `0` missing, `0` failures.
- Preserved reference gate: `PASS`; `youtube-dl:1` and `black:4` remained scoreable.
- Third scoreable replacement: `fastapi:1`.
- Executed episodes: `3`; scoreable episodes: `3`; replacement scoreable episodes: `1`; positive memory episodes: `0`.
- Aggregate result: `insufficient_positive_memory_evidence`.
- Full scoring remains `NOT_RUN` / disallowed.
- Main benchmark memory lift is not demonstrated by auxiliary closure metrics.
- Self-maintaining software is not demonstrated.

## v2.8s Positive Memory Evidence Lane

- Status: `verified_official_artifact`.
- Workflow run: `27733040511`.
- Artifact SHA256: `801f606ad990c7ca9ddfb8ea4dc90da7582f4e59675ddf02d81f4a68fa12ab3e`.
- Internal SHA256SUMS: `1864` checked across `33` manifests, `0` missing, `0` failures.
- Preserved v2.8r baseline gate: `PASS`; `youtube-dl:1`, `black:4`, and `fastapi:1` remained scoreable.
- Positive memory-only episode: `ansible:2`.
- Executed episodes: `4`; scoreable episodes: `4`; replacement scoreable episodes: `2`; positive memory episodes: `1`.
- Aggregate result: `insufficient_positive_memory_evidence`.
- Repair-outcome memory lift: `demonstrated` for the limited v2.8s lane; main benchmark memory lift remains `not_demonstrated`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.

## v2.8t Positive Memory Replication Lane

- Status: `verified_official_artifact`.
- Workflow run: `27769677857`.
- Artifact SHA256: `0b45a434ececf5f9a6f89c84c59d97cc057e63b7a2be678d3ed98a7e3d297e9f`.
- Internal SHA256SUMS: `2033` checked across `34` manifests, `0` missing, `0` failures.
- Preserved v2.8s baseline gate: `PASS`; `youtube-dl:1`, `black:4`, `fastapi:1`, and `ansible:2` remained scoreable.
- `ansible:2` preserved `positive_memory_only` status.
- New positive memory-only replication episode: `ansible:5`.
- Executed episodes: `5`; scoreable episodes: `5`; replacement scoreable episodes: `3`; positive memory episodes: `2`.
- Aggregate result: `replicated_positive_memory_signal`.
- Repair-outcome memory lift: `replicated_positive_signal`; selection, stability, and global closure memory lift remain `suggestive`.
- Main benchmark memory lift remains `not_demonstrated`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.

## v2.8u Positive Memory Signal Strengthening

- Status: `verified_official_artifact`.
- Workflow run: `27783319420`.
- Artifact SHA256: `8b058af2b137b138a83f1a8f6f7f72a6d1f20a10fb7b20ad0e017e1e213f966d`.
- Internal SHA256SUMS: `2538` checked across `37` manifests, `0` missing, `0` failures.
- Preserved v2.8t baseline gate: `PASS`; `youtube-dl:1`, `black:4`, `fastapi:1`, `ansible:2`, and `ansible:5` remained scoreable.
- `ansible:2` and `ansible:5` preserved `positive_memory_only` status.
- Memory-generalization attempts: `ansible:4`, `ansible:12`, and `ansible:13`; all three blocked with `blocked_no_safe_patch_candidate_generated`.
- Executed episodes: `8`; scoreable episodes: `5`; replacement scoreable episodes: `3`; positive memory episodes: `2`.
- Aggregate result: `replicated_positive_memory_signal_preserved`; no new v2.8u positive-memory-only episode appeared.
- Repair-outcome memory lift: `replicated_positive_memory_signal_preserved`; selection, stability, and global closure memory lift remain `suggestive`.
- Family generalization remains unexpanded: positive-memory evidence is still `ansible:2` and `ansible:5`, with no cross-project positive-memory signal.
- Main benchmark memory lift remains `not_demonstrated`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.

## v2.8v Cross-Family Positive Memory Generalization

- Status: `verified_official_artifact`.
- Workflow run: `27787816699`.
- Artifact SHA256: `9758be874f2d3623b2ad900aed7498b6ec6f885d213bed0d50609958220aeded`.
- Internal SHA256SUMS: `2671` checked across `38` manifests, `0` missing, `0` failures.
- Preserved v2.8u baseline gate: `PASS`; `youtube-dl:1`, `black:4`, `fastapi:1`, `ansible:2`, and `ansible:5` remained scoreable.
- `ansible:2` and `ansible:5` preserved `positive_memory_only` status.
- Cross-family attempts covered `fastapi` and `ansible`: `fastapi:1`, `fastapi:2`, `ansible:2`, and `ansible:5`.
- Executed episodes: `9`; scoreable episodes: `5`; replacement scoreable episodes: `3`; positive memory episodes: `2`.
- Aggregate result: `replicated_positive_memory_signal_preserved`; no new v2.8v positive-memory-only episode appeared.
- Repair-outcome memory lift: `replicated_positive_memory_signal_preserved`; selection, stability, and global closure memory lift remain `suggestive`.
- Family generalization remains `not_expanded`: positive-memory evidence is still `ansible:2` and `ansible:5`, with no cross-project positive-memory signal.
- Main benchmark memory lift remains `not_demonstrated`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.

## v2.8w Non-Ansible Materialization Repairability

- Status: `verified_official_artifact`.
- Workflow run: `27801291756`.
- Artifact SHA256: `314da1b9032a3a4cc4c9f6958cf1d46bda5b735c45574dece661958312652cd5`.
- Internal SHA256SUMS: `2676` checked across `38` manifests, `0` missing, `0` failures.
- Tar snapshots excluded from git ingest: `5`; retained in the verified artifact zip.
- Preserved v2.8v baseline gate: `PASS`; `youtube-dl:1`, `black:4`, `fastapi:1`, `ansible:2`, and `ansible:5` remained scoreable.
- `ansible:2` and `ansible:5` preserved `positive_memory_only` status.
- Non-Ansible repairability attempts covered `fastapi` and `PySnooper`: `fastapi:2`, `fastapi:3`, `fastapi:4`, and `PySnooper:1`.
- Executed episodes: `9`; scoreable episodes: `5`; replacement scoreable episodes: `3`; positive memory episodes: `2`.
- Aggregate result: `replicated_positive_memory_signal_preserved`; no new v2.8w positive-memory-only episode appeared.
- Repair-outcome memory lift: `replicated_positive_memory_signal_preserved`; selection, stability, and global closure memory lift remain `suggestive`.
- Family generalization remains `not_expanded`: positive-memory evidence is still `ansible:2` and `ansible:5`, with no non-Ansible positive-memory signal.
- Materialization readiness classified the attempted non-Ansible set as `source_discovery_blocked`; repair-path taxonomy assigned bounded `validation_guard` and `localized_exception_edge_case` paths before heuristic selection.
- Environmental stress-state and senescence audits are present; repeatedly blocked Ansible lanes were moved to watchlist or temporary retirement with reopen conditions.
- Interlocked isomorphism readiness, checkpoint-cycle discipline, duplicate clean replay readiness, and repair-template transfer readiness are recorded for the v2.9 bridge.
- Main benchmark memory lift remains `not_demonstrated`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.

## v2.9 Topological Source Discovery

- Status: `verified_official_artifact`.
- Workflow run: `27809240230`.
- Artifact SHA256: `bf3e57d0fe9e07a347e884fe4e47ac8c6abfd03fc427618ebb802f6e257309c0`.
- Internal SHA256SUMS: `2846` checked across `38` manifests, `0` missing, `0` failures.
- Tar snapshots excluded from git ingest: `5`; retained in the verified artifact zip.
- Preserved v2.8w baseline gate: `PASS`; `youtube-dl:1`, `black:4`, `fastapi:1`, `ansible:2`, and `ansible:5` remained scoreable.
- `ansible:2` and `ansible:5` preserved `positive_memory_only` status.
- Topology-aware candidates selected: `fastapi:2`, `fastapi:3`, `fastapi:4`, `PySnooper:1`, `PySnooper:2`, and `fastapi:5`; attempted episodes covered `fastapi:2`, `fastapi:3`, `fastapi:4`, and `PySnooper:1`.
- Topological context bundles built: `6`; source discovery upgraded from blocked to contextualized for `6` non-Ansible candidates.
- Repair-path taxonomy changed after loop extrusion for `4` candidates; topology-aware paths were `dependency_environment_defect` and `localized_exception_edge_case`.
- Executed episodes: `9`; scoreable episodes: `5`; replacement scoreable episodes: `3`; positive memory episodes: `2`.
- Aggregate result: `replicated_positive_memory_signal_preserved`; no new v2.9 positive-memory-only episode appeared.
- Repair-outcome memory lift: `replicated_positive_memory_signal_preserved`; selection, stability, and global closure memory lift remain `suggestive`.
- Family generalization remains `not_expanded`: positive-memory evidence is still `ansible:2` and `ansible:5`, with no non-Ansible positive-memory signal.
- Heterochromatin risk, materialization tension relief, duplicate clean replay verification, phase-inversion seed-constraint checks, and all four isomorphism layers are recorded for the next lane.
- Main benchmark memory lift remains `not_demonstrated`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.

## v2.10 Materialization Recovery and Topological Repair

- Status: `verified_official_artifact`.
- Workflow run: `27827139235`.
- Artifact ID: `7751053097`.
- Artifact SHA256: `6daecbff8af6e17c2c5709b5e43340dfa4b97e394b8e65afeb776d2f2733bbea`.
- Internal SHA256SUMS: `2973` checked across `38` manifests, `0` missing, `0` failures, `0` malformed.
- Tar snapshots excluded from git ingest: `5`; retained in the verified artifact zip.
- Preserved v2.9 baseline gate: `PASS`; `youtube-dl:1`, `black:4`, `fastapi:1`, `ansible:2`, and `ansible:5` remained scoreable.
- `ansible:2` and `ansible:5` preserved `positive_memory_only` status.
- Selected topology/materialization candidates: `fastapi:2`, `fastapi:3`, `fastapi:4`, `PySnooper:1`, `PySnooper:2`, and `fastapi:5`; attempted episodes covered `fastapi:2`, `fastapi:3`, `fastapi:4`, and `PySnooper:1`.
- Candidate families attempted: `fastapi` and `PySnooper`.
- Bounded dependency/materialization recovery diagnosed `6` non-Ansible candidates and recovered `4` lanes to a repair-allowed surface: `fastapi:2`, `fastapi:3`, `fastapi:4`, and `PySnooper:1`.
- Dependency cofactor recovery used declared buggy-checkout evidence only: the FastAPI lanes installed the declared `requests` TestClient cofactor from `pyproject.toml`; no arbitrary undeclared dependency install was recorded.
- Fixture materialization found no fixed-revision fixture copying and no test modification.
- v2.9 causal context bundles were reused as decision-time-safe summaries; post-materialization source discovery validated or updated the repair plan.
- Repair-path taxonomy changed after materialization for the recovered lanes, including FastAPI `validation_guard` paths and a PySnooper `import_compatibility_defect` path.
- Duplicate clean replay and phase-inversion checks remain supported and passed as `not_applicable` for new evidence because no new v2.10 scoreable source patch was locked.
- Heterochromatin and silent-scaffolding risk audits passed; all four interlocked isomorphism layers are present with dependency/cofactor materialization added.
- Executed episodes: `9`; scoreable episodes: `5`; replacement scoreable episodes: `3`; positive memory episodes: `2`.
- Aggregate result: `replicated_positive_memory_signal_preserved`; no new v2.10 positive-memory-only episode appeared.
- Repair-outcome memory lift: `replicated_positive_memory_signal_preserved`; selection, stability, and global closure memory lift remain `suggestive`.
- Family generalization remains `not_expanded`: positive-memory evidence is still `ansible:2` and `ansible:5`, with no non-Ansible positive-memory signal.
- Main benchmark memory lift remains `not_demonstrated`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.

## v2.11 Topology-Aware Source Repair

- Status: `verified_official_artifact`.
- Workflow run: `27833009856`.
- Artifact ID: `7753460223`.
- Artifact SHA256: `c9f191348b356074111016c2ddeb0578d4a06660532d1154a1ad9cd695563e35`.
- Internal SHA256SUMS: `3053` checked across `38` manifests, `0` missing, `0` failures, `0` malformed.
- Tar snapshots excluded from git ingest: `5`; retained in the verified artifact zip.
- Preserved v2.10 baseline gate: `PASS`; `youtube-dl:1`, `black:4`, `fastapi:1`, `ansible:2`, and `ansible:5` remained scoreable.
- `ansible:2` and `ansible:5` preserved `positive_memory_only` status.
- The topology-aware proposer evaluated no-memory and memory-enabled paths for the six selected candidates and attempted the four v2.10-recovered surfaces: `fastapi:2`, `fastapi:3`, `fastapi:4`, and `PySnooper:1`.
- The three FastAPI validation-guard lanes recovered topology context but produced no bounded safe source patch.
- The memory-enabled `PySnooper:1` lane generated one localized, source-only import-compatibility patch for `pysnooper/variables.py`; no tests were modified and the anti-leakage checks passed.
- The `PySnooper:1` target test still failed, so the patch remained unscoreable with classification `blocked_target_test_failed`; its proof chain correctly remained incomplete and duplicate replay/phase inversion were not applicable.
- Source-patch integrity, decision-time separation, memory-evidence eligibility, observer-state separation, heterochromatin, silent-scaffolding, and all four isomorphism-layer checks passed.
- Executed episodes: `9`; scoreable episodes: `5`; replacement scoreable episodes: `3`; positive memory episodes: `2`.
- Aggregate result: `replicated_positive_memory_signal_preserved`; no new v2.11 positive-memory-only episode appeared.
- Repair-outcome memory lift: `replicated_positive_memory_signal_preserved`; selection, stability, and global closure memory lift remain `suggestive`.
- Family generalization remains `not_expanded`: positive-memory evidence is still `ansible:2` and `ansible:5`, with no non-Ansible positive-memory signal.
- Main benchmark memory lift remains `not_demonstrated`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.
- Tooling note preserved from campaign metadata: the v2.10 artifact handling issue was a session/tooling surface problem, not ControllerGate evidence.

## v2.12 Dependency Cofactor Recovery and Locked Non-Ansible Repair Validation Lane

- Status: `verified_official_artifact`.
- Workflow run: `27847714846`; artifact ID: `7758557460`.
- Artifact SHA256: `153bb7a7626268c82aab9ddd06f09a6f300688c5585209ca274f471c09ac5454`.
- Internal SHA256SUMS: `3313` checked across `39` manifests, `0` missing, `0` malformed, `0` failures; root coverage complete.
- Tar snapshots excluded from Git ingest: `5`; retained in the verified ZIP.
- Preserved v2.11 baseline gate: `PASS`; `youtube-dl:1`, `black:4`, `fastapi:1`, `ansible:2`, and `ansible:5` remained scoreable.
- `ansible:2` and `ansible:5` preserved `positive_memory_only` status.
- Executed episodes: `10`; scoreable episodes: `5`; positive-memory-only episodes: `2`; non-Ansible positive-memory episodes: `0`.
- PySnooper:1 classification: `dependency_recovery_forbidden_by_policy`. The verified artifact also marks `python_toolbox` declared and recovery-eligible but not recovered, with an empty forbidden reason; that internal policy inconsistency is preserved rather than normalized away.
- PySnooper:2 recovered the declared `python_toolbox` cofactor and generated one source-only patch (`638b7f792087452d1dcd869a7ab29578e1818edcdc94b627d4484d8914b38c0e`), but exact target validation failed on missing `tests.mini_toolbox`; classification: `blocked_target_test_failed`.
- Aggregate result: `replicated_positive_memory_signal_preserved`; family generalization remains `not_expanded`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.

## v2.13 Minimal Forensic Context Lane

- Status: `verified_official_artifact`.
- Workflow run: `28130741168`; artifact name: `v2_13_minimal_forensic_context_lane_artifacts`.
- Artifact SHA256: `57f87a8e0726f55acf0a01282acf7a649808fc71007cba732b9491cf66567ee1`; byte size: `40422`.
- Internal SHA256SUMS verification: `51` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest: `52` entries after adding the local artifact-verification record.
- v2.13 audit: `PASS`.
- Baseline preservation: `PASS`; exactly `youtube-dl:1`, `black:4`, `fastapi:1`, `ansible:2`, and `ansible:5` were rerun through the v2.12 scoring harness.
- `ansible:2` and `ansible:5` preserved `positive_memory_only` status.
- PySnooper:1 policy result: `dependency_recovery_allowed_by_policy_not_executed_in_minimal_lane`; no dependency installation was performed in the minimal lane.
- PySnooper:2 deterministic failed-patch classification: `fixture_materialization_incomplete`.
- PySnooper:2 final blocker: `blocked_fixture_materialization_incomplete`; the target test imports missing `tests/mini_toolbox.py`, while test and fixture edits remain forbidden.
- Diagnostic probes used: `0`.
- Revised PySnooper:2 patch authorized: `false`; attempted: `false`.
- PySnooper:2 remains non-scoreable and not `positive_memory_only`.
- Scoreable episodes: `5`; positive-memory-only episodes: `2`; non-Ansible positive-memory episodes: `0`.
- Aggregate result remains `replicated_positive_memory_signal_preserved`; family generalization remains `not_expanded`.
- Full scoring remains `NOT_RUN` / disallowed.
- Self-maintaining software is not demonstrated.

## v2.15 Chromosomal Maintenance Gate-Order

- Status: `verified_official_artifact`.
- Workflow run: `28149638465`; artifact ID: `7869776529`; artifact name: `v2_15_chromosomal_maintenance_gate_order_artifacts`.
- Artifact verification: `PASS`; ZIP SHA256: `6efe1eb24b006436ee410dce76c7bc60f5d8e283eb69bca1fadf388cdfa209c9`; byte size: `38753`; ZIP entries: `29`; safe paths: `PASS`; duplicate paths: `0`.
- Internal SHA256SUMS: `27` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest: `28` entries after adding the local official artifact-verification record.
- v2.15 audit: `PASS`; v2.14 audit: `PASS`; v2.13 audit: `PASS`; v2.12 audit: `PASS`; current-protocol audit: `PASS`.
- Byte-custody correction status: `PASS`; committed LF bytes now match v2.15 manifest/proof-ledger evidence, with LF-safe writers for the workflow-audited v2.13/v2.14/v2.15 paths.
- Corrected chromosomal maintenance order implemented: `true`; every gate exposes machine-checkable `pass`/`block`/`manual_review` fields.
- Patch attempted: `false`; activation/license and materialization gates denied patch generation before source mutation.
- PySnooper:1 blocker: `activation_denied_after_dependency_or_cofactor_mismatch`.
- PySnooper:2 blocker: `activation_denied_after_fixture_materialization_incomplete`.
- Baseline preservation: `PASS`; previous positive-memory episodes preserved: `true`.
- Scoreable episodes: `5`; positive-memory-only episodes: `2`; non-Ansible positive-memory episodes: `0`.
- Family generalization remains `not_expanded`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.15 is not promoted to current.

## v2.16 PySnooper:1 Isolated Recovery Executor

- Status: `verified_official_artifact`.
- Campaign: `v2_16_pysnooper1_isolated_recovery_executor`.
- Artifact verification: `PASS`; ZIP SHA256: `92cc10c777e0fc56e665a963283bf94daca17a008252210ad6a05242b4f15070`; byte size: `30293`; ZIP entries: `13`; safe paths: `PASS`; duplicate paths: `0`.
- Internal SHA256SUMS: `10` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest: `11` entries after adding the local official artifact-verification record.
- v2.16 audit: `PASS`.
- Candidate scope: `PySnooper:1` only; PySnooper:2 remains blocked unless decision-time-safe provenance for `tests/mini_toolbox.py` can be proven.
- Decision-time-safe recovery evidence is limited to buggy-checkout dependency declarations and initial failing-test context; the recorded declaration is `python-toolbox` from the buggy PySnooper metadata.
- Executor contract: create an isolated `venv`, install only declared dependencies, normalize `PYTHONPATH` to the checked-out project root, and run the target test strictly inside the sandbox.
- Forbidden operations are explicit: no fixed revision, no BugsInPy gold patch, no future outcome evidence, no hidden labels, no test/benchmark/harness mutation, no undeclared dependency install, and no vendored global helpers.
- Local execution status: executor contract recorded, but the live BugsInPy PySnooper runtime workspace is not committed in the repository, so pre-repair replay could not be reproduced locally.
- Patch generated: `false`; no `.diff` payload is counted because patch preconditions did not pass.
- PySnooper:1 classification: `blocked_no_safe_patch_candidate_generated`.
- Scoreable episodes remain `5`; positive-memory-only episodes remain `2`; non-Ansible positive-memory episodes remain `0`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`; the aggregate positive-memory criteria across at least three BugsInPy real-bug episodes are not met.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.16 is not promoted to current.

## v2.17 PySnooper:1 Runtime Workspace Materialization

- Status: `verified_official_artifact`.
- Campaign: `v2_17_pysnooper1_runtime_workspace_materialization`.
- Artifact verification: `PASS`; ZIP SHA256: `a2606d558d9baf62e301cd74c4e5ef39f577e513f23c7464d3213819cdbd09ce`; byte size: `32097`; ZIP entries: `14`; safe paths: `PASS`; duplicate paths: `0`.
- Internal SHA256SUMS: `11` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest: `12` entries after adding the local official artifact-verification record.
- Candidate scope: `PySnooper:1` only; PySnooper:2 was not pursued.
- Workspace materialization classification: `blocked_no_decision_time_safe_workspace_source`.
- Workspace provenance status: `BLOCK`; no outside-repo PySnooper:1 buggy checkout or available BugsInPy checkout executable/source bundle could be tied to the v2.13/v2.16 decision-time-safe metadata.
- Dependency recovery execution status: `not_executed_workspace_blocked`.
- Pre-repair replay status: `not_run_workspace_blocked`.
- Patch generated: `false`; authorized: `false`; attempted: `false`.
- Target validation and duplicate replay are not applicable because no patch was authorized.
- PySnooper:1 scoreable: `false`; positive-memory-only: `false`.
- Scoreable episodes remain `5`; positive-memory-only episodes remain `2`; non-Ansible positive-memory episodes remain `0`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.17 is not promoted to current.

## v2.18 PySnooper:1 Origin Licensing / Source Acquisition

- Status: `verified_official_artifact`.
- Campaign: `v2_18_origin_licensing_source_acquisition`.
- Artifact verification: `PASS`; ZIP SHA256: `4c91b8e69dd75e1ed49432611f834b73ec700054d6395c99b42c729e9f84eac5`; byte size: `36500`; ZIP entries: `18`; safe paths: `PASS`; duplicate paths: `0`.
- Internal SHA256SUMS: `15` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `16` entries after adding the local official artifact-verification record.
- Candidate scope: `PySnooper:1` only; PySnooper:2 was not pursued.
- v2.17 source-acquisition blocker corrected: `true`; the lane now identifies and checks out the decision-time-safe public PySnooper buggy revision from committed BugsInPy metadata.
- Source acquisition status: `source_checkout_acquired`.
- Source commit acquired: `e21a31162f4c54be693d8ca8260e42393b39abd3`.
- Workspace purity status: `PASS`; the outside-repo runtime checkout was cleaned before evidence capture and removed after the run.
- Workspace equivalence status: `BLOCK`; the raw public checkout does not include the BugsInPy materialized target test `tests/test_chinese.py`.
- Environment lock status: `PASS`; command manifest status: `PASS`.
- Dependency recovery status: `not_executed_workspace_equivalence_blocked`.
- Pre-repair replay status: `not_run_workspace_equivalence_blocked`.
- Patch generated: `false`; authorized: `false`; attempted: `false`.
- Target validation and duplicate replay are not applicable because no patch was authorized.
- PySnooper:1 classification: `blocked_workspace_equivalence_missing_materialized_target_test`.
- PySnooper:1 scoreable: `false`; positive-memory-only: `false`.
- Scoreable episodes remain `5`; positive-memory-only episodes remain `2`; non-Ansible positive-memory episodes remain `0`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.18 is not promoted to current.

## Non-Ansible Capability Roadmap

- Roadmap document: `docs/non_ansible_capability_roadmap.md`.
- Machine-readable backlog: `configs/non_ansible_capability_backlog.json`.
- These files are planning/control artifacts, not proof that any capability has been demonstrated.
- They record the required future gates for materialized target-test provenance, environment locks, BugsInPy command translation, fresh workspaces, baseline preservation, rollback markers, repair-state capture, bounded diagnostic feedback, structural test signatures, patch locality, real-time patch safety, patch application semantics, workspace protection, post-validation analysis, PySnooper:2 policy, claim boundaries, and future version sequencing.

## v2.19 BugsInPy Materialized-Test Provenance

- Status: `verified_official_artifact`.
- Campaign: `v2_19_bugsinpy_materialized_test_provenance`.
- Artifact verification: `PASS`; ZIP SHA256: `bd7ee23458a60051abe2137266b91d06c72b06449941f2720ddc09b0b6ead695`; byte size: `51116`; ZIP entries: `29`; safe paths: `PASS`; duplicate paths: `0`.
- Workflow run: `28187693617`; artifact ID: `7885570481`; artifact name: `v2_19_bugsinpy_materialized_test_provenance_artifacts`.
- Internal SHA256SUMS: `24` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `25` entries after adding the local official artifact-verification record.
- v2.19 audit: `PASS`; v2.18 through v2.12 regression audits: `PASS`; current-protocol audit: `PASS`.
- Candidate scope: `PySnooper:1` only; PySnooper:2 was not pursued.
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
- Target validation and duplicate replay are not applicable because no patch was authorized.
- PySnooper:1 classification: `blocked_materialized_target_test_provenance_missing`.
- Exact blocker: decision-time-safe BugsInPy target-test content for `tests/test_chinese.py` was not found. Prior logs identify the target path and show fixed-revision test-copy behavior, but no allowed public benchmark source supplied the file content.
- PySnooper:1 scoreable: `false`; positive-memory-only: `false`.
- Scoreable episodes remain `5`; positive-memory-only episodes remain `2`; non-Ansible positive-memory episodes remain `0`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.19 is not promoted to current.

## v2.20 Coupled Test-Provenance Repair Lane

- Status: `verified_official_artifact`.
- Campaign: `v2_20_test_provenance_repair_lane`.
- Artifact verification: `PASS`; ZIP SHA256: `3b6090f33ab4e5bb04ca4f922e51d4688b8d1ef5bc343ab6b26efc40b9e7ca25`; byte size: `64492`; ZIP entries: `43`; safe paths: `PASS`; duplicate paths: `0`.
- Workflow run: `28199100858`; artifact ID: `7890304839`; artifact name: `v2_20_test_provenance_repair_lane_artifacts`.
- Internal SHA256SUMS: `36` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `37` entries after adding the local official artifact-verification record.
- v2.20 audit: `PASS`; v2.19 through v2.12 regression audits: `PASS`; current-protocol audit/dry-run: `PASS`.
- Candidate scope: `PySnooper:1` only; PySnooper:2 was not pursued.
- v2.19 official ingest verified: `true`.
- Source acquisition status: `source_checkout_acquired`; source commit acquired: `e21a31162f4c54be693d8ca8260e42393b39abd3`.
- BugsInPy harness origin status: `BLOCK`; harness-origin bootstrap status: `BLOCK`.
- Authoritative SHA256 source: `none_available_before_v2_20_execution`; self-referential harness-origin hash detected: `false`.
- Proposed harness-origin candidate written: `true`, marked proposal-only and not authoritative for the current run.
- Target-test provenance status: `BLOCK`; target-test source/origin: `null`; target-test SHA256: `null`.
- Recursive provenance chain status: `PASS`.
- Replisome coupling status: `BLOCK`; chaperonin topology status: `BLOCK`.
- Redundancy-cache lookup result: `not_found`; expected-vs-actual SHA256 status: `not_applicable_not_found`; trust result: `not_trusted`.
- Nuclear-pore transport status: `PASS`; workspace purity status: `PASS`; workspace equivalence status: `BLOCK`.
- Environment lock status: `PASS`; command manifest status: `PASS`; baseline registry precheck status: `PASS`.
- Dependency recovery status: `not_executed_harness_origin_blocked`; pre-repair replay status: `not_run_harness_origin_blocked`.
- S-Engine cognitive state snapshot status: `PASS`; pre-generation prompt/context hash status: `PASS`.
- Reward signal status: `PASS`; graded signal: `0.0`; failure type: `bugsinpy_harness_origin_missing`.
- Test structural signature status: `PASS`; patch size cap status: `PASS`; cap overshoot severity: `none`.
- Patch generated: `false`; authorized: `false`; attempted: `false`.
- Target validation: `not_applicable_no_patch`; post-validation analysis: `not_run_no_validation`; duplicate replay: `not_applicable_no_patch`.
- PySnooper:1 scoreable: `false`; positive-memory-only: `false`.
- Current resolution band: `source_acquisition_N6_passed__test_provenance_N7_blocked__harness_topology_N8_blocked`.
- Exact blocker: no non-circular authoritative BugsInPy harness-origin SHA256 pin was available before v2.20 execution, so target-test provenance could not be trusted.
- Scoreable episodes remain `5`; positive-memory-only episodes remain `2`; non-Ansible positive-memory episodes remain `0`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.20 is not promoted to current.

## v2.21 Harness-Origin Verification Lane

- Status: `verified_official_artifact`.
- Campaign: `v2_21_harness_origin_verification_lane`.
- Artifact verification: `PASS`; ZIP SHA256: `35b22fd48d93ae5c5163ad9ab5d27ac99cfc351bfd2e08b869f38479aebade08`; byte size: `72234`; ZIP entries: `47`; safe paths: `PASS`; duplicate paths: `0`.
- Workflow run: `28201995136`; artifact ID: `7891479826`; artifact name: `v2_21_harness_origin_verification_lane_artifacts`.
- Internal SHA256SUMS: `39` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `40` entries after adding the local official artifact-verification record.
- v2.21 audit: `PASS`; v2.20 through v2.12 regression audits: `PASS`; current-protocol audit/dry-run: `PASS`.
- Candidate scope: `PySnooper:1` only; PySnooper:2 is not pursued.
- Harness-origin pin source: `https://github.com/soarsmu/BugsInPy.git` at `11c5f1eea954a42132cfd06bf257766a7963e0fd`.
- Expected harness manifest SHA256: `3706244b4618612fad4681578dd740d1e54dbe9069303072ab7802f656f0e608`.
- The pin is committed configuration; workflow-runtime generation of harness authority is forbidden.
- Target-test provenance remains the hard gate. If the pinned source does not contain `projects/PySnooper/bugs/1/tests/test_chinese.py`, dependency recovery, pre-repair replay, patch generation, validation, duplicate replay, and scoring remain blocked.
- Patch generated: `false`; authorized: `false`; attempted: `false` unless every v2.21 gate passes in a later verified run.
- Scoreable episodes remain `5`; positive-memory-only episodes remain `2`; non-Ansible positive-memory episodes remain `0`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.21 is not promoted to current.

## v2.22 BugsInPy Target-Test Materialization Lane

- Status: `verified_official_artifact`.
- Campaign: `v2_22_bugsinpy_target_test_materialization_lane`.
- Artifact verification: `PASS`; ZIP SHA256: `32aaad406f10acecb373d3313722c5c7130fd4c4c87ae879e5feb83706cb852a`; byte size: `78669`; ZIP entries: `49`.
- Workflow run: `28204197043`; artifact ID: `7892349852`; artifact name: `v2_22_bugsinpy_target_test_materialization_lane_artifacts`.
- Internal SHA256SUMS: `42` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `43` entries after adding the local official artifact-verification record.
- Candidate scope: `PySnooper:1` only; PySnooper:2 is not pursued.
- Official framework source: `https://github.com/soarsmu/BugsInPy.git` at `11c5f1eea954a42132cfd06bf257766a7963e0fd`.
- The pinned BugsInPy repository is framework/metadata, not the expected materialized project source tree.
- Absence from `projects/PySnooper/bugs/1/tests/test_chinese.py` in the framework checkout alone is not terminal.
- Official framework materialization found `PySnooper/tests/test_chinese.py`; artifact-preserved target-test SHA256 is `7a3d64cd702fdfa1eba8c08ac3c8934948a3ef0178f141c1f5599307c1fe59f3`.
- The target-test provenance status is `BLOCK` because the pinned framework materialized the test through fixed-commit-derived content before resetting to the buggy commit.
- PySnooper:1 terminal blocker: `blocked_target_test_requires_fixed_or_future_source`.
- Dependency recovery, pre-repair replay, patch generation, validation, duplicate replay, and scoring were not run after the provenance block.
- Scoreable episodes remain `5`; positive-memory-only episodes remain `2`; non-Ansible positive-memory episodes remain `0`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.22 is not promoted to current.
## v2.23 Source Acquisition Method Boundary

- Status: `verified_official_artifact`.
- Campaign: `v2_23_non_ansible_candidate_transition_lane`.
- Artifact verification: `PASS`; ZIP SHA256: `fbbed9f699822b16733a77a8c4b32c960a5ef3fed527059737b645802b0116ca`; byte size: `64784`; ZIP entries: `28`.
- Workflow run: `28211816313`; artifact ID: `7895186058`; artifact name: `v2_23_non_ansible_candidate_transition_lane_artifacts`.
- Internal SHA256SUMS: `21` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `22` entries after adding the local official artifact-verification record.
- v2.22 official ingest verified: `true`.
- Method decision: `globally_blocked_under_current_provenance_rules`.
- Source acquisition method registry: `PASS`.
- Compound provenance combination registry: `PASS`.
- Candidate selection: `not_run_global_method_block`; no new BugsInPy candidate was selected.
- Patch generated / authorized / attempted: `false` / `false` / `false`.
- v2.24 recommendation: External Safe-Source Candidate Acquisition Lane.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.23 is not promoted to current.
## v2.24 External Candidate Registry Precheck

- Status: `verified_official_artifact`.
- Campaign: `v2_24_external_safe_source_candidate_acquisition_lane`.
- Artifact verification: `PASS`; ZIP SHA256: `1801c197bb032c415dea4a33a9208042b0377d069e95fc4cde1ab4e0f2e7db8d`; byte size: `51049`; ZIP entries: `20`.
- Workflow run: `28212746325`; artifact ID: `7895535773`; artifact name: `v2_24_external_safe_source_candidate_acquisition_lane_artifacts`.
- Internal SHA256SUMS: `12` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `13` entries after adding the local official artifact-verification record.
- v2.23 official ingest verified: `true`.
- External candidate registry precheck: `BLOCK`.
- Blocker: `blocked_external_candidate_registry_missing_or_invalid`.
- Candidate selection: `not_run_no_valid_registry_entries`.
- External clone, failure capture, patch generation, validation, duplicate replay, and scoring were not run.
- Safest next step: `create_reviewed_external_candidate_registry_entry`.
- Recommended next lane: `v2.25 External Candidate Registry Construction Lane`.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.24 is not promoted to current.
## v2.25 External Candidate Registry Construction

- Status: `verified_official_artifact`.
- Campaign: `v2_25_external_candidate_registry_construction_lane`.
- Artifact verification: `PASS`; ZIP SHA256: `41ac43048ca834c203542b2e0b9c9045c2ceb1be43a963cf2d4c66ca250864b2`; byte size: `61756`; ZIP entries: `27`.
- Workflow run: `28213908809`; artifact ID: `7895944211`; artifact name: `v2_25_external_candidate_registry_construction_lane_artifacts`.
- Internal SHA256SUMS: `17` checked, `0` missing, `0` malformed, `0` failures; final ingested output manifest has `18` entries after adding the local official artifact-verification record.
- v2.24 official ingest verified: `true`.
- Registry schema and validator: `present`.
- Seed file present: `false`.
- Registry candidate count: `0`.
- Reviewed valid candidate count: `0`.
- External clone, failure capture, repair, patch generation, validation, duplicate replay, and scoring were not run.
- Exact blocker: `blocked_no_reviewed_external_candidate_seed_provided`.
- Smallest next step: provide `inputs/external_candidate_seed_draft.json` with one manually reviewed seed draft for v2.26.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.25 is not promoted to current.
## v2.26 External Candidate Seed Capture

- Status: `implemented_pending_official_artifact_ingestion`.
- Campaign: `v2_26_external_candidate_seed_capture_lane`.
- v2.25 official ingest verified: `true`.
- Seed draft present: `false`.
- External clone, failure capture, registry merge, repair, patch generation, validation, duplicate replay, and scoring were not run.
- Exact blocker: `blocked_no_external_candidate_seed_draft_provided`.
- Smallest next step: provide inputs/external_candidate_seed_draft.json with exactly one manually reviewed seed draft.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.26 is not promoted to current.
## v2.27 External Candidate Seed Draft Verification

- Campaign: `v2_27_external_candidate_seed_draft_verification_lane`.
- v2.26 official ingest verified: `true`.
- Seed draft present: `false`.
- Reviewed valid candidate count after run: `0`.
- Exact blocker/result: `blocked_no_external_candidate_seed_draft_provided`.
- Repair, patch generation, post-patch validation, and scoring were not run.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.27 is not promoted to current.
## v2.28 External Candidate Seed Draft Verification

- Campaign: `v2_28_external_candidate_seed_draft_verification_lane`.
- Candidate: `py_bugger_issue_65`.
- v2.27 official ingest verified: `true`.
- Result: `verified_external_candidate_seed_added`.
- Reviewed valid candidate count after run: `1`.
- Repair, patch generation, post-patch validation, and scoring were not run.
- Full scoring remains `NOT_RUN` / disallowed.
- Memory lift remains `undemonstrated`.
- Self-maintaining software is not demonstrated.
- Current protocol remains `v2.13`; v2.28 is not promoted to current.
## v2.29 Structural Repair Capability Integration

v2.29 adds neutral repair-context controls and attempts exactly one bounded repair on the reviewed py-bugger candidate if the replay gates pass. Current protocol stays v2.13; full scoring and broad claims remain disabled.



## v2.30 Failure Signature Canonicalization

v2.30 preserves prior text-hash evidence, adds a three-capture semantic failure signature gate, and continues the bounded one-patch repair path only if replay and registry-refresh checks pass. Current protocol stays v2.13; full scoring and broad claims remain disabled.

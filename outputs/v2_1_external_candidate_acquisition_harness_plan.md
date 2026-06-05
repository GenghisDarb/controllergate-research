# v2.1 External Candidate Acquisition Harness Plan

v2.0 blocked at candidate acquisition. That result is not negative capability evidence: the pilot did not reach memory-vs-no-memory replay scoring because no deterministic, non-subjective local replay failure was acquired from the bounded public candidate scan.

The lesson is narrower and useful. Naive public repo scanning is not enough to create replay-ready external/fork episodes. v2.1 therefore designs systematic preflight candidate mining before any v2.2 repair or scoring attempt.

## Prior Evidence

- v2.0 result: `blocked_external_candidate_acquisition_failure`.
- v2.0 candidate attempts: 5 public/fork repos.
- v2.0 scoreable external/fork episodes: 0.
- v2.0 is blocked acquisition evidence, not negative capability evidence.
- v1.9 limited user-owned organic-style memory lift remains preserved.
- v1.8 limited seeded controlled memory lift remains preserved.
- Episode 003 simple-task no-memory-lift result remains preserved.
- External memory lift remains undemonstrated.
- Self-maintaining software remains undemonstrated.
- Full scoring remains disallowed.

## Source Tiers

The harness should rank candidate sources before replay attempts:

1. `tier_1_curated_bug_benchmarks`: curated bug datasets such as BugsInPy-style or bounded Defects4J-style sources.
2. `tier_2_small_public_repos_with_simple_tests`: small public repos with pytest, unittest, npm test, cargo test, or go test.
3. `tier_3_archived_public_repos_with_dependency_drift`: archived repos with pinned dependencies and local reproduction paths.
4. `tier_4_forked_issue_replay_candidates`: public issues or PRs with local reproduction commands.
5. `tier_5_user_owned_fallback_not_external`: Brad-owned fallback repos for harness validation only, not external evidence.

## Preflight Checks

Each candidate must pass preflight before it can advance:

- clone or fork availability;
- license and ethics screen;
- language and ecosystem detection;
- dependency install command detection;
- test, build, lint, or check command detection;
- clean checkout baseline command result;
- deterministic failure presence or reproducible issue branch;
- no private secrets or services required;
- runtime under pilot budget;
- artifact capture feasibility;
- baseline comparison feasibility;
- corruption or downstream check feasibility.

## Preferred Ecosystems

The first harness should prioritize small, locally testable ecosystems:

- Python with pytest/unittest and requirements or pyproject metadata;
- JavaScript/TypeScript with npm test and a lockfile;
- Rust with cargo test;
- Go with go test;
- small Java/Maven/Gradle only when runtime is bounded.

Flutter/Android should be avoided unless the environment is already stable. Large monorepos, service-heavy apps, private APIs, paid services, and security exploit targets should be rejected.

## Readiness Scoring

Candidate readiness is scored from 0 to 100. Candidates below 75 should not proceed to v2.2 execution.

The score is based on deterministic local command, failure reproducibility, simple environment, license clarity, runtime budget, baseline comparability, memory relevance, corruption-check availability, and artifact-custody ease.

This scoring is not ControllerGate repair scoring. Candidate pool creation is not external memory lift. It only decides whether a public/fork candidate is ready for a replay-safe v2.2 attempt.

## Rejection Reasons

The harness should use a controlled rejection vocabulary:

- `rejected_no_local_test_command`
- `rejected_no_deterministic_failure`
- `rejected_private_service_required`
- `rejected_license_or_ethics_unclear`
- `rejected_runtime_too_large`
- `rejected_environment_not_reproducible`
- `rejected_subjective_validator`
- `rejected_security_exploit_target`
- `rejected_remote_ci_only`
- `rejected_no_baseline_path`
- `rejected_no_corruption_check`

Blocked candidates are not negative capability evidence. They mean the candidate did not reach a fair replay-ready capability test.

## v2.2 Handoff

A candidate may advance to v2.2 only if:

- readiness score meets the threshold;
- clean checkout can be reproduced;
- deterministic failure exists;
- no-memory and memory-enabled paths are feasible;
- corruption check is defined;
- artifact custody plan is complete.

v2.2 should still avoid full scoring. External memory lift remains undemonstrated until scoreable v2.2 episodes meet aggregate criteria. Self-maintaining software remains undemonstrated.

## Claim Boundaries

Candidate acquisition success is not repair success. Candidate pool creation is not external memory lift. User-owned fallback is useful for harness debugging but must not count as external/fork evidence.

External memory lift requires scoreable v2.2 episodes. Self-maintaining software remains undemonstrated. Full scoring remains disallowed.

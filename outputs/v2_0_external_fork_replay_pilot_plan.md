# v2.0 External-Fork Replay Pilot Plan

v1.9 is a meaningful positive milestone: ControllerGate met preregistered criteria for limited user-owned organic-style memory lift. Across three scoreable v1.9 user-owned organic-style replay episodes, memory-enabled paths outperformed no-memory paths three times, with no corruption and no decision-time/outcome overlap.

That result is still not external evidence. User-owned organic-style evidence is stronger than seeded-only evidence, but it remains owner-controlled. It does not prove organic external memory lift, full scoring, or self-maintaining software.

## Purpose

v2.0 is designed to test whether the memory advantage survives outside Brad-owned repositories. The target evidence class is forked public or archived public replay evidence, captured locally under strict artifact custody.

No v2.0 execution is performed in this plan. Full scoring remains disallowed. Self-maintaining software remains undemonstrated. Organic external memory lift remains undemonstrated until external replay evidence exists and aggregate criteria are met.

## Prior Evidence

- Episode 003 remains negative memory-lift evidence for a simple seeded hash-mismatch task.
- v1.8 remains positive only within the seeded controlled replay campaign scope.
- v1.9 remains positive only within the limited user-owned organic-style replay scope.
- TatMapper historical episodes remain quarantined for deterministic replay readiness.

## Candidate Ethics

Do not open spam pull requests or issues upstream. Do not exploit security vulnerabilities. Do not access secrets, tokens, private credentials, paid services, or private APIs. Use local fork or clone replay. Preserve license information and source repo metadata. Keep all intervention branches clearly labeled. Do not represent forked or seeded results as upstream maintainer results.

## Acceptance Criteria

A v2.0 candidate can be accepted only if the repo is public and forkable or locally cloneable, the license/ethics are safe, a clean checkout can reproduce the failure, deterministic commands and logs can be captured locally, no-memory and memory-enabled paths can run under identical replay conditions, corruption checks can be defined, all artifacts can be hashed, and decision-time/outcome separation can be enforced.

## Rejection Criteria

Reject candidates when the only evidence is expired remote CI, local replay cannot reproduce the failure, setup requires private services or secrets, the task is security exploit focused, the validator is subjective, the repo is too large or slow for a bounded pilot, licensing or ethics are unclear, baseline comparison cannot be run, or artifact custody cannot be preserved.

## Evidence Outcomes

Positive evidence would be an external/fork replay-ready episode where memory-enabled ControllerGate outperforms no-memory under identical replay conditions without corruption.

Negative evidence would be a replay-ready external/fork episode where memory-enabled ControllerGate does not outperform no-memory, or where memory causes harm or corruption.

Blocked evidence would be candidate acquisition failure, replay-gate failure, missing baselines, artifact custody failure, or decision-time/outcome leakage. Blocked acquisition is not negative capability evidence.

Inconclusive evidence would be equal performance under replay-ready conditions.

## Aggregate Criteria

Limited external-fork memory lift can be claimed only if at least three external/fork episodes are scoreable, memory-enabled outperforms no-memory in at least two, no positive episode has corruption, decision-time/outcome overlap remains zero, and replay/custody passes for every positive episode.

If only one or two external scoreable episodes complete, classify the result as `insufficient_episode_count_for_external_memory_lift`. If no external candidates can be acquired, classify it as `blocked_external_candidate_acquisition_failure`, not negative capability evidence. If memory-enabled never outperforms no-memory, classify it as `negative_evidence_no_external_memory_lift`.

## Claim Boundaries

v2.0 external/fork success may support limited external-fork memory lift only. It does not allow full scoring. It does not demonstrate self-maintaining software. It does not prove broad organic public repo performance unless aggregate external criteria are met. Seeded controlled, user-owned organic-style, and external/fork evidence must remain labeled separately.

## Stop Conditions

Stop execution if external candidate acquisition repeatedly fails, replay gate repeatedly fails, artifact custody fails, decision-time/outcome leakage appears, memory-enabled causes repeated corruption, or resource limits prevent safe completion.

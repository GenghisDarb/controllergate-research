# v1.8 Episode 003 Limited Replay-Scoring Candidate Plan

Status: preregistered limited replay-scoring candidate design only. Do not execute. Do not score.

Episode 003 is the first possible bridge from replay-capture mechanics toward limited replay scoring. It is not executed yet, and it does not demonstrate memory lift, repair capability, or self-maintaining software.

## Why Episodes 001 And 002 Were Not Scoreable

Episodes 001 and 002 were capture dry runs. They proved that ControllerGate can preserve controlled TORUS replay artifacts from birth, including baseline/failing/post-repair SHAs, raw logs, patch diffs, decision-time/outcome separation, proof obligations, and SHA256 manifests.

They were intentionally `not_scoreable` because they did not include baseline comparators or a memory-enabled ControllerGate path. They validate artifact-capture mechanics, not repair performance.

## Why Episode 003 Is Different

Episode 003 is a limited replay-scoring candidate design. It adds mandatory baseline comparison requirements before any scoring can be considered.

Allowed scoring mode:

```text
limited_replay_scoring_candidate_not_executed
```

Full scoring remains false.

## Proposed Failure Class

Recommended failure type:

```text
metadata_manifest_hash_mismatch
```

Expected failure signature:

```text
HASH_MISMATCH: README.md
```

The proposed validator computes a local SHA256 for `README.md` and compares it with the manifest's declared hash. The seeded failure uses a deliberately wrong hash. This is mechanical, deterministic, locally replayable, and does not judge TORUS theory content or scientific correctness.

## New Requirements Episode 003 Adds

Episode 003 must require:

- Replay Gate success before any limited scoring
- no-memory baseline
- memory-enabled ControllerGate path
- identical replay conditions for baseline and memory-enabled paths
- corruption/downstream check
- decision-time inputs separated from post-outcome evidence
- SHA256 manifest with zero mismatches
- proof obligations ledger with no missing required obligations

Preferred additional baselines:

- always-rebuild baseline
- simple-rule baseline

## Why Baselines Are Mandatory

Without a no-memory baseline, a successful repair-like outcome cannot show whether ControllerGate memory helped. It could be a trivial deterministic repair, a generic rule, or an always-rebuild behavior.

Memory lift remains undemonstrated unless memory-enabled ControllerGate outperforms the no-memory baseline under the same replay protocol.

## Replay Gate Before Scoring

Episode 003 may not be scored unless:

- clean checkout reproduces the pre-repair failure
- failing command and raw failing log exist
- failure signature exists
- baseline and memory-enabled action traces exist
- post-repair validation logs exist
- decision-time/outcome overlap check is PASS with zero overlap
- corruption/downstream check is PASS
- SHA256SUMS verifies with zero mismatches
- proof obligations ledger is complete

## Evidence Classification

Positive evidence would be: replay gate passes, baseline and memory-enabled runs are captured under identical conditions, memory-enabled result outperforms no-memory without corruption.

Negative evidence would be: replay gate passes but memory-enabled ControllerGate does not outperform baselines or causes corruption.

Blocked evidence would be: replay gate fails, artifacts are missing, decision-time/outcome overlap is detected, or baselines are absent.

## Boundaries

Episode 003 is not executed yet.

Full scoring is not allowed. Self-maintaining software remains undemonstrated. One seeded controlled episode cannot demonstrate self-maintaining software.

Success on seeded controlled evidence does not equal organic external repo evidence.

TatMapper historical episodes remain quarantined as review-required, with 0 deterministic-replay-ready episodes. TatMapper evidence must not be mixed into v1.8 controlled replay scoring.

## Do And Do Not Say

Do say:

- Episode 003 is a preregistered limited replay-scoring candidate design.
- Episode 003 is not executed yet.
- Baselines are mandatory before memory lift can be evaluated.
- Replay Gate must pass before any limited scoring.

Do not say:

- ControllerGate demonstrated memory lift.
- ControllerGate demonstrated self-maintaining software.
- Full scoring is allowed.
- Seeded controlled evidence equals organic external evidence.
- Episodes 001/002 were repair-performance evidence.

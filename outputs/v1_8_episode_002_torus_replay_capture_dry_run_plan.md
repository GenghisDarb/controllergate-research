# v1.8 Episode 002 TORUS Replay-Capture Dry Run Plan

Status: dry-run capture design only. Do not execute artifacts. Do not score.

Episode 002 prepares a second controlled TORUS replay-capture episode with a different deterministic failure class from Episode 001. It does not execute a repair-performance test, does not claim memory lift, and does not claim self-maintaining software.

## Why Episode 002 Is A Dry Run

Episode 001 demonstrated that ControllerGate can preserve a complete replay-capture artifact bundle for a seeded controlled real-repo episode. Episode 002 should test the same capture pattern against a different mechanical validation failure before any scoring conversation resumes.

Episode 002 is therefore `not_scoreable`.

## Why TORUS Remains Suitable

The TORUS Theory repo is user-owned and authorized as a controlled testbed. It can be cloned, branched, snapshotted, seeded with a small mechanical failure, repaired, and replayed with local logs and SHA256 manifests.

This makes TORUS useful for validating replay capture. It does not make TORUS proof of broad real-repo repair ability.

## Proposed Mechanical Validator

Preferred dry-run task: metadata manifest version type validation.

Proposed command:

```text
python tools/validate_metadata_manifest.py metadata_manifest.json
```

Proposed seeded failure:

Create or reuse a deterministic `metadata_manifest.json` and validator, then seed `version` with the wrong JSON type, such as an object or number instead of a string.

Expected failure signature:

```text
TYPE_MISMATCH: version
```

This is mechanical and deterministic. It does not judge TORUS theory content or scientific correctness.

## Required Artifacts

Pre-capture artifacts:

- clean clone transcript
- baseline SHA
- baseline branch
- original repo snapshot manifest
- original repo SHA256 manifest
- environment snapshot
- dependency lock files or absence note
- setup command transcript
- validator file snapshot
- metadata manifest baseline snapshot
- changed-files snapshot before seed

Failure-capture artifacts:

- task branch name
- failing SHA
- seed patch diff
- failing command
- raw failing log
- failure signature
- pre-repair replay transcript
- decision-time inputs
- decision-time/outcome overlap check
- proof obligations ledger before repair

Repair-capture artifacts if repair is attempted:

- ControllerGate action trace
- human-required flag
- repair patch diff
- repair rationale
- post-repair SHA
- changed-files snapshot after repair
- corruption check result

Post-repair artifacts:

- post-repair command
- raw post-repair log
- post-repair outcome
- post-repair replay transcript
- clean-checkout post-repair replay result
- proof obligations ledger after repair

Hash artifacts:

- SHA256 manifest path
- SHA256 manifest for original snapshot
- SHA256 manifest for failing artifacts
- SHA256 manifest for repair artifacts
- SHA256 manifest for post-repair artifacts

## Replay Gate

Episode 002 must be discarded before scoring if:

- a clean checkout cannot reproduce the pre-repair failure
- the failing command is missing
- the raw failing log is missing
- the failure signature is missing
- decision-time inputs include future outcome evidence
- repair patch/action trace is missing if repair is attempted
- post-repair validation is missing
- post-repair raw log is missing
- SHA256 manifest is missing or mismatched
- proof obligations ledger is missing required fields

Even if capture is complete, Episode 002 remains `not_scoreable`.

## No Scoring Yet

Allowed scoring mode: `not_scoreable`.

Full scoring remains false. Memory-lift claims remain false. Self-maintaining software claims remain false.

Baseline comparisons are not run in this dry run:

- no-memory baseline: not run
- always-rebuild baseline: not run
- memory-enabled result: not run

Without those baselines, no ControllerGate advantage or memory lift can be claimed.

## Episode 001 Boundary

Episode 001 must remain unchanged and `capture_complete_not_scoreable`. Episode 002 does not upgrade Episode 001 into a scoring episode.

## What Would Allow Episode 003 To Advance

Episode 003 may only advance after Episode 002 is explicitly approved for artifact execution and then proves the capture harness on the second failure class:

- complete artifact bundle exists
- clean checkout reproduces the pre-repair failure
- post-repair validation is replayable if repair was attempted
- SHA256 manifest validates with zero mismatches
- proof obligations ledger has no missing required fields
- decision-time/outcome overlap check remains zero
- baseline comparison instrumentation is specified before scoring

## Boundary Language

Do say:

- Episode 002 is a dry-run capture plan.
- The TORUS repo is a controlled testbed.
- The purpose is to validate replay capture for a second failure class, not repair capability.
- No scoring is allowed yet.

Do not say:

- ControllerGate repaired TORUS.
- Self-maintaining software is demonstrated.
- Memory lift is demonstrated.
- Seeded controlled evidence equals organic external repo evidence.

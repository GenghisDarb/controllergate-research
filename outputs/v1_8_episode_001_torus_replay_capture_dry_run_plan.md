# v1.8 Episode 001 TORUS Replay-Capture Dry Run Plan

Status: dry-run capture design only. Do not score.

Episode 001 prepares ControllerGate to capture the first replay-ready controlled real-repo episode from the TORUS Theory repo. It does not execute a repair-performance test, does not claim memory lift, and does not claim self-maintaining software.

## Why Episode 001 Is A Dry Run

The immediate goal is to prove the capture harness, not ControllerGate repair capability. v1.7-beta showed that historical TatMapper evidence can remain too incomplete for deterministic replay. v1.8 Episode 001 avoids that problem by defining the evidence bundle before the first controlled failure is created.

Episode 001 is therefore `not_scoreable`.

## Why TORUS Is Suitable

The TORUS Theory repo is user-owned and authorized as a controlled testbed. It can be cloned, branched, snapshotted, seeded with a small mechanical failure, repaired, and replayed with local logs and SHA256 manifests.

This makes TORUS useful for validating replay capture. It does not make TORUS proof of broad real-repo repair ability.

## Proposed Mechanical Validator

Preferred dry-run task: metadata manifest validation.

Proposed command:

```text
python tools/validate_metadata_manifest.py metadata_manifest.json
```

Proposed seeded failure:

Create a deterministic `metadata_manifest.json` and a small validator, then seed one missing required field or invalid required-file entry on a controlled branch.

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

Episode 001 must be discarded before scoring if:

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

## No Scoring Yet

Allowed scoring mode: `not_scoreable`.

Full scoring remains false. Memory-lift claims remain false. Self-maintaining software claims remain false.

Baseline comparisons are not run in this dry run:

- no-memory baseline: not run
- always-rebuild baseline: not run
- memory-enabled result: not run

Without those baselines, no ControllerGate advantage or memory lift can be claimed.

## What Would Allow Episode 002 To Advance

Episode 002 may become a limited replay-scoring attempt only after Episode 001 proves that the capture harness works:

- complete artifact bundle exists
- clean checkout reproduces the pre-repair failure
- post-repair validation is replayable if repair was attempted
- SHA256 manifest validates with zero mismatches
- proof obligations ledger has no missing required fields
- decision-time/outcome overlap check remains zero
- baseline comparison instrumentation is specified before scoring

## Boundary Language

Do say:

- Episode 001 is a dry-run capture plan.
- The TORUS repo is a controlled testbed.
- The purpose is to validate replay capture, not repair capability.
- No scoring is allowed yet.

Do not say:

- ControllerGate repaired TORUS.
- Self-maintaining software is demonstrated.
- Memory lift is demonstrated.
- Seeded controlled evidence equals organic external repo evidence.

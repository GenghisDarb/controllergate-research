# Causal state and recorded-history experiment

Read [CAUSAL_HISTORY_REPORT.md](CAUSAL_HISTORY_REPORT.md) for the interpretation, results and exact boundaries.

## Completed results

- Both original source-derived graphs reproduce: 18 states/58 enabled edges and 6 states/10 enabled edges.
- All nonempty selected single readouts separate all state pairs through some controlled future experiment, despite ambiguous current snapshots.
- A single readout plus PASS/BLOCK admits guaranteed adaptive initial-state identification in 2–4 commands for these classes. Two exported policies were replayed for all 24 original initial states.
- Pairwise distinguishability does not guarantee retrospective identification: the six-state external-lactate-only channel has a certified failure that observing status repairs.
- Hidden fixed catalyst supports compress from 144 to 139 and 48 to 33 future-behavior classes. Every initial observation fiber can be brought to a known predictive class within four commands, even when the full context remains unknowable under these commands.
- A separately specified external-supply diagnostic exposes previously silent catalyst differences. Predictive equivalence is scoped to the allowed interventions.
- A separate implementation verifies all 40 declared cases. No numerical cap was hit.

These are exact finite-model/control results. Commands are not physical time, and this lane does not test resonance frequencies, consciousness, biological prediction or a uniquely necessary fourteen.

## Reproduce

The scripts use Python's standard library. The portable entry point checks the frozen source, copies the experiment into a fresh temporary directory, runs the primary calculation, independent implementation check, explanatory witnesses and policy replays, then compares every scientific result while preserving the originals:

```bash
python verify_replay.py
```

An optional `--receipt NEW_PATH` saves the compact receipt; existing paths are refused. Only execution timestamps and their resulting generated-output hashes are normalized. Source and specification hashes must still match, and all recorded hash fields are verified against the actual files before comparison. The completed portability receipt is `PORTABILITY_RECEIPT.json`.

For manual reproduction, copy the directory to a disposable location, remove `results.json` and the copied derivative output files there, then run:

```bash
python causal_history.py
python independent_review.py
python derive_witnesses.py
python export_policies.py
```

`python independent_review.py` writes a review receipt in its own directory, so use the temporary-copy wrapper above when all recorded bytes must be preserved. `FROZEN_DESIGN.json` preserves the original code, model and specification identities. `FOLLOWUP_SPEC.json` explicitly labels the later explanatory diagnostic. The prior model and its seed graphs were already known when the local freeze was made. The separate checking implementations are not external peer review.

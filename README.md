# ControllerGate

Current branch: `controllergate-v1.7-alpha-real-trace-pilot`

This repository currently contains:

- `controllergate_v1_6_release/`: v1.6 freeze evidence at psi.
- `controllergate_v1_7_alpha/`: v1.7-alpha real repository / real agent trace pilot scaffold.

## Current Status

v1.6 is frozen at psi based on the supplied separate fixture artifact custody package. The verified claim is bounded to controlled diagnostic benchmark evidence.

v1.7-alpha is not scored yet. The scaffold, schema, templates, and audit tooling are ready, but real maintenance episodes are still required before any real-pilot result can be claimed.

## Quick Checks

```powershell
python controllergate_v1_7_alpha\scripts\validate_ledger.py
python controllergate_v1_7_alpha\scripts\audit_trace_ledger.py
```

In this Codex app session, Python may need to be called with the bundled runtime:

```powershell
& 'C:\Users\thisb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' controllergate_v1_7_alpha\scripts\validate_ledger.py
& 'C:\Users\thisb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' controllergate_v1_7_alpha\scripts\audit_trace_ledger.py
```

Expected current result:

- Ledger validation passes with zero episodes.
- Trace audit reports `BLOCKED` because no real episodes have been supplied. This is an intentional non-pass state, not a v1.7-alpha failure.

## Next Evidence Needed

Provide a populated GitHub-backed repository or exported real maintenance episodes with CI logs, patch diffs, agent/tool traces, generated artifact manifests, and visible/downstream outcome evidence.

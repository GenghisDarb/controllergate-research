# ControllerGate

Current branch: `controllergate-v1.7-alpha-real-trace-pilot`

This repository currently contains:

- `controllergate_v1_6_release/`: v1.6 freeze evidence at psi.
- `controllergate_v1_7_alpha/`: v1.7-alpha real repository / real agent trace pilot scaffold.

## Current Status

v1.6 is frozen at psi based on the supplied separate fixture artifact custody package. The verified claim is bounded to controlled diagnostic benchmark evidence.

v1.7-alpha is not scored yet. Ten completed evidence bundles have been normalized into the trace ledger, validation passes, and the audit currently reports `REVIEW_REQUIRED`. The review classification layer confirms there are 0 external real repo episodes, so real-pilot scoring remains blocked.

## Quick Checks

```powershell
python controllergate_v1_7_alpha\scripts\validate_ledger.py
python controllergate_v1_7_alpha\scripts\audit_trace_ledger.py
python controllergate_v1_7_alpha\scripts\audit_episode_review_classification.py
```

In this Codex app session, Python may need to be called with the bundled runtime:

```powershell
& 'C:\Users\thisb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' controllergate_v1_7_alpha\scripts\validate_ledger.py
& 'C:\Users\thisb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' controllergate_v1_7_alpha\scripts\audit_trace_ledger.py
& 'C:\Users\thisb\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' controllergate_v1_7_alpha\scripts\audit_episode_review_classification.py
```

Expected current result:

- Ledger validation passes with 10 normalized episodes.
- Trace audit reports `REVIEW_REQUIRED`.
- Episode review classification passes with 2 correction-review episodes, 8 controlled benchmark evidence episodes, and 0 external real repo episodes.
- Scoring is not run.

## Next Evidence Needed

Collect and normalize external real repository maintenance episodes before v1.7-alpha real repo scoring. A GitHub remote should be added after this clean classification milestone if the repo is ready to push.

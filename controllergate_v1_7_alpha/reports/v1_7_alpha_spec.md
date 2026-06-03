# ControllerGate v1.7-alpha Real Pilot Specification

## Purpose

Move from controlled diagnostic benchmarks to real-world pilot evidence.

Core question:

> Can ControllerGate's discovered causal trace memory improve maintenance decisions on real repository / real agent traces without relying on synthetic issue generation?

## Required Inputs

Minimum artifact classes:

1. Repository snapshot: commit hash, branch, dependency lockfiles, configuration files, test files, and source files relevant to the failure.
2. CI / test logs: failing test output, command used, environment metadata, traceback or assertion failure, and before/after test result if available.
3. Patch attempts: diffs, changed files, changed line counts, commit or patch identifiers, and rejected or reverted attempts if available.
4. Agent/tool traces: tool calls, file reads, file writes, stale reads, command outputs, failed assumptions, retry loops, premature done claims, and false success reports.
5. Generated artifacts: build outputs, reports, notebooks, intermediate files, generated configs, package artifacts, and checksums if available.
6. Outcome evidence: visible test result, hidden/downstream result if available, human intervention, corruption/regression, and whether the agent claim matched reality.

## Recommended Dataset Shape

Start small:

| Requirement | Target |
| --- | --- |
| Repositories | `1` |
| Real maintenance episodes | `10` to `25` |
| Repeated failure families | at least `3` |
| Near-match but different failures | at least `3` |
| Stale-read or false-completion examples | at least `2` |
| Dependency/config drift examples | at least `2` |
| Generated-artifact mismatch examples | at least `2` |
| Visible-pass/downstream-fail cases | at least `2` |

## Runtime Modes

Compare:

1. strengthened best practice
2. always rebuild
3. no-memory ControllerGate
4. poisoned-memory ControllerGate
5. predefined-memory ControllerGate
6. discovered-memory ControllerGate
7. real-trace discovered-memory ControllerGate

The real-trace discovered-memory mode may learn only from earlier real episodes in the trace ledger.

## Blindness Rules

v1.7-alpha must enforce:

- no safe-action oracle;
- no hidden best-action injection;
- no future outcome evidence before the episode point;
- no direct label leakage from trace metadata;
- no scoring-field access during policy selection;
- no human outcome summaries as input unless available at that time;
- no training on the heldout episode outcome before decision;
- memory keys must be evidence-derived from real trace artifacts.

## Memory Key Sources

Allowed:

- failing test names;
- error signatures;
- stack trace shape;
- touched file paths;
- dependency/config files involved;
- command failure class;
- stale-read indicators;
- patch action type;
- generated artifact mismatch type;
- visible-pass/downstream-fail pattern;
- agent claim vs actual result mismatch.

Forbidden:

- true final success label;
- hidden test result before decision;
- human-curated correct action label;
- future correction note;
- benchmark-only family name;
- artificial attack class.

## Pass Gates

1. SHA/custody verification passes for all input artifacts.
2. Future-leakage audit passes.
3. Policy blindness passes.
4. Discovered memory hidden/downstream pass is greater than no-memory.
5. Discovered memory corruption is lower than no-memory.
6. Discovered memory human-required rate is lower than no-memory.
7. Discovered memory false-positive transfer is less than or equal to `0.20`.
8. Productive recommendation precision is at least `0.70`.
9. Avoidance transfer precision is at least `0.70`.
10. Discovered memory beats predefined memory on at least one repeated real failure family.
11. Discovered memory does not over-transfer on near-match real failures.
12. Stale-read or false-completion detection succeeds in at least one real case.
13. Generated artifact mismatch detection succeeds in at least one real case.
14. Proof ledger completeness is `100%`.
15. All failed criteria are preserved and reported.

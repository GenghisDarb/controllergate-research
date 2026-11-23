# ControllerGate observation-to-outcome integration candidate

## Result and scope

The local candidate connects measured observations to the frozen outcome predicates through the actual producer, fresh-record constructor, wrapper, seal, public compiler, and planner code. **The final run passes 42 test methods: 34 new regression methods and eight unchanged original test functions.** Fifteen real command-line invocations complete the seal, causal compilation, all ten planner arms, gain compilation, terminal compilation, and ownership compilation. Those workflow invocations use **12 explicitly synthetic receipts for six software test cells**, producing 90 arm/program executions. They are integration fixtures, not historical provider executions or evidence of biological equivalence.

Separately, the exact pinned Audioread source and the project's actual Audioread harness ran locally on Python 3.12.14. Both the `rawread` and `unrelated_backend` routes exited zero. The measured `rawread` import satisfies the frozen rawread control; the unrelated backend does not supply that measurement and remains unresolved for that control. The import exercise does not reproduce the exact original provider capsule or execute its pytest nodes.

The current remote branch was checked again during this pass. It remains `controllergate-v1.7-alpha-real-trace-pilot` at `38897b79588f3ff4b1b9002eedc299a9bcf05140`; the returned branch inventory contains one branch and the release inventory is empty. No remote repository, previous evidence package, or live PC was modified.

## Reproduce without earlier audit folders

Everything needed for the bounded replay is inside this `integration/` folder. The replay imports the included `checkout/`, reads its included registries and original test functions, and uses the included `vendor_source/audioread_577f8e2/`. It does not depend on an earlier `audit_work/` folder, network access, credentials, provider downloads, or the optional `prior_candidate/` directory.

Use Python 3.12 and Git for the recorded environment. The replay uses the standard library and invokes Git to construct a small, explicitly local source-capsule schema fixture. The original pytest runner was unavailable in this environment; its attempted pinned installation found no accessible package candidate. We therefore executed the eight unchanged, plain original test functions with the standard `unittest` runner. We do not claim the full original pytest suite passed.

From this directory:

```bash
python run_integration_checks.py --output replay_new
```

Choose a new output directory on every run. The script refuses to overwrite an existing evidence directory. `results_v6/` is the final recorded run. Python 3.13 and later can produce a different real Audioread result because the standard-library `aifc` module is absent; do not interpret an environment change as a replay of this Python 3.12.14 observation.

To inspect the proposed repository change, use `CONTROLLERGATE_INTEGRATION_CANDIDATE.patch`. It applies cleanly with `git apply --check` against the included unmodified `source/` baseline. It changes eleven files. The supplied `checkout/` already contains that patch, so do not apply it there a second time. `extend_pipeline.py` is an intermediate construction record, not the reproduction entry point.

## What was corrected

| Root cause | Implemented correction | Detection and covered boundary |
|---|---|---|
| The wrapper attached a v4 registry hash but copied the old candidate-specific boolean. | The shared raw-to-fresh constructor invokes the actual declarative evaluator on measured, role-specific operands; the legacy boolean is diagnostic only. | Wrong legacy true/false fixtures are corrected. The seal and compiler independently recompute the outcome. |
| Whole-observation hashes mixed outcome fields with volatile streams and metadata. | The new, explicitly versioned projection binds the selected role's measured operands and declared replay context. Raw custody hashes remain separate. | Changed irrelevant stderr preserves scoped replay; changed outcome does not. |
| The first repair required fields used only by the other role. | Role acceptance requires every operand of that role; both role predicates are separately recorded as diagnostics. | A directly observed rawread control can pass without inventing an unobserved incident measurement. |
| Audioread emits nested import records; Poetry's older record omitted actual cwd. | Explicit Audioread import/route adapters; source-supported return-code and project-name aliases; the producer now records the actual executed Poetry cwd basename. | Wrong routes, missing markers, conflicting nested/flat data, and old Poetry records remain unresolved or rejected. |
| The v4 inventory named 70 cells while the producer still executed the v2 inventory of 32. | A pre-execution compatibility check compares shared commands, environment, fixture, provider, role, and identity. Each raw record carries its producer registry and cell binding. | Changed argv/provider contracts block before execution. The 38 added cells are reported as not implemented by that producer. |
| Binding hashes could name a declared command while carrying a different observed command. | Reconstruct the actual argv/cwd from the original producer's replay layout, venv selection, fixture flag, and substitution rules; compare with both raw and broker observations. | Rehashed unrelated commands/cwd fail, including mirrored broker edits. Literal `--check/` is not normalized to `--check`; Linux backslashes remain literal. Windows separator conversion is restricted to explicitly identified path slots. |
| Nullable outcomes were collapsed into false or truthy booleans downstream. | Fresh receipt annotations allow `bool | None`; wrapper, seal, and planner require explicit evaluated status and `True` for acceptance. | Missing Audioread evidence remains `EXECUTED_SEMANTICS_UNRESOLVED`. Boolean-to-integer forgeries are rejected. |
| A copied receipt could look like two replay observations. | Require distinct receipt IDs, replay indices, and broker operation IDs; reject duplicate submitted receipt IDs at sealing. | A copied receipt does not establish replay. These consistency checks do not authenticate external execution. |
| Role predicate success was promoted to sensitivity and verified invariants. | Keep role classification, a common-predicate descriptive contrast, and causal invariants separate. No sensitivity is emitted without the missing independent invariant-measurement support. | Identical Py-bugger outcomes can satisfy both frozen predicates, but now yield `NO_DECLARED_OUTCOME_CONTRAST`. Darker fixture outcomes yield a descriptive contrast without causal authority. |

The existing necessity, sufficiency, factorial, and alternative-exclusion mechanisms remain in the source and their original plain tests passed. The correction does not replace them with terminology or erase their prior implementation.

## Complete source and role accounting

`SOURCE_MANIFEST.json` verifies **89 ControllerGate source files** against Git blob SHA-1 identities and also records fresh SHA256 hashes. `VENDOR_SOURCE_MANIFEST.json` verifies **ten Audioread files**, including its license, against commit `577f8e2cbe99f33dd7d236deb1626e372f4762e9`. `SOURCE_EXCERPTS.json` and `.md` provide selected original paths, physical line numbers, hashes, and GitHub URLs.

`PROGRAM_OBSERVATION_LEDGER.json` covers all nine programs, their exact incident/control predicates, measured operand fields, adapters, and measurement limitations. `CELL_ROLE_AND_MATERIALIZATION_LEDGER.json` covers every one of the 70 software test cells, including exact argv, known factor values, program-level provider lists, role requirements, and precise materialization blockers.

| Inventory fact | Count and interpretation |
|---|---|
| Frozen programs | 9 programs spanning 8 issue candidates. |
| Current registered software test cells | 70; these are experiment cases, not biological cells. |
| Cells implemented by the invoked producer | 32 from its v2 registry. |
| Later additions not selected by that producer | 38. |
| Cells missing its required per-cell provider ID, resource budget, and platform | 37 lack each of those fields. Later program-level provider lists still exist; this is not a claim that all provider metadata is absent. |
| Roles with frozen acceptance predicates | 26: 12 incident and 14 control. Eight of these are later additions not selected by the old producer. |
| Other roles requiring explicit measurement obligations | 44: 14 exclusion, 9 negative, 1 secondary, 1 diagnostic, 2 intervention, 17 factorial. |
| Newly declared Audioread argv incompatibilities | 3 cells: two use `unrelated` where the source harness requires `unrelated_backend`; one requests an unimplemented compatibility-provider argument. These frozen contracts were not silently rewritten. |

The 44 other-role cells were checked against the v4 program registry, v4 cell registry, alternative-exclusion registry, original producer's candidate/name branches, Batch101 projection and semantics, the v4 generator, and the later 70-row Batch103 intervention registry. The latter records preserve factor values and program-level provider choices, but contain no additional cell-specific outcome predicates. The source's causal-intervention module specifies what necessity, sufficiency and interaction evidence must contain. We retain those requirements and emit both measured predicate diagnostics where available; we do not assume every other role means “control.”

## Meaningful positive and negative results

The final fixture pipeline accepts two reproducible role-classification pairs. One Darker pair exhibits a descriptive change in the same incident/control predicate vector. An identical Py-bugger pair satisfies both role predicates but has no such contrast. The latter is a recovered false-promotion route, not a negative result about biological mechanisms. Both pairs correctly leave independently verified invariants, causal sensitivity, necessity, sufficiency, ownership, and repair gain unestablished.

The real Audioread run shows that the explicit nested-field adapter can carry an actual source observation into the frozen semantic criteria. It also preserves the important distinction between “another backend imported” and “rawread imported.” That is a concrete local integration result, not a complete replay of the original issue or a benchmark of Reactome's value.

Some original measurements remain weaker than their names suggest. The Py-bugger producer's `persisted_source_diff_mutation_count` is a binary indicator of any `git diff --numstat` output, not a count of independently persisted mutations. Several controls use zero matching `FAILED` tokens, which alone does not prove the intended tests collected and ran. Those definitions are preserved and identified in the program ledger; this repair does not retroactively strengthen their scientific meaning.

## Review, failures, and limits

`INDEPENDENT_REVIEW_FINAL.json` records the independent focused check. A valid source-shaped baseline was accepted and all eight targeted mutations were rejected, including unrelated command/cwd changes, boolean/integer and status changes, option suffix changes, and Linux backslash changes. This review covered execution/semantic binding, not external provider authentication or the full original suite.

`DEVELOPMENT_CORRECTIONS.json` preserves the observed correction history. The first 35-method run exposed an untested command-expansion gap in independent review. The subsequent constructor extraction briefly had a missing local `pred_hash` variable, causing 28 test errors; the run stopped before the workflow. A later schema inspection corrected the v2 source capsule key to `full_commit_sha` and added an actual source-capsule constructor test. Review then found two normalization loopholes, now covered by regression tests. Earlier result files remain historical receipts and are not the final acceptance record.

The whole provider-installation wrapper `main` was not launched: it acquires sources and dependencies and requires exact provider capsules unavailable here. Instead, the same actual raw-record constructor used by that `main`, the producer/parser functions, and the downstream real CLI scripts were executed locally. Source/provider authenticity remains dependent on their acquisition and independent verification boundary. Our synthetic dictionaries deliberately do not claim it.

No biological isomorphism, causal gain from Reactome, historical attribution correction, external repair success, or physical TORUS/TLD validation follows from these software integration tests. This package repairs identifiable evidence-processing faults and makes the remaining experimental obligations explicit.

## Packaging

The reproduction requires `checkout/`, `vendor_source/`, and `run_integration_checks.py`. Include `source/`, manifests, ledgers, patch, README, plans, final results, correction history, and independent review for a reviewable evidence package. Earlier result summaries/logs may be retained without their duplicate pipeline trees. The copied `prior_candidate/` and `test_deps/` are not required. Exclude `__pycache__`, `*.pyc`, and the local `.git` directories created inside source-capsule test fixtures. There are no remote credentials in the intended manifest.

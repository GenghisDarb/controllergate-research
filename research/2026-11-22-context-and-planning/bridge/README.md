# Conditional acquisition: a bounded ControllerGate bridge

## Outcome

The inspected Batch103 path freezes an **order**, not an observation-dependent next-action policy. This local addition demonstrates a conditional-policy interface with charged observations, exact finite-model reasoning, and a competent generic reference. It is a new synthetic acquisition control, not a replay of archived provider outcomes and not a biology experiment.

All substantive arms obtained the same **18 attainable pairs out of 32 scenarios**. Fourteen scenarios had no available pair under the declared model. Adaptation reduced wasted acquisition work; it did not improve acquisition coverage, establish ownership, or repair the live repository. Biological names added no information or benefit over the same generic planner.

| Frozen arm | Pairs acquired | Total actions | Actions on 18 attainable cases | Actions on 14 unattainable cases | Failed vault accesses | Costed prerequisite probes |
|---|---:|---:|---:|---:|---:|---:|
| Best fixed order | 18 | 164 | 52 | 112 | 128 | 0 |
| Generic adaptive, vault access only | 18 | 76 | 44 | 32 | 40 | 0 |
| Generic adaptive, prerequisite probes allowed | 18 | 74 | 48 | 26 | 22 | 16 |
| Reaction-schema adapter | 18 | 74 | 48 | 26 | 22 | 16 |
| Same adapter with neutral labels | 18 | 74 | 48 | 26 | 22 | 16 |
| Unknown-as-unavailable negative control | 0 | 0 | 0 | 0 | 0 | 0 |

Most of the total saving comes from proving, within the small model, when further acquisition cannot succeed and stopping. Costed prerequisite probes save only **two actions overall** compared with adaptive vault access alone; they cost **four additional actions on successful cases**, offset by six saved on impossible cases. They provide no extra benefit in two of the four graph families. The zero-cost negative control is useless: it prematurely treats uncertainty as absence and misses all 18 attainable pairs.

The fixed-order arm uses the historical success-or-budget stop rule. Adaptive arms also have sound model-relative impossibility stopping. Consequently the total difference combines conditional stopping and action selection; it does **not** isolate reordering alone. A separately frozen fixed-order-plus-sound-stop ablation would be needed for that narrower attribution. No such post-result arm has been silently added here.

The reaction adapter deliberately compiles into the **same generic solver**. Its tie is a compiler/label-invariance result, not an independently replicated algorithm comparison. No Reactome-specific performance advantage is established.

## What is grounded in actual source

The source snapshot is identified at commit `38897b79588f3ff4b1b9002eedc299a9bcf05140`. `SOURCE_LEDGER.md` gives stable URLs and physical source line numbers.

1. `reactome_planner_v1.py` records missing prerequisites, blocked reactions and alternatives. Its ranking depends on declared information gain, cost and intervention ID. The six pure-function controls in `source_capability_audit.json` reproduce that limited behavior.
2. `run_batch103_planner_arm.py` sets information gain to remaining fixed-list rank, rejects a selection that departs from the next frozen entry, and records unavailable vaults before continuing. It can stop early on a pair; it cannot branch to a different next selection after an observed blockage.
3. `reactome_source_grounded_scenarios_v2.py` preserves source lineage and maps present relation fields into operation families. Those family choices are unchanged when relation payload quantities/context change without changing source-value presence. This does not say the entire RPIR drops those values.
4. The inspected R3 shadow loop hashes source/operation labels and emits its structural verifier receipt in the generation loop. It is useful structural bookkeeping. It does not simulate resource consumption, concentrations, transport, crowding or executed software interventions.

These findings do not erase existing AND gates, typed unknown states, source custody, or nonauthorization boundaries. There is also an earlier real mechanism-rehearsal path: `isomorphism/primitives.py` checks resource underflow, compartments and irreversible transitions, and `isomorphism/runtime.py` executes primitive controls through canonical stages and SQLite receipts. The narrower finding is that the inspected **Batch103 source-grounded shadow generator** uses the label hash chain instead of that state-transition path. Resource-aware mechanisms should not be described as entirely absent or newly invented here.

These findings also do not establish that all historical failures had one cause. The separate history review traces a more immediate fresh-execution semantic-binding problem; fixing observation semantics must precede relying on those observations for adaptive decisions.

## Frozen design and fairness

`experiment_spec.json` declares four graphs, three hidden Boolean prerequisites, four paired routes, an eight-action budget, and six arms. All eight availability worlds are evaluated in each graph. A vault read or prerequisite probe costs one action. The planner receives only the public dependency model, prior and previous paid observations; the actual world is passed only to the environment and scorer.

The generic solver uses exact rational finite-horizon dynamic programming. It maximizes expected pair acquisition, then minimizes expected actions. The fixed-order comparator is globally optimized under the same public model using subset dynamic programming over all vault permutations. It is stronger than an arbitrary old order. Pure probes cannot improve that fixed policy because it cannot condition future choices on their answer and probes do not themselves yield a pair receipt.

The design, solver, runner, tests and verifier were sealed before evaluation:

```text
FROZEN_DESIGN.json SHA256
f13bbe36a9862f8ca2e32c81d372fd8f5b03ae8135505ea7e6c64a40ea7631ff

results.json SHA256
d63d92e3b26f711f49aa333649338cb66c40a650ac5bfc3941ca5aaafcd8cddf
```

These are local integrity anchors, not externally authenticated preregistration. No scenario, policy, graph or stopping criterion was changed after results opened. The evaluated combinations were frozen separately from development unit fixtures; they are not independently sampled real incidents or a claim of population generalization.

## Verification and reproduction

Python 3 standard library only. No packages, services, network or accounts are required.

From this directory:

```sh
python -B verify_experiment.py
python -B -m unittest -v test_conditional_acquisition.py
python -B audit_source_capabilities.py
```

The original receipt records **nine mechanism tests passing**. The independent elementary trace verifier checked **192 arm/scenario runs**, **462 charged observations**, and **64 generic/adapter trace equalities**. It found no budget violation, false pair terminal or false model-relative unreachable conclusion. It also checks that exact initial expected costs/probabilities equal the exhaustive realized averages, and that the sealed source hashes are unchanged.

For a fresh full replay, copy the five sealed source/spec files into an empty directory. Then run:

```sh
python -B run_experiment.py --freeze
python -B run_experiment.py --execute
python -B verify_experiment.py
```

The runner refuses to overwrite an existing design seal or result file. Timestamps and the new local seal hash change; scientific counts and trace decisions should agree. Keep original receipts instead of replacing them with replay receipts.

## Honest integration boundary

`conditional_acquisition.py` is an executable research component, not a deployed ControllerGate change. Its reaction adapter requires **explicit AND prerequisite references**; it cannot infer executable dependencies merely from biology labels. An integration should preserve current legal-action, source/provider, proof, and patch gates. Its policy should propose only the next already-authorized observation and record the history/context it used.

For a meaningful next real campaign, freeze the conditional policy code, registered action inventory, observation schema, costs, context/freshness contracts, stop rules and generic baseline. Run paid selected observations through the corrected semantic verifier. Evaluate useful evidence acquired, successful-case cost, false attribution, unavailable operations and total cost separately. Missing or stale evidence stays unresolved; a complete-world model should never be silently assumed for real software. No proposed policy here can authorize a repair.

## Limits

The prerequisites are persistent Boolean availability conditions, not consumable tokens or measured spatial resources. Observations are noiseless and the dependency model is supplied as correct. The finite belief solver can grow exponentially; these tiny graphs do not establish scalability. There are no measured kinetic rates, quantities, transport delays, contention, observer effects or physical perturbations. The result supports a modest implementation direction: freeze a conditional acquisition policy and test it against a competent generic policy, while preserving the possibility that the biological vocabulary contributes no measurable advantage.

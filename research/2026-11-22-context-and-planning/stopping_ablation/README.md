# Fixed order with sound stopping: exploratory follow-up

## Status and scope

PASS. This follow-up was prompted by the original experiment's outcomes. It reuses the same four synthetic dependency graphs and all eight Boolean resource-availability worlds per graph. It is **not independent validation**, a new biological result, a real-provider experiment, or evidence for a TORUS-specific mechanism.

The original frozen experiment and its results were not modified. The follow-up specification, implementation, and original input hashes were sealed before executing the follow-up. The seal is a local integrity record, not external preregistration. Results include 64 new episodes: two new arms across the same 32 scenarios.

## Main result

Every arm below acquired all 18 attainable pairs. There are 14 unattainable scenarios.

| Policy | Total actions | Actions in attainable scenarios | Actions in unattainable scenarios |
|---|---:|---:|---:|
| Original best fixed order; pair/budget stopping | 164 | 52 | 112 |
| Same original fixed order plus sound impossibility stopping | 102 | 52 | 50 |
| Best fixed vault order optimized with sound impossibility stopping | 96 | 54 | 42 |
| Original generic adaptive vault selection | 76 | 44 | 32 |
| Original generic adaptive selection with prerequisite probes | 74 | 48 | 26 |

Both new fixed-order arms made 14 sound, model-relative impossibility stops and 18 pair-acquired stops. They used no prerequisite probes. Neither changed its action order or skipped any action conditionally.

The 96-action optimum is over **vault-only permutations**, matching the adaptive vault-only comparator's observation class. It is not an optimum over fixed sequences containing prerequisite probes. Once sound impossibility stopping is allowed, a probe can potentially save later actions even without reordering; the original success-only baseline's probe-dominance rationale must not be extended to this different stopping rule.

Adding sound stopping to the original order saves 62 actions. Reoptimizing a fixed order with that stopping rule saves another 6. A residual 20-action advantage remains for adaptive vault selection, and prerequisite probes provide a further net 2-action saving under the original objective. These are sequential descriptive contrasts on this finite set, not a unique causal decomposition or an estimate for a larger population.

Thus most of the original 88-action gap between the success-only fixed baseline and adaptive vault selection was attributable to the stopping-rule difference. Conditional selection still helps after matching sound stopping. Its residual benefit includes avoiding reads already known to be unavailable; it should not be described narrowly as rearranging a complete permutation.

The optimized fixed order trades two additional actions on attainable cases for eight fewer actions on unattainable cases, compared with keeping the original fixed order. It minimizes the declared overall expected cost, not each stratum separately. Probe-enabled adaptation likewise has higher attainable-case cost than vault-only adaptation, while reducing unattainable-case cost enough to improve the total.

## Per-graph total costs

| Graph | Original fixed | Original order + stop | Best fixed + stop | Adaptive vault | Adaptive + probes |
|---|---:|---:|---:|---:|---:|
| triangle_and_complex | 46 | 34 | 31 | 23 | 22 |
| mixed_arity | 32 | 22 | 22 | 18 | 18 |
| shared_bottleneck | 40 | 12 | 12 | 12 | 12 |
| redundant_route | 46 | 34 | 31 | 23 | 22 |

The shared-bottleneck graph's entire original improvement is matched by sound stopping. The residual advantage comes from the other three graphs.

## Why the subset optimization is valid

Let W be the eight worlds under the declared uniform prior, and let S be a subset of already queried vaults. For a hypothetical world w, the observations on S determine a public posterior support B_S(w) and acquired-vault mask A_S(w). Define

\[
c_S(w)=\mathbf 1\{\text{no acquired pair in }A_S(w)\}
\mathbf 1\{\exists v\in B_S(w):\text{at least one route is available in }v\},
\qquad q(S)=\frac18\sum_{w\in W}c_S(w).
\]

This is the probability the fixed-order process must continue after the queried subset. A completed pair remains completed under additional observations, and a sound impossibility conclusion remains impossible as posterior support shrinks. Consequently stopping cannot be undone by a longer prefix. The deterministic observation law makes q(S) depend on the subset, not the order used to reach it.

For a frozen permutation with prefix subsets S_0,...,S_7, the expected number of charged actions is

\[
\mathbb E[N]=\sum_{k=0}^{7}P(N>k)=\sum_{k=0}^{7}q(S_k).
\]

The exact dynamic program therefore uses

\[
F(S)=q(S)+\min_{a\notin S}F(S\cup\{a\}),\qquad F(S_{\rm all})=0.
\]

Exact rational arithmetic and lexicographic tie breaking select one frozen permutation per graph. Hypothetical-world enumeration occurs during public-model planning; it does not give the episode policy its actual private world. During execution, the decision function receives only the public model, already paid observations, fixed order, and budget.

## Verification

- The DP optimum and chosen order matched enumeration of all 40,320 permutations in each graph: 161,280 permutations in total.
- An alternate survival-table calculation reconstructs public histories through the original public-state function and matches the bit-mask calculation for every subset and world.
- Survival monotonicity was checked for each one-action subset extension.
- Direct episode costs match the DP expectation exactly.
- All new episodes respect the fixed action sequence, unit charges, pair requirements, budget, and sound impossibility condition.
- Small development fixtures check that an empty unknown state is not declared unavailable, one failed route does not invalidate another route, no known-bad vault is silently skipped, and unconditional routes remain obtainable.
- Original source/result hashes matched before and after execution.

The alternative calculations share the original declared Model semantics. These checks are mathematical and implementation consistency checks, not a second independently developed scientific model.

## Files and rerun behavior

`experiment_spec.json` specifies this exploratory follow-up. `run_stopping_ablation.py` implements the optimizer, controls, finite exhaustive checks, and reports. `FROZEN_DESIGN.json` pins those two sources and four original input files. `results.json` contains summaries, all new traces, per-graph results, comparison receipts, and limits.

The script deliberately refuses to replace an existing seal or result. To reproduce independently, use a separate copy of the folder without its generated seal/results, retaining the original sibling `bridge` inputs, then run `python run_stopping_ablation.py --freeze` followed by `python run_stopping_ablation.py --execute`. Do not delete or overwrite this evidence copy.

## Attribution repair

Root cause: the original fixed baseline and adaptive arms differed in both conditional action selection and permission to stop on model-relative impossibility.

Fix: match the stopping permission, first keeping the old permutation and then optimizing the best complete fixed permutation for the matched objective.

Detection: audit allowed action classes, stopping rules, inference permissions, objective, prior, and budget before attributing a cost difference to a named algorithmic feature.

Where else it applies: any benchmark comparing an adaptive policy with a static schedule can mix search-order gains with abstention, early stopping, caching, known-bad action omission, or extra observation privileges. Separate those contributions before claiming the benefit comes from one feature.

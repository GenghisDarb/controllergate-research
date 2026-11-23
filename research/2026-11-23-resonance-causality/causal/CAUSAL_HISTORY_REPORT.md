# Current views, recorded histories and controlled futures

## What was tested

This is a new, explicitly specified extension of the previously frozen six-event reaction model. It tests the useful part of the proposal that an observer's available history and participation in causal chains can matter to closure and prediction.

The model is untimed. An input command requests one of the six curated reactions. If its prerequisites are present, the command updates the integer inventory and reports PASS. Otherwise it leaves the state unchanged and reports BLOCK. No stochastic rates, physical clock or oscillation frequency are assigned. This is therefore an action/observation test, not a physical resonance experiment.

The raw reaction JSON was independently parsed. Both original reachable sets were rebuilt, giving the same 18 states/58 enabled edges and 6 states/10 enabled edges. All eight subsets of the three selected metabolite readouts were tested, including an empty-observer negative control. Every map was tested with and without observing PASS/BLOCK. A separate extension allows all eight fixed catalyst masks, yielding 144 and 48 possible states. These product supports are not reachable from an original all-active seed under the original six commands alone.

The design and code were sealed before these new outcomes. The underlying reaction model and previous reachable-state counts were already known. The freeze is local provenance, not external preregistration.

## 1. A current view and a predictive state are different objects

Let a command a update the state by F_a, and let H be an observation map. Define its visible response as either H(F_a(x)), or the pair (PASS/BLOCK, H(F_a(x))).

A current observation is sufficient for the controlled future when equal current observations always have equal visible responses and equal successor observation classes, for every allowed command. Starting from equality of H, repeated refinement by each command's response and successor class produces a stable equivalence relation. Two states in one stable class have the same visible responses under every finite command word.

The calculation is finite and exact. Each proper refinement increases the number of state classes; a stable relation is checked explicitly for every action. A separately implemented backward state-pair calculation confirms both the class counts and every shortest distinguishing-word length. This is established finite-machine mathematics applied to this particular source model, not a new general theorem.

### Newly computed distinction

In the 18-state system, the GA3P-only, pyruvate-only and external-lactate-only snapshots have 3, 4 and 3 distinct values. With readout alone, their future-behavior partitions refine as follows:

| Readout | Class counts as future command depth is admitted |
|---|---|
| GA3P | 3 → 7 → 14 → 18 |
| Pyruvate | 4 → 8 → 14 → 17 → 18 |
| External lactate | 3 → 5 → 12 → 18 |

Thus every nonempty selected single view eventually distinguishes all state pairs through some command/response experiment, although the instantaneous readout does not identify the state. In the six-state system the corresponding sequences are 3 → 5 → 6, 3 → 6, and 2 → 3 → 5 → 6.

These depths refer to pair-specific experiments. They do not mean one universal command of that length identifies an arbitrary unknown state. The experiment separately checks that stronger question.

The triple of metabolite coordinates is already injective on each original conservation class, giving 18 or 6 classes immediately. In those classes it is an equivalent representation of the full metabolite state, not evidence of a genuinely smaller autonomous macrostate.

## 2. A recorded interaction history can repair snapshot ambiguity

The observer maintains a set B_t of states still compatible with its record. After taking command a_t and observing response r_t, it updates

\[
B_{t+1}=\{F_{a_t}(x):x\in B_t,\ R_{a_t}(x)=r_t\}.
\]

This explicitly includes action history as well as readouts. A fixed point on the complete finite belief graph asks whether an adaptive command policy guarantees a target for every possible response. All reachable belief sets were enumerated; no search cap was reached.

Three targets are kept separate:

1. **Current-state homing:** the present state becomes known. Commands may have forced several different starting states into the same current state.
2. **Initial-state identification:** the starting state becomes known. Distinct hypotheses must not merge within an identical observed-response branch.
3. **Predictive-class homing:** the remaining possibilities can be different full states, provided they have identical future visible behavior under all allowed commands.

With one metabolite readout plus PASS/BLOCK, adaptive policies identify both initial and current state from every original observation fiber:

| Available readout plus status | Maximum guaranteed commands: 18-state class | Six-state class |
|---|---:|---:|
| GA3P | 3 | 2 |
| Pyruvate | 3 | 2 |
| External lactate | 4 | 3 |

Two concrete policies were exported and replayed on every eligible initial state: GA3P plus status in the 18-state system, and external lactate plus status in the six-state system. All 24 initial-state replays identify the correct original state within three commands. `POLICY_EXAMPLES.json` exposes every action, response and belief update.

This is stronger than saying that history might help. It gives completed finite policies and exact domain limits. It does not show that passive, unrecorded biological observations carry the same information, nor does it establish the original full ControllerGate architecture.

## 3. A genuine failed inference was exposed and repaired

In the six-state class, **external lactate without PASS/BLOCK can distinguish every pair of states under some command word, yet no adaptive strategy guarantees identifying the starting state from its ambiguous zero-lactate fiber**.

The calculation supplies a short impossibility certificate. The initial fiber is state IDs {0,1,3,4,5}. Four reaction commands merge at least two starting hypotheses into the same state while giving the same visible readout. Import is uninformative. Export can single out state 3, but its other response leaves the four-state set {0,1,4,5}. In that set, four commands again merge hypotheses, while both transport commands are uninformative. At least one allowed outcome therefore prevents certain initial-state identification, however long the adaptive strategy continues.

This is a failure of guaranteed retrospective identification, not a failure of all prediction. Current-state homing remains possible within three commands. Observing PASS/BLOCK repairs the initial-identification failure: a successful transition and a blocked request can reach the same inventory but leave different recorded evidence.

The distinction directly matters to a controller: a final valid or stable state does not establish which earlier state or failure route produced it. A controller that needs causal attribution must preserve the relevant transition/status record rather than only final output.

The empty-observer control makes this especially clear. Without any readout or status, all initial states are output-equivalent, yet a fixed command sequence can force all 18 starting states to a known current state in seven commands, or all six to one current state in five commands. All starting hypotheses remain possible. This is synchronization by intervention, not information gained about the past.

## 4. Some hidden differences are irrelevant only within a declared environment

With hidden but fixed catalyst masks and the joint metabolite readout:

| Candidate state support | Future-behavior classes | Distinct-state pairs equivalent under every allowed command word |
|---|---:|---:|
| 18 metabolite states × 8 masks = 144 | 139 | 8 |
| 6 metabolite states × 8 masks = 48 | 33 | 24 |

The full catalyst mask cannot always be recovered. Nevertheless, an adaptive policy can identify the correct **predictive equivalence class** from every initial observation fiber in at most four commands. Full-state homing succeeds for only 15 of 18 fibers in the first support and one of six in the second. Including the catalyst mask in the observation makes every candidate state immediately distinguishable, which is a known-state control rather than a surprising emergent result.

The equivalent hidden states are not asserted to be physically identical. For example, two states share all metabolite values, but one has GAPDH active while the other has it inactive. In the selected example, required resources are absent and all other catalytic routes are off. Both states remain quiescent under every original command.

A **post-result diagnostic**, separately specified and preserved, adds the missing GA3P and phosphate to both states. A forward GAPDH request now passes in one and blocks in the other. This external supply changes the allowed intervention vocabulary and conservation class. It exposes a difference that was previously silent; it does not contradict the original closed-model equivalence.

Consequently, causal or predictive closure needs an environment/intervention boundary. A hidden variable can be safely irrelevant for one task and necessary after the environment changes. Dropping it forever because it was silent in one closed test would be an unjustified generalization.

The separate unreported catalyst-change check likewise shows that memory based on a fixed-context assumption can become wrong after the context changes. Correct history tracking requires either a valid fixed-context premise or an explicit update/reset when the environment changes.

## 5. How this advances the TORUS interpretation

The results provide a precise constructive interpretation of an observer participating in a causal chain. A policy chooses a command from the current belief; the command changes the physical/model state; its response changes observer memory; memory changes later command choice. The joint state (system, observer memory, relevant environment) is what closes this feedback description.

That interpretation does not require making the observer causally external. It also does not establish that human experience or the existence of reality is generated by this particular mechanism. The computation models a finite controller–system loop, with explicit action effects. It neither models consciousness nor supplies physical oscillation frequencies.

For the broader closure program, the new distinctions are useful:

- Projected return is an equality of observations at two points.
- Predictive closure concerns all allowed future input/output behavior.
- Recorded history may resolve a current ambiguity.
- A controlled reset can make the current state known while erasing evidence of the initial state.
- A compressed predictive state can omit a hidden distinction only relative to a declared intervention vocabulary.

This strengthens the research by making both the positive claims and the failures explicit. The all-active graphs do not support a smaller nontrivial predictive quotient for these nonempty observations: every state eventually has distinguishable behavior. The context-extended graphs do support genuine predictive compression, but that compression changes when external supply actions are admitted.

## Reproduction and evidence

- `EXPERIMENT_SPEC.json` and `FROZEN_DESIGN.json`: primary design and hashes before new execution.
- `causal_history.py`, `results.json`, `summary.json`: complete original calculation and outcomes.
- `independent_review.py`, `INDEPENDENT_REVIEW.json`: separately implemented checking of all 40 observer/context/channel cases, including refinement counts, paired-word lengths, belief counts and strategy bounds. Both implementations were authored in this analysis lane; this is independent implementation checking, not external peer review.
- `FOLLOWUP_SPEC.json`, `derive_witnesses.py`, `FOLLOWUP_RESULTS.json`: explicitly post-result explanatory certificate and external-supply witnesses.
- `export_policies.py`, `POLICY_EXAMPLES.json`: concrete adaptive policies and 24 original-state replays; derived from the primary implementation.

The primary script refuses to overwrite `results.json`. The portable `verify_replay.py` wrapper checks frozen source identities, copies the necessary package files to a fresh temporary directory, executes all four scripts, and compares every scientific field while preserving the original files. It normalizes only execution timestamps and the resulting regenerated-output hash after checking that hash against the actual new file. `PORTABILITY_RECEIPT.json` records the completed portability gate. No private archive contents or external full papers are required for these computations; Python's standard library suffices. This replay is not external peer review.

## Primary theoretical references

Moore's 1956 finite-machine experiments explicitly distinguish pairwise distinguishability from identifying an unknown initial state, and provide examples where an experiment can erase information about its starting condition. The negative case found here is an application of that known issue, not a newly discovered universal principle. [Original chapter](https://www.cs.cmu.edu/~cdm/resources/Moore1956-gedanken-experiments.pdf), especially Theorem 1 and the discussion of state equivalence.

Barnett and Crutchfield develop input–output computational mechanics and predictive representations for stochastic channels. That is a relevant bridge for a later stochastic extension. The current experiment remains a deterministic command model, so it does not claim to have inferred an epsilon-transducer from biological data. [Authors' primary publication page](https://csc.ucdavis.edu/~cmg/compmech/pubs/et1.htm), *Journal of Statistical Physics* 161 (2015), 404–451, DOI 10.1007/s10955-015-1327-5.

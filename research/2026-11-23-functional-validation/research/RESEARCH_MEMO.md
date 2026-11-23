# Executable reaction semantics and a real observation-model check

Prepared 2026-11-23. This memo accompanies the six-event Reactome source contract and a new, limited reanalysis of two real author-provided CTCF tracking records. It does not establish a whole-cell isomorphism, molecular kinetic parameters, or a TORUS-specific biological mechanism.

## What was actually obtained

Official Reactome records support six directed events: LDH forward/reverse, lactate/proton export/import, and GAPDH forward/reverse. The compact contract retains chemical identity, compartment, displayed unit stoichiometry, and nonconsumed catalytic roles. It is a manual, source-grounded transcription of the rendered records. Direct exact SBML/Content Service retrieval was blocked on the available route; it is not a byte-faithful SBML conversion.

Two real MATLAB tracking files were recovered from the eLife publisher archive of the authors' Spot-On repository. Their decoded bytes match the provider's Git-blob identifiers. Source identity, file timing, and the analysis split were inspected and frozen before fitting. A small empirical comparison was then completed, including heldout trajectories and a second named cell without refitting.

## Six-event source contract

All chemical species below are cytosolic unless marked extracellular. Each coefficient is one, as displayed by the source records.

| Event | Directed reaction or transport | Preserved catalytic role |
|---|---|---|
| [R-HSA-71849](https://reactome.org/content/detail/R-HSA-71849) | PYR + NADH + H+ → LACT + NAD+ | Active LDH alternative |
| [R-HSA-70510](https://reactome.org/content/detail/R-HSA-70510) | LACT + NAD+ → PYR + NADH + H+ | Active LDH alternative |
| [R-HSA-373875](https://reactome.org/content/detail/R-HSA-373875) | LACT + H+ → LACT(extracellular) + H+(extracellular) | Active membrane BSG:MCT complex |
| [R-HSA-373867](https://reactome.org/content/detail/R-HSA-373867) | LACT(extracellular) + H+(extracellular) → LACT + H+ | Active membrane BSG:MCT complex |
| [R-HSA-70449](https://reactome.org/content/detail/R-HSA-70449) | GA3P + Pi + NAD+ → 1,3BPG + NADH + H+ | Active GAPDH alternative |
| [R-HSA-70482](https://reactome.org/content/detail/R-HSA-70482) | 1,3BPG + NADH + H+ → GA3P + Pi + NAD+ | Active GAPDH alternative |

The apparent reversible/LEFT-TO-RIGHT issue has a straightforward resolution: separate directed records represent the forward and reverse chemistry. The compiled model should preserve both event identities, rather than infer unrestricted reversal from an edge label.

The NAD+/NADH coupling is substantive. GAPDH consumes the same cytosolic NAD+ entity that LDH produces; LDH consumes the NADH and proton that GAPDH produces. Adding the two forward equations cancels these cofactors and gives GA3P + Pi + PYR → 1,3BPG + LACT. This is a real source-supported shared-resource test. It does not determine which reaction happens first, how rapidly it happens, or the actual intracellular cofactor pool.

### Important source semantics

* [LDH R-HSA-184549](https://reactome.org/content/detail/R-HSA-184549) and [GAPDH R-HSA-372871](https://reactome.org/content/detail/R-HSA-372871) are defined sets of catalytic alternatives. An available active alternative supplies a role. Requiring every listed isoform at once would be wrong; treating alternatives as biologically exclusive would also be an added assumption.
* [BSG:MCT R-HSA-204396](https://reactome.org/content/detail/R-HSA-204396) is a membrane complex. The source composition includes two BSG proteins and a transporter homodimer alternative. The compact contract asserts availability of the active complex; it does not model its assembly.
* The LDH pages also identify negative regulation by PolyUb-LDHA. No quantitative regulation law was recovered. Turning that annotation into a hard zero-rate inhibitor would invent information. Its omission from the bounded active-role contract must remain visible.
* A catalyst guard describes the selected annotated catalytic channel. It is not proof that all alternative or uncatalyzed physical pathways are impossible.
* The forward GAPDH source title spells the enzyme “GADPH.” The source title is retained in the receipt; the chemical catalyst is GAPDH.

The bridge agent independently opened the complete reverse GAPDH record after the original source contract was sealed. The extra confirmation is recorded in the source manifest, without rewriting the original receipt.

## What a faithful transfer can prove

For a selected untimed state-transition model, let f map qualified resource states bijectively and g map event identities bijectively. A faithful transfer must preserve enabled actions and satisfy f(T_a(x)) = T'_{g(a)}(f(x)) whenever the transition is defined. Joint input requirements, resource consumption, outputs, read-only catalytic guards, compartment identity, and atomic shared-resource updates all belong to this contract. The observation map and permitted environment interventions must be declared too.

Preserving these properties proves an exact transfer of the selected model's untimed traces. The source-to-ControllerGate review found the six directions and guards consistent within the declared bounded domain. A formal statement must also respect the implementation's exact-integer resource range: the archived guard primitive becomes UNRESOLVED outside its representable range, while Python's abstract integer model is unbounded.

A timed or stochastic isomorphism is stronger. With a bijection of continuous-time Markov states and unchanged time units, the generators must satisfy Q'(f(x),f(y)) = Q(x,y), including escape rates. If t' = κt, the new generator is Q/κ. Matching graph edges and token updates does not supply these rates. A deterministic kinetic transfer similarly needs the vector field to commute with the state map.

Reactome's compact record is already an abstraction of biological systems. Exact contract-to-code transfer therefore does not by itself establish exact cell-to-code transfer. Molecule counts, concentrations, volume, catalytic activity, stochastic propensities, context, observation errors, and environmental exchange remain separate empirical obligations. A persistent ControllerGate evidence receipt must not silently be treated as a consumable molecule; an explicit resource-processing state is needed for that interpretation.

## Prior art and novelty boundary

* Racunas, Shah and Fedoroff, **A case study in pathway knowledgebase verification** (2006), [DOI 10.1186/1471-2105-7-196](https://doi.org/10.1186/1471-2105-7-196), [open primary article](https://pmc.ncbi.nlm.nih.gov/articles/PMC1522024/), already applied logical completeness, consistency and well-formedness checks to Reactome versions 10–14. Semantic verification of pathway databases is established work.
* Cardelli et al., **Forward and Backward Bisimulations for Chemical Reaction Networks** (CONCUR 2015), [DOI 10.4230/LIPIcs.CONCUR.2015.226](https://doi.org/10.4230/LIPIcs.CONCUR.2015.226), gives formal exact reductions under ODE semantics. Bisimulation can merge states; it must not be confused with the stronger bijection required by a literal 1:1 isomorphism.
* Lin et al., **Automatic construction of Petri net models for computational simulations of molecular interaction network** (2024), [DOI 10.1038/s41540-024-00464-z](https://doi.org/10.1038/s41540-024-00464-z), describes automated construction of signaling Petri nets from integrated molecular knowledge. The paper's signaling-net abbreviation should not silently be expanded as stochastic Petri nets.
* Beckers and Halpern, **Abstracting Causal Models** (2019), [arXiv:1812.03789](https://arxiv.org/abs/1812.03789), distinguishes exact, uniform and stronger forms of causal abstraction. A successful observational match is weaker than preserving declared interventions.

These sources support a careful, executable transfer and intervention-aware validation program. They prevent claims that pathway compilation, conserved-resource bookkeeping, or causal abstraction itself was invented here. A potentially useful contribution is the specific portable contract, truthful missing-information behavior, independent implementation comparison, and tests that expose lossy resource or compartment mappings. Whether that merits a paper depends on broader benchmarks and comparison with existing formal tools.

## Completed empirical analysis: real CTCF displacement records

Source: Hansen et al., **Robust model-based analysis of single-particle tracking experiments with Spot-On**, eLife 2018, 7:e33125, [DOI 10.7554/eLife.33125](https://doi.org/10.7554/eLife.33125). Data and example source came from [the publisher archive](https://github.com/elifesciences-publications/spot-on-matlab), pinned commit `f155c4c889ea124a8f55ab8f620e540628e18f92`. Author attribution and the repository GPLv3 license are retained. We did not run the full author Spot-On fitting pipeline.

The chosen files are the first named cell in each provided rep1 and rep3 directory: U2OS C32 Halo-CTCF, PA-JF646, 1 ms excitation, nominal 134 Hz. Internal acquisition dates are 2017-02-23 and 2017-03-09. The files contain 7,678 and 6,136 tracks respectively. Singleton tracks cannot provide displacement estimates and were retained in quality counts rather than silently counted as fitted trajectories.

The recorded coordinates are in micrometers. Each file's timestamps equal frame number × 0.0075 seconds exactly under the numerical check. The author example script uses 7.477 ms, a 0.3076% difference; this analysis consistently uses the actual stored timestamps. This is a disclosed metadata discrepancy, not proof of which clock value was physically exact.

### Frozen comparison

The primary specification and code were sealed locally at 08:34:55 UTC before fitting. This is a local audit trail, not external preregistration. Rep1 was split by a deterministic hash of whole-trajectory ordinal: 2,791 eligible training trajectories and 1,206 heldout trajectories. Rep3 supplies 2,812 eligible trajectories for a no-refit transfer check.

At frame lags 1, 2, 3 and 4, the analysis uses at most the first valid endpoint pair per trajectory. It averages marginal two-dimensional log densities within each trajectory and then across trajectories. This is a composite prediction score, not a likelihood that assumes all overlapping increments are independent. Training uses the same trajectory weights. Paired bootstrap intervals resample trajectory-average score differences; they are conditional on the fitted parameters and within-record exchangeability, not cell-population or parameter confidence intervals.

Both models use the same simplified localization and exposure model. With elapsed time Δt, exposure E = 0.001 s and localization error σ, a component with diffusion D has vector density exp(−r²/[4(D(Δt−E/3)+σ²)])/[4π(D(Δt−E/3)+σ²)]. One component is compared with a two-component mixture sharing σ. No component-count search was performed. Both models omit defocalization, tracking-selection bias and molecular switching.

| Scoring record | Eligible trajectories | Two minus one component, nats per trajectory-average marginal score | Conditional trajectory-bootstrap 95% interval |
|---|---:|---:|---:|
| Rep1 cell01, heldout | 1,206 | 0.615888 | [0.526181, 0.710782] |
| Rep3 cell01, no refit | 2,812 | 0.877488 | [0.777256, 0.982268] |

The gain is positive at each of the four lags in both records. The fitted descriptive mixture has Dslow = 0.005600 and Dfast = 3.388342 μm²/s, σ = 0.046206 μm, and observed slow-component weight 0.788235. These are parameters of the selected displacement model; the weight is not a validated molecular bound fraction. The one-component fit reaches its allowed σ upper bound of 0.075 μm, which required a stronger comparison.

### Post-result sensitivity

After inspecting that bound, a separate specification and code were sealed at 08:37:49 UTC. Each lag received an unrestricted two-dimensional Gaussian with a freely fitted mean and full covariance, using the same training weights. This removes the localization variance cap, isotropy and zero-drift restrictions from the Gaussian comparison. The Gaussian parameters have closed-form weighted maximum-likelihood estimates. The original mixture and both original scoring sets remain unchanged.

| Scoring record | Original mixture minus free Gaussian | Conditional trajectory-bootstrap 95% interval |
|---|---:|---:|
| Rep1 heldout | 0.624185 | [0.536998, 0.720693] |
| Rep3 no refit | 0.877628 | [0.778417, 0.981216] |

All four fitted covariance matrices are positive definite, and the mixture gains persist at every lag. This is a post-result sensitivity on the same data, not another independent validation. A free Gaussian is a descriptive null, not a calibrated Brownian kinetic model.

### What the result supports and leaves open

The selected records support the narrower conclusion that a single fitted Gaussian displacement population predicts these observed displacements worse than the tested mixture. This remains true after relaxing its variance, mean and covariance restrictions. There is still visible mixture misfit: maximum radial-CDF discrepancies range from about 0.055 to 0.100 in rep1 and 0.085 to 0.112 in rep3. We have not established that two physical molecular states generated the data.

Defocalization and track survival are material here: different lags select different surviving tracks, and recorded trajectories may not be independent molecules. A two-cell analysis does not quantify biological population variability. No binding-rate estimate, perturbation effect, crowding mechanism, whole-cell prediction, or fourteen-layer mechanism follows.

The empirical analysis is complementary to the Reactome transfer. The token tests establish a declared semantic preservation property; the tracking analysis demonstrates a quantitative observation-model check on real data. CTCF tracking is not a validation dataset for the LDH/GAPDH network or for ControllerGate's biological fidelity.

## Files, checks and limitations

`source_manifest.json` records pinned URLs, identifiers, hashes, bytes, provenance, timing and source scope. `reactome_event_contract.json` remains unchanged. The primary and sensitivity specifications, code, frozen receipts, quality results, numerical results and CDF plot are under `ctcf_reanalysis/`. Their README supplies a safe fresh-directory replay procedure.

Direct public-download failures are retained as exact route failures; they are not generalized into claims that the public data are unavailable. An unidentified public CSV format example was recovered but excluded from the empirical biological analysis. Provider base64 responses and bulk source captures are scratch evidence and should be excluded from the final deliverable archive; the exact MAT files, license, compact provenance and our code are sufficient for the described replay.

# What a functional correspondence can establish

## The claim has changed from the label control

Brad's stronger hypothesis concerns preserving the design's executable relationships: which actions can happen, what they consume or retain, which environment permits them, and how several actions compose. The earlier comparison after neutral renaming tested label dependence. It neither established nor refuted this stronger hypothesis.

There are two separate translations here:

1. **Curated biological knowledge to a chosen executable model.** Reactome supplies identified participants, compartments, reactions and catalytic roles. Our compact model adds a declared untimed token interpretation and supplies hypothetical active-role and resource inventories. It omits rates, continuous space, regulation magnitudes and internal assembly dynamics. This step is not proved equivalent to a living cell.
2. **The chosen executable model to software.** This step has precise preservation conditions. It can be proved and checked without claiming that the source model is complete biology.

## Source model and observation map

Let P be a finite set of identified, compartment-qualified places. A marking m:P→N assigns resource-token counts. The three active-catalyst places are asserted availability of an active aggregate role, not an inference from abundance. For reaction r, let u_r and v_r be input and output multisets and c_r the nonconsuming catalyst read requirements. A declared action is enabled when

    m(p) ≥ u_r(p) and m(p) ≥ c_r(p), for every place p.

On success its successor is

    T_r(m) = m − u_r + v_r.

Catalyst places are disjoint from consumed/produced places in this bounded contract. Their token counts therefore remain unchanged. A transport reaction consumes the qualified source-place token and produces a different destination-place token; it does not silently pool the two compartments.

The software observation map is an injective renaming f:P→P′ of those same places, together with their exact counts. The state map is the pushforward Φ(m)(f(p))=m(p). The action map retains each curated source event as a distinct action. Biological names need not appear in the executor; participant identity, role, multiplicity, location and shared-resource relationships must remain.

This is a 13-place abstract state contract: ten metabolite places and three active-role places. It is not a claim of thirteen physical dimensions, a TORUS ladder length, or thirteen independent biological degrees of freedom.

## Preservation proposition and proof

**Conditional proposition.** Suppose the compiler maps each input, output and read requirement by the same injective f, preserves action identity, and uses one joint precondition check followed by an atomic state update. Then enabling is equivalent and updates commute:

    r is enabled at m ⇔ translated(r) is enabled at Φ(m),
    Φ(T_r(m)) = G_translated(r)(Φ(m)).

**Proof.** Injectivity supplies one software place for each source place without merging quantities. For each p, the software guard is exactly Φ(m)(f(p))≥u_r(p) and ≥c_r(p), so the conjunction has the same truth value. On a successful action,

    G(Φ(m))(f(p)) = m(p) − u_r(p) + v_r(p)
                 = Φ(T_r(m))(f(p)).

Every retained catalyst has zero net change. Failed actions preserve the original marking. Applying this equality inductively proves corresponding finite action traces while the assumptions continue to hold.

For ideal exact-integer interpreters, a bijective state/action renaming with the converse transitions gives an isomorphism of the declared transition systems. A relation that only requires each source transition to have a matching target transition is a simulation; requiring the matching condition in both directions gives a bisimulation. These are established formal-methods concepts, not a new TORUS theorem. See Klaus Sutner, *Bisimulations*, Carnegie Mellon University, pp. 5–6: https://www.cs.cmu.edu/~cdm/resources/28-bisimulation.pdf .

**Implementation boundary.** The local faithful adapter invokes the archived floating-point RESOURCE_FLUX guard. It conservatively returns UNRESOLVED if any checked per-resource working balance plus requested magnitude exceeds 2^53. The generic and source-oracle interpreters use Python integers. Consequently the implementation equivalence is claimed only for steps and traces whose required state is known and whose complete working updates remain in the adapter's declared exact-integer range. It is not an unqualified equivalence over every Python integer. The evaluated initial counts are 0, 1, 2, with small exact successors; the finite initial grid need not itself be closed under successor updates.

## Properties that transfer, and those that do not

Under a genuine state/action isomorphism, corresponding finite traces, reachable states and state predicates expressed through the observation map agree. Resource nonnegativity, catalyst retention and declared compartment distinctions transfer within this model. Under only a one-way simulation, specify the direction: extra behaviors in an overapproximation can create spurious failures, and an underapproximation can miss failures. An unrestricted claim of equivalent behavior needs both directions or a property-specific proof.

Preserving possible untimed transitions does not preserve reaction rates, waiting-time distributions, thermodynamic feasibility, occupancy statistics or real-time completion. Liveness additionally depends on scheduling and environmental/fairness assumptions. Our atomic-batch comparison uses a declared sequential commit order; it is not a real multi-worker/SQLite race test. A production shared-state implementation would need transaction isolation or versioned compare-and-swap in addition to this pure functional transition kernel.

SBML explicitly separates stoichiometry, modifiers and kinetic laws. A modifier can affect a reaction without being produced or consumed, and kinetic information is a different modeling obligation: SBML Level 3 Version 1 Core, §4.11, https://sbml.org/specifications/sbml-level-3/version-1/core/sbml-level-3-version-1-core.pdf . The choice to require an asserted active catalytic role here is for the selected annotated catalyzed event. It is not proof that alternative or uncatalyzed physical pathways have zero rate.

## Exact examples of information lost by many-to-one mappings

- **Location collapse:** one proton in the cytosol and one proton only outside the cell have the same pooled count but different availability to the cytosolic LDH event. A separate source-defined lactate/proton cotransport action can change that availability; mere pooling cannot.
- **Quantity collapse:** presence booleans can suffice for one unit-coefficient firing, but cannot distinguish one available firing from two. Future behavior can differ even when the first answer agrees.
- **Role collapse:** consuming a catalyst and retaining it can give the same first enabledness decision while changing every successful successor and later enabling.
- **Shared-resource duplication:** two independent approvals against the same old resource snapshot can both be individually valid while jointly overspending a single resource. Composition needs a common state, reservations or ordered atomic rechecks.
- **Activity collapse:** distinct enzyme isoforms or modification states can have different kinetics. Our active-role aggregation deliberately excludes those kinetic distinctions; it is not a proved biological bisimulation.

A many-to-one abstraction is still exact for a declared observable if every source state in a collapsed class has the same relevant future response under the permitted actions. Without that condition, matching the abstract label is insufficient. Parent formal/transfer_contract.txt gives the explicit fiber criterion and finite-table lower bound.

## Coupled return without whole-state return

The sourced forward reactions share exact NAD/NADH/H+ entities:

    GAPDH: GA3P + Pi + NAD+ → 1,3BPG + NADH + H+
    LDH:   PYR + NADH + H+ → LACT + NAD+.

One GAPDH action followed by one LDH action restores the NAD+, NADH and H+ coordinates. The whole state instead changes by

    GA3P + Pi + PYR → 1,3BPG + LACT.

This is a concrete source-grounded cofactor coupling and a useful distinction between projected return and full-state return. It supplies neither a privileged 14-step cycle nor the stable-terminal/error-objective closure of TLD. The missing-regeneration control omits the second GAPDH action, so the missing resources are NADH/H+ regenerated by GAPDH; it does not remove the NAD+ recycling performed by the first LDH action.

## Meaning of the generic tie

The equally informed generic incidence interpreter and the biologically sourced translation have identical specified mechanisms. Their agreement is the expected test of fidelity. Biology may still be valuable as a source of good architectures or constraints. Showing that additional advantage requires a separate measurement of model discovery, sample efficiency, predictive accuracy, robustness or action selection against a competent alternative that is not already given the same correct mechanism. This test establishes a working semantic translation and detects concrete losses; it does not establish that biological origin makes an equivalent algorithm better.

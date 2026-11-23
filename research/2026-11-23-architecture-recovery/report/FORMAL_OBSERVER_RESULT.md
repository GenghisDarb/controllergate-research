# A sufficient joint observer for the selected reaction model

## Assumptions

There are ten metabolite coordinates. Six allowed reaction directions are three forward stoichiometric columns and their exact reverses. No additional reaction, influx, degradation or catalyst toggle is part of this closed transition system. Reaction enabling also depends on three known catalyst assertions which remain constant under these six reactions. State differences are compared within one fixed stoichiometric conservation class.

This statement concerns the explicitly supplied untimed token model. It does not assert that these six reactions form a complete description of a living cell.

## Construction

Let the three forward columns of the \(10\times3\) matrix \(B\) be the supplied GAPDH, LDH and lactate/proton-export stoichiometries. Let \(x\) be the ten-component metabolite state. Any legal sequence, including reversed reactions, changes \(x\) by

\[
\Delta x=B\xi,
\]

where \(\xi\) has three net reaction extents. Opposite steps can cancel; \(\xi\) describes net displacement rather than the full path or elapsed time.

Let \(C\) select `GA3P_c`, `PYR_c` and `LACT_e`, in that order. Their changes under the three forward directions are

\[
CB=\begin{pmatrix}
-1&0&0\\
0&-1&0\\
0&0&1
\end{pmatrix}.
\]

This diagonal matrix has determinant one and rank three.

## Result and proof

If the joint observation returns, \(C\Delta x=0\). Substitution gives \((CB)\xi=0\). Since \(CB\) is invertible, \(\xi=0\), hence \(\Delta x=B\xi=0\). Conversely, \(\Delta x=0\) immediately implies \(C\Delta x=0\).

Thus the joint three-readout return is equivalent to full metabolite return within a fixed stoichiometric class. Equivalently, C is injective on that affine class. Because the three catalyst assertions remain fixed under the specified reactions, their inclusion also gives full thirteen-component state return under the fixed-context assumption.

This is an application of standard linear observability/identifiability reasoning. It is not a new general theorem, a kinetic reconstruction, recovery of the reaction path, or a proof of the TORUS layer count.

## Why fewer selected views fail here

Deleting any selected readout leaves at least one independent net extent unobserved. The rank argument alone concerns the linear span; the executed finite-state experiment additionally verifies actual reachable ambiguity. In the 18-state reachable graph, the three two-readout choices admit 26, 26 and 22 ordered pairs of distinct states with equal observations. In the six-state graph, they admit 2, 4 and 4. The complete triple admits none in either graph.

These counts are state-pair identifiability counts, not recurrence rates or probabilities. The specified systems have curated reverse transitions; no kinetic weighting is imposed.

## Nonuniqueness and context limits

The independent review exhaustively evaluated all \(\binom{10}{3}=120\) coordinate triples. Seventy yield rank three on the same span. Therefore the chosen triple is a convenient sufficient observer, not uniquely necessary. \(B\) itself has rank three, leaving seven independent linear conservation relations among ten metabolite coordinates.

If catalytic assertions may change, metabolite readouts alone do not recover the full state or future enabling. The executed catalyst-off intervention preserves all ten metabolite coordinates and disables every reaction. It lies outside the specified six-reaction reachable class. Likewise, two states in different conservation classes can share the selected coordinates; the proof does not identify them.

## Evidence

- `../experiments/experiment_spec.json`: declared observations, seeds and scope.
- `../experiments/FROZEN_EXTENSION.json`: source hashes sealed before new execution.
- `../experiments/results.json`: complete reachable states, edges, fibers and interventions.
- `../experiments/observer_interlock.py`: role-inspired implementation and original computation.
- `../experiments/independent_observer_review.py`: independent parser, reachability and exact algebra.
- `../experiments/INDEPENDENT_OBSERVER_REVIEW.json`: matching state/edge sets, rank checks and all sufficient observer triples.

The independent review imports the role-shell implementation only as the system under test; its source semantics, case generation, graph traversal and algebra are separately implemented.

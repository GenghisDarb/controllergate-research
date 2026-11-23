# Review-triggered admissibility extension

## Finding and constructive repair

The reference-restoration candidate proposed in the parent experiment is

\[
F_0(x)=p+A(x-p),\qquad
A=I-\eta Q,\quad \eta=21/50,\quad
Q=aI+(1-a)L/4.
\]

Here \(L\) is the undirected cycle Laplacian, \(a\in[0,1]\), and the supplied reference \(p\) is fixed. This candidate is exact gradient descent on

\[
E'(x;p)=\tfrac12(x-p)^TQ(x-p)
=\tfrac a2\|x-p\|^2+\tfrac{1-a}{8}\sum_{\{i,j\}\in E}[(x_i-p_i)-(x_j-p_j)]^2.
\]

Its reference restoration does not by itself preserve a nonnegative state domain. At \(N=14\), \(a=1/2\), \(p=(1,0,\ldots,0)\), and \(x=0\), the exact output is

\[
F_0(x)=(63/200,-21/400,0,\ldots,0,-21/400).
\]

The central entry is 0.315 and the two neighboring entries are −0.0525. Thus a supplied nonnegative parent and a nonnegative input can produce negative coordinates. This is a counterexample to domain preservation by this new candidate, not a failure of the original archived operator, whose coefficients preserve nonnegativity.

The tested extension is projected gradient descent:

\[
F_C(x)=P_C[p+A(x-p)],\qquad C=\mathbb R^N_{\ge0},\quad p\in C.
\]

For this domain, \(P_C\) replaces each negative coordinate with zero. The correction addresses the demonstrated domain problem while retaining the conditional reference-restoration objective.

## General guarantee under explicit assumptions

The following is an application of established quadratic optimization and Euclidean projection facts, not a proposed new general mathematical theorem. It holds for every fixed nonnegative parent, all feasible inputs, every cycle size \(N\ge3\), and \(a\in[0,1]\). The finite suite checks the implementation against these claims.

### Reference fixed point and contraction

The cycle Laplacian satisfies \(0\preceq L\preceq4I\), so

\[
aI\preceq Q\preceq I,\qquad
0.58I\preceq A\preceq(1-0.42a)I.
\]

Let \(q=1-0.42a\). Orthogonal projection onto a closed convex set is nonexpansive, and \(F_C(p)=P_C(p)=p\). Consequently,

\[
\|F_C(x)-F_C(y)\|_2\le q\|x-y\|_2,
\qquad
\|F_C(x)-p\|_2\le q\|x-p\|_2.
\]

For \(a>0\), this gives a strict contraction and a unique fixed point \(p\). The bound is independent of cycle size. At \(a=0\), the guarantee is nonexpansiveness; exact return to \(p\) from every starting state does not follow. Projection can also remove the mean-conservation property of the unprojected \(a=0\) iteration.

The tested contraction factors were:

| a | q |
|---:|---:|
| 0 | 1 |
| 0.2 | 0.916 |
| 0.5 | 0.79 |
| 1 | 0.58 |

### Energy descent

Write \(g=Q(x-p)\) and \(s=F_C(x)-x\), with \(x\in C\). The defining projection inequality, applied with feasible comparison point \(x\), yields

\[
g^Ts\le-\|s\|^2/\eta.
\]

Because the objective is quadratic and \(Q\preceq I\),

\[
\begin{aligned}
E'(x+s;p)-E'(x;p)
&=g^Ts+\tfrac12s^TQs\\
&\le-(1/\eta-1/2)\|s\|^2\\
&=-\tfrac{79}{42}\|s\|^2.
\end{aligned}
\]

This is a feasible-input, fixed-reference, fixed-parameter energy guarantee. It does not supply a common energy function when a feedback system changes its reference or parameter between steps.

## Frozen execution and results

`FROZEN_EXTENSION.json` seals the experiment specification, implementation, and archived source snapshot before this extension was executed. This extension followed an analytical review of the proposed repair; it does not replace or modify the parent experiment's frozen specification or outcomes.

The suite used \(N\in\{12,13,14,15,28\}\), \(a\in\{0,1/5,1/2,1\}\), and 20 structured or seeded rational pairs for every combination: **400 pairs / 800 single inputs**. Five pairs per combination deliberately target domain boundaries, sparse parents, uniform modes, alternating profiles, and zero parents. Fifteen use frozen-seed rational values, including additional zeros. This is a diagnostic suite, not a probability sample of physical states.

Results:

- All **2,800 exact rational assertions** passed: nonnegativity, reference fixed point, both reference-distance bounds, pairwise contraction bound, and both energy descent bounds.
- All **400 floating-point archived-source parity checks** passed. The maximum absolute difference from the independent rational oracle was \(4.440892098500626\times10^{-16}\).
- The unprojected candidate had a negative coordinate in at least one member of **231 designed pairs**. Projection was nontrivial in the same 231 pairs. These counts describe this deliberately boundary-rich suite and are not estimates of failure prevalence.
- The explicit \(N=14,a=1/2\) witness produced the exact two negative neighbors \(-21/400\) required by the predeclared specification.
- There were no failed checks.

The exact input values and rational output witnesses are retained in `RESULTS.json`; the compact receipt is `SUMMARY.json`. Python version was 3.12.14.

## Scientific scope and limits

1. This repairs a specific mathematical domain defect under the declared reference-restoration objective. It does not predict the parent reference, explain why that reference exists, or prefer fourteen layers over the other tested sizes.
2. Coordinate nonnegativity is weaker than biochemical admissibility. This projection does not enforce reaction stoichiometry, catalyst conditions, conservation totals, allowed transitions, or empirical rates. It must not be described as a Reactome-isomorphic biological simulator.
3. The projected map is generally nonlinear. The parent experiment's global linear Fourier transfer formula applies to its unprojected kernels, not globally to this projected extension. Where no coordinate crosses the boundary, the corresponding local branch coincides with the unprojected map.
4. Projection can merge distinct feasible inputs, so the unprojected kernel's invertibility does not transfer. For example, take the same \(N=14,a=1/2,p=e_0\), but \(x=0.01\mathbf1\). Its preprojection neighbor outputs are −0.0446. Let \(\delta=0.001A^{-1}e_1\). Since \(\|A^{-1}\|_2\le1/0.58\), every coordinate of \(x+\delta\) stays positive. Before projection, the two outputs differ only in neighbor 1 by 0.001; that coordinate stays negative and is clipped in both. Therefore \(F_C(x+\delta)=F_C(x)\) although \(\delta\ne0\). This analytic scope witness is additional to the frozen numerical suite, and is not counted among its tests.
5. This remains an abstract deterministic iteration. The energy is an explicit optimization objective, not an identified physical energy or evidence of a fundamental arrow of time. Mathematical loss of information under clipping does not identify physical thermodynamic irreversibility.
6. A different closed convex admissible set containing \(p\) has the same nonexpansiveness argument, but no alternative domain was implemented or validated here.

## Reproduction

The source snapshot is read-only input. The script verifies every frozen hash, extracts only `LadderKernel._relax` through Python's AST, and does not execute the rest of the archived module. It refuses to overwrite its original results. To reproduce in a fresh directory:

```sh
python run_admissibility.py --output-dir /absolute/path/to/a/new/admissibility_reproduction
```

The frozen input record's SHA-256 is `a2d128c7141908c3979ebbfded914d827cb10d6d67056a6aa47b11ddff95c586`.

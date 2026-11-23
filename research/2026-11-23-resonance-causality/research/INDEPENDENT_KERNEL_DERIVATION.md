# Independent derivation for the recovered ladder relaxation

Prepared 23 November 2026 before inspecting the parent's new experimental outcomes. Source: the recovered `LadderKernel._relax` in `current_fieldstudio/python/torusbrot/kernels.py`, physical lines 181–190. This is a fresh derivation of the specified operator, not a new general theorem or a claim about every TORUS model.

## 1. Exact update

For a cycle of N >= 3 coordinates, let L be the ordinary unweighted graph Laplacian, p the fixed parent vector, and a the supplied anchoring parameter in [0,1]. The archived code uses neighborhood

\[
s_i=(x_{i-1}+2x_i+x_{i+1})/4=x_i-(Lx)_i/4
\]

and update

\[
x_i^+=0.58x_i+0.42[(1-a)s_i+ap_i].
\]

Therefore, exactly over real arithmetic,

\[
x^+=Ax+0.42ap,
\qquad
A=I-0.42Q,
\qquad Q=aI+\frac{1-a}{4}L.
\]

The component weights are diagonal 0.79-0.21a and neighbor weights 0.105(1-a). Their sum is 1-0.42a. The parent term restores the affine anchoring contribution.

## 2. Energy interpretation and descent

Define

\[
E_a(x;p)=\frac a2\|x-p\|^2+
\frac{1-a}{8}\sum_{\{i,j\}\in E}(x_i-x_j)^2.
\]

Each undirected cycle edge appears once. Since x^T L x equals that edge sum,

\[
\nabla E_a(x;p)=Qx-ap=:g.
\]

The source update is gradient descent with step eta=0.42. For this quadratic,

\[
E_a(x-\eta g;p)-E_a(x;p)
=-\eta\|g\|^2+\frac{\eta^2}{2}g^TQg.
\]

Cycle Laplacian eigenvalues lie in [0,4], so Q has eigenvalues in [a,1]. Consequently,

\[
E_a(x^+;p)-E_a(x;p)\le
-0.42(1-0.42/2)\|g\|^2
=-0.3318\|g\|^2.
\]

Energy therefore strictly decreases unless the gradient vanishes. This requires fixed p and fixed a. If a controller changes p or a, the function being minimized changes; the same inequality cannot be applied across that change without accounting for it.

At a>0, Q is positive definite and the unique minimizer is x*=Q^{-1}ap. At a=0, every constant vector minimizes the smoothness term. The algorithm preserves the mean and approaches the constant vector determined by that initial mean. Thus uniqueness at a=0 is conditional on the conserved mean, not global uniqueness.

## 3. A compatibility floor, not automatic perfect satisfaction

For 0<a<1, E_a=0 requires x=p and Lx=0. On a connected cycle this is possible only when p is constant. A nonconstant parent therefore creates an unavoidable positive minimum in this particular weighted objective.

For an orthonormal Fourier basis, put

\[
\mu_k=\sin^2(\pi k/N),\qquad q_k=a+(1-a)\mu_k.
\]

Then

\[
x_k^*=\frac{a}{q_k}p_k,
\qquad
x_k^*-p_k=-\frac{(1-a)\mu_k}{q_k}p_k,
\]

and

\[
E_a(x^*;p)=
\sum_k\frac{a(1-a)\mu_k}{2[a+(1-a)\mu_k]}|p_k|^2.
\]

This is a concrete explanation for a stable coupled relaxation failing a strict return-to-parent threshold. The final state can be the best joint compromise while retaining nonzero parent error. Whether that compromise is called structural resonance or closure is a project interpretation; the two objective values must still be reported.

## 4. Modes and size dependence

The update eigenvalues are

\[
\lambda_k=1-0.42[a+(1-a)\sin^2(\pi k/N)].
\]

For a in [0,1], every eigenvalue lies in [0.58,1]. At a>0 the upper endpoint is 1-0.42a<1. All error modes decay without intrinsic sign-alternating or complex-eigenvalue oscillation. A generic observed coordinate can still combine several decays and need not be monotone; that does not add an oscillatory eigenmode.

For a>0, the worst-case full-space contraction factor is 1-0.42a, independent of N, because the uniform mode exists for every N. For a=0, on the mean-zero subspace, the largest eigenvalue is 1-0.42 sin^2(pi/N). Increasing N slows this diffusion-like mixing smoothly. These formulas contain no unique special value at fourteen.

A dimension comparison must still hold graph rules, anchoring, normalization, forcing and initial-condition treatment fixed. Finite thresholds and changed parent spectra can produce size-specific measured outcomes without demonstrating a universal preferred size.

## 5. Forced response

For a parent forcing mode p_k(t)=P exp(i Omega t), take a steady response x_k(t)=X exp(i Omega t). Substitution gives

\[
\frac XP=\frac{0.42a}{e^{i\Omega}-\lambda_k}.
\]

The squared denominator is 1+lambda_k^2-2lambda_k cos(Omega). For positive lambda_k and Omega in [0,pi], it increases with Omega. The gain is therefore largest at zero frequency. The recovered operator has a low-pass forced response; it does not generate a nonzero-frequency resonant peak in this forcing convention.

At a=0 the parent is disconnected, so its transfer is zero. The expression at the unanchored uniform mode and zero frequency must not be evaluated as an ordinary 0/0 gain. An additive external forcing would be a different input convention; its unanchored uniform mode would integrate a constant input instead of reaching a finite forced steady state.

This diagnosis does not rule out oscillatory resonance in later TORUS operators with inertia, phase state, delay or nonlinear feedback. It identifies what this particular implemented map does.

## 6. Graph propagation and ancestry

The local stencil gives (A^t)_{ij}=0 whenever graph distance(i,j)>t. An impulse can therefore affect only coordinates reachable by at most t update steps. For a parent intervention the first state effect occurs on the next update, so time indexing matters. This is an abstract graph propagation cone; no physical distance, seconds or speed of light is identified.

Removing a graph edge must remove its two off-diagonal Laplacian entries and lower the corresponding diagonal degrees. Deleting off-diagonal weights while retaining the old diagonal changes more than connectivity and can introduce artificial leakage. An undirected path produced by cutting cycle edges still has Laplacian spectrum in [0,4], so the energy argument remains applicable with the revised edge set.

All eigenvalues of A are at least 0.58, so A is invertible. With the exact full state and known parent/input history, the previous state is uniquely recoverable by A^{-1}. Repeated inversion amplifies errors. Partial observation can also erase state distinctions. These facts distinguish numerical/observational irreversibility from an irreversible microscopic law. Energy descent alone proves neither a physical arrow of time nor a unique cosmic causal origin.

## 7. Connection to an embedded observer

An observer that only reads H(x) is a projection. An observer that uses memory to choose an action needs an extended state, for example (x,m,e), where m is observer/controller memory and e is relevant environment. A closed update law may then specify observation, memory update, action selection and the joint successor. Omitting m or e can make the apparent observed dynamics history-dependent even when the full model is Markovian.

The current ladder update contains no explicit human observer, sensory transduction, report generation or quantum measurement channel. Its exact local dependency structure can support a future explicit observer model. It does not identify the cause of subjective experience or establish that resonance creates all reality.

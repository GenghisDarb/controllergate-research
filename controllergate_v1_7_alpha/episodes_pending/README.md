# Pending Real Episode Bundles

This directory holds candidate ControllerGate v1.7-alpha real maintenance episodes before normalization.

Current status:

- `episode_001` through `episode_010` remain reusable collection templates.
- Ten completed evidence bundles have been collected and normalized into `../traces/normalized/episodes.jsonl`.
- The completed bundles are iota, pi, kappa, lambda, mu, nu, xi, omicron, rho, and psi.
- Audit status is `REVIEW_REQUIRED`; no v1.7-alpha scoring has been run.
- External TORUS-Theory candidate bundles have been started for `external_torus_pr_015_notebook_force_clean` and `external_torus_pr_016_paircorr_rebuild`.
- These external bundles now include captured PR diffs and fresh local rerun evidence.
- Additional TORUS-Theory candidate bundles have been started for `external_torus_pr_019_paircorr_kernelspec` and `external_torus_pr_020_paircorr_hann_fallback`.
- PR #19 and PR #20 local reruns both failed on the NumPy version assertion; PR #20 was closed unmerged.
- Reviewed pending TORUS episode folders have been created:
  - `episode_torus_pr15_invalid_notebook_json`
  - `episode_torus_pr16_torus_positive_pass`
  - `episode_torus_pr19_numpy_assertion_failure`
  - `episode_torus_pr20_numpy_assertion_closed_unmerged`
- PR #32/#33 target report exists at `../reports/torus_pr32_pr33_target_report.md`.
- Sampled historical GitHub Actions logs still returned HTTP 410, and original agent/tool traces remain unavailable.
- Do not score v1.7-alpha from these pending bundles.

Use `controllergate_v1_7_alpha/docs/episode_collection_instructions.md` to fill each bundle.

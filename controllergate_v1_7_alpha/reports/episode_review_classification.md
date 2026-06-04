# ControllerGate v1.7-alpha Episode Review Classification

Status: normalized and reviewed for scoring eligibility. Limited pilot eligibility is approved; full scoring remains blocked.

## Result

The normalized ledger contains 20 evidence episodes. Ten are external real repo episodes, and the pilot eligibility review approves those 10 for a limited exploratory v1.7-alpha real repo pilot. Full scoring remains blocked.

| Classification | Count | Scoring use |
| --- | ---: | --- |
| correction_review_episode | 2 | Not allowed for real repo scoring |
| controlled_benchmark_evidence | 8 | Not allowed for real repo scoring |
| external_real_repo_episode | 10 | Eligible for limited exploratory pilot only |
| excluded_from_scoring | 0 | Not allowed |

Scoring eligibility count for the v1.7-alpha limited real repo pilot: `10`.

Scoring mode: `limited_pilot_only`.

Full scoring allowed: `false`.

ControllerGate scoring: `NOT RUN`.

Reason: the ten TORUS-Theory external real repo episodes are diverse enough for a limited exploratory pilot, but several still lack historical GitHub Actions log text or original agent/tool transcript custody. Controlled benchmark and correction-review episodes remain excluded.

## Episode Classifications

| Source episode | Category | Allowed use | Reason |
| --- | --- | --- | --- |
| episode_iota_misreport | correction_review_episode | report-integrity training/evaluation only | Critic-correction event, not external repo maintenance. |
| episode_pi_misreport | correction_review_episode | report-integrity training/evaluation only | Critic-correction event, not external repo maintenance. |
| episode_kappa_verified_recovery | controlled_benchmark_evidence | scaffold validation, provenance verification, benchmark-history context only | Verified v1.6 benchmark evidence, not external real repo maintenance. |
| episode_lambda_noisy_drift | controlled_benchmark_evidence | scaffold validation, provenance verification, benchmark-history context only | Verified v1.6 benchmark evidence, not external real repo maintenance. |
| episode_mu_discovery_vs_predefinition | controlled_benchmark_evidence | scaffold validation, provenance verification, benchmark-history context only | Verified v1.6 benchmark evidence, not external real repo maintenance. |
| episode_nu_sparse_recurrence | controlled_benchmark_evidence | scaffold validation, provenance verification, benchmark-history context only | Verified v1.6 benchmark evidence, not external real repo maintenance. |
| episode_xi_temporal_inversion | controlled_benchmark_evidence | scaffold validation, provenance verification, benchmark-history context only | Verified v1.6 benchmark evidence, not external real repo maintenance. |
| episode_omicron_scripted_spoofing | controlled_benchmark_evidence | scaffold validation, provenance verification, benchmark-history context only | Verified v1.6 benchmark evidence, not external real repo maintenance. |
| episode_rho_pi_recovery_repair | controlled_benchmark_evidence | scaffold validation, provenance verification, benchmark-history context only | Verified v1.6 benchmark evidence, not external real repo maintenance. |
| episode_psi_custody_closure | controlled_benchmark_evidence | scaffold validation, provenance verification, benchmark-history context only | Verified v1.6 benchmark evidence, not external real repo maintenance. |
| episode_torus_pr15_invalid_notebook_json | external_real_repo_episode | external real repo ingestion review only | Fresh local rerun reproduced invalid notebook JSON; historical GitHub Actions log text and original agent trace remain unavailable. |
| episode_torus_pr16_torus_positive_pass | external_real_repo_episode | external real repo ingestion review only | Fresh local rerun passed and found `TORUS-POSITIVE`; historical GitHub Actions log text and original agent trace remain unavailable. |
| episode_torus_pr19_numpy_assertion_failure | external_real_repo_episode | external real repo ingestion review only | Fresh local rerun reproduced the NumPy `<2.3` assertion failure; historical GitHub Actions log text and original agent trace remain unavailable. |
| episode_torus_pr20_numpy_assertion_closed_unmerged | external_real_repo_episode | external real repo ingestion review only | Fresh local rerun reproduced the NumPy `<2.3` assertion failure in the current environment; PR #20 was closed unmerged. |
| episode_torus_pr32_notebook_kernel_failure | external_real_repo_episode | external real repo ingestion review only | Fresh bounded local rerun reproduced missing notebook kernel metadata; historical GitHub Actions log text and original agent trace remain unavailable. |
| episode_torus_pr32_validation_workflow_failure | external_real_repo_episode | external real repo ingestion review only | Workflow/job failure metadata is present, but exact historical logs and bounded local rerun output are unavailable. |
| episode_torus_pr33_notebook_selector_repair | external_real_repo_episode | external real repo ingestion review only | Fresh bounded selector rerun passed, but the full notebook execution loop and historical GitHub Actions log text remain unavailable. |
| episode_torus_pr33_readme_guard_warning_only | external_real_repo_episode | external real repo ingestion review only | Fresh bounded README guard rerun exited 0 while printing warnings; it is not the same as the historical shell `check-readmes` job. |
| episode_torus_pr17_latex_workflow_repair | external_real_repo_episode | external real repo ingestion review only | LaTeX workflow repair evidence is present, but historical logs are unavailable and local evidence is a bounded permission-failed TeX check. |
| episode_torus_pr34_readme_guard_failure | external_real_repo_episode | external real repo ingestion review only | Fresh bounded README guard rerun failed and CI metadata shows `full-dependency-install` failure, but historical logs and full job replay remain unavailable. |

## Scoring Boundary

This review layer protects the distinction between normalized evidence, limited pilot eligibility, and full scoring approval.

Current claim boundary:

- v1.7-alpha has 20 normalized evidence episodes.
- v1.7-alpha has 10 external real repo episodes.
- v1.7-alpha has 10 external real repo episodes eligible for a limited exploratory pilot.
- v1.7-alpha full real repo scoring remains blocked.
- ControllerGate scoring has not been run.

Required next step: request explicit approval before running the limited v1.7-alpha pilot. The pilot must include failed and ambiguous episodes and must not make self-maintaining or broad external generalization claims.

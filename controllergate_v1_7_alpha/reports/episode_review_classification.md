# ControllerGate v1.7-alpha Episode Review Classification

Status: normalized and reviewed for scoring eligibility. Scoring remains blocked.

## Result

The normalized ledger contains 10 evidence episodes, but none are eligible for v1.7-alpha real repo pilot scoring.

| Classification | Count | Scoring use |
| --- | ---: | --- |
| correction_review_episode | 2 | Not allowed for real repo scoring |
| controlled_benchmark_evidence | 8 | Not allowed for real repo scoring |
| external_real_repo_episode | 0 | Required for real repo scoring |
| excluded_from_scoring | 0 | Not allowed |

Scoring eligibility count for the v1.7-alpha real repo pilot: `0`.

Scoring allowed: `false`.

Reason: there are zero `external_real_repo_episode` entries.

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

## Scoring Boundary

This review layer protects the distinction between normalized evidence and scoring-eligible real repo evidence.

Current claim boundary:

- v1.7-alpha has 10 normalized evidence episodes.
- v1.7-alpha has 0 external real repo episodes.
- v1.7-alpha real repo scoring remains blocked.

Required next evidence: collect and normalize external real repository maintenance episodes with real CI failures, patch traces, agent/tool traces, generated artifact manifests, and visible or downstream outcomes.

# ControllerGate v1.7-alpha Pilot Eligibility Review

Status: eligible for limited exploratory pilot only. Limited pilot scoring has since been run; full scoring remains blocked.

## Decision

The v1.7-alpha ledger has 20 normalized episodes and 10 normalized `external_real_repo_episode` entries. The external set is diverse enough to permit a limited exploratory real-repo pilot, but it is not clean enough for full scoring or broad claims.

Decision: `limited_pilot_only`

Eligible external pilot episodes: `10`

Full scoring allowed: `false`

Limited pilot scoring: `RUN`

Full scoring run: `false`

Reason: the TORUS-Theory episodes include failures, pass evidence, repairs, dependency/config drift, closed-unmerged context, notebook/kernel failures, workflow metadata, and guardrail behavior. Several episodes still lack historical GitHub Actions log text or original agent/tool transcripts, so the approved scoring mode remains limited and exploratory with all caveats preserved.

## Episode List

| Episode | Source repo | PR | Outcome type | Verified result | Evidence status |
| --- | --- | ---: | --- | --- | --- |
| episode_011 | TORUS-Theory | 15 | malformed_artifact_failure | failed | partial; fresh local rerun evidence |
| episode_012 | TORUS-Theory | 16 | successful_rerun_positive_signal | passed | partial; fresh local rerun evidence |
| episode_013 | TORUS-Theory | 19 | dependency_version_assertion_failure | failed | partial; fresh local rerun evidence |
| episode_014 | TORUS-Theory | 20 | dependency_version_assertion_failure_closed_unmerged | failed | partial; fresh local rerun evidence |
| episode_015 | TORUS-Theory | 32 | notebook_kernel_failure | failed | partial; pending evidence bundle reviewed and normalized |
| episode_016 | TORUS-Theory | 32 | validation_workflow_failure | review_required | partial; pending evidence bundle reviewed and normalized |
| episode_017 | TORUS-Theory | 33 | notebook_selector_repair | passed | partial; pending evidence bundle reviewed and normalized |
| episode_018 | TORUS-Theory | 33 | readme_guard_warning_only | warning_only | partial; pending evidence bundle reviewed and normalized |
| episode_019 | TORUS-Theory | 17 | latex_workflow_repair | review_required | partial; pending evidence bundle reviewed and normalized |
| episode_020 | TORUS-Theory | 34 | readme_guard_failure | failed | partial; pending evidence bundle reviewed and normalized |

## Diversity Check

| Required evidence type | Covered | Episode(s) |
| --- | --- | --- |
| malformed artifact failure | yes | episode_011 |
| successful rerun / positive signal | yes | episode_012 |
| dependency or version assertion failure | yes | episode_013, episode_014 |
| closed unmerged episode | yes | episode_014 |
| notebook/kernel failure | yes | episode_015 |
| workflow/validation failure | yes | episode_016 |
| repair episode | yes | episode_017, episode_019 |
| warning-only or guardrail episode | yes | episode_018 |
| LaTeX/workflow repair | yes | episode_019 |
| README/guard failure | yes | episode_020 |

## Evidence Checks

Decision-time evidence and outcome-only evidence are separated in the normalized ledger. GitHub Actions rerun/log unavailability is documented where applicable, including HTTP 410 historical log failures and rerun limits on same-era runs. Local rerun commands and outputs are preserved where available.

Ambiguous or incomplete episodes must remain in the pilot report:

| Episode | Reason |
| --- | --- |
| episode_016 | Workflow failure metadata exists, but exact historical logs and local rerun output are unavailable. |
| episode_018 | Local guard behavior is warning-only and differs from the historical shell `check-readmes` job. |
| episode_019 | Full LaTeX workflow replay is unavailable; local bounded check failed due local environment permission. |

## Pilot Constraints

- Only `external_real_repo_episode` entries may be used.
- Controlled benchmark evidence remains excluded from real repo scoring.
- Correction-review episodes remain excluded from real repo scoring.
- The pilot must be reported as limited and exploratory.
- No self-maintaining software claim is allowed.
- No broad external generalization claim is allowed.
- Failed and ambiguous episodes must remain included in the report.
- Full scoring requires separate explicit approval.

## Claim Boundary

Allowed claim: ControllerGate v1.7-alpha is eligible for a limited exploratory real-repo pilot using 10 normalized TORUS-Theory external episodes.

Disallowed claim: ControllerGate works on real repos, self-maintains software, or generalizes broadly across external repositories.

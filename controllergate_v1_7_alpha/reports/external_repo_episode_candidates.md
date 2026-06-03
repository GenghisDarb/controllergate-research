# External Repo Episode Candidates

Status: discovery started. No external episode has been normalized.

## Source

Primary candidate source: `GenghisDarb/TORUS-Theory`

URL: `https://github.com/GenghisDarb/TORUS-Theory`

TORUS-Theory has real maintenance PRs with notebook repair, CI workflow repair, lint/test repair, and GitHub Actions metadata. That makes it a plausible first source for v1.7-alpha external real repo episodes.

## Best Initial Candidates

| Rank | Candidate | Why it matters | Current blocker |
| ---: | --- | --- | --- |
| 1 | PR #16, PairCorr notebook rebuild | Merged one-file repair replacing a corrupt notebook with nbformat-v4 JSON; successor workflow metadata shows PairCorr success; PR diff captured locally. | Full historical job logs returned HTTP 410. |
| 2 | PR #15, notebook force-clean | Merged cleanup that superseded prior notebook repair attempts; PairCorr failure metadata and PR diff captured locally. | Needs explicit failure/outcome linkage to #16 and unavailable-log note. |
| 3 | PR #17, LaTeX workflow hardening | Merged CI workflow repair with concrete workflow changes. | Need actual book workflow logs or archived output. |
| 4 | PR #19/#20, PairCorr kernelspec and hann fallback | Small notebook repair sequence with merged and unmerged attempts. | Need closure rationale and CI log availability review. |
| 5 | PR #32/#33/#34, July CI repair cluster | Real CI/lint/test repair cluster with mixed failure/success workflow metadata. | Large diffs need bounded extraction; failed job logs returned HTTP 410. |

## Gate

The ControllerGate v1.7-alpha harness is ready, but TORUS-Theory candidates are still evidence candidates only.

Current scoring boundary:

- 10 normalized ControllerGate evidence episodes exist.
- 0 normalized external real repo episodes exist.
- 0 episodes are scoring-eligible for the v1.7-alpha real repo pilot.
- Scoring remains blocked.

## Next Work

Continue completing the pending external episode bundles for PR #16 and PR #15 as a linked failure/repair pair.

Each bundle should preserve unavailable historical logs honestly instead of filling them with inferred text.

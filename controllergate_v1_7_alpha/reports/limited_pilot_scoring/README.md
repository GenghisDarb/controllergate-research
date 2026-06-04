# v1.7-alpha Limited Pilot Summary

ControllerGate v1.7-alpha limited pilot scoring was run on 10 normalized TORUS-Theory external real repo episodes. This is exploratory pilot evidence only, not proof of self-maintaining software.

## Result

- Status: `COMPLETED_WITH_REVIEW_REQUIRED_CAVEATS`
- Scoring mode: `limited_pilot_only`
- Eligible external episodes: `10`
- Passed: `2`
- Failed: `5`
- Warning-only: `1`
- Review-required: `2`
- Full scoring allowed: `false`

## Interpretation

The pilot proves the v1.7-alpha evidence and scoring harness can run on real external repo evidence while preserving exclusions, failed episodes, ambiguous episodes, and non-claim boundaries.

It does not prove self-maintaining software, full real-repo performance, or real-repo memory lift. Memory baselines were unavailable in this TORUS evidence set.

## Next Step

Start v1.7-beta second-repo evidence collection, preferably TatMapper or another non-TORUS repository with real CI/build/test failures.

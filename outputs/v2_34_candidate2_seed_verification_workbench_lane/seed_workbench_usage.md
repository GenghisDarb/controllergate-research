# v2.34 seed verification workbench

Place one reviewed seed at `inputs/external_candidate_seed_draft_v2_34.json`, then run:

```bash
python scripts/verify_external_candidate_seed.py --seed inputs/external_candidate_seed_draft_v2_34.json --output-dir outputs/v2_34_candidate2_seed_verification_workbench_lane/seed_verification --allow-merge
```

The verifier checks only the exact buggy commit. It does not inspect fixed or later commits, issue patches, pull request patches, hidden labels, or generated tests.

# v2.1b Curated External Candidate Sourcing Result

v2.1b improves candidate sourcing quality.

- Candidate pool produced: true
- Candidates evaluated: 10
- Ready candidates count: 0
- Manual-review candidates count: 5
- Rejected/blocked candidates count: 5
- Best source families: small public Python repo with simple tests, small public Python repo with simple tests, small public Python repo with simple tests
- v2.2 handoff recommendation: `manual_candidate_triage_before_v2_2`
- Candidate readiness is not repair success.
- Ready candidates only authorize future v2.2 replay attempts.
- Blocked acquisition is not negative capability evidence.
- External memory lift remains undemonstrated.
- Self-maintaining software remains undemonstrated.
- Full scoring remains disallowed.

## Ranked Candidates

- `v2_1b_candidate_006_sampleproject`: readiness 95, source quality 50, classification `needs_manual_review`
- `v2_1b_candidate_007_packaging`: readiness 95, source quality 50, classification `needs_manual_review`
- `v2_1b_candidate_008_requests`: readiness 95, source quality 50, classification `needs_manual_review`
- `v2_1b_candidate_009_itsdangerous`: readiness 95, source quality 50, classification `needs_manual_review`
- `v2_1b_candidate_010_markupsafe`: readiness 95, source quality 50, classification `needs_manual_review`
- `v2_1b_candidate_003_quixbugs_style`: readiness 0, source quality 45, classification `blocked_candidate_source_unavailable`
- `v2_1b_candidate_001_bugsinpy_style`: readiness 0, source quality 35, classification `blocked_candidate_source_unavailable`
- `v2_1b_candidate_002_swe_bench_style`: readiness 0, source quality 35, classification `blocked_candidate_source_unavailable`
- `v2_1b_candidate_004_defects4j_style`: readiness 0, source quality 35, classification `blocked_candidate_source_unavailable`
- `v2_1b_candidate_005_archived_dependency_drift`: readiness 0, source quality 10, classification `blocked_candidate_source_unavailable`

## Source Gap Analysis

Curated source quality improved, but v2.1b still did not acquire a ready v2.2 candidate. Curated benchmark descriptors are blocked because local datasets/checkouts are unavailable. Local public Python repos have clone, license, and command feasibility, but lack known deterministic failing issue branches. The next acquisition step should supply local benchmark datasets or issue-branch descriptors with exact failing commands.

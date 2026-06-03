# ControllerGate v1.6-psi Custody Verification

## Package Structure

Benchmark package ZIP:

`C:\Users\thisb\Downloads\ControllerGate_v1_6_psi_SeparateFixtureArtifactCustodyTrial_Package.zip`

Contained files:

```text
ControllerGate_v1_6_psi_SeparateFixtureArtifactCustodyTrial.ipynb
README.md
SHA256SUMS.txt
audit/
benchmarks/
benchmarks/__init__.py
benchmarks/analyze_agent_maintenance_trial.py
benchmarks/run_agent_maintenance_trial.py
locks/
locks/v1_6_psi.json
outputs/
outputs/decision_report.json
outputs/summary.json
```

External fixture artifact ZIP:

`C:\Users\thisb\Downloads\ControllerGate_v1_6_psi_ExternalFixtureArtifact.zip`

Contained files:

```text
AUTHORSHIP.md
SHA256SUMS.txt
external_red_team_fixtures.jsonl
fixture_manifest.json
```

## Lockfile Controls

`locks/v1_6_psi.json` records:

```json
{
  "disable_internal_generator_for_scoring": true,
  "expected_fixture_artifact_sha256": "1231ed48b78421f2850f1bf776d6ff9fdce12a94429ef8a83b4b6fccdb7f9c0d",
  "expected_fixture_count": 768,
  "expected_fixture_file_sha256": "1a8ce3498921743537a1e8d8ecff178d5b33d80d90830c8583353ed6c9e7ba6f",
  "external_fixture_artifact_default": "../ControllerGate_v1_6_psi_ExternalFixtureArtifact.zip",
  "reject_missing_fixture_artifact": true,
  "reject_tampered_fixture_artifact": true,
  "require_separate_fixture_artifact": true,
  "run_id": "v1_6_psi",
  "score_verified_external_fixture_only": true,
  "version": "v1.6-psi"
}
```

`fixture_manifest.json` records:

```json
{
  "artifact_name": "ControllerGate_v1_6_psi_ExternalFixtureArtifact",
  "authorship": "independent external fixture artifact simulated; generated outside benchmark code package",
  "benchmark_code_bundling_allowed": false,
  "custody_mode": "separate_fixture_artifact_required_at_runtime",
  "fixture_count": 768,
  "fixture_file": "external_red_team_fixtures.jsonl",
  "fixture_sha256": "1a8ce3498921743537a1e8d8ecff178d5b33d80d90830c8583353ed6c9e7ba6f",
  "scoring_requires_verified_artifact": true
}
```

## Packaged Result

Packaged `outputs/summary.json`:

```json
{
  "passed": 51,
  "total": 51
}
```

Packaged `outputs/decision_report.json` includes:

| Field | Value |
| --- | --- |
| Version | `v1.6-psi` |
| Status | `Diagnostic prototype, not proof of self-maintaining software.` |
| Passed | `51` |
| Total | `51` |
| Selected policy | `balanced` |
| Fixture artifact count | `768` |
| External artifact discovered hidden pass | `0.781` |
| External artifact predefined hidden pass | `0.024` |
| External artifact discovered-vs-predefined gap | `0.757` |
| External artifact no-memory hidden pass | `0.029` |
| External artifact poisoned hidden pass | `0.037` |
| Memory false-positive transfer | `0.176` |
| Productive recommendation precision | `0.928` |
| Avoidance transfer precision | `0.821` |
| Provenance failure score attempts blocked | `2` |
| Missing fixture rejected | `true` |
| Tampered fixture artifact rejected | `true` |
| Internal generator disabled for scoring | `true` |
| Verified external artifact scoring fraction | `1.0` |

## Fresh Rerun Verification

Fresh rerun command shape:

```bash
python -m benchmarks.run_agent_maintenance_trial --config locks/v1_6_psi.json --fixture-artifact ..\ControllerGate_v1_6_psi_ExternalFixtureArtifact.zip --out rerun_outputs
python -m benchmarks.analyze_agent_maintenance_trial --outputs rerun_outputs
```

Fresh rerun output:

```text
benchmark complete: 51 / 51 passed
separate external fixture artifact verified
verified fixture artifact only scored
decision report: 51 / 51 passed
all criteria passed
```

Fresh rerun semantic check:

| Check | Result |
| --- | --- |
| Packaged passed / total | `51 / 51` |
| Rerun passed / total | `51 / 51` |
| Packaged criterion count | `51` |
| Rerun criterion count | `51` |
| Rerun failed criteria | `0` |
| Artifact SHA verified in rerun | `true` |
| Manifest SHA verified in rerun | `true` |
| Payload SHA verified in rerun | `true` |
| Fixture count in rerun | `768` |

## SHA Verification

Benchmark package manifest verification:

```text
True ControllerGate_v1_6_psi_SeparateFixtureArtifactCustodyTrial.ipynb
True README.md
True benchmarks/__init__.py
True benchmarks/analyze_agent_maintenance_trial.py
True benchmarks/run_agent_maintenance_trial.py
True locks/v1_6_psi.json
True outputs/decision_report.json
True outputs/summary.json
```

External fixture artifact manifest verification:

```text
True AUTHORSHIP.md
True external_red_team_fixtures.jsonl
True fixture_manifest.json
```

## Custody Conclusion

v1.6-psi satisfies the separate fixture artifact custody closure condition for the controlled diagnostic benchmark chain.

This evidence supports freezing v1.6 at psi. It does not provide real repository / real agent trace episodes for v1.7-alpha scoring.

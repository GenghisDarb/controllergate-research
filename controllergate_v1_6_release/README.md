# ControllerGate v1.6 Release Evidence Bundle

Status: v1.6 is frozen at psi.

This bundle records the verified v1.6-psi separate fixture artifact custody result and the corrected claim boundary for ControllerGate v1.6.

The supplied artifacts are controlled diagnostic benchmark artifacts. They are valid evidence for closing v1.6 at psi, but they are not real repository / real agent trace episodes for v1.7-alpha scoring.

## Supplied Artifacts

| Artifact | Path | SHA256 |
| --- | --- | --- |
| External fixture artifact ZIP | `C:\Users\thisb\Downloads\ControllerGate_v1_6_psi_ExternalFixtureArtifact.zip` | `1231ed48b78421f2850f1bf776d6ff9fdce12a94429ef8a83b4b6fccdb7f9c0d` |
| Benchmark package ZIP | `C:\Users\thisb\Downloads\ControllerGate_v1_6_psi_SeparateFixtureArtifactCustodyTrial_Package.zip` | `0bfd1541f4c8e542efd846a72e30b60fdbe3657cae6f95c6fdff8a8a14f87243` |
| Notebook | `C:\Users\thisb\Downloads\ControllerGate_v1_6_psi_SeparateFixtureArtifactCustodyTrial.ipynb` | `d3211e046f04c5f318911bd5010f41c9704d01fefd5f7dfc547d068b12622050` |

## Fresh Verification

Fresh rerun was executed from an extracted temporary copy of the supplied benchmark package and external fixture artifact.

Rerun output:

```text
benchmark complete: 51 / 51 passed
separate external fixture artifact verified
verified fixture artifact only scored
decision report: 51 / 51 passed
all criteria passed
```

The benchmark package `SHA256SUMS.txt` verified all listed package files.

The external fixture artifact `SHA256SUMS.txt` verified all listed fixture files.

The rerun output JSON is semantically consistent with the packaged `outputs/decision_report.json`: both report `51 / 51`, both contain 51 criteria, and the rerun contains 0 failed criteria. The rerun JSON byte hashes differ from the packaged output because the runner rewrites JSON with sorted keys and formatting during rerun.

## Defensible v1.6 Claim

ControllerGate v1.6 provides verified diagnostic evidence that discovered causal trace memory can preserve hidden-downstream correctness, reduce corruption, recover from stale or adversarial memory conditions, outperform no-memory, predefined-memory, and poisoned-memory baselines, and score only verified external fixture artifacts under controlled benchmark conditions.

## Required Non-Claim

ControllerGate v1.6 does not prove self-maintaining software. It proves that the memory-and-gating architecture survives a progressively hardened diagnostic benchmark ladder.

## Next Stage

The next stage is ControllerGate v1.7-alpha: a real repository / real agent trace pilot using real CI logs, patch attempts, tool-loop traces, stale reads, false completion claims, generated artifacts, and downstream outcomes.

# ControllerGate v1.6 Corrected Version Ledger

## Freeze Point

v1.6 is closed at psi. No additional v1.6 microversion should be added unless a critic finds a serious defect in psi.

## Corrected Chronology

| Version | Corrected status | Lesson |
| --- | --- | --- |
| Theta | Partial diagnostic win | Budget-limited memory can help, but without precision gates it overgeneralizes. |
| Iota | Corrected false win: `16 / 20`, not `20 / 20` | Precision gates prevented bad transfer but suppressed useful memory. |
| Kappa | Verified `20 / 20` | Adaptive threshold calibration recovered useful transfer while preserving low false-positive transfer. |
| Lambda | Verified `20 / 20` | Memory remained useful under noisy heldout family drift. |
| Mu | Verified `20 / 20` | Discovered memory separated from frozen predefined memory under novel heldout recurrence. |
| Nu | Verified `21 / 21` | Sparse recurrence still helped without one-shot productive overfit. |
| Xi | Verified `23 / 23` | Discovered memory could detect contradiction, quarantine stale lessons, and relearn. |
| Omicron | Verified `25 / 25` | Discovered memory resisted scripted stale-memory spoofing. |
| Pi | Corrected false win: `27 / 28`, not `28 / 28` | Adaptive-adversary defense did not prove positive recovery after strategy change. |
| Rho | Verified `28 / 28` | Counter-strategy recovery stabilized after a phase transition. |
| Sigma | Verified `28 / 28` | Discovered memory survived black-box red-team selection, though later-round adaptation was not positive. |
| Tau | Verified `31 / 31` | Later-round red-team performance improved without increased abstention. |
| Upsilon | Verified `36 / 36` | The red-team learning curve transferred to an independent internal generator. |
| Phi | Verified `40 / 40` | Frozen external-style fixture ingestion worked with internal generation disabled for scoring. |
| Chi | Verified `45 / 45` | Runtime fixture ingestion verified manifests and hashes and rejected tampering. |
| Psi | Verified `51 / 51` | Benchmark code custody and red-team fixture artifact custody were separated and verified independently. |

## Reporting Rule

No pass result should be reported unless these agree:

1. Packaged `decision_report.json`.
2. Fresh rerun analyzer output.
3. SHA256 verification.

When fixture artifacts are separate, fixture artifact provenance must also verify.

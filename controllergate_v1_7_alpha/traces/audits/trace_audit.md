# ControllerGate v1.7-alpha Trace Audit

Status: blocked pending real maintenance episodes.

## Audit Result

No future-leakage or policy-blindness scoring audit can be completed because there are no real repository / real agent trace episodes in `traces/normalized/episodes.jsonl`.

## Findings

| Check | Result | Reason |
| --- | --- | --- |
| Episode ledger exists | PASS | `traces/normalized/episodes.jsonl` exists as an empty scaffold. |
| Real episodes available | FAIL | No real maintenance episodes have been supplied. |
| Future-leakage audit | BLOCKED | Requires episode records with decision-time and outcome fields. |
| Missing evidence audit | BLOCKED | Requires per-episode evidence bundles. |
| Ambiguous outcome-label audit | BLOCKED | Requires real visible/downstream outcome evidence. |
| Unsupported claim audit | PASS | Current scaffold makes no v1.7-alpha pass claim. |

## Required To Unblock

Add real episode bundles under `traces/raw/episode_###/`, then normalize them into `traces/normalized/episodes.jsonl` using `schemas/episode.schema.json`.

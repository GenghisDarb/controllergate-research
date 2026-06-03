# Episode Collection Instructions

Use `controllergate_v1_7_alpha/episodes_pending/` for candidate real maintenance episodes before they are normalized into `traces/normalized/episodes.jsonl`.

Do not score v1.7-alpha from pending episodes. Pending means the evidence bundle is incomplete, unverified, or not yet normalized.

## Required Files Per Episode

Each episode directory should contain:

```text
ci_log.txt
failing_command.txt
patch_diff.diff
agent_trace.md
files_read.txt
files_written.txt
artifact_manifest.txt
outcome.md
```

## File Rules

`ci_log.txt`

- Include real CI, test, analyzer, or verifier output.
- Include timestamps and command context when available.
- If there is no CI log yet, write `TODO_REQUIRED: reason`.

`failing_command.txt`

- Include the exact command that failed or exposed the mismatch.
- If the episode is a report verification correction, include the analyzer or verifier command.
- If unknown, write `TODO_REQUIRED: exact command needed`.

`patch_diff.diff`

- Include the real patch, generated report diff, package diff, or correction diff.
- If there was no code patch, explain why and mark the missing artifact as `TODO_REQUIRED`.

`agent_trace.md`

- Include the real builder/agent claim, tool-loop trace, file reads/writes, command outputs, stale reads, retry loops, and final status claim.
- Separate what was available at decision time from what was discovered later.
- Do not paraphrase an unavailable trace as if it exists.

`files_read.txt`

- List files read before the relevant decision or claim.
- Include package paths, report files, notebooks, logs, and manifests when applicable.

`files_written.txt`

- List files written or modified by the attempted repair, generated report, package, notebook, or correction.

`artifact_manifest.txt`

- List every artifact needed to verify the episode.
- Include path, SHA256, custody status, and whether it was available at decision time.
- Use `TODO_REQUIRED` for missing paths, hashes, rerun outputs, or package files.

`outcome.md`

- State the visible result, downstream result if available, agent claim, reality check, and corrected classification.
- Mark future-only evidence clearly.
- Preserve failed or corrected claims. Do not rewrite them into a clean pass.

## Valid Evidence

Valid evidence includes:

- packaged `decision_report.json`;
- fresh rerun analyzer output;
- `SHA256SUMS.txt` verification;
- CI or test logs;
- PR/commit diffs;
- notebook output;
- generated report text;
- critic verification notes;
- local command output captured during the episode;
- file hashes and custody manifests.

## Invalid Evidence

Invalid evidence includes:

- inferred success without logs;
- future outcome labels used as decision-time inputs;
- benchmark family labels used as real memory keys;
- synthetic recurrence labels;
- summaries that omit the actual packaged report or rerun result;
- claims that artifacts exist without path and custody verification.

## Completion Rule

An episode can move from `episodes_pending/` to `traces/raw/episode_###/` only when every required file is filled with real evidence or an explicit `UNAVAILABLE: reason`.

The normalized ledger should not be populated until at least 10 real episodes have complete evidence bundles.

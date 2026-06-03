# Episode Template

Copy this directory to `episode_001`, `episode_002`, and so on for real maintenance evidence.

Each evidence file should contain the real artifact content or the exact text:

```text
UNAVAILABLE: reason
```

Do not summarize unavailable evidence as if it existed.

The normalized record for this episode belongs in:

```text
controllergate_v1_7_alpha/traces/normalized/episodes.jsonl
```

Use `schemas/episode.schema.json` and keep all memory keys evidence-derived.

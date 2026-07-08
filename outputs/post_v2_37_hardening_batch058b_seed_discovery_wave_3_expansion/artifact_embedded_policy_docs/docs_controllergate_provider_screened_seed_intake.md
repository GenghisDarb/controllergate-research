# Provider-screened seed intake

Provider-screened seed intake admits candidate leads only after repository identity, commit identity, target command evidence, and provider/runtime metadata are recorded. The intake layer does not run replay, generate patches, apply patches, or increment repair counts.

The reusable intake rule is simple: a lead can move toward a future pre-repair replay only when it is not a counted, parked, retired, or active duplicate; has a reproducible commit SHA or an exact blocker; has native target path or command evidence; and excludes fixed, future, gold, and issue solution evidence.

Workflow success is not repair success. Seed discovery is not repair success. Provider/runtime pre-screening is not repair success.

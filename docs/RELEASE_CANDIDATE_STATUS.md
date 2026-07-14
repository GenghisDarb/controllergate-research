# Release candidate status

Batch085 decision: `PRODUCT_BETA_RC_BLOCKED_EXACT`.

The canonical architecture, durable state, typed tokens, proof-derived counts, memory isolation, controlled self-maintenance, read-only watch loop, and package build/install checks are implemented. The release gate remains blocked because no complete real historical repair replay and two correctly classified historical abstention replays have executed through the canonical runtime with real canary, health, and rollback. Version `0.2.0b1` is therefore not applied; the project retains `0.1.0a1`.

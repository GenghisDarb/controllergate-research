# AMDS full bug-tree closure mode

AMDS full bug-tree closure is a reusable runtime-wrapper policy for preserving every known failure branch before a source-only patch gate.

It extends existing AMDS/MinimalProbe evidence handling. It does not authorize extra patching, duplicate replay, count gates, or claim promotion.

Future candidates should use this mode when multiple failure families exist, provider/runtime blockers appear, or partial improvement exposes a second layer.

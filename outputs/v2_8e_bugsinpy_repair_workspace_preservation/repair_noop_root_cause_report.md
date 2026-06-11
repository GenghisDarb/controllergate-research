# Repair No-op Root Cause

The repair runner reached valid replay but emitted empty or no-op repair traces. v2.8e requires a bounded repair-attempt layer that records candidate-generation decisions. If no patch candidate can be generated from allowed decision-time inputs, the episode is blocked as `blocked_no_repair_candidate_generated` rather than scored.

# v2.8b Checkout Failure Root Cause

v2.8b reached the GitHub Actions workflow, but all three episodes blocked before replay/repair. The checkout logs contain path-resolution failures such as `No such file or directory`, `Could not parse object`, and missing workspace copy sources. The no-memory and memory-enabled logs report unavailable workspaces.

This is blocked checkout/runtime evidence, not negative ControllerGate repair capability evidence. v2.8c fixes the runner by using absolute workspace paths and by requiring a pre-repair replay gate before no-memory or memory-enabled repair paths can run.

# ControllerGate provider/runtime recovery patterns

Batch060c introduces a reusable provider/runtime recovery pattern library. It routes removed stdlib modules, optional backend gaps, test-runner mismatches, interpreter behavior changes, compiled dependency boundaries, network/model boundaries, and mixed source-provider surfaces before source-only patch licensing.

This subsystem is not repair success. Provider recovery can reduce or clarify a failure family, but repair success still requires original target pass, duplicate clean replay, and the appropriate count gate.

The provider/runtime screen is required before future source-only patch gates when these patterns are detected.

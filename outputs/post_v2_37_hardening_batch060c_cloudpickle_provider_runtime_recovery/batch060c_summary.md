# Batch060c Cloudpickle provider/runtime recovery

Batch060c officially verifies Batch060b and executes provider/runtime recovery for Cloudpickle without patching.

- Dev requirements alone left `distutils` unavailable in a fresh Python 3.13 venv.
- `setuptools` provider materialization is justified by the buggy `setup.py` importing `setuptools`.
- After `setuptools` materialization, both `distutils` importability nodes passed.
- The full target reduced to the `test_extract_class_dict` / `__firstlineno__` family.
- Batch060c generates no patches, applies no patches, runs no duplicate replay, and runs no count gate.
- Audioread remains preserved as a future provider/backend capsule branch.
- Batch060c also adds reusable provider/runtime recovery patterns and maintenance-memory ledgers.

Next allowed action: `batch060d_cloudpickle_class_dict_source_only_patch_gate`.

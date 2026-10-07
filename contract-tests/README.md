# Contract and tooling checks

Run from this directory with the Python 3.12 development environment:

```bash
python -m pytest -q
```

The 28 checks cover route inventory, unique contract IDs, synthetic fixtures,
response comparison, CI configuration and isolated test-runner safeguards.
They also run through `python tools/verify_foundation.py` from the repository root.

The route oracle reads the recorded Node baseline with `git show`; retain full Git
history when cloning. No retired Node backend is started by these tests.

`parity.py` compares status, important headers, JSON keys and value types while
ignoring generated values. Its compact shape comparator is not a full JSON Schema
validator. Live business behavior is covered separately by the 48-case integration
suite, run with `python tools/verify_ci.py` against disposable data.

See the [root README](../README.md) and [contract inventory](../contracts/README.md).

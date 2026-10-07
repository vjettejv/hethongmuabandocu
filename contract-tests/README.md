# Contract test scaffolding

Run through `python tools/verify_foundation.py` or, from this directory,
`python -m pytest -q` using the Python 3.12 development environment.

Tests verify source inventory completeness against Node route registrations, unique
contract identifiers, synthetic fixture constraints and the response comparator.
No live Node/Python business endpoint comparison is executed in Phase 1.

`parity.py` compares status, important header values, JSON keys and types. It ignores
generated values by design and distinguishes integer/number/string/boolean/null.
Array shape comparison needs populated controlled fixtures; empty arrays do not prove
item compatibility. Non-JSON body text comparison should be added when a specific
business contract requires it. It is a scaffold, not a full JSON Schema validator.

`fetch_read_only` only exposes GET, uses a bounded timeout and follows no redirects.
Future phase tests can call explicit NODE_BASE_URL/PYTHON_BASE_URL targets with controlled
synthetic data. Writes, JWT issuance, OTP/email and destructive operations must use an
isolated test environment and explicit opt-in, never baseline user data.

Foundation health is tested independently in each service; Node health text is not
expected to equal Python JSON. Business parity tests belong to Phases 2–7.

# Node contract baseline

The baseline is **source-derived**, not a dump of live production responses.
`endpoints.json` records all 37 declared business-service routes, gateway paths/aliases,
auth requirements, main request fields, success statuses/shapes and error statuses/shapes.
The Node baseline commit is recorded in the file. `shapes.json` describes camelCase
models and endpoint-specific serialization differences in a compact shape notation.

Notation: `?` means optional, `[]` means array, `|` means a union, named strings reference
shapes.json. This is a semi-machine-readable inventory, not a fabricated OpenAPI API.
Request fields without `?` describe the expected operation payload, not necessarily
complete legacy input validation. Do not infer unimplemented validation from this file.

JWT middleware errors are `{error:string}` with 401. Register validation uses
`{message:string}`. Post's global unhandled-error response may include `details`.
Unknown routes use Express's default response; no global JSON error envelope exists.

Key baselines:

- `auth/compatibility.json`: JWT claims/TTL/Bearer and synthetic bcrypt test plan.
- `posts/compatibility.json`: status, numeric price, uploads, sorting and pagination.
- `messages/socketio.json`: existing protocol path, event names and room behavior.
- `gateway.json`: prefixes, special routes, legacy health and proxy risks.
- `fixtures/*.synthetic.json`: invented IDs/accounts/image paths and invalid token.

No real password hash, JWT, OTP, account identity or secret was copied from SQL/data.
The bcrypt/JWT parity plan is scaffolding only; authentication is not implemented yet.

Contracts intentionally record notification route shadowing and OTP error mismatch.
Business API response parity is **not yet claimed**. Python foundation health JSON
also differs intentionally from legacy Node health strings.

The statements above describe the captured Phase 1 Node baseline. Phase 2 Auth
implementation and deliberate differences are recorded separately in
`auth/phase-2.json` and `docs/migration/phase-2-implementation-report.md`.
The original baseline files remain unchanged as the reference for comparison.
# Phase 3 additions

Implemented User/Category semantics and documented divergences are in
`users/phase-3.json` and `categories/phase-3.json`. Source-derived baseline files
remain unchanged; see `docs/migration/phase-3.md` for hybrid/runtime tests.

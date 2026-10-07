# Phase 2 preparation — Gateway + Auth

Prepared on 2026-10-06 (Asia/Saigon). This document prepares the next phase;
it does not implement proxy routes, Auth business behavior or a traffic cutover.
The Phase 1 runtime gate is recorded in [phase-1-verification.md](phase-1-verification.md).

## Starting point

- Keep the Node baseline at `92777b8f70b6717e3ffd12657c725b2ea4e3d0ab` as reference.
- Preserve the existing databases, volumes, frontend, Node sources and the
  pre-existing untracked `HUONG_DAN_TRIEN_KHAI.md`. No automatic commits.
- FastAPI app: `api-gateway/app/`; Django Auth: `auth-service/authentication/`.
- Contracts: `contracts/endpoints.json`, `shapes.json`, `gateway.json`,
  `auth/compatibility.json`; response comparator: `contract-tests/parity.py`.
- Current Python containers remain foundations on internal ports 3000–3009.
  Canonical Node hostnames remain configured as future upstreams; no proxy is active.

## Implementation order

1. Build synthetic Node/Python bcrypt and JWT interoperability tests before Auth
   behavior changes. Verify both directions, wrong password/signature, expiration,
   numeric `id`/`roleId`, HS256 and 86400-second TTL. Share the JWT signing key through
   environment only; Django `SECRET_KEY` is a separate setting. Do not copy real
   credentials, hashes, OTPs or tokens into fixtures/logs.
2. Inspect `auth_db.users` again and define explicit table/column mappings:
   numeric auto-increment id, roleId, username, email, password, isVerified, otp,
   createdAt and updatedAt. Use the actual lowercase physical table; do not create
   Django auth/session tables or run migrations against the legacy database.
3. Implement Auth serializers/services/views and the five routes below. Preserve
   per-endpoint response shapes, camelCase and errors using the Node handlers as
   evidence. Cover registration's downstream profile/email behavior with controlled
   upstream test doubles and failure cases.
4. Implement FastAPI proxy dispatch from env URLs. Test prefix rewriting, route
   precedence, query strings, methods, JSON/multipart/raw bodies, status/headers,
   uploads, upstream timeouts/errors and resource cleanup. Keep authentication
   ownership consistent with the baseline; do not invent a new global envelope.
5. Validate Gateway + Auth with an isolated DB and synthetic accounts, then a
   controlled cutover plan with rollback. Keep the remaining services on Node until
   their migration phases and verify Socket.IO forwarding separately.

## Auth routes to preserve

| Gateway route | Service route | Baseline |
|---|---|---|
| POST /auth/register | POST /register | 201 message/userId; validation error 400 message |
| POST /auth/login | POST /login | username or email; 200 token/user; failure 401 error |
| POST /auth/verify-otp | POST /verify-otp | 200 message; missing user 404; current wrong-OTP mapping 500 |
| GET /auth/:id | GET /:id | 200 AuthUser projection; missing user 404 |
| POST /auth/verify | POST /verify | Bearer JWT; 200 valid/user claims; failure 401 error |

Use `contracts/endpoints.json` and `shapes.json` for the complete shapes. The legacy
login is not gated by isVerified. OTP bypass/expiry/attempt limits and exposed fields
are existing security debt. Record any deliberate security behavior change separately
from compatibility work; do not silently copy a bypass or silently change the contract.

## Gateway boundaries

Preserve `/auth`, `/users`, `/posts`, `/categories`, `/messages`, `/notifications`,
`/reviews`, `/search`, `/favorites`, plus `/admin/posts`, `/admin/categories`,
`/uploads` and `/socket.io/`. No `/api` or `/api/v1` prefix is introduced.
Socket.IO forwarding is a gateway compatibility requirement; replacing the Message
server or adding Channels/Redis remains outside Phase 2.

Python health is intentionally JSON while legacy Gateway health is text. Make this
documented foundation exception explicit in parity checks. Other response behavior
must be verified route by route, including response headers and streaming bodies.

## Test and data boundaries

The Phase 1 pytest suites mock DB access. Auth write-flow tests need a separate,
explicitly named disposable test DB and synthetic fixtures. Never point pytest DB
creation/cleanup, registration or OTP tests at baseline accounts. Email tests use a
stub transport; no real email is sent. Node reference tests must avoid its production
startup path because it may call Sequelize sync alter.

Gate Phase 2 completion on synthetic bcrypt/JWT interop, five Auth route parity tests,
gateway dispatch/header/body/error tests, the existing 165 foundation tests, Docker
build/start/health/ready, unchanged legacy schemas and a reviewed rollback procedure.
Business parity has not been established by Phase 1 health checks.

## Planned files

Gateway: proxy implementation and tests under `api-gateway/app/` and `tests/`.
Auth: explicit model mapping, serializers, services, views and URLs under
`auth-service/authentication/`, plus isolated integration and interoperability tests.
Dependency pins/locks and env examples should change only when implementation needs
a concrete additional package. Do not add new infrastructure or modify other services'
business behavior as part of Gateway + Auth.

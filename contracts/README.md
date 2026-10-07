# API contract inventory

These source-derived JSON files preserve the original Node API contracts and the
Python migration decisions. They are used by the current compatibility checks.
They contain synthetic fixtures, not live accounts, tokens or database records.

- `endpoints.json`: all 37 declared business routes, gateway aliases, request fields,
  response shapes, authentication requirements and recorded baseline commit.
- `shapes.json`: camelCase models and endpoint-specific serialization differences.
- `gateway.json`: routing prefixes, special routes and proxy behavior.
- `auth/compatibility.json`, `posts/compatibility.json`, `messages/socketio.json`:
  authentication, uploads, moderation and real-time compatibility contracts.
- Service `phase-*.json` files: implementation decisions and deliberate differences.
- `fixtures/*.synthetic.json`: invented accounts, IDs, image paths and invalid tokens.

Notation: `?` means optional, `[]` means array and `|` means a union. Named strings
reference `shapes.json`. This inventory is not a full JSON Schema validator.
Historical baseline statements describe the captured Node behavior; consult the
service implementation files for subsequent Python behavior.

The current backend uses FastAPI and Django. See the [root README](../README.md)
for startup and verification, and [gateway OpenAPI](http://localhost:3000/docs)
for the running API. Removed migration reports remain in Git history at `6ca3c21`.

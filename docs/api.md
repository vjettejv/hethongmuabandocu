# API and real-time contract guide

The public browser API goes through Nginx and FastAPI. Use [gateway OpenAPI](http://localhost:3000/docs) for running route documentation and service `/schema/`/`/docs/` endpoints for details. The preserved inventory is `contracts/endpoints.json`; that file is the source of truth for exact legacy methods, aliases, and expected response shapes.

| Route group | Owner | Purpose |
|---|---|---|
| /auth | Auth | Registration, OTP verification, login, identity |
| /users | User | Profile lookup/update and Auth ID mapping |
| /posts, /admin/posts | Post | Listings, owner views, moderation, deletion |
| /categories, /admin/categories | Category | Lookup and administrative creation |
| /favorites | Favorite | Toggle, check, and saved listings |
| /reviews | Review | User reviews and image-backed writes |
| /search | Search | Query and projection synchronization |
| /messages | Message | Conversations and message writes |
| /notifications | Message / Notification | Persisted notification operations and email requests |
| /uploads | Post / Review through proxy | Shared uploaded image retrieval |
| /socket.io/ | Message through proxy | Socket.IO polling/WebSocket transports |

Protected requests use `Authorization: Bearer <token>`. Do not put credentials into committed examples. Profile IDs are not Auth IDs; resolve mappings through User. Post moderation enforces its preserved role checks. Category creation and notification writes retain legacy access boundaries; an `/admin` alias alone does not establish authentication. Validation and error JSON retain migration compatibility; route inventory tests verify aliases without introducing API redesign.

Post and Review accept their existing multipart image contracts. Listing writes cannot self-approve: new listings are `pending`; moderation accepts `approved` or `rejected`, and invalid status requests return validation errors. Public listings/search expose approved records according to their established service contracts. Shared file retention on deletion is preserved.

Socket.IO clients use `/socket.io/` and the preserved `join_user_room`, `receive_message`, and `receive_notification` events. Messages are written through HTTP. Exact event payload/room behavior is tested in `integration-tests/phase7/test_full_system.py` and documented in the Phase 6 contract evidence. Message persistence and real-time delivery are separate assertions. Legacy room identity behavior is not authenticated room access; see [architecture](architecture.md).

Notification SMTP defaults to mock mode. Gateway health/docs routes are not business endpoints. No production API hostname or live external service is claimed by these local examples.

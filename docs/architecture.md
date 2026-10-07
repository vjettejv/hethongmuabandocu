# Architecture

The canonical backend consists of a FastAPI gateway and nine Django/DRF services. React is compiled with Vite and served by Nginx. Root Compose contains nineteen containers: ten backend, eight MySQL, and one frontend. See the complete service/port/database matrix in the [README](../README.md).

## Request path and ownership

Browser requests reach Nginx, then FastAPI, then the owning service. Gateway preserves routes, methods, response shapes, authorization headers, request IDs, and transport behavior. It does not own business tables. Auth manages credentials and JWT; User maps Auth IDs to distinct profile IDs. Post owns listings and image metadata; Category owns categories; Favorite and Review own their own relations; Message owns messages and notification records; Search owns a denormalized projection. Notification sends mail and has no database.

Eight MySQL databases use existing table names, column types, indexes, and constraints. Django models are `managed=False`: a Django migration must not recreate legacy business tables. IDs linking services remain external identifiers; cross-service foreign keys are not created. Foreign keys within an owning database remain intact. The schema-only bootstrap initializes empty volumes; it is not an upgrade mechanism for existing data.

Registration and OTP verification operate in Auth; profile creation/lookup goes through User. Listing creation writes Post metadata/uploads, then triggers compatibility side effects, including Search synchronization. Moderation permits pending → approved/rejected; new clients cannot choose their own approval status. Favorite enriches its saved IDs through Post and skips missing posts. Reviews associate reviewer/target identifiers and their own image metadata. Message persists chat data before emitting the corresponding real-time events and notification side effects.

## HTTP authentication

Protected views use the preserved JWT bearer contract. Auth IDs and profile IDs must not be assumed equal. Administrative behavior follows the existing role checks. Gateway routing is not a substitute for service authorization. Existing OTP/JWT response behavior is retained for compatibility; this phase does not redesign authentication or claim production security hardening.

## Socket.IO

The Message ASGI application exposes `/socket.io/`; Nginx and Gateway forward polling, polling-to-WebSocket upgrade, and direct WebSocket traffic. Events: `join_user_room`, `receive_message`, `receive_notification`. Message writes use HTTP. Rooms and emissions are owned by python-socketio. Persisted messages and notifications remain in `message_db`.

Message uses **one Uvicorn worker**, because its room manager is in memory. Multiple workers require a shared manager, which is not implemented. The legacy join/room identity behavior is preserved and is not authenticated room authorization. Test coverage must include polling, direct WebSocket, upgrade, message delivery, notification delivery, and cleanup; simple successful connection alone is insufficient evidence.

## Files and projection

Post and Review mount the same `kientrucpm_shared_uploads` volume at `/app/uploads`. File URLs and multipart field contracts remain compatible. Existing file retention behavior on record deletion is intentional compatibility behavior, not automatic orphan cleanup. Safety verification compares every original file name, size, and SHA-256.

Search is a **MySQL projection**, not Elasticsearch. Best-effort synchronization can leave orphaned/stale rows; deleted projection tombstones are distinct from listing moderation states. Phase 8 must compare the current Search content/drift baseline and must not silently rebuild it. Historical drift does not justify changing business rows in this phase.

## Runtime and tests

All ten backend images run Python; Node/npm remains frontend build/test tooling only. Health checks detect process/service availability and readiness probes verify required dependencies. Database volumes are external; `docker compose down` keeps them. Eight new databases initialize from `seeds/schema/` without historical user/account data. Existing volumes bypass MySQL initialization.

CI derives an isolated Compose configuration from the root file. It assigns UUID container/network/image/volume names, removes canonical host ports and external volume references, supplies generated credentials, and injects only synthetic test fixtures. Search uses an owned test schema. Cleanup deletes only the runner's owned resources. See [development](development.md) and [CI/CD](ci-cd.md) for commands and limits.

There is no Kubernetes/AWS deployment, shared Socket.IO manager, distributed transaction, centralized tracing backend, object storage, or production backup automation configured here. Historical migration evidence remains under `docs/migration/`; its older Node commands do not describe the current runtime.

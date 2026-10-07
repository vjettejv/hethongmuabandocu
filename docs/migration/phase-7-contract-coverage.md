# Phase 7 API contract coverage

All 37 inventory route/method combinations resolve to the actual Python views. Safe GET probes traverse unchanged Nginx/Gateway; primary lifecycle assertions verify writes, envelopes, statuses, camelCase, decimal types and events. Existing local and Phase 2–6 differential tests retain their edge/error assertions. Route-resolution probes alone do not claim full response parity.

| Method | Public route | Service-local path | Aliases | Evidence |
|---|---|---|---|---|
| POST | `/auth/register` | `/register` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| POST | `/auth/login` | `/login` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| POST | `/auth/verify-otp` | `/verify-otp` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/auth/:id` | `/:id` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| POST | `/auth/verify` | `/verify` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/users/me` | `/me` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/users/:authId` | `/:authId` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| PUT | `/users/me` | `/me` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| PUT | `/users/:authId` | `/:authId` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/posts` | `/` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/posts/my-posts` | `/my-posts` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/admin/posts` | `/admin/posts` | `/posts/admin/posts` | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/posts/:id` | `/:id` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| POST | `/posts` | `/` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| DELETE | `/posts/:id` | `/:id` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| PUT | `/admin/posts/:id` | `/admin/posts/:id` | `/posts/admin/posts/:id` | Phase 7 route/method probe; local + Phase 2–6 contracts |
| DELETE | `/admin/posts/:id` | `/admin/posts/:id` | `/posts/admin/posts/:id` | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/categories` | `/` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| POST | `/categories` | `/` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| POST | `/admin/categories` | `/admin/categories` | `/categories/admin/categories` | Phase 7 route/method probe; local + Phase 2–6 contracts |
| POST | `/favorites/toggle` | `/toggle` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/favorites/check/:postId` | `/check/:postId` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/favorites/my-favorites` | `/my-favorites` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/reviews/user/:userId` | `/user/:userId` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| POST | `/reviews` | `/` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| PUT | `/reviews/:id` | `/:id` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| DELETE | `/reviews/:id` | `/:id` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/search` | `/` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| POST | `/search/sync` | `/sync` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/messages/health` | `/health` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/messages/contacts` | `/contacts` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/messages/:contactId` | `/:contactId` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| POST | `/messages` | `/` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| POST | `/messages/notifications` | `/notifications` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| GET | `/messages/notifications` | `/notifications` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| PUT | `/messages/notifications/read-all` | `/notifications/read-all` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |
| POST | `/notifications/email` | `/email` | — | Phase 7 route/method probe; local + Phase 2–6 contracts |

## Additional compatibility

| Behavior | Evidence |
|---|---|
| Post read/list/detail price number; raw multipart-create/moderation retain input string; Search price fixed-decimal string/null | Full lifecycle + prior Phase 4/5 edge/null parity |
| camelCase and UTC timestamps | Recursive E2E body checks + prior shape assertions |
| /uploads GET/HEAD/range/conditional bytes | Real synthetic Post file through Nginx, exact bytes |
| /socket.io/, default namespace, user_<id>, join_user_room | Frontend socket.io-client polling/WS/upgrade |
| receive_message and receive_notification; reconnect | Actual canonical room delivery and explicit rejoin |
| notification newest-first/own/50/read-all | Phase 7 inserts 53 owned rows, verifies exact newest 50 and read-all isolation; Phase 6 boundary assertions |
| /notifications/email | Real DB-less Django mock envelope; fake SMTP in Phase 6 |
| /admin/posts and /posts/admin/posts | Both live GET aliases; moderation uses established PUT |
| /admin/categories and /categories/admin/categories | POST-only contract; safe GET yields expected 405 |

Known intentional divergences remain: OTP bypass removed, notification list route shadow fixed, safe upload paths, finite dependency timeouts and controlled DB/SMTP errors. No alias is removed. Gateway schemas describe transport/foundation and do not duplicate proxied service schemas. Auth business docs are reachable directly inside its container, intentionally hidden at the public /auth/docs path.

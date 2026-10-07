# Frontend audit and login repair

This follow-up addresses the user's broken `/login` page and request to audit the rest
of the frontend. The earlier Phase 7 migration report remains historical evidence;
frontend changes here are explicitly subsequent work. Python business code, backend API
contracts, frontend package/lockfiles, existing credentials, databases and uploads were
not changed by the repair. No commit was made.

## Findings and fixes

| Area | Observed defect | Result |
|---|---|---|
| Login | Two unlabelled fields; no submit button, feedback, identity persistence or navigation | Complete labelled form, pending/error states, real login, token/user/role persistence and safe return path |
| Same-tab session | Layout memoized initial storage state; login did not update navigation | Shared session events/hook, storage-event support, expiry handling and immediate navigation update |
| Route guards | Any truthy storage token allowed entry; role came from separate stale storage | Validate claim shape/expiry for UI, derive identity/role from claims, retain protected return path |
| Logout | Cleared all localStorage including unrelated preferences | Remove only auth keys; disconnect shared socket and update all consumers |
| Register / OTP | No pending guard; resend only returned to the first step; weak OTP field constraints | Actual existing register endpoint for resend, six-digit validation, error/pending states and activation redirect |
| Account | Never loaded profile; PUT targeted nonexistent `/users/profile`; no complete form | GET/PUT `/users/me`, camelCase fields, retry, save feedback and persisted reload |
| Create Post | Empty form; request appended title only; corrupted condition text | Categories, title/price/description/condition fields, up to five multipart `images`, loading/error handling and My Posts redirect |
| My Posts | Never loaded rows; bare delete buttons | Actual own list, status labels, pagination, detail links, confirmation and owner DELETE |
| Favorites | Never loaded rows; used nonexistent DELETE route | Actual hydrated Post array; POST `/favorites/toggle` with returned state; add/check from detail and remove/list views |
| Chat | Static text; independent socket did not join the user room or render/send/history | Shared authenticated-layout connection, room join/rejoin, contacts, selected peer, HTTP send, realtime receive, history, deduplication and cleanup |
| Nested route context | Initial repaired Chat failed because nested Outlet dropped layout context | Both guards forward Outlet context; real Chat tests rerun successfully |
| Admin UI | Placeholder text without data/actions | Actual envelope list, paged status filters, approve/reject through existing PUT endpoint |
| Admin direct URL | Nginx proxied `/admin` to Gateway, returning JSON 404 | Exact `/admin` and `/admin/` serve SPA; nested admin API paths retain their proxy |
| Error handling | Unhandled rejected requests and missing loading/empty states | Cancellable reads, pending guards, visible errors, retry actions; authenticated 401 clears current auth session |
| Price display | Default VND formatting silently rounded API decimal amounts | Whole prices stay compact; up to two API decimal places retained consistently |
| Vietnamese / layout | Corrupted source labels and long-text overflow | Earlier header/footer/home corrections retained; forms use correct Vietnamese; narrow columns and long contact names wrap |

Session claims are used for frontend navigation only. JWT authenticity and business
permissions remain the backend's responsibility; this audit does not claim to repair
the previously documented backend authorization/security debt.

## Verification

The final production Vite build PASS (135 transformed modules). Rebuilt only frontend
with `docker compose up -d --build --no-deps frontend`. Eleven Node contract tests PASS:

```powershell
node do-cu-frontend/tests/frontend-contracts.test.js
```

The tests cover actual raw-array/envelope contracts, visible error handling, message
deduplication, upload URL handling, exact decimal VND display, safe return paths, full
login persistence/same-tab events, token-only session recovery, stale metadata, expired/
malformed tokens, mismatched login identities, admin role and scoped logout. The initial
`node --test` runner hit a sandbox child-process restriction before test execution;
running the same native `node:test` file directly passed without spawning a runner.

Real browser verification used three UUID-owned `.invalid` accounts, one synthetic PNG
and a journal recording exact account/Post/file ownership. Search writes used the
already owned empty `phase7_search_e2e` shadow; canonical Search was never synchronized
from these synthetic Post IDs. All final tested flows PASS:

1. Login form renders; invalid credentials produce visible feedback.
2. Registration/resend use the existing endpoint, wrong OTP produces feedback, actual
   six-digit fixture OTP activates the account and redirects to login.
3. Anonymous Account route returns to login; successful login returns to Account and
   updates authenticated navigation immediately.
4. Profile GET/PUT persists after full browser reload.
5. Actual multipart Create Post sends all fields and a PNG, then My Posts shows the new
   Post, image, price, category and legacy `available` status.
6. Owner-delete confirmation opens; cancelling leaves the owned Post intact. No
   destructive browser delete was performed against existing data.
7. Detail Favorite check/add, hydrated Favorites list and toggle removal work.
8. Chat selects the test peer, sends a real HTTP message, receives the peer's actual
   Socket.IO reply exactly once, and reloads both messages from database history.
9. Non-admin direct `/admin` redirects to Home; admin login exposes the admin link.
10. Admin list, approve, reload/persist and reject operate only on the owned Post.
11. Logout removes authenticated navigation and returns to a clean guest login page.

The first browser Chat test caught the nested-context error; this was repaired, rebuilt
and the affected Chat flow rerun. An exact-label selector initially missed the category
select's combined label text; the actual selector was inspected and selected through
its visible label. These diagnostics were not hidden or counted as passing tests.

Read-only HTTP checks confirm SPA pages return HTML and `/admin/posts` still returns its
unauthenticated JSON 401; POST-only category admin still returns JSON 405 on GET.
Existing Socket.IO polling returns 200. New final-render logs and the clean login
screenshot are stored under ignored `.artifacts/phase7`.

## Preservation and cleanup

All journal-owned synthetic accounts, profiles, Post/Image rows, favorites, both-direction
messages, moderation notifications, Search-shadow rows and the byte/hash-verified PNG
were removed. Canonical `search_db` was restored and readiness checked. Final safety
PASS: all eight original schema/count/full-row hashes, all 46 uploads and Search drift/
content hash match the original evidence. Nineteen canonical containers remain running.
Git index remains empty; the user's deployment guide and preexisting migration work are
preserved. Private fixture credentials remain ignored and are not included in this report.

## Files and scope

This audit modifies Login, Register, Account, CreatePost, MyPosts, MyFavorites, Admin,
Chat, PostDetail, Home's shared price/image formatting, SiteLayout, both route guards,
API handling, shared CSS and Nginx. New source files are `services/session.js`,
`services/contracts.js`, `hooks/useSession.js`, `components/Page.jsx`,
`components/PostCard.jsx` and `tests/frontend-contracts.test.js`.

Previously corrected Navbar/Footer/document language remain in the combined frontend
follow-up diff. No dependency additions, CI/CD, new backend feature or schema change
were introduced. This is verification of the listed normal/error flows, not exhaustive
browser/device/fuzz testing. Real external SMTP delivery remains outside the local mock
environment; test OTP was read only from the owned account. Existing backend security
and Search drift debts remain documented. The legacy frontend lint command has not been
claimed as a passing check; evidence here is production compilation, contract tests and
actual browser flows.

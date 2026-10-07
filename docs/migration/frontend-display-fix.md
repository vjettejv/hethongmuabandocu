# Frontend display repair after Phase 7

The user's localhost screenshot showed mojibake and an empty product page. Read-only
requests confirmed `/posts` and `/categories` both returned 200: 4463 original Posts
and five categories. The active source and immutable Git baseline both contained an
incomplete Home component: it fetched Posts but never rendered them. Navbar similarly
rendered only the logo, and Vietnamese UI strings were already corrupted in source.
The initial screenshot displayed an older build; the fresh browser initially showed
the incomplete source without that old error banner. Backend API failure was not
reproduced.

The follow-up request authorizes frontend repair after the completed Phase 7 migration,
whose original frontend-preservation evidence remains historical. No Python business
logic, API contract, dependency manifest/lockfile, database or uploaded file was edited.

## Changes

- `do-cu-frontend/src/pages/Home.jsx`: render actual Post and category arrays; handle
  loading, failure/retry and cancellation; use existing approved status for public
  listings; restore category/text filtering; display 12 cards per page with images,
  category and VND prices.
- `do-cu-frontend/src/pages/PostDetail.jsx`: fetch and render the actual selected Post,
  handle loading/error, preserve the existing chat route and provide a home link.
- `do-cu-frontend/src/components/Navbar.jsx`: restore brand, existing navigation and
  session actions using existing CSS; replace corrupted Vietnamese text.
- `do-cu-frontend/src/components/Footer.jsx`: correct Vietnamese and copyright text.
- `do-cu-frontend/src/components/SiteLayout.jsx`: correct the fallback notification
  title; retain existing socket behavior.
- `do-cu-frontend/src/index.css`: use existing layout with small card/category,
  pagination and wrapping adjustments.
- `do-cu-frontend/index.html`: declare Vietnamese document language with existing UTF-8.

## Verification

`docker compose up -d --build --no-deps frontend` passed and replaced only the frontend
container. API GET requests still returned 200. Real browser checks passed:

- 22 approved Posts displayed, 12 cards on page one and ten on page two.
- The electronics category displayed nine matching Posts.
- Searching `Boya` returned the matching microphone; an unmatched query displayed the
  empty state; clearing filters restored 22 products.
- Selecting the microphone displayed its real detail, 200000 VND price, category and
  description; returning home restored the product list.
- Header/footer/filter text rendered correct Vietnamese; no browser error/warning
  logs were captured during verification.

The repaired image is saved locally at `.artifacts/phase7/frontend-after.jpg`; build
and final preservation evidence are also ignored local files. All eight database
schema/count/full-row snapshots and 46 original upload entries were compared again.
No live data write was needed for this repair. No commit was made.

Other existing account/admin/chat forms are outside this display repair's verification;
this follow-up does not claim a complete frontend feature audit. The Phase 7 historical
`--files` guard intentionally rejects subsequent frontend edits; use its read-only
`--preservation --runtime` checks here and capture a new file baseline for future work.

# Post moderation status normalization

This user-authorized follow-up replaces the legacy `available` / `pending` split with
one moderation workflow: `pending` (Chờ duyệt) → `approved` (Đã duyệt) or `rejected`
(Từ chối). Earlier Phase 4–7 compatibility reports describe the historical behavior.
The current contract is `contracts/posts/moderation.json`.

## Behavior

- New Posts default to `pending` in Django and in the MySQL column default. A client
  supplying `status=approved` when creating a Post cannot bypass moderation.
- The existing moderation PUT endpoint accepts only `approved` or `rejected`.
  Missing, null, arbitrary or legacy status values return HTTP 400 before any write or
  dependency dispatch. Response: `{"error":"Status must be approved or rejected"}`.
- Repeating the same decision is idempotent and does not send a duplicate notification.
  An administrator can correct an existing approval or rejection through the same API.
- Only `approved` remains visible in Home/Search. Owner deletion still emits the
  internal Search tombstone `deleted`; it is not a fourth moderation state on a Post.
- The frontend retains an `available` display alias for older responses/caches; the
  canonical Post database and new Post creation no longer use that value.

## Data migration

The explicit migration command is needed because existing Django tables are unmanaged.
Updating a model default alone does not change existing MySQL rows or its column default.

```powershell
.venv/Scripts/python.exe tools/normalize_post_statuses.py
.venv/Scripts/python.exe tools/normalize_post_statuses.py --apply
```

The first command is read-only. Apply saves a durable journal under ignored
`.artifacts/post-status-normalization` before writing. It guards against concurrent
changes, locks rows during each database transaction, changes only `available` to
`pending`, and sets the Post column default to `pending`. Non-status fields, original
timestamps and already moderated decisions are preserved. Search receives the same
status-only normalization; there is no full Search rebuild, orphan cleanup, resync of
Post titles/images or notification replay.

Post and Search live in separate MySQL containers, so these are separate transactions;
MySQL's ALTER DEFAULT also commits implicitly. A partial failure remains journaled.
Do not assume cross-database atomicity. Inspect the journal before retrying or restoring.

Guarded rollback, after deploying the prior backend if required:

```powershell
.venv/Scripts/python.exe tools/normalize_post_statuses.py --rollback <journal-path>
```

Rollback refuses changed business rows or moderation decisions, restores journaled
status values/defaults, and does not erase later user activity. A fresh run can safely
normalize any remaining legacy rows; it writes a separate journal.

## Verification and actual deployment

- Post unit/API suite: **84 passed**, including 15 new moderation cases.
- Changed Python sources pass Ruff check/format; Post image rebuilt and restarted alone.
- `tools/test_post_status_normalization.py` passed against separate UUID-owned MySQL
  databases: concurrent-change refusal, migration, idempotent repeat, exact rollback,
  actual Django API creation/decisions/invalid values and internal deletion marker.
  Dependencies were intercepted in this isolated API smoke; no external notification
  was sent. Both disposable databases were removed afterward.
- Actual data migration: **4,431 Post rows** and **4,850 Search rows** changed from
  `available` to `pending`. Post totals remain **4,464**: **4,442 pending / 22 approved**.
  The canonical data currently contains no rejected Posts; this path passed isolated tests.
- Journal: `.artifacts/post-status-normalization/20261006T182356Z-2bc87051/journal.json`.
  It contains original status values/IDs and preservation hashes; no credentials.
- Final verification: Gateway `/posts` exposes only the three canonical statuses;
  the `available` filter returns no rows; Search still returns exactly 22 approved
  results. All row counts, non-status fields/timestamps, Image rows, 47 uploads and
  the six other databases match the pre-change hashes/inventory.

Existing authorization rules, upload handling, Search drift and other documented debts
are outside this status follow-up. No dependency, Git commit or database volume change
was made. Old Node parity tests that expect `available` creation or arbitrary moderation
values describe superseded behavior and are not claimed to pass this new contract.

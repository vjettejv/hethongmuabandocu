# Compatibility constraints and existing mismatches

- Gateway prefixes have no `/api` or `/api/v1`. Preserve special admin/upload/socket routes.
- Preserve endpoint-specific raw arrays/models and envelopes; do not add global pagination.
- Keep camelCase API fields, numeric IDs and JWT claim names.
- Keep bcrypt $2a$10$/$2b$10$ hashes; test using generated synthetic fixtures in Phase 2.
- Preserve `/uploads/<filename>` and shared_uploads. No files are moved or deleted.
- Search uses MySQL projection, approved filter, LIKE title/description and no pagination.
- Message REST sends save to DB before email and realtime emit; no Conversation model exists.
- Notification Service is email delivery; in-app Notification belongs to Message DB.
- Socket.IO cannot be replaced by a plain Channels WebSocket without a protocol adapter.

## Existing source inconsistencies, unchanged

1. Frontend Account calls PUT /users/profile; backend exposes /me and /:authId.
   `/profile` is caught as an authId string, not a dedicated profile endpoint.
2. Frontend MyFavorites calls DELETE /favorites/:postId; backend exposes POST /toggle.
3. Login frontend stores only token, while layout/admin logic expects userId/userRoleId.
4. Several pages are placeholders or have empty lists without backend loading.
5. Vite dev proxy omits favorites, while production Nginx includes it.
6. Message GET /notifications is shadowed by GET /:contactId; record intended and actual dispatch separately.
7. Wrong OTP error text differs between handler/controller, causing 500 rather than intended 400.
8. Posts default to available; search requires approved. sync-all.js defines a different pending default.
9. Admin post deletion does not synchronize Search.
10. Gateway dependency is proxy middleware v3 but event hooks use the older API style.
11. SiteLayout does not clean up its socket; Chat uses a different socket without joining a user room.

Foundation does not fix these business/frontend behaviors. Contract inventory records
them so later fixes can be explicit instead of accidental changes during migration.

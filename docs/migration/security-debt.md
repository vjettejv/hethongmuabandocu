# Legacy security debt (unchanged in Phase 1)

This list records observed implementation behavior; it does not authorize preserving
vulnerabilities in future Python business endpoints. Review security changes separately
from stack parity changes.

| Finding | Evidence | Phase for deliberate review |
|---|---|---|
| Admin post routes verify JWT but not role | post-service/src/routes/index.js, middleware/auth.js | 4 |
| Profile by authId can be written without JWT | user-service/src/routes/index.js | 3 |
| Review create/update/delete public; reviewer ID from body | review-service/src/routes/index.js, commands | 5 |
| Category/admin category create public | category-service/src/routes/index.js | 3 |
| Socket user rooms are unauthenticated | message-service/server.js | 6 |
| Search sync public | search-service/src/routes/index.js | 5 |
| In-app notification create public | message-service/src/routes/index.js | 6 |
| Email delivery endpoint public | notification-service/src/routes/index.js | 6 |
| Login does not require isVerified | auth-service/src/commands/loginHandler.js | 2 |
| OTP bypass hardcoded; no expiry/attempt limit | auth-service/src/commands/verifyOtpHandler.js | 2 |
| Unverified registration can update a matching account | auth-service/src/commands/registerHandler.js | 2 |
| Internal HTTP has no service credential | Auth/Post/Message/Favorite handlers | 2–7 |
| Uploads lack size/MIME validation at Multer | Post/Review upload middleware | 4–5 |
| Existing secret debt remains in legacy Node config | Compose, DB config, JWT fallbacks, import tooling | Separate cleanup/rotation |

No real secret, password hash or bypass value is copied into this document or the
Python examples. No credential rotation is performed in Phase 1.

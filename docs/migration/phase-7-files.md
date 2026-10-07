# Phase 7 complete workspace delta

Measured against the pre-phase snapshot of 577 non-ignored files:
427 byte-identical, 25 modified,
125 removed, 31 created.
These are Phase 7 workspace deltas, not the combined Phase 1–7 diff against the Node HEAD.
Protected user guide, frontend and existing `.gitignore` are byte-identical. No `.py` was
deleted. All removals are in the retirement manifest. Index remains empty.

## Removed files (125)

### Legacy Node source and dependency manifests (97)

- `api-gateway/package.json`
- `api-gateway/server.js`
- `auth-service/package.json`
- `auth-service/server.js`
- `auth-service/src/commands/loginHandler.js`
- `auth-service/src/commands/registerHandler.js`
- `auth-service/src/commands/verifyOtpHandler.js`
- `auth-service/src/config/db.js`
- `auth-service/src/controllers/commandController.js`
- `auth-service/src/controllers/queryController.js`
- `auth-service/src/models/AuthUser.js`
- `auth-service/src/queries/getUserByIdHandler.js`
- `auth-service/src/queries/verifyTokenHandler.js`
- `auth-service/src/routes/index.js`
- `category-service/package.json`
- `category-service/server.js`
- `category-service/src/commands/createCategoryHandler.js`
- `category-service/src/config/db.js`
- `category-service/src/controllers/commandController.js`
- `category-service/src/controllers/queryController.js`
- `category-service/src/models/Category.js`
- `category-service/src/queries/getAllCategoriesHandler.js`
- `category-service/src/routes/index.js`
- `favorite-service/package.json`
- `favorite-service/server.js`
- `favorite-service/src/commands/toggleFavoriteHandler.js`
- `favorite-service/src/config/db.js`
- `favorite-service/src/controllers/commandController.js`
- `favorite-service/src/controllers/queryController.js`
- `favorite-service/src/middlewares/auth.js`
- `favorite-service/src/models/Favorite.js`
- `favorite-service/src/queries/checkFavoriteHandler.js`
- `favorite-service/src/queries/getMyFavoritesHandler.js`
- `favorite-service/src/routes/index.js`
- `message-service/package.json`
- `message-service/server.js`
- `message-service/src/commands/messageCommands.js`
- `message-service/src/commands/notificationCommands.js`
- `message-service/src/config/db.js`
- `message-service/src/controllers/commandController.js`
- `message-service/src/controllers/queryController.js`
- `message-service/src/middlewares/auth.js`
- `message-service/src/models/index.js`
- `message-service/src/queries/messageQueries.js`
- `message-service/src/queries/notificationQueries.js`
- `message-service/src/routes/index.js`
- `notification-service/package.json`
- `notification-service/server.js`
- `notification-service/src/commands/sendEmailHandler.js`
- `notification-service/src/config/mailer.js`
- `notification-service/src/controllers/commandController.js`
- `notification-service/src/routes/index.js`
- `post-service/package.json`
- `post-service/server.js`
- `post-service/src/commands/postCommands.js`
- `post-service/src/config/db.js`
- `post-service/src/controllers/commandController.js`
- `post-service/src/controllers/queryController.js`
- `post-service/src/middlewares/auth.js`
- `post-service/src/middlewares/upload.js`
- `post-service/src/models/index.js`
- `post-service/src/queries/postQueries.js`
- `post-service/src/routes/index.js`
- `post-service/src/utils/helpers.js`
- `post-service/sync-all.js`
- `review-service/package-lock.json`
- `review-service/package.json`
- `review-service/server.js`
- `review-service/src/commands/createReviewHandler.js`
- `review-service/src/commands/deleteReviewHandler.js`
- `review-service/src/commands/updateReviewHandler.js`
- `review-service/src/config/db.js`
- `review-service/src/controllers/commandController.js`
- `review-service/src/controllers/queryController.js`
- `review-service/src/middlewares/upload.js`
- `review-service/src/models/Review.js`
- `review-service/src/queries/getReviewsHandler.js`
- `review-service/src/routes/index.js`
- `search-service/package.json`
- `search-service/server.js`
- `search-service/src/commands/syncIndexHandler.js`
- `search-service/src/config/db.js`
- `search-service/src/controllers/commandController.js`
- `search-service/src/controllers/queryController.js`
- `search-service/src/models/SearchIndex.js`
- `search-service/src/queries/searchHandler.js`
- `search-service/src/routes/index.js`
- `user-service/package.json`
- `user-service/server.js`
- `user-service/src/commands/updateProfileHandler.js`
- `user-service/src/config/db.js`
- `user-service/src/controllers/commandController.js`
- `user-service/src/controllers/queryController.js`
- `user-service/src/middlewares/auth.js`
- `user-service/src/models/UserProfile.js`
- `user-service/src/queries/getProfileHandler.js`
- `user-service/src/routes/index.js`

### Unsafe obsolete root migration scripts (2)

- `migrate.ps1`
- `migration.sh`

### Promoted Python Docker aliases (20)

- `api-gateway/Dockerfile.python`
- `api-gateway/Dockerfile.python.dockerignore`
- `auth-service/Dockerfile.python`
- `auth-service/Dockerfile.python.dockerignore`
- `category-service/Dockerfile.python`
- `category-service/Dockerfile.python.dockerignore`
- `favorite-service/Dockerfile.python`
- `favorite-service/Dockerfile.python.dockerignore`
- `message-service/Dockerfile.python`
- `message-service/Dockerfile.python.dockerignore`
- `notification-service/Dockerfile.python`
- `notification-service/Dockerfile.python.dockerignore`
- `post-service/Dockerfile.python`
- `post-service/Dockerfile.python.dockerignore`
- `review-service/Dockerfile.python`
- `review-service/Dockerfile.python.dockerignore`
- `search-service/Dockerfile.python`
- `search-service/Dockerfile.python.dockerignore`
- `user-service/Dockerfile.python`
- `user-service/Dockerfile.python.dockerignore`

### Obsolete cumulative runtime overlays (6)

- `docker-compose.phase2.yml`
- `docker-compose.phase3.yml`
- `docker-compose.phase4.yml`
- `docker-compose.phase5.yml`
- `docker-compose.phase6.yml`
- `docker-compose.python.yml`

## Modified files (25)

- `README.md`
- `api-gateway/Dockerfile`
- `auth-service/Dockerfile`
- `category-service/Dockerfile`
- `contract-tests/test_baseline.py`
- `docker-compose.phase2.rollback.yml`
- `docker-compose.phase2.test.yml`
- `docker-compose.phase3.rollback.yml`
- `docker-compose.phase3.test.yml`
- `docker-compose.phase4.rollback.yml`
- `docker-compose.phase4.test.yml`
- `docker-compose.phase5.rollback.yml`
- `docker-compose.phase5.test.yml`
- `docker-compose.phase6.rollback.yml`
- `docker-compose.phase6.test.yml`
- `docker-compose.yml`
- `favorite-service/Dockerfile`
- `integration-tests/phase2/test_auth_parity.py`
- `message-service/Dockerfile`
- `notification-service/Dockerfile`
- `post-service/Dockerfile`
- `review-service/Dockerfile`
- `search-service/Dockerfile`
- `tools/verify_phase6_regressions.ps1`
- `user-service/Dockerfile`

## Created files (31)

- `.env.example`
- `api-gateway/Dockerfile.dockerignore`
- `auth-service/Dockerfile.dockerignore`
- `category-service/Dockerfile.dockerignore`
- `docker-compose.phase7.e2e.yml`
- `docker-compose.phase7.rollback-test.yml`
- `docs/migration/phase-7-contract-coverage.md`
- `docs/migration/phase-7-files.md`
- `docs/migration/phase-7-implementation-report.md`
- `docs/migration/phase-7-node-retirement-manifest.md`
- `docs/migration/phase-7-rollback.md`
- `docs/migration/phase-7-runbook.md`
- `favorite-service/Dockerfile.dockerignore`
- `integration-tests/phase7/conftest.py`
- `integration-tests/phase7/pytest.ini`
- `integration-tests/phase7/test_full_system.py`
- `message-service/Dockerfile.dockerignore`
- `notification-service/Dockerfile.dockerignore`
- `post-service/Dockerfile.dockerignore`
- `review-service/Dockerfile.dockerignore`
- `search-service/Dockerfile.dockerignore`
- `tools/audit_phase7_runtime.py`
- `tools/legacy_reference.py`
- `tools/prepare_phase7_tests.py`
- `tools/rehearse_phase7_rollback.py`
- `tools/retire_phase7_node.py`
- `tools/snapshot_phase7_state.py`
- `tools/update_phase7_references.py`
- `tools/verify_phase7_integration.ps1`
- `tools/verify_phase7_state.py`
- `user-service/Dockerfile.dockerignore`

## Ignored local state

Private `.env` preserves existing settings. `.artifacts/phase7` holds safety inventories,
test logs, exact source backups, immutable Git reference export, owned test journals and
sanitized runtime checks. It is not a public artifact bundle: old private backups can
contain secrets. Existing `notification-service/node_modules` and
`review-service/node_modules` caches remain inert and excluded from Python Docker builds.
No ignored user cache was deleted. Reference images and stopped disposable test
containers remain available, while all reference processes are stopped.

## Retained Node reference audit

The automated audit searches non-ignored source and configuration for legacy Node entrypoint/dependency terms. Each matching file is classified below. Frontend manifests/client tooling and opted-in reference mounts are also explained in report section 23; keyword matching alone does not establish runtime usage. No matched values are reproduced.

| File | Classification |
|---|---|
| `README.md` | historical/reference documentation or contract oracle |
| `auth-service/authentication/services/passwords.py` | Python compatibility comments/literals; no Node entrypoint |
| `category-service/categories/selectors.py` | Python compatibility comments/literals; no Node entrypoint |
| `contracts/README.md` | historical/reference documentation or contract oracle |
| `contracts/auth/compatibility.json` | historical/reference documentation or contract oracle |
| `contracts/gateway.json` | historical/reference documentation or contract oracle |
| `docs/migration/phase-1-implementation-report.md` | historical/reference documentation or contract oracle |
| `docs/migration/phase-1-verification.md` | historical/reference documentation or contract oracle |
| `docs/migration/phase-1.md` | historical/reference documentation or contract oracle |
| `docs/migration/phase-2-implementation-report.md` | historical/reference documentation or contract oracle |
| `docs/migration/phase-2-readiness.md` | historical/reference documentation or contract oracle |
| `docs/migration/phase-2.md` | historical/reference documentation or contract oracle |
| `docs/migration/phase-3-implementation-report.md` | historical/reference documentation or contract oracle |
| `docs/migration/phase-3.md` | historical/reference documentation or contract oracle |
| `docs/migration/phase-4-implementation-report.md` | historical/reference documentation or contract oracle |
| `docs/migration/phase-4.md` | historical/reference documentation or contract oracle |
| `docs/migration/phase-5.md` | historical/reference documentation or contract oracle |
| `docs/migration/phase-6-implementation-report.md` | historical/reference documentation or contract oracle |
| `docs/migration/phase-6-runbook.md` | historical/reference documentation or contract oracle |
| `docs/migration/phase-7-implementation-report.md` | historical/reference documentation or contract oracle |
| `docs/migration/phase-7-rollback.md` | historical/reference documentation or contract oracle |
| `docs/migration/security-debt.md` | historical/reference documentation or contract oracle |
| `docs/migration/table-mapping.md` | historical/reference documentation or contract oracle |
| `integration-tests/phase2/conftest.py` | opt-in parity/recovery/test tooling |
| `integration-tests/phase2/test_auth_parity.py` | opt-in parity/recovery/test tooling |
| `integration-tests/phase3/conftest.py` | opt-in parity/recovery/test tooling |
| `integration-tests/phase4/conftest.py` | opt-in parity/recovery/test tooling |
| `integration-tests/phase5/conftest.py` | opt-in parity/recovery/test tooling |
| `integration-tests/phase6/conftest.py` | opt-in parity/recovery/test tooling |
| `post-service/posts/selectors.py` | Python compatibility comments/literals; no Node entrypoint |
| `post-service/posts/serializers.py` | Python compatibility comments/literals; no Node entrypoint |
| `review-service/reviews/services.py` | Python compatibility comments/literals; no Node entrypoint |
| `search-service/search_app/selectors.py` | Python compatibility comments/literals; no Node entrypoint |
| `search-service/search_app/services.py` | Python compatibility comments/literals; no Node entrypoint |
| `tools/audit_phase7_runtime.py` | opt-in parity/recovery/test tooling |
| `tools/runtime/legacy-schema-guard.cjs` | opt-in parity/recovery/test tooling |
| `user-service/profiles/services.py` | Python compatibility comments/literals; no Node entrypoint |

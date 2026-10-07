# Phase 7 Node retirement manifest

Prepared before deletion and executed after all retirement gates passed. Source retirement is complete; the canonical stack has passed another full cold restart and 48 final integration tests.

Legacy baseline: `92777b8f70b6717e3ffd12657c725b2ea4e3d0ab`. Immutable export: 107 backend files.

Executed targets: 125 = 99 legacy Node/root-script removals, 20 Python Docker promotions, 6 obsolete runtime overlays. Ten Node Dockerfiles are replaced by byte-identical promoted Python Dockerfiles, not removed paths. Docker ignore files retain the Python allowlist with canonical filenames updated.

No `.py`, frontend, guide, contracts, business data or uploads are retirement targets. Existing source hashes are verified before every mutation. Uncommitted overlay/Docker sources have an ignored byte-preserving backup; do not assume Git can recover them.

| Service | Target | Action / reason | Python replacement | Recovery |
|---|---|---|---|---|
| api-gateway | `api-gateway/package.json` | remove: Legacy Node backend source/dependency manifest | `api-gateway/app` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| api-gateway | `api-gateway/server.js` | remove: Legacy Node backend source/dependency manifest | `api-gateway/app` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| auth-service | `auth-service/package.json` | remove: Legacy Node backend source/dependency manifest | `auth-service/authentication` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| auth-service | `auth-service/server.js` | remove: Legacy Node backend source/dependency manifest | `auth-service/authentication` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| auth-service | `auth-service/src/commands/loginHandler.js` | remove: Legacy Node backend source/dependency manifest | `auth-service/authentication` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| auth-service | `auth-service/src/commands/registerHandler.js` | remove: Legacy Node backend source/dependency manifest | `auth-service/authentication` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| auth-service | `auth-service/src/commands/verifyOtpHandler.js` | remove: Legacy Node backend source/dependency manifest | `auth-service/authentication` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| auth-service | `auth-service/src/config/db.js` | remove: Legacy Node backend source/dependency manifest | `auth-service/authentication` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| auth-service | `auth-service/src/controllers/commandController.js` | remove: Legacy Node backend source/dependency manifest | `auth-service/authentication` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| auth-service | `auth-service/src/controllers/queryController.js` | remove: Legacy Node backend source/dependency manifest | `auth-service/authentication` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| auth-service | `auth-service/src/models/AuthUser.js` | remove: Legacy Node backend source/dependency manifest | `auth-service/authentication` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| auth-service | `auth-service/src/queries/getUserByIdHandler.js` | remove: Legacy Node backend source/dependency manifest | `auth-service/authentication` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| auth-service | `auth-service/src/queries/verifyTokenHandler.js` | remove: Legacy Node backend source/dependency manifest | `auth-service/authentication` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| auth-service | `auth-service/src/routes/index.js` | remove: Legacy Node backend source/dependency manifest | `auth-service/authentication` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| category-service | `category-service/package.json` | remove: Legacy Node backend source/dependency manifest | `category-service/categories` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| category-service | `category-service/server.js` | remove: Legacy Node backend source/dependency manifest | `category-service/categories` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| category-service | `category-service/src/commands/createCategoryHandler.js` | remove: Legacy Node backend source/dependency manifest | `category-service/categories` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| category-service | `category-service/src/config/db.js` | remove: Legacy Node backend source/dependency manifest | `category-service/categories` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| category-service | `category-service/src/controllers/commandController.js` | remove: Legacy Node backend source/dependency manifest | `category-service/categories` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| category-service | `category-service/src/controllers/queryController.js` | remove: Legacy Node backend source/dependency manifest | `category-service/categories` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| category-service | `category-service/src/models/Category.js` | remove: Legacy Node backend source/dependency manifest | `category-service/categories` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| category-service | `category-service/src/queries/getAllCategoriesHandler.js` | remove: Legacy Node backend source/dependency manifest | `category-service/categories` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| category-service | `category-service/src/routes/index.js` | remove: Legacy Node backend source/dependency manifest | `category-service/categories` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| favorite-service | `favorite-service/package.json` | remove: Legacy Node backend source/dependency manifest | `favorite-service/favorites` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| favorite-service | `favorite-service/server.js` | remove: Legacy Node backend source/dependency manifest | `favorite-service/favorites` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| favorite-service | `favorite-service/src/commands/toggleFavoriteHandler.js` | remove: Legacy Node backend source/dependency manifest | `favorite-service/favorites` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| favorite-service | `favorite-service/src/config/db.js` | remove: Legacy Node backend source/dependency manifest | `favorite-service/favorites` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| favorite-service | `favorite-service/src/controllers/commandController.js` | remove: Legacy Node backend source/dependency manifest | `favorite-service/favorites` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| favorite-service | `favorite-service/src/controllers/queryController.js` | remove: Legacy Node backend source/dependency manifest | `favorite-service/favorites` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| favorite-service | `favorite-service/src/middlewares/auth.js` | remove: Legacy Node backend source/dependency manifest | `favorite-service/favorites` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| favorite-service | `favorite-service/src/models/Favorite.js` | remove: Legacy Node backend source/dependency manifest | `favorite-service/favorites` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| favorite-service | `favorite-service/src/queries/checkFavoriteHandler.js` | remove: Legacy Node backend source/dependency manifest | `favorite-service/favorites` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| favorite-service | `favorite-service/src/queries/getMyFavoritesHandler.js` | remove: Legacy Node backend source/dependency manifest | `favorite-service/favorites` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| favorite-service | `favorite-service/src/routes/index.js` | remove: Legacy Node backend source/dependency manifest | `favorite-service/favorites` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| message-service | `message-service/package.json` | remove: Legacy Node backend source/dependency manifest | `message-service/messaging` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| message-service | `message-service/server.js` | remove: Legacy Node backend source/dependency manifest | `message-service/messaging` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| message-service | `message-service/src/commands/messageCommands.js` | remove: Legacy Node backend source/dependency manifest | `message-service/messaging` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| message-service | `message-service/src/commands/notificationCommands.js` | remove: Legacy Node backend source/dependency manifest | `message-service/messaging` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| message-service | `message-service/src/config/db.js` | remove: Legacy Node backend source/dependency manifest | `message-service/messaging` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| message-service | `message-service/src/controllers/commandController.js` | remove: Legacy Node backend source/dependency manifest | `message-service/messaging` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| message-service | `message-service/src/controllers/queryController.js` | remove: Legacy Node backend source/dependency manifest | `message-service/messaging` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| message-service | `message-service/src/middlewares/auth.js` | remove: Legacy Node backend source/dependency manifest | `message-service/messaging` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| message-service | `message-service/src/models/index.js` | remove: Legacy Node backend source/dependency manifest | `message-service/messaging` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| message-service | `message-service/src/queries/messageQueries.js` | remove: Legacy Node backend source/dependency manifest | `message-service/messaging` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| message-service | `message-service/src/queries/notificationQueries.js` | remove: Legacy Node backend source/dependency manifest | `message-service/messaging` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| message-service | `message-service/src/routes/index.js` | remove: Legacy Node backend source/dependency manifest | `message-service/messaging` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| notification-service | `notification-service/package.json` | remove: Legacy Node backend source/dependency manifest | `notification-service/email_delivery` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| notification-service | `notification-service/server.js` | remove: Legacy Node backend source/dependency manifest | `notification-service/email_delivery` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| notification-service | `notification-service/src/commands/sendEmailHandler.js` | remove: Legacy Node backend source/dependency manifest | `notification-service/email_delivery` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| notification-service | `notification-service/src/config/mailer.js` | remove: Legacy Node backend source/dependency manifest | `notification-service/email_delivery` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| notification-service | `notification-service/src/controllers/commandController.js` | remove: Legacy Node backend source/dependency manifest | `notification-service/email_delivery` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| notification-service | `notification-service/src/routes/index.js` | remove: Legacy Node backend source/dependency manifest | `notification-service/email_delivery` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| post-service | `post-service/package.json` | remove: Legacy Node backend source/dependency manifest | `post-service/posts` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| post-service | `post-service/server.js` | remove: Legacy Node backend source/dependency manifest | `post-service/posts` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| post-service | `post-service/src/commands/postCommands.js` | remove: Legacy Node backend source/dependency manifest | `post-service/posts` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| post-service | `post-service/src/config/db.js` | remove: Legacy Node backend source/dependency manifest | `post-service/posts` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| post-service | `post-service/src/controllers/commandController.js` | remove: Legacy Node backend source/dependency manifest | `post-service/posts` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| post-service | `post-service/src/controllers/queryController.js` | remove: Legacy Node backend source/dependency manifest | `post-service/posts` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| post-service | `post-service/src/middlewares/auth.js` | remove: Legacy Node backend source/dependency manifest | `post-service/posts` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| post-service | `post-service/src/middlewares/upload.js` | remove: Legacy Node backend source/dependency manifest | `post-service/posts` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| post-service | `post-service/src/models/index.js` | remove: Legacy Node backend source/dependency manifest | `post-service/posts` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| post-service | `post-service/src/queries/postQueries.js` | remove: Legacy Node backend source/dependency manifest | `post-service/posts` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| post-service | `post-service/src/routes/index.js` | remove: Legacy Node backend source/dependency manifest | `post-service/posts` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| post-service | `post-service/src/utils/helpers.js` | remove: Legacy Node backend source/dependency manifest | `post-service/posts` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| post-service | `post-service/sync-all.js` | remove: Legacy Node backend source/dependency manifest | `post-service/posts` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| review-service | `review-service/package-lock.json` | remove: Legacy Node backend source/dependency manifest | `review-service/reviews` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| review-service | `review-service/package.json` | remove: Legacy Node backend source/dependency manifest | `review-service/reviews` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| review-service | `review-service/server.js` | remove: Legacy Node backend source/dependency manifest | `review-service/reviews` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| review-service | `review-service/src/commands/createReviewHandler.js` | remove: Legacy Node backend source/dependency manifest | `review-service/reviews` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| review-service | `review-service/src/commands/deleteReviewHandler.js` | remove: Legacy Node backend source/dependency manifest | `review-service/reviews` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| review-service | `review-service/src/commands/updateReviewHandler.js` | remove: Legacy Node backend source/dependency manifest | `review-service/reviews` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| review-service | `review-service/src/config/db.js` | remove: Legacy Node backend source/dependency manifest | `review-service/reviews` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| review-service | `review-service/src/controllers/commandController.js` | remove: Legacy Node backend source/dependency manifest | `review-service/reviews` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| review-service | `review-service/src/controllers/queryController.js` | remove: Legacy Node backend source/dependency manifest | `review-service/reviews` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| review-service | `review-service/src/middlewares/upload.js` | remove: Legacy Node backend source/dependency manifest | `review-service/reviews` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| review-service | `review-service/src/models/Review.js` | remove: Legacy Node backend source/dependency manifest | `review-service/reviews` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| review-service | `review-service/src/queries/getReviewsHandler.js` | remove: Legacy Node backend source/dependency manifest | `review-service/reviews` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| review-service | `review-service/src/routes/index.js` | remove: Legacy Node backend source/dependency manifest | `review-service/reviews` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| search-service | `search-service/package.json` | remove: Legacy Node backend source/dependency manifest | `search-service/search_app` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| search-service | `search-service/server.js` | remove: Legacy Node backend source/dependency manifest | `search-service/search_app` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| search-service | `search-service/src/commands/syncIndexHandler.js` | remove: Legacy Node backend source/dependency manifest | `search-service/search_app` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| search-service | `search-service/src/config/db.js` | remove: Legacy Node backend source/dependency manifest | `search-service/search_app` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| search-service | `search-service/src/controllers/commandController.js` | remove: Legacy Node backend source/dependency manifest | `search-service/search_app` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| search-service | `search-service/src/controllers/queryController.js` | remove: Legacy Node backend source/dependency manifest | `search-service/search_app` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| search-service | `search-service/src/models/SearchIndex.js` | remove: Legacy Node backend source/dependency manifest | `search-service/search_app` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| search-service | `search-service/src/queries/searchHandler.js` | remove: Legacy Node backend source/dependency manifest | `search-service/search_app` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| search-service | `search-service/src/routes/index.js` | remove: Legacy Node backend source/dependency manifest | `search-service/search_app` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| user-service | `user-service/package.json` | remove: Legacy Node backend source/dependency manifest | `user-service/profiles` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| user-service | `user-service/server.js` | remove: Legacy Node backend source/dependency manifest | `user-service/profiles` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| user-service | `user-service/src/commands/updateProfileHandler.js` | remove: Legacy Node backend source/dependency manifest | `user-service/profiles` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| user-service | `user-service/src/config/db.js` | remove: Legacy Node backend source/dependency manifest | `user-service/profiles` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| user-service | `user-service/src/controllers/commandController.js` | remove: Legacy Node backend source/dependency manifest | `user-service/profiles` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| user-service | `user-service/src/controllers/queryController.js` | remove: Legacy Node backend source/dependency manifest | `user-service/profiles` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| user-service | `user-service/src/middlewares/auth.js` | remove: Legacy Node backend source/dependency manifest | `user-service/profiles` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| user-service | `user-service/src/models/UserProfile.js` | remove: Legacy Node backend source/dependency manifest | `user-service/profiles` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| user-service | `user-service/src/queries/getProfileHandler.js` | remove: Legacy Node backend source/dependency manifest | `user-service/profiles` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| user-service | `user-service/src/routes/index.js` | remove: Legacy Node backend source/dependency manifest | `user-service/profiles` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| root | `migration.sh` | remove: Obsolete destructive truncate-based setup; never executed | `docker-compose.yml and tools/verify_phase7_integration.ps1` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| root | `migrate.ps1` | remove: Obsolete destructive truncate-based setup; never executed | `docker-compose.yml and tools/verify_phase7_integration.ps1` | 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab |
| api-gateway | `api-gateway/Dockerfile.python` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `api-gateway/Dockerfile` | Identical canonical replacement plus Phase 7 baseline hashes |
| api-gateway | `api-gateway/Dockerfile.python.dockerignore` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `api-gateway/Dockerfile.dockerignore` | Identical canonical replacement plus Phase 7 baseline hashes |
| auth-service | `auth-service/Dockerfile.python` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `auth-service/Dockerfile` | Identical canonical replacement plus Phase 7 baseline hashes |
| auth-service | `auth-service/Dockerfile.python.dockerignore` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `auth-service/Dockerfile.dockerignore` | Identical canonical replacement plus Phase 7 baseline hashes |
| user-service | `user-service/Dockerfile.python` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `user-service/Dockerfile` | Identical canonical replacement plus Phase 7 baseline hashes |
| user-service | `user-service/Dockerfile.python.dockerignore` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `user-service/Dockerfile.dockerignore` | Identical canonical replacement plus Phase 7 baseline hashes |
| post-service | `post-service/Dockerfile.python` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `post-service/Dockerfile` | Identical canonical replacement plus Phase 7 baseline hashes |
| post-service | `post-service/Dockerfile.python.dockerignore` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `post-service/Dockerfile.dockerignore` | Identical canonical replacement plus Phase 7 baseline hashes |
| category-service | `category-service/Dockerfile.python` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `category-service/Dockerfile` | Identical canonical replacement plus Phase 7 baseline hashes |
| category-service | `category-service/Dockerfile.python.dockerignore` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `category-service/Dockerfile.dockerignore` | Identical canonical replacement plus Phase 7 baseline hashes |
| message-service | `message-service/Dockerfile.python` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `message-service/Dockerfile` | Identical canonical replacement plus Phase 7 baseline hashes |
| message-service | `message-service/Dockerfile.python.dockerignore` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `message-service/Dockerfile.dockerignore` | Identical canonical replacement plus Phase 7 baseline hashes |
| notification-service | `notification-service/Dockerfile.python` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `notification-service/Dockerfile` | Identical canonical replacement plus Phase 7 baseline hashes |
| notification-service | `notification-service/Dockerfile.python.dockerignore` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `notification-service/Dockerfile.dockerignore` | Identical canonical replacement plus Phase 7 baseline hashes |
| review-service | `review-service/Dockerfile.python` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `review-service/Dockerfile` | Identical canonical replacement plus Phase 7 baseline hashes |
| review-service | `review-service/Dockerfile.python.dockerignore` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `review-service/Dockerfile.dockerignore` | Identical canonical replacement plus Phase 7 baseline hashes |
| search-service | `search-service/Dockerfile.python` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `search-service/Dockerfile` | Identical canonical replacement plus Phase 7 baseline hashes |
| search-service | `search-service/Dockerfile.python.dockerignore` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `search-service/Dockerfile.dockerignore` | Identical canonical replacement plus Phase 7 baseline hashes |
| favorite-service | `favorite-service/Dockerfile.python` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `favorite-service/Dockerfile` | Identical canonical replacement plus Phase 7 baseline hashes |
| favorite-service | `favorite-service/Dockerfile.python.dockerignore` | promote: Promote Python Docker configuration (Dockerfile bytes identical; ignore allowlist filenames updated); remove migration filename | `favorite-service/Dockerfile.dockerignore` | Identical canonical replacement plus Phase 7 baseline hashes |
| root | `docker-compose.python.yml` | remove-scaffold: Obsolete cumulative runtime overlay; test/rollback overlays retained separately | `docker-compose.yml` | Phase 7 ignored before-retirement backup (uncommitted source) |
| root | `docker-compose.phase2.yml` | remove-scaffold: Obsolete cumulative runtime overlay; test/rollback overlays retained separately | `docker-compose.yml` | Phase 7 ignored before-retirement backup (uncommitted source) |
| root | `docker-compose.phase3.yml` | remove-scaffold: Obsolete cumulative runtime overlay; test/rollback overlays retained separately | `docker-compose.yml` | Phase 7 ignored before-retirement backup (uncommitted source) |
| root | `docker-compose.phase4.yml` | remove-scaffold: Obsolete cumulative runtime overlay; test/rollback overlays retained separately | `docker-compose.yml` | Phase 7 ignored before-retirement backup (uncommitted source) |
| root | `docker-compose.phase5.yml` | remove-scaffold: Obsolete cumulative runtime overlay; test/rollback overlays retained separately | `docker-compose.yml` | Phase 7 ignored before-retirement backup (uncommitted source) |
| root | `docker-compose.phase6.yml` | remove-scaffold: Obsolete cumulative runtime overlay; test/rollback overlays retained separately | `docker-compose.yml` | Phase 7 ignored before-retirement backup (uncommitted source) |

Frontend package/lock files and `tools/runtime/*.cjs` remain for legitimate frontend/test tooling. The old Node differential sources are read/exported from Git, outside canonical service trees. No backend npm package manifest/entrypoint remains after execution. No source directory is recursively deleted.


For rollback and isolated source inspection see [phase-7-rollback.md](phase-7-rollback.md). Historical parity/rollback overlays are retained and redirected to the immutable reference cache; Phase 1–6 documentation is retained as evidence.


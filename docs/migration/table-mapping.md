# Legacy physical table mapping

Source baseline: commit `92777b8f70b6717e3ffd12657c725b2ea4e3d0ab`.
Live metadata was read from existing Docker volumes during Phase 1 on 2026-10-06
(Asia/Saigon), using information_schema only. This is not a schema migration.

| Owner | DB | Physical table(s) confirmed | Primary/reference constraints |
|---|---|---|---|
| Auth | auth_db | users | INT id; username/email unique; bcrypt password |
| User | user_db | userprofiles | INT id; unique authId references Auth logically |
| Category | category_db | categories | INT id; unique name |
| Post | post_db | posts, images | INT IDs; images.postId local FK; user/category ID references |
| Message | message_db | messages, notifications | INT IDs; logical user references |
| Review | review_db | reviews | INT id; reviewerId/revieweeId/postId logical references |
| Search | search_db | searchindices | INT postId PK, not generated; denormalized projection |
| Favorite | favorite_db | favorites | INT id; unique userId/postId pair in model |
| Notification email | None | None | Do not create notification_db |

MySQL reports `lower_case_table_names=1`. Favor exact lowercase physical names in
future explicit `db_table` mappings; do not assume Sequelize model capitalization is
the physical name on a different operating system.

Review source has imageUrl, while `seeds/review_db.sql` lacks it. The live DB checked
in Phase 1 **does contain imageUrl**. Seed/source/live schema must be reconciled
deliberately in the Review migration phase; no ALTER is performed by foundation.

Preserve camelCase physical columns and external fields, numeric IDs, DECIMAL(10,2),
createdAt/updatedAt semantics and existing indexes. UserProfile.id is not authId.
Do not turn cross-service numeric references into cross-database Django ForeignKeys.
Do not substitute Django's auth_user for auth_db.users.

No foundation app defines business models. Before implementing a model in its phase,
inspect the exact target DB again and review generated SQL against the baseline.

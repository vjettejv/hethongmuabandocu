# Phase 7 legacy recovery

Immutable baseline: `92777b8f70b6717e3ffd12657c725b2ea4e3d0ab`.
The active `develop` checkout also contains uncommitted Python migration work. Never
reset/clean/restore that checkout to recover Node. Preserve the Python work separately.

Inspect a file without changing anything:

```powershell
git cat-file -t 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab
git show 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab:auth-service/server.js
```

If worktrees are allowed, use a detached worktree in a separate directory:

```powershell
git worktree add --detach <separate-legacy-directory> 92777b8f70b6717e3ffd12657c725b2ea4e3d0ab
```

Phase 7 uses an immutable export instead, because no Git metadata writes are needed.
Each exported backend file is read from `git show` and SHA-256 verified. The ignored
reference cache is regenerable and supports retained differential tests:

```powershell
.\.venv\Scripts\python.exe tools/legacy_reference.py --export .artifacts/phase7/legacy
.\.venv\Scripts\python.exe tools/rehearse_phase7_rollback.py
```

The second command builds four Node images from the exported baseline and launches
`docker-compose.phase7.rollback-test.yml` as **phase7-legacy-recovery**, never as
`kientrucpm`. Its private random password exists only in process environment. One
MySQL 8 container uses tmpfs, `lower_case_table_names=1`, and empty Auth/Post/Category
schemas copied from the canonical schema definitions, with synthetic fixture rows.
There is no connection to the canonical network or data/upload volumes. Legacy
Sequelize DDL is blocked by the reference guard. Gateway is published on an ephemeral
loopback port. `finally` removes only that project's processes/network with `down`.
No volume deletion is performed. Images/reference cache remain useful and regenerable.

The rehearsal proves Gateway boot, real Node Auth login, Post list and Category list.
It is a recovery capability check, not certification of every historical Node behavior.
Full Phase 2–6 parity suites remain separate from ordinary Python verification.

Never run the old root Compose from the baseline against production or existing data
without a separate operational review: it contains historical environment assumptions,
Sequelize schema synchronization and unsafe setup scripts. The old OTP and notification
route bugs also differ intentionally from Python. A live rollback needs backups,
compatible schema/collation/case settings, preserved JWT/bcrypt semantics and a deliberate
data/write cutover plan. This phase does not perform live canonical data rollback.

Returning to Python after rehearsal requires no cutover: the canonical stack was never
changed by it. For ordinary Python startup use the root Compose and private `.env`:

```powershell
docker compose up -d --build
docker compose down
```

Existing named database/upload volumes are external. Never add `-v`, remove volumes,
truncate tables or reset ID counters. Message stays at one ASGI worker.

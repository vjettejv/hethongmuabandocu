# Development and operations

## Requirements and environment

Use Docker/Compose v2 with Linux containers, Git, and Python 3.12. Host frontend development uses the existing Node 18/npm toolchain. Python source checks use `requirements-dev.lock.txt`; on Ubuntu, mysqlclient installation requires `pkg-config default-libmysqlclient-dev` and a compiler. Docker backend images supply their own build prerequisites.

Copy `.env.example` to the ignored `.env`. New installations: generate distinct random Django/JWT keys, choose a MySQL root password, set `PYTHON_DB_USER=root`, and set `PYTHON_DB_PASSWORD` to that password. Existing deployments: retain the actual credentials and keys already used by their volumes and clients. Compose refuses missing required fields. Do not print resolved Compose configuration in CI logs because it includes substituted secrets; validate with `config --quiet`.

| Variable | Purpose |
|---|---|
| PYTHON_SECRET_KEY | Shared Django configuration key |
| JWT_SECRET | Existing token signing contract |
| PYTHON_DB_USER / PYTHON_DB_PASSWORD | Backend database credentials |
| MYSQL_ROOT_PASSWORD | Existing/new MySQL root credential |
| NODE_ENV | Retained compatibility configuration name; not a Node backend |
| MOCK_EMAIL | Development email mock switch |
| SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS | Real SMTP configuration when mock mode is disabled |

Keep `MOCK_EMAIL=true` locally. Never commit environment files, raw database dumps, test credentials, or private runtime logs.

## Startup and shutdown

```bash
python tools/bootstrap_volumes.py --create-missing
docker compose config --quiet
docker compose up -d --build
docker compose ps
```

The bootstrap command creates only missing canonical external volumes; it never deletes or resets an existing volume. MySQL initializes new empty volumes using the eight `seeds/schema/*.sql` files. Those files contain schema only. No historical user rows or password hashes are imported. Fresh business tables are empty; use registration and supported APIs for new data. Legacy SQL dumps outside `seeds/schema/` are migration evidence and are not canonical initialization inputs.

Open [localhost](http://localhost/) and [gateway docs](http://localhost:3000/docs). Django services expose `/health`, `/ready`, `/schema/`, and `/docs/` on internal service ports 3001–3009; Message/Notification remain internal-only in root Compose. Gateway exposes `/health`, `/ready`, `/openapi.json`, and `/docs` on host port 3000. Inspect internal probes through `docker compose exec` or the verification helpers; not every service port is published to localhost. Database host ports are development mappings, not an authorization boundary.

Mock email does not deliver a registration OTP to an inbox. To verify your own newly registered development account, use a private MySQL session:

```bash
docker compose exec auth-db sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mysql -uroot auth_db'
```

At the MySQL prompt, query only your own development address: `SELECT id, otp FROM users WHERE email='your-own-dev-address@example.invalid';`. Enter that OTP into the verification page and exit the database client. Alternatively, deliberately configure real SMTP with mock mode disabled. Do not paste OTPs/database output into shared logs. Fresh initialization does not provision an administrator; administrative moderation needs a deliberately provisioned account under the existing role contract. No default admin password or historical account is shipped.

```bash
docker compose logs --tail 100 api-gateway post-service
docker compose up -d --build post-service
docker compose down
```

Logs may contain private development data; inspect locally and do not upload them indiscriminately. Stop uses no volume-deletion command.

## Source verification

```bash
python -m venv .venv
```

Activate with `source .venv/bin/activate` on Linux/macOS, or `.\.venv\Scripts\Activate.ps1` in PowerShell, then:

```bash
python -m pip install -r requirements-dev.lock.txt
python -m pip check
python tools/verify_foundation.py
python -m ruff check .
python -m ruff format --check .
npm ci --prefix do-cu-frontend
node do-cu-frontend/tests/frontend-contracts.test.js
npm run build --prefix do-cu-frontend
```

Foundation runs lint/format, nine Django system checks, the gateway import/tests, all service unit tests, and contract/tooling tests. Unit checks use blocked database endpoints and synthetic configuration, not the developer database. Frontend host development: `npm run dev --prefix do-cu-frontend`; its configured proxy reaches the running backend. Available frontend scripts are in its package.json; there is no invented npm test/lint script.

## Portable isolated integration

```bash
python tools/verify_ci.py --validate-only
python tools/verify_ci.py --smoke
python tools/verify_ci.py
```

Validation reads canonical Compose without exposing secrets and validates the derived isolated file. Smoke selects the business lifecycle plus ten service health/schema cases (11 cases). Full integration selects all 48 cases. Both build eleven images and start an isolated nineteen-container stack; they require Docker and adequate disk/memory. Do not run multiple eight-database stacks concurrently on an undersized machine.

The runner uses `marketplace-ci-<UUID>` names, generated secrets, a random loopback frontend port, schema-only SQL, one synthetic category, and intentionally different Auth/Profile IDs. It never mounts real data/uploads, reads a developer `.env`, or starts retired Node fixtures. It removes only its UUID-owned containers/network/volumes and removes its temporary credential file. Failure logs stay under ignored `.artifacts/ci/`; the workflow uploads only JUnit XML and a non-sensitive result summary.

Historical parity suites are opt-in migration evidence. They are excluded from canonical CI. To explicitly verify an existing local stack, follow [Phase 7 runbook](migration/phase-7-runbook.md), take fresh database/upload/Search snapshots first, then run the guarded `tools/verify_phase7_integration.ps1 -Canonical` wrapper. It temporarily switches Search to an owned test schema, restores it in `finally`, and removes only owned synthetic rows/files. Recheck preservation afterwards. It is not the clean-clone CI entry point.

## Troubleshooting

- Docker pipe/daemon unavailable: start Docker and verify `docker info`; if Desktop reports disk full, free disk space before retrying. Do not remove canonical volumes to make room.
- Missing external volume: rerun `bootstrap_volumes.py --create-missing`.
- Existing database access denied: verify existing credentials privately. Changing `.env` does not change the password stored in an existing MySQL volume.
- Empty fresh UI: schema-only installation contains no historical categories/listings/accounts; this is expected.
- Stale browser assets after rebuilding frontend: reload the page; check Nginx and gateway health before debugging source.
- Mail remains mocked: `MOCK_EMAIL=true` intentionally returns mock responses; real SMTP delivery is a separate verification.
- Search differs from Post: audit the projection; do not run bulk synchronization or repair existing records as an incidental test cleanup.
- Tests fail midway after Docker stops: treat the run as failed, recover Docker, clean only the recorded CI UUID stack, and rerun. Container startup success alone is not integration PASS.

Dependency audit: the existing frontend lock currently reports 17 npm advisories (1 low, 7 moderate, 9 high). Phase 8 keeps the established dependency versions; upgrades and compatibility/security verification require separate work. The local audit is evidence of remaining dependency debt, not a claim of a hardened production release.

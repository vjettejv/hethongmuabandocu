# CI/CD configuration

Two GitHub Actions workflows are configured. Local verification results and unresolved gates are recorded in [Phase 8 report](migration/phase-8-report.md). No commit, push, tag, image publication, release, or production deployment is performed by the Phase 8 implementation itself.

## Continuous integration

`.github/workflows/ci.yml` handles pull requests, pushes to the existing `develop`/`main` branches, manual dispatch, and reusable workflow calls. Permissions are `contents: read`. Actions are pinned to full commit SHAs. Runners use Ubuntu 24.04, Python 3.12, and the existing Node 18 toolchain.

| Job | Checks |
|---|---|
| quality-python | Install `requirements-dev.lock.txt`; pip check; Ruff lint/format; nine Django checks; gateway import; Python unit/contract tests |
| frontend | npm ci; frontend contract checks; Vite build |
| docker-integration | Validate canonical/derived Compose; build eleven images; start isolated nineteen-container stack; execute canonical integration; owned cleanup |

The exact Python entry point is `python tools/verify_foundation.py`. Docker entry point is `python tools/verify_ci.py`: pull requests add `--smoke` (11 cases), other triggers run all 48 cases. Tests use generated credentials and schema-only synthetic data, not historical dumps/private fixtures or Node backend services. The temporary Compose names and volumes are UUID-owned; canonical external volumes are never mounted.

Dependencies use the committed Python lock files and frontend package-lock. Only JUnit XML and a non-sensitive `result.json` are uploaded, for seven days. Environment files, resolved Compose config, SQL dumps, raw private logs, and database snapshots are excluded. Remote GitHub runner success must be confirmed by an actual workflow run; a local PASS does not establish it.

The Python quality checkout includes full Git history because contract tests read the recorded baseline commit with `git show`. That historical source is a contract oracle; it is not executed as a Node backend. Disposable MySQL instances use smaller buffer/redo settings to fit CI resources; canonical database resource settings remain unchanged. All eight databases have TCP `SELECT 1` healthchecks so Compose waits for fresh initialization to finish; frontend has an HTTP healthcheck.

## GHCR images

`.github/workflows/docker-publish.yml` first invokes CI, then builds the ten backend images and frontend. Matrix contexts are `api-gateway`, the nine `*-service` directories, and `do-cu-frontend`. Matrix parallelism is limited to three; caches are scoped per service.

Version tag pushes matching `vMAJOR.MINOR.PATCH` (optional prerelease suffix) enable publication. A manual dispatch defaults to **publish=false**, so it builds without login/push. Explicit manual publication is restricted to `main`, `develop`, or a valid version tag. Invalid version tags are rejected by shell validation.

| Image | Context |
|---|---|
| ghcr.io/vjettejv/hethongmuabandocu-api-gateway | api-gateway |
| ghcr.io/vjettejv/hethongmuabandocu-auth-service | auth-service |
| ghcr.io/vjettejv/hethongmuabandocu-user-service | user-service |
| ghcr.io/vjettejv/hethongmuabandocu-post-service | post-service |
| ghcr.io/vjettejv/hethongmuabandocu-category-service | category-service |
| ghcr.io/vjettejv/hethongmuabandocu-message-service | message-service |
| ghcr.io/vjettejv/hethongmuabandocu-notification-service | notification-service |
| ghcr.io/vjettejv/hethongmuabandocu-review-service | review-service |
| ghcr.io/vjettejv/hethongmuabandocu-search-service | search-service |
| ghcr.io/vjettejv/hethongmuabandocu-favorite-service | favorite-service |
| ghcr.io/vjettejv/hethongmuabandocu-frontend | do-cu-frontend |

Image names derive from the repository in lowercase. Tags include the exact version reference and `sha-<full commit SHA>`; `latest` is emitted only for stable version-tag releases, not prereleases or branch dispatches. Publishing uses the built-in `GITHUB_TOKEN` and `packages: write` only on the image job; no PAT/registry password is embedded. See [GitHub's official publishing guide](https://docs.github.com/en/actions/tutorials/publish-packages/publish-docker-images) and [Docker's official Actions guide](https://docs.docker.com/build/ci/github-actions/).

## Release and operational boundaries

This config builds GHCR artifacts; it does not deploy them. No AWS/Kubernetes/cloud provisioning, SSH production rollout, release creation, tag creation, or branch modification is included. Existing Compose remains the local runtime and continues to build from source. Credentials/database volumes are not rotated or migrated as part of CI.

Before deliberately enabling a remote release, review and commit the intended changes, observe actual GitHub CI results, and supply a valid version tag through the repository's own authorized release process. Those actions are outside the work performed in this phase.

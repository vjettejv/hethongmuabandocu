param([switch]$Canonical)
$ErrorActionPreference = 'Stop'
$phase7Root = Split-Path -Parent $PSScriptRoot
Push-Location $phase7Root
$phase7Stack = @('-f','docker-compose.yml')
# -Canonical is retained for CLI compatibility; root Compose is always canonical.
try {
    & .\.venv\Scripts\python.exe tools/prepare_phase7_tests.py
    if ($LASTEXITCODE -ne 0) { throw 'Owned Search schema preparation failed' }
    docker compose @phase7Stack -f docker-compose.phase7.e2e.yml config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Invalid E2E configuration' }
    try {
        docker compose @phase7Stack -f docker-compose.phase7.e2e.yml up -d --no-deps --no-build search-service
        if ($LASTEXITCODE -ne 0) { throw 'Search test switch failed' }
        & .\.venv\Scripts\python.exe tools/prepare_phase7_tests.py --ready
        if ($LASTEXITCODE -ne 0) { throw 'Search not ready' }
        $env:PHASE7_TEST = '1'
        & .\.venv\Scripts\python.exe -u -m pytest -c integration-tests/phase7/pytest.ini integration-tests/phase7 -q
        if ($LASTEXITCODE -ne 0) { throw 'Phase 7 integration failed' }
    } finally {
        docker compose @phase7Stack up -d --no-deps --no-build search-service
        if ($LASTEXITCODE -ne 0) { throw 'Canonical Search restoration failed' }
        & .\.venv\Scripts\python.exe tools/prepare_phase7_tests.py --ready
        if ($LASTEXITCODE -ne 0) { throw 'Restored Search not ready' }
    }
} finally { Pop-Location }

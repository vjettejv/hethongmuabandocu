param([ValidateSet(2,3,4,5,6)][int]$Phase)
$ErrorActionPreference = 'Stop'
# Private root .env or deployment environment is validated by Compose.
& .\.venv\Scripts\python.exe tools/legacy_reference.py --export .artifacts/phase7/legacy
if ($LASTEXITCODE -ne 0) { throw 'Immutable reference export failed' }
$phase6Stack = @('-f','docker-compose.yml')
$phase6Extras = @('-f',"docker-compose.phase$Phase.test.yml")
if ($Phase -eq 3) { $phase6Extras = @('-f','docker-compose.phase2.test.yml') + $phase6Extras }
if ($Phase -eq 4) { $phase6Extras += @('-f','docker-compose.phase5.regression.yml') }
$phase6Extras += @('-f','docker-compose.phase6.regression.yml','--profile',"phase$Phase-test")
$phase6Services = switch ($Phase) {
    2 { @('auth-reference','auth-candidate','user-test','notification-test','proxy-fixture','gateway-probe') }
    3 { @('phase3-search-fixture','user-reference','user-candidate','category-reference',
          'category-candidate','message-cross','post-cross','gateway-phase3-probe') }
    4 { @('post-reference','post-candidate','search-phase4-node','search-phase4-python',
          'message-phase4-node','message-phase4-python','dependencies-node','dependencies-python',
          'favorite-phase4','gateway-phase4') }
    5 { @('favorite-phase5-node','favorite-phase5-python','review-phase5-node','review-phase5-python',
          'search-phase5-node','search-phase5-python','post-phase5','message-phase5',
          'dependencies-phase5','gateway-phase5') }
    6 { @('message-phase6-node','dependencies-phase6-node','notification-phase6-node',
          'notification-phase6-node-production-mock','notification-phase6-node-missing-user',
          'notification-phase6-node-smtp','message-phase6-python','dependencies-phase6-python',
          'notification-phase6-python','notification-phase6-python-production-mock',
          'notification-phase6-python-missing-user','notification-phase6-python-smtp',
          'auth-phase6','user-phase6','search-phase6','post-phase6','gateway-phase6','smtp-phase6') }
}
$phase6Candidate = switch ($Phase) {
    2 { 'notification-test' }; 3 { 'message-cross' }
    4 { 'message-phase4-python' }; 5 { 'message-phase5' }
    6 { 'message-phase6-python' }
}
try {
    docker compose @phase6Stack @phase6Extras config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'Invalid regression Compose configuration' }
    # Canonical cold restart replaces the network ID. Recreate only disposable
    # fixtures so stopped containers cannot retain the removed network identity.
    docker compose @phase6Stack @phase6Extras up -d --force-recreate --no-deps --no-build @phase6Services
    if ($LASTEXITCODE -ne 0) { throw 'Regression fixtures failed to start' }
    $phase6Identifier = (& docker ps -q --filter "label=com.docker.compose.service=$phase6Candidate")
    $phase6Expected = if ($Phase -eq 2) { 'kientrucpm-notification-python-phase6' } else { 'kientrucpm-message-python-phase6' }
    if ((& docker inspect $phase6Identifier --format '{{.Config.Image}}').Trim() -ne $phase6Expected) {
        throw 'Regression candidate is not the Phase 6 Python image'
    }
    if ($Phase -eq 2 -and ((& docker inspect message-service --format '{{.Config.Image}}').Trim() -ne 'kientrucpm-message-python-phase6')) {
        throw 'Phase 2 Socket.IO regression must use canonical Python Message'
    }
    Start-Sleep -Seconds 3
    Set-Item -LiteralPath "Env:PHASE${Phase}_TEST" -Value '1'
    Write-Output "Verified Phase $Phase candidate image: $phase6Expected"
    & .\.venv\Scripts\python.exe -u -m pytest -c "integration-tests/phase$Phase/pytest.ini" "integration-tests/phase$Phase" -q
    if ($LASTEXITCODE -ne 0) { throw "Phase $Phase regression failed" }
} finally {
    docker compose @phase6Stack @phase6Extras stop @phase6Services
    if ($LASTEXITCODE -ne 0) { throw 'Could not stop regression fixtures' }
}

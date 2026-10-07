# Phase 2 file manifest

Created files: 32. Modified Phase 1 files: 21.

Compared with the 379-file snapshot captured before Phase 2.

## Created

```text
api-gateway/app/proxy.py
api-gateway/tests/test_proxy.py
auth-service/authentication/exceptions.py
auth-service/authentication/models.py
auth-service/authentication/selectors.py
auth-service/authentication/serializers.py
auth-service/authentication/services/__init__.py
auth-service/authentication/services/clients.py
auth-service/authentication/services/login.py
auth-service/authentication/services/otp.py
auth-service/authentication/services/passwords.py
auth-service/authentication/services/registration.py
auth-service/authentication/services/tokens.py
auth-service/authentication/urls.py
auth-service/authentication/views.py
auth-service/tests/test_auth.py
contracts/auth/phase-2.json
docker-compose.phase2.rollback.yml
docker-compose.phase2.test.yml
docker-compose.phase2.yml
docs/migration/phase-2-files.md
docs/migration/phase-2-implementation-report.md
docs/migration/phase-2.md
integration-tests/phase2/conftest.py
integration-tests/phase2/pytest.ini
integration-tests/phase2/test_auth_parity.py
integration-tests/phase2/test_gateway_transport.py
tools/prepare_phase2_tests.py
tools/runtime/legacy-schema-guard.cjs
tools/runtime/node-reference-preload.cjs
tools/runtime/proxy-fixture.cjs
tools/verify_phase2_runtime.py
```

## Modified

```text
.env.python.example
api-gateway/.env.example
api-gateway/app/logging_config.py
api-gateway/app/main.py
api-gateway/app/middleware.py
api-gateway/app/settings.py
api-gateway/requirements.lock.txt
api-gateway/requirements.txt
api-gateway/tests/test_health.py
auth-service/.env.example
auth-service/common/logging.py
auth-service/common/middleware.py
auth-service/config/settings.py
auth-service/config/urls.py
auth-service/requirements.lock.txt
auth-service/requirements.txt
auth-service/tests/test_health.py
contracts/README.md
docker-compose.python.yml
requirements-dev.lock.txt
tools/verify_foundation.py
```

Node source/manifests/legacy Dockerfiles, frontend, baseline Compose, seeds and
HUONG_DAN_TRIEN_KHAI.md remain unchanged. No files were deleted or staged.


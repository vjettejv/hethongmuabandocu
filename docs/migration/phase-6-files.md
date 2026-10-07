# Phase 6 file manifest

Baseline 534 files; 518 unchanged; 16 modified; 43 created.

## Created

```text
contracts/messages/phase-6.json
contracts/notifications/phase-6.json
docker-compose.phase6.e2e.yml
docker-compose.phase6.regression.yml
docker-compose.phase6.rollback.yml
docker-compose.phase6.test.yml
docker-compose.phase6.yml
docs/migration/phase-6-files.md
docs/migration/phase-6-implementation-report.md
docs/migration/phase-6-runbook.md
integration-tests/phase6/conftest.py
integration-tests/phase6/pytest.ini
integration-tests/phase6/test_email_parity.py
integration-tests/phase6/test_message_parity.py
integration-tests/phase6/test_realtime.py
message-service/messaging/asgi.py
message-service/messaging/authentication.py
message-service/messaging/clients.py
message-service/messaging/exceptions.py
message-service/messaging/http.py
message-service/messaging/models.py
message-service/messaging/realtime.py
message-service/messaging/selectors.py
message-service/messaging/serializers.py
message-service/messaging/services.py
message-service/messaging/urls.py
message-service/messaging/views.py
message-service/tests/test_messaging.py
notification-service/email_delivery/exceptions.py
notification-service/email_delivery/http.py
notification-service/email_delivery/mailer.py
notification-service/email_delivery/services.py
notification-service/email_delivery/urls.py
notification-service/email_delivery/views.py
notification-service/tests/test_email.py
tools/phase6_socket.py
tools/prepare_phase6_tests.py
tools/runtime/phase6-dependencies.cjs
tools/runtime/phase6-smtp.cjs
tools/runtime/phase6-socket-client.cjs
tools/verify_phase6_regressions.ps1
tools/verify_phase6_runtime.py
tools/verify_phase6_state.py
```

## Modified

```text
message-service/.env.example
message-service/Dockerfile.python
message-service/common/logging.py
message-service/config/asgi.py
message-service/config/settings.py
message-service/config/urls.py
message-service/requirements.lock.txt
message-service/requirements.txt
message-service/tests/test_health.py
notification-service/.env.example
notification-service/common/logging.py
notification-service/config/settings.py
notification-service/config/urls.py
notification-service/tests/test_health.py
requirements-dev.lock.txt
requirements-dev.txt
```

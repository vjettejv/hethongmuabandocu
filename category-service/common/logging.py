import json
import logging
from datetime import UTC, datetime


class JsonFormatter(logging.Formatter):
    def __init__(self, service):
        super().__init__()
        self.service = service

    def format(self, record):
        # Never serialize request bodies, query strings, headers or exception details.
        return json.dumps(
            {
                "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
                "level": record.levelname,
                "service": self.service,
                "request_id": getattr(record, "request_id", "-"),
                "method": getattr(record, "method", "-"),
                "path": getattr(record, "path", "-"),
                "status_code": getattr(record, "status_code", None),
                "duration_ms": getattr(record, "duration_ms", None),
            }
        )


def build_logging(service):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"json": {"()": JsonFormatter, "service": service}},
        "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
        "root": {"handlers": ["console"], "level": "INFO"},
        "loggers": {
            "django.request": {"handlers": ["console"], "level": "CRITICAL", "propagate": False},
            "django.server": {"handlers": ["console"], "level": "CRITICAL", "propagate": False},
        },
    }

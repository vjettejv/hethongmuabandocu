import logging
import re
from time import perf_counter
from uuid import uuid4

from django.conf import settings
from django.http import HttpResponse
from django.utils.cache import patch_vary_headers

logger = logging.getLogger("foundation.request")
REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z")


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        incoming = request.headers.get("X-Request-ID", "")
        request.request_id = incoming if REQUEST_ID_PATTERN.fullmatch(incoming) else str(uuid4())
        start = perf_counter()
        origin = request.headers.get("Origin")
        allowed = origin in settings.CORS_ALLOWED_ORIGINS
        if request.method == "OPTIONS" and request.headers.get("Access-Control-Request-Method"):
            response = HttpResponse(status=204 if allowed else 403)
            if allowed:
                response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
                response["Access-Control-Allow-Headers"] = (
                    "Content-Type, Authorization, X-Request-ID"
                )
        else:
            response = self.get_response(request)
        response["X-Request-ID"] = request.request_id
        if origin:
            patch_vary_headers(response, ["Origin"])
        if allowed:
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Expose-Headers"] = "X-Request-ID"
        logger.info(
            "request completed",
            extra={
                "request_id": request.request_id,
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": round((perf_counter() - start) * 1000, 3),
            },
        )
        return response

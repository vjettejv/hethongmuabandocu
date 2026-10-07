import logging
from concurrent.futures import ThreadPoolExecutor
from itertools import islice

import httpx
from django.conf import settings

LOGGER = logging.getLogger("favorites.dependencies")


def hydrate(post_ids, request_id):
    identifiers = iter(post_ids)
    result = []
    with httpx.Client(
        timeout=settings.DEPENDENCY_TIMEOUT, trust_env=False, limits=httpx.Limits(max_connections=8)
    ) as client:

        def fetch(identifier):
            try:
                response = client.get(
                    settings.SERVICE_URLS["POST_SERVICE_URL"].rstrip("/") + f"/{identifier}",
                    headers={"X-Request-ID": request_id},
                )
                LOGGER.info(
                    "dependency response",
                    extra={
                        "request_id": request_id,
                        "dependency": "post",
                        "status_code": response.status_code,
                    },
                )
                if response.is_success:
                    return response.json()
            except (httpx.HTTPError, ValueError):
                LOGGER.warning(
                    "dependency failure",
                    extra={
                        "request_id": request_id,
                        "dependency": "post",
                        "failure": "unavailable",
                    },
                )
            return None

        with ThreadPoolExecutor(max_workers=8, thread_name_prefix="favorite-post") as executor:
            while batch := list(islice(identifiers, 8)):
                result.extend(value for value in executor.map(fetch, batch) if value is not None)
    return result

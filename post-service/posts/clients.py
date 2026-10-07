"""HTTP-only dependencies; bounded in-process best effort, without durable delivery."""

import logging
from concurrent.futures import ThreadPoolExecutor
from threading import BoundedSemaphore

import httpx
from django.conf import settings

LOGGER = logging.getLogger("posts.dependencies")
EXECUTOR = ThreadPoolExecutor(max_workers=4, thread_name_prefix="post-http")
SLOTS = BoundedSemaphore(64)


def failure(dependency, request_id, reason, status=None):
    LOGGER.warning(
        "dependency failure",
        extra={
            "dependency": dependency,
            "request_id": request_id,
            "failure": reason,
            "status_code": status,
        },
    )


def exchange(dependency, method, suffix, request_id, payload=None):
    url = settings.SERVICE_URLS.get(dependency + "_SERVICE_URL", "").rstrip("/")
    if not url:
        failure(dependency, request_id, "unconfigured")
        return None
    try:
        with httpx.Client(timeout=settings.DEPENDENCY_TIMEOUT, trust_env=False) as client:
            response = client.request(
                method, url + suffix, json=payload, headers={"X-Request-ID": request_id}
            )
        if not response.is_success:
            failure(dependency, request_id, "http_status", response.status_code)
            return None
        return response.json()
    except (httpx.HTTPError, ValueError):
        failure(dependency, request_id, "transport_or_json")
        return None


def categories(request_id):
    result = exchange("CATEGORY", "GET", "", request_id)
    rows = result.get("data", []) if isinstance(result, dict) else result
    if not isinstance(rows, list):
        return {}
    return {str(row["id"]): row for row in rows if isinstance(row, dict) and "id" in row}


def dispatch(dependency, suffix, payload, request_id):
    if not SLOTS.acquire(blocking=False):
        failure(dependency, request_id, "capacity")
        return

    def send():
        try:
            exchange(dependency, "POST", suffix, request_id, payload)
        finally:
            SLOTS.release()

    try:
        EXECUTOR.submit(send)
    except RuntimeError:
        SLOTS.release()
        failure(dependency, request_id, "shutdown")


def sync_search(raw, category_map, request_id, images=None):
    images = raw.get("Images", images or [])
    payload = {
        key: raw[key]
        for key in ("title", "description", "price", "categoryId", "status")
        if key in raw
    }
    payload.update(
        postId=raw["id"],
        imageUrl=images[0]["imageUrl"] if images else None,
        categoryName=category_map.get(str(raw["categoryId"]), {}).get("name", "Đang cập nhật"),
    )
    dispatch("SEARCH", "/sync", payload, request_id)


def notify(post, request_id):
    approved = post.status == "approved"
    dispatch(
        "MESSAGE",
        "/notifications",
        {
            "receiverId": post.userId,
            "title": "Bài viết đã được duyệt" if approved else "Bài viết bị từ chối",
            "message": f'Bài viết "{post.title}" của bạn '
            + ("đã được hiển thị trên chợ." if approved else "đã bị từ chối duyệt."),
        },
        request_id,
    )

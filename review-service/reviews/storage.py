import re
import time
from pathlib import Path

from django.conf import settings

from reviews.exceptions import LegacyError


def save_files(files):
    root = Path(settings.UPLOAD_ROOT)
    root.mkdir(parents=True, exist_ok=True)
    owned = []
    try:
        for upload in files:
            name = re.sub(r"[\x00-\x1f\x7f]", "", upload.name.replace("\\", "/").split("/")[-1])
            name = name or "upload"
            tick = int(time.time() * 1000)
            while True:
                target = root / f"{tick}-{name}"
                if len("/uploads/" + target.name) > 255:
                    raise LegacyError("Invalid upload filename")
                try:
                    stream = target.open("xb")
                    break
                except FileExistsError:
                    tick += 1
            owned.append(target)
            with stream:
                for chunk in upload.chunks():
                    stream.write(chunk)
        return owned
    except Exception:
        cleanup(owned)
        raise


def cleanup(owned):
    for target in owned:
        target.unlink(missing_ok=True)


def unlink_image(url, review_id, request_id):
    """Only unlink this row's exact contained file, with shared-reference checks."""
    import logging

    import httpx

    from .models import Review

    logger = logging.getLogger("reviews.storage")
    if not url or not url.startswith("/uploads/"):
        return
    name = url.removeprefix("/uploads/")
    root = Path(settings.UPLOAD_ROOT).resolve()
    target = root / name
    if (
        not name
        or Path(name).name != name
        or name.startswith(".")
        or target.is_symlink()
        or not target.resolve().is_relative_to(root)
    ):
        return
    if Review.objects.filter(imageUrl=url).exclude(pk=review_id).exists():
        return
    try:
        response = httpx.get(
            settings.SERVICE_URLS["POST_SERVICE_URL"].rstrip("/") + "/",
            headers={"X-Request-ID": request_id},
            timeout=settings.DEPENDENCY_TIMEOUT,
            trust_env=False,
        )
        response.raise_for_status()
        posts = response.json()
        if not isinstance(posts, list) or any(
            image.get("imageUrl") == url for post in posts for image in post.get("Images", [])
        ):
            return
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        logger.warning(
            "file ownership check unavailable",
            extra={
                "request_id": request_id,
                "dependency": "post",
                "failure": "ownership-unverified",
            },
        )
        return
    target.unlink(missing_ok=True)

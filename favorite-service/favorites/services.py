from django.db import transaction
from django.utils import timezone

from .exceptions import LegacyError
from .models import Favorite


def toggle(user_id, data):
    if "postId" not in data:
        raise LegacyError('WHERE parameter "postId" has invalid "undefined" value')
    missing = [
        key for key, value in (("userId", user_id), ("postId", data.get("postId"))) if value is None
    ]
    if missing:
        raise LegacyError(
            ",\n".join(f"notNull Violation: Favorite.{key} cannot be null" for key in missing)
        )
    with transaction.atomic():
        existing = (
            Favorite.objects.select_for_update()
            .filter(userId=user_id, postId=data["postId"])
            .first()
        )
        if existing:
            existing.delete()
            return {"message": "Removed from favorites", "isFavorited": False}
        now = timezone.now()
        Favorite.objects.create(userId=user_id, postId=data["postId"], createdAt=now, updatedAt=now)
        return {"message": "Added to favorites", "isFavorited": True}

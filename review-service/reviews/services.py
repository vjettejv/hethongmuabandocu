import logging
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from . import storage
from .exceptions import LegacyError
from .models import Review
from .serializers import response, truthy


def rating_value(value):
    try:
        number = float(value)
        if number < 1:
            raise LegacyError("Validation error: Validation min on rating failed")
        if number > 5:
            raise LegacyError("Validation error: Validation max on rating failed")
        # Sequelize validates the numeric 1..5 range; MySQL rounds INTEGER writes.
        return int(Decimal(str(number)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    except (ValueError, TypeError, OverflowError) as error:
        raise LegacyError("Invalid review data") from error


def create(data, file):
    missing = [key for key in ("reviewerId", "revieweeId", "rating") if data.get(key) is None]
    if missing:
        raise LegacyError(
            ",\n".join(f"notNull Violation: Review.{key} cannot be null" for key in missing)
        )
    rating = rating_value(data["rating"])
    owned = storage.save_files([file] if file else [])
    try:
        now = timezone.now()
        with transaction.atomic():
            review = Review.objects.create(
                reviewerId=data["reviewerId"],
                revieweeId=data["revieweeId"],
                postId=data.get("postId"),
                rating=rating,
                comment=data.get("comment"),
                imageUrl="/uploads/" + owned[0].name if owned else None,
                createdAt=now,
                updatedAt=now,
            )
        return response(review, data, create=True)
    except Exception:
        storage.cleanup(owned)
        raise


def update(identifier, data, file, request_id):
    owned = []
    try:
        with transaction.atomic():
            review = (
                Review.objects.select_for_update()
                .extra(where=["`id` = %s"], params=[identifier])
                .first()
            )
            if review is None:
                raise LegacyError("Review not found", 404)
            changed = []
            for key in ("rating", "comment"):
                if truthy(data.get(key)):
                    value = rating_value(data[key]) if key == "rating" else data[key]
                    if data[key] != getattr(review, key):
                        changed.append(key)
                    setattr(review, key, value)
            old = review.imageUrl
            if file:
                owned = storage.save_files([file])
                review.imageUrl = "/uploads/" + owned[0].name
                changed.append("imageUrl")
            if changed:
                review.updatedAt = timezone.now()
                review.save(update_fields=[*changed, "updatedAt"])
    except Exception:
        storage.cleanup(owned)
        raise
    if file:
        unlink_after_commit(old, review.id, request_id)
    return response(review, data)


def unlink_after_commit(url, identifier, request_id):
    # A failed ownership probe/unlink must not remove the committed replacement.
    try:
        storage.unlink_image(url, identifier, request_id)
    except Exception as error:
        logging.getLogger("reviews.storage").warning(
            "file cleanup deferred",
            extra={"request_id": request_id, "failure": type(error).__name__},
        )


def delete(identifier, request_id):
    with transaction.atomic():
        review = (
            Review.objects.select_for_update()
            .extra(where=["`id` = %s"], params=[identifier])
            .first()
        )
        if review is None:
            raise LegacyError("Review not found", 404)
        identifier, url = review.id, review.imageUrl
        review.delete()
    unlink_after_commit(url, identifier, request_id)
    return {"message": "Review deleted successfully"}

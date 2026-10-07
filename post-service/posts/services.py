from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from posts import clients, storage
from posts.exceptions import PostError
from posts.models import Image, Post
from posts.serializers import image_response, raw_response


def create(user_id, data, files, request_id):
    missing = [
        key
        for key in ("userId", "categoryId", "title", "price")
        if (user_id if key == "userId" else data.get(key)) is None
    ]
    if missing:
        raise PostError(
            ",\n".join(f"notNull Violation: Post.{key} cannot be null" for key in missing)
        )
    try:
        price = Decimal(str(data["price"]))
        if not price.is_finite():
            raise InvalidOperation
        price = price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        category_id = int(data["categoryId"])
        user_id = int(user_id)
    except (ValueError, TypeError, InvalidOperation) as error:
        raise PostError("Invalid post data") from error
    owned = []
    try:
        owned = storage.save_files(files)
        now = timezone.now()
        with transaction.atomic():
            post = Post.objects.create(
                userId=user_id,
                categoryId=category_id,
                title=data["title"],
                description=data.get("description"),
                price=price,
                condition=data.get("condition"),
                createdAt=now,
                updatedAt=now,
            )
            images = Image.objects.bulk_create(
                [
                    Image(post=post, imageUrl="/uploads/" + path.name, createdAt=now, updatedAt=now)
                    for path in owned
                ]
            )
    except Exception:
        storage.cleanup(owned)
        raise
    raw = raw_response(post, original=data)
    clients.sync_search(
        raw, clients.categories(request_id), request_id, [image_response(image) for image in images]
    )
    return raw


def owner_delete(identifier, user_id, request_id):
    try:
        with transaction.atomic():
            post = Post.objects.select_for_update().filter(pk=identifier, userId=user_id).first()
            if post is None:
                raise PostError("Post not found or unauthorized", 404)
            raw = raw_response(post)
            Image.objects.filter(post_id=post.id).delete()
            post.delete()
    except (ValueError, TypeError) as error:
        raise PostError("Post not found or unauthorized", 404) from error
    raw["status"] = "deleted"
    clients.sync_search(raw, clients.categories(request_id), request_id)
    return {"message": "Deleted successfully"}


def moderate(identifier, data, request_id):
    status = data.get("status")
    if not isinstance(status, str) or status not in {Post.Status.APPROVED, Post.Status.REJECTED}:
        raise PostError("Status must be approved or rejected", 400)
    try:
        with transaction.atomic():
            post = (
                Post.objects.select_for_update()
                .prefetch_related("Images")
                .filter(pk=identifier)
                .first()
            )
            if post is None:
                raise PostError("Not found", 404)
            old = post.status
            if old != status:
                post.status = status
                post.updatedAt = timezone.now()
                post.save(update_fields=["status", "updatedAt"])
            raw = raw_response(post, images=post.Images.all())
    except (ValueError, TypeError) as error:
        raise PostError("Not found", 404) from error
    clients.sync_search(raw, clients.categories(request_id), request_id)
    if old != post.status and post.status in {"approved", "rejected"}:
        clients.notify(post, request_id)
    return raw


def admin_delete(identifier):
    try:
        with transaction.atomic():
            Image.objects.filter(post_id=identifier).delete()
            Post.objects.filter(pk=identifier).delete()
    except (ValueError, TypeError):
        pass
    return {"message": "Deleted"}

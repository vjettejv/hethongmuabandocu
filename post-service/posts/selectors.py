import re
from urllib.parse import unquote

from posts.models import Image, Post
from posts.serializers import FIELDS


def legacy_parameters(request):
    # Express qs preserves a parameter verbatim when decodeURIComponent fails.
    # Django replaces invalid UTF-8, which changes SQL LIKE wildcard searches.
    def decode(value):
        if re.search(r"%(?![0-9a-fA-F]{2})", value):
            return value
        try:
            return unquote(value.replace("+", " "), encoding="utf-8", errors="strict")
        except UnicodeDecodeError:
            return value

    parameters = request.query_params.dict()
    for pair in request.META.get("QUERY_STRING", "").split("&"):
        key, _, value = pair.partition("=")
        key = decode(key)
        if key in {"keyword", "status", "categoryId"}:
            parameters[key] = decode(value)
    return parameters


def list_posts(parameters=None, user_id=None):
    query = Post.objects.all()
    if user_id is not None:
        query = query.filter(userId=user_id)
    for key in ("categoryId", "status"):
        if parameters and parameters.get(key):
            query = query.filter(**{key: parameters[key]})
    if parameters and parameters.get("keyword"):
        # Preserve Sequelize LIKE wildcards; Django contains would escape % and _.
        query = query.extra(
            where=["`posts`.`title` LIKE %s"], params=["%" + parameters["keyword"] + "%"]
        )
    # Match Sequelize's single LEFT JOIN + createdAt DESC. Prefetching images in
    # a second query changes the observed image order of the legacy list query.
    image_fields = ("id", "post_id", "imageUrl", "createdAt", "updatedAt")
    rows = query.order_by("-createdAt").values(
        *FIELDS, *("Images__" + field for field in image_fields)
    )
    grouped = {}
    for row in rows:
        if row["id"] not in grouped:
            record = Post(**{field: row[field] for field in FIELDS})
            record._prefetched_objects_cache = {"Images": []}
            grouped[row["id"]] = record
        if row["Images__id"] is not None:
            grouped[row["id"]]._prefetched_objects_cache["Images"].append(
                Image(**{field: row["Images__" + field] for field in image_fields})
            )
    return list(grouped.values())


def detail(identifier):
    try:
        return Post.objects.prefetch_related("Images").filter(pk=identifier).first()
    except (ValueError, TypeError):
        return None

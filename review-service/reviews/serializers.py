FIELDS = (
    "id",
    "reviewerId",
    "revieweeId",
    "postId",
    "rating",
    "comment",
    "imageUrl",
    "createdAt",
    "updatedAt",
)


def response(review, original=None, create=False):
    result = {key: getattr(review, key) for key in FIELDS}
    for key in ("createdAt", "updatedAt"):
        result[key] = result[key].isoformat(timespec="milliseconds").replace("+00:00", "Z")
    if original is not None:
        for key in (
            ("reviewerId", "revieweeId", "postId", "rating", "comment")
            if create
            else ("rating", "comment")
        ):
            if key in original and (create or truthy(original[key])):
                result[key] = original[key]
            elif create:
                result.pop(key, None)
    return result


def truthy(value):
    return value is not None and value is not False and value != 0 and value != ""

FIELDS = (
    "postId",
    "title",
    "description",
    "price",
    "categoryId",
    "imageUrl",
    "categoryName",
    "status",
    "createdAt",
    "updatedAt",
)


def response(row):
    result = {field: getattr(row, field) for field in FIELDS}
    result["price"] = format(row.price, ".2f") if row.price is not None else None
    for field in ("createdAt", "updatedAt"):
        result[field] = result[field].isoformat(timespec="milliseconds").replace("+00:00", "Z")
    result["id"] = row.postId
    return result

FIELDS = (
    "id",
    "userId",
    "categoryId",
    "title",
    "description",
    "price",
    "status",
    "condition",
    "createdAt",
    "updatedAt",
)


def timestamp(value):
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def image_response(image):
    return {
        "id": image.id,
        "postId": image.post_id,
        "imageUrl": image.imageUrl,
        "createdAt": timestamp(image.createdAt),
        "updatedAt": timestamp(image.updatedAt),
    }


def raw_response(post, *, images=None, original=None):
    result = {field: getattr(post, field) for field in FIELDS}
    result.update(
        price=format(post.price, ".2f"),
        createdAt=timestamp(post.createdAt),
        updatedAt=timestamp(post.updatedAt),
    )
    if original is not None:
        # Sequelize create retains input types and omits undefined optional values.
        for field in ("categoryId", "price", "description", "condition"):
            if field in original:
                result[field] = original[field]
            else:
                result.pop(field, None)
    if images is not None:
        result["Images"] = [image_response(image) for image in images]
    return result


def formatted_response(post, categories):
    result = raw_response(post, images=post.Images.all())
    result["price"] = float(post.price) if post.price else 0
    result["Category"] = categories.get(
        str(post.categoryId),
        {
            "id": post.categoryId,
            "name": "Đang cập nhật",
        },
    )
    return result

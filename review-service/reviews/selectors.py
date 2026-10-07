from .models import Review


def list_reviews(user_id, parameters):
    query = Review.objects.extra(where=["`revieweeId` = %s"], params=[user_id])
    if parameters.get("rating"):
        query = query.extra(where=["`rating` = %s"], params=[parameters["rating"]])
    if parameters.get("hasImage") in {"true", "false"}:
        query = query.filter(imageUrl__isnull=parameters["hasImage"] == "false")
    return query.order_by("-createdAt")

from .models import Favorite


def rows(user_id):
    return Favorite.objects.filter(userId=user_id).order_by()


def check(user_id, post_id):
    return rows(user_id).extra(where=["`postId` = %s"], params=[post_id]).exists()

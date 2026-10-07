from django.db.models import Q

from . import clients
from .models import Message, Notification
from .serializers import projection


def history(user_id, contact_id):
    # SQL comparisons retain MySQL's legacy string-to-integer lookup semantics.
    rows = Message.objects.extra(
        where=["(senderId=%s AND receiverId=%s) OR (senderId=%s AND receiverId=%s)"],
        params=[user_id, contact_id, contact_id, user_id],
    ).order_by("createdAt")
    return [projection(row) for row in rows]


def contacts(user_id, request_id):
    latest = {}
    for row in Message.objects.filter(Q(senderId=user_id) | Q(receiverId=user_id)).order_by(
        "-createdAt"
    ):
        contact_id = (
            row.receiverId
            if type(row.senderId) is type(user_id) and row.senderId == user_id
            else row.senderId
        )
        latest.setdefault(contact_id, {"id": contact_id, "lastMessage": projection(row)})
    # Object.values in Node enumerates integer property keys in ascending order.
    keys = sorted(key for key in latest if 0 <= key < 4294967295)
    keys += [key for key in latest if key not in keys]
    result = []
    for key in keys:
        item = latest[key]
        item["user"] = clients.user(key, request_id)
        result.append(item)
    return result


def notifications(user_id):
    return [
        projection(row)
        for row in Notification.objects.filter(userId=user_id).order_by("-createdAt")[:50]
    ]

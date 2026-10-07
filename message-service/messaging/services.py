from django.utils import timezone

from . import clients, realtime
from .exceptions import LegacyError
from .models import Message, Notification
from .serializers import projection


def required(data, names, model):
    missing = [name for name in names if data.get(name) is None]
    if missing:
        raise LegacyError(
            ",\n".join(f"notNull Violation: {model}.{name} cannot be null" for name in missing)
        )
    for name in names:
        if name in {"content", "title", "message"} and isinstance(data.get(name), (list, dict)):
            raise LegacyError(f"string violation: {name} cannot be an array or an object")


def send(sender_id, data, request_id):
    values = {
        "senderId": sender_id,
        "receiverId": data.get("receiverId"),
        "content": data.get("content"),
    }
    required(values, ("senderId", "receiverId", "content"), "Message")
    now = timezone.now()
    row = Message.objects.create(**values, isRead=False, createdAt=now, updatedAt=now)
    payload = projection(row)
    clients.email(data["receiverId"], data["content"], request_id)
    realtime.emit("receive_message", payload, data["receiverId"], request_id)
    return payload


def notify(data, request_id):
    values = {
        "userId": data.get("receiverId"),
        "title": data.get("title"),
        "message": data.get("message"),
    }
    required(values, ("userId", "title", "message"), "Notification")
    now = timezone.now()
    row = Notification.objects.create(
        **values, link=data.get("link"), isRead=False, createdAt=now, updatedAt=now
    )
    if "link" not in data:
        row._omitted_fields = ("link",)
    payload = projection(row)
    realtime.emit("receive_notification", payload, data["receiverId"], request_id)
    return payload


def read_all(user_id):
    Notification.objects.filter(userId=user_id, isRead=False).update(
        isRead=True, updatedAt=timezone.now()
    )
    return {"success": True}

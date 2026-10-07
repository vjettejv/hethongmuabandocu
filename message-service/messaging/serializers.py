MESSAGE_FIELDS = ("id", "senderId", "receiverId", "content", "isRead", "createdAt", "updatedAt")
NOTIFICATION_FIELDS = (
    "id",
    "userId",
    "title",
    "message",
    "isRead",
    "link",
    "createdAt",
    "updatedAt",
)


def projection(row):
    fields = MESSAGE_FIELDS if row._meta.db_table == "messages" else NOTIFICATION_FIELDS
    data = {field: getattr(row, field) for field in fields}
    for field in ("createdAt", "updatedAt"):
        data[field] = data[field].isoformat(timespec="milliseconds").replace("+00:00", "Z")
    for field in getattr(row, "_omitted_fields", ()):
        data.pop(field, None)
    return data

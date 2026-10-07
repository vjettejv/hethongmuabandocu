from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from django.db import connection
from django.utils import timezone

from .exceptions import LegacyError
from .serializers import FIELDS


def sync(data):
    if "title" in data and data["title"] is None:
        raise LegacyError("notNull Violation: SearchIndex.title cannot be null")
    if data.get("postId") is None:
        raise LegacyError("Column 'postId' cannot be null")
    if "title" not in data:
        raise LegacyError("Field 'title' doesn't have a default value")
    values = {
        field: data[field]
        for field in FIELDS
        if field in data and field not in {"createdAt", "updatedAt"}
    }
    if values.get("price") is not None:
        try:
            price = Decimal(str(values["price"]))
            if not price.is_finite():
                raise InvalidOperation
            values["price"] = price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        except (InvalidOperation, ValueError, TypeError) as error:
            raise LegacyError("Invalid search data") from error
    now = timezone.now()
    values.update(createdAt=now, updatedAt=now)
    # Sequelize updates supplied fields and updatedAt on conflict. createdAt is
    # generated only for insertion; omitted optional fields survive an update.
    fields = list(values)
    columns = ",".join(f"`{field}`" for field in fields)
    updates = ",".join(f"`{field}`=VALUES(`{field}`)" for field in fields if field != "createdAt")
    with connection.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO `searchindices` ({columns}) "
            f"VALUES ({','.join(['%s'] * len(fields))}) ON DUPLICATE KEY UPDATE {updates}",
            [
                connection.ops.adapt_datetimefield_value(value)
                if field in {"createdAt", "updatedAt"}
                else value
                for field, value in values.items()
            ],
        )
    return {"message": "Index synced"}

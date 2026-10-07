from django.db import IntegrityError
from django.utils import timezone

from categories.exceptions import CategoryError
from categories.models import Category


def create_category(payload):
    if not isinstance(payload, dict):
        raise CategoryError("Validation error")
    name = payload.get("name")
    description = payload.get("description")
    if name is None:
        raise CategoryError("notNull Violation: Category.name cannot be null")
    if not isinstance(name, str) or (description is not None and not isinstance(description, str)):
        raise CategoryError("Validation error")
    now = timezone.now()
    try:
        category = Category.objects.create(
            name=name, description=description, created_at=now, updated_at=now
        )
        category._description_omitted = "description" not in payload
        return category
    except IntegrityError as error:
        cause = error.__cause__
        if cause and cause.args and cause.args[0] == 1062:
            raise CategoryError("Validation error") from error
        raise

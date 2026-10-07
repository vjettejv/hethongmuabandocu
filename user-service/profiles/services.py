from django.utils import timezone

from profiles.exceptions import ProfileError
from profiles.models import UserProfile
from profiles.selectors import numeric_identity

FIELDS = {"fullName": "full_name", "phone": "phone", "address": "address", "avatar": "avatar"}


def update_profile(auth_id, payload):
    identifier = numeric_identity(auth_id)
    if identifier is None:
        raise ProfileError("Invalid authId")
    if not isinstance(payload, dict):
        raise ProfileError("Invalid profile fields")
    values = {}
    for external, internal in FIELDS.items():
        if external in payload:
            value = payload[external]
            if value is not None and not isinstance(value, str):
                raise ProfileError("Invalid profile fields")
            values[internal] = value
    now = timezone.now()
    profile, created = UserProfile.objects.get_or_create(
        auth_id=identifier,
        defaults={**values, "created_at": now, "updated_at": now},
    )
    if created:
        # Sequelize create returns its in-memory values: undefined fields are omitted,
        # and URL authId is still a decimal string until the next DB lookup.
        profile._omitted_response_fields = {key for key in FIELDS if key not in payload}
        profile._response_auth_id = auth_id
    else:
        changed = [name for name, value in values.items() if getattr(profile, name) != value]
        if changed:
            for name in changed:
                setattr(profile, name, values[name])
            profile.updated_at = now
            profile.save(update_fields=[*changed, "updated_at"])
    return profile

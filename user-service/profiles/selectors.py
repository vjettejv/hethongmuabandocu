from profiles.models import UserProfile


def numeric_identity(value):
    # URL identities refer to Auth IDs, never the profile primary key.
    if isinstance(value, bool):
        return None
    try:
        identifier = int(value)
    except (ValueError, TypeError, OverflowError):
        return None
    if isinstance(value, float) and value != identifier:
        return None
    return identifier if -(2**31) <= identifier < 2**31 else None


def by_auth_id(value):
    identifier = numeric_identity(value)
    if identifier is None:
        return None
    return UserProfile.objects.filter(auth_id=identifier).first()

from django.db.models import Q

from authentication.models import AuthUser


def by_identifier(identifier):
    return AuthUser.objects.filter(Q(username=identifier) | Q(email=identifier)).first()


def for_registration(username, email):
    return AuthUser.objects.filter(Q(username=username) | Q(email=email)).first()


def by_email(email):
    return AuthUser.objects.filter(email=email).first()


def by_id(identifier):
    try:
        return AuthUser.objects.filter(pk=identifier).first()
    except (ValueError, TypeError, OverflowError):
        return None

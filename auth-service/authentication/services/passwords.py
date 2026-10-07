import bcrypt


def password_bytes(password):
    # bcryptjs uses the first 72 UTF-8 bytes, including when truncating a code point.
    return password.encode("utf-8")[:72]


def hash_password(password):
    return bcrypt.hashpw(password_bytes(password), bcrypt.gensalt(rounds=10)).decode("ascii")


def verify_password(password, encoded):
    try:
        return isinstance(password, str) and bcrypt.checkpw(
            password_bytes(password), encoded.encode("ascii")
        )
    except (ValueError, TypeError, UnicodeError, AttributeError):
        return False

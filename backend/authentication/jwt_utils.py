import jwt
import time
from django.conf import settings

def create_access_token(user):
    """
    Tworzy access token JWT o długości życia zdefiniowanej w settings.JWT_ACCESS_TTL.
    """
    return jwt.encode({
        "sub": user,
        "type": "access",
        "exp": int(time.time()) + settings.JWT_ACCESS_TTL
    }, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user):
    """
    Tworzy refresh token JWT o długości życia zdefiniowanej w settings.JWT_REFRESH_TTL.
    """
    return jwt.encode({
        "sub": user,
        "type": "refresh",
        "exp": int(time.time()) + settings.JWT_REFRESH_TTL
    }, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token, expected_type):
    """
    Dekoduje i weryfikuje token JWT.

    Weryfikacja:
    - poprawność podpisu (SECRET_KEY),
    - data wygaśnięcia (exp),
    - typ tokena (access / refresh).
    """
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )

    if payload.get("type") != expected_type:
        raise ValueError("Invalid token type")

    return payload
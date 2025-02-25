from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
import os

ALGORITHM = "HS256"


def create_access_token(*, subject: str | Any, expires_delta: timedelta) -> str:
    """Crea un token de acceso.

    Args:
        subject (str | Any): Sujeto del token.
        expires_delta (timedelta): Duración del token.

    Returns:
        str: Token de acceso.
    """

    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, os.environ["SECRET_KEY"], algorithm=ALGORITHM)
    return encoded_jwt

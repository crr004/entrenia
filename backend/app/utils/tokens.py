from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
import os
from jwt.exceptions import InvalidTokenError

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


def create_password_reset_token(*, email: str) -> str:
    """Crea un token de restablecimiento de contraseña.

    Args:
        email (str): Email del usuario.

    Returns:
        str: Token de restablecimiento de contraseña.
    """

    delta = timedelta(int(os.environ["PASSWORD_RESET_TOKEN_EXPIRE"]))
    now = datetime.now(timezone.utc)
    expire = now + delta
    exp = expire.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        os.environ["SECRET_KEY"],
        algorithm=ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(*, token: str) -> str | None:
    """Crea un token de restablecimiento de contraseña.

    Args:
        token (str): Token de restablecimiento de contraseña.

    Returns:
        str | None: El identificador del usuario (extraído del token) si es válido,
                    o None si el token es inválido.
    """

    try:
        decoded_token = jwt.decode(
            token, os.environ["SECRET_KEY"], algorithms=[ALGORITHM]
        )
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None

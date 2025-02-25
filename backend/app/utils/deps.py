import os
import jwt
from typing import Annotated


from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel import Session

from app.core import db
from app.models.users import User
from app.models.tokens import TokenData
from app.utils import tokens
from app.crud.users import get_user_by_id

API_PREFIX = os.environ["API_PREFIX"]
TOKEN_URL = f"{API_PREFIX}/login/access-token"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)

SessionDep = Annotated[Session, Depends(db.get_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(session: SessionDep, token: TokenDep):
    """Obtiene el usuario actual a partir del token JWT.

    Args:
        session (Session): Sesión de la base de datos.
        token (str): Token JWT.

    Raises:
        HTTPException: Error HTTP.

    Returns:
        User: Usuario actual.
    """
    try:
        data = jwt.decode(token, os.environ["SECRET_KEY"], algorithms=tokens.ALGORITHM)
        token_data = TokenData(**data)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    user = get_user_by_id(session=session, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    if not user.is_verified:
        raise HTTPException(status_code=400, detail="Unverified user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_superuser(current_user: CurrentUser):
    """Obtiene el usuario actual si es un superusuario.

    Args:
        current_user (User): Usuario actual.

    Raises:
        HTTPException: Error HTTP.

    Returns:
        User: Usuario actual.
    """

    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403, detail="The user doesn't have enough privileges"
        )
    return current_user

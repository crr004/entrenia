import os
from typing import Annotated
from datetime import timedelta

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import HTTPException

from app.crud.users import SessionDep
from app.utils.users import authenticate_user
from app.models.tokens import Token
from app.utils.tokens import create_access_token

router = APIRouter(prefix="/login", tags=["login"])


@router.post("/", status_code=status.HTTP_200_OK, response_model=Token)
def login_user(
    session: SessionDep, data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """Obtiene un token de acceso para un usuario.

    Args:
        session (SessionDep): Sesión de la base de datos.
        data (OAuth2PasswordRequestForm): Datos del usuario.

    Returns:
        Token: Token de acceso.
    """

    user = authenticate_user(
        session=session, email=data.username, password=data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    elif not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unverified user"
        )
    acces_token_expire = timedelta(minutes=int(os.environ["ACCESS_TOKEN_EXPIRE"]))
    return Token(
        access_token=create_access_token(
            subject=user.id, expires_delta=acces_token_expire
        )
    )

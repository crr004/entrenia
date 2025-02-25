import uuid
import os
import jwt
from typing import Annotated
from jwt.exceptions import InvalidTokenError

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlmodel import Session, select, func

from app.models.users import User, UserCreate, UsersReturn
from app.models.tokens import TokenData
from app.utils import tokens
from app.utils.hashing import hash_password
from app.core import db


API_PREFIX = os.environ["API_PREFIX"]
TOKEN_URL = f"{API_PREFIX}/login/access-token"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)

SessionDep = Annotated[Session, Depends(db.get_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def create_user(*, session: Session, user_in: UserCreate) -> User:
    """Crea un nuevo usuario en la base de datos.

    Args:
        session (Session): Sesión de la base de datos.
        user_in (UserCreate): Datos del usuario a crear.

    Returns:
        User: Usuario creado.
    """

    user = User.model_validate(
        user_in, update={"password": hash_password(password=user_in.password)}
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_by_email(*, session: Session, email: str) -> User:
    """Obtiene un usuario dado su email.

    Args:
        session (Session): Sesión de la base de datos.
        email (str): Email del usuario.

    Returns:
        User: Usuario encontrado.
    """

    statement = select(User).where(User.email == email)
    user = session.exec(statement).first()
    return user


def get_user_by_id(*, session: Session, id: uuid.UUID) -> User:
    """Obtiene un usuario dado su ID.

    Args:
        session (Session): Sesión de la base de datos.
        id (uuid.UUID): ID del usuario.

    Returns:
        User: Usuario encontrado.
    """

    user = session.get(User, id)
    return user


def get_all_users(*, session: SessionDep, skip: int, limit: int) -> UsersReturn:
    """Obtiene todos los usuarios de la base de datos.

     Args:
         session (SessionDep): Sesión de la base de datos.
         skip (int): Cantidad de usuarios a omitir.
         limit (int): Cantidad de usuarios a devolver.

    Returns:
         UsersReturn: Usuarios encontrados.
    """

    count_statement = select(func.count()).select_from(User)
    count = session.exec(count_statement).one()

    statement = select(User).offset(skip).limit(limit)
    users = session.exec(statement).all()

    return UsersReturn(users=users, count=count)


def get_current_user(*, session: SessionDep, token: TokenDep) -> User:
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unverified user"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_admin(*, current_user: CurrentUser) -> User:
    """Obtiene el usuario actual si es un superusuario.

    Args:
        current_user (User): Usuario actual.

    Raises:
        HTTPException: Error HTTP.

    Returns:
        User: Usuario actual.
    """

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user

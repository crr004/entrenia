import uuid
import os
import jwt
from typing import Annotated
from jwt.exceptions import InvalidTokenError

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlmodel import Session, select, func

from app.models.users import User, UserCreate, UsersReturn, UserUpdate
from app.models.tokens import TokenData
from app.utils import tokens
from app.utils.hashing import hash_password
from app.core import db


API_PREFIX = os.environ["API_PREFIX"]
TOKEN_URL = f"{API_PREFIX}/login"

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


def get_user_by_username(*, session: Session, username: str) -> User:
    """Obtiene un usuario dado su nombre de usuario.

    Args:
        session (Session): Sesión de la base de datos.
        username (str): Nombre de usuario.

    Returns:
        User: Usuario encontrado.
    """

    statement = select(User).where(User.username == username)
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


def get_all_users(*, session: Session, skip: int, limit: int) -> UsersReturn:
    """Obtiene todos los usuarios de la base de datos.

     Args:
         session (Session): Sesión de la base de datos.
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
        session (SessionDep): Sesión de la base de datos.
        token (str): Token JWT.

    Raises:
        HTTPException[403]: Si el token no es válido.
        HTTPException[400]: Si el usuario no existe o su cuenta está desactivada o no verificada.

    Returns:
        User: Usuario actual.
    """

    try:
        data = jwt.decode(token, os.environ["SECRET_KEY"], algorithms=tokens.ALGORITHM)
        token_data = TokenData(**data)
        if data.get("type") != "auth":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
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
        HTTPException[403]: Si el usuario no tiene suficientes privilegios.

    Returns:
        User: Usuario actual.
    """

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user


def update_user(
    *, session: Session, user: User, user_data: dict, extra_data: dict | None = None
) -> User:
    """Actualiza los datos de un usuario.

    Args:
        session (Session): Sesión de la base de datos.
        current_user (User): Usuario actual.
        user_data (dict): Datos del usuario a actualizar.

    Returns:
        User: Usuario actualizado.
    """

    if extra_data:
        user.sqlmodel_update(user_data, update=extra_data)
    else:
        user.sqlmodel_update(user_data)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def update_user_by_admin(*, session: Session, db_user: User, user_in: UserUpdate):
    """Actualiza los datos de un usuario (función auxiliar para los admins).

    Args:
        session (Session): Sesión de la base de datos.
        db_user (User): Usuario a actualizar.
        user_in (UserUpdate): Datos del usuario a actualizar.

    Returns:
        User: Usuario actualizado.
    """

    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = hash_password(password=password)
        extra_data["password"] = hashed_password
    db_user = update_user(
        session=session, user=db_user, user_data=user_data, extra_data=extra_data
    )
    return db_user


def update_password(*, session: Session, user: User, new_password: str) -> User:
    """Actualiza la contraseña de un usuario.

    Args:
        session (Session): Sesión de la base de datos.
        current_user (User): Usuario actual.
        new_password (str): Nueva contraseña.

    Returns:
        User: Usuario actualizado.
    """

    user.password = new_password
    session.add(user)
    session.commit()
    return user


def delete_user(*, session: Session, user: User) -> None:
    """Elimina un usuario de la base de datos.

    Args:
        session (Session): Sesión de la base de datos.
        user (User): Usuario a eliminar.
    """

    session.delete(user)
    session.commit()

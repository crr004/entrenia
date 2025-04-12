import uuid
import os
import jwt
import logging
from typing import Annotated
from jwt.exceptions import InvalidTokenError
from sqlalchemy import or_, desc, asc

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlmodel import Session, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User, UserCreate, UsersReturn, UserUpdate
from app.models.tokens import TokenData
from app.utils import tokens
from app.utils.hashing import hash_password
from app.core import db
from app.models.datasets import Dataset
from app.models.images import Image
from app.models.classifiers import Classifier


API_PREFIX = os.environ["API_PREFIX"]
TOKEN_URL = f"{API_PREFIX}/login"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=TOKEN_URL)

SessionDep = Annotated[AsyncSession, Depends(db.get_session)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]

logger = logging.getLogger(__name__)

MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/app/media")


async def create_user(*, session: AsyncSession, user_in: UserCreate) -> User:
    """Crea un nuevo usuario en la base de datos.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        user_in (UserCreate): Datos del usuario a crear.

    Returns:
        User: Usuario creado.
    """

    user = User.model_validate(
        user_in, update={"password": hash_password(password=user_in.password)}
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def get_user_by_email(*, session: AsyncSession, email: str) -> User | None:
    """Obtiene un usuario dado su email.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        email (str): Email del usuario.

    Returns:
        User | None: Usuario encontrado.
    """

    statement = select(User).where(User.email == email)
    res = await session.execute(statement)
    user = res.scalars().first()
    if not user:
        return None
    return user


async def get_user_by_username(*, session: AsyncSession, username: str) -> User | None:
    """Obtiene un usuario dado su nombre de usuario.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        username (str): Nombre de usuario.

    Returns:
        User | None: Usuario encontrado.
    """

    statement = select(User).where(User.username == username)
    res = await session.execute(statement)
    user = res.scalars().first()
    if not user:
        return None
    return user


async def get_user_by_id(*, session: AsyncSession, id: uuid.UUID) -> User | None:
    """Obtiene un usuario dado su ID.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        id (uuid.UUID): ID del usuario.

    Returns:
        User | None: Usuario encontrado.
    """

    user = await session.get(User, id)
    if not user:
        return None
    return user


async def get_all_users(
    *,
    session: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> UsersReturn:
    """Obtiene todos los usuarios de la base de datos con soporte para paginación, búsqueda y ordenación.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        skip (int): Cantidad de usuarios a omitir. Por defecto 0.
        limit (int): Cantidad de usuarios a devolver. Por defecto 100.
        search (str | None): Texto a buscar en email, username o full_name. Por defecto None.
        sort_by (str): Campo por el que ordenar. Por defecto "created_at".
        sort_order (str): Orden ascendente ("asc") o descendente ("desc"). Por defecto "desc".

    Returns:
        UsersReturn: Usuarios encontrados y su conteo total.
    """

    # Crear consulta base.
    query = select(User)
    count_query = select(func.count()).select_from(User)

    # Aplicar filtro de búsqueda si existe.
    if search:
        search_term = f"%{search.lower()}%"
        query = query.where(
            or_(
                func.lower(User.email).like(search_term),
                func.lower(User.username).like(search_term),
                func.lower(User.full_name).like(search_term),
            )
        )
        count_query = count_query.where(
            or_(
                func.lower(User.email).like(search_term),
                func.lower(User.username).like(search_term),
                func.lower(User.full_name).like(search_term),
            )
        )

    # Aplicar ordenación.
    valid_sort_fields = [
        "email",
        "username",
        "full_name",
        "is_admin",
        "is_active",
        "is_verified",
        "created_at",
    ]
    if sort_by not in valid_sort_fields:
        sort_by = "created_at"

    # Definir dirección de ordenación.
    sort_direction = desc if sort_order.lower() == "desc" else asc

    # Manejar campos booleanos para ordenación coherente.
    if sort_by in ["is_admin", "is_active", "is_verified"]:
        # Para campos booleanos, ordenamos descendentemente (True primero) si es "desc"
        # o ascendentemente (False primero) si es "asc".
        query = query.order_by(sort_direction(getattr(User, sort_by)))
    else:
        query = query.order_by(sort_direction(getattr(User, sort_by)))

    # Añadir created_at como criterio de ordenación secundario.
    if sort_by != "created_at":
        query = query.order_by(desc(User.created_at))

    # Aplicar paginación.
    query = query.offset(skip).limit(limit)

    # Ejecutar consultas.
    users_res = await session.execute(query)
    count_res = await session.execute(count_query)

    users = list(users_res.scalars().all())
    count = count_res.scalar()

    return UsersReturn(users=users, count=count)


async def get_current_user(*, session: SessionDep, token: TokenDep) -> User:
    """Obtiene el usuario actual a partir del token JWT.

    Args:
        session (SessionDep): Sesión de la base de datos.
        token (str): Token JWT.

    Raises:
        HTTPException[403]: Si el token no es válido o no se pueden validar las credenciales.
                            o si la cuenta del usuario está desactivada/no verificada.
        HTTPException[404]: Si no existe un usuario con ese ID.

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
    user = await get_user_by_id(session=session, id=token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Unverified user"
        )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_admin(*, current_user: CurrentUser) -> User:
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


async def update_user(
    *,
    session: AsyncSession,
    user: User,
    user_data: dict,
    extra_data: dict | None = None,
) -> User:
    """Actualiza los datos de un usuario.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        current_user (User): Usuario actual.
        user_data (dict): Datos del usuario a actualizar.
        extra_data (dict | None): Datos del usuario adicionales a actualizar.

    Returns:
        User: Usuario actualizado.
    """

    if extra_data:
        user.sqlmodel_update(user_data, update=extra_data)
    else:
        user.sqlmodel_update(user_data)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user_by_admin(
    *, session: AsyncSession, db_user: User, user_in: UserUpdate
):
    """Actualiza los datos de un usuario (función auxiliar para los admins).

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
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
    db_user = await update_user(
        session=session, user=db_user, user_data=user_data, extra_data=extra_data
    )
    return db_user


async def update_password(
    *, session: AsyncSession, user: User, new_password: str
) -> User:
    """Actualiza la contraseña de un usuario.

    Args:
        session (AsyncSession): Sesión asíncrona de la base de datos.
        current_user (User): Usuario actual.
        new_password (str): Nueva contraseña.

    Returns:
        User: Usuario actualizado.
    """

    user.password = new_password
    session.add(user)
    await session.commit()
    return user


async def delete_user(*, session: AsyncSession, user: User) -> None:
    """Elimina un usuario de la base de datos y todos sus datos asociados (imágenes y modelos).

    Args:
        session (Session): Sesión de la base de datos.
        user (User): Usuario a eliminar.
    """

    # Obtener todos los datasets del usuario.
    datasets_query = select(Dataset).where(Dataset.user_id == user.id)
    result = await session.execute(datasets_query)
    datasets = result.scalars().all()

    # Para cada dataset, eliminar manualmente los archivos de imágenes.
    for dataset in datasets:
        # Obtener todas las imágenes del dataset.
        images_query = select(Image).where(Image.dataset_id == dataset.id)
        images_result = await session.execute(images_query)
        images = images_result.scalars().all()

        # Eliminar los archivos físicos de cada imagen.
        for image in images:
            try:
                file_path = os.path.join(MEDIA_ROOT, image.file_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                logger.error(
                    f"Error deleting image file {file_path}: {str(e)}", exc_info=True
                )

    # Obtener todos los clasificadores (modelos) del usuario.
    classifiers_query = select(Classifier).where(Classifier.user_id == user.id)
    classifiers_result = await session.execute(classifiers_query)
    classifiers = classifiers_result.scalars().all()

    # Eliminar los archivos físicos de cada modelo.
    for classifier in classifiers:
        if classifier.file_path:
            try:
                # Directorio que contiene el modelo y sus metadatos.
                model_dir = os.path.join(MEDIA_ROOT, classifier.file_path)
                if os.path.exists(model_dir):
                    # Eliminar el archivo del modelo.
                    model_file = os.path.join(model_dir, "model.keras")
                    if os.path.exists(model_file):
                        os.remove(model_file)

                    # Eliminar el archivo de metadatos.
                    metadata_file = os.path.join(model_dir, "metadata.json")
                    if os.path.exists(metadata_file):
                        os.remove(metadata_file)

                    # Eliminar el directorio.
                    try:
                        os.rmdir(model_dir)
                    except OSError as e:
                        logger.warning(
                            f"Error deleting directory at {model_dir}: {str(e)}"
                        )
            except Exception as e:
                logger.error(
                    f"Error deleting model files at {model_dir}: {str(e)}",
                    exc_info=True,
                )

    # Eliminar el usuario.
    await session.delete(user)
    await session.commit()

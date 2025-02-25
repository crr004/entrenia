from sqlmodel import Session, select, func
import uuid

from app.models.users import User, UserCreate, UsersReturn
from app.utils.hashing import hash_password

# from app.utils.deps import SessionDep


def create_user(*, session: Session, user_in: UserCreate) -> User:
    """Crea un nuevo usuario en la base de datos.

    Args:
        session (Session): Sesión de la base de datos.
        user_in (UserCreate): Datos del usuario a crear.

    Returns:
        User: Usuario creado.
    """

    user = User.model_validate(
        user_in, update={"password": hash_password(user_in.password)}
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


def get_user_by_id(*, session: Session, id: uuid.UUID):
    """Obtiene un usuario dado su ID.

    Args:
        session (Session): Sesión de la base de datos.
        id (uuid.UUID): ID del usuario.

    Returns:
        User: Usuario encontrado.
    """

    user = session.get(User, id)
    return user


# def get_all_users(session: SessionDep, skip: int, limit: int):
#    """Obtiene todos los usuarios de la base de datos.
#
#     Args:
#         session (SessionDep): Sesión de la base de datos.
#         skip (int): Cantidad de usuarios a omitir.
#         limit (int): Cantidad de usuarios a devolver.
#
#    Returns:
#         UsersReturn: Usuarios encontrados.
#    """
#
#    count_statement = select(func.count()).select_from(User)
#    count = session.exec(count_statement).one()
#
#    statement = select(User).offset(skip).limit(limit)
#    users = session.exec(statement).all()
#
#    return UsersReturn(data=users, count=count)

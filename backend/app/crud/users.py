from sqlmodel import Session
from app.models.users import User, UserCreate
from app.utils.hashing import hash_password


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

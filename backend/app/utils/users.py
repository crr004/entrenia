from sqlmodel import Session

from app.utils.hashing import verify_password
from app.crud.users import get_user_by_email, get_user_by_username
from app.models.users import User


def authenticate_user(
    *, session: Session, email_or_username: str, password: str
) -> User:
    """Autentica un usuario: Verifica que exista en la base de datos y que la contraseña sea correcta.

    Args:
        session (Session): Sesión de la base de datos.
        email_or_username (str): Email del usuario o nombre de usuario.
        password (str): Contraseña del usuario.

    Returns:
        User: Usuario autenticado.
    """

    if "@" in email_or_username:
        user = get_user_by_email(session=session, email=email_or_username)
    else:
        user = get_user_by_username(session=session, username=email_or_username)

    if not user:
        return None
    if not verify_password(plain_password=password, hashed_password=user.password):
        return None
    return user

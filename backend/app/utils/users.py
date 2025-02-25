from sqlmodel import Session, select
from app.models.users import User
from app.utils.hashing import verify_password
from app.crud.users import get_user_by_email


def authenticate_user(*, session: Session, email: str, password: str):
    """Autentica un usuario: Verifica que exista en la base de datos y que la contraseña sea correcta.

    Args:
        session (Session): Sesión de la base de datos.
        email (str): Email del usuario.
        password (str): Contraseña del usuario.

    Returns:
        User: Usuario autenticado.
    """

    user = get_user_by_email(session=session, email=email)
    if not user:
        return None
    if not verify_password(password, user.password):
        return None
    return user

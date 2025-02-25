from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Hashea la contraseña recibida.

    Args:
        password (str): Contraseña a hashear.

    Returns:
        str: Contraseña hasheada.
    """

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica que la contraseña recibida coincida con la contraseña hasheada.

    Args:
        plain_password (str): Contraseña a verificar en texto plano.
        hashed_password (str): Contraseña hasheada.

    Returns:
        bool: True si la contraseña coincide, False si no.
    """

    return pwd_context.verify(plain_password, hashed_password)

from sqlmodel import Session, create_engine, SQLModel, select
from app.models.users import User
import os
from app.crud import users

DB_URL = os.environ["POSTGRES_URL"]
engine = create_engine(DB_URL)


def init_db():
    """Inicializa la base de datos."""

    SQLModel.metadata.create_all(engine)


def get_session():
    """Genera una nueva sesión de la base de datos."""

    with Session(engine) as session:
        yield session


def create_first_admin(session: Session):
    """Crea el primer usuario administrador.

    Args:
        session (Session): Sesión de la base de datos.
    """

    user = session.exec(select(User).where(User.username == "admin")).first()
    if not user:
        admin = User(
            username=os.environ["FIRST_ADMIN_USERNAME"],
            email=os.environ["FIRST_ADMIN_EMAIL"],
            password=os.environ["FIRST_ADMIN_PASSWORD"],
            is_superuser=True,
            is_verified=True,
        )
        user = users.create_user(session=session, user_in=admin)

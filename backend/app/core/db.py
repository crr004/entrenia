import os

from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import sqlalchemy.exc

from app.models.users import User, UserCreate
from app.crud import users

DB_URL = os.environ["POSTGRES_URL"].replace("postgresql://", "postgresql+asyncpg://")
engine = create_async_engine(DB_URL, future=True)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Inicializa la base de datos."""
    try:
        async with engine.begin() as conn:
            # Usar checkfirst=True para no fallar si las tablas o tipos ya existen.
            await conn.run_sync(
                lambda conn: SQLModel.metadata.create_all(conn, checkfirst=True)
            )
    except sqlalchemy.exc.IntegrityError:
        # Manejo explícito de errores de integridad (como duplicación de ENUM).
        print(
            "Advertencia: Algunos objetos de la base de datos ya existen, continuando..."
        )
        pass


async def get_session():
    """Genera una nueva sesión asíncrona de la base de datos."""

    async with AsyncSession(engine) as session:
        yield session


async def create_first_admin(session: AsyncSession):
    """Crea el primer usuario administrador de forma asíncrona."""
    try:
        user = await session.execute(select(User).where(User.username == "admin"))
        user = user.first()
        if not user:
            admin = UserCreate(
                username=os.environ["FIRST_ADMIN_USERNAME"],
                email=os.environ["FIRST_ADMIN_EMAIL"],
                password=os.environ["FIRST_ADMIN_PASSWORD"],
                is_admin=True,
                is_verified=True,
            )
            user = await users.create_user(session=session, user_in=admin)
        return user
    except sqlalchemy.exc.IntegrityError:
        # Otro worker ya creó el usuario, simplemente continuar.
        await session.rollback()
        user = await session.execute(select(User).where(User.username == "admin"))
        return user.first()

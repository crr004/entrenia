import os

from sqlmodel import SQLModel, select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.users import User
from app.crud import users

DB_URL = os.environ["POSTGRES_URL"].replace("postgresql://", "postgresql+asyncpg://")
engine = create_async_engine(DB_URL, echo=True, future=True)

async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Inicializa la base de datos."""

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session():
    """Genera una nueva sesión asíncrona de la base de datos."""

    async with AsyncSession(engine) as session:
        yield session


async def create_first_admin(session: AsyncSession):
    """Crea el primer usuario administrador de forma asíncrona."""

    user = await session.execute(select(User).where(User.username == "admin"))
    user = user.first()
    if not user:
        admin = User(
            username=os.environ["FIRST_ADMIN_USERNAME"],
            email=os.environ["FIRST_ADMIN_EMAIL"],
            password=os.environ["FIRST_ADMIN_PASSWORD"],
            is_admin=True,
            is_verified=True,
        )

        user = await users.create_user(session=session, user_in=admin)

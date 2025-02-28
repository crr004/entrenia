from app.core import db


async def start():
    """Inicia la base de datos y crea el primer administrador."""

    await db.init_db()

    async for session in db.get_session():
        await db.create_first_admin(session)

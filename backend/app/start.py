from app.core import db


def start():
    """Iniciar la base de datos y crear el primer administrador."""

    db.init_db()
    with db.Session(db.engine) as session:
        db.create_first_admin(session)

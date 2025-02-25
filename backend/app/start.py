from app.core import db
from app.core.db import engine


def start():
    db.init_db()
    with db.Session(engine) as session:
        db.create_first_admin(session)
